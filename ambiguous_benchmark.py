
"""
Milestone 8A: Ambiguous Repair Benchmark

Compare heuristic-only and grammar-validated SmartParse
on cases with competing repair candidates.

This benchmark measures repair selection, not merely
diagnostic detection.
"""

import csv
from pathlib import Path

from smartparse import (
    Parser,
    StrictParser,
    ParseError,
    tokenize
)
from recovery import rank_candidates
from local_validation import apply_candidate


CASES = [
    {
        "id": "A01",
        "name": "Extra semicolon in if condition",
        "source": "if (x > 5 ; ) x = 1;",
        "actual": ";",
        "expected": ")",
        "correct_operation": "delete"
    },
    {
        "id": "A02",
        "name": "Wrong closer in if condition",
        "source": "if (x > 5 } { x = 1; }",
        "actual": "}",
        "expected": ")",
        "correct_operation": "substitute"
    },
    {
        "id": "A03",
        "name": "Extra semicolon in while condition",
        "source": "while (x < 3 ; ) x++;",
        "actual": ";",
        "expected": ")",
        "correct_operation": "delete"
    },
    {
        "id": "A04",
        "name": "Wrong closer in while condition",
        "source": "while (x < 3 } { x++; }",
        "actual": "}",
        "expected": ")",
        "correct_operation": "substitute"
    },
    {
        "id": "A05",
        "name": "Extra semicolon before if block",
        "source": "if (x > 0 ; ) { x++; }",
        "actual": ";",
        "expected": ")",
        "correct_operation": "delete"
    },
    {
        "id": "A06",
        "name": "Wrong closer before if block",
        "source": "if (x > 0 } { x++; }",
        "actual": "}",
        "expected": ")",
        "correct_operation": "substitute"
    }
]


def locate_error(tokens, case):
    """
    Find the intended ambiguous error location.
    Require at least two recovery candidates.
    """
    for index, token in enumerate(tokens):
        if token.value != case["actual"]:
            continue

        candidates = rank_candidates(
            tokens, index, case["expected"]
        )

        if len(candidates) >= 2:
            return index, candidates

    raise AssertionError(
        f"{case['id']}: no ambiguous repair found"
    )


def strict_parse_succeeds(tokens):
    parser = StrictParser(tokens)

    try:
        parser.parse()
        return True
    except ParseError:
        return False


def evaluate_case(case, validate_repairs):
    tokens = tokenize(case["source"])
    index, candidates = locate_error(tokens, case)

    parser = Parser(
        tokens,
        validate_repairs=validate_repairs
    )
    parser.parse()

    target = tokens[index]

    matching_repairs = [
        repair
        for repair in parser.repairs
        if repair["line"] == target.line
        and repair["column"] == target.col
        and repair["token"] == case["expected"]
    ]

    if not matching_repairs:
        chosen_operation = None
        completed = False
        probes = 0

    else:
        repair = matching_repairs[0]
        chosen_operation = repair["operation"]

        validation = repair.get(
            "grammar_validation"
        )

        probes = (
            1 if validation is not None else 0
        )

        selected_candidate = next(
            (
                candidate
                for candidate in candidates
                if candidate.operation == chosen_operation
            ),
            None
        )

        if selected_candidate is None:
            completed = False
        else:
            corrected = apply_candidate(
                tokens, index, selected_candidate
            )
            completed = strict_parse_succeeds(
                corrected
            )

    return {
        "id": case["id"],
        "name": case["name"],
        "mode": (
            "validated"
            if validate_repairs
            else "heuristic"
        ),
        "expected_operation": case["correct_operation"],
        "chosen_operation": chosen_operation or "none",
        "correct_repair": int(
            chosen_operation == case["correct_operation"]
        ),
        "strict_parse_completed": int(completed),
        "candidate_count": len(candidates),
        "grammar_probes": probes,
        "diagnostic_count": len(parser.diagnostics)
    }


def run_benchmark():
    Path("results").mkdir(exist_ok=True)

    rows = []
    decisions_changed = 0
    improved = 0
    worsened = 0

    print("=" * 72)
    print("SMARTPARSE: AMBIGUOUS REPAIR BENCHMARK")
    print("=" * 72)

    for case in CASES:
        heuristic = evaluate_case(
            case, validate_repairs=False
        )
        validated = evaluate_case(
            case, validate_repairs=True
        )

        rows.extend([heuristic, validated])

        changed = (
            heuristic["chosen_operation"]
            != validated["chosen_operation"]
        )

        if changed:
            decisions_changed += 1

        if (
            not heuristic["correct_repair"]
            and validated["correct_repair"]
        ):
            improved += 1

        if (
            heuristic["correct_repair"]
            and not validated["correct_repair"]
        ):
            worsened += 1

        print(
            f"\n{case['id']} | {case['name']}"
        )
        print(
            "  Expected:",
            case["correct_operation"]
        )

        for result in (heuristic, validated):
            status = (
                "CORRECT"
                if result["correct_repair"]
                else "INCORRECT"
            )

            print(
                f"  {result['mode']:<10}"
                f" selected={result['chosen_operation']:<12}"
                f" {status:<9}"
                f" strict_parse="
                f"{bool(result['strict_parse_completed'])}"
            )

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    for mode in ("heuristic", "validated"):
        subset = [
            row for row in rows
            if row["mode"] == mode
        ]

        correct = sum(
            row["correct_repair"]
            for row in subset
        )

        completed = sum(
            row["strict_parse_completed"]
            for row in subset
        )

        probes = sum(
            row["grammar_probes"]
            for row in subset
        )

        total = len(subset)

        print(f"\n{mode.upper()}")
        print(
            f"  Repair accuracy: "
            f"{correct}/{total} "
            f"({100 * correct / total:.2f}%)"
        )
        print(
            f"  Strict parse completion: "
            f"{completed}/{total}"
        )
        print(
            f"  Grammar probes: {probes}"
        )

    print("\nDecision changes:", decisions_changed)
    print("Improved cases:", improved)
    print("Worsened cases:", worsened)

    output = Path(
        "results/ambiguous_benchmark.csv"
    )

    with output.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nResults saved to:", output)

    if decisions_changed == 0:
        print(
            "\nFINDING: Grammar validation was invoked,"
            "\nbut did not change the heuristic decisions"
            "\non this benchmark."
        )

    print(
        "\nLIMITATION: This is a small, hand-labelled"
        "\nbenchmark of single-error programs."
    )

    return rows


if __name__ == "__main__":
    run_benchmark()
