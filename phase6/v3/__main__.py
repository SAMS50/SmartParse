"""Separate opt-in CLI; no changes to existing commands or schemas."""
import argparse
import json
import sys
from .engine import run_recovery
from .execution import Limits
from extended_c.configuration import configuration_args


def main(argv=None):
    parser=argparse.ArgumentParser(description='Bounded punctuation recovery for analysis; no original-source edits.')
    parser.add_argument('source')
    parser.add_argument('--compiler',default='auto',help='auto, clang, gcc, or explicit driver path')
    parser.add_argument('--std',dest='standard')
    parser.add_argument('-I','--include-dir',dest='include_dirs',action='append',default=[])
    parser.add_argument('-D','--define',dest='defines',action='append',default=[])
    parser.add_argument('--static-analysis',action='store_true',help='use the selected Clang driver; no silent analyzer fallback')
    parser.add_argument('--repair-for-analysis',action='store_true',help='explicitly enable temporary semicolon variants')
    parser.add_argument('--max-candidates',type=int,default=4)
    parser.add_argument('--max-rounds',type=int,default=3)
    parser.add_argument('--max-invocations',type=int,default=48)
    parser.add_argument('--max-variants',type=int,default=4)
    parser.add_argument('--max-edits',type=int,default=4)
    parser.add_argument('--total-timeout',type=float,default=90)
    parser.add_argument('--timeout',type=float,default=10,help='per compiler call, clamped to remaining total time')
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args(argv)
    limits=Limits(args.max_candidates,args.max_rounds,args.max_invocations,args.max_variants,args.max_edits,args.total_timeout,args.timeout)
    try:
        limits.validate()
        configuration_args(args.standard,args.include_dirs,args.defines)
    except ValueError as error:parser.error(str(error))
    try:
        report=run_recovery(args.source,repair=args.repair_for_analysis,compiler=args.compiler,standard=args.standard,
                            include_dirs=args.include_dirs,defines=args.defines,static_analysis=args.static_analysis,limits=limits)
    except (OSError,ValueError) as error:
        report={'schema':'smartparse.repair_for_analysis','schema_version':'1.0','failure':str(error)}
    if args.json:text=json.dumps(report,indent=2,ensure_ascii=False)
    elif 'failure' in report:text='Recovery tool failure: '+report['failure']
    else:
        recovery=report['recovery'];baseline=report['baseline']
        text='Bounded recovery for analysis (original source unchanged: '+str(report['source']['original_unchanged'])+')\n'
        text+='Baseline compiler: '+(baseline['analysis']['status'] if baseline else 'not captured')+'\n'
        text+='Accepted temporary variants: '+str(len(recovery['accepted_variants']))+'\n'
        for candidate in recovery['candidates']:
            text+=f"{candidate['id']}: {candidate['status']} — {candidate['reason']}\n"
        text+='Stop: '+str(recovery['stop_reason'])+'\n'
        text+='Eligibility: '+json.dumps(recovery['eligibility_change'])+'\n'
        text+='Variant findings are repair-conditioned, never baseline facts.'
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
    try:print(text)
    except OSError:return 3
    if 'failure' in report or report['baseline'] is None or not report['source']['original_unchanged']:return 3
    if report['recovery']['budget_exhausted'] or not report['recovery']['temporary_workspace_removed']:return 3
    effective=(report['recovery']['accepted_variants'][-1]['eligibility']['analysis']
               if report['recovery']['accepted_variants'] else report['baseline']['analysis'])
    if args.static_analysis and effective.get('static_analysis',{}).get('status')!='completed':return 3
    # Preserve baseline rejection even if a temporary variant becomes analyzable.
    if report['baseline']['analysis']['status']!='completed':return 3
    if any(d['severity'] in ('error','fatal error') for d in report['baseline']['analysis']['diagnostics']):return 1
    return 0


if __name__=='__main__':sys.exit(main())
