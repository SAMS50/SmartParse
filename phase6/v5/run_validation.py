"""Staged, bounded validation. Freeze baseline before configured comparison."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from phase6.v3.supervision import run_logged
from .engine import run_detection,export_v1_run
from .evaluation import evaluate_fixtures,compare

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def fixture_stage(stage,compiler):
    dataset=json.loads((HERE/'reference.json').read_text());cap=None
    frozen=OUT/'frozen_baseline';configured=OUT/'configured'
    target=frozen if stage=='freeze' else configured
    if stage=='freeze' and frozen.exists():raise ValueError('Frozen baseline exists; refusing overwrite')
    if stage=='compare':
        inventory=json.loads((frozen/'hashes.json').read_text())
        assert all(sha(Path(p))==h for p,h in inventory.items()),'frozen baseline/source changed'
    target.mkdir(exist_ok=True);reports={}
    for source in sorted((HERE/'fixtures').glob('*.c')):
        print(stage+': '+source.stem,flush=True)
        report=run_detection(source,enabled=True,profile='baseline' if stage=='freeze' else 'memory',compiler=str(compiler),capability=cap)
        assert report['source']['original_unchanged'] and report['temporary_workspace_removed']
        assert report['status'] not in ('failed','timed_out','budget_exhausted'),report['reason']
        cap=report['capabilities'];reports[source.stem]=report;write(target/(source.stem+'.json'),report)
    result=evaluate_fixtures(dataset,reports);write(target/'evaluation.json',result)
    write(target/'capability_audit.json',cap)
    if stage=='freeze':
        files=[p for p in target.glob('*.json')]+[HERE/'reference.json']+list((HERE/'fixtures').glob('*.c'))
        write(target/'hashes.json',{str(p.resolve()):sha(p) for p in files})
    else:
        baseline=json.loads((frozen/'evaluation.json').read_text());write(OUT/'comparison.json',compare(baseline,result))
        # Conditioned cohort remains separate; never flatten into v1 baseline.
        conditioned=run_detection(HERE/'fixtures/malformed_semantic.c',enabled=True,isolate=True,compiler=str(compiler),capability=cap)
        write(target/'malformed_isolated.json',conditioned)
        assert conditioned['provenance']['isolation_conditioned'],conditioned['upstream']['isolation']['reason']
        assert all(f['provenance']['isolation_conditioned'] for f in conditioned['observations'])
    return 0


def worker():
    started=time.monotonic();r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
    write(OUT/'tests.json',{'run':r.testsRun,'passed':r.testsRun-len(r.failures)-len(r.errors)-len(r.skipped),
                           'failures':len(r.failures),'errors':len(r.errors),'skipped':[{'test':str(t),'reason':s} for t,s in r.skipped],
                           'elapsed_seconds':round(time.monotonic()-started,3)})
    return 0 if r.wasSuccessful() else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=('targeted','freeze','compare','benchmark','full'))
    p.add_argument('--compiler',type=Path);p.add_argument('--worker');a=p.parse_args()
    if a.worker=='full':return worker()
    if a.worker in ('freeze','compare'):return fixture_stage(a.worker,a.compiler)
    if not a.stage or not a.compiler:p.error('--stage and --compiler required')
    compiler=a.compiler.resolve(strict=True);env=os.environ.copy();env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
    protected=json.loads((OUT/'protected_hashes.json').read_text());csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')};restored=[]
    def changed():return [name for name,h in protected.items() if sha(Path(name))!=h]
    assert not changed(),changed()
    try:
        if a.stage=='targeted':
            from .test_detection import LiveTests
            tests=['phase6.v5.test_detection.PolicyTests']+['phase6.v5.test_detection.LiveTests.'+n for n in unittest.defaultTestLoader.getTestCaseNames(LiveTests)]
            statuses=[]
            for name in tests:
                print(name,flush=True)
                status=run_logged([sys.executable,'-m','unittest',name,'-v'],OUT/(name.split('.')[-1]+'.txt'),timeout=45,env=env,cwd=ROOT)
                statuses.append(status);write(OUT/'targeted.json',statuses)
                if status['timed_out'] or status['exit_code']!=0:raise RuntimeError('targeted test failed: '+name)
        elif a.stage in ('freeze','compare','full'):
            timeout=420 if a.stage=='full' else 240
            status=run_logged([sys.executable,'-m','phase6.v5.run_validation','--worker',a.stage,'--compiler',str(compiler)],OUT/(a.stage+'.txt'),timeout=timeout,env=env,cwd=ROOT)
            write(OUT/(a.stage+'.supervision.json'),status)
            if status['timed_out'] or status['exit_code']!=0:raise RuntimeError(a.stage+' failed; inspect log')
        else:
            source=ROOT/'acceptance/cleaned/c_error_detection_500_lines.c'
            statuses=[]
            for name,flags in [('baseline',['--profile','baseline']),('configured',[]),('conditioned',['--punctuation-recovery','--isolate-unaffected'])]:
                cmd=[sys.executable,'-m','phase6.v5',str(source),'--compiler',str(compiler),'--memory-analysis','--json',*flags]
                status=run_logged(cmd,OUT/('benchmark_'+name+'.json'),timeout=135,env=env,cwd=ROOT)
                statuses.append(status);write(OUT/'benchmark_supervision.json',statuses)
                assert not status['timed_out'] and status['exit_code']==3,status
            r=json.loads((OUT/'benchmark_configured.json').read_text())
            from phase6.v1.evaluation import evaluate,fingerprint
            dataset=json.loads((ROOT/'phase6/v1/reference.json').read_text())
            runs=[export_v1_run(r,'sample-500-cleaned')]
            review={'scope':{'dataset':fingerprint(dataset),'runs':fingerprint(runs)},'matches':[],'adjudications':[],'contracts':{}}
            write(OUT/'benchmark_v1_unreviewed.json',evaluate(dataset,runs,review))
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path))
        state={'protected_files':len(protected),'changed_protected_files':changed(),'historical_csvs':len(csvs),'legacy_csv_writes_restored':restored}
        write(OUT/('preservation_'+a.stage+'.json'),state);assert not state['changed_protected_files'],state
    return 0


if __name__=='__main__':sys.exit(main())
