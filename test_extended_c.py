"""Milestone 1: compiler boundary tests and independent real-C fixtures."""
import hashlib
from pathlib import Path
import subprocess
import shutil
import uuid
import unittest
from unittest.mock import patch

from extended_c.backend import Compiler, analyze_file, collect_diagnostics, discover_compiler


FIXTURES = Path(__file__).parent / 'tests_fixtures' / 'extended_c'
FAKE = Compiler('compiler', 'gcc', 'gcc test', ('-Wall',))


class DiagnosticTests(unittest.TestCase):
    def test_windows_and_optional_column(self):
        records = collect_diagnostics('C:\\a b\\test.c:12:4: error: bad type\nx.c:2: warning: suspicious\n', 'gcc')
        self.assertEqual(records[0].file, 'C:\\a b\\test.c')
        self.assertEqual((records[0].line, records[0].column), (12, 4))
        self.assertIsNone(records[1].column)
        self.assertEqual(records[1].backend, 'gcc')

    def test_driver_error(self):
        record = collect_diagnostics('cc1: fatal error: cannot open input', 'gcc')[0]
        self.assertIsNone(record.file)
        self.assertEqual(record.severity, 'fatal error')


class DiscoveryTests(unittest.TestCase):
    @patch('extended_c.backend.shutil.which', return_value=None)
    def test_missing_compilers(self, which):
        with self.assertRaisesRegex(RuntimeError, 'No usable C compiler'):
            discover_compiler()
        self.assertEqual(which.call_count, 2)

    @patch('extended_c.backend.shutil.which', return_value='gcc')
    @patch('extended_c.backend._run')
    def test_old_driver_optional_flags_are_probed(self, run, which):
        def respond(command, timeout, input=None):
            if '--version' in command:
                return subprocess.CompletedProcess(command, 0, b'gcc version 6.3.0', b'')
            rejected = '-fdiagnostics-color=never' in command
            return subprocess.CompletedProcess(command, 1 if rejected else 0, b'', b'unknown option' if rejected else b'')
        run.side_effect = respond
        compiler = discover_compiler('gcc')
        self.assertNotIn('-fdiagnostics-color=never', compiler.flags)
        self.assertIn('-fmax-errors=0', compiler.flags)

    @patch('extended_c.backend.shutil.which', return_value='gcc')
    @patch('extended_c.backend._run', side_effect=subprocess.TimeoutExpired('gcc', 1))
    def test_discovery_timeout(self, run, which):
        with self.assertRaisesRegex(RuntimeError, 'No usable C compiler'):
            discover_compiler('gcc')

    def test_bad_timeout(self):
        for value in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                discover_compiler(timeout=value)


class ExecutionTests(unittest.TestCase):
    def check_process(self, process):
        with patch('extended_c.backend.discover_compiler', return_value=FAKE), patch('extended_c.backend._run') as run:
            if isinstance(process, Exception):
                run.side_effect = process
            else:
                run.return_value = process
            return analyze_file(FIXTURES / 'valid.c')

    def test_timeout_without_findings(self):
        result = self.check_process(subprocess.TimeoutExpired('gcc', 1))
        self.assertEqual(result.status, 'timed_out')
        self.assertIsNone(result.returncode)

    def test_timeout_preserves_partial_findings(self):
        result = self.check_process(subprocess.TimeoutExpired('gcc', 1, stderr=b'x.c:1:2: error: bad\n'))
        self.assertEqual(result.status, 'partial')
        self.assertEqual(len(result.diagnostics), 1)
        self.assertIn('timed out', result.issues[0])

    def test_os_failure(self):
        result = self.check_process(OSError('cannot start compiler'))
        self.assertEqual(result.status, 'failed')
        self.assertIn('cannot start', result.issues[0])

    def test_fatal_and_internal_failure(self):
        for output in (b'x.c:1:1: fatal error: header missing', b'cc1: internal compiler error: crash'):
            result = self.check_process(subprocess.CompletedProcess([], 1, b'', output))
            self.assertNotEqual(result.status, 'completed')

    def test_unknown_output_and_encoding(self):
        result = self.check_process(subprocess.CompletedProcess([], 1, b'', b'unknown\xff'))
        self.assertEqual(result.status, 'failed')
        self.assertIn('\ufffd', result.stderr)

    def test_missing_file_and_invalid_timeout(self):
        self.assertEqual(analyze_file(FIXTURES / 'absent.c').status, 'failed')
        self.assertEqual(analyze_file(FIXTURES / 'valid.c', timeout=0).status, 'failed')

    @patch('extended_c.backend.subprocess.run')
    def test_safe_subprocess_boundary(self, run):
        from extended_c.backend import _run
        _run(['compiler', 'a b.c'], 2)
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(run.call_args.args[0], ['compiler', 'a b.c'])
        self.assertEqual(run.call_args.kwargs['env']['LC_ALL'], 'C')


class RealCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.compiler = discover_compiler()
        except RuntimeError as error:
            raise unittest.SkipTest(str(error))

    def analyze(self, name):
        return analyze_file(FIXTURES / name, executable=self.compiler.path)

    def test_standard_c_constructs_and_legal_ambiguity(self):
        for name in ('valid.c', 'ambiguous.c'):
            result = self.analyze(name)
            self.assertEqual(result.status, 'completed', result)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(result.diagnostics, result.stderr)

    def test_independent_syntax_errors(self):
        result = self.analyze('syntax.c')
        self.assertEqual(result.status, 'completed', result)
        self.assertEqual({d.line for d in result.diagnostics if d.severity == 'error'}, {1, 2})

    def test_semantic_errors_and_condition_warning(self):
        result = self.analyze('semantic.c')
        self.assertEqual(result.status, 'completed', result)
        messages = '\n'.join(d.message for d in result.diagnostics)
        self.assertIn('missing_identifier', messages)
        self.assertIn('incompatible', messages)
        self.assertIn('too many arguments', messages)
        self.assertTrue(any(d.severity == 'warning' and 'assignment' in d.message for d in result.diagnostics))
        self.assertTrue(all(d.backend == self.compiler.backend for d in result.diagnostics))

    def test_missing_header_incomplete(self):
        self.assertEqual(self.analyze('missing_header.c').status, 'partial')

    def test_large_unfamiliar_source_and_preservation(self):
        directory = FIXTURES / ('smartparse c ' + uuid.uuid4().hex)
        directory.mkdir()
        try:
            source = directory / 'large sample.c'
            source.write_bytes((FIXTURES / 'valid.c').read_bytes() + b'\n' +
                               b'\n'.join(f'int function_{i}(int x) {{ return x + {i}; }}'.encode() for i in range(600)))
            before = hashlib.sha256(source.read_bytes()).digest()
            result = analyze_file(source, executable=self.compiler.path)
            self.assertEqual(result.status, 'completed', result)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)
            self.assertEqual(list(Path(directory).iterdir()), [source])
            self.assertIn('-fsyntax-only', result.command)
        finally:
            shutil.rmtree(directory)


if __name__ == '__main__':
    unittest.main()
