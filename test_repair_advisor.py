import unittest
from smartparse import tokenize
from repair_advisor import advise


class RepairAdvisorTests(unittest.TestCase):
    def test_pair_marked_for_review(self):
        ts = tokenize('if (x > 1 ; ] { x = 2; }')
        idx = next(i for i, t in enumerate(ts) if t.value == ';')
        result = advise(ts, idx, ')')
        self.assertEqual(result.status, 'review')
        self.assertIn('delete', result.alternatives[0])

    def test_unsupported_abstains(self):
        ts = tokenize('int x = 1;')
        idx = next(i for i, t in enumerate(ts) if t.value == 'x')
        self.assertEqual(advise(ts, idx, ')').status, 'abstain')

    def test_single_candidate_not_overconfident(self):
        ts = tokenize('int x = 1;')
        idx = next(i for i, t in enumerate(ts) if t.value == ';')
        self.assertEqual(advise(ts, idx, ')').status, 'review')

    def test_invalid_margin(self):
        with self.assertRaises(ValueError):
            advise(tokenize('int x;'), 0, ';', margin=-1)

    def test_out_of_range(self):
        with self.assertRaises(IndexError):
            advise(tokenize('int x;'), 999, ';')
