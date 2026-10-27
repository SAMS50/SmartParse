# Phase 5G — Comparative evaluation (curated exploratory benchmark)

Run `python -m unittest discover -v` and `python phase5g_eval.py --repeats 5`.

This uses the **same 16 frozen Phase 5D cases** for panic-mode, original SmartParse, the conservative standalone CGAR advisor, and opt-in integrated CGAR. It writes per-case and summary CSV files under `results/`.

## Metric definitions and caveats

- `detected_invalid` counts cases with at least one reported diagnostic (or advisor status indicating malformed input). It is not error-location recall or cascading-error quality. There are 13 invalid and 3 valid inputs under the restricted grammar.
- `false_alarms_valid` counts cases marked erroneous among the three valid inputs. S07 (`int x = 1;;`) is **valid** because the second semicolon is an empty statement; the supplied reference removes it, but that does not make the original erroneous.
- `exact_reference` is reported **only when the mode returns a complete corrected token stream**. The original parser's local repair log is not reconstructed into a full corrected stream, and panic-mode does not propose edits; therefore their exact metric is N/A, not zero. Conditional exact-match fractions must **not** be described as overall accuracy.
- Standalone and integrated CGAR use the same underlying conservative advisor. They are **not independent algorithms**; matching repair results are expected. Integration adds diagnostics and fallback behavior.
- `median_ms` and `median_peak_kib` use repeated end-to-end invocations (including tokenization) measured with Python `tracemalloc`; they are exploratory, machine-dependent and include tracing overhead.
- This dataset is curated and overlaps development cases. It is **not** a blind holdout or evidence of superiority on real C code.
- A future genuinely fair exact-repair comparison needs a canonical patch reconstruction for original SmartParse and independent held-out examples; diagnostic quality requires location-level gold labels and cascade measures.

## Research conclusion

Treat CGAR as an opt-in grammar-verified **suggestion** system with conservative abstention and a legacy fallback. The current evidence supports functional integration and bounded repair on the supported grammar, but not universal correctness, semantic equivalence, or a proven improvement over prior recovery research.
