"""Opt-in semantic adapters over validated compiler AST and existing checkers."""
from dataclasses import asdict
from pathlib import Path
import os
import tempfile
import time
from extended_c import Compiler,Diagnostic,to_report
from extended_c.configuration import configuration_args
from phase6.v1.evaluation import fingerprint
from phase6.v2.regions import same_path
from phase6.v3.engine import ast,analyzer_check,overlay_file,mapped_diagnostic,sha
from phase6.v3.execution import LimitReached
from phase6.v3.policy import apply_edits,point_offset,original_offset
from phase6.v4.policy import mask
from phase6.v5.engine import run_detection,DetectionLimits,Controller
from .detectors import scan

CHECKER='alpha.deadcode.UnreachableCode'


def original_boundary(position,edits):
    mapped=original_offset(position,edits)
    if mapped is not None:return mapped
    shift=0
    for edit in sorted(edits,key=lambda e:e['original_offset']):
        if position==edit['original_offset']+shift:return edit['original_offset']
        shift+=1
    raise ValueError('unmapped source boundary')


def run_semantics(source,*,enabled=False,compiler='auto',standard=None,include_dirs=(),defines=(),
                  repair=False,isolate=False,limits=None,capability=None,max_findings=64):
    limits=limits or DetectionLimits(invocations=96,analyzer_invocations=20)
    limits.validate()
    if type(max_findings) is not int or not 1<=max_findings<=128:raise ValueError('max_findings must be 1..128')
    started=time.monotonic();path=Path(source).resolve();original=path.read_bytes()
    config=configuration_args(standard,include_dirs,defines)
    upstream=run_detection(path,enabled=enabled,compiler=compiler,standard=standard,include_dirs=include_dirs,
                           defines=defines,repair=repair,isolate=isolate,limits=limits,capability=capability)
    r={'schema':'smartparse.semantic_analysis','schema_version':'1.0','source':{'path':str(path),'sha256':sha(original)},
       'enabled':enabled,'status':'not_attempted','reason':'semantic analysis not requested','upstream':upstream,
       'provenance':upstream['provenance'],'findings':[],'inventory':None,'additional_backend':None,'checker_capability':None,
       'function_path_coverage_certified':False}
    controller=None;directory=None
    try:
        if not enabled:return r
        r['status']='blocked'
        if upstream['status'] in ('failed','timed_out','budget_exhausted'):raise ValueError('upstream unavailable/incomplete: '+upstream['reason'])
        if not upstream.get('eligibility') or not upstream['eligibility']['stages']['compiler']['frontend_accepted']:
            r['reason']='Frontend rejected snapshot; no custom semantic analysis of invalid AST regions.';return r
        cap=upstream['capabilities'];c=cap['compiler'];selected=Compiler(c['path'],c['backend'],c['version'],tuple(c['flags']))
        if selected.backend!='clang':raise ValueError('physical semantic AST requires selected Clang')
        controller=Controller(limits,upstream['usage']['compiler_invocations'],upstream['usage']['analyzer_invocations'],
                              limits.total_seconds-(time.monotonic()-started))
        v4=upstream['upstream'];v3=v4['recovery_report'];variants=v3['recovery']['accepted_variants'];edits=variants[-1]['edits'] if variants else []
        current=apply_edits(original,edits)
        if r['provenance']['isolation_conditioned']:current=mask(current,v4['isolation']['excluded_functions'])
        with tempfile.TemporaryDirectory(prefix='smartparse-semantic-') as work:
            directory=work;overlay=[]
            if edits or r['provenance']['isolation_conditioned']:
                private=Path(work)/'snapshot.c';private.write_bytes(current);overlay=overlay_file(work,'snapshot',path,private)
            tree,code=ast(controller,selected,path,config,overlay)
            if code:raise ValueError('AST frontend did not accept snapshot')
            records,inventory=scan(tree,path,current,controller.budget.check)
            r['inventory']=inventory
            if len(records)>max_findings:raise LimitReached('semantic finding budget exceeded; no truncated success')
            support=list(upstream['analysis']['diagnostics'])
            available=CHECKER in cap['available'];r['checker_capability']={'checker':CHECKER,'advertised':available,'supported':False,'experimental':True}
            if available:
                p=controller.call('semantic_checker_capability',[selected.path,'--analyze','-x','c',*config,'-Xclang','-analyzer-checker='+CHECKER,'-Xanalyzer','-analyzer-output=text','-o',os.devnull,'-'],b'int probe;\n')
                r['checker_capability'].update(supported=p.returncode==0 and not p.stderr.strip(),stderr=p.stderr.decode('utf-8',errors='replace'))
                if r['checker_capability']['supported']:
                    extra=analyzer_check(controller,selected,path,(*config,'-Xclang','-analyzer-checker='+CHECKER),overlay)
                    r['additional_backend']=to_report(extra)
                    if extra.status=='completed':support += [asdict(d) for d in extra.findings if d.severity=='warning' and d.diagnostic_id==CHECKER]
            for record in records:
                start=record['start_byte'];line=current.count(b'\n',0,start)+1;column=start-(current.rfind(b'\n',0,start)+1)+1
                rid=record['rule_id'];proof=record['proof'];witnesses=[];existing=[]
                statement=record['statement_range'];left=statement['begin']['offset'];right=statement['end']['offset']+statement['end']['tokLen']
                for d in support:
                    if d['severity']!='warning' or not same_path(d['file'],str(path)) or not d['line'] or not d['column']:continue
                    at=point_offset(current,d['line'],d['column']);identifier=d.get('diagnostic_id')
                    matches=(rid.endswith('contradictory_int_conjunction') and identifier in ('-Wtautological-overlap-compare','-Wlogical-op',CHECKER))
                    matches |= (rid.endswith('fixed_buffer_input') and identifier=='-Wfortify-source' and all(word in d['message'].lower() for word in ('scanf','overflow','size')))
                    if matches and left<=at<right:
                        witnesses.append(d)
                        if identifier!=CHECKER:existing.append(d)
                message=('Signed-int constraints have an empty intersection; this condition cannot be true.' if rid.endswith('contradictory_int_conjunction') else proof['explanation'])
                diagnostic=Diagnostic(str(path),line,column,'warning',message,'smartparse-semantic-ast',record['category'],
                                      current.splitlines()[line-1].decode('utf-8',errors='replace'),rid)
                evidence=mapped_diagnostic(diagnostic,path,current,original,edits)
                evidence['physical_range']={'coordinate_space':'snapshot-bytes','start_byte':start,'end_byte_exclusive':record['end_byte_exclusive']}
                evidence['original_range']={'coordinate_space':'original-bytes','start_byte':original_boundary(start,edits),
                                            'end_byte_exclusive':original_boundary(record['end_byte_exclusive'],edits)}
                finding={'id':'S-'+fingerprint([rid,evidence.get('original_location'),sha(original)])[:20],
                         'evidence':evidence,'function':record['function'],'proof':proof,'confidence':record['confidence'],
                         'provenance':r['provenance'],'backend_witnesses':witnesses,'duplicate_of_existing':bool(existing),
                         'eligibility':'validated_main_file_function_and_accepted_frontend',
                         'adjudication':'unreviewed','confirmed_programmer_intent_bug':False}
                r['findings'].append(finding)
            r.update(status='completed',reason='Bounded semantic AST scan completed; no full path/logic coverage claim.')
            if r['additional_backend'] and r['additional_backend']['status']!='completed':
                r.update(status='partial',reason='AST scan completed; optional unreachable-code backend incomplete.')
    except LimitReached as error:r.update(status='timed_out' if 'timed out' in str(error) else 'budget_exhausted',reason=str(error),findings=[])
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,AttributeError,RecursionError) as error:r.update(status='failed',reason=str(error),findings=[])
    finally:
        try:r['source']['original_unchanged']=path.read_bytes()==original
        except OSError:r['source']['original_unchanged']=False
        r['temporary_workspace_removed']=directory is None or not Path(directory).exists()
        calls=controller.budget.calls if controller else []
        r['usage']={'compiler_invocations':upstream['usage']['compiler_invocations']+len(calls),
                    'analyzer_invocations':upstream['usage']['analyzer_invocations']+sum('--analyze' in c['command'] for c in calls),
                    'elapsed_seconds':round(time.monotonic()-started,6),'calls':calls,'limits':asdict(limits),
                    'max_findings':max_findings,'max_ast_nodes':100000,'max_conjunction_terms':8}
        if not r['source']['original_unchanged'] or not r['temporary_workspace_removed']:
            r.update(status='failed',reason='source preservation/cleanup not verified',findings=[])
    return r
