import unittest
from phase5d_eval import CASES, evaluate
from smartparse import tokenize
from cgar_verified import _strict_error

class Phase5DEvaluationTests(unittest.TestCase):
    def test_reference_programs_are_valid(self):
        for case in CASES:
            with self.subTest(case=case.name):
                self.assertIsNone(_strict_error(tokenize(case.reference)))
    def test_evaluation_has_all_cases(self):
        self.assertEqual(len(evaluate(repeats=1)),len(CASES))
    def test_exact_is_not_grammar_valid(self):
        for row in evaluate(repeats=1):
            self.assertFalse(row['exact_reference'] and not row['grammar_valid'])
    def test_invalid_repeats(self):
        with self.assertRaises(ValueError):evaluate(repeats=0)
