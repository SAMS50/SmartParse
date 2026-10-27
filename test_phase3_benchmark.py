import unittest
from phase3_benchmark import evaluate
from smartparse import Parser, tokenize


class BoundedPairTests(unittest.TestCase):
    def test_two_edits_at_same_expectation(self):
        p = Parser(tokenize('if (x > 5 ; ] { x = 1; }'), multi_token_recovery=True)
        p.parse()
        self.assertEqual([(r['operation'], r['token'], r['from']) for r in p.repairs],
                         [('delete', ')', ';'), ('substitute', ')', ']')])
        self.assertEqual(p.multi_token_stats['accepted'], 1)

    def test_opt_in_preserves_previous_behavior(self):
        p = Parser(tokenize('if (x > 5 ; ] { x = 1; }'))
        p.parse()
        self.assertEqual(p.multi_token_stats['accepted'], 0)

    def test_single_token_deletion_unchanged(self):
        p = Parser(tokenize('if (x > 5 ; ) { x = 1; }'), multi_token_recovery=True)
        p.parse()
        self.assertEqual(p.repairs[0]['operation'], 'delete')
        self.assertEqual(p.multi_token_stats['accepted'], 0)

    def test_benchmark_improves_frozen_cases(self):
        rows = evaluate(1)
        old = [r for r in rows if r['mode'] == 'phase2']
        new = [r for r in rows if r['mode'] == 'bounded_pair']
        self.assertGreater(sum(r['correct_repairs'] for r in new),
                           sum(r['correct_repairs'] for r in old))

    def test_bad_repeats(self):
        with self.assertRaises(ValueError):
            evaluate(0)


if __name__ == '__main__':
    unittest.main()
