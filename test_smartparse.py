
import unittest

from smartparse import analyze, tokenize
from recovery import context, rank_candidates


class SmartParseTests(unittest.TestCase):

    def check_valid(self, source):
        _, errors, repairs = analyze(source)
        self.assertEqual(errors, [])
        self.assertEqual(repairs, [])

    def test_01_valid_declaration(self):
        self.check_valid("int x = 5;")

    def test_02_valid_if_else(self):
        self.check_valid(
            "if (x > 2) { x = 3; } else { x = 4; }"
        )

    def test_03_valid_while(self):
        self.check_valid(
            "while (x < 10) { x = x + 1; }"
        )

    def test_04_valid_for(self):
        self.check_valid(
            "for (int i = 0; i < 10; i++) { x = x + i; }"
        )

    def test_05_valid_function(self):
        self.check_valid(
            "int add(int a, int b) { return a + b; }"
        )

    def test_06_valid_function_call(self):
        self.check_valid(
            "int x = add(2, 3);"
        )

    def test_07_missing_parenthesis(self):
        _, errors, repairs = analyze(
            "if (x > 2 { x = 3; }"
        )
        self.assertTrue(
            any("Missing ')'" in e["message"] for e in errors)
        )
        self.assertTrue(
            any(r["operation"] == "insert" for r in repairs)
        )

    def test_08_missing_semicolon(self):
        _, errors, repairs = analyze(
            "int x = 5\nint y = 3;"
        )
        self.assertTrue(
            any("Missing ';'" in e["message"] for e in errors)
        )

    def test_09_wrong_bracket(self):
        _, errors, repairs = analyze(
            "if (x > 2] { x = 3; }"
        )
        self.assertTrue(
            any(r["operation"] == "substitute" for r in repairs)
        )

    def test_10_multiple_errors(self):
        source = """
        int x = 5
        int y = 10
        int z = 15;
        """
        _, errors, repairs = analyze(source)
        self.assertEqual(len(errors), 2)
        self.assertEqual(len(repairs), 2)

    def test_11_recovery_continues(self):
        source = """
        int x = 5
        int y = 10;
        if (y > 2 { y = y + 1; }
        """
        _, errors, repairs = analyze(source)
        self.assertEqual(len(errors), 2)
        self.assertEqual(len(repairs), 2)

    def test_12_source_preserved(self):
        source = "if (x > 2 { x = 3; }"
        original = source
        analyze(source)
        self.assertEqual(source, original)

    def test_13_context_nesting(self):
        tokens = tokenize("if (x > 2 { x = 3; }")
        index = next(
            i for i, t in enumerate(tokens)
            if t.value == "{"
        )
        ctx = context(tokens, index, ")")
        self.assertIn("(", ctx["nesting"])

    def test_14_candidate_insertion(self):
        tokens = tokenize("if (x > 2 { x = 3; }")
        index = next(
            i for i, t in enumerate(tokens)
            if t.value == "{"
        )
        candidates = rank_candidates(tokens, index, ")")
        self.assertEqual(candidates[0].operation, "insert")

    def test_15_candidate_substitution(self):
        tokens = tokenize("if (x > 2] { x = 3; }")
        index = next(
            i for i, t in enumerate(tokens)
            if t.value == "]"
        )
        candidates = rank_candidates(tokens, index, ")")
        self.assertEqual(candidates[0].operation, "substitute")

    def test_16_candidate_deletion(self):
        tokens = tokenize("x ; )")
        candidates = rank_candidates(tokens, 1, ")")
        self.assertEqual(candidates[0].operation, "delete")

    def test_17_empty_statement(self):
        self.check_valid("int x = 5;;")

    def test_18_nested_blocks(self):
        self.check_valid(
            "int x = 0; { { x = 1; } }"
        )


if __name__ == "__main__":
    unittest.main()
