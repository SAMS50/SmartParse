"""Extended C Analysis CLI. Original SmartParse/CGAR commands are independent."""
import argparse
import math
import sys

from extended_c import AnalysisResult, analyze_file, format_terminal, to_json
from extended_c.configuration import configuration_args


def positive_timeout(value):
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError('timeout must be a positive finite number')
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('timeout must be a positive finite number')
    return number


def build_parser():
    parser = argparse.ArgumentParser(description='Extended C Analysis using external GCC/Clang; no binary execution.')
    parser.add_argument('source', help='.c file path (quote paths containing spaces)')
    parser.add_argument('--compiler', default='auto', help='auto, gcc, clang, or a compiler executable path')
    parser.add_argument('--std', '--standard', dest='standard', help='C dialect supported by the selected compiler, e.g. c11')
    parser.add_argument('-I', '--include-dir', dest='include_dirs', action='append', default=[], help='include directory; repeatable')
    parser.add_argument('-D', '--define', dest='defines', action='append', default=[], help='NAME or NAME=VALUE; repeatable')
    parser.add_argument('--timeout', type=positive_timeout, default=30.0, help='analysis timeout in seconds (default: 30)')
    parser.add_argument('--discovery-timeout', type=positive_timeout, default=5.0, help='timeout per capability probe (default: 5)')
    parser.add_argument('--static-analysis', action='store_true', help='explicitly request independent Clang Static Analyzer pass')
    parser.add_argument('--analyzer-executable', help='explicit Clang executable for static analysis')
    parser.add_argument('--analyzer-timeout', type=positive_timeout, help='static analysis timeout (defaults to --timeout)')
    output = parser.add_mutually_exclusive_group()
    output.add_argument('--format', choices=('terminal', 'json'), default='terminal')
    output.add_argument('--json', dest='format', action='store_const', const='json', help='emit schema 1.0 JSON to stdout')
    return parser


def exit_code(result):
    passes = [result] + ([result.static_analysis] if result.static_analysis is not None else [])
    if any(item.status != 'completed' for item in passes):
        return 3
    if any(d.severity in ('error', 'fatal error') for item in passes for d in item.diagnostics):
        return 1
    if any(d.severity != 'note' for item in passes for d in (item.findings or [])):
        return 1
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        configuration_args(args.standard, args.include_dirs, args.defines)
    except ValueError as error:
        parser.error(str(error))
    if not args.static_analysis and (args.analyzer_executable or args.analyzer_timeout is not None):
        parser.error('analyzer options require --static-analysis')
    preference = args.compiler if args.compiler in ('auto', 'gcc', 'clang') else 'auto'
    executable = None if args.compiler in ('auto', 'gcc', 'clang') else args.compiler
    try:
        result = analyze_file(args.source, preference=preference, executable=executable,
                              standard=args.standard, include_dirs=args.include_dirs, defines=args.defines,
                              timeout=args.timeout, discovery_timeout=args.discovery_timeout,
                              static_analysis=args.static_analysis, analyzer_executable=args.analyzer_executable,
                              analyzer_timeout=args.analyzer_timeout if args.analyzer_timeout is not None else args.timeout)
    except (OSError, ValueError, RuntimeError) as error:
        result = AnalysisResult('failed', issues=[str(error)])
    text = to_json(result) if args.format == 'json' else format_terminal(result)
    if args.format != 'json' and result.static_analysis is None:
        text += '\nClang Static Analyzer: not requested (availability not probed)'
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='backslashreplace')
        print(text)
    except OSError:
        return 3
    return exit_code(result)


if __name__ == '__main__':
    sys.exit(main())
