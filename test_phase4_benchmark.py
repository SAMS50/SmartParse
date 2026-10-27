import unittest
from phase4_benchmark import make_holdout, make_scaling, evaluate_holdout, evaluate_scaling


class Phase4Tests(unittest.TestCase):
    def test_holdout_deterministic(self):
        self.assertEqual(make_holdout(101), make_holdout(101))
        self.assertNotEqual(make_holdout(101), make_holdout(202))

    def test_holdout_has_two_intended_repairs(self):
        self.assertTrue(all(len(expected) == 2 for _, _, expected in make_holdout(101)))

    def test_scaling_injected_pair_count(self):
        source, count = make_scaling(120, 101, 4)
        self.assertEqual(count, 8)
        self.assertEqual(source.count(' ; ] {'), 4)

    def test_all_modes_report(self):
        rows = evaluate_holdout((101,), 1)
        self.assertEqual(len(rows), 48)
        self.assertEqual({r['mode'] for r in rows}, {'legacy', 'contextual', 'selective', 'bounded_pair'})

    def test_scaling_has_memory_measurements(self):
        rows = evaluate_scaling((120,), (101,), 1)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r['peak_tracemalloc_kib'] > 0 for r in rows))


if __name__ == '__main__':
    unittest.main()
