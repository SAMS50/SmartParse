"""Experimental grammar-verified bounded repair planner.

Not wired into Parser: a valid parse is not proof of programmer intent.
Search uses the actual strict grammar and an explicit expansion budget.
"""
from dataclasses import dataclass
from heapq import heappush, heappop
from itertools import count
from smartparse import StrictParser, ParseError, Token, tokenize

REPLACEABLE = frozenset('(){}[];,')
INSERTABLE = frozenset('(){}[];,')

@dataclass(frozen=True)
class VerifiedPlan:
    edits: tuple
    corrected: tuple
    explored: int
    status: str


def _strict_error(tokens):
    parser = StrictParser(list(tokens))
    try:
        while parser.peek().kind != 'EOF':
            before = parser.i
            parser.statement()
            if parser.i <= before:
                return parser.i, 'progress'
        return None
    except ParseError as error:
        return parser.i, error.expected


def plan(source, *, max_edits=3, max_nodes=150):
    """Return minimal-edit grammar-valid repair, or None under budget.

    Handles punctuation insertion, deletion and replacement. Each expanded
    state starts from the next actual strict-parser error. This is a whole-
    program experiment, not an automatic change to the user's source.
    """
    if max_edits < 1 or max_nodes < 1:
        raise ValueError('budgets must be positive')
    original = tuple(tokenize(source))
    seq = count()
    heap = [(0, next(seq), original, ())]
    seen = {tuple((t.kind,t.value) for t in original)}
    explored = 0
    while heap and explored < max_nodes:
        cost, _, tokens, edits = heappop(heap)
        explored += 1
        error = _strict_error(tokens)
        if error is None:
            return VerifiedPlan(edits, tokens, explored, 'grammar_valid')
        if cost >= max_edits:
            continue
        index, expected = error
        token = tokens[index]
        candidates = []
        if expected in INSERTABLE:
            inserted = Token(expected, expected, token.line, token.col)
            candidates.append(('insert', expected, tokens[:index]+(inserted,)+tokens[index:]))
        if token.kind != 'EOF':
            if token.value in REPLACEABLE:
                candidates.append(('delete', token.value, tokens[:index]+tokens[index+1:]))
            if token.value in REPLACEABLE and expected in INSERTABLE and token.value != expected:
                replacement = Token(expected, expected, token.line, token.col)
                candidates.append(('substitute', f'{token.value}->{expected}', tokens[:index]+(replacement,)+tokens[index+1:]))
        for operation, detail, trial in candidates:
            key = tuple((t.kind,t.value) for t in trial)
            if key not in seen:
                seen.add(key)
                heappush(heap, (cost+1,next(seq),trial,edits+((operation,index,detail),)))
    return None
