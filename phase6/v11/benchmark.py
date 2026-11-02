"""Reconstructed/synthetic edit benchmark. Ground truth stays in evaluator only.

No human recordings or independent labels are claimed. Snapshot histories are
explicitly permitted engine inputs, never hidden ground-truth candidate seeds.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
from smartparse import Parser, tokenize, LexError
from smartparse_cli.tools import locate
from phase6.v3.execution import bounded_run
from phase6.v3.policy import fixits, point_offset
from .engine import MODES, Config, generate, rank, recover
from .history import replay, reconstruct as history
from .semantics import Validator, projection

ROOT=Path(__file__).resolve().parents[2]


def cases():
    programs=[
        ('ownership','int f(int x){if(x){x++;}return x;}'),
        ('else','int f(int x){if(x){x++;}else{x--;}return x;}'),
        ('while','int f(int x){while(x){x--;}return x;}'),
        ('for','int f(int x){for(int i=0;i<x;i++){x--;}return x;}'),
        ('shadow','int f(int x){int y=0;if(x){int y=1;y++;}return y;}'),
        ('expression','int f(int a,int b,int c){return (a+b)*c;}'),
        ('pointer','int f(int *p){return *p;}'),
        ('multiple','int f(int x){int y=1;return x+y;}'),
    ]
    result=[]
    for name,good in programs:
        if name in ('ownership','else','while','for','shadow'):bad=good.replace('}', '',1)
        elif name=='expression':bad=good.replace(')*', '*',1)
        elif name=='multiple':bad=good.replace(';','',2)
        else:bad=good[:-1]
        for condition in ('verified','missing'):
            result.append(dict(id=name+'-'+condition,provenance='synthetic mutation of authored C microprogram',
                ground_truth=good,source=bad,history=history(good,bad) if condition=='verified' else None))
    # Consistent but misleading: last valid snapshot represented different grouping.
    good=programs[0][1];bad=good.replace('}return','return')
    stale='int f(int x){if(x){x++;return x;}}'
    result.append(dict(id='misleading-valid-snapshot',provenance='synthetic misleading history',ground_truth=good,source=bad,history=history(stale,bad)))
    h=history(good,bad);h['events'][0]['version']=8
    result.append(dict(id='broken-version',provenance='synthetic inconsistent history',ground_truth=good,source=bad,history=h))
    for filename in ('S01.c',):
        path=ROOT/'phase6/v8/fixtures/syntax'/filename
        good=path.read_bytes().decode('utf-8');bad=good.replace(';','',1)
        result.append(dict(id='repository-'+filename,provenance=str(path.relative_to(ROOT))+'; synthetic semicolon deletion',
                           ground_truth=good,source=bad,history=history(good,bad)))
    # Existing full-C fixture is an intentionally unsupported realism control.
    path=ROOT/'phase6/v8/fixtures/c/C12_valid_full.c'
    good=path.read_bytes().decode('utf-8');bad=good.replace(';','',1)
    result.append(dict(id='repository-full-c',provenance=str(path.relative_to(ROOT))+'; synthetic semicolon deletion',
                      ground_truth=good,source=bad,history=history(good,bad)))
    return result


def measure(result,truth,truth_projection):
    valid=[c for c in result['candidates'] if c['validation']['status']=='VALID']
    selected=next((c for c in valid if c['id']==result['recommendation']),None)
    exact=bool(selected and selected['source']==truth)
    wrong=bool(selected and not exact)
    # Structural comparison for evaluation only; never fed back into ranking.
    structural=None
    if selected:
        v=Validator();p=projection(selected['source'],v.inspect(selected['source']))
        if p is not None and truth_projection is not None:structural=p!=truth_projection
    return dict(exact=exact,top3=any(c['source']==truth for c in valid[:3]),wrong=wrong,
                compilable_incorrect=wrong,structural_change=structural,abstained=selected is None,
                coverage=any(c['source']==truth for c in valid),recommended=selected['source'] if selected else None)


def summarize(rows):
    n=len(rows);recommended=sum(not r['abstained'] for r in rows)
    structural=[r for r in rows if r['structural_change'] is not None]
    def metric(key,denominator=n):return dict(numerator=sum(bool(r[key]) for r in rows),denominator=denominator)
    return dict(samples=n,exact_intended_accuracy=metric('exact'),top3_accuracy=metric('top3'),wrong_repair_rate=metric('wrong'),
                compilable_incorrect_rate=metric('compilable_incorrect'),abstention_rate=metric('abstained'),
                accuracy_when_recommended=metric('exact',recommended),candidate_coverage=metric('coverage'),
                structural_change_rate=dict(numerator=sum(r['structural_change'] is True for r in structural),denominator=len(structural)),
                mean_rank_ms=sum(r['rank_ms'] for r in rows)/n)


def compiler_baseline(source, truth, name):
    path=locate(name)
    if not path:return dict(status='unavailable',repair_accuracy_applicable=False)
    try:
        flags=['-fdiagnostics-parseable-fixits']
        start=time.perf_counter()
        p=bounded_run([path,'-x','c','-std=c11','-fsyntax-only',*flags,'-'],input=source.encode(),capture_output=True,shell=False,timeout=3)
        text=p.stderr.decode(errors='replace');repaired=source.encode();found=fixits(p.stderr)
        patches=[]
        for f in found:
            if f['file'] not in ('<stdin>','-'):continue
            patches.append((point_offset(repaired,f['start_line'],f['start_column']),point_offset(repaired,f['end_line'],f['end_column']),f['replacement'].encode()))
        if any(b>c for (a,b,_),(c,d,__) in zip(sorted(patches),sorted(patches)[1:])):patches=[]
        for a,b,value in sorted(patches,reverse=True):repaired=repaired[:a]+value+repaired[b:]
        return dict(status='completed',rejected=p.returncode!=0,diagnostics=text[:4000],
                    repair_accuracy_applicable=bool(patches),exact=bool(patches) and repaired.decode()==truth,
                    fixit_count=len(patches),elapsed_ms=(time.perf_counter()-start)*1000)
    except Exception as error:return dict(status='unavailable',reason=str(error),repair_accuracy_applicable=False)


def run(full_system=False):
    data=cases();modes={m:[] for m in MODES};details=[];system={m:[] for m in MODES}
    for case in data:
        print('Evaluating '+case['id'],flush=True)
        source=case['source'];truth=case['ground_truth'];v=Validator();t=time.perf_counter()
        pool,generation=generate(source,v);generation_ms=(time.perf_counter()-t)*1000
        snapshots,mapping=replay(source,case['history']);reference=None
        for s in reversed(snapshots[:-1]):
            checked=v.inspect(s)
            if checked['status']=='VALID':reference=projection(s,checked);break
        # A separate validator for ground truth prevents accidental cache/input leakage.
        truth_validator=Validator();tv=truth_validator.inspect(truth)
        if tv['status']!='VALID':raise ValueError('Invalid benchmark ground truth: '+case['id'])
        tp=projection(truth,tv);record={k:val for k,val in case.items() if k!='history'}
        record.update(history_condition=case['id'].split('-')[-1],generation=generation,generation_ms=generation_ms,modes={})
        for mode in MODES:
            t=time.perf_counter();result=rank(source,pool,snapshots,reference,mode,mapping=case['history'] is None or bool(snapshots));rank_ms=(time.perf_counter()-t)*1000
            row=measure(result,truth,tp);row['rank_ms']=rank_ms;modes[mode].append(row)
            record['modes'][mode]=dict(**row,decision=result['decision'],reason=result['reason'],
                ordered_sources=[c['source'] for c in result['candidates'] if c['validation']['status']=='VALID'])
            if full_system:
                t=time.perf_counter();actual=recover(source,case['history'],mode);elapsed=(time.perf_counter()-t)*1000
                sr=measure(actual,truth,tp);sr['rank_ms']=elapsed;system[mode].append(sr)
        # Actual old parser plan, rather than describing same-pool ranker as old engine.
        try:
            p=Parser(tokenize(source));p.parse();variant=source
            changes=[]
            for r in p.repairs:
                at=sum(map(len,source.splitlines(keepends=True)[:r['line']-1]))+r['column']-1
                changes.append((at,at if r['operation']=='insert' else at+len(r.get('from','')),
                                '' if r['operation']=='delete' else r['token']))
            for a,b,val in sorted(set(changes),reverse=True):variant=variant[:a]+val+variant[b:]
            checked=Validator().inspect(variant)
            record['old_parser']=dict(exact=variant==truth,source=variant,validation=checked['status'],repair_count=len(changes))
        except (LexError,RecursionError):record['old_parser']=dict(exact=False,validation='UNSUPPORTED')
        record['compilers']={name:compiler_baseline(source,truth,name) for name in ('gcc','clang')}
        details.append(record)
    return dict(schema='smartparse.v11.benchmark',config=asdict(Config()),samples=len(data),
        provenance='20 reconstructed/synthetic cases; 0 recorded human histories; 2 repository-fixture cases; no independent adjudication',
        ranking_only={m:summarize(rows) for m,rows in modes.items()},
        full_system={m:summarize(rows) for m,rows in system.items()} if full_system else None,
        mean_generation_ms=sum(c['generation_ms'] for c in details)/len(details),
        old_parser_exact=dict(numerator=sum(c['old_parser']['exact'] for c in details),denominator=len(details)),cases=details)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='.studio-artifacts/m11/benchmark.json');parser.add_argument('--full-system',action='store_true')
    args=parser.parse_args();result=run(args.full_system);path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))


if __name__=='__main__':main()
