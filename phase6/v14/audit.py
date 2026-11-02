"""Diagnose the exposed v13 benchmark before changing recovery decisions."""
import argparse
from collections import Counter
import json
from pathlib import Path
from phase6.v11.engine import edits
from phase6.v13.ingest import sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--result',default='.studio-artifacts/m14/v13-reproduced.json');a=p.parse_args()
    reproduced=json.loads(Path(a.result).read_text(encoding='utf-8'))
    historical=json.loads(Path('phase6/v13/results/final.json').read_text(encoding='utf-8'))
    for mode in reproduced['systems']:
        for metric in ('exact','wrong','recommended','abstained','candidate_coverage'):
            assert reproduced['systems'][mode][metric]['numerator']==historical['systems'][mode][metric]['numerator'],(mode,metric)
    private={r['id']:r for r in json.loads(Path('.studio-artifacts/m13/private/final.json').read_text(encoding='utf-8'))}
    cases={r['id']:r for r in json.loads(Path('.studio-artifacts/m13/prepared/cases.json').read_text(encoding='utf-8'))}
    rows=[]
    for r in reproduced['cases']:
        if r['category']!='A':continue
        result=private[r['id']]['engine']['modes']['full'];candidates=result['candidates']
        summaries=[]
        for c in candidates:
            changes=edits(cases[r['id']]['source'],c['source'])
            summaries.append(dict(id=c['id'],source_sha256=sha(c['source']),origin=c.get('origin'),validation=c['validation']['status'],
                score=c['score'],semantic={k:v['status'] for k,v in c['semantic'].items()},
                changes=[dict(line=e['line'],column=e['column'],deleted_length=len(e['deleted']),inserted_length=len(e['inserted']),
                              punctuation_only=set(e['deleted']+e['inserted'])<=set('{}()[];, \t\r\n')) for e in changes]))
        rows.append(dict(id=r['id'],error_category=r['error_category'],candidates=summaries,
            intended_generated=r['systems']['full']['candidate_coverage'],history='none',
            independent_compilation=r['systems']['existing'].get('independent_compilation'),
            reason=r['systems']['full']['reason'],existing_exact=r['systems']['existing']['exact'],
            existing_wrong=r['systems']['existing']['wrong'],
            fallback='Lower-assurance compiler-valid syntax fallback possible; intent not proved' if r['systems']['full']['valid_candidates'] else 'No validated candidate; ranking fallback cannot supply one'))
    root=Path('phase6/v14');(root/'results').mkdir(parents=True,exist_ok=True)
    (root/'results/root-causes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    lines=['# Milestone 14 root-cause analysis','',
      'Completed before implementing the adaptive algorithm. Reproduced frozen v13 final results: 79 primary A cases; existing scoring 20 exact, 4 exact mismatches, 55 abstentions; full scoring 79 abstentions. One additional B case is excluded consistently. This split was exposed in v13 and is historical, not an unseen evaluation set.','',
      '45 pools contain no generated program; 10 contain generated but rejected programs; 24 contain one validated program. All 24 validated inputs retain preprocessing and have seven UNKNOWN historical semantic checks; no preceding histories exist. Full mode confuses unsupported/unavailable structural evidence with a mandatory recommendation gate. No verified structural change was found in these valid pools.','',
      'A lower-assurance syntax fallback is possible on those 24, but compiler acceptance alone does not prove intent: four existing recommendations mismatch the reference (one is token-equivalent). There is no numeric-ranking solution to 55 pools with no valid candidate. Custom lexing rejects common real-C headers/types; supplemental search rejects preprocessing wholesale. Clang hints already enter v12 generation but attribution is only an origin string, not a separately evaluated provider.','',
      'The general changes justified by this diagnosis are explicit evidence availability/risk states, a conservative syntax-only policy, source-mapped compiler candidate bundles, and separate custom/compiler/combined pools. Do not whitelist the twenty known successes or blacklist the four known mismatches. Calibrate only on the v13 development split and test on new family-disjoint cases; label this original split exposed.','',
      '## Complete primary-case ledger','',
      '| Case | Error category | Generated / valid | Intended available | Syntax/compiler validation | Independent compiler check | History | Semantic availability | Abstention reason | Theoretical fallback |',
      '|---|---|---:|---|---|---|---|---|---|---|']
    for r in rows:
        valid=sum(c['validation']=='VALID' for c in r['candidates']);statuses=dict(Counter(c['validation'] for c in r['candidates']))
        lines.append(f"| {r['id']} | {r['error_category']} | {len(r['candidates'])} / {valid} | {r['intended_generated']} | {statuses} | {r['independent_compilation']} | none | {'UNKNOWN (preprocessing unsupported)' if valid else 'no valid AST'} | {r['reason']} | {r['fallback']} |")
    lines+=['','Candidate IDs, origins, score, validation statuses, exact edit locations/lengths and all seven semantic statuses are in `results/root-causes.json`. Student code remains local, not redistributed.','',
       '## Existing exact successes (20)','',', '.join('`'+r['id']+'`' for r in rows if r['existing_exact']), '',
       '## Existing exact mismatches (4)','',', '.join('`'+r['id']+'`' for r in rows if r['existing_wrong']), '',
       'An exact mismatch is not a proven behavioral change. The full policy avoided these four only by withholding twenty exact successes as well. Missing history is unavailable evidence, not evidence against every candidate. Unsupported semantic projection is not a detected structural hazard.','']
    (root/'ROOT_CAUSE_ANALYSIS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Reproduction confirmed and all',len(rows),'primary abstentions diagnosed')


if __name__=='__main__':main()
