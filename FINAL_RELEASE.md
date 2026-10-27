# SmartParse — Final academic release (Phase 5H)

## Scope and contribution
SmartParse studies recovery for a **restricted C-like grammar** using recursive-descent parsing. Its base system ranks token-level insertion, deletion and substitution candidates with context-aware heuristics and optional local grammar probes. The optional **CGAR (Context-Guided Adaptive Recovery)** research mode adds a bounded, whole-program grammar-verified suggestion planner, a conservative advisor, and a fallback to the existing parser. CGAR is a **project label**, not a claim of a newly established algorithm or novel priority over prior research.

CGAR is invoked before the normal parsing loop when `Parser(..., verified_cgar=True)` is selected. It is **not** an incremental search at every error. It does not rewrite the user's source. A syntactically valid repair may be semantically wrong or differ from the programmer's intent.

## Reproduce on Windows PowerShell
From the extracted `smartparse_work` directory, with Python 3.10+:

```powershell
python -m unittest discover -v
python demo.py --example multiple --mode cgar
python demo.py --example unsupported --mode cgar
python demo.py --example valid --mode original
python phase5g_eval.py --repeats 5
```

The comparative evaluation writes `results/phase5g_cases.csv` and `results/phase5g_summary.csv`. It uses 16 curated cases: 13 syntactically invalid and 3 syntactically valid under the supported grammar. S07 (`int x = 1;;`) is syntactically valid because the extra semicolon is an empty statement, despite a different reference program.

## Observed Windows evaluation (user-run, 27 October 2026)

| Mode | Invalid inputs detected | False alarms on valid inputs | Exact reference matches, only when complete stream available | Median runtime | Peak traced memory |
|---|---:|---:|---:|---:|---:|
| Panic-mode | 13/13 | 0/3 | N/A | 0.0748 ms | 3.32 KiB |
| Original SmartParse | 13/13 | 0/3 | N/A | 0.0965 ms | 3.15 KiB |
| Standalone CGAR advisor | 13/13 | 0/3 | 13/13 available | 0.1898 ms | 4.59 KiB |
| Integrated CGAR | 13/13 | 0/3 | 13/13 available | 0.3319 ms | 6.42 KiB |

The advisor and integrated modes each abstained on **two** cases. The exact-match denominator excludes those abstentions and other cases without complete corrected streams. It is **not** 100% overall repair accuracy. Original SmartParse's local repair log was not reconstructed as a canonical corrected program; its exact-repair result is therefore **N/A**, not zero. The standalone and integrated modes share an advisor and are not independent repair algorithms. Runtime/memory measurements are exploratory, hardware-dependent, and affected by instrumentation.

## Interpretation
On this small curated set, all four modes identified all malformed inputs and did not flag valid inputs. CGAR returned reference-matching suggestions for the cases where a complete correction was produced, with explicit abstentions for unsupported repairs. The extra verification incurs runtime and memory overhead. These experiments do **not** prove superior repair accuracy over the original SmartParse or panic-mode, semantic equivalence, performance scalability, or generalization to full C programs.

## Architecture and key files

- `smartparse.py`: lexer, recursive-descent parser, opt-in integration and fallback
- `recovery.py`: contextual candidate generation and ranking
- `cgar_verified.py`: bounded whole-program grammar-verified repair search
- `cgar_reliable.py`: conservative advisor and abstention policy
- `repair_advisor.py`: separate local repair-advice interface
- `baseline.py`: panic-mode comparator
- `phase5g_eval.py`: four-mode same-case comparative evaluation
- `phase5d_eval.py`: frozen curated examples and references
- `demo.py`: small command-line demonstration
- `test_*.py`: regression and phase-specific tests
- `results/`: generated evaluation artifacts (not independent holdout data)

## Research limitations and future work

1. Restricted grammar, no full C semantics or compiler backend.
2. Punctuation-oriented bounded candidate generation; missing expressions and identifiers can trigger abstention.
3. Whole-program grammar verification can be computationally costly and does not establish intent.
4. Frozen examples overlap development; no independent blind held-out corpus.
5. Detection counts are **not** error-location precision/recall, cascading-error measures, or repair quality.
6. Fair original-vs-CGAR exact-repair evaluation requires reconstruction of the original parser's edit log into corrected token streams.
7. Future studies should add blinded diverse programs, per-error location annotations, more baselines, budget sensitivity, and semantic/AST checks.

## Submission checklist

- [ ] Run the entire unit test suite locally and capture its summary.
- [ ] Run `phase5g_eval.py --repeats 5` locally and save the CSVs.
- [ ] Demonstrate multiple errors, abstention, and valid input with `demo.py`.
- [ ] Cite this release's actual metrics, not conditional accuracy as overall accuracy.
- [ ] Verify no personal files, credentials, or unrelated artifacts are committed.
- [ ] Commit and push to the intended GitHub repository after successful local verification.
