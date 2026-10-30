"""Full regression supervision without rewriting earlier acceptance artifacts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from phase6.v3.supervision import run_logged

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:
        started=time.monotonic();r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT)))
        write(OUT/'tests.json',{'run':r.testsRun,'passed':r.testsRun-len(r.failures)-len(r.errors)-len(r.skipped),
                              'failures':len(r.failures),'errors':len(r.errors),'skipped':[{'test':str(t),'reason':s} for t,s in r.skipped],
                              'elapsed_seconds':round(time.monotonic()-started,3)})
        return 0 if r.wasSuccessful() else 1
    protected=json.loads((OUT/'protected_hashes.json').read_text());frozen=json.loads((OUT/'frozen_baseline/hashes.json').read_text())
    assert all(sha(Path(p))==h for p,h in protected.items());assert all(sha(Path(p))==h for p,h in frozen.items())
    csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')};restored=[]
    env=os.environ.copy();env['PATH']=r'C:\android-sdk\ndk\26.3.11579264\toolchains\llvm\prebuilt\windows-x86_64\bin'+os.pathsep+env.get('PATH','')
    try:
        status=run_logged([sys.executable,'-m','phase6.v7.run_validation','--worker'],OUT/'full.txt',timeout=480,env=env,cwd=ROOT)
        write(OUT/'full.supervision.json',status)
        assert not status['timed_out'] and status['exit_code']==0,status
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path))
        changes=[p for p,h in protected.items() if sha(Path(p))!=h];fchanges=[p for p,h in frozen.items() if sha(Path(p))!=h]
        write(OUT/'preservation_full.json',{'protected_files':len(protected),'changed_protected_files':changes,
            'frozen_files':len(frozen),'changed_frozen_files':fchanges,'historical_csvs':len(csvs),'legacy_csv_writes_restored':restored})
        assert not changes and not fchanges
    return 0


if __name__=='__main__':sys.exit(main())
