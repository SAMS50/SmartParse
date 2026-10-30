"""No custom detectors: bounded, measured checker configuration with provenance."""
from dataclasses import dataclass,asdict,replace
import os
from pathlib import Path
import tempfile
import time
from extended_c import Compiler,to_report
from extended_c.configuration import configuration_args
from phase6.v1.evaluation import fingerprint
from phase6.v2.regions import same_path
from phase6.v3.execution import Budget,Limits,LimitReached
from phase6.v3.engine import compiler_check,analyzer_check,ast,eligibility,overlay_file,mapped_diagnostic,sha
from phase6.v3.policy import apply_edits,point_offset
from phase6.v4.engine import run_isolation,IsolationLimits
from phase6.v4.policy import mask
from .capabilities import audit,selected_options,CHECKERS


@dataclass(frozen=True)
class DetectionLimits:
    invocations:int=80
    analyzer_invocations:int=16
    checkers:int=4
    total_seconds:float=120
    call_seconds:float=10

    def validate(self):
        import math
        for name,cap in [('invocations',120),('analyzer_invocations',20),('checkers',4)]:
            value=getattr(self,name)
            if type(value) is not int or not 1<=value<=cap:raise ValueError(f'{name} must be 1..{cap}')
        for name,cap in [('total_seconds',120),('call_seconds',30)]:
            value=getattr(self,name)
            if not math.isfinite(value) or not 0<value<=cap:raise ValueError(f'{name} must be positive and <= {cap}')


class Controller:
    def __init__(self,limits,prior_calls,prior_analyzers,remaining):
        self.limits=limits;self.prior=prior_calls;self.analyzers=prior_analyzers
        allowance=min(80,limits.invocations-prior_calls)
        if allowance<1 or remaining<=0:raise LimitReached('combined detection budget exhausted')
        self.budget=Budget(Limits(invocations=allowance,total_seconds=remaining,call_seconds=limits.call_seconds))
    def call(self,role,command,data=None):
        if '--analyze' in command:
            if self.analyzers>=self.limits.analyzer_invocations:raise LimitReached('analyzer invocation budget exhausted')
            self.analyzers+=1
        return self.budget.call(role,command,data)


def run_detection(source,*,enabled=False,profile='memory',compiler='auto',standard=None,
                  include_dirs=(),defines=(),repair=False,isolate=False,limits=None,capability=None):
    if profile not in ('baseline','memory'):raise ValueError('profile must be baseline or memory')
    limits=limits or DetectionLimits();limits.validate();started=time.monotonic()
    path=Path(source).resolve();original=path.read_bytes();config=configuration_args(standard,include_dirs,defines)
    upstream=run_isolation(path,isolate=isolate,repair=repair,compiler=compiler,standard=standard,
                           include_dirs=include_dirs,defines=defines,
                           limits=IsolationLimits(invocations=min(64,limits.invocations),analyzer_invocations=min(5,limits.analyzer_invocations),
                                                  total_seconds=limits.total_seconds,call_seconds=limits.call_seconds))
    previous=upstream['isolation']['usage'];controller=None;directory=None
    r={'schema':'smartparse.memory_analysis','schema_version':'1.0','source':{'path':str(path),'sha256':sha(original)},
       'enabled':enabled,'profile':profile,'status':'not_attempted','reason':'memory profile not requested','upstream':upstream,
       'capabilities':None,'baseline_analyzer':None,'analysis':None,'eligibility':None,'observations':[],
       'review_suggestions':[],'unrecognized_or_unmapped_findings':[],
       'provenance':{'repair_conditioned':False,'isolation_conditioned':False,'original_source_modified':False}}
    try:
        if not enabled:return r
        r['status']='failed';base=upstream['recovery_report'];b=base['baseline']
        if not b or not upstream['source']['original_unchanged']:raise ValueError('original baseline/preservation unavailable')
        c=b['analysis']['compiler']
        if c['backend']!='clang':raise ValueError('memory profile requires installed selected Clang; GCC baseline remains available')
        c=Compiler(c['path'],c['backend'],c['version'],tuple(c['flags']))
        controller=Controller(limits,previous['compiler_invocations'],previous['analyzer_invocations'],limits.total_seconds-(time.monotonic()-started))
        if capability is None:capability=audit(controller,c,config)
        checks,warnings=selected_options(capability,c,config)
        if profile=='memory' and len(checks)>limits.checkers:raise LimitReached('checker budget exceeded; no silent truncation')
        r['capabilities']=capability
        # Always preserve the unmodified-source analyzer baseline, never replace
        # it with findings from repaired or isolated snapshots.
        if upstream.get('baseline_static_analysis') is not None:r['baseline_analyzer']=upstream['baseline_static_analysis']
        else:r['baseline_analyzer']=to_report(analyzer_check(controller,c,path,config))
        variants=base['recovery']['accepted_variants'];edits=variants[-1]['edits'] if variants else []
        current=apply_edits(original,edits)
        isolation=upstream['isolation'];iv=isolation.get('variant')
        isolated=bool(iv and iv['status']=='accepted' and isolation['status'] in ('completed','partial'))
        exclusions=isolation['excluded_functions'] if isolated else []
        if isolated:current=mask(current,exclusions)
        r['provenance'].update(repair_conditioned=bool(edits),isolation_conditioned=isolated,
                               recovery_variant_id=variants[-1]['id'] if variants else None,
                               isolation_variant_id=iv['id'] if isolated else None,
                               snapshot_sha256=sha(current),excluded_spans=exclusions,
                               source_map=iv['mapping'] if isolated else variants[-1]['source_map'] if variants else 'identity')
        # Never modify existing default checker algorithms. Optional alpha
        # observations are review suggestions until separately adjudicated.
        extra=[]
        if profile=='memory':
            for checker in checks:extra.extend(['-Xclang','-analyzer-checker='+checker])
        active_warnings=warnings if profile=='memory' else []
        selected=replace(c,flags=tuple(dict.fromkeys((*c.flags,*active_warnings))))
        with tempfile.TemporaryDirectory(prefix='smartparse-memory-') as work:
            directory=work;overlay=[]
            if edits or isolated:
                private=Path(work)/'snapshot.c';private.write_bytes(current)
                overlay=overlay_file(work,'snapshot',path,private)
            result=compiler_check(controller,selected,path,config,overlay)
            result.static_analysis=analyzer_check(controller,c,path,(*config,*extra),overlay)
            tree,code=ast(controller,c,path,config,overlay)
            context=b['eligibility']['manifest'].copy();context.pop('source',None)
            context['memory_profile']={'profile':profile,'checker_options':checks if profile=='memory' else [],
                                       'warning_options':active_warnings,'capability_binding':capability['binding']}
            envelope=eligibility(path,current,result,tree,code,context,analyzer_requested=True,original_sha256=sha(original))
            if isolated:envelope['manifest']['source']['snapshot_kind']='private_isolation_variant'
            envelope['mapping']['conditioning']=r['provenance']
            r['analysis']=to_report(result);r['eligibility']=envelope
            r['status']=result.static_analysis.status
            r['reason']='Analyzer invocation '+r['status']+'; no per-function/path completion claim.'
            group=None
            for diagnostic in result.static_analysis.findings:
                evidence=mapped_diagnostic(diagnostic,path,current,original,edits)
                allowed=True
                if same_path(diagnostic.file,str(path)) and diagnostic.line and diagnostic.column:
                    at=point_offset(current,diagnostic.line,diagnostic.column)
                    allowed=not any(e['start_byte']<=at<e['end_byte_exclusive'] for e in exclusions)
                else:allowed=False
                if diagnostic.severity=='warning':
                    group=None
                    if not allowed:
                        r['unrecognized_or_unmapped_findings'].append(evidence);continue
                    group={'id':'F-'+fingerprint([evidence.get('original_location'),diagnostic.diagnostic_id,diagnostic.message])[:20],
                           'evidence':evidence,'notes':[],'provenance':r['provenance'],
                           'classification':'review_suggestion' if diagnostic.diagnostic_id in CHECKERS else 'backend_supported_potential',
                           'adjudication':'unknown','confirmed_defect':False}
                    # Exact primary observations only; notes are not defects.
                    if any(x['id']==group['id'] for x in r['observations']):group=None;continue
                    r['observations'].append(group)
                elif diagnostic.severity=='note' and group is not None:
                    group['notes'].append(evidence)
                    if not allowed:group['trace_outside_retained_source']=True
            r['observations']=[f for f in r['observations'] if not f.get('trace_outside_retained_source')]
            r['review_suggestions']=[f['id'] for f in r['observations'] if f['classification']=='review_suggestion']
    except LimitReached as error:
        r.update(status='timed_out' if 'timed out' in str(error) else 'budget_exhausted',reason=str(error),observations=[],review_suggestions=[])
    except (ValueError,OSError,RuntimeError,KeyError,TypeError,AttributeError,RecursionError) as error:
        r.update(status='failed',reason=str(error),observations=[],review_suggestions=[])
    finally:
        try:r['source']['original_unchanged']=path.read_bytes()==original
        except OSError:r['source']['original_unchanged']=False
        r['temporary_workspace_removed']=directory is None or not Path(directory).exists()
        r['usage']={'compiler_invocations':previous['compiler_invocations']+(len(controller.budget.calls) if controller else 0),
                    'analyzer_invocations':controller.analyzers if controller else previous['analyzer_invocations'],
                    'elapsed_seconds':round(time.monotonic()-started,6),'calls':controller.budget.calls if controller else [],'limits':asdict(limits)}
        all_calls=(upstream['recovery_report']['recovery']['usage']['calls']+
                   upstream['isolation']['usage']['isolation_calls']+r['usage']['calls'])
        r['usage']['analyzer_slots_used']=r['usage']['analyzer_invocations']
        r['usage']['analyzer_invocations']=sum('--analyze' in call['command'] for call in all_calls)
        r['usage']['completed_subprocesses']=sum(call['status']=='completed' for call in all_calls)
        if not r['source']['original_unchanged'] or not r['temporary_workspace_removed']:
            r.update(status='failed',reason='source preservation/cleanup not verified',observations=[],review_suggestions=[])
    return r


def export_v1_run(report,source_id):
    """v1 cannot express isolation/repair conditioning: prohibit flattening it."""
    if any(report['provenance'][k] for k in ('repair_conditioned','isolation_conditioned')):
        raise ValueError('conditioned evidence must remain a separate provenance-aware evaluation cohort')
    if report['analysis'] is None:raise ValueError('no analysis report')
    if (report['source'].get('original_unchanged') is not True or
            report.get('temporary_workspace_removed') is not True or
            report['status'] in ('failed','timed_out','budget_exhausted')):
        raise ValueError('unverified or failed analysis cannot be exported as source-bound evidence')
    return {'id':'v5-'+source_id+'-'+report['profile'],'source_bindings':{source_id:{'reported_paths':[report['source']['path']], 'sha256':report['source']['sha256']}},
            'coverage':[{'source_id':source_id,'analysis':stage,'status':state,'reason':'Invocation-level coverage only; no function completeness proof.'}
                        for stage,state in [('compiler','completed' if report['analysis']['status']=='completed' else 'blocked'),
                                            ('analyzer','completed' if report['status']=='completed' else 'blocked')]],
            'report':report['analysis']}
