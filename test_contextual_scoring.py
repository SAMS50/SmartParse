import unittest
from smartparse import Parser, tokenize
from recovery import rank_candidates


class ContextualScoringTests(unittest.TestCase):
    def test_missing_semicolon_explained(self):
        tokens = tokenize("int a = 1\nint b = 2;")
        index = next(i for i, t in enumerate(tokens) if i and t.value == "int")
        best = rank_candidates(tokens, index, ";")[0]
        self.assertEqual(best.operation, "insert")
        self.assertIn("statement_boundary_fit", dict(best.factors))

    def test_wrong_closer_uses_nesting(self):
        tokens = tokenize("if (x > 2] { x = 3; }")
        index = next(i for i, t in enumerate(tokens) if t.value == "]")
        best = rank_candidates(tokens, index, ")")[0]
        self.assertEqual(best.operation, "substitute")
        self.assertIn("matching_opener_in_context", dict(best.factors))

    def test_competing_candidates_prefers_delete(self):
        tokens = tokenize("if (x > 5 ; ) x = 1;")
        index = next(i for i, t in enumerate(tokens) if t.value == ";")
        options = rank_candidates(tokens, index, ")")
        self.assertGreaterEqual(len(options), 2)
        self.assertEqual(options[0].operation, "delete")

    def test_legacy_unchanged(self):
        tokens = tokenize("int a = 1\nint b = 2;")
        index = next(i for i, t in enumerate(tokens) if i and t.value == "int")
        self.assertEqual(rank_candidates(tokens, index, ";", mode="legacy")[0].score, 10)

    def test_parser_emits_explanations(self):
        parser = Parser(tokenize("int a = 1\nint b = 2;"))
        parser.parse()
        self.assertEqual(len(parser.repairs), 1)
        self.assertTrue(parser.repairs[0]["score_factors"])
        self.assertEqual(parser.repairs[0]["scoring_mode"], "contextual")

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            rank_candidates(tokenize("int a;"), 0, ";", mode="bad")


if __name__ == "__main__":
    unittest.main()
