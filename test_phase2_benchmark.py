import unittest
from phase2_benchmark import CASES, evaluate
from smartparse import Parser, tokenize


class Phase2Tests(unittest.TestCase):
    def test_cases_include_multiple_errors_in_statement(self):
        self.assertTrue(any(len(label) > 1 for _, _, label in CASES))

    def test_selective_never_probes_more_than_all(self):
        rows = evaluate(1)
        for case_id, _, _ in CASES:
            full = next(r for r in rows if r['case'] == case_id and r['validation'] == 'all' and r['scoring'] == 'contextual')
            selective = next(r for r in rows if r['case'] == case_id and r['validation'] == 'selective')
            self.assertLessEqual(selective['performed_probes'], full['performed_probes'])

    def test_validation_policy_invalid(self):
        with self.assertRaises(ValueError):
            Parser(tokenize('int x;'), validation_policy='bad')

    def test_selective_skips_confident_competition(self):
        parser = Parser(tokenize('if (x > 5 ; ) x = 1;'), validation_policy='selective')
        parser.parse()
        self.assertGreater(parser.validation_stats['skipped_confident'], 0)


if __name__ == '__main__':
    unittest.main()
