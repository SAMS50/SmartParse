"""Conservative, explainable repair recommendations for SmartParse.

This is a decision-support layer, NOT a calibrated probability estimator.
It never applies edits or changes the parser's recovery behaviour.
"""
from dataclasses import dataclass
from recovery import rank_candidates


@dataclass(frozen=True)
class Advice:
    status: str
    explanation: str
    alternatives: tuple
    score_gap: float | None


def advise(tokens, index, expected, *, margin=15):
    """Return a cautious recommendation at one parser expectation.

    The margin is a heuristic score separation, not a probability. Bounded
    two-token cases are explicitly marked for review rather than called safe.
    """
    if margin < 0:
        raise ValueError('margin must be nonnegative')
    if not 0 <= index < len(tokens):
        raise IndexError('token index out of range')
    actual = tokens[index].value
    following = tokens[index + 1].value if index + 1 < len(tokens) else None
    if expected in (')', '}', ']') and actual in (';', ',') and following in (')', '}', ']') and following != expected:
        return Advice('review', 'Two-token correction is pattern-based; inspect the intended delimiter and punctuation.',
                      (f"delete '{actual}', replace '{following}' with '{expected}'",), None)
    choices = rank_candidates(tokens, index, expected, mode='contextual')
    if not choices:
        return Advice('abstain', 'No supported local correction; request manual inspection.', (), None)
    labels = tuple(f"{c.operation} '{c.expected}' (score={c.score:g}; {c.reason})" for c in choices)
    if len(choices) == 1:
        return Advice('review', 'Only one eligible local repair; there is no competing candidate to confirm it.', labels, None)
    gap = choices[0].score - choices[1].score
    if gap <= margin:
        return Advice('ambiguous', 'Top repairs have similar heuristic scores; present alternatives.', labels, gap)
    return Advice('preferred', 'Top candidate has a larger heuristic score margin; grammar correctness is not guaranteed.', labels, gap)
