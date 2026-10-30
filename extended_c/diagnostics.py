"""Conservative adapters for GCC/Clang text diagnostics; no source writes."""
from dataclasses import dataclass, replace
import re


@dataclass(frozen=True)
class Diagnostic:
    file: str | None
    line: int | None
    column: int | None
    severity: str
    message: str
    backend: str
    category: str = 'unknown'
    source_snippet: str | None = None
    diagnostic_id: str | None = None


_LOCATION = re.compile(r'^(.*?):(\d+)(?::(\d+))?:\s*(fatal error|error|warning|note):\s*(.*)$')
_FILE = re.compile(r'^(.*?):\s*(fatal error|error|warning|note):\s*(.*)$')
_BARE = re.compile(r'^(fatal error|error|warning|note):\s*(.*)$')
_OPTION = re.compile(r'\s+\[(-W[^\],\s]+)(?:,\s*-W[^\]]+)?\]$')
_ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
_CONTEXT = re.compile(r'^(?:In file included from |\s+from .*:\d+|.*: In (?:function|member function|file|instantiation)|\d+ (?:warnings?|errors?)(?: and \d+ (?:warnings?|errors?))? generated\.|compilation terminated\.|.*: At top level:)')
_NUMBERED_SOURCE = re.compile(r'^\s*\d+\s*\| ?(.*)$')
_CARET = re.compile(r'^\s*(?:\|\s*)?[~^]+(?:[~^ ]*)$')


def _coordinate(value):
    # Malformed output must not trigger Python's huge-integer conversion limit.
    return (int(value) or None) if value and len(value) <= 12 else None


def categorize(severity, message):
    """Warnings remain warnings, notes unknown; only narrow error patterns infer type."""
    if severity == 'warning':
        return 'compiler warning'
    if severity not in ('error', 'fatal error'):
        return 'unknown'
    if re.search(r'^(?:expected (?:[\'‘“\"]|expression\b|identifier\b|declaration\b)|extraneous |unterminated |stray |missing terminating )', message):
        return 'syntax'
    if re.search(r'\b(?:undeclared|incompatible (?:types?|result type|pointer(?: types?)?)|conflicting types|too (?:many|few) arguments|invalid operands|implicit declaration of function|unknown type name)\b', message):
        return 'semantic/type'
    return 'unknown'


def parse_output(output, backend):
    """Return (diagnostics, unrecognized lines), preserving order and real repeats.

    Source/caret blocks and wrapped prose attach to their header, never become
    extra diagnostics. Unknown unindented lines remain explicit raw evidence.
    """
    records, unknown = [], []
    lines = _ANSI.sub('', output).splitlines()
    source_seen = False
    for index, line in enumerate(lines):
        numbered = _NUMBERED_SOURCE.match(line)
        next_line = lines[index + 1] if index + 1 < len(lines) else ''
        # Source text may itself contain strings such as "error: ...".
        if records and (numbered or (next_line and _CARET.match(next_line))):
            snippet = numbered.group(1) if numbered else line[1:] if backend == 'gcc' and line.startswith(' ') else line
            records[-1] = replace(records[-1], source_snippet=snippet)
            source_seen = True
            continue
        match = _LOCATION.match(line)
        if match:
            file, row, col, severity, message = match.groups()
            row, col = _coordinate(row), _coordinate(col)
        else:
            match = _FILE.match(line)
            bare = _BARE.match(line) if not match else None
            if match:
                file, severity, message = match.groups()
                # Driver prefixes are not filenames.
                if not re.search(r'\.(?:c|h|i)$', file, re.I):
                    file = None
            elif bare:
                severity, message = bare.groups()
                file = None
            row = col = None
        if match or (not match and bare):
            option = _OPTION.search(message)
            identifier = option.group(1) if option else None
            if option:
                message = message[:option.start()]
            records.append(Diagnostic(file, row, col, severity, message, backend,
                                      categorize(severity, message), diagnostic_id=identifier))
            source_seen = False
            continue
        if not line.strip() or _CONTEXT.match(line):
            continue
        if records:
            if _CARET.match(line) or re.match(r'^\s*\|\s*$', line):
                continue
            # Clang renders these replacement hints after assignment-condition
            # notes. They are suggestions, not diagnostics or source edits;
            # retain their exact text in raw output without marking a failure.
            if (source_seen and records[-1].severity == 'note'
                    and re.search(r'parentheses|assignment', records[-1].message)
                    and re.fullmatch(r'\s+(?:\(\s+\)|==)\s*', line)):
                continue
            if line[:1].isspace() and not source_seen:
                previous = records[-1]
                message = previous.message + '\n' + line.strip()
                option = _OPTION.search(message)
                records[-1] = replace(previous, message=message[:option.start()] if option else message,
                                      diagnostic_id=option.group(1) if option else previous.diagnostic_id,
                                      category=categorize(previous.severity, message))
                continue
        unknown.append(line)
    return records, unknown


def collect_diagnostics(output, backend):
    return parse_output(output, backend)[0]
