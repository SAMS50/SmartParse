import unittest
from cgar_reliable import advise
from cgar_verified import _strict_error
from phase5e_eval import evaluate

class Phase5ETests(unittest.TestCase):
    def test_consecutive_semicolons_are_not_silently_removed(self):
        a=advise('int x = 1;;')
        self.assertEqual(a.status,'ambiguous_valid')
        self.assertIsNone(a.result)

    def test_declaration_operator_repair(self):
        a=advise('int x == 1;')
        self.assertEqual(a.status,'verified_candidate')
        self.assertEqual(a.result.edits[0][2], '==->=')
        self.assertIsNone(_strict_error(a.result.corrected))

    def test_missing_identifier_abstains(self):
        self.assertEqual(advise('int = 1;').status,'abstain')

    def test_missing_expression_abstains(self):
        self.assertEqual(advise('int x = ;').status,'abstain')

    def test_valid_unchanged(self):
        self.assertEqual(advise('int x = 1;').status,'unchanged')

    def test_budget_validation(self):
        with self.assertRaises(ValueError): advise('int x;',max_nodes=0)

    def test_frozen_cases(self):
        rows=evaluate()
        self.assertEqual(len(rows),16)
        self.assertEqual(sum(r['wrong_suggestion'] for r in rows),0)
        self.assertEqual(sum(r['exact_reference'] for r in rows),13)

if __name__=='__main__': unittest.main()
