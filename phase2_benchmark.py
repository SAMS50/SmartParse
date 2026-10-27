"""Review 3 Phase 2: same-statement repair choices and selective probing.

The labels describe intended repairs, not just matching diagnostics.
This deliberately includes a difficult two-error condition where current
single-token recovery is expected to struggle; failures remain visible.
"""
import argparse
import csv
from pathlib import Path
from statistics import median
from time import perf_counter
from smartparse import Parser, tokenize

CASES = [
    ("C01", "if (x > 5 ; ) { x = 1 }", [("delete", ")", ";"), ("insert", ";", None)]),
    ("C02", "while (x < 3 ; ) { x = 1 }", [("delete", ")", ";"), ("insert", ";", None)]),
    ("C03", "if (x > 5 } { x = 1 }", [("substitute", ")", "}"), ("insert", ";", None)]),
    ("C04", "if (x > 5 ; ] { x = 1; }", [("delete", ")", ";"), ("substitute", ")", "]")]),
    ("C05", "while (x < 3 ; ] { x = 1; }", [("delete", ")", ";"), ("substitute", ")", "]")]),
    ("C06", "if (x > 5 ; ) { x = 1;; }", [("delete", ")", ";")]),
]


def evaluate(repeats=5):
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    rows = []
    for case_id, source, intended in CASES:
        for scoring, policy, validation in (
            ("legacy", "all", False),
            ("contextual", "all", False),
            ("contextual", "all", True),
            ("contextual", "selective", True),
        ):
            times = []
            parser = None
            for _ in range(repeats):
                start = perf_counter()
                parser = Parser(tokenize(source), validate_repairs=validation,
                                scoring_mode=scoring, validation_policy=policy)
                parser.parse()
                times.append((perf_counter() - start) * 1000)
            actual = [(r["operation"], r["token"], r["from"]) for r in parser.repairs]
            matched = sum(1 for repair in intended if repair in actual)
            rows.append({
                "case": case_id, "scoring": scoring, "validation": policy if validation else "off",
                "expected_repairs": len(intended), "correct_repairs": matched,
                "reported_repairs": len(actual), "exact_sequence": int(actual == intended),
                "diagnostics": len(parser.diagnostics),
                "eligible_probes": parser.validation_stats["eligible"],
                "performed_probes": parser.validation_stats["probed"],
                "skipped_probes": parser.validation_stats["skipped_confident"],
                "median_ms": round(median(times), 4),
                "actual": repr(actual), "intended": repr(intended),
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()
    rows = evaluate(args.repeats)
    out = Path("results/phase2_repair_choices.csv")
    out.parent.mkdir(exist_ok=True, parents=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for scoring, validation in (("legacy", "off"), ("contextual", "off"),
                                ("contextual", "all"), ("contextual", "selective")):
        subset = [r for r in rows if r["scoring"] == scoring and r["validation"] == validation]
        print(f"{scoring:10} {validation:9} correct={sum(r['correct_repairs'] for r in subset)}/"
              f"{sum(r['expected_repairs'] for r in subset)} exact_cases="
              f"{sum(r['exact_sequence'] for r in subset)}/{len(subset)} "
              f"probes={sum(r['performed_probes'] for r in subset)} "
              f"median_case_ms={median(r['median_ms'] for r in subset):.4f}")
    print("Failures are included in the CSV; labels are intended edits, not diagnostic anchors.")
    print("Saved:", out)


if __name__ == "__main__":
    main()
