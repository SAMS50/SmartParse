
import csv
from pathlib import Path

from smartparse import analyze
from baseline import analyze_baseline
from dataset import DATASET
from metrics import (
    evaluate_diagnostics,
    aggregate,
    percentage
)


OUTPUT_DIR = Path("results")


def run_parser(source, mode):
    if mode == "smartparse":
        _, diagnostics, repairs = analyze(source)

        return {
            "diagnostics": diagnostics,
            "repairs": len(repairs),
            "skipped_tokens": None
        }

    result = analyze_baseline(source)

    return {
        "diagnostics": result["diagnostics"],
        "repairs": 0,
        "skipped_tokens": result["skipped_tokens"]
    }


def run_evaluation():
    OUTPUT_DIR.mkdir(exist_ok=True)

    all_rows = []
    summaries = {}

    for mode in ("smartparse", "panic"):
        print("\n" + "=" * 65)
        print(f"EVALUATING: {mode.upper()}")
        print("=" * 65)

        case_metrics = []

        for case in DATASET:
            result = run_parser(case["source"], mode)

            scores = evaluate_diagnostics(
                case["errors"],
                result["diagnostics"]
            )

            case_metrics.append(scores)

            status = (
                "PASS"
                if scores["fp"] == 0 and scores["fn"] == 0
                else "CHECK"
            )

            print(
                f"{case['id']} | {case['name']:<29} "
                f"| {status}"
            )

            print(
                f"     TP={scores['tp']} "
                f"FP={scores['fp']} "
                f"FN={scores['fn']}"
            )

            for diagnostic in result["diagnostics"]:
                print(
                    f"     {diagnostic['line']}:"
                    f"{diagnostic['column']} "
                    f"{diagnostic['message']}"
                )

            all_rows.append({
                "parser": mode,
                "case_id": case["id"],
                "case_name": case["name"],
                "ground_truth": scores["ground_truth"],
                "diagnostics": scores["diagnostics"],
                "true_positive": scores["tp"],
                "false_positive": scores["fp"],
                "false_negative": scores["fn"],
                "precision": (
                    "" if scores["precision"] is None
                    else round(scores["precision"], 4)
                ),
                "recall": (
                    "" if scores["recall"] is None
                    else round(scores["recall"], 4)
                ),
                "complete_detection": scores["detected_all"],
                "local_repairs": result["repairs"],
                "skipped_tokens": (
                    "" if result["skipped_tokens"] is None
                    else result["skipped_tokens"]
                )
            })

        summaries[mode] = aggregate(case_metrics)

    output_file = OUTPUT_DIR / "evaluation_results.csv"

    with output_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=all_rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print("\n" + "=" * 65)
    print("FINAL RESEARCH EVALUATION SUMMARY")
    print("=" * 65)

    print(
        f"{'Metric':<29}"
        f"{'SmartParse':>15}"
        f"{'Panic Mode':>15}"
    )
    print("-" * 65)

    metrics = [
        ("True positives", "tp"),
        ("False positives", "fp"),
        ("False negatives", "fn"),
        ("Complete detection cases",
         "complete_detection_cases")
    ]

    for label, key in metrics:
        print(
            f"{label:<29}"
            f"{summaries['smartparse'][key]:>15}"
            f"{summaries['panic'][key]:>15}"
        )

    for label, key in [
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1 score", "f1")
    ]:
        print(
            f"{label:<29}"
            f"{percentage(summaries['smartparse'][key]):>15}"
            f"{percentage(summaries['panic'][key]):>15}"
        )

    print("\nResults saved to:", output_file)

    print(
        "\nNOTE: Metrics use labelled diagnostic anchors. "
        "They do not prove that a repair is syntactically "
        "valid or that parsing fully recovered."
    )

    return summaries


if __name__ == "__main__":
    run_evaluation()

