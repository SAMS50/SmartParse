
import unittest

from smartparse import analyze, tokenize
from recovery import (
    context,
    generate_candidates,
    rank_candidates
)


class SmartParseTests(unittest.TestCase):

    def test_valid_program(self):
        source = (
            "int x = 5; "
            "if (x > 2) { x = x + 1; }"
        )

        _, errors, repairs = analyze(source)

        self.assertEqual(errors, [])
        self.assertEqual(repairs, [])

    def test_missing_parenthesis(self):
        source = "if (x > 2 { x = 3; }"

        _, errors, repairs = analyze(source)

        self.assertTrue(
            any(
                "Missing ')'" in error["message"]
                for error in errors
            )
        )

        self.assertTrue(
            any(
                repair["operation"] == "insert"
                for repair in repairs
            )
        )

    def test_missing_semicolon(self):
        source = "int x = 5\nint y = 3;"

        _, errors, repairs = analyze(source)

        self.assertTrue(
            any(
                "Missing ';'" in error["message"]
                for error in errors
            )
        )

    def test_wrong_closing_bracket(self):
        source = "if (x > 2] { x = 3; }"

        _, errors, repairs = analyze(source)

        self.assertTrue(
            any(
                repair["operation"] == "substitute"
                for repair in repairs
            )
        )

    def test_valid_empty_statement(self):
        source = "int x = 5;;"

        _, errors, repairs = analyze(source)

        self.assertEqual(errors, [])
        self.assertEqual(repairs, [])

    def test_source_not_modified(self):
        source = "if (x > 2 { x = 3; }"
        original = source

        analyze(source)

        self.assertEqual(source, original)


class ContextAnalyzerTests(unittest.TestCase):

    def test_bracket_nesting(self):
        tokens = tokenize(
            "if (x > 2 { x = 3; }"
        )

        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "{"
        )

        result = context(tokens, index, ")")

        self.assertIn("(", result["nesting"])
        self.assertEqual(result["current"], "{")
        self.assertEqual(result["expected"], ")")


class CandidateTests(unittest.TestCase):

    def test_insertion_candidate(self):
        tokens = tokenize(
            "if (x > 2 { x = 3; }"
        )

        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "{"
        )

        candidates = generate_candidates(
            tokens, index, ")"
        )

        self.assertTrue(
            any(
                candidate.operation == "insert"
                for candidate in candidates
            )
        )

    def test_substitution_candidate(self):
        tokens = tokenize(
            "if (x > 2] { x = 3; }"
        )

        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "]"
        )

        candidates = rank_candidates(
            tokens, index, ")"
        )

        self.assertEqual(
            candidates[0].operation,
            "substitute"
        )

    def test_deletion_candidate(self):
        tokens = tokenize("x ; )")

        candidates = rank_candidates(
            tokens, 1, ")"
        )

        self.assertEqual(
            candidates[0].operation,
            "delete"
        )


if __name__ == "__main__":
    unittest.main()
