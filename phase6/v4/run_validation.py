"""Finite validation stages. All output stays in v4; old artifacts restored."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest

from phase6.v3.supervision import run_logged

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'outputs'


def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def worker():
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
    write('tests.json',{'run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
                        'failures':len(result.failures),'errors':len(result.errors),
                        'skipped':[{'test':str(t),'reason':reason} for t,reason in result.skipped],
                        'elapsed_seconds':round(time.monotonic()-started,3)})
    return 0 if result.wasSuccessful() else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',type=Path);p.add_argument('--stage',choices=('targeted','full','cases'))
    p.add_argument('--suite-worker',action='store_true');a=p.parse_args()
    if a.suite_worker:return worker()
    if not a.compiler or not a.stage:p.error('--compiler and --stage required')
    compiler=a.compiler.resolve(strict=True);env=os.environ.copy();env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
    protected=json.loads((OUT/'protected_hashes.json').read_text())
    def changes():return [name for name,h in protected.items() if sha(Path(name))!=h]
    assert not changes(),changes()
    csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')};restored=[]
    try:
        if a.stage=='targeted':
            from .test_isolation import LiveTests
            commands=[('policy',[sys.executable,'-m','unittest','phase6.v4.test_isolation.PolicyTests','-v'],20)]
            commands += [(name,[sys.executable,'-m','unittest','phase6.v4.test_isolation.LiveTests.'+name,'-v'],35)
                         for name in unittest.defaultTestLoader.getTestCaseNames(LiveTests)]
            results=[]
            for name,cmd,timeout in commands:
                print('Targeted: '+name,flush=True)
                status=run_logged(cmd,OUT/('targeted_'+name+'.txt'),timeout=timeout,env=env,cwd=ROOT)
                results.append(status);write('targeted.json',results)
                if status['timed_out'] or status['exit_code']!=0:raise RuntimeError('Targeted failure: '+name)
        elif a.stage=='full':
            status=run_logged([sys.executable,'-m','phase6.v4.run_validation','--suite-worker'],OUT/'tests.txt',timeout=300,env=env,cwd=ROOT)
            write('suite_supervision.json',status);print(json.dumps(status),flush=True)
            if status['timed_out'] or status['exit_code']!=0:raise RuntimeError('Full regression failed: inspect tests.txt')
        else:
            cases=[('benchmark_unrepaired',ROOT/'acceptance/cleaned/c_error_detection_500_lines.c',[]),
                   ('benchmark_after_v3',ROOT/'acceptance/cleaned/c_error_detection_500_lines.c',['--punctuation-recovery'])]
            cases.extend((p.stem,p,[]) for p in sorted((HERE/'fixtures').glob('*.c')))
            results=[]
            for name,source,extra in cases:
                print('Case: '+name,flush=True);before=source.read_bytes()
                status=run_logged([sys.executable,'-m','phase6.v4',str(source),'--compiler',str(compiler),'--isolate-unaffected','--json',*extra],
                                  OUT/(name+'.json'),timeout=135,env=env,cwd=ROOT)
                write(name+'.supervision.json',status)
                if status['timed_out']:raise RuntimeError('Case timeout: '+name)
                r=json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'));i=r['isolation']
                assert source.read_bytes()==before and r['source']['original_unchanged'] and i['temporary_workspace_removed']
                assert i['usage']['compiler_invocations']<=i['limits']['invocations']
                assert i['usage']['analyzer_invocations']<=i['limits']['analyzer_invocations']
                expected=1 if name in ('independent','dependent') else 0 if name=='valid' else 3
                assert status['exit_code']==expected,(name,status['exit_code'],expected)
                results.append({'case':name,'exit_code':status['exit_code'],'elapsed_seconds':status['elapsed_seconds'],
                                'status':i['status'],'reason':i['reason'],'eligibility_improved':i['eligibility_improved'],
                                'excluded_functions':i['excluded_functions'],'retained_functions':i['retained_functions'],
                                'unique_additional_findings':len(r['unique_additional_findings']),
                                'finding_evidence':[f['evidence'] for f in r['isolation_conditioned_findings']],
                                'compiler_invocations':i['usage']['compiler_invocations'],
                                'analyzer_invocations':i['usage']['analyzer_invocations']})
                write('cases.json',results)
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path))
        state={'protected_files':len(protected),'changed_protected_files':changes(),'historical_csvs':len(csvs),
               'legacy_csv_writes_restored':restored}
        write('preservation_'+a.stage+'.json',state)
        assert not state['changed_protected_files'],state
    return 0


if __name__=='__main__':sys.exit(main())
