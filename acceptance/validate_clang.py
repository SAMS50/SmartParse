"""Live validation using an explicit installed Clang; no installation/PATH edit.

PATH is adjusted only inside this Python process and its validation children.
Earlier GCC acceptance artifacts remain intact for side-by-side review.
"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from acceptance import run_acceptance as acceptance
from acceptance.checks import validate_report
from extended_c import analyze_static, to_report, format_terminal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compiler', required=True, type=Path)
    args = parser.parse_args()
    compiler = args.compiler.resolve(strict=True)
    output = ROOT / 'acceptance/output/clang_validation'
    output.mkdir(parents=True, exist_ok=True)
    os.environ['PATH'] = str(compiler.parent) + os.pathsep + os.environ.get('PATH', '')
    old_manifest = json.loads((ROOT / 'acceptance/output/preservation.json').read_text(encoding='utf-8'))
    for path, expected in old_manifest['sha256'].items():
        assert acceptance.digest(Path(path).read_bytes()) == expected, f'Changed before validation: {path}'
    originals = {Path(path): Path(path).read_bytes() for path in old_manifest['sha256']}
    cleaned = ROOT / 'acceptance/cleaned/c_error_detection_500_lines.c'
    originals[cleaned] = cleaned.read_bytes()
    artifacts = acceptance.build_artifacts()
    csvs = {path: data for path, data in originals.items() if path.suffix == '.csv'}
    try:
        names = ['test_extended_c_reporting.BackendReportIntegrationTests.test_clang_reporting',
                 'test_extended_c_static.LiveAnalyzerTests']
        targeted_log = io.StringIO()
        with contextlib.redirect_stdout(targeted_log), contextlib.redirect_stderr(targeted_log):
            targeted = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
        (output / 'previously_skipped_tests.txt').write_text(targeted_log.getvalue(), encoding='utf-8')
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
        (output / 'tests.txt').write_text(capture.getvalue(), encoding='utf-8')
        def stats(run):
            return {'run': run.testsRun, 'passed': run.testsRun - len(run.failures) - len(run.errors) - len(run.skipped),
                    'failures': len(run.failures), 'errors': len(run.errors),
                    'skipped': [{'test': str(test), 'reason': reason} for test, reason in run.skipped]}
        acceptance.write_json(output / 'tests.json', {'previously_skipped': stats(targeted), 'full_suite': stats(result)})
        fixtures = []
        for name in ('null_pointer', 'memory_leak', 'use_after_free', 'double_free'):
            source = ROOT / 'tests_fixtures/extended_c' / (name + '.c')
            analyzed = analyze_static(source, executable=str(compiler), temp_dir=output)
            report = to_report(analyzed)
            validate_report(report)
            acceptance.write_json(output / (name + '.json'), report)
            (output / (name + '.txt')).write_text(format_terminal(analyzed) + '\n', encoding='utf-8')
            fixtures.append({'fixture': name, 'status': analyzed.status, 'summary': report['summary'],
                             'findings_summary': report['findings_summary']})
        acceptance.OUTPUT = output
        cases = []
        for name, source in (('sample', cleaned), ('valid_inventory', ROOT / 'acceptance/fixtures/valid_inventory.c'),
                             ('broken_records', ROOT / 'acceptance/fixtures/broken_records.c'),
                             ('pointer_and_logic', ROOT / 'acceptance/fixtures/pointer_and_logic.c')):
            cases.append(acceptance.invoke(name, source, ('--compiler', str(compiler))))
            cases.append(acceptance.invoke(name + '_static', source,
                         ('--compiler', str(compiler), '--static-analysis', '--analyzer-executable', str(compiler))))
        acceptance.write_json(output / 'cases.json', {'compiler_path': str(compiler), 'fixtures': fixtures, 'cli_cases': cases})
        print(json.dumps({'targeted': stats(targeted), 'full_suite': stats(result), 'fixtures': fixtures, 'cases': cases}, indent=2))
    finally:
        restored = []
        for path, data in csvs.items():
            if path.read_bytes() != data:
                path.write_bytes(data)
                restored.append(str(path))
        changes = [str(path) for path, data in originals.items() if path.read_bytes() != data]
        acceptance.write_json(output / 'preservation.json', {'historical_csv_count': len(csvs),
                              'changed_protected_files': changes, 'legacy_csv_writes_restored': restored,
                              'new_build_artifacts': sorted(acceptance.build_artifacts() - artifacts),
                              'sha256': {str(path): acceptance.digest(data) for path, data in originals.items()}})
        assert not changes
        assert acceptance.build_artifacts() == artifacts
    assert targeted.wasSuccessful() and result.wasSuccessful(), 'Inspect saved live test failures'


if __name__ == '__main__':
    main()
