import argparse
import json
import sys
from .adapter import analyze_external
from phase6.v3.execution import Limits
from extended_c.configuration import configuration_args


def main(argv=None):
    p=argparse.ArgumentParser(description='Opt-in selected external analyzers; source review required.')
    p.add_argument('source');p.add_argument('--external-analysis',action='store_true');p.add_argument('--tool',choices=('gcc14','cppcheck'),default='gcc14')
    p.add_argument('--executable');p.add_argument('--std',default='c11');p.add_argument('-I',dest='includes',action='append',default=[]);p.add_argument('-D',dest='defines',action='append',default=[])
    p.add_argument('--total-timeout',type=float,default=30);p.add_argument('--timeout',type=float,default=10);p.add_argument('--max-invocations',type=int,default=4)
    p.add_argument('--json',action='store_true');a=p.parse_args(argv)
    try:
        configuration_args(a.std,a.includes,a.defines)
        Limits(invocations=a.max_invocations,total_seconds=a.total_timeout,call_seconds=a.timeout).validate()
    except ValueError as e:p.error(str(e))
    try:r=analyze_external(a.source,enabled=a.external_analysis,tool=a.tool,executable=a.executable,standard=a.std,
                          total_timeout=a.total_timeout,timeout=a.timeout,invocation_budget=a.max_invocations,include_dirs=a.includes,defines=a.defines)
    except (OSError,ValueError) as e:r={'schema':'smartparse.external_analysis','schema_version':'1.0','status':'failed','reason':str(e),'diagnostics':[]}
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
    if a.json:print(json.dumps(r,indent=2,ensure_ascii=False))
    else:
        print('External analysis: '+r['status']+'; '+str(r.get('reason')))
        for d in r['diagnostics']:print(f"{d['file']}:{d['line']}:{d['column']}: {d['severity']}: {d['message']} [{d['diagnostic_id']}]")
        print('Tool reports are not confirmed defect roots; function/path coverage is unknown.')
    if r['status']=='not_attempted':return 0
    if r['status']!='completed':return 3
    return 1 if any(d['severity'] in ('warning','error','fatal error') and not d.get('context_note') for d in r['diagnostics']) else 0


if __name__=='__main__':sys.exit(main())
