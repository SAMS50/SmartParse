
from smartparse import analyze
from baseline import analyze_baseline


TEST_CASES = [
    {
        "name": "Valid program",
        "source": """
int x = 5;
int y = 10;
x = x + y;
"""
    },
    {
        "name": "Missing semicolon",
        "source": """
int x = 5
int y = 10;
"""
    },
    {
        "name": "Missing parenthesis",
        "source": """
if (x > 10 {
    x = x + 1;
}
"""
    },
    {
        "name": "Wrong closing bracket",
        "source": """
if (x > 10] {
    x = x + 1;
}
"""
    },
    {
        "name": "Multiple syntax errors",
        "source": """
int x = 5
int y = 10
int z = 15;
"""
    },
    {
        "name": "Nested control structures",
        "source": """
int x = 0;
while (x < 10) {
    if (x > 5 {
        x = x + 1;
    }
}
"""
    },
    {
        "name": "Missing closing brace",
        "source": """
int main() {
    int x = 5;
    return x;
"""
    },
    {
        "name": "Valid for loop",
        "source": """
for (int i = 0; i < 5; i++) {
    x = x + i;
}
"""
    }
]


def run_evaluation():
    results = []

    print("=" * 72)
    print("SMARTPARSE VS PANIC-MODE BASELINE")
    print("=" * 72)

    for case in TEST_CASES:
        source = case["source"]

        _, smart_errors, smart_repairs = analyze(source)
        baseline = analyze_baseline(source)

        smart_count = len(smart_errors)
        baseline_count = len(baseline["diagnostics"])

        results.append({
            "name": case["name"],
            "smart_errors": smart_count,
            "baseline_errors": baseline_count,
            "smart_repairs": len(smart_repairs),
            "baseline_skipped": baseline["skipped_tokens"]
        })

        print(f"\nTEST: {case['name']}")
        print("-" * 72)

        print("SmartParse:")
        print(f"  Diagnostics: {smart_count}")
        print(f"  Local repairs: {len(smart_repairs)}")

        for error in smart_errors:
            print(
                f"  {error['line']}:{error['column']} "
                f"{error['message']}"
            )

        print("Panic Mode:")
        print(f"  Diagnostics: {baseline_count}")
        print(
            f"  Skipped tokens: "
            f"{baseline['skipped_tokens']}"
        )

        for error in baseline["diagnostics"]:
            print(
                f"  {error['line']}:{error['column']} "
                f"{error['message']}"
            )

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    header = (
        f"{'Test':<29}"
        f"{'Smart':>8}"
        f"{'Panic':>8}"
        f"{'Repairs':>10}"
        f"{'Skipped':>10}"
    )

    print(header)
    print("-" * 72)

    for result in results:
        print(
            f"{result['name'][:28]:<29}"
            f"{result['smart_errors']:>8}"
            f"{result['baseline_errors']:>8}"
            f"{result['smart_repairs']:>10}"
            f"{result['baseline_skipped']:>10}"
        )

    print("-" * 72)

    total_smart = sum(
        result["smart_errors"] for result in results
    )
    total_panic = sum(
        result["baseline_errors"] for result in results
    )
    total_repairs = sum(
        result["smart_repairs"] for result in results
    )
    total_skipped = sum(
        result["baseline_skipped"] for result in results
    )

    print(
        f"{'TOTAL':<29}"
        f"{total_smart:>8}"
        f"{total_panic:>8}"
        f"{total_repairs:>10}"
        f"{total_skipped:>10}"
    )

    print("\nInterpretation:")
    print(
        "- Smart/Panic: number of diagnostic messages"
    )
    print(
        "- Repairs: SmartParse local recovery operations"
    )
    print(
        "- Skipped: tokens discarded by panic mode"
    )
    print(
        "\nThese are descriptive measurements, "
        "not yet accuracy or cascading-error metrics."
    )

    return results


if __name__ == "__main__":
    run_evaluation()

