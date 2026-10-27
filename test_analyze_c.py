"""CLI, configuration, exit policy, and independent large-C integration tests."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch

import analyze_c
from extended_c import AnalysisResult, Compiler, Diagnostic, analyze_file
from extended_c.configuration import configuration_args

ROOT = Path(__file__).parent
FIXTURES = ROOT / 'tests_fixtures' / 'extended_c'


class CliTests(unittest.TestCase):
    def invoke(self, arguments, result=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch('analyze_c.analyze_file', return_value=result or AnalysisResult('completed')) as analyze:
            code = analyze_c.main(arguments)
        return code, output.getvalue(), analyze.call_args.kwargs

    def test_terminal_default_and_not_requested(self):
        code, text, args = self.invoke(['a file.c'])
        self.assertEqual(code, 0)
        self.assertIn('not requested (availability not probed)', text)
        self.assertEqual(args['preference'], 'auto')
        self.assertFalse(args['static_analysis'])

    def test_json_existing_schema(self):
        code, text, _ = self.invoke(['a.c', '--json'])
        report = json.loads(text)
        self.assertEqual(report['schema_version'], '1.0')
        self.assertEqual(report['status'], 'completed')
        self.assertNotIn('static_analysis', report)

    def test_compiler_selection(self):
        for value in ('auto', 'gcc', 'clang', 'C:\\Program Files\\LLVM\\bin\\clang.exe'):
            _, _, args = self.invoke(['a.c', '--compiler', value])
            self.assertEqual(args['executable'], None if value in ('auto', 'gcc', 'clang') else value)
            self.assertEqual(args['preference'], value if value in ('auto', 'gcc', 'clang') else 'auto')

    def test_configuration_and_analyzer_timeout(self):
        _, _, args = self.invoke(['a.c', '--std', 'c11', '-I', 'folder with spaces', '-Isecond', '-D', 'COUNT=2', '-DENABLED',
                                   '--timeout', '4', '--discovery-timeout', '2', '--static-analysis', '--analyzer-executable', 'clang-custom'])
        self.assertEqual(args['include_dirs'], ['folder with spaces', 'second'])
        self.assertEqual(args['defines'], ['COUNT=2', 'ENABLED'])
        self.assertEqual(args['standard'], 'c11')
        self.assertEqual(args['analyzer_timeout'], 4)
        self.assertEqual(args['discovery_timeout'], 2)

    def test_independent_analyzer_timeout_and_status(self):
        result = AnalysisResult('completed', static_analysis=AnalysisResult('unavailable', findings=[]))
        code, text, args = self.invoke(['a.c', '--static-analysis', '--analyzer-timeout', '7', '--json'], result)
        self.assertEqual(code, 3)
        self.assertEqual(args['analyzer_timeout'], 7)
        self.assertEqual(json.loads(text)['static_analysis']['status'], 'unavailable')

    def test_invalid_arguments_exit_two(self):
        for args in ([], ['a.c', '--unknown'], ['a.c', '--timeout', '0'], ['a.c', '--timeout', 'nan'],
                     ['a.c', '--timeout', 'inf'], ['a.c', '--timeout', 'abc'], ['a.c', '-D', '2BAD'],
                     ['a.c', '--std=bad value'], ['a.c', '--analyzer-timeout', '2']):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                analyze_c.main(args)
            self.assertEqual(error.exception.code, 2)

    def test_exit_source_errors(self):
        result = AnalysisResult('completed', diagnostics=[Diagnostic('a.c', 1, 1, 'error', 'expected expression', 'gcc')])
        self.assertEqual(analyze_c.exit_code(result), 1)

    def test_warnings_only_exit_zero(self):
        result = AnalysisResult('completed', diagnostics=[Diagnostic('a.c', 1, 1, 'warning', 'suspicious', 'gcc')])
        self.assertEqual(analyze_c.exit_code(result), 0)

    def test_static_findings_exit_one(self):
        result = AnalysisResult('completed', static_analysis=AnalysisResult('completed', findings=[Diagnostic('a.c', 1, 1, 'warning', 'potential defect', 'clang-static-analyzer')]))
        self.assertEqual(analyze_c.exit_code(result), 1)

    def test_incomplete_takes_precedence(self):
        for status in ('partial', 'timed_out', 'failed', 'unavailable'):
            self.assertEqual(analyze_c.exit_code(AnalysisResult(status)), 3)

    def test_tool_exception_is_reported_as_json(self):
        with patch('analyze_c.analyze_file', side_effect=OSError('subprocess unavailable')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(analyze_c.main(['a.c', '--json']), 3)
        self.assertEqual(json.loads(out.getvalue())['tool_issues'], ['subprocess unavailable'])

    def test_compiler_timeout_reported_without_traceback(self):
        with patch('extended_c.backend.discover_compiler', return_value=Compiler('gcc', 'gcc', 'test', ())), \
             patch('extended_c.backend._run', side_effect=subprocess.TimeoutExpired('gcc', 1)), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(analyze_c.main([str(FIXTURES / 'valid.c'), '--json']), 3)
        report = json.loads(out.getvalue())
        self.assertEqual(report['status'], 'timed_out')
        self.assertIn('timed out', report['tool_issues'][0])

    def test_help(self):
        with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as error:
            analyze_c.main(['--help'])
        self.assertEqual(error.exception.code, 0)
        self.assertIn('--static-analysis', output.getvalue())


class ConfigurationTests(unittest.TestCase):
    def test_safe_args(self):
        self.assertEqual(configuration_args('gnu11', ['a b'], ['TEXT=$(anything)', 'N=2']),
                         ('-std=gnu11', '-I', 'a b', '-D', 'TEXT=$(anything)', '-D', 'N=2'))

    def test_invalid_configuration(self):
        for kwargs in ({'standard': '-bad'}, {'defines': ['A\nB']}, {'include_dirs': ['a\0b']}):
            with self.assertRaises(ValueError):
                configuration_args(**kwargs)

    def test_config_forwarded_to_both_passes(self):
        with patch('extended_c.backend._analyze_file', return_value=AnalysisResult('completed')) as compiler, patch('extended_c.static_analysis.analyze_static') as analyzer:
            analyze_file('a.c', standard='c11', include_dirs=['a b'], defines=['N=1'], static_analysis=True)
            for call in (compiler.call_args, analyzer.call_args):
                self.assertEqual(call.kwargs['standard'], 'c11')
                self.assertEqual(call.kwargs['include_dirs'], ('a b',))
                self.assertEqual(call.kwargs['defines'], ('N=1',))

    def test_analyzer_command_config(self):
        from extended_c.static_analysis import _command
        command = _command(Compiler('clang', 'clang', 'test', ()), 'a.c', 'temp.txt', configuration_args('c11', ['a b'], ['N=1']))
        self.assertIn('-std=c11', command)
        self.assertIn('a b', command)
        self.assertIn('N=1', command)
        self.assertIn('--analyze', command)

    def test_unsupported_standard(self):
        from extended_c.configuration import check_standard
        with patch('extended_c.backend._run', return_value=subprocess.CompletedProcess([], 1, b'', b'unsupported standard')):
            with self.assertRaisesRegex(RuntimeError, 'unsupported'):
                check_standard(Compiler('gcc', 'gcc', 'test', ()), 'c23', 1)


class RealCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gcc = shutil.which('gcc')
        if not cls.gcc:
            raise unittest.SkipTest('GCC not installed')

    def setUp(self):
        self.directory = FIXTURES / ('cli sample ' + uuid.uuid4().hex)
        self.directory.mkdir()
        self.addCleanup(shutil.rmtree, self.directory)

    def run_cli(self, source, *arguments):
        command = [sys.executable, str(ROOT / 'analyze_c.py'), str(source), '--compiler', self.gcc, '--json', *arguments]
        process = subprocess.run(command, capture_output=True, timeout=30, shell=False)
        self.assertNotIn(b'Traceback', process.stderr)
        return process.returncode, json.loads(process.stdout)

    def test_paths_spaces_standard_include_and_define(self):
        header = self.directory / 'settings.h'
        header.write_text('typedef struct { const char *name; int count; } Setting;\n')
        source = self.directory / 'valid source.c'
        source.write_text('#include "settings.h"\n#ifndef COUNT\n#error COUNT required\n#endif\nint main(void) { Setting s = {"hello", COUNT}; return s.count; }\n')
        before = source.read_bytes()
        code, report = self.run_cli(source, '--std', 'c11', '-I', str(self.directory), '-DCOUNT=2')
        self.assertEqual(code, 0, report)
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()), ['settings.h', 'valid source.c'])
        self.assertIn('-std=c11', report['execution']['command'])

    def test_unfamiliar_large_valid(self):
        source = self.directory / 'large valid.c'
        prefix = '#include <stddef.h>\ntypedef struct { const char *name; int values[2]; } Entry;\n'
        functions = '\n'.join(f'int entry_{i}(const Entry *p) {{ return p ? p->values[{i % 2}] : 0; }}' for i in range(620))
        source.write_text(prefix + functions + '\n')
        before = source.read_bytes()
        code, report = self.run_cli(source)
        self.assertEqual(code, 0, report)
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(list(self.directory.iterdir()), [source])

    def test_unfamiliar_large_multiple_errors(self):
        source = self.directory / 'large invalid.c'
        lines = ['typedef struct { const char *text; int count; } Entry;']
        error_lines = set()
        for i in range(620):
            if i in (10, 310, 610):
                lines.append(f'int test_{i}(void) {{ return unknown_{i}; }}')
                error_lines.add(len(lines))
            else:
                lines.append(f'int test_{i}(const Entry *entry) {{ return entry->count; }}')
        source.write_text('\n'.join(lines) + '\n')
        before = source.read_bytes()
        code, report = self.run_cli(source)
        self.assertEqual(code, 1, report)
        self.assertTrue(error_lines.issubset({d['line'] for d in report['diagnostics'] if d['severity'] == 'error'}))
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(source.read_bytes(), before)

    def test_missing_file_tool_failure(self):
        code, report = self.run_cli(self.directory / 'missing.c')
        self.assertEqual(code, 3)
        self.assertEqual(report['status'], 'failed')

    def test_missing_header_incomplete(self):
        code, report = self.run_cli(FIXTURES / 'missing_header.c')
        self.assertEqual(code, 3)
        self.assertEqual(report['status'], 'partial')

    def test_wrong_file_type(self):
        source = self.directory / 'source.txt'
        source.write_text('int main(void) { return 0; }')
        code, report = self.run_cli(source)
        self.assertEqual(code, 3)
        self.assertIn('.c extension', report['tool_issues'][0])

    def test_missing_compiler(self):
        process = subprocess.run([sys.executable, str(ROOT / 'analyze_c.py'), str(FIXTURES / 'valid.c'), '--compiler', str(self.directory / 'not-installed.exe'), '--json'], capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 3)
        self.assertEqual(json.loads(process.stdout)['status'], 'failed')

    def test_unsupported_standard_is_clear_tool_failure(self):
        code, report = self.run_cli(FIXTURES / 'valid.c', '--std', 'smartparse-nonexistent-standard')
        self.assertEqual(code, 3)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('unsupported', report['tool_issues'][0])

    def test_malformed_bytes_preserved(self):
        source = self.directory / 'malformed.c'
        source.write_bytes(b'int main(void) { return \xff; }\n')
        before = source.read_bytes()
        code, report = self.run_cli(source)
        self.assertEqual(code, 1, report)
        self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
