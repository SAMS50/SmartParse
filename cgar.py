"""Conservative grammar-guided adaptive local repair search.

Searches edit sequences of up to max_edits, with a finite node budget. Only
punctuation and delimiter tokens are eligible for removal/replacement.
A candidate must restore the parser's *currently expected literal*; this is
not a proof that the entire corrected program is valid.
"""
from dataclasses import dataclass

CLOSERS = frozenset({")", "}", "]"})
PUNCT = frozenset({";", ",", ")", "}", "]", "(" , "[", "{"})

@dataclass(frozen=True)
class Plan:
    edits: tuple  # (operation, original token, expected value)
    consumed: int
    cost: int
    evidence: str


def search(tokens, index, expected, *, max_edits=3, max_nodes=64):
    """Return best strongly supported plan or None; never mutate tokens."""
    if max_edits < 1 or max_nodes < 1:
        raise ValueError("search budgets must be positive")
    if expected not in CLOSERS | {";", "(" , "{"}:
        return None
    if index >= len(tokens) or tokens[index].value == expected:
        return None
    # Explore deletions before a matching expected token, or a wrong closer.
    # Do not delete identifiers, operators, or numbers: no intent evidence.
    plans = []
    visited = 0
    for n_delete in range(min(max_edits, len(tokens) - index)):
        visited += 1
        if visited > max_nodes:
            break
        prefix = tokens[index:index+n_delete]
        if any(t.value not in PUNCT or t.kind == "EOF" for t in prefix):
            break
        target_i = index + n_delete
        if target_i >= len(tokens):
            break
        target = tokens[target_i]
        if target.value == expected:
            if n_delete:
                edits = tuple(("delete", t, None) for t in prefix)
                plans.append(Plan(edits, n_delete + 1, n_delete, "expected token follows removable punctuation"))
        elif (target.value in CLOSERS and expected in CLOSERS
              and n_delete + 1 <= max_edits):
            edits = tuple(("delete", t, None) for t in prefix) + (("substitute", target, expected),)
            plans.append(Plan(edits, n_delete + 1, n_delete + 1, "mismatched closer after removable punctuation"))
    # Only apply multi-edit plans. Single-edit recovery remains the existing
    # contextual/validated system; no blind search or source mutation.
    plans = [p for p in plans if p.cost >= 2]
    if not plans:
        return None
    return min(plans, key=lambda p: (p.cost, p.consumed))
