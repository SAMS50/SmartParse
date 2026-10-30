import copy
import unittest

from acceptance.checks import clean_numbered_source, validate_report
from extended_c import AnalysisResult, Diagnostic, to_report


class AcceptanceChecksTests(unittest.TestCase):
    def test_clean_preserves_line_numbers_endings_and_bytes(self):
        original = b'001 | #include <stdio.h>\r\n002 | \r\n003 | int x = \xff;\r\n'
        cleaned, changed = clean_numbered_source(original)
        self.assertTrue(changed)
        self.assertEqual(cleaned, b'#include <stdio.h>\r\n\r\nint x = \xff;\r\n')
        self.assertEqual(len(cleaned.splitlines()), len(original.splitlines()))

    def test_unprefixed_program_unchanged(self):
        original = b'int x = 1 | 2;\n'
        self.assertEqual(clean_numbered_source(original), (original, False))

    def test_rejects_ambiguous_line_mapping(self):
        for data in (b'002 | int x;\n', b'001 | int x;\n003 | int y;\n', b'001 | int x;\nint y;\n'):
            with self.assertRaises(ValueError):
                clean_numbered_source(data)

    def test_validates_regular_and_analyzer_reports(self):
        result = AnalysisResult('completed', static_analysis=AnalysisResult('unavailable', findings=[]))
        self.assertTrue(validate_report(to_report(result)))

    def test_rejects_wrong_schema_types_and_counts(self):
        report = to_report(AnalysisResult('completed', diagnostics=[Diagnostic('x.c', 1, 1, 'error', 'bad', 'gcc')]))
        for change in ('count', 'location', 'backend', 'field'):
            bad = copy.deepcopy(report)
            if change == 'count':
                bad['summary']['errors'] = 0
            elif change == 'location':
                bad['diagnostics'][0]['line'] = '1'
            elif change == 'backend':
                bad['diagnostics'][0]['backend'] = 'CGAR'
            else:
                del bad['diagnostics'][0]['source_snippet']
            with self.assertRaises(ValueError):
                validate_report(bad)


if __name__ == '__main__':
    unittest.main()
