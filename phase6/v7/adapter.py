"""Only the source-reviewed selected profiles; disabled unless requested."""
import json
from pathlib import Path
from .experiment import run_case

HERE=Path(__file__).resolve().parent


def analyze_external(source,*,enabled=False,tool='gcc14',executable=None,total_timeout=30,timeout=10,
                     invocation_budget=4,standard='c11',include_dirs=(),defines=(),provenance=None):
    if not enabled:return {'schema':'smartparse.external_analysis','schema_version':'1.0','enabled':False,'status':'not_attempted','diagnostics':[],
                           'reason':'External analysis must be explicitly requested.','usage':{'compiler_invocations':0}}
    decision=json.loads((HERE/'integration_decision.json').read_text())
    if tool not in decision['selected']:raise ValueError('tool is comparison-only or not reviewed for integration')
    if provenance and any(provenance.get(k) for k in ('repair_conditioned','isolation_conditioned')):
        return {'schema':'smartparse.external_analysis','schema_version':'1.0','enabled':True,'status':'unsupported','diagnostics':[],
                'provenance':provenance,'reason':'This adapter supports original files only; conditioned mapping is not implemented or flattened.',
                'usage':{'compiler_invocations':0}}
    selected=next(t.copy() for t in json.loads((HERE/'catalog.json').read_text()) if t['id']==tool)
    if executable is not None:selected['path']=str(Path(executable).resolve())
    r=run_case(selected,source,timeout=total_timeout,call_timeout=timeout,invocations=invocation_budget,
               standard=standard,includes=include_dirs,defines=defines,capability_probe=True)
    r.update(schema='smartparse.external_analysis',enabled=True,confirmed_defect_roots=None,
             analysis_mode='original_source_only',integration_decision=decision['schema_version'])
    return r
