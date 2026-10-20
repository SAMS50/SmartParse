
"""
SmartParse — Milestone 10A
Final research results and visualizations.

Data: verified experimental outputs from Milestone 9B.
Update these constants if future evaluations change.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


OUT = Path("results") / "final"
OUT.mkdir(parents=True, exist_ok=True)

# Final labelled-dataset results: 12 programs,
# 11 labelled syntax-error anchors.
ACCURACY = {
    "Panic mode": {
        "tp": 10, "fp": 5, "fn": 1
    },
    "Heuristic": {
        "tp": 11, "fp": 0, "fn": 0
    },
    "Grammar-validated": {
        "tp": 11, "fp": 0, "fn": 0
    },
}

# Median times from latest rotated benchmark.
# Units: milliseconds per entire workload.
PERFORMANCE = {
    "Labelled": {
        "Panic mode": 0.4762,
        "Heuristic": 0.5057,
        "Grammar-validated": 0.4935,
    },
    "Ambiguous": {
        "Panic mode": 0.1855,
        "Heuristic": 0.1851,
        "Grammar-validated": 0.3610,
    },
    "Stress": {
        "Panic mode": 0.3196,
        "Heuristic": 0.3504,
        "Grammar-validated": 0.3742,
    },
}

# Six ambiguous cases: both modes selected
# the intended repair in all six cases.
AMBIGUOUS = {
    "Heuristic": 6,
    "Grammar-validated": 6,
}

# Six stress cases: both modes reached EOF
# and met minimum diagnostic counts.
STRESS = {
    "Heuristic": 6,
    "Grammar-validated": 6,
}


def metrics(counts):
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]

    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return precision, recall, f1


def save_csv(filename, headers, rows):
    path = OUT / filename

    with path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    print("Saved:", path)


def finish_plot(filename):
    plt.tight_layout()
    path = OUT / filename
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    print("Saved:", path)


def plot_accuracy():
    names = list(ACCURACY)
    values = [metrics(ACCURACY[n]) for n in names]
    categories = ["Precision", "Recall", "F1 score"]

    x = list(range(len(categories)))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for index, name in enumerate(names):
        scores = [
            values[index][metric_index] * 100
            for metric_index in range(3)
        ]

        positions = [
            p + (index - 1) * width
            for p in x
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

    ax.set_xticks(x, categories)
    ax.set_ylim(0, 115)
    ax.set_ylabel("Score (%)")
    ax.set_title(
        "Diagnostic Accuracy — 12 Labelled Programs"
    )
    ax.legend()
    ax.grid(axis="y", alpha=0.2)

    finish_plot("01_diagnostic_accuracy.png")


def plot_error_counts():
    names = list(ACCURACY)

    categories = [
        "True positives",
        "False positives",
        "False negatives"
    ]
    keys = ["tp", "fp", "fn"]

    x = list(range(len(categories)))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for index, name in enumerate(names):
        values = [
            ACCURACY[name][key] for key in keys
        ]

        positions = [
            p + (index - 1) * width
            for p in x
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

    ax.set_xticks(x, categories)
    ax.set_ylim(0, 13)
    ax.set_ylabel("Diagnostic anchors")
    ax.set_title("Diagnostic Error Analysis")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)

    finish_plot("02_error_analysis.png")


def plot_performance():
    workloads = list(PERFORMANCE)
    modes = list(ACCURACY)

    x = list(range(len(workloads)))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for index, mode in enumerate(modes):
        values = [
            PERFORMANCE[workload][mode]
            for workload in workloads
        ]

        positions = [
            p + (index - 1) * width
            for p in x
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

    ax.set_xticks(x, workloads)
    ax.set_ylim(0, 0.65)
    ax.set_ylabel("Median time (ms)")
    ax.set_title(
        "Parsing Performance — Rotated Benchmark"
    )
    ax.legend()
    ax.grid(axis="y", alpha=0.2)

    finish_plot("03_performance_comparison.png")


def plot_robustness():
    modes = list(STRESS)

    fig, ax = plt.subplots(figsize=(7.5, 5))

    bars = ax.bar(
        modes,
        [STRESS[mode] for mode in modes]
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
    ax.set_ylabel("Cases meeting test criteria")
    ax.set_title(
        "Stress Benchmark — 6 Test Scenarios"
    )
    ax.grid(axis="y", alpha=0.2)

    finish_plot("04_stress_robustness.png")


def export_summaries():
    accuracy_rows = []

    for name, counts in ACCURACY.items():
        precision, recall, f1 = metrics(counts)

        accuracy_rows.append([
            name,
            counts["tp"],
            counts["fp"],
            counts["fn"],
            round(precision * 100, 2),
            round(recall * 100, 2),
            round(f1 * 100, 2),
        ])

    save_csv(
        "accuracy_summary.csv",
        [
            "mode", "tp", "fp", "fn",
            "precision_pct",
            "recall_pct", "f1_pct"
        ],
        accuracy_rows
    )

    performance_rows = [
        [
            workload,
            mode,
            median
        ]
        for workload, modes in PERFORMANCE.items()
        for mode, median in modes.items()
    ]

    save_csv(
        "performance_summary.csv",
        ["workload", "mode", "median_ms"],
        performance_rows
    )

    save_csv(
        "benchmark_summary.csv",
        [
            "mode",
            "ambiguous_correct_of_6",
            "stress_cases_passed_of_6"
        ],
        [
            [
                mode,
                AMBIGUOUS[mode],
                STRESS[mode]
            ]
            for mode in AMBIGUOUS
        ]
    )


def main():
    export_summaries()
    plot_accuracy()
    plot_error_counts()
    plot_performance()
    plot_robustness()

    print("\nMilestone 10A outputs generated.")
    print("Output directory:", OUT.resolve())


if __name__ == "__main__":
    main()
