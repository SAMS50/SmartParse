import unittest
from cgar_verified import plan, _strict_error
from smartparse import tokenize

class VerifiedCGARTests(unittest.TestCase):
    def test_missing_semicolon(self):
        result = plan('int x = 1')
        self.assertIsNotNone(result)
        self.assertEqual(result.status, 'grammar_valid')
        self.assertTrue(any(op == 'insert' for op,_,_ in result.edits))

    def test_wrong_closer(self):
        result = plan('if (x > 1] { x = 2; }')
        self.assertIsNotNone(result)
        self.assertIsNone(_strict_error(result.corrected))

    def test_multiple_errors(self):
        result = plan('int x = 1 if (x > 0] { x = 2; }', max_edits=3)
        self.assertIsNotNone(result)
        self.assertIsNone(_strict_error(result.corrected))

    def test_budget_exhaustion(self):
        self.assertIsNone(plan('int x = 1 if (x > 0] { x = 2; }', max_edits=1))

    def test_valid_input_no_changes(self):
        result = plan('int x = 1;')
        self.assertEqual(result.edits, ())

    def test_source_not_mutated(self):
        source = 'int x = 1'
        before = tuple(t.value for t in tokenize(source))
        plan(source)
        self.assertEqual(before,tuple(t.value for t in tokenize(source)))

    def test_reject_bad_budgets(self):
        with self.assertRaises(ValueError):
            plan('int x;', max_nodes=0)

if __name__ == '__main__': unittest.main()
