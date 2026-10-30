"""Bounded regression run and byte-preservation checks, without old evaluators."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import unittest
from .prepare import HERE,ROOT,digest,write_json,verify_freeze


def preservation():
    old=json.loads((HERE/'outputs/protected_hashes.json').read_text())
    changed=[];missing=[]
    for name,expected in old.items():
        path=Path(name)
        if not path.is_file():missing.append(name)
        elif digest(path.read_bytes())!=expected:changed.append(name)
    frozen=verify_freeze()
    unique={str(Path(name).resolve()):sha for name,sha in old.items()}
    report=dict(protected_hash_records=len(old),protected_files=len(unique),historical_csvs=sum(Path(p).suffix.lower()=='.csv' for p in unique),
                changed=changed,missing=missing,frozen_inputs_verified=frozen,
                preserved=not changed and not missing)
    write_json(HERE/'outputs/preservation.json',report)
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--full-suite',action='store_true');p.add_argument('--worker',action='store_true');args=p.parse_args()
    if args.worker:
        started=time.monotonic()
        suite=unittest.defaultTestLoader.discover(str(ROOT))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        write_json(HERE/'outputs/tests.json',dict(run=result.testsRun,
            passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
            failures=len(result.failures),errors=len(result.errors),
            skipped=[dict(test=str(t),reason=reason) for t,reason in result.skipped],
            elapsed_seconds=round(time.monotonic()-started,3)))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    if args.full_suite:
        from phase6.v3.supervision import run_logged
        old=json.loads((HERE/'outputs/protected_hashes.json').read_text())
        csvs={Path(name).resolve():Path(name).read_bytes() for name in old if Path(name).suffix.lower()=='.csv'}
        restored=[]
        env=os.environ.copy()
        tools=json.loads((HERE/'configurations.json').read_text())['tools']
        clang=next(t['path'] for t in tools if t['id']=='clang17')
        env['PATH']=str(Path(clang).parent)+os.pathsep+env.get('PATH','')
        for name in ('regression.log','regression.json'):
            original=HERE/'outputs'/name;archive=HERE/'outputs'/('initial_path_limited_'+name)
            if original.exists() and not archive.exists():archive.write_bytes(original.read_bytes())
        try:
            result=run_logged([sys.executable,'-m','phase6.v8.validate','--worker'],HERE/'outputs/regression.log',timeout=600,cwd=ROOT,env=env)
        finally:
            for path,data in csvs.items():
                if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path))
        result['historical_csvs_restored_after_legacy_writer']=restored
        result['child_path_prefix']=str(Path(clang).parent)
        write_json(HERE/'outputs/regression.json',result)
        print(json.dumps(result,indent=2))
    result=preservation();print(json.dumps(result,indent=2))
    if not result['preserved']:raise SystemExit(1)
    if args.full_suite:
        test_status=json.loads((HERE/'outputs/regression.json').read_text())
        if test_status['timed_out'] or test_status['exit_code']!=0:raise SystemExit(1)


if __name__=='__main__':main()
