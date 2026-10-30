"""Run all tests while preserving every pre-Phase-6 artifact byte-for-byte.

python -m phase6.v1.run_tests --compiler PATH_TO_CLANG
Only new files under phase6/v1/outputs are written, apart from finally restoring
legacy CSV writes made by original tests. No historical report is regenerated.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--compiler',type=Path,help='optional installed Clang; PATH changes only in this process')
    args=parser.parse_args()
    if args.compiler:
        compiler=args.compiler.resolve(strict=True)
        os.environ['PATH']=str(compiler.parent)+os.pathsep+os.environ.get('PATH','')
    snapshot=json.loads((HERE/'outputs/preimplementation_hashes.json').read_text(encoding='utf-8'))
    def changed():
        return [name for name,sha in snapshot.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=sha]
    if changed(): raise RuntimeError('Preexisting artifact changed before tests: '+repr(changed()))
    csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')}
    restored=[]
    try:
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):
            suite=unittest.defaultTestLoader.discover(str(ROOT))
            result=unittest.TextTestRunner(verbosity=2).run(suite)
        (HERE/'outputs/tests.txt').write_text(capture.getvalue(),encoding='utf-8')
        stats={'run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
               'failures':len(result.failures),'errors':len(result.errors),
               'skipped':[{'test':str(test),'reason':reason} for test,reason in result.skipped]}
        (HERE/'outputs/tests.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:
                path.write_bytes(data); restored.append(str(path))
        preservation={'protected_existing_files':len(snapshot),'changed_existing_files':changed(),
                      'historical_csv_count':len(csvs),'legacy_csv_writes_restored':restored,
                      'scope':'All readable preexisting workspace files except git metadata/caches; external original sample included.'}
        (HERE/'outputs/preservation.json').write_text(json.dumps(preservation,indent=2)+'\n',encoding='utf-8')
        if preservation['changed_existing_files']: raise RuntimeError('Existing artifacts changed: '+repr(changed()))
    print(json.dumps({'tests':stats,'preservation':preservation},indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__': sys.exit(main())
