"""Bounded regression and case validation, preserving all pre-v3 artifacts.

Run only after run_targeted.py passes. Compiler calls have internal budgets;
the full suite and each CLI case additionally have external process supervision.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest

from .supervision import run_logged
from .validation import validate_report

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'outputs'


def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_worker():
    # Flush progress per test so the last test is identifiable after a timeout.
    class Progress(unittest.TextTestResult):
        def startTest(self,test):super().startTest(test);self.stream.flush()
    started=time.monotonic()
    suite=unittest.defaultTestLoader.discover(str(ROOT))
    result=unittest.TextTestRunner(verbosity=2,resultclass=Progress).run(suite)
    stats={'run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
           'failures':len(result.failures),'errors':len(result.errors),
           'skipped':[{'test':str(t),'reason':r} for t,r in result.skipped],
           'elapsed_seconds':round(time.monotonic()-started,3)}
    write('tests.json',stats)
    return 0 if result.wasSuccessful() else 1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--compiler',type=Path)
    parser.add_argument('--suite-worker',action='store_true')
    args=parser.parse_args()
    if args.suite_worker:return suite_worker()
    if not args.compiler:parser.error('--compiler is required')
    compiler=args.compiler.resolve(strict=True)
    env=os.environ.copy();env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
    protected=json.loads((OUT/'protected_hashes.json').read_text(encoding='utf-8'))
    def changed():return [p for p,h in protected.items() if sha(Path(p))!=h]
    if changed():raise RuntimeError('Protected files already changed: '+repr(changed()))
    csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')}
    fixtures={p:sha(p) for p in (HERE/'fixtures').rglob('*') if p.is_file()}
    restored=[]
    try:
        status=run_logged([sys.executable,'-m','phase6.v3.run_validation','--suite-worker'],OUT/'tests.txt',timeout=240,env=env,cwd=ROOT)
        write('suite_supervision.json',status)
        print('Full regression: '+json.dumps(status),flush=True)
        if status['timed_out'] or status['exit_code']!=0:raise RuntimeError('Regression failed or timed out; inspect tests.txt before continuing')
        cases=[('benchmark_disabled',ROOT/'acceptance/cleaned/c_error_detection_500_lines.c',[],True),
               ('benchmark_repair',ROOT/'acceptance/cleaned/c_error_detection_500_lines.c',['--repair-for-analysis'],True)]
        for name in ('positive_declaration','positive_return','positive_analyzer','positive_two','unicode_crlf',
                     'negative_unbraced','negative_macro','negative_header','negative_expression','negative_semantic','negative_legal'):
            cases.append((name,HERE/'fixtures'/(name+'.c'),['--repair-for-analysis'],name=='positive_analyzer'))
        cases.append(('invocation_budget',HERE/'fixtures/positive_return.c',['--repair-for-analysis','--max-invocations','1'],False))
        summaries=[]
        for name,source,extra,static in cases:
            print('Case '+name,flush=True)
            original=source.read_bytes()
            command=[sys.executable,'-m','phase6.v3',str(source),'--compiler',str(compiler),'--json',*extra]
            if static:command.append('--static-analysis')
            status=run_logged(command,OUT/(name+'.json'),timeout=105,env=env,cwd=ROOT)
            write(name+'.supervision.json',status)
            if status['timed_out']:raise RuntimeError('Case timed out; stopped before further testing: '+name)
            report=json.loads((OUT/(name+'.json')).read_text(encoding='utf-8-sig'))
            validate_report(report,original)
            expected=3 if name in ('benchmark_disabled','benchmark_repair','invocation_budget') else 0 if name=='negative_legal' else 1
            assert status['exit_code']==expected,(name,status['exit_code'],expected)
            assert source.read_bytes()==original
            baseline=report['baseline']
            recovery=report['recovery']
            summaries.append({'case':name,'exit_code':status['exit_code'],'elapsed_seconds':status['elapsed_seconds'],
                'baseline_summary':baseline['analysis']['summary'] if baseline else None,
                'baseline_analysis_sha256':baseline['analysis_sha256'] if baseline else None,
                'candidate_edits':[{'id':c['id'],'line':c['fixit']['start_line'],'column':c['fixit']['start_column'],
                                    'status':c['status'],'reason':c['reason']} for c in recovery['candidates']],
                'accepted_variants':len(recovery['accepted_variants']),
                'final_summary':recovery['accepted_variants'][-1]['eligibility']['analysis']['summary'] if recovery['accepted_variants'] else None,
                'eligibility_change':recovery['eligibility_change'],'stop_reason':recovery['stop_reason'],
                'compiler_invocations':recovery['usage']['compiler_invocations'],'temporary_workspace_removed':recovery['temporary_workspace_removed']})
            write('cases.json',summaries)
        assert summaries[0]['baseline_analysis_sha256']==summaries[1]['baseline_analysis_sha256'],'Opt-in recovery changed immutable baseline diagnostics'
        print(json.dumps(summaries,indent=2),flush=True)
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path))
        preserve={'protected_preexisting_files':len(protected),'changed_preexisting_files':changed(),
                  'historical_csvs':len(csvs),'legacy_csv_writes_restored':restored,
                  'changed_v3_fixture_sources':[str(p) for p,h in fixtures.items() if sha(p)!=h]}
        write('preservation.json',preserve)
        assert not preserve['changed_preexisting_files'] and not preserve['changed_v3_fixture_sources']
    return 0


if __name__=='__main__':sys.exit(main())
