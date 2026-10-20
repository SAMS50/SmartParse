
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
    line = 1
    col = 1

    for match in PATTERN.finditer(source):
        kind = match.lastgroup
        value = match.group()

        if kind == "MISMATCH":
            raise LexError(
                f"Unexpected character {value!r} at {line}:{col}"
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

        lines = value.count("\n")

        if lines:
            line += lines
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

    def peek(self):
        return self.tokens[self.i]

    def at(self, value):
        return self.peek().value == value

    def take(self):
        tok = self.peek()

        if tok.kind != "EOF":
            self.i += 1

        return tok

    def accept(self, value):
        if self.at(value):
            return self.take()
        return None

    def expect(self, value):
        if self.at(value):
            return self.take()

        tok = self.peek()
        error_index = self.i

        candidates = rank_candidates(
            self.tokens, self.i, value
        )

        if not candidates:
            raise ParseError(tok, value)

        chosen = candidates[0]

        if chosen.operation == "insert":
            message = (
                f"Missing '{value}' before "
                f"'{tok.value or 'end of file'}'."
            )

        elif chosen.operation == "substitute":
            message = (
                f"Expected '{value}' instead "
                f"of '{tok.value}'."
            )
            self.take()

        elif chosen.operation == "delete":
            message = (
                f"Unexpected '{tok.value}' "
                f"before '{value}'."
            )
            self.take()
            self.take()

        self.diagnostics.append({
            "line": tok.line,
            "column": tok.col,
            "message": message
        })

        self.repairs.append({
            "operation": chosen.operation,
            "token": value,
            "from": (
                tok.value
                if chosen.operation != "insert"
                else None
            ),
            "line": tok.line,
            "column": tok.col,
            "score": chosen.score,
            "reason": chosen.reason,
            "context": context(
                self.tokens, error_index, value
            )
        })

        # Virtual token: source code is unchanged.
        return Token(value, value, tok.line, tok.col)

    def parse(self):
        while self.peek().kind != "EOF":
            start = self.i

            try:
                self.statement()
            except ParseError as error:
                self.recover(error)

            if self.i == start:
                self.take()

        return self.diagnostics

    def statement(self):
        if self.peek().value in ("int", "float", "void"):
            self.take()
            self.expect_identifier()

            if self.accept("("):
                if not self.at(")"):
                    self.parameter()

                    while self.accept(","):
                        self.parameter()

                self.expect(")")
                self.block()

            else:
                if self.accept("="):
                    self.expression()

                self.expect(";")

        elif self.at("{"):
            self.block()

        elif self.peek().value in ("if", "while"):
            self.take()
            self.expect("(")
            self.expression()
            self.expect(")")
            self.statement()

            if self.at("else"):
                self.take()
                self.statement()

        elif self.at("return"):
            self.take()

            if not self.at(";"):
                self.expression()

            self.expect(";")

        elif self.at(";"):
            self.take()

        else:
            self.expression()
            self.expect(";")

    def parameter(self):
        if self.peek().value not in (
            "int", "float", "void"
        ):
            raise ParseError(self.peek(), "type")

        self.take()
        self.expect_identifier()

    def expect_identifier(self):
        if self.peek().kind != "ID":
            raise ParseError(
                self.peek(), "identifier"
            )

        return self.take()

    def block(self):
        self.expect("{")

        while (
            not self.at("}")
            and self.peek().kind != "EOF"
        ):
            start = self.i

            try:
                self.statement()
            except ParseError as error:
                self.recover(error)

            if self.i == start:
                self.take()

        self.expect("}")

    def expression(self, min_prec=0):
        if self.peek().value in ("!", "-", "+"):
            self.take()
            self.expression(8)

        elif self.accept("("):
            self.expression()
            self.expect(")")

        elif self.peek().kind in ("ID", "NUMBER"):
            self.take()

        else:
            raise ParseError(
                self.peek(), "expression"
            )

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

            next_prec = (
                prec if operator == "="
                else prec + 1
            )

            self.expression(next_prec)

    def recover(self, error):
        tok = error.token
        expected = error.expected

        # Fallback recovery for unsupported repairs.
        message = (
            f"Expected {expected} before "
            f"'{tok.value or 'end of file'}'."
        )

        while (
            self.peek().kind != "EOF"
            and self.peek().value not in (";", "}")
        ):
            self.take()

        if self.at(";"):
            self.take()

        self.diagnostics.append({
            "line": tok.line,
            "column": tok.col,
            "message": message
        })


def analyze(source):
    tokens = tokenize(source)
    parser = Parser(tokens)
    parser.parse()

    return (
        tokens,
        parser.diagnostics,
        parser.repairs
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python smartparse.py example.c"
        )
        sys.exit(2)

    try:
        with open(
            sys.argv[1], encoding="utf-8"
        ) as file:
            source = file.read()

        tokens, diagnostics, repairs = analyze(
            source
        )

        if diagnostics:
            for diagnostic in diagnostics:
                print(
                    f"{diagnostic['line']}:"
                    f"{diagnostic['column']}: "
                    f"{diagnostic['message']}"
                )
        else:
            print("No syntax errors detected.")

        print(
            f"Tokens: {len(tokens) - 1}; "
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

    except LexError as error:
        print(f"Lexical error: {error}")
        sys.exit(1)
