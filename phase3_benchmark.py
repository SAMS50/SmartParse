"""Opt-in bounded two-edit recovery against the frozen Phase 2 labels."""
import argparse
import csv
from pathlib import Path
from statistics import median
from time import perf_counter
from phase2_benchmark import CASES
from smartparse import Parser, tokenize


def evaluate(repeats=5):
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    rows = []
    for case_id, source, intended in CASES:
        for mode in ("phase2", "bounded_pair"):
            samples = []
            for _ in range(repeats):
                start = perf_counter()
                parser = Parser(tokenize(source), validate_repairs=True,
                                scoring_mode="contextual", validation_policy="selective",
                                multi_token_recovery=(mode == "bounded_pair"))
                parser.parse()
                samples.append((perf_counter() - start) * 1000)
            actual = [(r["operation"], r["token"], r["from"]) for r in parser.repairs]
            rows.append({"case": case_id, "mode": mode, "expected_repairs": len(intended),
                         "correct_repairs": sum(r in actual for r in intended),
                         "exact_sequence": int(actual == intended),
                         "reported_repairs": len(actual), "diagnostics": len(parser.diagnostics),
                         "multi_token_attempted": parser.multi_token_stats["attempted"],
                         "multi_token_accepted": parser.multi_token_stats["accepted"],
                         "median_ms": round(median(samples), 5),
                         "actual": repr(actual), "intended": repr(intended)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()
    rows = evaluate(args.repeats)
    out = Path("results/phase3_repair_choices.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for mode in ("phase2", "bounded_pair"):
        sub = [r for r in rows if r["mode"] == mode]
        print(f"{mode:12} correct={sum(r['correct_repairs'] for r in sub)}/"
              f"{sum(r['expected_repairs'] for r in sub)} "
              f"exact_cases={sum(r['exact_sequence'] for r in sub)}/{len(sub)} "
              f"median_case_ms={median(r['median_ms'] for r in sub):.5f}")
    print("Saved:", out)


if __name__ == "__main__":
    main()
