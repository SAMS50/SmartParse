
from smartparse import Parser, ParseError, tokenize


class PanicModeParser(Parser):
    """
    Traditional panic-mode recovery baseline.

    Uses the same lexer and grammar as SmartParse,
    but disables context-aware local token repairs.
    """

    def __init__(self, tokens):
        super().__init__(tokens)
        self.skipped_tokens = 0
        self.recovery_events = []

    def expect(self, value):
        # No insertion, deletion, or substitution.
        if self.at(value):
            return self.take()

        raise ParseError(self.peek(), value)

    def panic_recover(self, error):
        token = error.token
        start = self.i
        skipped = []

        # Skip tokens until a synchronization point.
        while (
            self.peek().kind != "EOF"
            and self.peek().value not in (";", "}")
        ):
            skipped.append(self.take().value)

        # Consume semicolon to resume after statement.
        if self.at(";"):
            self.take()

        self.skipped_tokens += len(skipped)

        self.report(
            token,
            f"Expected {error.expected} before "
            f"'{token.value or 'end of file'}'."
        )

        self.recovery_events.append({
            "line": token.line,
            "column": token.col,
            "expected": error.expected,
            "skipped": skipped,
            "start_index": start
        })

    def safe_statement(self):
        start = self.i

        try:
            self.statement()
        except ParseError as error:
            self.panic_recover(error)

        # Prevent infinite loops when a closing brace
        # remains at the same position.
        if self.i == start and self.peek().kind != "EOF":
            self.take()


def analyze_baseline(source):
    tokens = tokenize(source)
    parser = PanicModeParser(tokens)
    parser.parse()

    return {
        "tokens": tokens,
        "diagnostics": parser.diagnostics,
        "repairs": parser.repairs,
        "skipped_tokens": parser.skipped_tokens,
        "recovery_events": parser.recovery_events
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python baseline.py example.c")
        sys.exit(2)

    try:
        with open(
            sys.argv[1], "r", encoding="utf-8"
        ) as file:
            source = file.read()

        result = analyze_baseline(source)

        print("\nPANIC-MODE BASELINE\n")

        if not result["diagnostics"]:
            print("No syntax errors detected.")

        for error in result["diagnostics"]:
            print(
                f"{error['line']}:{error['column']}: "
                f"{error['message']}"
            )

        print(
            f"\nDiagnostics: "
            f"{len(result['diagnostics'])}"
        )
        print(
            f"Skipped tokens: "
            f"{result['skipped_tokens']}"
        )
        print(
            f"Recovery events: "
            f"{len(result['recovery_events'])}"
        )

    except (OSError, Exception) as error:
        print(f"Error: {error}")
        sys.exit(1)
