"""Development-only margin selection followed by frozen held-out evaluation."""
import argparse
from collections import Counter,defaultdict
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import time
from phase6.v11 import engine as v11
from phase6.v11.history import replay
from phase6.v11.semantics import projection as old_projection, Validator
from phase6.v11.benchmark import cases as historical_cases
from .dataset import manifest
from . import engine as v12
from .history import assess

MARGINS=(0,6,12,24)
ROOT=Path(__file__).resolve().parents[2]


def fingerprint():
    files=['engine.py','candidates.py','history.py','semantics.py','dataset.py']
    return hashlib.sha256(b''.join((Path(__file__).parent/f).read_text(encoding='utf-8').encode('utf-8') for f in files)).hexdigest()


def observation(result,truth,elapsed):
    valid=[c for c in result['candidates'] if c['validation']['status']=='VALID']
    chosen=next((c for c in valid if c['id']==result['recommendation']),None)
    return dict(exact=bool(chosen and chosen['source']==truth),wrong=bool(chosen and chosen['source']!=truth),
        recommended=chosen is not None,top3=any(c['source']==truth for c in valid[:3]),coverage=any(c['source']==truth for c in valid),
        decision=result['decision'],reason=result['reason'],selected_source=chosen['source'] if chosen else None,rank_ms=elapsed,
        margin=valid[0]['score']-valid[1]['score'] if len(valid)>1 else None,
        candidates=[dict(id=c['id'],source=c['source'],syntax=c['validation']['status'],score=c['score'],
                        history=c['history'],semantic={k:v['status'] for k,v in c['semantic'].items()}) for c in result['candidates']])


def summary(rows):
    n=len(rows);rec=sum(r['recommended'] for r in rows)
    def metric(key,den=n):return dict(numerator=sum(r[key] for r in rows),denominator=den)
    return dict(samples=n,exact=metric('exact'),wrong=metric('wrong'),abstained=dict(numerator=n-rec,denominator=n),
                accuracy=metric('exact',rec),recommendation_coverage=dict(numerator=rec,denominator=n),
                top3=metric('top3'),candidate_coverage=metric('coverage'),mean_rank_ms=sum(r['rank_ms'] for r in rows)/n if n else None)


def bootstrap(rows,system):
    groups=defaultdict(list)
    for row in rows:groups[row['family']].append(row['systems'][system])
    names=sorted(groups);rng=random.Random(12003);values=defaultdict(list)
    for _ in range(2000):
        sample=[x for name in rng.choices(names,k=len(names)) for x in groups[name]]
        n=len(sample);rec=sum(r['recommended'] for r in sample)
        values['exact_rate'].append(sum(r['exact'] for r in sample)/n)
        values['wrong_rate'].append(sum(r['wrong'] for r in sample)/n)
        if rec:values['selective_accuracy'].append(sum(r['exact'] for r in sample)/rec)
    zero_errors=not any(r['wrong'] for group in groups.values() for r in group)
    return dict(method='2000 seeded source-family bootstrap samples; exploratory percentile 95% intervals',families=len(names),
                zero_error_family_risk_upper95=1-.05**(1/len(names)) if zero_errors else None,
                intervals={key:[sorted(v)[int(.025*(len(v)-1))],sorted(v)[int(.975*(len(v)-1))]] for key,v in values.items() if v})


def run(split,margin,full_system=False):
    data=historical_cases() if split=='historical' else manifest()[split]
    rows=[]
    for index,case in enumerate(data):
        print(f'{split} {index+1}/{len(data)} {case["id"]}',flush=True)
        source=case['source'];truth=case['ground_truth'];tv=Validator()
        if tv.inspect(truth)['status']!='VALID':raise ValueError('Invalid ground truth: '+case['id'])
        row=dict(id=case['id'],family=case.get('family',case['id'].split('-')[0]),category=case.get('category','historical'),
                 history_condition=case.get('history_condition','historical'),provenance=case['provenance'],source=source,ground_truth=truth,
                 systems={},generation_ms={},generation={},curves={},full_system_ms={})
        for version,engine in (('v11',v11),('v12',v12)):
            v=(Validator if version=='v11' else v12.Validator)(max_calls=34);t=time.perf_counter()
            pool,info=engine.generate(source,v,engine.Config());row['generation_ms'][version]=(time.perf_counter()-t)*1000;row['generation'][version]=info
            if version=='v11':
                snapshots,_=replay(source,case['history']);ref=None
                for s in reversed(snapshots[:-1]):
                    val=v.inspect(s)
                    if val['status']=='VALID':ref=old_projection(s,val);break
                def ranking(mode,m):return v11.rank(source,pool,snapshots,ref,mode,replace(v11.Config(),ambiguity_margin=m),mapping=case['history'] is None or bool(snapshots))
            else:
                snapshots,reliability=assess(source,case['history']);ref=v12.reference_for(snapshots,v)
                row['reliability']=reliability
                def ranking(mode,m):return v12.rank(source,pool,snapshots,ref,reliability,mode,replace(v12.Config(),ambiguity_margin=m))
            for mode in v11.MODES:
                t=time.perf_counter();r=ranking(mode,12 if version=='v11' else margin);elapsed=(time.perf_counter()-t)*1000
                row['systems'][version+'-'+mode]=observation(r,truth,elapsed)
            for m in MARGINS:
                r=ranking('full',m);obs=observation(r,truth,0)
                row['curves'][version+'-'+str(m)]={k:val for k,val in obs.items() if k not in ('candidates','selected_source')}
            if full_system:
                t=time.perf_counter();r=engine.recover(source,case['history'],config=replace(engine.Config(),ambiguity_margin=12 if version=='v11' else margin))
                row['full_system_ms'][version]=(time.perf_counter()-t)*1000
                # Independent full-system validation must agree, or report budget variation.
                obs=observation(r,truth,0)
                row.setdefault('full_system_decisions',{})[version]={k:obs[k] for k in ('exact','wrong','recommended','decision')}
        rows.append(row)
    keys=rows[0]['systems'];curvekeys=rows[0]['curves']
    return dict(split=split,samples=len(rows),families=len({r['family'] for r in rows}),algorithm_fingerprint=fingerprint(),selected_margin=margin,
                systems={k:summary([r['systems'][k] for r in rows]) for k in keys},
                selective_curves={k:summary([r['curves'][k] for r in rows]) for k in curvekeys},
                mean_generation_ms={v:sum(r['generation_ms'][v] for r in rows)/len(rows) for v in ('v11','v12')},
                mean_full_system_ms={v:sum(r['full_system_ms'][v] for r in rows)/len(rows) for v in ('v11','v12')} if full_system else None,
                family_bootstrap={k:bootstrap(rows,k) for k in ('v11-full','v12-full')} if split!='historical' else None,cases=rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=('development','heldout','historical'),required=True)
    p.add_argument('--output',required=True);p.add_argument('--selection',default='.studio-artifacts/m12/selection.json');p.add_argument('--full-system',action='store_true')
    a=p.parse_args();selection=Path(a.selection);margin=12
    if a.split=='heldout':
        chosen=json.loads(selection.read_text(encoding='utf-8'))
        if chosen['algorithm_fingerprint']!=fingerprint():raise ValueError('Algorithm/dataset changed since development selection; held-out evaluation refused')
        margin=chosen['margin']
    result=run(a.split,margin,a.full_system)
    if a.split=='development':
        curves=result['selective_curves']
        # Minimize wrong recommendations first; maximize correct second; prefer default on ties.
        chosen=min(MARGINS,key=lambda m:(curves['v12-'+str(m)]['wrong']['numerator'],-curves['v12-'+str(m)]['exact']['numerator'],abs(m-12)))
        selection.parent.mkdir(parents=True,exist_ok=True)
        selection.write_text(json.dumps(dict(margin=chosen,algorithm_fingerprint=fingerprint(),development_samples=result['samples'],
            rule='minimize development wrong count, maximize correct count, prefer original margin 12 on ties'),indent=2),encoding='utf-8')
        result['development_selected_margin']=chosen
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','selective_curves','family_bootstrap')},indent=2))


if __name__=='__main__':main()
