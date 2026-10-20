
"""
Local grammar validation for SmartParse.

Tries each repair on a temporary token stream and
strictly reparses the statement containing the error.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeResult:
    operation: str
    completed: bool
    progress: int
    heuristic_score: float
    reached_repair: bool


def apply_candidate(tokens, index, candidate):
    from smartparse import Token

    trial = list(tokens)
    original = trial[index]

    replacement = Token(
        candidate.expected,
        candidate.expected,
        original.line,
        original.col
    )

    if candidate.operation == "insert":
        trial.insert(index, replacement)

    elif candidate.operation == "substitute":
        trial[index] = replacement

    elif candidate.operation == "delete":
        del trial[index]

    else:
        raise ValueError(
            f"Unsupported repair: {candidate.operation}"
        )

    return trial


def probe_candidate(tokens, statement_start, index, candidate):
    from smartparse import StrictParser, ParseError

    trial = apply_candidate(tokens, index, candidate)
    parser = StrictParser(trial)
    parser.i = statement_start

    completed = False

    try:
        parser.statement()
        completed = True
    except ParseError:
        pass

    position = parser.i

    # Translate the trial position approximately
    # back to the original token coordinates.
    if candidate.operation == "insert" and position > index:
        position -= 1
    elif candidate.operation == "delete" and position >= index:
        position += 1

    return ProbeResult(
        operation=candidate.operation,
        completed=completed,
        progress=max(0, position - index),
        heuristic_score=candidate.score,
        reached_repair=position >= index
    )


def choose_candidate(tokens, statement_start, index, candidates):
    evaluations = []

    for candidate in candidates:
        result = probe_candidate(
            tokens,
            statement_start,
            index,
            candidate
        )
        evaluations.append((candidate, result))

    # Successful local parse first, then forward
    # progress, then original heuristic score.
    chosen, best = max(
        evaluations,
        key=lambda pair: (
            pair[1].completed,
            pair[1].progress,
            pair[1].heuristic_score
        )
    )

    metadata = {
        "method": "local_statement_probe",
        "statement_start": statement_start,
        "candidates_tested": len(evaluations),
        "completed": best.completed,
        "progress": best.progress,
        "reached_repair": best.reached_repair,
        "alternatives": [
            {
                "operation": candidate.operation,
                "completed": result.completed,
                "progress": result.progress,
                "heuristic_score": result.heuristic_score
            }
            for candidate, result in evaluations
        ]
    }

    return chosen, metadata
