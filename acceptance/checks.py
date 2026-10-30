"""Acceptance-only checks; no dependency on compiler message categorization."""
import re


def clean_numbered_source(data):
    """Strip display prefixes only when every nonblank line agrees with its row.

    Keep byte encoding, line endings, blank lines, and exactly one physical row
    per original row. Refuse gaps/mismatches instead of silently remapping code.
    """
    lines = data.splitlines(keepends=True)
    pattern = re.compile(rb'^[ \t]*([0-9]+)[ \t]*\| ?')
    numbered = any(pattern.match(line) for line in lines)
    if not numbered:
        return data, False
    cleaned = []
    for row, line in enumerate(lines, 1):
        match = pattern.match(line)
        if match:
            if int(match.group(1)) != row:
                raise ValueError(f'Numbered prefix does not match physical line {row}')
            cleaned.append(line[match.end():])
        elif line.strip():
            raise ValueError(f'Mixed numbered/non-numbered content at line {row}')
        else:
            cleaned.append(line)
    return b''.join(cleaned), True


def validate_report(report):
    """Validate schema 1.0 fields, types, enums, and summary consistency.

    Deliberately independent acceptance assertions, not runtime normalization.
    Additive fields are allowed by the documented schema contract.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def strings(value):
        return isinstance(value, list) and all(isinstance(item, str) for item in value)

    def diagnostics(value, summary):
        require(isinstance(value, list), 'diagnostics must be an array')
        keys = {'file', 'line', 'column', 'severity', 'category', 'message', 'source_snippet', 'backend', 'diagnostic_id'}
        categories = ('syntax', 'semantic/type', 'compiler warning', 'unknown')
        for d in value:
            require(isinstance(d, dict) and keys <= d.keys(), 'missing diagnostic fields')
            for key in ('file', 'source_snippet', 'diagnostic_id'):
                require(d[key] is None or isinstance(d[key], str), f'invalid {key}')
            for key in ('line', 'column'):
                require(d[key] is None or (type(d[key]) is int and d[key] > 0), f'invalid {key}')
            require(d['severity'] in ('error', 'fatal error', 'warning', 'note'), 'invalid severity')
            require(d['category'] in categories, 'invalid category')
            require(isinstance(d['message'], str), 'invalid message')
            require(d['backend'] in ('gcc', 'clang', 'clang-static-analyzer'), 'invalid backend')
        expected = {
            'total_diagnostics': len(value),
            'errors': sum(d['severity'] in ('error', 'fatal error') for d in value),
            'warnings': sum(d['severity'] == 'warning' for d in value),
            'notes': sum(d['severity'] == 'note' for d in value),
            'categories': {c: sum(d['category'] == c for d in value) for c in categories},
        }
        require(summary == expected, 'summary does not match diagnostics')

    keys = {'schema_version', 'analysis_mode', 'status', 'compiler', 'summary', 'diagnostics', 'tool_issues', 'execution', 'raw_output', 'unrecognized_output'}
    require(isinstance(report, dict) and keys <= report.keys(), 'missing report fields')
    require(report['schema_version'] == '1.0', 'unexpected schema version')
    require(report['analysis_mode'] in ('extended_c', 'clang_static_analyzer'), 'invalid mode')
    require(report['status'] in ('completed', 'failed', 'partial', 'timed_out', 'unavailable'), 'invalid status')
    compiler = report['compiler']
    if compiler is not None:
        require(isinstance(compiler, dict), 'invalid compiler')
        require(all(isinstance(compiler.get(k), str) for k in ('path', 'backend', 'version')), 'invalid compiler metadata')
        require(strings(compiler.get('flags')), 'invalid compiler flags')
    require(strings(report['tool_issues']) and strings(report['unrecognized_output']), 'invalid issue arrays')
    execution = report['execution']
    require(isinstance(execution, dict) and strings(execution.get('command')), 'invalid command')
    require('returncode' in execution and (execution['returncode'] is None or type(execution['returncode']) is int), 'invalid return code')
    require(isinstance(report['raw_output'], dict) and all(isinstance(report['raw_output'].get(k), str) for k in ('stdout', 'stderr')), 'invalid raw output')
    diagnostics(report['diagnostics'], report['summary'])
    if report['analysis_mode'] == 'clang_static_analyzer':
        require('findings' in report and 'findings_summary' in report, 'missing analyzer findings')
        diagnostics(report['findings'], report['findings_summary'])
        require(all(d['backend'] == 'clang-static-analyzer' for d in report['findings']), 'wrong findings source')
    if 'static_analysis' in report:
        validate_report(report['static_analysis'])
        require(report['static_analysis']['analysis_mode'] == 'clang_static_analyzer', 'wrong analyzer mode')
    return True
