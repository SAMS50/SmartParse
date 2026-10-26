"""Compare legacy and contextual scoring on the same labelled cases.

This is a diagnostic-anchor comparison, not a claim of intended-edit accuracy.
"""
import csv
from pathlib import Path
from smartparse import Parser, tokenize
from dataset import DATASET
from metrics import evaluate_diagnostics


def compare(output='results/scoring_comparison.csv'):
    rows = []
    for case in DATASET:
        for mode in ('legacy', 'contextual'):
            parser = Parser(tokenize(case['source']),
                            validate_repairs=False, scoring_mode=mode)
            parser.parse()
            metrics = evaluate_diagnostics(case['errors'], parser.diagnostics)
            rows.append({
                'case': case['id'], 'name': case['name'], 'scoring': mode,
                'tp': metrics['tp'], 'fp': metrics['fp'], 'fn': metrics['fn'],
                'repairs': len(parser.repairs),
                'operations': '|'.join(r['operation'] for r in parser.repairs),
            })
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for mode in ('legacy', 'contextual'):
        subset = [r for r in rows if r['scoring'] == mode]
        print(f"{mode:10} TP={sum(r['tp'] for r in subset)} "
              f"FP={sum(r['fp'] for r in subset)} "
              f"FN={sum(r['fn'] for r in subset)} "
              f"repairs={sum(r['repairs'] for r in subset)}")
    print(f'Saved: {path}')
    print('Diagnostic anchors only; repair-choice correctness requires a separate labelled dataset.')
    return rows


if __name__ == '__main__':
    compare()
