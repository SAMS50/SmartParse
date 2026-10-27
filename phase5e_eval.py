"""Evaluate conservative Phase 5E advice on frozen Phase 5D cases."""
import csv
from pathlib import Path
from phase5d_eval import CASES, values
from cgar_reliable import advise


def evaluate():
    rows=[]
    for case in CASES:
        advice=advise(case.broken)
        corrected=(tuple((t.kind,t.value) for t in advice.result.corrected)
                   if advice.result is not None else None)
        exact=corrected == values(case.reference)
        rows.append(dict(case=case.name, category=case.category, status=advice.status,
                         exact_reference=int(exact),
                         wrong_suggestion=int(advice.status=='verified_candidate' and not exact),
                         explanation=advice.explanation))
    return rows


def main():
    rows=evaluate()
    out=Path('results/phase5e_reliability.csv');out.parent.mkdir(exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    for r in rows:
        print(f"{r['case']} {r['category']:23} {r['status']:20} exact={r['exact_reference']}")
    print(f"TOTAL {len(rows)}; exact={sum(r['exact_reference'] for r in rows)}/{len(rows)}; "
          f"wrong_suggestions={sum(r['wrong_suggestion'] for r in rows)}")
    print('Note: valid ambiguous inputs are deliberately not changed; exact-reference rate is not intent accuracy.')
    print('Saved:',out)

if __name__=='__main__': main()
