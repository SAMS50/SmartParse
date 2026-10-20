
"""
SmartParse Milestone 9
Robustness, recovery and performance evaluation.

No changes to the production parser are required.
"""

import csv
import statistics
import time
from pathlib import Path

from smartparse import Parser, StrictParser, ParseError, tokenize
from ablation_eval import run_mode
from dataset import DATASET
from ambiguous_benchmark import CASES


OUTPUT_DIR = Path("results")

STRESS_CASES = [
    {
        "id": "S01",
        "name": "Three missing semicolons",
        "source": (
            "int a = 1\n"
            "int b = 2\n"
            "int c = 3\n"
            "int d = 4;"
        ),
        "corrected": (
            "int a = 1;\n"
            "int b = 2;\n"
            "int c = 3;\n"
            "int d = 4;"
        ),
        "minimum_diagnostics": 3
    },
    {
        "id": "S02",
        "name": "Errors in separate blocks",
        "source": (
            "if (x > 0 {\n"
            "  x = 1;\n"
            "}\n"
            "while (x < 5 {\n"
            "  x++;\n"
            "}"
        ),
        "corrected": (
            "if (x > 0) {\n"
            "  x = 1;\n"
            "}\n"
            "while (x < 5) {\n"
            "  x++;\n"
            "}"
        ),
        "minimum_diagnostics": 2
    },
    {
        "id": "S03",
        "name": "Errors followed by valid code",
        "source": (
            "int x = 1\n"
            "int y = 2;\n"
            "y = y + 1;\n"
            "int z = 3;"
        ),
        "corrected": (
            "int x = 1;\n"
            "int y = 2;\n"
            "y = y + 1;\n"
            "int z = 3;"
        ),
        "minimum_diagnostics": 1
    },
    {
        "id": "S04",
        "name": "Nested missing parenthesis",
        "source": (
            "int main() {\n"
            "  if (x > 0 {\n"
            "    while (x < 5 {\n"
            "      x++;\n"
            "    }\n"
            "  }\n"
            "  return 0;\n"
            "}"
        ),
        "corrected": (
            "int main() {\n"
            "  if (x > 0) {\n"
            "    while (x < 5) {\n"
            "      x++;\n"
            "    }\n"
            "  }\n"
            "  return 0;\n"
            "}"
        ),
        "minimum_diagnostics": 2
    },
    {
        "id": "S05",
        "name": "Valid nested program",
        "source": (
            "int main() {\n"
            "  int x = 0;\n"
            "  while (x < 10) {\n"
            "    if (x > 5) { x++; }\n"
            "    x++;\n"
            "  }\n"
            "  return x;\n"
            "}"
        ),
        "corrected": (
            "int main() {\n"
            "  int x = 0;\n"
            "  while (x < 10) {\n"
            "    if (x > 5) { x++; }\n"
            "    x++;\n"
            "  }\n"
            "  return x;\n"
            "}"
        ),
        "minimum_diagnostics": 0
    },
    {
        "id": "S06",
        "name": "Ambiguous repair after earlier error",
        "source": (
            "int a = 1\n"
            "int b = 2;\n"
            "if (x > 5 ; ) x = 1;"
        ),
        "corrected": (
            "int a = 1;\n"
            "int b = 2;\n"
            "if (x > 5) x = 1;"
        ),
        "minimum_diagnostics": 2
    }
]


def strict_accepts(source):
    parser = StrictParser(tokenize(source))

    try:
        parser.parse()
        return parser.peek().kind == "EOF"
    except ParseError:
        return False


def run_smartparse(source, validated):
    tokens = tokenize(source)
    parser = Parser(
        tokens,
        validate_repairs=validated
    )
    parser.parse()

    return {
        "diagnostics": parser.diagnostics,
        "repairs": parser.repairs,
        "reached_eof": parser.peek().kind == "EOF",
        "grammar_probes": sum(
            repair.get("grammar_validation") is not None
            for repair in parser.repairs
        )
    }


def evaluate_stress_case(case):
    if not strict_accepts(case["corrected"]):
        raise AssertionError(
            f"{case['id']}: corrected reference "
            "does not parse strictly"
        )

    results = {}

    for mode in ("heuristic", "validated"):
        result = run_smartparse(
            case["source"],
            validated=(mode == "validated")
        )

        results[mode] = {
            "diagnostics": len(result["diagnostics"]),
            "repairs": len(result["repairs"]),
            "reached_eof": result["reached_eof"],
            "grammar_probes": result["grammar_probes"],
            "meets_minimum": (
                len(result["diagnostics"])
                >= case["minimum_diagnostics"]
            )
        }

    return results


def timed_run(source, mode, repetitions=100):
    durations = []

    for _ in range(repetitions):
        start = time.perf_counter()
        run_mode(source, mode)
        elapsed = time.perf_counter() - start
        durations.append(elapsed * 1000)

    return {
        "mean_ms": statistics.mean(durations),
        "median_ms": statistics.median(durations),
        "min_ms": min(durations),
        "max_ms": max(durations)
    }


def run_stress_evaluation():
    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = []

    print("=" * 70)
    print("MILESTONE 9: ROBUSTNESS EVALUATION")
    print("=" * 70)

    for case in STRESS_CASES:
        results = evaluate_stress_case(case)

        print(f"\n{case['id']} | {case['name']}")

        for mode, result in results.items():
            print(
                f"  {mode:<10} "
                f"diagnostics={result['diagnostics']} "
                f"repairs={result['repairs']} "
                f"EOF={result['reached_eof']} "
                f"probes={result['grammar_probes']} "
                f"minimum_met={result['meets_minimum']}"
            )

            rows.append({
                "case_id": case["id"],
                "case_name": case["name"],
                "mode": mode,
                **result
            })

    output = OUTPUT_DIR / "stress_results.csv"

    with output.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSaved:", output)
    print(
        "\nImportant: EOF means the parser reached "
        "the end of its token stream. It does NOT "
        "prove every statement was recovered."
    )

    return rows


def run_performance_evaluation(repetitions=100):
    OUTPUT_DIR.mkdir(exist_ok=True)

    workloads = [
        {
            "id": "P01",
            "name": "Original labelled dataset",
            "sources": [
                case["source"] for case in DATASET
            ]
        },
        {
            "id": "P02",
            "name": "Ambiguous repair dataset",
            "sources": [
                case["source"] for case in CASES
            ]
        },
        {
            "id": "P03",
            "name": "Stress dataset",
            "sources": [
                case["source"] for case in STRESS_CASES
            ]
        }
    ]

    rows = []

    print("\n" + "=" * 70)
    print("PERFORMANCE EVALUATION")
    print("=" * 70)

    for workload in workloads:
        print(f"\n{workload['id']} | {workload['name']}")

        for mode in (
            "panic", "heuristic", "grammar_validated"
        ):
            # Warm up before timing.
            for source in workload["sources"]:
                run_mode(source, mode)

            samples = []

            for _ in range(repetitions):
                start = time.perf_counter()

                for source in workload["sources"]:
                    run_mode(source, mode)

                samples.append(
                    (time.perf_counter() - start) * 1000
                )

            measurement = {
                "workload": workload["id"],
                "name": workload["name"],
                "mode": mode,
                "program_count": len(workload["sources"]),
                "repetitions": repetitions,
                "mean_ms": statistics.mean(samples),
                "median_ms": statistics.median(samples),
                "min_ms": min(samples),
                "max_ms": max(samples)
            }

            rows.append(measurement)

            print(
                f"  {mode:<18} "
                f"median={measurement['median_ms']:.4f} ms "
                f"mean={measurement['mean_ms']:.4f} ms"
            )

    output = OUTPUT_DIR / "performance_results.csv"

    with output.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nSaved:", output)
    print(
        "\nTiming is exploratory. Small workloads, "
        "Python interpreter overhead, and system "
        "activity affect these measurements."
    )

    return rows


if __name__ == "__main__":
    run_stress_evaluation()
    run_performance_evaluation()
