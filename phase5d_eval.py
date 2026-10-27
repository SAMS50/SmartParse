"""Phase 5D: transparent, deterministic repair-planner reliability evaluation.

Exact match means the corrected token stream equals the supplied reference,
not merely that the strict grammar accepts it. This is a small curated dataset,
not evidence of generalization to real-world C.
"""
import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from time import perf_counter
from smartparse import Parser, StrictParser, tokenize
from cgar_verified import plan, _strict_error

@dataclass(frozen=True)
class Case:
    name: str
    category: str
    broken: str
    reference: str

CASES = (
    Case('S01','missing_semicolon','int x = 1','int x = 1;'),
    Case('S02','wrong_closer','if (x > 1] { x = 2; }','if (x > 1) { x = 2; }'),
    Case('S03','missing_and_wrong','int x = 1 if (x > 0] { x = 2; }','int x = 1; if (x > 0) { x = 2; }'),
    Case('S04','extra_punctuation','if (x > 1 ; ) { x = 2; }','if (x > 1) { x = 2; }'),
    Case('S05','extra_two_punctuation','if (x > 1 ; , ) { x = 2; }','if (x > 1) { x = 2; }'),
    Case('S06','missing_closer','while (x < 3 { x = 2; }','while (x < 3) { x = 2; }'),
    Case('S07','extra_semicolon','int x = 1;;','int x = 1;'),
    Case('S08','missing_block_close','if (x > 1) { x = 2;','if (x > 1) { x = 2; }'),
    Case('S09','valid','int x = 1;','int x = 1;'),
    Case('S10','valid_nested','if (x > 1) { x = 2; }','if (x > 1) { x = 2; }'),
    Case('S11','incomplete_expression','int x = ;','int x = 1;'),
    Case('S12','missing_identifier','int = 1;','int x = 1;'),
    Case('S13','wrong_operator','int x == 1;','int x = 1;'),
    Case('S14','missing_two_semicolons','int x = 1 int y = 2','int x = 1; int y = 2;'),
    Case('S15','wrong_block_closer','if (x > 1) { x = 2; ]','if (x > 1) { x = 2; }'),
    Case('S16','extra_comma','int x = , 1;','int x = 1;'),
)

def values(source):
    return tuple((t.kind,t.value) for t in tokenize(source))

def evaluate(repeats=3, max_edits=3, max_nodes=150):
    if repeats < 1: raise ValueError('repeats must be positive')
    rows=[]
    for case in CASES:
        assert _strict_error(tokenize(case.reference)) is None, case.name
        times=[]; result=None
        for _ in range(repeats):
            start=perf_counter()
            result=plan(case.broken,max_edits=max_edits,max_nodes=max_nodes)
            times.append((perf_counter()-start)*1000)
        original=values(case.broken)
        reference=values(case.reference)
        found=result is not None
        corrected=tuple((t.kind,t.value) for t in result.corrected) if found else None
        exact=corrected==reference
        grammar_valid=bool(found and _strict_error(result.corrected) is None)
        parser=Parser(tokenize(case.broken),validate_repairs=False,scoring_mode='contextual')
        parser.parse()
        rows.append(dict(case=case.name,category=case.category,requires_edit=int(original!=reference),
                         plan_found=int(found),grammar_valid=int(grammar_valid),exact_reference=int(exact),
                         wrong_valid_repair=int(grammar_valid and not exact),
                         abstained=int(not found),edits=len(result.edits) if found else 0,
                         explored=result.explored if found else '',median_ms=round(median(times),4),
                         existing_parser_repairs=len(parser.repairs),existing_parser_diagnostics=len(parser.diagnostics),
                         suggested=repr(result.edits) if found else 'NONE'))
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--max-edits',type=int,default=3);p.add_argument('--max-nodes',type=int,default=150)
    args=p.parse_args()
    rows=evaluate(args.repeats,args.max_edits,args.max_nodes)
    out=Path('results/phase5d_reliability.csv');out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    for r in rows:
        print(f"{r['case']} {r['category']:23} found={r['plan_found']} exact={r['exact_reference']} wrong_valid={r['wrong_valid_repair']} abstain={r['abstained']} ms={r['median_ms']}")
    print(f"TOTAL {len(rows)} cases; exact={sum(r['exact_reference'] for r in rows)}/{len(rows)}; "
          f"wrong_valid={sum(r['wrong_valid_repair'] for r in rows)}; abstained={sum(r['abstained'] for r in rows)}")
    print('Existing parser repair/diagnostic counts are descriptive, NOT directly comparable exact-repair accuracy.')
    print('Saved:',out)
if __name__=='__main__':main()
