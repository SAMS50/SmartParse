# Phase 5E — Conservative repair reliability (experimental)

## Changes
- Added `cgar_reliable.py`, a separate, opt-in advisory layer. It does **not** alter `Parser` or `cgar_verified.plan`.
- Recognizes that `int x = 1;;` already parses because an empty statement is legal. Labels it `ambiguous_valid` rather than silently deleting a semicolon.
- Adds a narrowly scoped declaration-operator candidate for `int x == 1;` -> `int x = 1;`, verified with the strict grammar. It is **not** a general operator-repair engine.
- Abstains from inventing identifier names or expression values.
- `phase5e_eval.py` reruns the same 16 frozen Phase 5D examples and writes `results/phase5e_reliability.csv`.

## Results on frozen curated cases
- Phase 5D: 12/16 exact reference, 1 grammar-valid mismatch, 3 no-plan.
- Phase 5E: 13/16 exact reference, 0 wrong **suggestions**, 2 abstentions, 1 ambiguous-valid case.
- S07 is not a recovered exact match. It is a **valid ambiguous input**; the advisor declines to change it. Therefore the zero-wrong-suggestions figure is achieved partly by explicitly withholding a suggestion.
- These results do not establish general accuracy, superiority to panic mode, or knowledge of programmer intent.

## Commands (PowerShell)
```powershell
python -m unittest discover -v
python phase5d_eval.py --repeats 3 --max-edits 3 --max-nodes 150
python phase5e_eval.py
python -c "from cgar_reliable import advise; a=advise('int x == 1;'); print(a.status, a.result.edits if a.result else None)"
```

## Next steps
Integrate advisor with the main parser only after a fair, common-metric evaluation. Extend beyond narrow punctuation/operator cases with negative tests and held-out examples.
