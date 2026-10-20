
import unittest

from ambiguous_benchmark import (
    CASES,
    locate_error,
    evaluate_case,
    strict_parse_succeeds
)
from smartparse import tokenize


class AmbiguousBenchmarkTests(unittest.TestCase):

    def test_01_all_cases_are_ambiguous(self):
        for case in CASES:
            tokens = tokenize(case["source"])
            _, candidates = locate_error(
                tokens, case
            )
            self.assertGreaterEqual(
                len(candidates), 2
            )

    def test_02_validated_mode_invokes_probes(self):
        for case in CASES:
            result = evaluate_case(
                case, validate_repairs=True
            )
            self.assertEqual(
                result["grammar_probes"], 1
            )

    def test_03_heuristic_mode_has_no_probes(self):
        for case in CASES:
            result = evaluate_case(
                case, validate_repairs=False
            )
            self.assertEqual(
                result["grammar_probes"], 0
            )

    def test_04_valid_program_strictly_parses(self):
        tokens = tokenize(
            "if (x > 5) { x = 1; }"
        )
        self.assertTrue(
            strict_parse_succeeds(tokens)
        )

    def test_05_both_modes_produce_results(self):
        for case in CASES:
            for enabled in (False, True):
                result = evaluate_case(
                    case,
                    validate_repairs=enabled
                )

                self.assertIn(
                    result["chosen_operation"],
                    {
                        "insert",
                        "delete",
                        "substitute",
                        "none"
                    }
                )

                self.assertIn(
                    result["correct_repair"],
                    (0, 1)
                )


if __name__ == "__main__":
    unittest.main()
