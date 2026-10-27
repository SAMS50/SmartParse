# Review 3 — Milestone 4, Phase 2

## Added

- `Parser(..., validation_policy="selective", validation_margin=10)` enables selective local grammar probing. Existing `validation_policy="all"` is the default for backwards compatibility.
- `parser.validation_stats` counts eligible, performed and skipped probes.
- `phase2_benchmark.py` evaluates intended repair operations on six same-statement cases, including two difficult adjacent-error cases. It saves a case-level CSV with both successful and failed repairs.
- `test_phase2_benchmark.py` adds four regression tests.

## How to run

```powershell
python -m unittest discover -v
python phase2_benchmark.py --repeats 5
```

## Interpretation and limitations

On the initial six cases (11 labelled edits), legacy and contextual heuristics each recover 7/11 edits; unconditional grammar validation recovers 3/11, while selective validation recovers 7/11 and skips four probes. Selective validation avoids the observed harmful probes, but is **not** proven superior generally. The threshold 10 is a preliminary design parameter, not trained or tuned on a held-out set. The six cases are a small hand-authored challenge set, not a representative dataset.

The double-error conditions `; ]` expose a real limitation: the parser's candidate generator cannot plan two consecutive edits when no single edit is sufficient. This is a future implementation target. Do not present this phase as proof of improved accuracy over legacy scoring.
