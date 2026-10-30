"""Separate experimental CLI; isolation must be explicitly enabled."""
import argparse
import json
import sys
from .engine import run_isolation,IsolationLimits
from extended_c.configuration import configuration_args


def main(argv=None):
    p=argparse.ArgumentParser(description='Experimental unaffected-region analysis; originals unchanged.')
    p.add_argument('source');p.add_argument('--compiler',default='auto');p.add_argument('--std')
    p.add_argument('-I',dest='include_dirs',action='append',default=[])
    p.add_argument('-D',dest='defines',action='append',default=[])
    p.add_argument('--isolate-unaffected',action='store_true',help='explicit opt-in; requests Clang Static Analyzer')
    p.add_argument('--punctuation-recovery',action='store_true',help='separate opt-in v3 preprocessing stage')
    p.add_argument('--max-exclusions',type=int,default=8);p.add_argument('--max-invocations',type=int,default=64)
    p.add_argument('--max-analyzer-invocations',type=int,default=5)
    p.add_argument('--total-timeout',type=float,default=120);p.add_argument('--timeout',type=float,default=10)
    p.add_argument('--json',action='store_true');a=p.parse_args(argv)
    limits=IsolationLimits(exclusions=a.max_exclusions,invocations=a.max_invocations,
                           analyzer_invocations=a.max_analyzer_invocations,total_seconds=a.total_timeout,call_seconds=a.timeout)
    try:limits.validate();configuration_args(a.std,a.include_dirs,a.defines)
    except ValueError as error:p.error(str(error))
    try:r=run_isolation(a.source,isolate=a.isolate_unaffected,repair=a.punctuation_recovery,compiler=a.compiler,
                       standard=a.std,include_dirs=a.include_dirs,defines=a.defines,limits=limits)
    except (OSError,ValueError) as error:r={'schema':'smartparse.unaffected_regions','schema_version':'1.0','failure':str(error)}
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
    if a.json:print(json.dumps(r,ensure_ascii=False,indent=2))
    elif 'failure' in r:print('Tool failure: '+r['failure'])
    else:
        i=r['isolation'];print('Experimental isolation: '+i['status']+'; '+str(i['reason']))
        for f in i['excluded_functions']:print('Excluded '+f['name']+': '+'; '.join(f['exclusion_reasons']))
        print('Additional unique conditioned analyzer warnings: '+str(len(r['unique_additional_findings'])))
        print('Function/path coverage is not certified. Original source unchanged: '+str(r['source']['original_unchanged']))
    if 'failure' in r:return 3
    i=r['isolation'];b=r['recovery_report']['baseline']
    if not b or not r['source']['original_unchanged'] or not i['temporary_workspace_removed']:return 3
    unnecessary=i['reason']=='frontend already accepted; isolation unnecessary' and (r.get('baseline_static_analysis') or {}).get('status')=='completed'
    if a.isolate_unaffected and i['status']!='completed' and not unnecessary:return 3
    if any(d['severity'] in ('error','fatal error') for d in b['analysis']['diagnostics']):return 1
    return 0 if b['analysis']['status']=='completed' else 3


if __name__=='__main__':sys.exit(main())
