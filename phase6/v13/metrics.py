"""Exact text, token agreement, compilation and behavior are separate endpoints."""
from collections import Counter
import math
import random
import statistics
from .ingest import tokens


def label_case(source_checks,reference_checks):
    compatible=[name for name,r in source_checks.items() if r.get('status')=='completed' and r.get('accepted') is False and not r.get('environment_failure')]
    if any(reference_checks[n].get('status')=='completed' and reference_checks[n].get('accepted') is True for n in compatible):return 'A','human pair, broken source and compiling correction verified on the same compiler'
    if compatible:return 'B','human error but no locally compatible verified correction'
    if any(r.get('accepted') is True for r in source_checks.values()):return 'D','no reproducible current compilation rejection on a compatible compiler'
    return 'D','unsupported environment, unavailable compiler or failed validation'


def observation(result,reference):
    valid=[c for c in result['candidates'] if c['validation']['status']=='VALID']
    selected=next((c for c in valid if c['id']==result['recommendation']),None)
    exact=selected is not None and selected['source']==reference
    token=selected is not None and tokens(selected['source'])==tokens(reference)
    return dict(recommended=selected is not None,exact=exact,token_match=token,
                wrong=selected is not None and not exact,abstained=selected is None,
                compilation_success=selected is not None,compilable_incorrect=selected is not None and not exact,
                top3=any(c['source']==reference for c in valid[:3]),token_top3=any(tokens(c['source'])==tokens(reference) for c in valid[:3]),
                candidate_coverage=any(c['source']==reference for c in valid),valid_candidates=len(valid),candidates=len(result['candidates']),
                score_margin=valid[0]['score']-valid[1]['score'] if len(valid)>1 else None,
                changed_checks=sum(v['status']=='CHANGED' for v in valid[0]['semantic'].values()) if valid else None,
                unknown_checks=sum(v['status']=='UNKNOWN' for v in valid[0]['semantic'].values()) if valid else None,
                decision=result['decision'],reason=result['reason'],behavioral_equivalence='not assessed')


def wilson(k,n):
    if not n:return None
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,center-half),min(1,center+half)]


def rate(k,n):return dict(numerator=k,denominator=n,estimate=k/n if n else None,wilson95=wilson(k,n))


def summarize(rows):
    n=len(rows);rec=sum(r['recommended'] for r in rows)
    verified=[r for r in rows if r['recommended'] and r['compilation_success'] is not None]
    return {**{key:rate(sum(r[key] for r in rows),n) for key in ('exact','token_match','wrong','abstained','recommended','top3','token_top3','candidate_coverage','compilable_incorrect')},
            'accuracy_when_recommended':rate(sum(r['exact'] for r in rows),rec),
            'compilation_when_recommended':rate(sum(bool(r['compilation_success']) for r in verified),len(verified)),
            'behavioral_equivalence':'not assessed'}


def distribution(values):
    if not values:return dict(n=0,mean=None,median=None,p95=None)
    values=sorted(values)
    return dict(n=len(values),mean=statistics.mean(values),median=statistics.median(values),p95=values[math.ceil(.95*len(values))-1])


def paired_bootstrap(rows,left,right,metric='exact',seed=13003):
    if not rows:return dict(n=0,interval95=None,mean_difference=None)
    # Cases in this study are one per inferred family. Generic grouping also
    # supports future manifests with several records per family.
    groups={}
    for row in rows:groups.setdefault(row['family'],[]).append(row)
    names=sorted(groups);rng=random.Random(seed);values=[]
    for _ in range(2000):
        sample=[r for name in rng.choices(names,k=len(names)) for r in groups[name]]
        values.append(sum(r['systems'][right][metric]-r['systems'][left][metric] for r in sample)/len(sample))
    values.sort()
    differences=[r['systems'][right][metric]-r['systems'][left][metric] for r in rows]
    return dict(n=len(rows),families=len(names),metric=metric,left=left,right=right,mean_difference=statistics.mean(differences),
                interval95=[values[49],values[1949]],right_only=sum(d>0 for d in differences),left_only=sum(d<0 for d in differences),
                method='2000 seeded paired family bootstrap replicates; exploratory, no significance claim')
