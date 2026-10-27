"""Independent text adapters, report contracts, and real backend verification."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from extended_c import AnalysisResult, Compiler, analyze_file, format_terminal, to_json, to_report
from extended_c.diagnostics import Diagnostic, categorize, parse_output

FIXTURES = Path(__file__).parent / 'tests_fixtures' / 'extended_c'


class ParsingTests(unittest.TestCase):
    def test_live_clang_assignment_fix_hints_are_not_unknown_output(self):
        output = """x.c:7:15: note: place parentheses around the assignment to silence this warning
    if (value = 3) return value;
              ^
        (        )
x.c:7:15: note: use '==' to turn this assignment into an equality comparison
    if (value = 3) return value;
              ^
              ==
"""
        records, unknown = parse_output(output, 'clang')
        self.assertEqual(len(records), 2)
        self.assertEqual(unknown, [])
        self.assertEqual(records[0].source_snippet, '    if (value = 3) return value;')

    def test_clang_incompatible_result_type_is_semantic(self):
        records, _ = parse_output("x.c:3:55: error: returning 'struct Item' from a function with incompatible result type 'int'", 'clang')
        self.assertEqual(records[0].category, 'semantic/type')

    def test_old_gcc_snippet_and_notes(self):
        output = """test.c: In function 'main':
test.c:4:7: error: 'name' undeclared (first use in this function)
 int x = name;
         ^~~~
test.c:4:7: note: each undeclared identifier is reported only once
 for each function it appears in
"""
        records, unknown = parse_output(output, 'gcc')
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].source_snippet, 'int x = name;')
        self.assertEqual(records[0].category, 'semantic/type')
        self.assertIn('\nfor each function', records[1].message)
        self.assertEqual(records[1].category, 'unknown')
        self.assertEqual(unknown, [])

    def test_clang_modern_source_and_identifier(self):
        output = """C:\\work dir\\a.c:8:5: warning: using the result of an assignment as a condition
    without parentheses [-Wparentheses]
    8 | if (x = 2) return 0;
      |     ~~^~~
1 warning generated.
"""
        records, unknown = parse_output(output, 'clang')
        self.assertEqual(len(records), 1)
        d = records[0]
        self.assertEqual((d.file, d.line, d.column), ('C:\\work dir\\a.c', 8, 5))
        self.assertEqual(d.diagnostic_id, '-Wparentheses')
        self.assertEqual(d.source_snippet, 'if (x = 2) return 0;')
        self.assertEqual(d.category, 'compiler warning')
        self.assertEqual(unknown, [])

    def test_no_location_and_bare_diagnostic(self):
        records, _ = parse_output('clang: error: no input files\nwarning: strange [-Wexample]\na.h: note: included here\na.c:0:0: error: bad', 'clang')
        self.assertEqual(len(records), 4)
        self.assertIsNone(records[0].file)
        self.assertEqual(records[2].file, 'a.h')
        self.assertIsNone(records[3].line)
        self.assertIsNone(records[3].column)

    def test_unicode_and_color(self):
        records, _ = parse_output('\x1b[31m猫.c:1:2: error: expected ‘;’ before ‘猫’\x1b[0m', 'gcc')
        self.assertEqual(records[0].file, '猫.c')
        self.assertEqual(records[0].category, 'syntax')
        self.assertNotIn('\x1b', records[0].message)

    def test_unrecognized_and_malformed_records(self):
        records, unknown = parse_output('x.c:bogus: error? bad\n???\nx.c:1:1: error: something unfamiliar\nopaque trailer', 'gcc')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].category, 'unknown')
        self.assertEqual(len(unknown), 3)

    def test_source_text_is_not_an_extra_diagnostic(self):
        records, _ = parse_output('x.c:1:1: error: expected expression\n const char *x = "error: hello";\n ^~~~\n', 'gcc')
        self.assertEqual(len(records), 1)
        self.assertIn('error: hello', records[0].source_snippet)

    def test_repeated_real_headers_not_deduplicated(self):
        records, _ = parse_output('a.c:1:1: error: expected expression\na.c:1:1: error: expected expression', 'gcc')
        self.assertEqual(len(records), 2)

    def test_include_context(self):
        records, unknown = parse_output('In file included from a.c:1:\n                 from b.h:2:\na.h:3: error: expected identifier\ncompilation terminated.', 'gcc')
        self.assertEqual(len(records), 1)
        self.assertEqual(unknown, [])

    def test_option_not_invented_from_brackets(self):
        records, _ = parse_output('a.c:1:1: error: bad [some text]', 'clang')
        self.assertIsNone(records[0].diagnostic_id)
        self.assertTrue(records[0].message.endswith('[some text]'))
        records, _ = parse_output('a.c:1:1: error: incompatible pointer types [-Werror,-Wincompatible-pointer-types]', 'clang')
        self.assertEqual(records[0].diagnostic_id, '-Werror')
        self.assertEqual(records[0].message, 'incompatible pointer types')

    def test_malformed_huge_coordinate(self):
        records, _ = parse_output('x.c:' + '9' * 5000 + ':1: error: bad', 'gcc')
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].line)

    def test_unavailable_snippet_stays_null(self):
        records, _ = parse_output('absent.c:1:1: error: expected expression', 'clang')
        self.assertIsNone(records[0].source_snippet)


class CategoryTests(unittest.TestCase):
    def test_conservative_rules(self):
        for message in ('expected expression', "expected ';' before '}'", 'unterminated comment'):
            self.assertEqual(categorize('error', message), 'syntax')
        for message in ("'x' undeclared (first use)", 'unknown type name T', 'too few arguments to function f', 'incompatible types when returning type X'):
            self.assertEqual(categorize('error', message), 'semantic/type')
        for message in ('header not found', 'syntax or type problem', 'expected a miracle'):
            self.assertEqual(categorize('error', message), 'unknown')
        self.assertEqual(categorize('warning', 'incompatible pointer types'), 'compiler warning')
        self.assertEqual(categorize('note', 'expected expression'), 'unknown')


class ReportTests(unittest.TestCase):
    def result(self):
        return AnalysisResult('partial', Compiler('gcc', 'gcc', 'gcc 6.3.0', ('-Wall',)), [
            Diagnostic('猫.c', 2, 3, 'error', 'expected expression', 'gcc', 'syntax', 'int x = ;'),
            Diagnostic(None, None, None, 'warning', 'suspicious', 'gcc', 'compiler warning', diagnostic_id='-Wexample'),
            Diagnostic(None, None, None, 'note', 'context', 'gcc'),
            Diagnostic(None, None, None, 'fatal error', 'missing header', 'gcc'),
        ], returncode=1, stderr='raw\x1b text\n', issues=['incomplete'], unrecognized_output=['opaque'])

    def test_schema_and_json_roundtrip(self):
        result = self.result()
        report = to_report(result)
        self.assertEqual(json.loads(to_json(result)), report)
        self.assertEqual(report['schema_version'], '1.0')
        self.assertEqual(report['analysis_mode'], 'extended_c')
        self.assertEqual(set(report), {'schema_version', 'analysis_mode', 'status', 'compiler', 'summary', 'diagnostics', 'tool_issues', 'execution', 'raw_output', 'unrecognized_output'})
        self.assertEqual(set(report['diagnostics'][0]), {'file', 'line', 'column', 'severity', 'category', 'message', 'source_snippet', 'backend', 'diagnostic_id'})
        self.assertEqual(report['summary'], {'total_diagnostics': 4, 'errors': 2, 'warnings': 1, 'notes': 1,
                                           'categories': {'syntax': 1, 'semantic/type': 0, 'compiler warning': 1, 'unknown': 2}})
        self.assertEqual(report['raw_output']['stderr'], result.stderr)
        self.assertEqual(report['tool_issues'], ['incomplete'])
        self.assertIsNone(report['diagnostics'][1]['file'])
        self.assertIn('猫', to_json(result))

    def test_terminal_summary_and_issues(self):
        output = format_terminal(self.result())
        for text in ('external compiler', 'partial', 'gcc 6.3.0', '2 errors, 1 warnings, 1 notes', 'syntax=1', '猫.c:2:3', 'int x = ;', '[-Wexample]', 'Tool issue: incomplete', '<no location>'):
            self.assertIn(text, output)
        self.assertNotIn('CGAR', output)

    def test_failure_report_without_compiler(self):
        result = AnalysisResult('failed', issues=['compiler not found'])
        self.assertIsNone(to_report(result)['compiler'])
        self.assertEqual(to_report(result)['summary']['errors'], 0)
        self.assertIn('Compiler: unavailable', format_terminal(result))

    def test_terminal_controls_escaped(self):
        result = AnalysisResult('failed', issues=['bad\x1b[31m\rdata'])
        self.assertNotIn('\x1b', format_terminal(result))
        self.assertNotIn('\r', format_terminal(result))

    def test_unknown_mixed_output_marks_partial_and_preserves_raw(self):
        raw = b'x.c:1:1: error: expected expression\n???\xff\n'
        with patch('extended_c.backend.discover_compiler', return_value=self.result().compiler), patch('extended_c.backend._run', return_value=subprocess.CompletedProcess([], 1, b'', raw)):
            result = analyze_file(FIXTURES / 'valid.c')
        self.assertEqual(result.status, 'partial')
        self.assertEqual(len(result.diagnostics), 1)
        self.assertEqual(result.unrecognized_output, ['???\ufffd'])
        self.assertEqual(json.loads(to_json(result))['raw_output']['stderr'], raw.decode('utf-8', errors='replace'))


class BackendReportIntegrationTests(unittest.TestCase):
    def check_backend(self, backend):
        if not shutil.which(backend):
            self.skipTest(f'{backend} is not installed on PATH')
        path = FIXTURES / 'semantic.c'
        before = path.read_bytes()
        result = analyze_file(path, preference=backend)
        self.assertEqual(result.status, 'completed', result)
        self.assertEqual(path.read_bytes(), before)
        report = json.loads(to_json(result))
        self.assertGreaterEqual(report['summary']['errors'], 3)
        self.assertGreaterEqual(report['summary']['warnings'], 1)
        self.assertGreaterEqual(report['summary']['categories']['semantic/type'], 3)
        self.assertTrue(any(d['diagnostic_id'] == '-Wparentheses' for d in report['diagnostics']))
        self.assertTrue(any(d['source_snippet'] for d in report['diagnostics']))
        self.assertTrue(result.stderr)
        self.assertIn(result.compiler.version, format_terminal(result))

    def test_gcc_reporting(self):
        self.check_backend('gcc')

    def test_clang_reporting(self):
        self.check_backend('clang')


if __name__ == '__main__':
    unittest.main()
