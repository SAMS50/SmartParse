# Phase 5D: Reliability evaluation (experimental)

Run:

```powershell
python -m unittest discover -v
python phase5d_eval.py --repeats 3 --max-edits 3 --max-nodes 150
```

The evaluation contains 16 hand-curated cases with explicit intended reference programs. The planner is compared to the reference *token sequence*, not just whether the corrected code parses. It reports exact matches, grammatically valid but unintended repairs, and cases where the planner abstains under the search budget. It also records existing-parser diagnostic and repair counts as descriptive information, **not a fair accuracy comparison**, because the old parser's repairs are represented differently and are not replayed into a corrected token stream here.

Initial run: 12/16 exact reference matches, 1 grammatically valid but unintended correction, 3 no-plan outcomes. This small curated dataset is not an independent real-world benchmark, and is not evidence of superiority to published systems.

Current gaps: expression/identifier/operator repairs, ambiguous grammar-valid alternatives, and reliable correction ranking. The new planner remains separate from the main Parser. Next: add ambiguity-aware alternative enumeration, and compare all modes on a common exact-repair representation with broader held-out cases.
