from dataclasses import dataclass

BOUNDARIES = {
    '{', '}', ';', 'else', 'int',
    'float', 'void', 'if', 'while', 'for', 'return'
}

CLOSERS = {')', '}', ']'}


@dataclass(frozen=True)
class Candidate:
    operation: str
    expected: str
    actual: str
    score: float
    reason: str
    factors: tuple = ()


# MODULE 1: CONTEXT ANALYZER

def context(tokens, index, expected):
    stack = []
    matching = {')': '(', '}': '{', ']': '['}

    for token in tokens[:index]:
        if token.value in ('(', '{', '['):
            stack.append(token.value)

        elif (token.value in matching
              and stack
              and stack[-1] == matching[token.value]):
            stack.pop()

    return {
        'expected': expected,
        'previous': tokens[index - 1].value if index else None,
        'current': tokens[index].value,
        'next': (
            tokens[index + 1].value
            if index + 1 < len(tokens)
            else None
        ),
        'nesting': tuple(stack)
    }


# MODULE 2 + 3: CANDIDATE GENERATOR AND RANKER

def rank_candidates(tokens, index, expected, mode="contextual"):
    if mode not in ("contextual", "legacy"):
        raise ValueError("mode must be contextual or legacy")
    ctx = context(tokens, index, expected)

    actual = ctx['current']
    following = ctx['next']
    at_eof = tokens[index].kind == 'EOF'

    candidates = []

    # Candidate 1: INSERTION
    boundary = actual in BOUNDARIES or at_eof

    insertion_valid = (
        expected in (')', ';', '}')
        and boundary
    )

    if expected == '}' and actual == ';':
        insertion_valid = False

    if insertion_valid:
        fit = 1

        if (expected == ')'
                and actual == '{'
                and '(' in ctx['nesting']):
            fit = 3

        candidates.append(
            Candidate(
                'insert', expected, actual,
                10 + fit - 1,
                'expected delimiter at boundary'
            )
        )

    # Candidate 2: SUBSTITUTION
    if (expected in CLOSERS
            and actual in CLOSERS
            and actual != expected):

        candidates.append(
            Candidate(
                'substitute', expected, actual,
                11,
                'mismatched closing delimiter'
            )
        )

    # Candidate 3: DELETION
    if (actual in (';', ',', ')', ']', '}')
            and following == expected):

        candidates.append(
            Candidate(
                'delete', expected, actual,
                12,
                'redundant punctuation before expected token'
            )
        )

    if mode == "contextual":
        candidates = [contextual_score(c, ctx, tokens, index) for c in candidates]

    # Higher score = better candidate
    return sorted(
        candidates,
        key=lambda c: (-c.score, c.operation)
    )

def generate_candidates(tokens, index, expected):
    return rank_candidates(tokens, index, expected)

def contextual_score(candidate, ctx, tokens, index):
    """Explainable ranking from local evidence; no universal operation preference.

    Weights are initial design hypotheses, not learned probabilities.
    Candidate eligibility is unchanged from Review 2.
    """
    operation = candidate.operation
    expected = candidate.expected
    actual = ctx["current"]
    following = ctx["next"]
    nesting = ctx["nesting"]
    matching = {")": "(", "}": "{", "]": "["}
    factors = []

    # Each candidate is a one-token edit, so none gets an automatic advantage.
    factors.append(("single_token_edit", 10))

    if operation == "insert":
        factors.append(("statement_or_block_boundary", 25))
        if expected == ";" and actual in BOUNDARIES:
            factors.append(("statement_boundary_fit", 25))
        if expected in matching and matching[expected] in nesting:
            factors.append(("unclosed_matching_opener", 30))
        if actual == "{" and expected == ")":
            factors.append(("block_starts_after_condition", 15))
        if tokens[index].kind == "EOF":
            factors.append(("missing_at_eof", 20))

    elif operation == "substitute":
        factors.append(("wrong_closing_delimiter", 25))
        if expected in matching and matching[expected] in nesting:
            factors.append(("matching_opener_in_context", 30))
        if actual in matching and matching[actual] not in nesting:
            factors.append(("unexpected_closer", 15))

    elif operation == "delete":
        # Strong direct evidence: after removing current token, the parser's
        # expected token is exactly the next token.
        if following == expected:
            factors.append(("next_token_is_expected", 55))
        if actual in (";", ",", ")", "]", "}"):
            factors.append(("extra_punctuation", 15))

    score = sum(value for _, value in factors)
    return Candidate(operation, expected, actual, score,
                     candidate.reason, tuple(factors))
