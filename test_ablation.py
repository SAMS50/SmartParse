
import unittest

from ablation_eval import run_mode
from dataset import DATASET
from metrics import evaluate_diagnostics


class AblationTests(unittest.TestCase):

    def test_01_valid_program_all_modes(self):
        source = "int x = 5;"

        for mode in (
            "panic",
            "heuristic",
            "grammar_validated"
        ):
            result = run_mode(source, mode)

            self.assertEqual(
                len(result["diagnostics"]), 0
            )

    def test_02_heuristic_has_no_probes(self):
        source = "if (x > 5 ; ) x = 1;"

        result = run_mode(
            source, "heuristic"
        )

        for repair in result["repairs"]:
            self.assertIsNone(
                repair["grammar_validation"]
            )

    def test_03_validated_mode_runs_probe(self):
        source = "if (x > 5 ; ) x = 1;"

        result = run_mode(
            source, "grammar_validated"
        )

        probes = [
            repair
            for repair in result["repairs"]
            if repair["grammar_validation"] is not None
        ]

        self.assertGreaterEqual(
            len(probes), 1
        )

    def test_04_heuristic_detects_semicolon(self):
        source = "int x = 5\nint y = 10;"

        result = run_mode(
            source, "heuristic"
        )

        self.assertEqual(
            len(result["diagnostics"]), 1
        )

    def test_05_validated_detects_semicolon(self):
        source = "int x = 5\nint y = 10;"

        result = run_mode(
            source, "grammar_validated"
        )

        self.assertEqual(
            len(result["diagnostics"]), 1
        )

    def test_06_dataset_scoring(self):
        case = DATASET[2]

        for mode in (
            "panic",
            "heuristic",
            "grammar_validated"
        ):
            result = run_mode(
                case["source"], mode
            )

            scores = evaluate_diagnostics(
                case["errors"],
                result["diagnostics"]
            )

            self.assertEqual(scores["tp"], 1)
            self.assertEqual(scores["fn"], 0)


if __name__ == "__main__":
    unittest.main()
