import unittest
from mixed_benchmark import make_program, run_case, score_detection, score_recovery
from smartparse import StrictParser, tokenize


class MixedBenchmarkTests(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(make_program(120, 12, 3), make_program(120, 12, 3))

    def test_valid_reference(self):
        _, _, valid = make_program(120, 12)
        self.assertEqual(StrictParser(tokenize(valid)).parse(), [])

    def test_all_operations_labelled(self):
        _, labels, _ = make_program(120, 12)
        self.assertEqual({x['operation'] for x in labels}, {'insert', 'delete', 'substitute'})

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            make_program(10, 1)
        with self.assertRaises(ValueError):
            make_program(120, 41)

    def test_recovery_metric_is_not_diagnostic_metric(self):
        labels = [{'line': 2, 'column': 1, 'operation': 'insert', 'token': ';'}]
        self.assertEqual(score_detection(labels, [{'line': 2, 'column': 1}]), (1, 0, 0))
        self.assertEqual(score_recovery(labels, [{'line': 2, 'column': 1,
                                                  'operation': 'delete', 'token': ';'}]), 0)

    def test_runs_both_modes(self):
        source, labels, _ = make_program(120, 9)
        for mode in ('panic', 'legacy', 'contextual', 'validated'):
            row = run_case(source, labels, mode, 1)
            self.assertEqual(row['injected_errors'], 9)
            self.assertGreaterEqual(row['tp'], 0)


if __name__ == '__main__':
    unittest.main()
