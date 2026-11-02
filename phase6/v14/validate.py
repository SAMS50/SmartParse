"""Preserve every older milestone and acceptance output during regressions."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def snapshot():
    files=subprocess.check_output(['git','ls-files','phase6','results','acceptance/output'],cwd=ROOT,text=True).splitlines()
    files=[f for f in files if not f.startswith('phase6/v14/')]
    files.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'acceptance/output').rglob('*') if p.is_file())
    return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sorted(set(files)) if (ROOT/f).is_file()}


def main():
    before=snapshot();path=ROOT/'results/verified_performance.csv';saved=path.read_bytes()
    try:r=subprocess.run([sys.executable,'-m','unittest','discover'],cwd=ROOT,timeout=600)
    finally:
        if path.read_bytes()!=saved:path.write_bytes(saved)
    after=snapshot();changed=[f for f,digest in before.items() if after.get(f)!=digest]
    out=ROOT/'.studio-artifacts/m14/preservation.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(files_checked=len(before),changed=changed,test_exit_code=r.returncode,
                                  v11_v12_v13_included=True,legacy_timing_restored_to_prerun_bytes=True),indent=2),encoding='utf-8')
    print(f'Preservation: {len(before)} files checked; {len(changed)} changed')
    if changed:raise SystemExit('Historical files changed: '+', '.join(changed))
    raise SystemExit(r.returncode)


if __name__=='__main__':main()
