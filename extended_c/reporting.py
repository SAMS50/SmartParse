"""Versioned reports containing external compiler evidence only."""
from dataclasses import asdict
import json

SCHEMA_VERSION = '1.0'
CATEGORIES = ('syntax', 'semantic/type', 'compiler warning', 'unknown')


def _summary(diagnostics):
    return {
        'total_diagnostics': len(diagnostics),
        'errors': sum(d['severity'] in ('error', 'fatal error') for d in diagnostics),
        'warnings': sum(d['severity'] == 'warning' for d in diagnostics),
        'notes': sum(d['severity'] == 'note' for d in diagnostics),
        'categories': {c: sum(d['category'] == c for d in diagnostics) for c in CATEGORIES},
    }


def to_report(result):
    diagnostics = [asdict(d) for d in result.diagnostics]
    compiler = asdict(result.compiler) if result.compiler else None
    if compiler:
        compiler['flags'] = list(compiler['flags'])
    report = {
        'schema_version': SCHEMA_VERSION,
        'analysis_mode': 'extended_c',
        'status': result.status,
        'compiler': compiler,
        'summary': _summary(diagnostics),
        'diagnostics': diagnostics,
        'tool_issues': list(result.issues),
        'execution': {'returncode': result.returncode, 'command': list(result.command)},
        'raw_output': {'stdout': result.stdout, 'stderr': result.stderr},
        'unrecognized_output': list(result.unrecognized_output),
    }
    if result.findings is not None:
        report['analysis_mode'] = 'clang_static_analyzer'
        report['findings'] = [asdict(d) for d in result.findings]
        report['findings_summary'] = _summary(report['findings'])
    if result.static_analysis is not None:
        report['static_analysis'] = to_report(result.static_analysis)
    return report


def to_json(result, *, indent=2):
    return json.dumps(to_report(result), ensure_ascii=False, indent=indent, allow_nan=False)


def _safe(text):
    # Keep diagnostic output from introducing terminal control sequences.
    return ''.join(c if c.isprintable() or c == '\n' else f'\\x{ord(c):02x}' for c in str(text))


def format_terminal(result):
    report = to_report(result)
    compiler = result.compiler
    label = 'Clang Static Analyzer' if result.findings is not None else 'Extended C Analysis (external compiler)'
    lines = [f'{label}: {result.status}',
             f'Compiler: {compiler.version if compiler else "unavailable"}']
    if compiler:
        lines.append(f'Backend: {compiler.backend}; executable: {compiler.path}')
    for diagnostic in result.diagnostics + (result.findings or []):
        location = diagnostic.file or '<no location>'
        if diagnostic.line is not None:
            location += f':{diagnostic.line}'
        if diagnostic.column is not None:
            location += f':{diagnostic.column}'
        identifier = f' [{diagnostic.diagnostic_id}]' if diagnostic.diagnostic_id else ''
        lines.append(f'{location}: {diagnostic.severity} ({diagnostic.category}, {diagnostic.backend}): {diagnostic.message}{identifier}')
        if diagnostic.source_snippet is not None:
            lines.append('    ' + diagnostic.source_snippet)
    summary = report['summary']
    lines.append(f'Total: {summary["errors"]} errors, {summary["warnings"]} warnings, {summary["notes"]} notes')
    lines.append('Categories: ' + ', '.join(f'{key}={value}' for key, value in summary['categories'].items()))
    if result.findings is not None:
        counts = report['findings_summary']
        lines.append(f'Potential static-analysis findings: {counts["warnings"]}; path notes: {counts["notes"]} (separate from compiler totals)')
        lines.append('Unavailable analysis or zero findings does not establish that the source is bug-free.')
    for issue in result.issues:
        lines.append(f'Tool issue: {issue}')
    if result.unrecognized_output:
        lines.append(f'Unrecognized compiler output: {len(result.unrecognized_output)} lines (retained in JSON/raw output)')
    lines.append('Completion does not establish absence of runtime or logic bugs.')
    if result.static_analysis is not None:
        lines.append('\n' + format_terminal(result.static_analysis))
    return _safe('\n'.join(lines))
