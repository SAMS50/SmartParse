
import unittest

from smartparse import (
    Parser,
    StrictParser,
    ParseError,
    Token,
    tokenize,
    analyze,
    apply_candidate,
    probe_candidate,
    choose_validated_candidate
)
from recovery import rank_candidates


class GrammarValidationTests(unittest.TestCase):

    def test_01_strict_parser_accepts_valid_code(self):
        tokens = tokenize(
            "int x = 5;\nint y = x + 1;\n"
        )
        parser = StrictParser(tokens)
        parser.parse()

        self.assertEqual(parser.i, len(tokens) - 1)

    def test_02_strict_parser_rejects_missing_semicolon(self):
        tokens = tokenize(
            "int x = 5\nint y = 10;\n"
        )
        parser = StrictParser(tokens)

        with self.assertRaises(ParseError):
            parser.parse()

    def test_03_insertion_does_not_mutate_original(self):
        tokens = tokenize(
            "int x = 5\nint y = 10;\n"
        )
        original = list(tokens)

        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "int" and i > 0
        )

        candidates = rank_candidates(
            tokens, index, ";"
        )
        insertion = next(
            c for c in candidates
            if c.operation == "insert"
        )

        trial = apply_candidate(
            tokens, index, insertion
        )

        self.assertEqual(tokens, original)
        self.assertEqual(len(trial), len(tokens) + 1)
        self.assertEqual(trial[index].value, ";")

    def test_04_probe_can_validate_insertion(self):
        tokens = tokenize(
            "int x = 5\nint y = 10;\n"
        )
        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "int" and i > 0
        )

        candidate = rank_candidates(
            tokens, index, ";"
        )[0]

        result = probe_candidate(
            tokens, index, candidate
        )

        self.assertTrue(result["completed"])

    def test_05_multiple_candidates_are_compared(self):
        tokens = tokenize(
            "if (x > 5 }"
        )

        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "}"
        )

        candidates = rank_candidates(
            tokens, index, ")"
        )

        self.assertGreaterEqual(
            len(candidates), 2
        )

        chosen, validation = (
            choose_validated_candidate(
                tokens, index, candidates
            )
        )

        self.assertIn(chosen, candidates)
        self.assertEqual(
            validation["candidates_tested"],
            len(candidates)
        )

        self.assertEqual(
            len(validation["alternatives"]),
            len(candidates)
        )

    def test_06_recovery_keeps_source_unchanged(self):
        source = (
            "int x = 5\n"
            "int y = 10;\n"
        )
        original = source[:]

        _, diagnostics, repairs = analyze(source)

        self.assertEqual(source, original)
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(len(repairs), 1)

    def test_07_existing_error_recovery(self):
        source = (
            "int x = 5\n"
            "int y = 10\n"
            "int z = 15;\n"
        )

        _, diagnostics, repairs = analyze(source)

        self.assertEqual(len(diagnostics), 2)
        self.assertEqual(len(repairs), 2)

    def test_08_validation_metadata_available(self):
        tokens = tokenize("if (x > 5 }")
        index = next(
            i for i, token in enumerate(tokens)
            if token.value == "}"
        )

        candidates = rank_candidates(
            tokens, index, ")"
        )

        _, metadata = choose_validated_candidate(
            tokens, index, candidates
        )

        self.assertEqual(
            metadata["method"],
            "strict_grammar_probe"
        )
        self.assertIn("progress", metadata)
        self.assertIn("completed", metadata)


if __name__ == "__main__":
    unittest.main()
