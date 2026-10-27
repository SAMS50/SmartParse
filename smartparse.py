
from dataclasses import dataclass
import re
import sys

from recovery import context, rank_candidates
from cgar import search as cgar_search


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
            f"Expected {expected} at {token.line}:{token.col}"
        )


class Parser:
    def __init__(self, tokens, validate_repairs=True, scoring_mode="contextual", validation_policy="all", validation_margin=10, multi_token_recovery=False, adaptive_recovery=False, recovery_max_edits=3, recovery_max_nodes=64, verified_cgar=False, verified_max_edits=3, verified_max_nodes=150):
        self.tokens = tokens
        self.verified_cgar = verified_cgar
        if verified_max_edits < 1 or verified_max_nodes < 1:
            raise ValueError("verified CGAR budgets must be positive")
        self.verified_max_edits = verified_max_edits
        self.verified_max_nodes = verified_max_nodes
        self.verified_cgar_status = "not_attempted"
        self.verified_cgar_advice = None
        self.i = 0
        self.diagnostics = []
        self.repairs = []
        self.max_errors = 50
        self.validate_repairs = validate_repairs
        self.scoring_mode = scoring_mode
        if validation_policy not in ("all", "selective"):
            raise ValueError("validation_policy must be all or selective")
        if validation_margin < 0:
            raise ValueError("validation_margin must be nonnegative")
        self.validation_policy = validation_policy
        self.validation_margin = validation_margin
        self.validation_stats = {"eligible": 0, "probed": 0, "skipped_confident": 0}
        self.statement_starts = []
        if recovery_max_edits < 1 or recovery_max_nodes < 1:
            raise ValueError("recovery budgets must be positive")
        self.adaptive_recovery = adaptive_recovery
        self.recovery_max_edits = recovery_max_edits
        self.recovery_max_nodes = recovery_max_nodes
        self.adaptive_stats = {"attempted": 0, "accepted": 0}
        self.multi_token_recovery = multi_token_recovery
        self.multi_token_stats = {"attempted": 0, "accepted": 0}

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

    def _try_bounded_pair(self, expected):
        """Recognize a two-edit punctuation pattern at an expected closer.

        Delete a redundant punctuation token followed by a mismatched closer.
        This deliberately bounded, evidence-based rule never scans further than
        the next token and never modifies the original source token objects.
        """
        if expected not in (")", "}", "]"):
            return None
        first = self.peek()
        second = self.peek(1)
        if first.value not in (";", ",") or second.value not in (")", "}", "]"):
            return None
        if second.value == expected:
            return None  # Already handled by the single-token deletion rule.
        self.multi_token_stats["attempted"] += 1
        # A mismatched closer immediately after stray punctuation provides
        # evidence for exactly two edits: delete then substitute.
        self.take()
        self.take()
        self.multi_token_stats["accepted"] += 1
        edits = (
            ("delete", first, first.value, "remove stray punctuation before mismatched closer"),
            ("substitute", second, second.value, "replace mismatched closing delimiter"),
        )
        for operation, original, actual, reason in edits:
            message = (f"Unexpected '{actual}' before '{expected}'." if operation == "delete"
                       else f"Expected '{expected}' instead of '{actual}'.")
            self.report(original, message)
            self.repairs.append({
                "operation": operation, "token": expected, "from": actual,
                "line": original.line, "column": original.col,
                "score": None, "score_factors": {"bounded_two_edit_pattern": 1},
                "scoring_mode": self.scoring_mode, "reason": reason,
                "context": context(self.tokens, self.i - 2, expected),
                "grammar_validation": None,
                "multi_token": True,
            })
        return Token(expected, expected, second.line, second.col)

    def _try_adaptive(self, expected):
        self.adaptive_stats["attempted"] += 1
        plan = cgar_search(self.tokens, self.i, expected,
                           max_edits=self.recovery_max_edits,
                           max_nodes=self.recovery_max_nodes)
        if plan is None:
            return None
        start = self.i
        for operation, original, replacement in plan.edits:
            self.report(original, (f"Unexpected '{original.value}' before '{expected}'."
                         if operation == "delete" else
                         f"Expected '{replacement}' instead of '{original.value}' ."))
            self.repairs.append({
                "operation": operation,
                "token": replacement if replacement is not None else expected,
                "from": original.value, "line": original.line,
                "column": original.col, "score": None,
                "score_factors": {"cgar_budgeted_search": 1},
                "scoring_mode": self.scoring_mode,
                "reason": plan.evidence,
                "context": context(self.tokens, start, expected),
                "grammar_validation": None, "multi_token": True,
                "adaptive_recovery": True,
            })
        for _ in range(plan.consumed):
            self.take()
        self.adaptive_stats["accepted"] += 1
        last = self.tokens[start + plan.consumed - 1]
        return Token(expected, expected, last.line, last.col)

    def expect(self, value):
        if self.at(value):
            return self.take()

        if self.adaptive_recovery:
            repaired = self._try_adaptive(value)
            if repaired is not None:
                return repaired

        if self.multi_token_recovery:
            paired = self._try_bounded_pair(value)
            if paired is not None:
                return paired

        token = self.peek()
        index = self.i
        candidates = rank_candidates(
            self.tokens, index, value, mode=self.scoring_mode
        )

        if not candidates:
            raise ParseError(token, value)

        chosen = candidates[0]
        validation = None

        if (
            self.validate_repairs
            and len(candidates) > 1
            and self.statement_starts
        ):
            self.validation_stats["eligible"] += 1
            margin = candidates[0].score - candidates[1].score
            should_probe = (
                self.validation_policy == "all"
                or margin <= self.validation_margin
            )
            if should_probe:
                from local_validation import choose_candidate

                chosen, validation = choose_candidate(
                    self.tokens,
                    self.statement_starts[-1],
                    index,
                    candidates
                )
                self.validation_stats["probed"] += 1
            else:
                self.validation_stats["skipped_confident"] += 1

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
            "score_factors": dict(chosen.factors),
            "scoring_mode": self.scoring_mode,
            "reason": chosen.reason,
            "context": context(
                self.tokens, index, value
            ),
            "grammar_validation": validation
        })

        return Token(
            value, value, token.line, token.col
        )

    def identifier(self):
        if self.peek().kind != "ID":
            raise ParseError(
                self.peek(), "identifier"
            )
        return self.take()

    def _try_verified_cgar(self):
        """Opt-in whole-program advisor; never changes the caller's tokens.

        Only a strictly valid proposed correction is used to report repairs.
        Abstentions fall through to the existing recovery pipeline.
        """
        from cgar_reliable import advise
        from cgar_verified import _strict_error
        from difflib import SequenceMatcher

        # Token values separated by whitespace preserve lexical token boundaries.
        # The planner works on token indices, while diagnostics use original locations.
        source = " ".join(t.value for t in self.tokens if t.kind != "EOF")
        try:
            advice = advise(source, max_edits=self.verified_max_edits,
                            max_nodes=self.verified_max_nodes)
        except (ValueError, LexError):
            self.verified_cgar_status = "abstain"
            return False
        self.verified_cgar_advice = advice
        self.verified_cgar_status = advice.status
        if advice.status != "verified_candidate" or advice.result is None:
            return False
        corrected = advice.result.corrected
        if _strict_error(corrected) is not None:
            self.verified_cgar_status = "abstain"
            return False

        original = [t for t in self.tokens if t.kind != "EOF"]
        proposed = [t for t in corrected if t.kind != "EOF"]
        matcher = SequenceMatcher(a=[t.value for t in original],
                                  b=[t.value for t in proposed], autojunk=False)
        changes = []
        for tag, a0, a1, b0, b1 in matcher.get_opcodes():
            if tag == "equal":
                continue
            anchor = self.tokens[min(a0, len(self.tokens) - 1)]
            before = " ".join(t.value for t in original[a0:a1])
            after = " ".join(t.value for t in proposed[b0:b1])
            operation = {"insert": "insert", "delete": "delete", "replace": "substitute"}[tag]
            changes.append((anchor, operation, before, after))
        if not changes:
            self.verified_cgar_status = "unchanged"
            return False
        for token, operation, before, after in changes:
            message = (f"CGAR suggested {operation}: "
                       f"{before!r} -> {after!r}; grammar-verified, intent unconfirmed.")
            self.report(token, message)
            self.repairs.append({
                "operation": operation, "token": after or None,
                "from": before or None, "line": token.line, "column": token.col,
                "score": None, "score_factors": {"strict_grammar_verified": 1},
                "scoring_mode": self.scoring_mode,
                "reason": "Whole-program grammar-verified candidate; author intent not proven",
                "context": None, "grammar_validation": "whole_program_pass",
                "verified_cgar": True,
            })
        self.i = len(self.tokens) - 1
        return True

    def parse(self):
        if self.verified_cgar and self.i == 0:
            if self._try_verified_cgar():
                return self.diagnostics
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

        while (
            self.peek().kind != "EOF"
            and self.peek().value not in (";", "}")
        ):
            self.take()

        if self.at(";"):
            self.take()

    def statement(self):
        self.statement_starts.append(self.i)

        try:
            return self._statement()
        finally:
            self.statement_starts.pop()

    def _statement(self):
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
        self.take()
        self.identifier()

        if self.accept("("):
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

        if self.peek().value in ("int", "float"):
            self.declaration(
                require_semicolon=False
            )
        elif not self.at(";"):
            self.expression()

        self.expect(";")

        if not self.at(";"):
            self.expression()

        self.expect(";")

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
            next_prec = (
                prec if operator == "=" else prec + 1
            )
            self.expression(next_prec)

    def unary(self):
        if self.peek().value in ("!", "-", "+"):
            self.take()
            self.unary()
            return

        self.primary()

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


class StrictParser(Parser):
    def __init__(self, tokens):
        super().__init__(
            tokens, validate_repairs=False
        )

    def expect(self, value):
        if self.at(value):
            return self.take()
        raise ParseError(self.peek(), value)

    def safe_statement(self):
        self.statement()


# Compatibility functions from Milestone 6.
# Existing tests and scripts can continue using them.

def apply_candidate(tokens, index, candidate):
    from local_validation import apply_candidate as apply
    return apply(tokens, index, candidate)


def probe_candidate(tokens, index, candidate):
    trial = apply_candidate(
        tokens, index, candidate
    )
    parser = StrictParser(trial)
    completed = False

    try:
        parser.parse()
        completed = True
    except ParseError:
        pass

    position = parser.i

    if candidate.operation == "insert" and position > index:
        position -= 1
    elif candidate.operation == "delete" and position >= index:
        position += 1

    return {
        "progress": max(0, position - index),
        "completed": completed
    }


def choose_validated_candidate(tokens, index, candidates):
    evaluations = []

    for candidate in candidates:
        result = probe_candidate(
            tokens, index, candidate
        )
        evaluations.append({
            "candidate": candidate,
            "progress": result["progress"],
            "completed": result["completed"]
        })

    evaluations.sort(
        key=lambda item: (
            item["completed"],
            item["progress"],
            item["candidate"].score
        ),
        reverse=True
    )

    best = evaluations[0]

    return best["candidate"], {
        "method": "strict_grammar_probe",
        "candidates_tested": len(evaluations),
        "progress": best["progress"],
        "completed": best["completed"],
        "alternatives": [
            {
                "operation": item["candidate"].operation,
                "progress": item["progress"],
                "completed": item["completed"],
                "heuristic_score": item["candidate"].score
            }
            for item in evaluations
        ]
    }


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

        tokens, diagnostics, repairs = analyze(
            source
        )

        if not diagnostics:
            print("No syntax errors detected.")
        else:
            for error in diagnostics:
                print(
                    f"{error['line']}:"
                    f"{error['column']}: "
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

                validation = repair[
                    "grammar_validation"
                ]

                if validation is not None:
                    print(
                        "    Local grammar probe: "
                        f"{validation['progress']} "
                        "tokens of progress, "
                        f"{validation['candidates_tested']} "
                        "candidates tested"
                    )

        return 0

    except (LexError, OSError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
