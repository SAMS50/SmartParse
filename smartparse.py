
from dataclasses import dataclass
import re
import sys

from recovery import context, rank_candidates


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    col: int


PATTERN = re.compile(
    r"(?P<SPACE>[ \t\r]+)"
    r"|(?P<NEWLINE>\n)"
    r"|(?P<COMMENT>//[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<NUMBER>\d+(?:\.\d+)?)"
    r"|(?P<ID>[A-Za-z_]\w*)"
    r"|(?P<OP>==|!=|<=|>=|&&|\|\||\+\+|--|[+*/%<>=!\-])"
    r"|(?P<PUNCT>[(){};,\[\]])"
    r"|(?P<MISMATCH>.)"
)

KEYWORDS = {
    "int", "float", "void", "if", "else",
    "while", "for", "return"
}


class LexError(Exception):
    pass


def tokenize(source):
    tokens = []
    line, col = 1, 1

    for match in PATTERN.finditer(source):
        kind = match.lastgroup
        value = match.group()

        if kind == "MISMATCH":
            raise LexError(
                f"Unexpected character {value!r} "
                f"at {line}:{col}"
            )

        if kind not in {"SPACE", "NEWLINE", "COMMENT"}:
            token_kind = (
                value if kind in {"OP", "PUNCT"}
                else "KEYWORD" if value in KEYWORDS
                else kind
            )
            tokens.append(
                Token(token_kind, value, line, col)
            )

        if "\n" in value:
            line += value.count("\n")
            col = len(value.rsplit("\n", 1)[-1]) + 1
        else:
            col += len(value)

    tokens.append(Token("EOF", "", line, col))
    return tokens


class ParseError(Exception):
    def __init__(self, token, expected):
        self.token = token
        self.expected = expected
        super().__init__(
            f"Expected {expected} at "
            f"{token.line}:{token.col}"
        )


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.diagnostics = []
        self.repairs = []
        self.max_errors = 50

    def peek(self, offset=0):
        return self.tokens[
            min(self.i + offset, len(self.tokens) - 1)
        ]

    def at(self, value):
        return self.peek().value == value

    def take(self):
        token = self.peek()
        if token.kind != "EOF":
            self.i += 1
        return token

    def accept(self, value):
        if self.at(value):
            return self.take()
        return None

    def report(self, token, message):
        if len(self.diagnostics) < self.max_errors:
            self.diagnostics.append({
                "line": token.line,
                "column": token.col,
                "message": message
            })

    def expect(self, value):
        if self.at(value):
            return self.take()

        token = self.peek()
        index = self.i

        candidates = rank_candidates(
            self.tokens, index, value
        )

        if not candidates:
            raise ParseError(token, value)

        chosen = candidates[0]

        if chosen.operation == "insert":
            message = (
                f"Missing '{value}' before "
                f"'{token.value or 'end of file'}'."
            )

        elif chosen.operation == "substitute":
            message = (
                f"Expected '{value}' instead "
                f"of '{token.value}'."
            )
            self.take()

        elif chosen.operation == "delete":
            message = (
                f"Unexpected '{token.value}' "
                f"before '{value}'."
            )
            self.take()
            self.take()

        else:
            raise ParseError(token, value)

        self.report(token, message)

        self.repairs.append({
            "operation": chosen.operation,
            "token": value,
            "from": (
                token.value
                if chosen.operation != "insert"
                else None
            ),
            "line": token.line,
            "column": token.col,
            "score": chosen.score,
            "reason": chosen.reason,
            "context": context(
                self.tokens, index, value
            )
        })

        return Token(value, value, token.line, token.col)

    def identifier(self):
        if self.peek().kind != "ID":
            raise ParseError(
                self.peek(), "identifier"
            )
        return self.take()

    def parse(self):
        while self.peek().kind != "EOF":
            if len(self.diagnostics) >= self.max_errors:
                break
            self.safe_statement()
        return self.diagnostics

    def safe_statement(self):
        start = self.i

        try:
            self.statement()
        except ParseError as error:
            self.panic_recover(error)

        if self.i == start and self.peek().kind != "EOF":
            self.take()

    def panic_recover(self, error):
        token = error.token

        self.report(
            token,
            f"Expected {error.expected} before "
            f"'{token.value or 'end of file'}'."
        )

        # Synchronize at a statement boundary.
        while (
            self.peek().kind != "EOF"
            and self.peek().value not in (";", "}")
        ):
            self.take()

        if self.at(";"):
            self.take()

    def statement(self):
        value = self.peek().value

        if value in ("int", "float", "void"):
            self.declaration()

        elif value == "{":
            self.block()

        elif value == "if":
            self.if_statement()

        elif value == "while":
            self.while_statement()

        elif value == "for":
            self.for_statement()

        elif value == "return":
            self.take()
            if not self.at(";"):
                self.expression()
            self.expect(";")

        elif value == ";":
            self.take()

        else:
            self.expression()
            self.expect(";")

    def declaration(self, require_semicolon=True):
        self.take()  # type
        self.identifier()

        if self.accept("("):
            # Function declaration/definition.
            if not self.at(")"):
                self.parameter()
                while self.accept(","):
                    self.parameter()

            self.expect(")")

            if self.at("{"):
                self.block()
            elif require_semicolon:
                self.expect(";")
            return

        if self.accept("="):
            self.expression()

        while self.accept(","):
            self.identifier()
            if self.accept("="):
                self.expression()

        if require_semicolon:
            self.expect(";")

    def parameter(self):
        if self.peek().value not in (
            "int", "float", "void"
        ):
            raise ParseError(self.peek(), "type")

        self.take()
        self.identifier()

    def block(self):
        self.expect("{")

        while (
            not self.at("}")
            and self.peek().kind != "EOF"
            and len(self.diagnostics) < self.max_errors
        ):
            self.safe_statement()

        self.expect("}")

    def if_statement(self):
        self.take()
        self.expect("(")
        self.expression()
        self.expect(")")
        self.statement()

        if self.accept("else"):
            self.statement()

    def while_statement(self):
        self.take()
        self.expect("(")
        self.expression()
        self.expect(")")
        self.statement()

    def for_statement(self):
        self.take()
        self.expect("(")

        # Initialization
        if self.peek().value in ("int", "float"):
            self.declaration(require_semicolon=False)
        elif not self.at(";"):
            self.expression()

        self.expect(";")

        # Condition
        if not self.at(";"):
            self.expression()

        self.expect(";")

        # Update
        if not self.at(")"):
            self.expression()

        self.expect(")")
        self.statement()

    def expression(self, min_prec=0):
        self.unary()

        precedence = {
            "=": 1,
            "||": 2,
            "&&": 3,
            "==": 4,
            "!=": 4,
            "<": 5,
            ">": 5,
            "<=": 5,
            ">=": 5,
            "+": 6,
            "-": 6,
            "*": 7,
            "/": 7,
            "%": 7
        }

        while (
            self.peek().value in precedence
            and precedence[self.peek().value] >= min_prec
        ):
            operator = self.take().value
            prec = precedence[operator]
            next_prec = prec if operator == "=" else prec + 1
            self.expression(next_prec)

    def unary(self):
        if self.peek().value in ("!", "-", "+"):
            self.take()
            self.unary()
            return

        self.primary()

        # Function calls and postfix operations.
        while True:
            if self.accept("("):
                if not self.at(")"):
                    self.expression()
                    while self.accept(","):
                        self.expression()
                self.expect(")")

            elif self.peek().value in ("++", "--"):
                self.take()

            else:
                break

    def primary(self):
        if self.accept("("):
            self.expression()
            self.expect(")")

        elif self.peek().kind in ("ID", "NUMBER"):
            self.take()

        else:
            raise ParseError(
                self.peek(), "expression"
            )


def analyze(source):
    tokens = tokenize(source)
    parser = Parser(tokens)
    parser.parse()

    return tokens, parser.diagnostics, parser.repairs


def main():
    if len(sys.argv) < 2:
        print("Usage: python smartparse.py example.c")
        return 2

    try:
        with open(
            sys.argv[1], "r", encoding="utf-8"
        ) as file:
            source = file.read()

        tokens, diagnostics, repairs = analyze(source)

        if not diagnostics:
            print("No syntax errors detected.")
        else:
            for error in diagnostics:
                print(
                    f"{error['line']}:{error['column']}: "
                    f"{error['message']}"
                )

        print(
            f"\nTokens: {len(tokens) - 1}; "
            f"Diagnostics: {len(diagnostics)}"
        )

        if repairs:
            print("\nRecovery operations:")
            for repair in repairs:
                print(
                    f"  {repair['operation']}: "
                    f"{repair['token']} "
                    f"(score: {repair['score']})"
                )

        return 0

    except (LexError, OSError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
