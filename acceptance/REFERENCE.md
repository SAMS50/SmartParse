# Manual acceptance reference (27 October 2026)

This list was established by reading the source before running the acceptance
CLI checks. It is a small author-created acceptance set, not a blind third-party
corpus. It must not be represented as validation of the unavailable 500-line
sample or general accuracy on arbitrary C. Nothing in these files is executed.

| Source | Line | Reference issue | Kind | Expected scope |
|---|---:|---|---|---|
| valid_inventory.c | — | No identified syntax/type defect in the reviewed program | Valid control | Should pass syntax/type checking; not proof of no possible bug |
| broken_records.c | 4 | Missing initializer expression | Syntax | Compiler diagnostic |
| broken_records.c | 9 | Missing operand after `+` | Syntax | Compiler diagnostic |
| broken_records.c | 13 | Undeclared `unknown_record` | Semantic/type | Compiler diagnostic |
| broken_records.c | 17 | Too many arguments to `accepts` | Semantic/type | Compiler diagnostic |
| pointer_and_logic.c | 5 | Dereference of known null pointer | Memory safety | Optional analyzer; not guaranteed by syntax-only checking |
| pointer_and_logic.c | 12 | Allocated buffer goes out of scope without `free` | Memory safety | Optional analyzer; report location may be at function exit |
| pointer_and_logic.c | 19 | Read through a freed pointer | Memory safety | Optional analyzer |
| pointer_and_logic.c | 26 | Free same allocation twice | Memory safety | Optional analyzer |
| pointer_and_logic.c | 32 | Loop omits last element, contrary to stated contract | Logic | No general intent/contract checking implemented |
| pointer_and_logic.c | 38 | Assignment in condition is deliberately intentional | Suspicious-code control | A warning is expected, but is not evidence of a genuine bug |

Use these outcome terms in the measured report: **detected** (matching backend
diagnostic at the relevant source anchor), **missed** (reference issue with no
diagnostic in the actual pass), **unsupported** (required analysis unavailable or
outside implemented scope), and **uncertain** (ambiguous evidence or intent).
Memory defects may be missed by the syntax-only pass while their analyzer
assessment remains unsupported. Do not report unavailable analysis as a negative
finding or include it in a recall denominator. Additional compiler warnings,
notes, and cascades must be recorded without counting each as an independent bug.

The supplied `c_error_detection_500_lines.c` was subsequently located in the
parent Downloads directory. Its separate pre-execution manual reference is
[sample_reference.json](sample_reference.json); the measured outcomes are in
[sample_comparison.md](output/sample_comparison.md). The three programs above
remain independent controls, not substitutes for that sample.
