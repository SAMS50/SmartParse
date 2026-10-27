"""Explicit opt-in Clang Static Analyzer integration, independent of CGAR."""
from dataclasses import replace
from pathlib import Path
import re
import subprocess
import tempfile

from .backend import AnalysisResult, _decode, _run, _timeout, discover_compiler
from .diagnostics import parse_output
from .configuration import configuration_args, check_standard

ANALYZER_BACKEND = 'clang-static-analyzer'
_CHECKER = re.compile(r'\s+\[([A-Za-z][\w-]*(?:\.[\w-]+)+)\]$')


def parse_analyzer_output(output):
    """Split analyzer findings/path notes from ordinary frontend diagnostics.

    Only emitted checker IDs establish analyzer provenance. We do not infer a
    memory defect from message keywords or deduplicate against compiler records.
    """
    diagnostics, unknown = parse_output(output, 'clang')
    regular, findings = [], []
    analyzer_context = False
    for diagnostic in diagnostics:
        checker = _CHECKER.search(diagnostic.message)
        if diagnostic.severity == 'warning' and checker:
            analyzer_context = True
            findings.append(replace(diagnostic, backend=ANALYZER_BACKEND,
                                    category='unknown', diagnostic_id=checker.group(1),
                                    message=diagnostic.message[:checker.start()]))
        elif diagnostic.severity == 'note' and analyzer_context:
            findings.append(replace(diagnostic, backend=ANALYZER_BACKEND,
                                    category='unknown'))
        else:
            analyzer_context = False
            regular.append(diagnostic)
    return regular, findings, unknown


def _command(compiler, source, output, config=()):
    # Avoid adding general compiler warnings or writing adjacent .plist files.
    flags = [f for f in compiler.flags if f in ('-fdiagnostics-color=never',
                                               '-fdiagnostics-show-option', '-ferror-limit=0',
                                               '-fno-diagnostics-fixit-info')]
    return (compiler.path, '--analyze', '-x', 'c', *flags, *config,
            '-Xanalyzer', '-analyzer-output=text', '-o', str(output), str(source))


def discover_analyzer(*, executable=None, timeout=5.0, temp_dir=None):
    """Verify Clang identity and the exact text-output analyzer invocation.

    Uses only a valid probe, not an assumed checker inventory. Default enabled
    checks vary by Clang version. Probe artifacts live in a private directory.
    """
    compiler = discover_compiler('clang', executable=executable, timeout=timeout)
    with tempfile.TemporaryDirectory(prefix='smartparse-analyzer-', dir=temp_dir) as directory:
        command = _command(compiler, '-', Path(directory) / 'probe.txt')
        checked = _run(list(command), timeout, b'int main(void) { return 0; }\n')
        if checked.returncode or checked.stderr.strip() or checked.stdout.strip():
            raise RuntimeError('Clang analyzer text-output capability probe failed: ' +
                               _decode(checked.stderr) + _decode(checked.stdout))
    return compiler


def analyze_static(source, *, executable=None, timeout=30.0,
                   discovery_timeout=5.0, temp_dir=None,
                   standard=None, include_dirs=(), defines=()):
    """Return ordinary frontend diagnostics separately from potential findings.

    Default analyzer checkers only. No binary is produced or run. `temp_dir` is
    an optional scratch parent; caller source files are never temporary outputs.
    """
    result = AnalysisResult('failed', findings=[])
    try:
        _timeout(timeout)
        _timeout(discovery_timeout)
        config = configuration_args(standard, include_dirs, defines)
        path = Path(source).resolve(strict=True)
        if not path.is_file() or path.suffix.lower() != '.c':
            raise ValueError('source must be a regular .c file')
        with path.open('rb') as stream:
            stream.read(1)
        try:
            result.compiler = discover_analyzer(executable=executable,
                                                timeout=discovery_timeout, temp_dir=temp_dir)
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            result.status = 'unavailable'
            result.issues.append(f'Clang Static Analyzer unavailable: {error}')
            return result
        check_standard(result.compiler, standard, discovery_timeout)
        # TemporaryDirectory provides unique paths and cleanup even on errors.
        with tempfile.TemporaryDirectory(prefix='smartparse-analyzer-', dir=temp_dir) as directory:
            result.command = _command(result.compiler, path, Path(directory) / 'analysis.txt', config)
            timed_out = False
            try:
                process = _run(list(result.command), timeout)
                result.returncode = process.returncode
                result.stdout, result.stderr = _decode(process.stdout), _decode(process.stderr)
            except subprocess.TimeoutExpired as error:
                timed_out = True
                result.stdout, result.stderr = _decode(error.stdout), _decode(error.stderr)
            result.diagnostics, result.findings, result.unrecognized_output = parse_analyzer_output(result.stderr)
            evidence = bool(result.diagnostics or result.findings)
            if timed_out:
                result.status = 'partial' if evidence else 'timed_out'
                result.issues.append(f'Static analysis timed out after {timeout} seconds; analysis incomplete')
            elif result.returncode != 0 or any(d.severity in ('error', 'fatal error') for d in result.diagnostics):
                result.status = 'partial' if evidence else 'failed'
                result.issues.append('Clang Static Analyzer did not finish normally')
            elif result.unrecognized_output or result.stdout.strip():
                result.status = 'partial'
                result.issues.append('Unrecognized analyzer output; inspect raw output')
            else:
                result.status = 'completed'
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result.status = 'partial' if result.diagnostics or result.findings else 'failed'
        result.issues.append(str(error))
    return result
