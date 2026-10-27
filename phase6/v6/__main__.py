import argparse
import json
import sys
from .engine import run_semantics
from phase6.v5.engine import DetectionLimits
from extended_c.configuration import configuration_args


def main(argv=None):
    p=argparse.ArgumentParser(description='Opt-in bounded semantic facts and review suggestions; no C execution.')
    p.add_argument('source');p.add_argument('--semantic-analysis',action='store_true');p.add_argument('--compiler',default='auto');p.add_argument('--std')
    p.add_argument('-I',dest='include_dirs',action='append',default=[]);p.add_argument('-D',dest='defines',action='append',default=[])
    p.add_argument('--punctuation-recovery',action='store_true');p.add_argument('--isolate-unaffected',action='store_true')
    p.add_argument('--total-timeout',type=float,default=120);p.add_argument('--timeout',type=float,default=10)
    p.add_argument('--max-invocations',type=int,default=96);p.add_argument('--max-analyzer-invocations',type=int,default=20)
    p.add_argument('--max-findings',type=int,default=64);p.add_argument('--json',action='store_true');a=p.parse_args(argv)
    limits=DetectionLimits(invocations=a.max_invocations,analyzer_invocations=a.max_analyzer_invocations,total_seconds=a.total_timeout,call_seconds=a.timeout)
    try:
        limits.validate();configuration_args(a.std,a.include_dirs,a.defines)
        if not 1<=a.max_findings<=128:raise ValueError('max-findings must be 1..128')
    except ValueError as e:p.error(str(e))
    try:r=run_semantics(a.source,enabled=a.semantic_analysis,compiler=a.compiler,standard=a.std,include_dirs=a.include_dirs,defines=a.defines,
                       repair=a.punctuation_recovery,isolate=a.isolate_unaffected,limits=limits,max_findings=a.max_findings)
    except (OSError,ValueError) as e:r={'schema':'smartparse.semantic_analysis','schema_version':'1.0','failure':str(e)}
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
    if a.json:print(json.dumps(r,indent=2,ensure_ascii=False))
    elif 'failure' in r:print('Tool failure: '+r['failure'])
    else:
        print('Semantic analysis: '+r['status']+'; '+r['reason'])
        for f in r['findings']:
            d=f['evidence'];print(f"{d['file']}:{d['line']}:{d['column']}: {d['message']} [{d['diagnostic_id']}] ({f['confidence']}; existing root: {f['duplicate_of_existing']})")
        print('Review suggestions are not confirmed bugs; conditioning: '+json.dumps(r['provenance']))
    if 'failure' in r:return 3
    if not r['source']['original_unchanged'] or not r['temporary_workspace_removed']:return 3
    if a.semantic_analysis and r['status']!='completed':return 3
    base=r['upstream']['upstream']['recovery_report']['baseline']
    if not base:return 3
    return 1 if base['analysis']['summary']['errors'] else 0


if __name__=='__main__':sys.exit(main())
