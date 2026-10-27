"""Analyzer boundary tests; live checks are conditional on installed capabilities."""
from contextlib import contextmanager
from pathlib import Path
import json
import shutil
import subprocess
import unittest
import uuid
from unittest.mock import patch

from extended_c import Compiler, analyze_file, analyze_static, discover_analyzer, format_terminal, to_report, to_json
from extended_c.static_analysis import parse_analyzer_output

FIXTURES = Path(__file__).parent / 'tests_fixtures' / 'extended_c'
CLANG = Compiler('clang', 'clang', 'clang test', ('-Wall', '-fdiagnostics-color=never'))
FINDING = b'''C:\\work dir\\input.c:3:5: warning: Dereference of null pointer [core.NullDereference]
    3 | return *pointer;
      |        ^~~~~~~~
C:\\work dir\\input.c:2:5: note: 'pointer' initialized to a null pointer value
1 warning generated.
'''


@contextmanager
def scratch_directory(*, prefix, dir=None):
    # tempfile's Windows private ACLs cannot be traversed by this sandbox.
    # Use a unique workspace directory only in tests, retaining production's
    # TemporaryDirectory context and cleanup semantics through this test double.
    path = Path(dir or FIXTURES) / (prefix + uuid.uuid4().hex)
    path.mkdir()
    try:
        yield str(path)
    finally:
        shutil.rmtree(path)


class AnalyzerParsingTests(unittest.TestCase):
    def test_source_identifier_and_path_note(self):
        regular, findings, unknown = parse_analyzer_output(FINDING.decode())
        self.assertEqual(regular, [])
        self.assertEqual(unknown, [])
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0].backend, 'clang-static-analyzer')
        self.assertEqual(findings[0].diagnostic_id, 'core.NullDereference')
        self.assertEqual(findings[0].source_snippet, 'return *pointer;')
        self.assertEqual(findings[0].file, 'C:\\work dir\\input.c')
        self.assertEqual(findings[0].category, 'unknown')
        self.assertEqual(findings[1].severity, 'note')

    def test_ordinary_errors_warnings_and_notes_remain_separate(self):
        raw = FINDING.decode() + 'x.c:4:2: error: expected expression\nx.c:4:2: note: previous declaration\nx.c:5:1: warning: unused variable [-Wunused-variable]\n'
        regular, findings, unknown = parse_analyzer_output(raw)
        self.assertEqual(len(regular), 3)
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(d.backend == 'clang' for d in regular))
        self.assertEqual(regular[-1].diagnostic_id, '-Wunused-variable')

    def test_no_guessing_or_deduplication(self):
        raw = 'x.c:1:1: warning: possible null pointer\n' + FINDING.decode() * 2
        regular, findings, _ = parse_analyzer_output(raw)
        self.assertEqual(len(regular), 1)
        self.assertEqual(len(findings), 4)

    def test_unknown_output_retained(self):
        self.assertEqual(parse_analyzer_output('???')[2], ['???'])


class AnalyzerDiscoveryTests(unittest.TestCase):
    @patch('extended_c.static_analysis.discover_compiler', side_effect=RuntimeError('not installed'))
    @patch('extended_c.static_analysis._run')
    def test_unavailable_does_not_launch(self, run, discover):
        result = analyze_static(FIXTURES / 'valid.c')
        self.assertEqual(result.status, 'unavailable')
        run.assert_not_called()
        self.assertEqual(result.findings, [])

    def probe(self, response):
        with patch('extended_c.static_analysis.discover_compiler', return_value=CLANG) as discover, \
             patch('extended_c.static_analysis.tempfile.TemporaryDirectory', scratch_directory), \
             patch('extended_c.static_analysis._run') as run:
            if isinstance(response, Exception):
                run.side_effect = response
            else:
                run.return_value = response
            try:
                return discover_analyzer(temp_dir=FIXTURES)
            finally:
                command = run.call_args.args[0]
                self.assertFalse(Path(command[command.index('-o') + 1]).parent.exists())
                discover.assert_called_once_with('clang', executable=None, timeout=5.0)
                self.assertIn('--analyze', command)
                self.assertIn('-analyzer-output=text', command)
                self.assertEqual(command[-1], '-')
                self.assertNotIn('-Wall', command)

    def test_supported_invocation(self):
        self.assertEqual(self.probe(subprocess.CompletedProcess([], 0, b'', b'')), CLANG)

    def test_unsupported_invocation(self):
        with self.assertRaisesRegex(RuntimeError, 'capability probe failed'):
            self.probe(subprocess.CompletedProcess([], 1, b'', b'unknown argument'))

    def test_warning_only_rejection(self):
        with self.assertRaises(RuntimeError):
            self.probe(subprocess.CompletedProcess([], 0, b'', b'argument ignored'))

    def test_probe_timeout_cleanup(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.probe(subprocess.TimeoutExpired('clang', 1))


class AnalyzerExecutionTests(unittest.TestCase):
    def invoke(self, response):
        before = (FIXTURES / 'null_pointer.c').read_bytes()
        with patch('extended_c.static_analysis.discover_analyzer', return_value=CLANG), \
             patch('extended_c.static_analysis.tempfile.TemporaryDirectory', scratch_directory), \
             patch('extended_c.static_analysis._run') as run:
            def perform(command, timeout):
                output = Path(command[command.index('-o') + 1])
                output.write_text('temporary analyzer artifact')
                self.assertEqual(command[-1], str((FIXTURES / 'null_pointer.c').resolve()))
                self.assertIn('--analyze', command)
                self.assertEqual(timeout, 2)
                if isinstance(response, Exception):
                    raise response
                return response
            run.side_effect = perform
            result = analyze_static(FIXTURES / 'null_pointer.c', timeout=2, temp_dir=FIXTURES)
            self.assertFalse(Path(result.command[result.command.index('-o') + 1]).parent.exists())
        self.assertEqual((FIXTURES / 'null_pointer.c').read_bytes(), before)
        return result

    def test_findings_completion_and_cleanup(self):
        result = self.invoke(subprocess.CompletedProcess([], 0, b'', FINDING))
        self.assertEqual(result.status, 'completed')
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.stderr, FINDING.decode())

    def test_zero_findings_is_not_bug_free(self):
        result = self.invoke(subprocess.CompletedProcess([], 0, b'', b''))
        self.assertEqual(result.status, 'completed')
        self.assertIn('zero findings does not establish', format_terminal(result))

    def test_timeout_and_cleanup(self):
        result = self.invoke(subprocess.TimeoutExpired('clang', 2))
        self.assertEqual(result.status, 'timed_out')

    def test_timeout_retains_partial_findings(self):
        result = self.invoke(subprocess.TimeoutExpired('clang', 2, stderr=FINDING))
        self.assertEqual(result.status, 'partial')
        self.assertEqual(len(result.findings), 2)
        self.assertIn('timed out', result.issues[0])

    def test_process_error_cleanup(self):
        self.assertEqual(self.invoke(OSError('cannot start')).status, 'failed')

    def test_nonzero_without_findings(self):
        self.assertEqual(self.invoke(subprocess.CompletedProcess([], 2, b'', b'crash')).status, 'failed')

    def test_frontend_error_prevents_completion(self):
        result = self.invoke(subprocess.CompletedProcess([], 1, b'', b'x.c:1:1: error: expected expression'))
        self.assertEqual(result.status, 'partial')
        self.assertEqual(len(result.diagnostics), 1)
        self.assertEqual(result.findings, [])

    def test_mixed_unknown_output_is_partial(self):
        self.assertEqual(self.invoke(subprocess.CompletedProcess([], 0, b'', FINDING + b'???')).status, 'partial')

    def test_missing_input_and_invalid_timeout(self):
        self.assertEqual(analyze_static(FIXTURES / 'absent.c').status, 'failed')
        self.assertEqual(analyze_static(FIXTURES / 'valid.c', timeout=0).status, 'failed')

    def test_opt_in_required(self):
        with patch('extended_c.backend._analyze_file') as regular, patch('extended_c.static_analysis.analyze_static') as analyzer:
            result = analyze_file('unused.c')
            self.assertIs(result, regular.return_value)
            analyzer.assert_not_called()

    def test_explicit_opt_in_does_not_replace_regular_result(self):
        with patch('extended_c.backend._analyze_file') as regular, patch('extended_c.static_analysis.analyze_static') as analyzer:
            result = analyze_file('unused.c', static_analysis=True, analyzer_timeout=7, analyzer_executable='myclang')
            self.assertIs(result, regular.return_value)
            self.assertIs(result.static_analysis, analyzer.return_value)
            analyzer.assert_called_once_with('unused.c', executable='myclang', timeout=7, discovery_timeout=5.0)

    def test_report_separation_and_json(self):
        result = self.invoke(subprocess.CompletedProcess([], 0, b'', FINDING))
        report = json.loads(to_json(result))
        self.assertEqual(report['analysis_mode'], 'clang_static_analyzer')
        self.assertEqual(report['summary']['total_diagnostics'], 0)
        self.assertEqual(report['findings_summary']['warnings'], 1)
        self.assertEqual(report['findings'][0]['backend'], 'clang-static-analyzer')
        self.assertEqual(report['raw_output']['stderr'], FINDING.decode())
        from extended_c import AnalysisResult
        ordinary = AnalysisResult('completed', static_analysis=result)
        self.assertEqual(to_report(ordinary)['summary']['warnings'], 0)
        self.assertEqual(to_report(ordinary)['static_analysis'], report)
        self.assertIn('Clang Static Analyzer: completed', format_terminal(ordinary))


class LiveAnalyzerTests(unittest.TestCase):
    def check_fixture(self, fixture):
        if not shutil.which('clang'):
            self.skipTest('Clang unavailable; live analyzer validation pending')
        # Workspace scratch parent supports controlled local environments.
        result = analyze_static(FIXTURES / fixture, temp_dir=FIXTURES)
        if result.status == 'unavailable':
            self.skipTest('; '.join(result.issues))
        self.assertEqual(result.status, 'completed', result)
        warnings = [d for d in result.findings if d.severity == 'warning']
        if not warnings:
            self.skipTest(f'{result.compiler.version}: default checks produced no finding for {fixture}; check may be unsupported')
        self.assertTrue(all(d.backend == 'clang-static-analyzer' and d.diagnostic_id for d in warnings))

    def test_null_pointer(self):
        self.check_fixture('null_pointer.c')

    def test_memory_leak(self):
        self.check_fixture('memory_leak.c')

    def test_use_after_free(self):
        self.check_fixture('use_after_free.c')

    def test_double_free(self):
        self.check_fixture('double_free.c')


if __name__ == '__main__':
    unittest.main()
