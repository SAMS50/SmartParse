
"""
SmartParse Milestone 9B
Final technical verification.

Audits:
1. Statement-level recovery and parser progress
2. Panic-mode baseline diagnostics
3. Performance with rotated measurement order

Does not modify the production parser.
"""

import csv
import statistics
import time
from pathlib import Path

from smartparse import Parser, tokenize
from ablation_eval import run_mode
from dataset import DATASET
from ambiguous_benchmark import CASES
from stress_eval import STRESS_CASES


OUTPUT_DIR = Path("results")
MODES = ("panic", "heuristic", "grammar_validated")


class TracedParser(Parser):
    """
    Records statement parsing attempts.

    This trace measures parser control flow.
    It does not prove semantic correctness.
    """

    def __init__(self, tokens, validate_repairs=True):
        super().__init__(
            tokens,
            validate_repairs=validate_repairs
        )
        self.trace = []

    def _statement(self):
        start = self.i
        errors_before = len(self.diagnostics)
        repairs_before = len(self.repairs)

        try:
            result = super()._statement()
        except Exception:
            self.trace.append({
                "start": start,
                "end": self.i,
                "status": "failed",
                "new_diagnostics": (
                    len(self.diagnostics) - errors_before
                ),
                "new_repairs": (
                    len(self.repairs) - repairs_before
                )
            })
            raise

        self.trace.append({
            "start": start,
            "end": self.i,
            "status": "returned",
            "new_diagnostics": (
                len(self.diagnostics) - errors_before
            ),
            "new_repairs": (
                len(self.repairs) - repairs_before
            )
        })

        return result


def audit_recovery():
    rows = []

    print("=" * 72)
    print("RECOVERY TRACE AUDIT")
    print("=" * 72)

    for case in STRESS_CASES:
        for validated in (False, True):
            tokens = tokenize(case["source"])

            parser = TracedParser(
                tokens,
                validate_repairs=validated
            )

            parser.parse()

            returned = [
                item for item in parser.trace
                if item["status"] == "returned"
            ]

            failed = [
                item for item in parser.trace
                if item["status"] == "failed"
            ]

            returned_after_repair = sum(
                item["new_repairs"] > 0
                for item in returned
            )

            row = {
                "case_id": case["id"],
                "mode": (
                    "validated" if validated
                    else "heuristic"
                ),
                "statement_attempts": len(parser.trace),
                "returned_statements": len(returned),
                "failed_statements": len(failed),
                "returned_with_repairs": (
                    returned_after_repair
                ),
                "diagnostics": len(parser.diagnostics),
                "repairs": len(parser.repairs),
                "reached_eof": (
                    parser.peek().kind == "EOF"
                )
            }

            rows.append(row)

            print(
                f"{row['case_id']} "
                f"{row['mode']:<10} "
                f"attempts={row['statement_attempts']} "
                f"returned={row['returned_statements']} "
                f"failed={row['failed_statements']} "
                f"repaired_returns="
                f"{row['returned_with_repairs']}"
            )

    save_csv(
        OUTPUT_DIR / "recovery_audit.csv",
        rows
    )

    print(
        "\nNOTE: A returned statement may contain "
        "nested statements. Counts are not "
        "independent program statements."
    )

    return rows


def audit_baseline():
    rows = []

    print("\n" + "=" * 72)
    print("PANIC-MODE DIAGNOSTIC AUDIT")
    print("=" * 72)

    for case in DATASET:
        result = run_mode(
            case["source"], "panic"
        )

        diagnostics = result["diagnostics"]

        print(
            f"\n{case['id']} | {case['name']}"
            f" | diagnostics={len(diagnostics)}"
        )

        for diagnostic in diagnostics:
            row = {
                "case_id": case["id"],
                "line": diagnostic["line"],
                "column": diagnostic["column"],
                "message": diagnostic["message"]
            }

            rows.append(row)

            print(
                f"  {row['line']}:{row['column']} "
                f"{row['message']}"
            )

    save_csv(
        OUTPUT_DIR / "baseline_audit.csv",
        rows
    )

    print(
        "\nInspect repeated diagnostics at closing "
        "braces. These may indicate cascading "
        "errors caused by synchronization."
    )

    return rows


def measure_performance(repetitions=300):
    """
    Rotate execution order between repetitions.

    Measures entire workload batches.
    No fixed performance improvement is assumed.
    """

    workloads = {
        "labelled": [
            case["source"] for case in DATASET
        ],
        "ambiguous": [
            case["source"] for case in CASES
        ],
        "stress": [
            case["source"] for case in STRESS_CASES
        ]
    }

    rows = []

    print("\n" + "=" * 72)
    print("ROTATED PERFORMANCE BENCHMARK")
    print("=" * 72)

    for workload_name, sources in workloads.items():
        samples = {
            mode: [] for mode in MODES
        }

        # Warm up all three configurations.
        for mode in MODES:
            for source in sources:
                run_mode(source, mode)

        for repetition in range(repetitions):
            shift = repetition % len(MODES)

            order = (
                MODES[shift:] + MODES[:shift]
            )

            for mode in order:
                start = time.perf_counter_ns()

                for source in sources:
                    run_mode(source, mode)

                elapsed_ms = (
                    time.perf_counter_ns() - start
                ) / 1_000_000

                samples[mode].append(elapsed_ms)

        print(f"\n{workload_name.upper()}")

        for mode in MODES:
            values = samples[mode]

            row = {
                "workload": workload_name,
                "mode": mode,
                "programs": len(sources),
                "repetitions": repetitions,
                "median_ms": statistics.median(values),
                "mean_ms": statistics.mean(values),
                "min_ms": min(values),
                "max_ms": max(values)
            }

            rows.append(row)

            print(
                f"  {mode:<18} "
                f"median={row['median_ms']:.4f} ms "
                f"mean={row['mean_ms']:.4f} ms"
            )

    save_csv(
        OUTPUT_DIR / "verified_performance.csv",
        rows
    )

    print(
        "\nTiming includes tokenization and parsing. "
        "Results are exploratory measurements "
        "on this machine, not universal benchmarks."
    )

    return rows


def save_csv(path, rows):
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not rows:
        print("No rows to save:", path)
        return

    with path.open(
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

    print("Saved:", path)


def main():
    audit_recovery()
    audit_baseline()
    measure_performance()


if __name__ == "__main__":
    main()
