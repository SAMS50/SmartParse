"""Portable release membership and integrity, separate from historical audits."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/'phase6/v9/release_manifest.json'
LEGACY=('smartparse.py','baseline.py','analyze_c.py')
EXCLUDED={
    'phase6/v8/outputs/interim_summary.txt','phase6/v8/outputs/final_summary.txt',
    'phase6/v9/outputs/README.before.md','phase6/v9/outputs/parser_smoke.json',
    'phase6/v9/reproducibility/original_workspace_hashes.json',
}


def canonical_bytes(data):
    """Only CRLF becomes LF. No whitespace, encoding or token normalization."""
    return data.replace(b'\r\n',b'\n')


def digest(data,policy='exact'):
    if policy=='git-text-lf':data=canonical_bytes(data)
    elif policy!='exact':raise ValueError('Unknown content policy: '+str(policy))
    return hashlib.sha256(data).hexdigest()


def relative(root,name):
    path=PurePosixPath(name.replace('\\','/'))
    if path.is_absolute() or '..' in path.parts or not path.parts or ':' in path.parts[0]:
        raise ValueError('Manifest path must stay relative to the checkout')
    return Path(root).joinpath(*path.parts)


def excluded(name):
    name=name.replace('\\','/')
    return (name in EXCLUDED or '__pycache__' in PurePosixPath(name).parts or
            name.startswith('phase6/v9/reproducibility/runs/') or
            name.startswith('phase6/v8/outputs/extended/') and name.endswith('.log'))


def git(*args,cwd=ROOT):
    return subprocess.run(['git','--no-optional-locks',*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          check=True,timeout=30,shell=False).stdout


def payload(root=ROOT):
    """HEAD-tracked files plus deliberately selected release additions only."""
    tracked={x.decode('utf-8') for x in git('ls-files','-z',cwd=root).split(b'\0') if x}
    selected=set(tracked)
    for name in ('phase6/v8','phase6/v9','smartparse_cli'):
        selected.update(p.relative_to(root).as_posix() for p in (root/name).rglob('*') if p.is_file())
    selected.update(('.gitattributes','test_smartparse_cli.py','test_release_reproducibility.py'))
    return sorted(name for name in selected if not excluded(name))


def policy_for(name,data):
    # Freeze all new v8 evidence and archived v9 reports exactly. Existing older
    # Git text blobs retain their pre-existing checkout normalization semantics.
    if name.startswith(('phase6/v8/','phase6/v9/outputs/','phase6/v9/fixtures/legacy_acceptance/')):return 'exact'
    if name=='acceptance/cleaned/c_error_detection_500_lines.c' or name.startswith(('phase6/v5/fixtures/','phase6/v6/fixtures/','phase6/v7/fixtures/')):
        return 'exact'
    if name=='phase6/v3/fixtures/unicode_crlf.c':return 'exact'
    binary={'.png','.pdf','.jpg','.jpeg','.gif','.ico','.ttf','.woff','.woff2','.zip','.gz','.exe','.dll'}
    return 'exact' if b'\0' in data or Path(name).suffix.lower() in binary else 'git-text-lf'


def build_manifest(root=ROOT):
    names=payload(root);files={}
    self_name='phase6/v9/release_manifest.json'
    for name in names:
        if name==self_name:continue
        path=relative(root,name)
        if not path.is_file():raise ValueError('Required release file missing: '+name)
        data=path.read_bytes();policy=policy_for(name,data)
        files[name]=dict(sha256=digest(data,policy),policy=policy)
    legacy={}
    for name in LEGACY:
        # Bind compatibility to established Git HEAD content, not a newly
        # accepted edit or this Windows checkout's CRLF representation.
        legacy[name]=digest(git('show','HEAD:'+name,cwd=root),'git-text-lf')
        if digest((root/name).read_bytes(),'git-text-lf')!=legacy[name]:
            raise ValueError('Legacy implementation changed: '+name)
    return dict(schema='smartparse.portable_release_manifest',schema_version='1.0',
        self_path=self_name,self_hash='not self-referential; manifest must be present and parseable',
        scope='Intentionally distributed release payload; not the historical workstation snapshot',
        files=files,legacy_compatibility=legacy,
        exclusions=['Untracked legacy acceptance outputs','Empty v8 worker logs','Redundant summaries/backups','Bytecode and new runtime validation outputs'])


def verify(root=ROOT,manifest=None):
    if manifest is None:manifest=json.loads((Path(root)/'phase6/v9/release_manifest.json').read_text(encoding='utf-8'))
    changed=[];missing=[]
    for name,entry in manifest['files'].items():
        path=relative(root,name)
        if not path.is_file():missing.append(name)
        elif digest(path.read_bytes(),entry['policy'])!=entry['sha256']:changed.append(name)
    return dict(scope='portable_release_payload',expected_files=len(manifest['files']),changed=changed,
                missing=missing,preserved=not changed and not missing)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
    if a.build:
        MANIFEST.write_text(json.dumps(build_manifest(),indent=2)+'\n',encoding='utf-8',newline='\n')
        print('Built portable manifest. Historical snapshots were not changed.')
    print(json.dumps(verify(),indent=2))
