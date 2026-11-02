"""Reproduce complete v11 per-candidate evidence before implementing changes."""
import argparse
import json
from pathlib import Path
from phase6.v11.benchmark import cases
from phase6.v11.engine import recover, edits


def classify(case,result):
    valid=[c for c in result['candidates'] if c['validation']['status']=='VALID']
    intended=[c for c in result['candidates'] if c['source']==case['ground_truth']]
    chosen=next((c for c in valid if c['id']==result['recommendation']),None)
    if chosen and chosen['source']==case['ground_truth']:return 'Correct recommendation','Yes'
    if chosen:return 'Incorrect history interpretation','No: two intentions fit the observable invalid program; historical validity is not intent'
    if intended and intended[0]['validation']['status']!='VALID':return 'Candidate-validation failure','Unknown until validation succeeds'
    if not intended:return 'Candidate-generation failure','Possibly: inspect missing boundary candidates'
    if case['id']=='broken-version':return 'Unsupported syntax or unavailable evidence','No: invalid source-version chain'
    if any(x['status']=='UNKNOWN' for x in intended[0]['semantic'].values()):
        if case['history'] is None:
            if len(valid)==1:return 'Overly conservative abstention','Potentially: unique supported candidate, without an intent guarantee'
            return 'Correct abstention due to genuine ambiguity','No reliable choice among different valid structures'
        return 'Unsupported syntax or unavailable evidence','Structural coverage gap; no claim of semantic safety'
    return 'Incorrect candidate ranking','Inspect score margin and competing structural evidence'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='.studio-artifacts/m12/failure-details.json');a=p.parse_args()
    rows=[]
    for case in cases():
        print(case['id'],flush=True);r=recover(case['source'],case['history']);failure,recoverable=classify(case,r)
        valid=[c for c in r['candidates'] if c['validation']['status']=='VALID']
        rows.append(dict(**case,result=r,classification=failure,recoverable=recoverable,
                         intended_edits=edits(case['source'],case['ground_truth']),
                         margin=valid[0]['score']-valid[1]['score'] if len(valid)>1 else None))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    md=['# Milestone 11 failure analysis','',
        'Reproduced from frozen v11 code at d261ec3. Complete candidate sources, validation, history features, semantic checks, scores and explanations are in `results/failure-details.json`. No v11 artifact is edited. Categories below are evaluator assessments, not human adjudication.','',
        '| Case / category | Intended edit | Pool / valid / intended generated | Top margin | Outcome | Classification | Recoverable evidence |',
        '|---|---|---|---:|---|---|---|']
    for row in rows:
        r=row['result'];pool=r['candidates'];valid=[c for c in pool if c['validation']['status']=='VALID']
        correction='; '.join(f"{e['line']}:{e['column']} {e['deleted']!r} → {e['inserted']!r}" for e in row['intended_edits'])
        present=any(c['source']==row['ground_truth'] for c in pool)
        md.append(f"| {row['id']} | `{correction}` | {len(pool)} / {len(valid)} / {present} | {row['margin']} | {r['decision']}: {r['reason']} | {row['classification']} | {row['recoverable']} |")
    md+=['','## Root causes and implementation decisions','',
        '* The misleading snapshot replays exactly. Its offsets and versions are valid. It deletes an EOF brace from a program whose return is inside an if block. Restoring it is structurally equal to history but differs from evaluator intent. Lowering history weight alone cannot identify that intention; structural evidence is not independent of the reference. Add a boundary-history ambiguity guard when supported alternatives disagree. Do not assert the history is corrupt.',
        '* Missing histories are mostly justified abstentions: multiple valid block/expression structures remain. A unique supported punctuation repair or unanimous supported candidate structure can provide narrower reference-free evidence; report this basis explicitly, without asserting preservation against an absent AST.',
        '* Pointer syntax misses the intended EOF brace because the custom grammar rejects pointers and Clang supplies no applicable fix-it. Add lexer-aware unmatched delimiter candidates, without importing history into generation. Keep unsupported pointer semantics UNKNOWN.',
        '* Repository S01 has a supported function plus a scalar global. The blanket global rejection prevents otherwise justified structural comparison. Support scalar global declarations and their bindings while retaining UNKNOWN for records, preprocessing and other unsupported constructs.',
        '* Multiple compiler fix-its were applied independently in v11. A bounded, nonoverlapping composite can cover multi-error cases without enumerating arbitrary token combinations.',
        '* AST ownership currently omits expression statements (BinaryOperator/UnaryOperator roots). Add explicit ownership records for those statements. Function-boundary projection stores signatures only; include per-function body inventory. These are identified coverage gaps, not a claim that the historical failure was caused by them.',
        '* No historical case demonstrates that increasing candidate counts or fitting arbitrary weights is justified. Retain the 24-program cap and margin 12 as a candidate setting; evaluate margins on development families only. Keep the original 20 separate from held-out evaluation.','']
    Path('phase6/v12/FAILURE_ANALYSIS.md').write_text('\n'.join(md),encoding='utf-8')


if __name__=='__main__':main()
