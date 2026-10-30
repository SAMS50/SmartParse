"""Build configuration as compiler arguments, never shell fragments."""
import re


def configuration_args(standard=None, include_dirs=(), defines=()):
    args = []
    if standard is not None:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:.+-]*', standard):
            raise ValueError('invalid C standard spelling')
        args.append('-std=' + standard)
    for directory in include_dirs:
        value = str(directory)
        if not value or '\0' in value or '\n' in value or '\r' in value:
            raise ValueError('include directories must be nonempty paths without NUL/newline')
        args.extend(('-I', value))
    for definition in defines:
        if not isinstance(definition, str) or not re.fullmatch(r'[A-Za-z_]\w*(?:=[^\r\n\0]*)?', definition, re.ASCII):
            raise ValueError('macro definitions must be NAME or NAME=VALUE')
        args.extend(('-D', definition))
    return tuple(args)


def check_standard(compiler, standard, timeout):
    if standard is None:
        return
    from .backend import _run, _decode
    command = [compiler.path, '-x', 'c', '-fsyntax-only', '-std=' + standard, '-']
    result = _run(command, timeout, b'int smartparse_standard_probe;\n')
    if result.returncode or result.stderr.strip():
        raise RuntimeError('Requested C standard is unsupported by this compiler: ' +
                           standard + '; ' + _decode(result.stderr))
