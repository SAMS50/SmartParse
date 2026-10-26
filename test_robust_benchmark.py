import unittest
from robust_benchmark import build_case, evaluate, summarize
from smartparse import StrictParser, tokenize


class RobustBenchmarkTests(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(build_case(120, 10, 4, 'clustered'),
                         build_case(120, 10, 4, 'clustered'))

    def test_valid_references(self):
        for layout in ('clustered', 'dispersed'):
            source, labels, valid = build_case(120, 10, 4, layout)
            self.assertEqual(len(labels), 10)
            StrictParser(tokenize(valid)).parse()
            self.assertEqual(len(source.splitlines()), 120)

    def test_exact_label_positions(self):
        for layout in ('clustered', 'dispersed'):
            source, labels, _ = build_case(120, 10, 4, layout)
            lines = source.splitlines()
            for label in labels:
                self.assertIn(label['operation'], ('insert', 'substitute', 'delete'))
                self.assertEqual(label['line'] % 6, 2)
                if label['operation'] != 'insert':
                    self.assertIn(lines[label['line'] - 1][label['column'] - 1], '];')

    def test_summary(self):
        rows = evaluate((120,), (7,), 6, 1)
        summary = summarize(rows)
        self.assertEqual(len(rows), 8)
        self.assertEqual(len(summary), 8)
        self.assertTrue(all(row['injected_errors'] == 6 for row in summary))


if __name__ == '__main__':
    unittest.main()
