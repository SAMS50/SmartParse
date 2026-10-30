"""Syntax/type checking without linking, running programs, or editing sources.

Compiler diagnostics remain external-backend evidence. A completed check may
contain errors; completion does not imply correctness or exhaustive detection.
"""
from dataclasses import dataclass, field
from pathlib import Path
import math
import os
import shutil
import subprocess

from .diagnostics import Diagnostic, collect_diagnostics, parse_output
from .configuration import configuration_args, check_standard


@dataclass(frozen=True)
class Compiler:
    path: str
    backend: str
    version: str
    flags: tuple[str, ...]


@dataclass
class AnalysisResult:
    # completed means the compiler finished normally, including rejection of C.
    status: str
    compiler: Compiler | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    returncode: int | None = None
    stdout: str = ''
    stderr: str = ''
    command: tuple[str, ...] = ()
    issues: list[str] = field(default_factory=list)
    unrecognized_output: list[str] = field(default_factory=list)
    static_analysis: 'AnalysisResult | None' = None
    findings: list[Diagnostic] | None = None


def _timeout(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError('timeout must be finite and positive')


def _decode(value):
    if value is None:
        return ''
    return value if isinstance(value, str) else value.decode('utf-8', errors='replace')


def _run(command, timeout, input=None):
    env = os.environ.copy()
    env.update(LC_ALL='C', LANG='C', GCC_COLORS='')
    return subprocess.run(command, input=input, capture_output=True,
                          timeout=timeout, shell=False, env=env)


def discover_compiler(preference='auto', *, executable=None, timeout=5.0):
    """Return a verified Clang/GCC driver, or raise a descriptive exception.

    Each optional flag is tested on a valid stdin translation unit. Explicit
    selection never silently falls back to another compiler.
    """
    _timeout(timeout)
    if preference not in ('auto', 'clang', 'gcc'):
        raise ValueError('compiler preference must be auto, clang, or gcc')
    candidates = [executable] if executable is not None else (
        ['clang', 'gcc'] if preference == 'auto' else [preference])
    failures = []
    for candidate in candidates:
        path = shutil.which(str(candidate))
        if not path:
            failures.append(f'{candidate}: executable not found')
            continue
        try:
            version_run = _run([path, '--version'], timeout)
            version = _decode(version_run.stdout) + _decode(version_run.stderr)
            lower = version.lower()
            backend = 'clang' if 'clang' in lower else 'gcc' if ('gcc' in lower or 'free software foundation' in lower) else None
            if version_run.returncode or backend is None:
                raise RuntimeError('not a recognized Clang/GCC driver')
            if preference != 'auto' and backend != preference:
                raise RuntimeError(f'expected {preference}, found {backend}')
            base = [path, '-x', 'c', '-fsyntax-only']
            probe = b'int main(void) { return 0; }\n'
            required = _run(base + ['-'], timeout, probe)
            if required.returncode:
                raise RuntimeError('required -fsyntax-only capability unavailable')
            options = ['-Wall', '-Wextra', '-Wparentheses', '-fdiagnostics-show-option',
                       '-fdiagnostics-color=never',
                       '-ferror-limit=0' if backend == 'clang' else '-fmax-errors=0']
            if backend == 'clang':
                # Keep diagnostic notes, but suppress inline replacement rows
                # (e.g. bare ';', identifiers, or format strings) when supported.
                # These are compiler suggestions, not additional diagnostics.
                options.append('-fno-diagnostics-fixit-info')
            supported = []
            for flag in options:
                checked = _run(base + [flag, '-'], timeout, probe)
                # Some drivers warn rather than fail on unknown options.
                if checked.returncode == 0 and not checked.stderr.strip():
                    supported.append(flag)
            return Compiler(str(Path(path).resolve()), backend,
                            version.strip().splitlines()[0], tuple(supported))
        except (OSError, subprocess.SubprocessError, RuntimeError) as error:
            failures.append(f'{candidate}: {error}')
    raise RuntimeError('No usable C compiler. ' + '; '.join(failures))


def _analyze_file(source, *, preference='auto', executable=None, timeout=30.0,
                 discovery_timeout=5.0, standard=None, include_dirs=(), defines=()):
    """Check one translation unit. Never produce or execute a compiled binary.

    Status: completed, failed, timed_out, or partial. Partial denotes retained
    findings from an interrupted/fatal/unrecognized compiler result. Tool issues
    are separate from compiler diagnostics. Syntax and type errors can cascade.
    """
    result = AnalysisResult('failed')
    try:
        _timeout(timeout)
        config = configuration_args(standard, include_dirs, defines)
        path = Path(source).resolve(strict=True)
        if not path.is_file():
            raise ValueError('source must be a regular file')
        if path.suffix.lower() != '.c':
            raise ValueError('source must have a .c extension')
        # Verify readability without decoding or rewriting compiler input.
        with path.open('rb') as stream:
            stream.read(1)
        compiler = discover_compiler(preference, executable=executable,
                                     timeout=discovery_timeout)
        result.compiler = compiler
        check_standard(compiler, standard, discovery_timeout)
        command = (compiler.path, '-x', 'c', '-fsyntax-only', *compiler.flags, *config, str(path))
        result.command = command
        try:
            process = _run(list(command), timeout)
            result.returncode = process.returncode
            result.stdout, result.stderr = _decode(process.stdout), _decode(process.stderr)
        except subprocess.TimeoutExpired as error:
            result.stdout, result.stderr = _decode(error.stdout), _decode(error.stderr)
            result.diagnostics, result.unrecognized_output = parse_output(result.stderr, compiler.backend)
            result.status = 'partial' if result.diagnostics else 'timed_out'
            result.issues.append(f'Compiler timed out after {timeout} seconds; analysis incomplete')
            return result
        result.diagnostics, result.unrecognized_output = parse_output(result.stderr, compiler.backend)
        fatal = any(d.severity == 'fatal error' for d in result.diagnostics)
        internal = 'internal compiler error' in result.stderr.lower()
        if fatal or internal or process.returncode not in (0, 1):
            result.status = 'partial' if result.diagnostics else 'failed'
            result.issues.append('Compiler could not finish analysis normally')
        elif process.returncode and not result.diagnostics:
            result.status = 'failed'
            result.issues.append('Compiler failed without recognized diagnostics; inspect raw output')
        elif result.stderr.strip() and not result.diagnostics:
            result.status = 'partial'
            result.issues.append('Unrecognized compiler output; inspect raw output')
        elif result.unrecognized_output:
            result.status = 'partial'
            result.issues.append('Some compiler output was unrecognized; inspect raw output')
        else:
            result.status = 'completed'
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        result.issues.append(str(error))
    return result


def analyze_file(source, *, preference='auto', executable=None, timeout=30.0,
                 discovery_timeout=5.0, static_analysis=False,
                 analyzer_executable=None, analyzer_timeout=30.0,
                 standard=None, include_dirs=(), defines=()):
    """Regular compiler check, plus an independent analyzer pass only on opt-in.

    The top-level completion status always describes the regular compiler pass.
    The optional static_analysis result carries its own status and evidence.
    """
    config = {}
    if standard is not None or include_dirs or defines:
        config = dict(standard=standard, include_dirs=tuple(include_dirs), defines=tuple(defines))
    result = _analyze_file(source, preference=preference, executable=executable,
                           timeout=timeout, discovery_timeout=discovery_timeout, **config)
    if static_analysis:
        from .static_analysis import analyze_static
        result.static_analysis = analyze_static(source, executable=analyzer_executable,
                                                timeout=analyzer_timeout,
                                                discovery_timeout=discovery_timeout, **config)
    return result
