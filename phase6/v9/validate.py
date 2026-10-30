"""Supervised regression with preserved historical CSV bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from datetime import datetime,timezone
from phase6.v3.supervision import run_logged

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ARCHIVE=HERE/'outputs'
OUT=HERE/'reproducibility/runs'/('validation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+str(os.getpid()))


def write(name,data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def historical_audit():
    """Strict original-workstation audit; never treat absent files as success."""
    hashes=json.loads((ARCHIVE/'protected_hashes.json').read_text())
    changes=[]
    for name,sha in hashes.items():
        if name=='README.md':continue  # Explicitly authorized release documentation update.
        p=ROOT/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:changes.append(name)
    r=dict(protected_files=len(hashes)-1,changed=changes,authorized_changes=['README.md'],
           historical_csvs=sum(p.startswith('results') and p.endswith('.csv') for p in hashes),preserved=not changes)
    r['scope']='historical_original_workstation; not a clean-checkout requirement'
    write('historical_preservation.json',r)
    return r


def preserve():
    from .release import verify
    r=verify(ROOT);write('portable_preservation.json',r)
    return r


def main():
    global OUT
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--label',default='regression')
    p.add_argument('--historical-audit',action='store_true',help='strict original local snapshot; missing local artifacts are failures')
    p.add_argument('--output-dir',type=Path);a=p.parse_args()
    if a.output_dir:OUT=a.output_dir.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    if a.historical_audit:
        r=historical_audit();print(json.dumps(r,indent=2));return 0 if r['preserved'] else 1
    if a.worker:
        start=time.monotonic();suite=unittest.defaultTestLoader.discover(str(ROOT))
        r=unittest.TextTestRunner(verbosity=2).run(suite)
        write(a.worker+'.tests.json',dict(run=r.testsRun,passed=r.testsRun-len(r.failures)-len(r.errors)-len(r.skipped),
             failures=len(r.failures),errors=len(r.errors),skipped=[dict(test=str(t),reason=s) for t,s in r.skipped],
             elapsed_seconds=round(time.monotonic()-start,3)))
        return 0 if r.wasSuccessful() else 1
    before=preserve()
    if not before['preserved']:
        print(json.dumps(before,indent=2));return 1
    from .release import relative,digest
    manifest=json.loads((HERE/'release_manifest.json').read_text())
    exact_before={name:relative(ROOT,name).read_bytes() for name in manifest['files']}
    csvs={p:p.read_bytes() for p in (ROOT/'results').rglob('*.csv')};restored=[]
    env=os.environ.copy()
    # Existing installation, added only to child environment; no PATH installation change.
    from smartparse_cli.tools import locate
    clang=locate('clang')
    if clang:env['PATH']=str(Path(clang).parent)+os.pathsep+env.get('PATH','')
    try:r=run_logged([sys.executable,'-m','phase6.v9.validate','--worker',a.label,'--output-dir',str(OUT)],OUT/(a.label+'.log'),timeout=600,env=env,cwd=ROOT)
    finally:
        for path,data in csvs.items():
            if path.read_bytes()!=data:path.write_bytes(data);restored.append(str(path.relative_to(ROOT)))
    r['legacy_csv_writes_restored']=restored;write(a.label+'.supervisor.json',r)
    preserved=preserve();print(json.dumps(dict(supervisor=r,preservation=preserved),indent=2))
    changed=[name for name,data in exact_before.items() if not relative(ROOT,name).is_file() or relative(ROOT,name).read_bytes()!=data]
    write('exact_before_after.json',dict(scope='actual checkout bytes before/after tests',files=len(exact_before),changed=changed,preserved=not changed))
    return 0 if r['exit_code']==0 and not r['timed_out'] and preserved['preserved'] and not changed else 1


if __name__=='__main__':sys.exit(main())
