"""Separate opt-in CLI; existing analyze_c.py and report schema remain untouched."""
import json
import sys

from analyze_c import build_parser, exit_code, positive_timeout
from extended_c import format_terminal
from .eligibility import analyze_eligibility


def main(argv=None):
    parser=build_parser()
    parser.description='Opt-in analysis eligibility and build-context manifest. No source repair.'
    parser.add_argument('--metadata-timeout',type=positive_timeout,default=5.0,help='timeout for each metadata/preprocessing/AST query')
    args=parser.parse_args(argv)
    if not args.static_analysis and (args.analyzer_executable or args.analyzer_timeout is not None):
        parser.error('analyzer options require --static-analysis')
    compiler=args.compiler
    try:
        report,result=analyze_eligibility(args.source,preference=compiler if compiler in ('auto','gcc','clang') else 'auto',
                      executable=None if compiler in ('auto','gcc','clang') else compiler,
                      timeout=args.timeout,discovery_timeout=args.discovery_timeout,
                      standard=args.standard,include_dirs=args.include_dirs,defines=args.defines,
                      static_analysis=args.static_analysis,analyzer_executable=args.analyzer_executable,
                      analyzer_timeout=args.analyzer_timeout or args.timeout,metadata_timeout=args.metadata_timeout)
    except (ValueError,OSError) as error:
        parser.error(str(error))
    if args.format=='json': text=json.dumps(report,indent=2,ensure_ascii=False)
    else:
        text=format_terminal(result)+'\n\nEligibility (configured source only):\n'
        text+='Compiler completion: '+report['stages']['compiler']['completion']+'; analyzer completion: '+report['stages']['analyzer']['completion']+'\n'
        text+='Blockers: '+', '.join(sorted({b['category'] for b in report['blockers']}))+'\n'
        text+='Region inventory: '+report['region_inventory']['status']+'\n'
        for region in report['regions']:
            text+=f"{region['name'] or region['kind']}: compiler={region['compiler_coverage']['status']}; analyzer={region['analyzer_coverage']['status']}\n"
        text+='Completed invocation is not proof of exhaustive function/path coverage.'
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(errors='backslashreplace')
    try: print(text)
    except OSError: return 3
    return 3 if report['manifest']['source']['original_source_unchanged'] is False else exit_code(result)


if __name__=='__main__': sys.exit(main())
