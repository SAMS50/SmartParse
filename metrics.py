
"""
Diagnostic evaluation metrics for SmartParse.

A diagnostic is counted as a true positive when its
line and expected token match an unmatched ground-truth
error.

This is an anchor-level metric, not exact source-edit
accuracy or semantic correctness.
"""

import re


def diagnostic_token(message):
    """Extract the expected token from a diagnostic."""

    patterns = [
        r"Missing '([^']+)'",
        r"Expected '([^']+)'",
        r"Expected ([^\s]+) before"
    ]

    for pattern in patterns:
        match = re.search(pattern, message)

        if match:
            return match.group(1)

    return None


def evaluate_diagnostics(expected, actual):
    """
    Match diagnostics one-to-one against ground truth.

    Each labelled error can match at most one diagnostic.
    Unmatched diagnostics count as false positives.
    Unmatched expected errors count as false negatives.
    """

    unmatched = list(range(len(expected)))
    matches = []

    for diagnostic in actual:
        line = diagnostic["line"]
        token = diagnostic_token(diagnostic["message"])

        matched_index = None

        for index in unmatched:
            truth = expected[index]

            if (
                truth["line"] == line
                and truth["expected"] == token
            ):
                matched_index = index
                break

        if matched_index is not None:
            unmatched.remove(matched_index)
            matches.append(matched_index)

    tp = len(matches)
    fp = len(actual) - tp
    fn = len(expected) - tp

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": (
            tp / (tp + fp) if tp + fp else None
        ),
        "recall": (
            tp / (tp + fn) if tp + fn else None
        ),
        "false_diagnostics": fp,
        "detected_all": fn == 0,
        "diagnostics": len(actual),
        "ground_truth": len(expected)
    }


def aggregate(results):
    """Combine case-level diagnostic counts."""

    tp = sum(item["tp"] for item in results)
    fp = sum(item["fp"] for item in results)
    fn = sum(item["fn"] for item in results)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": (
            tp / (tp + fp) if tp + fp else None
        ),
        "recall": (
            tp / (tp + fn) if tp + fn else None
        ),
        "f1": (
            2 * tp / (2 * tp + fp + fn)
            if 2 * tp + fp + fn else None
        ),
        "false_diagnostics": fp,
        "complete_detection_cases": sum(
            item["detected_all"] for item in results
        ),
        "total_cases": len(results)
    }


def percentage(value):
    if value is None:
        return "N/A"

    return f"{value * 100:.2f}%"
