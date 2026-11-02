"""Development calibration, exposed comparison and new family-disjoint evaluation."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import time
from phase6.v13.evaluate import load_cases
from phase6.v13.compiler import Compiler
from phase6.v13.metrics import observation,summarize,rate,label_case,distribution,paired_bootstrap
from phase6.v13.engine import evaluate_input,frozen_engine_hash
from phase6.v13.history import RecoveryInput
from phase6.v13.ingest import sha
from .engine import prepare
from .providers import select_pool
from .policy import Policy,decide

ROOT=Path(__file__).resolve().parent


def fingerprint():
    return sha(''.join(name+(ROOT/name).read_text(encoding='utf-8') for name in ('engine.py','policy.py','providers.py','semantics.py')))


def observe(result,truth):
    obs=observation(result,truth)
    outcome=result.get('outcome','recommended repair' if result['recommendation'] else 'abstention')
    obs.update(outcome=outcome,abstained=outcome=='abstention',suggested_alternatives=outcome=='suggested alternatives',
        unverified_suggestion_count=len(result.get('unverified_suggestions',[])),blocked_candidate_count=len(result.get('blocked_repairs',[])),
        nonrecommendation=result['recommendation'] is None,decision_mode=result.get('decision_mode','legacy'),provider=None,
        candidate_ids=[c['id'] for c in result['candidates']],selected_sha256=None)
    if result['recommendation']:
        c=next(c for c in result['candidates'] if c['id']==result['recommendation'])
        obs['provider']='both' if len(c.get('origins',[]))>1 else c.get('origin','legacy')
        obs['selected_sha256']=sha(c['source'])
    return obs


def totals(rows):
    base=summarize(rows);n=len(rows)
    base['suggested_alternatives']=rate(sum(r['suggested_alternatives'] for r in rows),n)
    base['nonrecommendation']=rate(sum(r['nonrecommendation'] for r in rows),n)
    base['modes']=dict(Counter(r['decision_mode'] for r in rows))
    base['attribution']=dict(Counter(r['provider'] for r in rows if r['recommended']))
    base['unverified_suggestions']=sum(r['unverified_suggestion_count'] for r in rows)
    base['blocked_candidates']=sum(r['blocked_candidate_count'] for r in rows)
    return base


def simple_fallback(result):
    # Research comparator only: deliberately has no adaptive safety/evidence gates.
    candidates=sorted(result['candidates'],key=lambda c:(c['validation']['status']!='VALID',-c['heuristic'],c['id']))
    valid=[c for c in candidates if c['validation']['status']=='VALID']
    return dict(candidates=candidates,recommendation=valid[0]['id'] if valid else None,decision='recommended repair' if valid else 'abstention',reason='Simple highest-heuristic compiler-valid fallback; benchmark comparator, not a Studio policy')


def run(split,max_hunks):
    cases,_=load_cases('.studio-artifacts/m14/prepared','phase6/v14/sample-manifest.json')
    data=[c for c in cases if c['split']==split];rows=[];private=[]
    tools={n:Compiler(n) for n in ('gcc','clang')};before=fingerprint();old_hash=frozen_engine_hash()
    for i,case in enumerate(data):
        print(f'{split} {i+1}/{len(data)} {case["id"]}',flush=True)
        source=case['source'];old=evaluate_input(RecoveryInput(source))
        pool,snapshots,reliability,usage=prepare(source)
        results={f'v13-{m}':old['modes'][m] for m in ('existing','full')}
        for provider in ('custom','compiler','combined'):
            results['adaptive-'+provider]=decide(source,select_pool(pool,provider),snapshots,reliability,Policy(max_edit_hunks=max_hunks))
        results['without-semantic']=decide(source,pool,snapshots,reliability,Policy(max_edit_hunks=max_hunks),use_semantic=False)
        results['without-history']=decide(source,pool,snapshots,reliability,Policy(max_edit_hunks=max_hunks),use_history=False)
        results['simple-fallback']=simple_fallback(results['adaptive-combined'])
        calibration={str(h):decide(source,pool,snapshots,reliability,Policy(max_edit_hunks=h)) for h in (1,2)} if split=='development' else {}
        originals={n:t.check(source) for n,t in tools.items()}
        # Future correction first enters evaluator here, after both engines finished.
        references={n:t.check(case['reference']) for n,t in tools.items()}
        category,why=label_case(originals,references)
        row={k:case[k] for k in ('id','family','split','source_sha256','reference_sha256','provenance','lines','token_count')}
        row.update(category=category,category_reason=why,history='none',systems={name:observe(r,case['reference']) for name,r in results.items()},
            calibration={h:observe(r,case['reference']) for h,r in calibration.items()},
            elapsed_ms=dict(v13=old['elapsed_ms'],adaptive=usage['elapsed_seconds']*1000),
            compiler_invocations=usage['compiler_invocations'],generation=usage['generation'],
            semantic_states=dict(Counter(c['semantic_risk']['status'] for c in pool)),
            candidate_attribution=dict(Counter(c['origin'] for c in pool)))
        rows.append(row);private.append(dict(id=case['id'],results=results,reference_validation=references))
    if fingerprint()!=before or frozen_engine_hash()!=old_hash:raise ValueError('Engine changed during experiment')
    primary=[r for r in rows if r['category']=='A'];names=rows[0]['systems']
    result=dict(split=split,selected=len(rows),category_counts=dict(Counter(r['category'] for r in rows)),primary_A=len(primary),
        algorithm_fingerprint=before,frozen_v13_engine_hash=old_hash,policy=asdict(Policy(max_edit_hunks=max_hunks)),
        compiler_profiles={n:t.identity for n,t in tools.items()},
        systems={name:totals([r['systems'][name] for r in primary]) for name in names},
        calibration={h:totals([r['calibration'][h] for r in primary]) for h in ('1','2')} if split=='development' else {},
        runtime_ms={v:distribution([r['elapsed_ms'][v] for r in primary]) for v in ('v13','adaptive')},
        paired={name:paired_bootstrap(primary,name,'adaptive-combined') for name in ('v13-existing','v13-full','simple-fallback')},
        cases=rows)
    return result,private


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',required=True,choices=('development','exposed','independent'));p.add_argument('--output',required=True)
    p.add_argument('--selection',default='phase6/v14/selection.json');a=p.parse_args();path=Path(a.selection);max_hunks=1
    if a.split!='development':
        selection=json.loads(path.read_text(encoding='utf-8'))
        if selection['algorithm_fingerprint']!=fingerprint():raise ValueError('Algorithm changed since development calibration')
        max_hunks=selection['max_edit_hunks']
    result,private=run(a.split,max_hunks)
    if a.split=='development':
        chosen=min((1,2),key=lambda h:(result['calibration'][str(h)]['wrong']['numerator'],-result['calibration'][str(h)]['exact']['numerator'],h))
        path.write_text(json.dumps(dict(max_edit_hunks=chosen,algorithm_fingerprint=fingerprint(),development_primary=result['primary_A'],
             rule='minimize development exact mismatches, maximize exact recommendations, then smaller hunk cap'),indent=2),encoding='utf-8')
        result['selected_max_edit_hunks']=chosen
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    raw=Path('.studio-artifacts/m14/private');raw.mkdir(parents=True,exist_ok=True)
    (raw/(a.split+'.json')).write_text(json.dumps(private,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','paired','compiler_profiles')},indent=2))


if __name__=='__main__':main()
