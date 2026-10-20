
"""
SmartParse — Final Research Results and Visualizations

Generates:
    1. Diagnostic accuracy comparison
    2. Diagnostic error analysis
    3. Performance comparison
    4. Stress-test robustness

Also exports:
    - accuracy_summary.csv
    - performance_summary.csv
    - benchmark_summary.csv

Performance data is loaded from:
    results/verified_performance.csv

Run:
    python verification_eval.py
    python final_results.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = BASE_DIR / "results"
OUTPUT_DIR = RESULTS_DIR / "final"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# VERIFIED DIAGNOSTIC ACCURACY
# --------------------------------------------------

# Results from 12 labelled programs containing
# 11 labelled syntax-error anchors.

ACCURACY = {
    "Panic mode": {
        "tp": 10,
        "fp": 5,
        "fn": 1
    },
    "Heuristic": {
        "tp": 11,
        "fp": 0,
        "fn": 0
    },
    "Grammar-validated": {
        "tp": 11,
        "fp": 0,
        "fn": 0
    }
}


# --------------------------------------------------
# AMBIGUOUS RECOVERY RESULTS
# --------------------------------------------------

# Both SmartParse modes selected the intended
# repair operation in all six curated cases.

AMBIGUOUS = {
    "Heuristic": 6,
    "Grammar-validated": 6
}


# --------------------------------------------------
# STRESS EVALUATION RESULTS
# --------------------------------------------------

# Both SmartParse modes met the defined
# minimum-diagnostic and EOF criteria
# in all six stress scenarios.

STRESS = {
    "Heuristic": 6,
    "Grammar-validated": 6
}


# --------------------------------------------------
# LOAD PERFORMANCE DATA
# --------------------------------------------------

def load_performance():
    """
    Load latest rotated performance results.

    CSV columns expected:
        workload
        mode
        programs
        repetitions
        median_ms
        mean_ms
        min_ms
        max_ms
    """

    path = RESULTS_DIR / "verified_performance.csv"

    if not path.exists():
        raise FileNotFoundError(
            "Performance results not found.\n"
            "Run: python verification_eval.py"
        )

    mode_names = {
        "panic": "Panic mode",
        "heuristic": "Heuristic",
        "grammar_validated": "Grammar-validated"
    }

    workload_names = {
        "labelled": "Labelled",
        "ambiguous": "Ambiguous",
        "stress": "Stress"
    }

    performance = {}

    with path.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            workload_key = row["workload"]
            mode_key = row["mode"]

            if workload_key not in workload_names:
                raise ValueError(
                    f"Unknown workload: {workload_key}"
                )

            if mode_key not in mode_names:
                raise ValueError(
                    f"Unknown mode: {mode_key}"
                )

            workload = workload_names[workload_key]
            mode = mode_names[mode_key]

            median = float(row["median_ms"])

            performance.setdefault(
                workload, {}
            )[mode] = median

    required_modes = set(mode_names.values())

    for workload in workload_names.values():
        if workload not in performance:
            raise ValueError(
                f"Missing workload: {workload}"
            )

        missing = required_modes - set(
            performance[workload]
        )

        if missing:
            raise ValueError(
                f"Missing modes for {workload}: "
                f"{sorted(missing)}"
            )

    return {
        name: performance[name]
        for name in workload_names.values()
    }


# --------------------------------------------------
# ACCURACY METRICS
# --------------------------------------------------

def calculate_metrics(counts):
    """
    Calculate precision, recall and F1.
    """

    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]

    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else 1.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 1.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    return precision, recall, f1


# --------------------------------------------------
# CSV EXPORT
# --------------------------------------------------

def save_csv(filename, headers, rows):

    path = OUTPUT_DIR / filename

    with path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(headers)
        writer.writerows(rows)

    print("Saved:", path)


# --------------------------------------------------
# GRAPH EXPORT
# --------------------------------------------------

def save_graph(filename):

    plt.tight_layout()

    path = OUTPUT_DIR / filename

    plt.savefig(
        path,
        dpi=220,
        bbox_inches="tight"
    )

    plt.close()

    print("Saved:", path)


# --------------------------------------------------
# GRAPH 1 — DIAGNOSTIC ACCURACY
# --------------------------------------------------

def plot_accuracy():

    names = list(ACCURACY.keys())

    values = [
        calculate_metrics(ACCURACY[name])
        for name in names
    ]

    categories = [
        "Precision",
        "Recall",
        "F1 score"
    ]

    x = list(range(len(categories)))
    width = 0.24

    fig, ax = plt.subplots(
        figsize=(9, 5.5)
    )

    for index, name in enumerate(names):

        scores = [
            values[index][metric_index] * 100
            for metric_index in range(3)
        ]

        positions = [
            position + (index - 1) * width
            for position in x
        ]

        bars = ax.bar(
            positions,
            scores,
            width,
            label=name
        )

        ax.bar_label(
            bars,
            fmt="%.1f",
            padding=3,
            fontsize=8
        )

    ax.set_xticks(
        x,
        categories
    )

    ax.set_ylim(0, 115)

    ax.set_ylabel(
        "Score (%)"
    )

    ax.set_title(
        "Diagnostic Accuracy — "
        "12 Labelled Programs"
    )

    ax.legend()

    ax.grid(
        axis="y",
        alpha=0.2
    )

    save_graph(
        "01_diagnostic_accuracy.png"
    )


# --------------------------------------------------
# GRAPH 2 — DIAGNOSTIC ERROR COUNTS
# --------------------------------------------------

def plot_error_counts():

    names = list(ACCURACY.keys())

    categories = [
        "True positives",
        "False positives",
        "False negatives"
    ]

    keys = [
        "tp",
        "fp",
        "fn"
    ]

    x = list(range(len(categories)))
    width = 0.24

    fig, ax = plt.subplots(
        figsize=(9, 5.5)
    )

    for index, name in enumerate(names):

        values = [
            ACCURACY[name][key]
            for key in keys
        ]

        positions = [
            position + (index - 1) * width
            for position in x
        ]

        bars = ax.bar(
            positions,
            values,
            width,
            label=name
        )

        ax.bar_label(
            bars,
            padding=3,
            fontsize=9
        )

    ax.set_xticks(
        x,
        categories
    )

    ax.set_ylim(0, 13)

    ax.set_ylabel(
        "Diagnostic anchors"
    )

    ax.set_title(
        "Diagnostic Error Analysis"
    )

    ax.legend()

    ax.grid(
        axis="y",
        alpha=0.2
    )

    save_graph(
        "02_error_analysis.png"
    )


# --------------------------------------------------
# GRAPH 3 — PERFORMANCE COMPARISON
# --------------------------------------------------

def plot_performance(performance):

    workloads = list(performance.keys())

    modes = list(ACCURACY.keys())

    x = list(range(len(workloads)))
    width = 0.24

    fig, ax = plt.subplots(
        figsize=(9, 5.5)
    )

    maximum_time = max(
        performance[workload][mode]
        for workload in workloads
        for mode in modes
    )

    for index, mode in enumerate(modes):

        values = [
            performance[workload][mode]
            for workload in workloads
        ]

        positions = [
            position + (index - 1) * width
            for position in x
        ]

        bars = ax.bar(
            positions,
            values,
            width,
            label=mode
        )

        ax.bar_label(
            bars,
            fmt="%.3f",
            padding=3,
            fontsize=8
        )

    ax.set_xticks(
        x,
        workloads
    )

    ax.set_ylim(
        0,
        maximum_time * 1.30
    )

    ax.set_ylabel(
        "Median time (ms)"
    )

    ax.set_title(
        "Parsing Performance — "
        "Rotated Benchmark"
    )

    ax.legend()

    ax.grid(
        axis="y",
        alpha=0.2
    )

    save_graph(
        "03_performance_comparison.png"
    )


# --------------------------------------------------
# GRAPH 4 — STRESS ROBUSTNESS
# --------------------------------------------------

def plot_robustness():

    modes = list(STRESS.keys())

    values = [
        STRESS[mode]
        for mode in modes
    ]

    fig, ax = plt.subplots(
        figsize=(7.5, 5)
    )

    bars = ax.bar(
        modes,
        values
    )

    ax.bar_label(
        bars,
        labels=[
            f"{STRESS[mode]}/6"
            for mode in modes
        ],
        padding=4
    )

    ax.set_ylim(0, 7)

    ax.set_ylabel(
        "Cases meeting test criteria"
    )

    ax.set_title(
        "Stress Benchmark — "
        "6 Test Scenarios"
    )

    ax.grid(
        axis="y",
        alpha=0.2
    )

    save_graph(
        "04_stress_robustness.png"
    )


# --------------------------------------------------
# EXPORT RESEARCH SUMMARY TABLES
# --------------------------------------------------

def export_summaries(performance):

    # Diagnostic accuracy

    accuracy_rows = []

    for name, counts in ACCURACY.items():

        precision, recall, f1 = (
            calculate_metrics(counts)
        )

        accuracy_rows.append([
            name,
            counts["tp"],
            counts["fp"],
            counts["fn"],
            round(precision * 100, 2),
            round(recall * 100, 2),
            round(f1 * 100, 2)
        ])

    save_csv(
        "accuracy_summary.csv",
        [
            "mode",
            "tp",
            "fp",
            "fn",
            "precision_pct",
            "recall_pct",
            "f1_pct"
        ],
        accuracy_rows
    )

    # Performance

    performance_rows = []

    for workload, modes in performance.items():

        for mode, median in modes.items():

            performance_rows.append([
                workload,
                mode,
                median
            ])

    save_csv(
        "performance_summary.csv",
        [
            "workload",
            "mode",
            "median_ms"
        ],
        performance_rows
    )

    # Benchmark results

    benchmark_rows = []

    for mode in AMBIGUOUS:

        benchmark_rows.append([
            mode,
            AMBIGUOUS[mode],
            STRESS[mode]
        ])

    save_csv(
        "benchmark_summary.csv",
        [
            "mode",
            "ambiguous_correct_of_6",
            "stress_cases_passed_of_6"
        ],
        benchmark_rows
    )


# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------

def print_summary(performance):

    print("\n" + "=" * 65)
    print("SMARTPARSE — FINAL RESEARCH SUMMARY")
    print("=" * 65)

    print("\nDIAGNOSTIC ACCURACY")

    for mode, counts in ACCURACY.items():

        precision, recall, f1 = (
            calculate_metrics(counts)
        )

        print(
            f"{mode:<20}"
            f"Precision={precision * 100:.2f}%  "
            f"Recall={recall * 100:.2f}%  "
            f"F1={f1 * 100:.2f}%"
        )

    print("\nPERFORMANCE — MEDIAN TIME (ms)")

    for workload, modes in performance.items():

        print(f"\n{workload} workload:")

        for mode, median in modes.items():

            print(
                f"  {mode:<20}"
                f"{median:.4f} ms"
            )

    ambiguous = performance["Ambiguous"]

    heuristic_time = ambiguous["Heuristic"]
    validated_time = ambiguous["Grammar-validated"]

    if heuristic_time > 0:

        overhead = (
            validated_time / heuristic_time
        )

        print(
            "\nGrammar-validation runtime ratio "
            f"on ambiguous workload: {overhead:.2f}x"
        )

    print("\nAMBIGUOUS RECOVERY")

    for mode, correct in AMBIGUOUS.items():

        print(
            f"{mode}: {correct}/6 intended "
            "operations selected"
        )

    print("\nSTRESS EVALUATION")

    for mode, passed in STRESS.items():

        print(
            f"{mode}: {passed}/6 cases met "
            "defined criteria"
        )

    print(
        "\nNOTE: Diagnostic accuracy is measured "
        "on a small curated dataset."
    )

    print(
        "Grammar validation has not demonstrated "
        "an accuracy advantage in the tested cases."
    )

    print(
        "Performance measurements are "
        "machine-dependent."
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print(
        "\nLoading verified performance results..."
    )

    performance = load_performance()

    print(
        "Performance CSV loaded successfully."
    )

    print(
        "\nGenerating final research outputs...\n"
    )

    export_summaries(performance)

    plot_accuracy()

    plot_error_counts()

    plot_performance(performance)

    plot_robustness()

    print_summary(performance)

    print(
        "\n" + "=" * 65
    )

    print(
        "Milestone 10B: Results generated successfully."
    )

    print(
        "Output directory:",
        OUTPUT_DIR
    )

    print("=" * 65)


if __name__ == "__main__":
    main()
