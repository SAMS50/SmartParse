import unittest
from large_benchmark import make_program, measure


class LargeBenchmarkTests(unittest.TestCase):
    def test_deterministic_generation(self):
        self.assertEqual(make_program(100, 10, 4), make_program(100, 10, 4))

    def test_valid_program(self):
        source, truth = make_program(100, 0)
        for mode in ('panic', 'heuristic', 'validated'):
            result = measure(source, truth, mode, repeats=1)
            self.assertEqual(result['diagnostics'], 0)

    def test_missing_semicolons(self):
        source, truth = make_program(100, 10)
        result = measure(source, truth, 'heuristic', repeats=1)
        self.assertEqual(result['tp'], 10)
        self.assertEqual(result['fp'], 0)
        self.assertEqual(result['fn'], 0)

    def test_reject_bad_inputs(self):
        with self.assertRaises(ValueError):
            make_program(1, 0)
        with self.assertRaises(ValueError):
            make_program(100, 100)


if __name__ == '__main__':
    unittest.main()
