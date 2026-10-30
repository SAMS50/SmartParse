"""Bounded regression runner; artifacts stay separate from frozen milestones.

Restores the legacy tests' historical CSV writes in a finally block and verifies
actual pre/post checkout bytes, including local untracked acceptance evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from phase6.v3.supervision import run_logged
from smartparse_cli.tools import locate

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.studio-artifacts/regression')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(); output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    def write(name, data):
        (output / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    if args.worker:
        started = time.monotonic()
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
        write('tests.json', dict(run=result.testsRun,
            passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
            failures=len(result.failures), errors=len(result.errors),
            skipped=[dict(test=str(test), reason=reason) for test, reason in result.skipped],
            elapsed_seconds=round(time.monotonic()-started, 3)))
        return 0 if result.wasSuccessful() else 1
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    paths = {ROOT / name for name in tracked if name}
    paths.update(path for path in (ROOT / 'acceptance/output').rglob('*') if path.is_file())
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    csvs = {path: path.read_bytes() for path in (ROOT / 'results').rglob('*.csv')}
    restored = []
    env = os.environ.copy(); clang = locate('clang')
    if clang: env['PATH'] = str(Path(clang).parent) + os.pathsep + env.get('PATH', '')
    try:
        run = run_logged([sys.executable, '-m', 'smartparse_studio.validate', '--worker', '--output', str(output)],
                         output / 'tests.log', timeout=600, env=env, cwd=ROOT)
    finally:
        for path, data in csvs.items():
            if not path.is_file() or path.read_bytes() != data:
                path.write_bytes(data); restored.append(str(path.relative_to(ROOT)))
    changed = [str(path.relative_to(ROOT)) for path, digest in before.items()
               if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest]
    preservation = dict(scope='actual checkout and local acceptance evidence before/after this run',
                        files=len(before), changed=sorted(changed), preserved=not changed,
                        csvs=len(csvs), legacy_csv_writes_restored=restored)
    write('supervisor.json', run); write('preservation.json', preservation)
    print(json.dumps(dict(supervisor=run, preservation=preservation), indent=2))
    return 0 if run['exit_code'] == 0 and not run['timed_out'] and not changed else 1


if __name__ == '__main__':
    sys.exit(main())
