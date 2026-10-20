
import unittest

from smartparse import tokenize
from verification_eval import (
    TracedParser,
    audit_recovery,
    audit_baseline,
    measure_performance
)


class VerificationTests(unittest.TestCase):

    def test_01_valid_statement_trace(self):
        parser = TracedParser(
            tokenize("int x = 5;")
        )
        parser.parse()

        self.assertEqual(
            len(parser.diagnostics), 0
        )

        self.assertTrue(
            any(
                item["status"] == "returned"
                for item in parser.trace
            )
        )

    def test_02_recovery_is_traced(self):
        parser = TracedParser(
            tokenize(
                "int x = 5\nint y = 10;"
            )
        )
        parser.parse()

        self.assertGreaterEqual(
            len(parser.repairs), 1
        )

        self.assertTrue(
            any(
                item["new_repairs"] > 0
                for item in parser.trace
            )
        )

    def test_03_recovery_audit_returns_rows(self):
        rows = audit_recovery()

        self.assertEqual(len(rows), 12)

        for row in rows:
            self.assertGreaterEqual(
                row["statement_attempts"], 1
            )

    def test_04_baseline_audit_returns_rows(self):
        rows = audit_baseline()

        self.assertGreater(
            len(rows), 0
        )

    def test_05_performance_audit_returns_rows(self):
        rows = measure_performance(
            repetitions=3
        )

        self.assertEqual(len(rows), 9)

        for row in rows:
            self.assertGreaterEqual(
                row["median_ms"], 0
            )


if __name__ == "__main__":
    unittest.main()
