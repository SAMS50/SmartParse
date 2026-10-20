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

def rank_candidates(tokens, index, expected):
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

    # Higher score = better candidate
    return sorted(
        candidates,
        key=lambda c: (-c.score, c.operation)
    )

def generate_candidates(tokens, index, expected):
    return rank_candidates(tokens, index, expected)