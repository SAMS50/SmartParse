import argparse
import json
import sys
from .engine import run_detection,DetectionLimits
from extended_c.configuration import configuration_args


def main(argv=None):
    p=argparse.ArgumentParser(description='Opt-in evidence-based memory/resource/bounds profile; no source execution.')
    p.add_argument('source');p.add_argument('--compiler',default='auto');p.add_argument('--std')
    p.add_argument('-I',dest='include_dirs',action='append',default=[]);p.add_argument('-D',dest='defines',action='append',default=[])
    p.add_argument('--memory-analysis',action='store_true');p.add_argument('--profile',choices=('baseline','memory'),default='memory')
    p.add_argument('--punctuation-recovery',action='store_true');p.add_argument('--isolate-unaffected',action='store_true')
    p.add_argument('--max-invocations',type=int,default=80);p.add_argument('--max-analyzer-invocations',type=int,default=16)
    p.add_argument('--max-checkers',type=int,default=4);p.add_argument('--total-timeout',type=float,default=120)
    p.add_argument('--timeout',type=float,default=10);p.add_argument('--json',action='store_true');a=p.parse_args(argv)
    limits=DetectionLimits(a.max_invocations,a.max_analyzer_invocations,a.max_checkers,a.total_timeout,a.timeout)
    try:limits.validate();configuration_args(a.std,a.include_dirs,a.defines)
    except ValueError as e:p.error(str(e))
    try:r=run_detection(a.source,enabled=a.memory_analysis,profile=a.profile,compiler=a.compiler,standard=a.std,
                        include_dirs=a.include_dirs,defines=a.defines,repair=a.punctuation_recovery,isolate=a.isolate_unaffected,limits=limits)
    except (OSError,ValueError) as e:r={'schema':'smartparse.memory_analysis','schema_version':'1.0','failure':str(e)}
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
    if a.json:print(json.dumps(r,indent=2,ensure_ascii=False))
    elif 'failure' in r:print('Tool failure: '+r['failure'])
    else:
        print('Memory profile: '+r['status']+'; '+r['reason'])
        print('Conditioning: '+json.dumps(r['provenance']))
        for f in r['observations']:
            d=f['evidence'];print(f"{d['file']}:{d['line']}:{d['column']}: {d['message']} [{d['diagnostic_id']}] ({f['classification']})")
        print('Observations require adjudication; notes are not independent defects.')
    if 'failure' in r:return 3
    if not r['source']['original_unchanged'] or not r['temporary_workspace_removed']:return 3
    if a.memory_analysis and r['status']!='completed':return 3
    b=r['upstream']['recovery_report']['baseline']
    if not b:return 3
    return 1 if b['analysis']['summary']['errors'] else 0


if __name__=='__main__':sys.exit(main())
