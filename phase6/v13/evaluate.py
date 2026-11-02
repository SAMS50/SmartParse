"""Leakage-separated real-pair evaluation; engines remain immutable."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import time
from .compiler import Compiler
from .engine import evaluate_input,frozen_engine_hash
from .history import build_input
from .ingest import sha,tokens,normalize
from .metrics import observation,summarize,rate,label_case,paired_bootstrap,distribution

ROOT=Path(__file__).resolve().parents[2]


def load_cases(prepared,frozen_manifest):
    prepared=Path(prepared);manifest=json.loads(Path(frozen_manifest).read_text(encoding='utf-8'))
    actual=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'))
    if actual!=manifest:raise ValueError('Prepared manifest differs from frozen provenance/sampling manifest')
    cases=json.loads((prepared/'cases.json').read_text(encoding='utf-8'))
    expected={c['id']:c for c in manifest['cases']}
    if len(cases)!=len(expected):raise ValueError('Case count differs from frozen sample')
    seen=set()
    for c in cases:
        if c['id'] in seen or c['id'] not in expected:raise ValueError('Duplicate or unknown case ID')
        seen.add(c['id']);e=expected[c['id']]
        for key in ('source','reference','raw_source','raw_reference'):
            if sha(c[key])!=e[key+'_sha256']:raise ValueError('Source/reference hash mismatch')
        if normalize(c['raw_source'])!=c['source'] or normalize(c['raw_reference'])!=c['reference']:raise ValueError('Unexpected normalization')
        if any(c[k]!=e[k] for k in ('family','split','csv_ordinal','dataset','human_written','correction_known')):raise ValueError('Provenance metadata mismatch')
        if c.get('history') is not None:raise ValueError('TEGCER endpoints cannot be used as preceding edit history')
    splits=defaultdict(set)
    for c in cases:splits[c['split']].add(c['family'])
    if splits['development']&splits['final']:raise ValueError('Family leakage between splits')
    return cases,manifest


def public_compiler(record):
    original=record['original'];validation=record.get('validation')
    def clean(r):
        if r is None:return None
        return {**{k:r.get(k) for k in ('status','accepted','exit_status','elapsed_ms','resources','environment_failure','fixit_issue')},
                'command':['$COMPILER',*[('<INPUT.C>' if str(a).endswith('input.c') else a) for a in r.get('command',[])[1:]]],
                'diagnostics':[{k:d[k] for k in ('line','column','severity','category')} for d in r.get('diagnostics',[])],
                'diagnostic_categories':dict(Counter(d['category'] for d in r.get('diagnostics',[]))),
                'fixit_count':len(r.get('fixits',[]))}
    return dict(original=clean(original),applicable=record['applicable'],applicability_reason=record['applicability_reason'],
                repaired_sha256=record.get('repaired_sha256'),validation=clean(validation),exact=record['exact'],token_match=record['token_match'])


def run(prepared,manifest_path,split):
    cases,manifest=load_cases(prepared,manifest_path);data=[c for c in cases if c['split']==split]
    if not data:raise ValueError('No cases in requested split')
    before=frozen_engine_hash();tools={n:Compiler(n) for n in ('gcc','clang')};rows=[];private=[]
    for i,case in enumerate(data):
        print(f'{split} {i+1}/{len(data)} {case["id"]}',flush=True)
        # This boundary is called BEFORE any corrected-program compilation. It
        # contains neither target text nor target diagnostics or future history.
        request=build_input(case['source'],case['source_time'])
        t=time.perf_counter()
        try:engine=evaluate_input(request)
        except (RecursionError,ValueError,RuntimeError) as error:
            engine=dict(modes={m:dict(candidates=[],recommendation=None,decision='unsupported repair',reason=type(error).__name__) for m in ('existing','history','semantic','full')},elapsed_ms=(time.perf_counter()-t)*1000,compiler_invocations=0,harness_issue=type(error).__name__)
        original={n:tool.check(case['source']) for n,tool in tools.items()}
        # The reference is first used here, exclusively in the evaluator.
        refs={n:tool.check(case['reference']) for n,tool in tools.items()}
        category,why=label_case(original,refs)
        row={k:case[k] for k in ('id','family','split','dataset','provenance','source_sha256','reference_sha256','lines','token_count')}
        row.update(category=category,category_reason=why,history_condition=request.history_condition,systems={},compilers={},
            engine_elapsed_ms=engine['elapsed_ms'],engine_compiler_invocations=engine['compiler_invocations'],
            resources=engine.get('resources',{}),generation=engine.get('generation'),rank_ms=engine.get('rank_ms',{}),
            reference_compatibility={n:refs[n].get('accepted') for n in tools},
            error_diagnostic_count=max((sum(d['severity'] in ('error','fatal error') for d in r['diagnostics']) for r in original.values()),default=0))
        errors=[d['category'] for r in original.values() for d in r['diagnostics'] if d['severity'] in ('error','fatal error')]
        row['error_category']=Counter(errors).most_common(1)[0][0] if errors else 'no structured rejection'
        selected_cache={}
        for mode,r in engine['modes'].items():
            obs=observation(r,case['reference'])
            if obs['recommended']:
                candidate=next(c for c in r['candidates'] if c['id']==r['recommendation'])
                text=candidate['source'];digest=sha(text)
                if digest not in selected_cache:selected_cache[digest]={n:tool.check(text) for n,tool in tools.items()}
                checks=selected_cache[digest]
                known=[v['accepted'] for v in checks.values() if v.get('status')=='completed']
                obs['compilation_success']=any(known) if known else None
                obs['compilable_incorrect']=obs['compilation_success'] is True and not obs['exact']
                obs['selected_sha256']=digest;obs['independent_compilation']={n:v.get('accepted') for n,v in checks.items()}
            row['systems'][mode]=obs
        baseline_records={}
        for name,tool in tools.items():
            r=tool.repair(case['source'],original[name]);r['exact']=r['applicable'] and r['repaired_source']==case['reference']
            r['token_match']=r['applicable'] and tokens(r['repaired_source'])==tokens(case['reference'])
            baseline_records[name]=r;row['compilers'][name]=public_compiler(r)
        rows.append(row);private.append(dict(id=case['id'],engine=engine,compilers=baseline_records,reference_validation=refs,selected_validation=selected_cache))
    if frozen_engine_hash()!=before:raise ValueError('Frozen recovery implementation changed during evaluation')
    primary=[r for r in rows if r['category']=='A'];systems={m:summarize([r['systems'][m] for r in primary]) for m in ('existing','history','semantic','full')}
    comparisons={n:dict(diagnostic_rejection=rate(sum(r['compilers'][n]['original']['accepted'] is False and not r['compilers'][n]['original']['environment_failure'] for r in primary),sum(r['compilers'][n]['original']['status']=='completed' and not r['compilers'][n]['original']['environment_failure'] for r in primary)),
         applicable_output_coverage=rate(sum(r['compilers'][n]['applicable'] for r in primary),len(primary)),
         exact_over_all_A=rate(sum(r['compilers'][n]['exact'] for r in primary),len(primary)),
         exact_when_applicable=rate(sum(r['compilers'][n]['exact'] for r in primary),sum(r['compilers'][n]['applicable'] for r in primary)),
         token_when_applicable=rate(sum(r['compilers'][n]['token_match'] for r in primary),sum(r['compilers'][n]['applicable'] for r in primary)),
         compile_when_applicable=rate(sum(r['compilers'][n]['validation'] is not None and r['compilers'][n]['validation']['accepted'] is True for r in primary),sum(r['compilers'][n]['applicable'] and r['compilers'][n]['validation']['accepted'] is not None for r in primary)),
         original_runtime_ms=distribution([r['compilers'][n]['original']['elapsed_ms'] for r in primary])) for n in tools}
    paired_rows=[{**r,'systems':{**r['systems'],**{n:{'exact':r['compilers'][n]['exact']} for n in tools}}} for r in primary]
    subgroups={}
    def subgroup(key,fn):
        groups=defaultdict(list)
        for r in primary:groups[str(fn(r))].append(r)
        subgroups[key]={name:dict(n=len(group),systems={m:summarize([r['systems'][m] for r in group]) for m in systems},engine_runtime_ms=distribution([r['engine_elapsed_ms'] for r in group])) for name,group in sorted(groups.items())}
    subgroup('error_category',lambda r:r['error_category']);subgroup('history',lambda r:r['history_condition'])
    subgroup('length',lambda r:'<=20 lines' if r['lines']<=20 else '21-50 lines' if r['lines']<=50 else '>50 lines')
    subgroup('error_diagnostics',lambda r:'one' if r['error_diagnostic_count']==1 else 'multiple diagnostics')
    subgroup('plausible_candidates',lambda r:r['systems']['full']['valid_candidates'])
    subgroup('semantic_unknown',lambda r:r['systems']['full']['unknown_checks'])
    subgroup('compiler_compatibility',lambda r:','.join(n for n,a in r['reference_compatibility'].items() if a))
    curves={}
    for mode in systems:
        curves[mode]={}
        for threshold in (0,12,60,120,240):
            accepted=[r['systems'][mode] for r in primary if r['systems'][mode]['recommended'] and (r['systems'][mode]['score_margin'] is None or r['systems'][mode]['score_margin']>=threshold)]
            curves[mode][str(threshold)]=dict(coverage=rate(len(accepted),len(primary)),accuracy=rate(sum(r['exact'] for r in accepted),len(accepted)))
    result=dict(schema='smartparse.v13.real_world',split=split,selected=len(rows),category_counts=dict(Counter(r['category'] for r in rows)),primary_A=len(primary),
                frozen_engine_hash=before,compiler_identities={n:t.identity for n,t in tools.items()},systems=systems,compiler_comparison=comparisons,
                paired_comparisons={m:paired_bootstrap(primary,'existing',m) for m in ('history','semantic','full')},
                paired_compiler_comparisons={n:paired_bootstrap(paired_rows,n,'full') for n in tools},
                history_beyond_semantic=paired_bootstrap(primary,'semantic','full'),runtime_ms=distribution([r['engine_elapsed_ms'] for r in primary]),
                compiler_invocations=distribution([r['engine_compiler_invocations'] for r in primary]),subgroups=subgroups,
                selective_diagnostic_curves=curves,behavioral_equivalence='not assessed',cases=rows)
    return result,private


def main():
    p=argparse.ArgumentParser();p.add_argument('--prepared',default='.studio-artifacts/m13/prepared');p.add_argument('--manifest',default='phase6/v13/sample-manifest.json')
    p.add_argument('--split',choices=('development','final'),required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result,private=run(a.prepared,a.manifest,a.split);path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    # Private captures include external code/diagnostics and stay under ignored storage.
    raw=ROOT/'.studio-artifacts/m13/private';raw.mkdir(parents=True,exist_ok=True)
    (raw/(a.split+'.json')).write_text(json.dumps(private,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('split','selected','primary_A','category_counts','systems','compiler_comparison','runtime_ms','paired_comparisons')},indent=2))


if __name__=='__main__':main()
