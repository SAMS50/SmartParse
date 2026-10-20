
import unittest

from baseline import (
    PanicModeParser,
    analyze_baseline
)
from smartparse import tokenize


class BaselineFairnessTests(unittest.TestCase):

    def test_01_valid_nested_program(self):
        source = (
            "int main() {\n"
            "  int x = 1;\n"
            "  if (x > 0) {\n"
            "    x++;\n"
            "  }\n"
            "  return x;\n"
            "}"
        )

        result = analyze_baseline(source)

        self.assertEqual(
            len(result["diagnostics"]), 0
        )

    def test_02_preserves_enclosing_block(self):
        source = (
            "int main() {\n"
            "  if (x > 0 {\n"
            "    x++;\n"
            "  }\n"
            "  return x;\n"
            "}"
        )

        result = analyze_baseline(source)

        self.assertGreaterEqual(
            len(result["diagnostics"]), 1
        )

    def test_03_no_infinite_loop_on_stray_brace(self):
        result = analyze_baseline(
            "int x = 1; } int y = 2;"
        )

        self.assertGreaterEqual(
            len(result["diagnostics"]), 1
        )

    def test_04_baseline_never_repairs_tokens(self):
        result = analyze_baseline(
            "int x = 1\nint y = 2;"
        )

        self.assertEqual(
            result["repairs"], []
        )

    def test_05_block_depth_resets(self):
        parser = PanicModeParser(
            tokenize(
                "int main() { int x = 1; }"
            )
        )

        parser.parse()

        self.assertEqual(
            parser.block_depth, 0
        )


if __name__ == "__main__":
    unittest.main()
