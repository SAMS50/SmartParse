"""Bounded stages writing only v6 artifacts, preserving every earlier hash."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from phase6.v3.supervision import run_logged
from .engine import run_semantics
from .evaluation import evaluate_reports
from phase6.v5.engine import DetectionLimits

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def compare(compiler):
    dataset=json.loads((HERE/'reference.json').read_text());baseline={}
    for folder in ('frozen_baseline','frozen_extension'):
        hashes=json.loads((OUT/folder/'hashes.json').read_text());assert all(sha(Path(p))==h for p,h in hashes.items())
        for p in (OUT/folder).glob('*.json'):
            r=json.loads(p.read_text())
            if isinstance(r,dict) and r.get('schema')=='smartparse.memory_analysis':baseline[p.stem]=r
    cap=baseline['valid']['capabilities'];reports={};folder=OUT/'configured';folder.mkdir(exist_ok=True)
    supervision=[]
    for sid in sorted(dataset['sources']):
        print('Compare '+sid,flush=True)
        target=folder/(sid+'.json');r=json.loads(target.read_text()) if target.exists() else None
        reusable=(isinstance(r,dict) and r.get('schema')=='smartparse.semantic_analysis' and r.get('status') in ('completed','blocked')
                  and r['source']['sha256']==dataset['sources'][sid]['sha256'] and r['source']['original_unchanged']
                  and r['temporary_workspace_removed'] and r['upstream']['capabilities']['binding']==cap['binding'])
        if reusable:supervision.append({'case':sid,'reused_verified_result':True,'artifact_sha256':sha(target)})
        else:
            status=run_logged([sys.executable,'-m','phase6.v6.run_validation','--worker','case','--case',sid,'--compiler',str(compiler)],
                              OUT/('case_'+sid+'.txt'),timeout=45,cwd=ROOT)
            supervision.append({'case':sid,**status});write(OUT/'comparison_case_supervision.json',supervision)
            assert not status['timed_out'] and status['exit_code']==0,(sid,status)
            r=json.loads(target.read_text())
        write(OUT/'comparison_case_supervision.json',supervision)
        assert r['status'] in ('completed','blocked'),(sid,r['reason'])
        assert r['source']['original_unchanged'] and r['temporary_workspace_removed']
        reports[sid]=r;write(folder/(sid+'.json'),r)
    before=evaluate_reports(dataset,baseline);after=evaluate_reports(dataset,reports,True)
    write(OUT/'baseline_evaluation.json',before);write(OUT/'configured_evaluation.json',after)
    left=set(before['summary']['detected_root_cause_ids']);right=set(after['summary']['detected_root_cause_ids'])
    review_targets=[{'source':sid,'rule_id':f['evidence']['diagnostic_id'],'already_reported':f['duplicate_of_existing']}
                    for sid,r in reports.items() for f in r['findings'] if f['confidence']=='review_suggestion']
    control_ids=[sid for sid in dataset['sources'] if sid not in {d['source_id'] for d in dataset['defects']}]
    unexpected=[{'source':sid,'finding':f} for sid in control_ids for f in reports[sid]['findings']]
    write(OUT/'comparison.json',{'baseline':before['summary'],'configured':after['summary'],'new_structural_roots':sorted(right-left),
          'lost_roots':sorted(left-right),'review_targets':review_targets,'unexpected_semantic_findings_on_controls':unexpected,
          'precision':None,'recall':None,'review_status':'Agent source review only; conditional targets not counted as detected bugs.'})
    assert not unexpected,unexpected
    # Conditioned cohort stays separate from baseline scoring.
    for name,source,opts in [('isolated',HERE/'fixtures/malformed_semantic.c',{'isolate':True}),
                              ('repaired',ROOT/'phase6/v3/fixtures/positive_analyzer.c',{'repair':True})]:
        r=run_semantics(source,enabled=True,compiler=str(compiler),capability=cap,**opts);write(OUT/(name+'.json'),r)
        assert r['provenance']['isolation_conditioned' if name=='isolated' else 'repair_conditioned']
    return 0


def worker():
    started=time.monotonic();r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
    write(OUT/'tests.json',{'run':r.testsRun,'passed':r.testsRun-len(r.failures)-len(r.errors)-len(r.skipped),
          'failures':len(r.failures),'errors':len(r.errors),'skipped':[{'test':str(t),'reason':s} for t,s in r.skipped],
          'elapsed_seconds':round(time.monotonic()-started,3)})
    return 0 if r.wasSuccessful() else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=('targeted','compare','benchmark','full'));p.add_argument('--compiler',type=Path)
    p.add_argument('--worker',choices=('compare','full','case'));p.add_argument('--case');a=p.parse_args()
    if a.worker=='case':
        dataset=json.loads((HERE/'reference.json').read_text());assert a.case in dataset['sources']
        cap=json.loads((OUT/'frozen_baseline/valid.json').read_text())['capabilities']
        r=run_semantics(HERE/'fixtures'/(a.case+'.c'),enabled=True,compiler=str(a.compiler),capability=cap,
                        limits=DetectionLimits(invocations=96,analyzer_invocations=20,total_seconds=30,call_seconds=5))
        write(OUT/'configured'/(a.case+'.json'),r)
        return 0 if r['status'] in ('completed','blocked') else 1
    if a.worker:return worker() if a.worker=='full' else compare(a.compiler)
    if not a.stage or not a.compiler:p.error('--stage and --compiler required')
    compiler=a.compiler.resolve(strict=True);env=os.environ.copy();env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
    protected=json.loads((OUT/'protected_hashes.json').read_text());csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')};restored=[]
    def changed():return [p for p,h in protected.items() if sha(Path(p))!=h]
    assert not changed(),changed()
    try:
        if a.stage=='targeted':
            from .test_semantics import LiveTests
            names=['phase6.v6.test_semantics.PolicyTests']+['phase6.v6.test_semantics.LiveTests.'+n for n in unittest.defaultTestLoader.getTestCaseNames(LiveTests)]
            results=[]
            for name in names:
                print(name,flush=True);status=run_logged([sys.executable,'-m','unittest',name,'-v'],OUT/(name.split('.')[-1]+'.txt'),timeout=75,env=env,cwd=ROOT)
                results.append(status);write(OUT/'targeted.json',results)
                if status['timed_out'] or status['exit_code']!=0:raise RuntimeError('targeted failure: '+name)
        elif a.stage in ('compare','full'):
            timeout=480 if a.stage=='full' else 240
            status=run_logged([sys.executable,'-m','phase6.v6.run_validation','--worker',a.stage,'--compiler',str(compiler)],OUT/(a.stage+'.txt'),timeout=timeout,env=env,cwd=ROOT)
            write(OUT/(a.stage+'.supervision.json'),status)
            assert not status['timed_out'] and status['exit_code']==0,status
        else:
            source=ROOT/'acceptance/cleaned/c_error_detection_500_lines.c';statuses=[]
            for name,args in [('baseline',[]),('semantic',['--semantic-analysis']),('conditioned',['--semantic-analysis','--punctuation-recovery','--isolate-unaffected'])]:
                status=run_logged([sys.executable,'-m','phase6.v6',str(source),'--compiler',str(compiler),'--json',*args],OUT/('benchmark_'+name+'.json'),timeout=135,env=env,cwd=ROOT)
                statuses.append(status);write(OUT/'benchmark_supervision.json',statuses)
                expected=1 if name=='baseline' else 3
                assert not status['timed_out'] and status['exit_code']==expected,status
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path))
        state={'protected_files':len(protected),'changed_protected_files':changed(),'historical_csvs':len(csvs),'legacy_csv_writes_restored':restored}
        write(OUT/('preservation_'+a.stage+'.json'),state);assert not state['changed_protected_files']
    return 0


if __name__=='__main__':sys.exit(main())
