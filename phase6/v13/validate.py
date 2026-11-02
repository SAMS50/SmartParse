"""Regression runner preserving v11/v12 and older frozen artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def snapshot():
    files=subprocess.check_output(['git','ls-files','phase6','results','acceptance/output'],cwd=ROOT,text=True).splitlines()
    files=[f for f in files if not f.startswith('phase6/v13/')]
    files.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'acceptance/output').rglob('*') if p.is_file())
    return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sorted(set(files)) if (ROOT/f).is_file()}


def main():
    before=snapshot();timing=ROOT/'results/verified_performance.csv';saved=timing.read_bytes()
    try:r=subprocess.run([sys.executable,'-m','unittest','discover'],cwd=ROOT,timeout=600)
    finally:
        if timing.read_bytes()!=saved:timing.write_bytes(saved)
    after=snapshot();changed=[f for f,digest in before.items() if after.get(f)!=digest]
    path=ROOT/'.studio-artifacts/m13/preservation.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(files_checked=len(before),changed=changed,test_exit_code=r.returncode,
                                   v11_v12_included=True,legacy_timing_restored_to_prerun_bytes=True),indent=2),encoding='utf-8')
    print(f'Preservation: {len(before)} files checked; {len(changed)} changed')
    if changed:raise SystemExit('Frozen files changed: '+', '.join(changed))
    raise SystemExit(r.returncode)


if __name__=='__main__':main()
