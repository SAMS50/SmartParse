"""Bounded, opt-in semicolon insertion using Clang fix-its + physical ASTs.

All variants use a private VFS overlay: source, include root and __FILE__ retain
their original virtual identities. No original file or prior artifact is written.
"""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from extended_c import AnalysisResult,Compiler,to_report
from extended_c.configuration import configuration_args
from extended_c.diagnostics import parse_output
from extended_c.static_analysis import parse_analyzer_output, _command as analyzer_command
from phase6.v2.eligibility import coverage,pass_blockers,parse_macros,parse_checkers,parse_includes
from phase6.v2.regions import functions_from_ast,same_path
from .execution import Budget,Limits,LimitReached
from .policy import fixits,boundary_candidate,apply_edits,original_offset,point_offset,source_map,only_inserted_semicolon,unescape


def sha(data):return hashlib.sha256(data).hexdigest()


def overlay_file(directory,name,path,external):
    overlay=Path(directory)/(name+'.json')
    overlay.write_text(json.dumps({'version':0,'use-external-names':False,
        'roots':[{'type':'file','name':str(path),'external-contents':str(external)}]}),encoding='utf-8')
    return ['-ivfsoverlay',str(overlay)]


def discover(budget,choice):
    choices=['clang','gcc'] if choice=='auto' else [choice]
    problems=[]
    for name in choices:
        path=shutil.which(name)
        if not path:problems.append(name+': not found');continue
        version=budget.call('compiler_version',[path,'--version'])
        text=(version.stdout+version.stderr).decode('utf-8',errors='replace')
        family='clang' if 'clang' in text.lower() else 'gcc' if 'gcc' in text.lower() else None
        if version.returncode or not family:problems.append(name+': not a recognized Clang/GCC');continue
        required=budget.call('syntax_capability',[path,'-x','c','-fsyntax-only','-'],b'int capability_probe;\n')
        if required.returncode:problems.append(name+': syntax-only unavailable');continue
        options=['-Wall','-Wextra','-Wparentheses','-fdiagnostics-show-option','-fdiagnostics-color=never',
                 '-ferror-limit=0' if family=='clang' else '-fmax-errors=0']
        if family=='clang':options.append('-fno-diagnostics-fixit-info')
        flags=[]
        for flag in options:
            checked=budget.call('optional_flag_capability',[path,'-x','c','-fsyntax-only',flag,'-'],b'int capability_probe;\n')
            if checked.returncode==0 and not checked.stderr.strip():flags.append(flag)
        return Compiler(str(Path(path).resolve()),family,text.strip().splitlines()[0],tuple(flags))
    raise RuntimeError('No usable selected compiler: '+'; '.join(problems))


def compiler_check(budget,compiler,path,config,overlay=()):
    command=(compiler.path,'-x','c','-fsyntax-only',*compiler.flags,*config,*overlay,str(path))
    process=budget.call('compiler_validation',command)
    diagnostics,unknown=parse_output(process.stderr.decode('utf-8',errors='replace'),compiler.backend)
    status='completed' if process.returncode in (0,1) and not unknown and not any(d.severity=='fatal error' for d in diagnostics) else 'partial'
    if process.returncode and not diagnostics:status='failed'
    return AnalysisResult(status,compiler,diagnostics,returncode=process.returncode,
        stdout=process.stdout.decode('utf-8',errors='replace'),stderr=process.stderr.decode('utf-8',errors='replace'),
        command=command,unrecognized_output=unknown)


def analyzer_check(budget,compiler,path,config,overlay=()):
    command=analyzer_command(compiler,path,os.devnull,(*config,*overlay))
    process=budget.call('static_analysis',command)
    diagnostics,findings,unknown=parse_analyzer_output(process.stderr.decode('utf-8',errors='replace'))
    status='completed' if process.returncode==0 and not unknown and not any(d.severity in ('error','fatal error') for d in diagnostics) else 'partial'
    return AnalysisResult(status,compiler,diagnostics,returncode=process.returncode,
        stdout=process.stdout.decode('utf-8',errors='replace'),stderr=process.stderr.decode('utf-8',errors='replace'),
        command=command,findings=findings,unrecognized_output=unknown)


def ast(budget,compiler,path,config,overlay=()):
    process=budget.call('ast_inventory',[compiler.path,'-x','c','-fsyntax-only',*compiler.flags,*config,*overlay,'-Xclang','-ast-dump=json',str(path)])
    try:tree=json.loads(process.stdout)
    except (ValueError,UnicodeError) as error:raise ValueError('unusable AST JSON') from error
    if not isinstance(tree,dict) or tree.get('kind')!='TranslationUnitDecl':raise ValueError('unusable AST envelope')
    return tree,process.returncode


def preprocess(budget,compiler,path,config,overlay=()):
    process=budget.call('preprocessing_guard',[compiler.path,'-x','c','-E','-P',*config,*overlay,str(path)])
    if process.returncode:raise ValueError('preprocessing did not complete')
    return process.stdout


def mapped_diagnostic(diagnostic,path,current,original,edits):
    data=asdict(diagnostic)
    data['coordinate_space']='compiler-reported'
    if same_path(diagnostic.file,str(path)) and diagnostic.line and diagnostic.column:
        offset=point_offset(current,diagnostic.line,diagnostic.column)
        mapped=original_offset(offset,edits)
        data['variant_location']={'line':diagnostic.line,'column':diagnostic.column,'byte_offset':offset}
        if mapped is None:data['original_location']=None;data['coordinate_space']='generated_semicolon'
        else:
            row=original.count(b'\n',0,mapped)+1
            start=original.rfind(b'\n',0,mapped)+1
            data['original_location']={'file':str(path),'line':row,'column':mapped-start+1,'byte_offset':mapped}
            data['coordinate_space']='mapped-original-bytes'
    return data


def error_keys(result,path,current,original,edits):
    keys=set()
    for diagnostic in result.diagnostics:
        if diagnostic.severity not in ('error','fatal error'):continue
        item=mapped_diagnostic(diagnostic,path,current,original,edits)
        if item.get('coordinate_space')=='generated_semicolon':raise ValueError('error points into generated punctuation')
        location=item.get('original_location') or {'file':diagnostic.file,'line':diagnostic.line,'column':diagnostic.column}
        keys.add((location['file'],location['line'],location['column'],diagnostic.severity,diagnostic.diagnostic_id,diagnostic.message))
    return keys


def eligibility(path,data,result,tree,ast_status,context,*,analyzer_requested=False,original_sha256=None):
    """Same conservative coverage contract as v2, without unaccounted probes."""
    accepted=result.status=='completed' and result.returncode==0
    inventory={'status':'unsupported','regions':[],'exclusions':[],'basis':'No verified Clang AST inventory available'}
    if tree is not None:
        regions,exclusions=functions_from_ast(tree,str(path),data)
        inventory.update(status='completed' if ast_status==0 else 'partial',regions=regions,exclusions=exclusions,
                         basis='v2 physical AST validation; recovery does not certify analyzer path coverage')
    analyzer=result.static_analysis
    compiler_cov=coverage(result,'compiler',frontend_accepted=accepted)
    analyzer_cov=coverage(analyzer,'analyzer')
    if analyzer_requested and not accepted and analyzer is None:
        analyzer_cov={'status':'blocked','reason':'Variant frontend rejected; analyzer not invoked on this intermediate variant.'}
    regions=[{'id':'translation_unit','kind':'translation_unit','name':None,'start_line':1 if data else None,
              'end_line':len(data.splitlines()),'compiler_coverage':compiler_cov,'analyzer_coverage':analyzer_cov}]
    for region in inventory['regions']:
        regions.append({**region,'compiler_coverage':coverage(result,'compiler',reliable_function=True,frontend_accepted=accepted and ast_status==0),
                        'analyzer_coverage':analyzer_cov})
    return {'schema':'smartparse.analysis_eligibility','schema_version':'1.0',
        'manifest':{'source':{'path':str(path),'sha256':sha(data),'bytes':len(data),'physical_lines':len(data.splitlines()),
                              'original_source_unchanged':True,'pre_analysis_sha256':sha(data),
                              'snapshot_kind':'private_vfs_variant' if original_sha256 and sha(data)!=original_sha256 else 'original',
                              'original_file_sha256':original_sha256 or sha(data)},
                    **context},
        'stages':{'compiler':{'completion':result.status,'returncode':result.returncode,'frontend_accepted':accepted},
                  'analyzer':{'completion':analyzer.status if analyzer else 'not_attempted','returncode':analyzer.returncode if analyzer else None},
                  'preprocessing_probe':{'status':'see_recovery_budget_log'}},
        'blockers':pass_blockers(result,'compiler')+pass_blockers(analyzer,'analyzer'),
        'region_inventory':inventory,'regions':regions,
        'mapping':{'source_edits_applied':False,'private_overlay_edits':bool(original_sha256 and sha(data)!=original_sha256),
                   'function_locations':'physical bytes of this source snapshot; variant maps stored in recovery provenance'},
        'analysis':to_report(result)}


def run_recovery(source,*,repair=False,compiler='auto',standard=None,include_dirs=(),defines=(),static_analysis=False,limits=None):
    limits=limits or Limits();budget=Budget(limits)
    path=Path(source).resolve()
    original=path.read_bytes()
    if path.suffix.lower()!='.c':raise ValueError('source must be .c')
    if len(original)>1024*1024:raise ValueError('this bounded recovery prototype accepts at most 1 MiB of source')
    config=configuration_args(standard,include_dirs,defines)
    output={'schema':'smartparse.repair_for_analysis','schema_version':'1.0',
            'source':{'path':str(path),'sha256':sha(original)},'baseline':None,
            'recovery':{'enabled':repair,'limits':asdict(limits),'candidates':[],'accepted_variants':[],
                        'non_whitelisted_suggestions':[],'stop_reason':None,'eligibility_change':None},
            'repair_conditioned_findings':[]}
    selected=None;baseline=None;context=None;tree=None;current_result=None;workdir=None;baseline_digest=None
    try:
        selected=discover(budget,compiler)
        context={'working_directory':str(Path.cwd()),'requested_standard':standard,
                 'include_directories':[{'provided':str(p),'resolved':str(Path(p).resolve())} for p in include_dirs],
                 'macro_definitions':list(defines),'warning_options':{'compiler':list(selected.flags),'analyzer':list(selected.flags) if static_analysis else []},
                 'checker_options':'driver defaults; query recorded if static analysis requested','tool_contexts':{'compiler':{'compiler':asdict(selected)}}}
        target=budget.call('target_context',[selected.path,'-dumpmachine'])
        context['tool_contexts']['compiler']['target']=target.stdout.decode('utf-8',errors='replace').strip() if target.returncode==0 else None
        macros=budget.call('standard_context',[selected.path,'-x','c','-E','-dM',*config,'-'],b'\n')
        context['tool_contexts']['compiler']['standard_macros']=parse_macros(macros.stdout.decode('utf-8',errors='replace')) if macros.returncode==0 else {}
        includes=budget.call('include_context',[selected.path,'-x','c','-E','-v',*config,'-'],b'\n')
        context['tool_contexts']['compiler']['system_include_paths']=parse_includes(includes.stderr.decode('utf-8',errors='replace')) if includes.returncode==0 else None
        context['quote_include_root']=str(path.parent)
        context['include_environment']={key:os.environ.get(key) for key in ('CPATH','C_INCLUDE_PATH','INCLUDE','SDKROOT')}
        baseline=compiler_check(budget,selected,path,config)
        current_result=baseline
        if selected.backend=='clang':tree,ast_status=ast(budget,selected,path,config)
        else:ast_status=None
        before_pp=preprocess(budget,selected,path,config)
        if static_analysis and selected.backend=='clang':
            capability=budget.call('analyzer_capability',[selected.path,'--analyze','-x','c','-Xanalyzer','-analyzer-output=text','-o',os.devnull,'-'],b'int capability_probe;\n')
            if capability.returncode==0 and not capability.stderr.strip():
                baseline.static_analysis=analyzer_check(budget,selected,path,config)
                base=analyzer_command(selected,'-',os.devnull,config)
                query=budget.call('checker_context',[*base[:-1],'-Xclang','-analyzer-list-enabled-checkers','-'],b'int capability_probe;\n')
                context['tool_contexts']['analyzer']={'compiler':asdict(selected),'target':context['tool_contexts']['compiler']['target'],
                    'enabled_default_checkers':parse_checkers(query.stdout.decode('utf-8',errors='replace')) if query.returncode==0 else None}
            else:baseline.static_analysis=AnalysisResult('unavailable',issues=['Selected analyzer invocation unavailable'],findings=[])
        elif static_analysis:
            baseline.static_analysis=AnalysisResult('unavailable',issues=['This prototype uses the selected Clang driver; GCC remains regular syntax/type only'],findings=[])
        output['baseline']={'immutable':True,'source_sha256':sha(original),'analysis':to_report(baseline),
                            'eligibility':eligibility(path,original,baseline,tree,ast_status,context,analyzer_requested=static_analysis)}
        baseline_digest=sha(json.dumps(output['baseline']['analysis'],sort_keys=True).encode())
        budget.check()
        if not repair:output['recovery']['stop_reason']='repair_not_requested';return output
        if selected.backend!='clang':output['recovery']['stop_reason']='abstained: selected compiler has no verified fix-it/AST/VFS recovery adapter';return output
        if not any(d.severity=='error' and d.category=='syntax' for d in baseline.diagnostics):
            output['recovery']['stop_reason']='abstained: no syntax blocker eligible for punctuation recovery';return output
        # Private output, including VFS capability fixtures, is always cleaned.
        with tempfile.TemporaryDirectory(prefix='smartparse-recovery-') as directory:
            workdir=directory
            virtual=Path(directory)/'virtual.c';external=Path(directory)/'mapped.c'
            virtual.write_bytes(b'#error VFS capability must not read this file\n')
            external.write_bytes(b'const char *probe_file = __FILE__;\n')
            overlay=overlay_file(directory,'capability',virtual,external)
            checked=compiler_check(budget,selected,virtual,config,overlay)
            pp=preprocess(budget,selected,virtual,config,overlay)
            literals=re.findall(rb'"((?:\\.|[^"\\])*)"',pp)
            if checked.returncode or not any(same_path(unescape(x).decode('utf-8'),str(virtual)) for x in literals):
                raise ValueError('VFS source/name preservation capability unavailable')
            capability=budget.call('fixit_capability',[selected.path,'-x','c','-fsyntax-only','-fdiagnostics-parseable-fixits','-'],b'int capability_probe\n')
            if not any(f['replacement']==';' for f in fixits(capability.stderr)):
                raise ValueError('machine-readable semicolon fix-it capability unavailable')
            edits=[];current=original;current_overlay=[];current_tree=tree
            for round_number in range(1,limits.rounds+1):
                budget.check()
                if path.read_bytes()!=original:raise ValueError('original source changed during recovery')
                if not any(d.severity=='error' and d.category=='syntax' for d in current_result.diagnostics):
                    output['recovery']['stop_reason']='abstained: remaining blockers require semantic assumptions' if current_result.returncode else 'frontend_accepted'
                    break
                if len(edits)>=limits.edits:raise LimitReached('edit budget exhausted')
                output['recovery']['rounds_attempted']=round_number
                captured=budget.call('machine_fixit_capture',[selected.path,'-x','c','-fsyntax-only',*selected.flags,*config,*current_overlay,'-fdiagnostics-parseable-fixits',str(path)])
                suggestions=fixits(captured.stderr)
                advanced=False
                for fix in suggestions:
                    if fix['replacement']!=';':
                        output['recovery']['non_whitelisted_suggestions'].append({'replacement':fix['replacement'],'line':fix['start_line'],'reason':'not a semicolon insertion'});continue
                    if len(output['recovery']['candidates'])>=limits.candidates:raise LimitReached('candidate budget exhausted')
                    candidate={'id':f'C{len(output["recovery"]["candidates"])+1}','round':round_number,'fixit':fix,'status':'rejected','reason':None}
                    output['recovery']['candidates'].append(candidate)
                    private=None;proposed_overlay=None
                    try:
                        proof=boundary_candidate(fix,current_tree,path,current)
                        offset=original_offset(proof['offset'],edits)
                        if offset is None or any(e['original_offset']==offset for e in edits):raise ValueError('ambiguous/generated insertion location')
                        next_edits=edits+[{'original_offset':offset,'replacement':';','candidate_id':candidate['id'],
                                          'original_line':original.count(b'\n',0,offset)+1,'original_byte_column':offset-(original.rfind(b'\n',0,offset)+1)+1,
                                          'proof':proof,'source_sha256':sha(original)}]
                        variant=apply_edits(original,next_edits)
                        if len(variant.splitlines())!=len(original.splitlines()):raise ValueError('line mapping changed')
                        if len(output['recovery']['accepted_variants'])>=limits.retained_variants:raise LimitReached('retained-variant budget exhausted')
                        private=Path(directory)/(candidate['id']+'.c');private.write_bytes(variant)
                        proposed_overlay=overlay_file(directory,candidate['id'],path,private)
                        validated=compiler_check(budget,selected,path,config,proposed_overlay)
                        old_keys=error_keys(current_result,path,current,original,edits)
                        new_keys=error_keys(validated,path,variant,original,next_edits)
                        if validated.status!='completed' or not new_keys<old_keys:raise ValueError('compiler validation introduced new errors or failed to remove an existing error')
                        after_pp=preprocess(budget,selected,path,config,proposed_overlay)
                        if not only_inserted_semicolon(before_pp,after_pp):raise ValueError('preprocessing changed beyond one semicolon token')
                        next_tree,next_ast_status=ast(budget,selected,path,config,proposed_overlay)
                        if static_analysis and validated.returncode==0:
                            if baseline.static_analysis is None or baseline.static_analysis.status=='unavailable':raise ValueError('analyzer capability unavailable')
                            validated.static_analysis=analyzer_check(budget,selected,path,config,proposed_overlay)
                        variant_id=f'V{len(output["recovery"]["accepted_variants"])+1}'
                        entry={'id':variant_id,'repair_conditioned':True,'source_sha256':sha(variant),'parent_sha256':sha(current),
                               'original_sha256':sha(original),'edits':next_edits,'source_map':source_map(original,next_edits),
                               'line_mapping':'identity; byte columns use explicit insertion map','temporary_files_removed':None,
                               'eligibility':eligibility(path,variant,validated,next_tree,next_ast_status,context,analyzer_requested=static_analysis,original_sha256=sha(original)),
                               'preprocessing_guard':{'before_sha256':sha(before_pp),'after_sha256':sha(after_pp),'only_one_semicolon_token_added':True}}
                        conditioned=[]
                        for role,items in [('compiler',validated.diagnostics),('analyzer',validated.static_analysis.findings if validated.static_analysis else [])]:
                            for diagnostic in items:
                                conditioned.append({'variant_id':variant_id,'source':role,'repair_conditioned':True,
                                    'evidence':mapped_diagnostic(diagnostic,path,variant,original,next_edits),'edit_candidate_ids':[e['candidate_id'] for e in next_edits]})
                        output['recovery']['accepted_variants'].append(entry)
                        output['repair_conditioned_findings'].extend(conditioned)
                        candidate.update(status='accepted',reason='machine fix-it + unique AST boundary + strict compiler error-subset + preprocessing token guard',
                                         original_offset=offset,variant_id=variant_id)
                        current,current_result,current_overlay,current_tree,before_pp,edits=variant,validated,proposed_overlay,next_tree,after_pp,next_edits
                        advanced=True;break
                    except ValueError as error:
                        candidate['reason']=str(error)
                        if private is not None:private.unlink(missing_ok=True)
                        if proposed_overlay:Path(proposed_overlay[1]).unlink(missing_ok=True)
                if advanced and not any(d.severity=='error' and d.category=='syntax' for d in current_result.diagnostics):
                    output['recovery']['stop_reason']='abstained: remaining blockers require semantic assumptions' if current_result.returncode else 'frontend_accepted'
                    break
                if not advanced:output['recovery']['stop_reason']='abstained: no unique whitelisted candidate passed validation';break
            else:output['recovery']['stop_reason']='repair round budget exhausted'
    except LimitReached as error:output['recovery']['stop_reason']=str(error)
    except (ValueError,OSError,RuntimeError,TypeError,KeyError,AttributeError) as error:output['recovery']['stop_reason']='abstained: '+str(error)
    finally:
        try:output['source']['original_unchanged']=path.read_bytes()==original
        except OSError:output['source']['original_unchanged']=False
        if baseline is not None and output['baseline'] is None:
            output['baseline']={'immutable':True,'source_sha256':sha(original),'analysis':to_report(baseline),
                'eligibility':eligibility(path,original,baseline,None,None,context or {},analyzer_requested=static_analysis),
                'metadata_incomplete':True}
        for candidate in output['recovery']['candidates']:
            if candidate['reason'] is None:candidate['reason']='validation interrupted; no accepted repair claim'
        try:cleaned=workdir is None or not Path(workdir).exists()
        except OSError:cleaned=False
        output['recovery']['temporary_workspace_removed']=cleaned
        for variant in output['recovery']['accepted_variants']:variant['temporary_files_removed']=cleaned
        if not cleaned:output['recovery']['stop_reason']='temporary cleanup could not be verified; inspect invocation paths'
        initial=baseline is not None and baseline.returncode==0 and baseline.status=='completed'
        last=output['source']['original_unchanged'] and current_result is not None and current_result.returncode==0 and current_result.status=='completed'
        output['recovery']['eligibility_change']={'baseline_frontend_accepted':initial,'final_frontend_accepted':last,
            'frontend_newly_eligible':not initial and last,
            'analyzer_newly_completed':bool(output['source']['original_unchanged'] and current_result and current_result.static_analysis and current_result.static_analysis.status=='completed' and
                                            (not baseline or not baseline.static_analysis or baseline.static_analysis.status!='completed')),
            'function_path_coverage_certified':False,
            'note':'Fewer compiler errors alone do not establish improved analysis eligibility.'}
        output['recovery']['usage']=budget.usage()
        output['recovery']['budget_exhausted']=bool(budget.stopped or 'budget exhausted' in (output['recovery']['stop_reason'] or ''))
        if output['baseline'] is not None:
            output['baseline']['analysis_sha256']=sha(json.dumps(output['baseline']['analysis'],sort_keys=True).encode())
            if baseline_digest and output['baseline']['analysis_sha256']!=baseline_digest:raise RuntimeError('baseline diagnostics mutated')
    return output
