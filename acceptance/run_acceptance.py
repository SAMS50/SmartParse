"""Reproducible release checks; writes only acceptance artifacts and new copies.

Run: python acceptance/run_acceptance.py --sample PATH
Historical CSV bytes are restored in finally because legacy tests write them.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from acceptance.checks import clean_numbered_source, validate_report

OUTPUT = ROOT / 'acceptance' / 'output'
AUDITED_CLI = '''import json, pathlib, runpy, sys
audit = pathlib.Path(sys.argv[1])
def record(event, args):
    if event == 'subprocess.Popen':
        with audit.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'executable': str(args[0]), 'arguments': args[1]}) + '\\n')
sys.addaudithook(record)
sys.argv = sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
'''


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build_artifacts():
    found = set()
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in ('.git', '__pycache__')]
        for name in files:
            if Path(name).suffix.lower() in ('.exe', '.o', '.obj', '.out', '.plist'):
                found.add(str(Path(directory) / name))
    return found


def invoke(name, source, extra=(), expected=None):
    audit = OUTPUT / (name + '.processes.jsonl')
    audit.write_text('', encoding='utf-8')
    base = [sys.executable, '-c', AUDITED_CLI, str(audit), str(ROOT / 'analyze_c.py'), str(source), '--compiler', 'gcc']
    process = subprocess.run([*base, '--json', *extra], cwd=ROOT, capture_output=True, timeout=120, shell=False)
    report = json.loads(process.stdout)
    validate_report(report)
    write_json(OUTPUT / (name + '.json'), report)
    terminal = subprocess.run([*base, *extra], cwd=ROOT, capture_output=True, timeout=120, shell=False)
    text = terminal.stdout.decode('utf-8', errors='replace').replace('\r\n', '\n')
    (OUTPUT / (name + '.txt')).write_text(text, encoding='utf-8')
    assert process.returncode == terminal.returncode, name
    assert b'Traceback' not in process.stderr + terminal.stderr, name
    assert report['status'] in text, name
    summary = report['summary']
    assert f'Total: {summary["errors"]} errors, {summary["warnings"]} warnings, {summary["notes"]} notes' in text, name
    if expected is not None:
        assert process.returncode == expected, (name, process.returncode, report)
    launched = [json.loads(line) for line in audit.read_text(encoding='utf-8').splitlines()]
    for event in launched:
        arguments = event['arguments']
        # Windows emits the OS command-line string in this audit event;
        # POSIX emits an argv array. Record the original representation.
        assert isinstance(arguments, (list, str))
        tokens = arguments if isinstance(arguments, list) else arguments.split()
        assert '--version' in tokens or '-fsyntax-only' in tokens or '--analyze' in tokens, event
        assert '-o' not in tokens or '--analyze' in tokens, event
    return {'case': name, 'exit_code': process.returncode, 'status': report['status'],
            'summary': summary, 'compiler': report['compiler'],
            'analyzer_status': report.get('static_analysis', {}).get('status', 'not requested'),
            'schema_valid': True, 'terminal_valid': True, 'python_child_process_audit_valid': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=Path, default=ROOT / 'c_error_detection_500_lines.c')
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    artifacts_before = build_artifacts()
    csvs = {p: p.read_bytes() for p in (ROOT / 'results').rglob('*.csv')}
    originals = {p: p.read_bytes() for p in (ROOT / 'tests_fixtures/extended_c').glob('*.c')}
    originals.update({p: p.read_bytes() for p in (ROOT / 'acceptance/fixtures').glob('*.c')})
    originals[ROOT / 'example.c'] = (ROOT / 'example.c').read_bytes()
    # Protect every original tracked Python parser, test, and evaluation script.
    tracked = subprocess.check_output(['git', 'ls-files', '*.py'], cwd=ROOT).decode().splitlines()
    originals.update({ROOT / p: (ROOT / p).read_bytes() for p in tracked})
    sample_info = {'available': args.sample.is_file(), 'path': str(args.sample.resolve())}
    if sample_info['available']:
        data = args.sample.read_bytes()
        originals[args.sample] = data
        cleaned, stripped = clean_numbered_source(data)
        cleaned_path = ROOT / 'acceptance' / 'cleaned' / 'c_error_detection_500_lines.c'
        cleaned_path.parent.mkdir(exist_ok=True)
        cleaned_path.write_bytes(cleaned)
        sample_info.update(original_sha256=digest(data), cleaned_sha256=digest(cleaned),
                           prefixes_removed=stripped, lines=len(cleaned.splitlines()),
                           line_mapping='identity: cleaned physical line N equals original physical/prefix line N')
    write_json(OUTPUT / 'sample_provenance.json', sample_info)
    try:
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
        (OUTPUT / 'tests.txt').write_text(capture.getvalue(), encoding='utf-8')
        tests = {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                 'skipped': [{'test': str(test), 'reason': reason} for test, reason in result.skipped],
                 'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}
        write_json(OUTPUT / 'tests.json', tests)
        assert result.wasSuccessful(), 'Automated tests failed; inspect acceptance/output/tests.txt'
        cases = [invoke('valid_inventory', ROOT / 'acceptance/fixtures/valid_inventory.c', expected=0),
                 invoke('broken_records', ROOT / 'acceptance/fixtures/broken_records.c', expected=1),
                 invoke('pointer_and_logic', ROOT / 'acceptance/fixtures/pointer_and_logic.c', expected=0),
                 invoke('semantic', ROOT / 'tests_fixtures/extended_c/semantic.c', expected=1),
                 invoke('missing_header', ROOT / 'tests_fixtures/extended_c/missing_header.c', expected=3)]
        if sample_info['available']:
            cases.append(invoke('sample', cleaned_path, expected=1))
            cases.append(invoke('sample_static', cleaned_path, ('--static-analysis',)))
        else:
            cases.append(invoke('sample_missing', args.sample, expected=3))
        invalid = subprocess.run([sys.executable, str(ROOT / 'analyze_c.py'), 'unused.c', '--timeout', '0'], cwd=ROOT, capture_output=True, timeout=10)
        assert invalid.returncode == 2 and b'Traceback' not in invalid.stderr
        (OUTPUT / 'invalid_arguments.txt').write_bytes(invalid.stderr)
        write_json(OUTPUT / 'cases.json', cases)
    finally:
        restored = []
        for path, data in csvs.items():
            if path.read_bytes() != data:
                path.write_bytes(data)
                restored.append(str(path.relative_to(ROOT)))
        preserved = all(p.read_bytes() == data for p, data in originals.items())
        write_json(OUTPUT / 'preservation.json', {
            'historical_csv_count': len(csvs), 'historical_csvs_unchanged': all(p.read_bytes() == data for p, data in csvs.items()),
            'legacy_test_writes_restored': restored,
            'protected_sources_and_original_python_unchanged': preserved,
            'new_workspace_binary_object_or_plist_files': sorted(build_artifacts() - artifacts_before),
            'sha256': {str(p): digest(data) for p, data in {**csvs, **originals}.items()}})
        assert preserved, 'Protected source/script changed'
        assert build_artifacts() == artifacts_before, 'Unexpected build artifact created'
    print(json.dumps({'tests': tests, 'sample': sample_info, 'cases': cases}, indent=2))


if __name__ == '__main__':
    main()
