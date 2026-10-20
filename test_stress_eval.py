
import unittest

from stress_eval import (
    STRESS_CASES,
    strict_accepts,
    run_smartparse,
    evaluate_stress_case,
    timed_run
)


class StressEvaluationTests(unittest.TestCase):

    def test_01_corrected_references_are_valid(self):
        for case in STRESS_CASES:
            with self.subTest(case=case["id"]):
                self.assertTrue(
                    strict_accepts(case["corrected"])
                )

    def test_02_invalid_code_fails_strict_parser(self):
        self.assertFalse(
            strict_accepts(
                "int x = 1\nint y = 2;"
            )
        )

    def test_03_both_modes_return_results(self):
        for case in STRESS_CASES:
            with self.subTest(case=case["id"]):
                results = evaluate_stress_case(case)

                self.assertIn("heuristic", results)
                self.assertIn("validated", results)

    def test_04_valid_program_has_no_diagnostics(self):
        source = STRESS_CASES[4]["source"]

        for validated in (False, True):
            result = run_smartparse(
                source, validated
            )

            self.assertEqual(
                result["diagnostics"], []
            )
            self.assertTrue(
                result["reached_eof"]
            )

    def test_05_heuristic_mode_has_no_probes(self):
        for case in STRESS_CASES:
            result = run_smartparse(
                case["source"], False
            )

            self.assertEqual(
                result["grammar_probes"], 0
            )

    def test_06_timing_returns_valid_measurements(self):
        result = timed_run(
            "int x = 5;",
            "heuristic",
            repetitions=5
        )

        self.assertGreaterEqual(
            result["mean_ms"], 0
        )
        self.assertGreaterEqual(
            result["median_ms"], 0
        )
        self.assertLessEqual(
            result["min_ms"],
            result["max_ms"]
        )


if __name__ == "__main__":
    unittest.main()
