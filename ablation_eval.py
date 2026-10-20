
"""
SmartParse Milestone 8
Three-way ablation study.

Compares:
1. Traditional panic-mode baseline
2. Heuristic-only SmartParse
3. Grammar-validated SmartParse

Uses the same lexer and grammar for each approach.
"""

import csv
from pathlib import Path

from smartparse import Parser, tokenize
from baseline import analyze_baseline
from dataset import DATASET
from metrics import (
    evaluate_diagnostics,
    aggregate,
    percentage
)


OUTPUT_DIR = Path("results")

MODES = (
    "panic",
    "heuristic",
    "grammar_validated"
)


def run_mode(source, mode):
    if mode == "panic":
        result = analyze_baseline(source)

        return {
            "diagnostics": result["diagnostics"],
            "repairs": [],
            "skipped_tokens": result["skipped_tokens"]
        }

    tokens = tokenize(source)

    parser = Parser(
        tokens,
        validate_repairs=(
            mode == "grammar_validated"
        )
    )

    parser.parse()

    return {
        "diagnostics": parser.diagnostics,
        "repairs": parser.repairs,
        "skipped_tokens": None
    }


def run_ablation():
    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = []
    summaries = {}
    observations = {}

    for mode in MODES:
        print("\n" + "=" * 72)
        print("MODE:", mode.upper())
        print("=" * 72)

        case_scores = []
        total_repairs = 0
        total_skipped = 0
        total_probes = 0

        for case in DATASET:
            result = run_mode(
                case["source"], mode
            )

            scores = evaluate_diagnostics(
                case["errors"],
                result["diagnostics"]
            )

            case_scores.append(scores)

            repairs = result["repairs"]

            probes = sum(
                1 for repair in repairs
                if repair.get(
                    "grammar_validation"
                ) is not None
            )

            total_repairs += len(repairs)
            total_probes += probes

            if result["skipped_tokens"] is not None:
                total_skipped += result["skipped_tokens"]

            print(
                f"{case['id']} "
                f"{case['name']:<30} "
                f"TP={scores['tp']} "
                f"FP={scores['fp']} "
                f"FN={scores['fn']} "
                f"Repairs={len(repairs)} "
                f"Probes={probes}"
            )

            rows.append({
                "mode": mode,
                "case_id": case["id"],
                "case_name": case["name"],
                "expected_errors": len(case["errors"]),
                "diagnostics": len(
                    result["diagnostics"]
                ),
                "tp": scores["tp"],
                "fp": scores["fp"],
                "fn": scores["fn"],
                "repairs": len(repairs),
                "grammar_probes": probes,
                "skipped_tokens": (
                    result["skipped_tokens"]
                    if result["skipped_tokens"] is not None
                    else ""
                )
            })

        summaries[mode] = aggregate(case_scores)

        observations[mode] = {
            "repairs": total_repairs,
            "skipped": total_skipped,
            "probes": total_probes
        }

    print("\n" + "=" * 72)
    print("THREE-WAY COMPARISON")
    print("=" * 72)

    print(
        f"{'Metric':<22}"
        f"{'Panic':>13}"
        f"{'Heuristic':>13}"
        f"{'Validated':>13}"
    )

    print("-" * 61)

    for label, key in (
        ("True positives", "tp"),
        ("False positives", "fp"),
        ("False negatives", "fn")
    ):
        print(
            f"{label:<22}"
            f"{summaries['panic'][key]:>13}"
            f"{summaries['heuristic'][key]:>13}"
            f"{summaries['grammar_validated'][key]:>13}"
        )

    for label, key in (
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1 score", "f1")
    ):
        print(
            f"{label:<22}"
            f"{percentage(summaries['panic'][key]):>13}"
            f"{percentage(summaries['heuristic'][key]):>13}"
            f"{percentage(summaries['grammar_validated'][key]):>13}"
        )

    print("\nGrammar probes performed:",
          observations["grammar_validated"]["probes"])

    print(
        "Panic-mode tokens skipped:",
        observations["panic"]["skipped"]
    )

    output_file = (
        OUTPUT_DIR / "ablation_results.csv"
    )

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSaved:", output_file)

    print(
        "\nNOTE: Matching uses diagnostic anchors."
        "\nThis is not full repair correctness."
    )

    return summaries


if __name__ == "__main__":
    run_ablation()
