
import unittest

from smartparse import tokenize, analyze
from recovery import rank_candidates
from local_validation import (
    apply_candidate,
    probe_candidate,
    choose_candidate
)


SOURCE = (
    "int a = 1\n"
    "int b = 2;\n"
    "if (x > 5 ; ) x = 1;\n"
)


def get_case():
    tokens = tokenize(SOURCE)

    start = next(
        i for i, token in enumerate(tokens)
        if token.value == "if"
    )

    index = next(
        i for i, token in enumerate(tokens)
        if i > start and token.value == ";"
    )

    candidates = rank_candidates(
        tokens, index, ")"
    )

    return tokens, start, index, candidates


class LocalValidationTests(unittest.TestCase):

    def test_01_multiple_candidates_exist(self):
        _, _, _, candidates = get_case()

        operations = {
            candidate.operation
            for candidate in candidates
        }

        self.assertIn("insert", operations)
        self.assertIn("delete", operations)

    def test_02_original_tokens_are_preserved(self):
        tokens, _, index, candidates = get_case()
        original = list(tokens)

        for candidate in candidates:
            apply_candidate(
                tokens, index, candidate
            )

        self.assertEqual(tokens, original)

    def test_03_local_probe_ignores_earlier_error(self):
        tokens, start, index, candidates = get_case()

        deletion = next(
            candidate for candidate in candidates
            if candidate.operation == "delete"
        )

        result = probe_candidate(
            tokens, start, index, deletion
        )

        self.assertTrue(result.completed)
        self.assertTrue(result.reached_repair)

    def test_04_local_ranking_prefers_deletion(self):
        tokens, start, index, candidates = get_case()

        chosen, metadata = choose_candidate(
            tokens, start, index, candidates
        )

        self.assertEqual(
            chosen.operation, "delete"
        )
        self.assertEqual(
            metadata["method"],
            "local_statement_probe"
        )

    def test_05_validation_runs_in_actual_parser(self):
        _, _, repairs = analyze(SOURCE)

        validated = [
            repair for repair in repairs
            if repair["grammar_validation"] is not None
        ]

        self.assertGreaterEqual(
            len(validated), 1
        )

        self.assertEqual(
            validated[0]["grammar_validation"]["method"],
            "local_statement_probe"
        )

    def test_06_local_probe_reports_alternatives(self):
        tokens, start, index, candidates = get_case()

        _, metadata = choose_candidate(
            tokens, start, index, candidates
        )

        self.assertEqual(
            metadata["candidates_tested"],
            len(candidates)
        )
        self.assertEqual(
            len(metadata["alternatives"]),
            len(candidates)
        )


if __name__ == "__main__":
    unittest.main()
