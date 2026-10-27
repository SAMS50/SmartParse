"""Opt-in removal of independent blocked definitions in private VFS variants."""
from dataclasses import dataclass,asdict
import json
import os
import re
from pathlib import Path
import tempfile
import time

from extended_c import Compiler,to_report
from extended_c.configuration import configuration_args
from phase6.v2.regions import same_path
from phase6.v2.eligibility import parse_checkers
from phase6.v3.engine import (run_recovery,sha,compiler_check,analyzer_check,ast,
                             overlay_file,eligibility,mapped_diagnostic)
from phase6.v3.execution import Budget,Limits,LimitReached
from phase6.v3.policy import apply_edits,point_offset,source_map,unescape,original_offset
from .policy import inventory,plan,mask,preprocess_signature


@dataclass(frozen=True)
class IsolationLimits:
    exclusions:int=8
    variants:int=1
    invocations:int=64
    analyzer_invocations:int=5
    total_seconds:float=120
    call_seconds:float=10

    def validate(self):
        import math
        for key,cap in [('exclusions',16),('variants',1),('invocations',80),('analyzer_invocations',6)]:
            value=getattr(self,key)
            if type(value) is not int or not 1<=value<=cap:raise ValueError(f'{key} must be 1..{cap}')
        for key,cap in [('total_seconds',120),('call_seconds',30)]:
            value=getattr(self,key)
            if not math.isfinite(value) or not 0<value<=cap:raise ValueError(f'{key} must be positive and <= {cap}')


def run_isolation(source,*,isolate=False,repair=False,compiler='auto',standard=None,
                  include_dirs=(),defines=(),limits=None):
    limits=limits or IsolationLimits();limits.validate();started=time.monotonic()
    path=Path(source).resolve();original=path.read_bytes()
    config=configuration_args(standard,include_dirs,defines)
    # v3 is composed without modifying its API, output, or implementation.
    base=run_recovery(path,repair=repair,compiler=compiler,standard=standard,
                      include_dirs=include_dirs,defines=defines,static_analysis=False,
                      limits=Limits(invocations=limits.invocations,total_seconds=min(90,limits.total_seconds),call_seconds=limits.call_seconds))
    base_calls=base['recovery']['usage']['calls'];budget=None;directory=None;accepted=False
    report={'schema':'smartparse.unaffected_regions','schema_version':'1.0',
            'source':{'path':str(path),'sha256':sha(original)},'recovery_report':base,
            'isolation':{'enabled':isolate,'experimental':True,'limits':asdict(limits),
                         'status':'not_attempted','reason':'isolation_not_requested','inventory':[],
                         'excluded_functions':[],'retained_functions':[],'blockers':[],
                         'variant':None,'eligibility_improved':False,'function_path_coverage_certified':False},
            'baseline_static_analysis':None,
            'isolation_conditioned_findings':[],'unique_additional_findings':[],'suppressed_findings':[]}
    iso=report['isolation'];analyzer_calls=sum('--analyze' in c['command'] for c in base_calls)
    try:
        if not isolate:return report
        iso.update(status='abstained',reason=None)
        if not base['source']['original_unchanged'] or not base['baseline']:raise ValueError('baseline/source preservation unavailable')
        if base['recovery']['budget_exhausted']:raise LimitReached('baseline/recovery budget exhausted')
        analysis=base['baseline']['analysis'];selected=analysis.get('compiler')
        if not selected or selected['backend']!='clang':raise ValueError('isolation requires selected Clang')
        selected=Compiler(selected['path'],selected['backend'],selected['version'],tuple(selected['flags']))
        if analyzer_calls>=limits.analyzer_invocations:raise LimitReached('analyzer invocation budget exhausted')
        remaining=limits.total_seconds-(time.monotonic()-started)
        calls_left=limits.invocations-len(base_calls)
        if remaining<=0 or calls_left<=0:raise LimitReached('combined runtime/invocation budget exhausted')
        budget=Budget(Limits(invocations=calls_left,total_seconds=remaining,call_seconds=limits.call_seconds))
        def analyzer_slot():
            nonlocal analyzer_calls
            if analyzer_calls>=limits.analyzer_invocations:raise LimitReached('analyzer invocation budget exhausted')
            analyzer_calls+=1
        analyzer_slot()
        probe=budget.call('isolation_analyzer_capability',[selected.path,'--analyze','-x','c','-Xanalyzer','-analyzer-output=text','-o',os.devnull,'-'],b'int capability_probe;\n')
        if probe.returncode or probe.stderr.strip():raise ValueError('selected analyzer capability unavailable')
        analyzer_slot()
        baseline_analyzer=analyzer_check(budget,selected,path,config)
        report['baseline_static_analysis']=to_report(baseline_analyzer)
        analyzer_slot()
        query=budget.call('isolation_checker_context',[selected.path,'--analyze','-x','c','-Xclang','-analyzer-list-enabled-checkers','-o',os.devnull,'-'],b'int capability_probe;\n')
        report['analyzer_context']={'compiler':asdict(selected),'enabled_default_checkers':parse_checkers(query.stdout.decode('utf-8',errors='replace')) if query.returncode==0 else None,
                                    'checker_query_returncode':query.returncode,'extra_checkers_enabled':False}
        variants=base['recovery']['accepted_variants'];edits=variants[-1]['edits'] if variants else []
        current=apply_edits(original,edits)
        previous=variants[-1]['eligibility'] if variants else base['baseline']['eligibility']
        if previous['stages']['compiler']['frontend_accepted']:raise ValueError('frontend already accepted; isolation unnecessary')
        with tempfile.TemporaryDirectory(prefix='smartparse-isolation-') as work:
            directory=work;before_overlay=[]
            if edits:
                repaired=Path(work)/'repaired.c';repaired.write_bytes(current)
                before_overlay=overlay_file(work,'repaired',path,repaired)
            # Check VFS filename semantics even without v3 punctuation recovery.
            virtual=Path(work)/'probe.c';external=Path(work)/'probe-content.c'
            virtual.write_bytes(b'#error overlay must replace this\n');external.write_bytes(b'const char *probe = __FILE__;\n')
            probe_overlay=overlay_file(work,'probe',virtual,external)
            if compiler_check(budget,selected,virtual,config,probe_overlay).returncode:raise ValueError('VFS capability unavailable')
            probe_pp=budget.call('vfs_identity',[selected.path,'-x','c','-E',*config,*probe_overlay,str(virtual)])
            literals=re.findall(rb'"((?:\\.|[^"\\])*)"',probe_pp.stdout)
            if probe_pp.returncode or not any(same_path(unescape(x).decode('utf-8'),str(virtual)) for x in literals):
                raise ValueError('VFS original filename identity not preserved')
            tree,code=ast(budget,selected,path,config,before_overlay)
            iso['inventory']=inventory(tree,path,current)
            # Use freshly parsed diagnostics to assign blockers by physical
            # byte location; this is blocker assignment, never coverage proof.
            checked=compiler_check(budget,selected,path,config,before_overlay)
            if checked.status!='completed' or any(d.category=='syntax' and d.severity=='error' for d in checked.diagnostics):
                raise ValueError('syntax/incomplete frontend requires recovery before isolation')
            excluded,retained,blockers=plan(iso['inventory'],checked.diagnostics,path,current,limits.exclusions)
            for r in excluded+retained:
                r['coordinate_space']='punctuation_recovery_parent' if edits else 'original'
                r['original_source_range']={'start_byte':original_offset(r['start_byte'],edits),
                                            'end_byte_exclusive':original_offset(r['end_byte_exclusive'],edits),
                                            'start_line':r['start_line'],'end_line':r['end_line']}
            iso.update(excluded_functions=excluded,retained_functions=retained,blockers=blockers)
            variant=mask(current,excluded)
            if path.read_bytes()!=original:raise ValueError('original source changed during analysis')
            private=Path(work)/'isolated.c';private.write_bytes(variant)
            overlay=overlay_file(work,'isolated',path,private)
            iso['variant']={'id':'I1','status':'validating','isolation_conditioned':True,'source_sha256':sha(variant),
                            'parent_sha256':sha(current),'original_sha256':sha(original),'bytes':len(variant),
                            'punctuation_edit_candidate_ids':[e['candidate_id'] for e in edits],
                            'excluded_spans':[{k:r[k] for k in ('name','start_byte','end_byte_exclusive','start_line','end_line')} for r in excluded],
                            'mapping':{'isolation_offsets':'identity; excluded non-newline bytes replaced by spaces',
                                       'parent_to_original':source_map(original,edits)},'eligibility':None}
            validated=compiler_check(budget,selected,path,config,overlay)
            if validated.returncode or validated.status!='completed':raise ValueError('isolation variant frontend did not complete without errors')
            pp=[]
            for label,flags in [('before',before_overlay),('after',overlay)]:
                process=budget.call('isolation_preprocessing_'+label,[selected.path,'-x','c','-E',*config,*flags,str(path)])
                if process.returncode:raise ValueError('isolation preprocessing failed')
                pp.append(process.stdout)
            if preprocess_signature(pp[0],path,excluded)!=preprocess_signature(pp[1],path,excluded):
                raise ValueError('preprocessing outside excluded functions changed')
            next_tree,next_code=ast(budget,selected,path,config,overlay)
            after=inventory(next_tree,path,variant)
            if next_code or [(r['name'],r['start_byte'],r['end_byte_exclusive'],r['references']) for r in after]!=[(r['name'],r['start_byte'],r['end_byte_exclusive'],r['references']) for r in retained]:
                raise ValueError('retained physical AST/dependencies changed')
            if path.read_bytes()!=original:raise ValueError('original source changed during validation')
            analyzer_slot()
            validated.static_analysis=analyzer_check(budget,selected,path,config,overlay)
            context=previous['manifest'].copy();context.pop('source',None)
            envelope=eligibility(path,variant,validated,next_tree,next_code,context,analyzer_requested=True,original_sha256=sha(original))
            envelope['manifest']['source']['snapshot_kind']='private_isolation_variant'
            envelope['mapping']['isolation_excluded_spans']=iso['variant']['excluded_spans']
            envelope['mapping']['private_overlay_edits']=True
            iso['variant'].update(status='accepted',eligibility=envelope,preprocessing_preserved_outside_exclusions=True)
            accepted=True;iso['status']='completed' if validated.static_analysis.status=='completed' else 'partial'
            iso['reason']='frontend accepted; analyzer '+validated.static_analysis.status
            iso['eligibility_improved']=validated.static_analysis.status=='completed'
            for r in retained:
                r['analyzer_coverage']={'status':'unknown','reason':'Invocation completion does not prove per-function/path execution.'}
            for r in excluded:r['analyzer_coverage']={'status':'not_attempted','reason':'Definition excluded from private variant.'}
            # Count only primary analyzer warnings in retained physical bodies.
            # Notes remain supporting evidence, never independent findings.
            known=set()
            def key(d):return (d.get('file'),d.get('line'),d.get('column'),d.get('diagnostic_id'),d.get('message'))
            for d in (report['baseline_static_analysis'] or {}).get('findings',[]):
                if d['severity']=='warning':known.add(key(d))
            for f in base['repair_conditioned_findings']:
                d=f['evidence']
                if f['source']=='analyzer' and d['severity']=='warning':known.add(key({**d,**(d.get('original_location') or {})}))
            seen=set();group=None
            for d in validated.static_analysis.findings:
                item=mapped_diagnostic(d,path,variant,original,edits)
                retained_location=False
                if same_path(d.file,str(path)) and d.line and d.column:
                    at=point_offset(variant,d.line,d.column)
                    retained_location=any(r['start_byte']<=at<r['end_byte_exclusive'] for r in retained)
                if d.severity=='warning':
                    group=None
                    if not retained_location:
                        report['suppressed_findings'].append({'evidence':item,'reason':'not in retained main-file function'});continue
                    identifier=key({**item,**(item.get('original_location') or {})})
                    if identifier in seen:continue
                    seen.add(identifier)
                    group={'id':'I1:F'+str(len(report['isolation_conditioned_findings'])+1),'variant_id':'I1',
                           'isolation_conditioned':True,'repair_conditioned':bool(edits),'evidence':item,'supporting_notes':[],
                           'additional_to_baseline_and_recovery':identifier not in known,
                           'adjudication':'unreviewed_conditioned_observation','confirmed_original_defect':False}
                    report['isolation_conditioned_findings'].append(group)
                elif d.severity=='note' and group is not None:
                    group['supporting_notes'].append(item)
            safe=[]
            for finding in report['isolation_conditioned_findings']:
                crosses=False
                for note in finding['supporting_notes']:
                    if same_path(note['file'],str(path)) and note.get('line') and note.get('column'):
                        at=point_offset(variant,note['line'],note['column'])
                        if any(r['start_byte']<=at<r['end_byte_exclusive'] for r in excluded):crosses=True
                if crosses:report['suppressed_findings'].append({'evidence':finding,'reason':'trace references an excluded region'})
                else:safe.append(finding)
            report['isolation_conditioned_findings']=safe
            report['unique_additional_findings']=[f['id'] for f in safe if f['additional_to_baseline_and_recovery']]
    except LimitReached as error:
        accepted=False
        iso.update(status='timed_out' if 'timed out' in str(error) else 'budget_exhausted',reason=str(error),eligibility_improved=False)
        report['isolation_conditioned_findings']=[];report['unique_additional_findings']=[]
    except (ValueError,OSError,RuntimeError,KeyError,TypeError,AttributeError,RecursionError) as error:
        accepted=False;iso.update(status='abstained',reason=str(error),eligibility_improved=False)
        report['isolation_conditioned_findings']=[];report['unique_additional_findings']=[]
    finally:
        if iso['variant'] and not accepted:iso['variant']['status']='rejected'
        try:report['source']['original_unchanged']=path.read_bytes()==original
        except OSError:report['source']['original_unchanged']=False
        iso['temporary_workspace_removed']=directory is None or not Path(directory).exists()
        iso['usage']={'compiler_invocations':len(base_calls)+(len(budget.calls) if budget else 0),
                      'analyzer_invocations':analyzer_calls,'elapsed_seconds':round(time.monotonic()-started,6),
                      'isolation_calls':budget.calls if budget else []}
        if not report['source']['original_unchanged'] or not iso['temporary_workspace_removed']:
            iso.update(status='failed',reason='source preservation/temporary cleanup not verified',eligibility_improved=False)
            report['isolation_conditioned_findings']=[];report['unique_additional_findings']=[]
    return report
