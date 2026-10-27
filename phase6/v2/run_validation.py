"""Preservation-aware full-suite and live eligibility validation.

python -m phase6.v2.run_validation --compiler PATH_TO_CLANG
Writes only phase6/v2 outputs; never regenerates Phase 5 or Phase 6 v1 artifacts.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from .validation import validate_eligibility

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'outputs'


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--compiler',required=True,type=Path)
    args=parser.parse_args()
    compiler=args.compiler.resolve(strict=True)
    os.environ['PATH']=str(compiler.parent)+os.pathsep+os.environ.get('PATH','')
    protected=json.loads((OUT/'protected_hashes.json').read_text(encoding='utf-8'))
    def changes(): return [p for p,h in protected.items() if sha(Path(p))!=h]
    if changes(): raise RuntimeError('Protected files changed before run: '+repr(changes()))
    csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')}
    fixtures={p:sha(p) for p in (HERE/'fixtures').rglob('*') if p.is_file()}
    restored=[]
    try:
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
        (OUT/'tests.txt').write_text(log.getvalue(),encoding='utf-8')
        stats={'run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
               'failures':len(result.failures),'errors':len(result.errors),
               'skipped':[{'test':str(t),'reason':r} for t,r in result.skipped]}
        write('tests.json',stats)
        cases=[]
        definitions=[('benchmark_clang',ROOT/'acceptance/cleaned/c_error_detection_500_lines.c',str(compiler),True,[]),
                     ('benchmark_gcc',ROOT/'acceptance/cleaned/c_error_detection_500_lines.c','gcc',False,[]),
                     ('valid_context',HERE/'fixtures/valid_context.c',str(compiler),True,['--std','c11','-DINITIAL_VALUE=9']),
                     ('preprocessing_failure',HERE/'fixtures/preprocessing_failure.c',str(compiler),True,[]),
                     ('syntax_failure',HERE/'fixtures/syntax_failure.c',str(compiler),True,[]),
                     ('semantic_failure',HERE/'fixtures/semantic_failure.c',str(compiler),True,[]),
                     ('config_blocked',HERE/'fixtures/config_required.c',str(compiler),False,[]),
                     ('config_enabled',HERE/'fixtures/config_required.c',str(compiler),False,['-DENABLE_FEATURE=1']),
                     ('macro_regions',HERE/'fixtures/macro_regions.c',str(compiler),False,[])]
        # Audit only direct Python child processes; never log the environment.
        wrapper='''import json,pathlib,runpy,sys
path=pathlib.Path(sys.argv[1])
def audit(event,args):
    if event=='subprocess.Popen':
        with path.open('a',encoding='utf-8') as f: f.write(json.dumps({'executable':str(args[0]),'arguments':args[1]})+'\\n')
sys.addaudithook(audit)
sys.argv=['phase6.v2']+sys.argv[2:]
runpy.run_module('phase6.v2',run_name='__main__')
'''
        for name,source,driver,static,extra in definitions:
            before=sha(source)
            audit=OUT/(name+'.processes.jsonl'); audit.write_text('',encoding='utf-8')
            command=[sys.executable,'-c',wrapper,str(audit),str(source),'--compiler',driver,'--metadata-timeout','10',*extra]
            if static: command+=['--static-analysis','--analyzer-executable',str(compiler)]
            process=subprocess.run([*command,'--json'],cwd=ROOT,capture_output=True,timeout=120,shell=False)
            report=json.loads(process.stdout)
            validate_eligibility(report)
            write(name+'.json',report)
            text=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=120,shell=False)
            (OUT/(name+'.txt')).write_text(text.stdout.decode('utf-8',errors='replace').replace('\r\n','\n'),encoding='utf-8')
            assert process.returncode==text.returncode and b'Traceback' not in process.stderr+text.stderr
            assert sha(source)==before
            for line in audit.read_text(encoding='utf-8').splitlines():
                argv=json.loads(line)['arguments']
                tokens=argv if isinstance(argv,list) else argv.split()
                assert any(flag in tokens for flag in ('--version','-dumpmachine','-E','-fsyntax-only','--analyze')),argv
                assert '-o' not in tokens or '--analyze' in tokens,argv
            cases.append({'case':name,'exit_code':process.returncode,'compiler':report['stages']['compiler'],
                          'analyzer':report['stages']['analyzer'], 'inventory_status':report['region_inventory']['status'],
                          'function_regions':len(report['regions'])-1,'excluded_definitions':len(report['region_inventory']['exclusions']),
                          'blocker_categories':sorted({b['category'] for b in report['blockers']}),
                          'schema_validated':True,'source_unchanged':True,'direct_process_audit_valid':True})
        write('cases.json',cases)
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data: path.write_bytes(data); restored.append(str(path))
        preservation={'protected_preexisting_files':len(protected),'changed_preexisting_files':changes(),
                      'historical_csv_count':len(csvs),'legacy_test_writes_restored':restored,
                      'changed_new_holdout_sources':[str(p) for p,h in fixtures.items() if sha(p)!=h]}
        write('preservation.json',preservation)
        assert not preservation['changed_preexisting_files'] and not preservation['changed_new_holdout_sources']
    print(json.dumps({'tests':stats,'cases':cases,'preservation':preservation},indent=2))
    assert result.wasSuccessful(), 'Inspect phase6/v2/outputs/tests.txt'


if __name__=='__main__': main()
