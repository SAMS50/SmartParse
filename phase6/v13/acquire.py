"""Acquire pinned public inputs only; no external code is executed or committed."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

REVISION='0fa71a05a5a4c9bb7c9670e38b05cb2d647dcfd5'
BASE=f'https://raw.githubusercontent.com/umairzahmed/tegcer/{REVISION}/'
SOURCE=dict(name='TEGCER',repository='https://github.com/umairzahmed/tegcer',revision=REVISION,
            archive_url=BASE+'data/input/dataset.zip',license_url=BASE+'LICENSE',readme_url=BASE+'README.md',
            license='GPL-3.0 repository license; external student sources are not redistributed',
            provenance='Maintainer-documented same-student compilation error/correction pairs',
            recorded_edit_events=False,chronological_endpoints=True)


def fetch(url,path,limit,expected=None):
    path=Path(path)
    if path.exists():data=path.read_bytes()
    else:
        request=urllib.request.Request(url,headers={'User-Agent':'SmartParse-research/13'})
        with urllib.request.urlopen(request,timeout=30) as response:data=response.read(limit+1)
        if len(data)>limit:raise ValueError('Download exceeds acquisition bound')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if len(data)>limit:raise ValueError('Cached/downloaded asset exceeds acquisition bound')
    digest=hashlib.sha256(data).hexdigest()
    if expected and digest!=expected:raise ValueError('Acquisition hash mismatch: '+path.name)
    return dict(sha256=digest,bytes=len(data),url=url)


def acquire(directory,lock=None):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    expected=json.loads(Path(lock).read_text(encoding='utf-8')) if lock else {}
    assets={}
    for name,url,limit in (('dataset.zip',SOURCE['archive_url'],16*1024*1024),('LICENSE',SOURCE['license_url'],100000),('README.md',SOURCE['readme_url'],100000)):
        assets[name]=fetch(url,directory/name,limit,expected.get('assets',{}).get(name,{}).get('sha256'))
    license_text=(directory/'LICENSE').read_text(encoding='utf-8')
    if 'GNU GENERAL PUBLIC LICENSE' not in license_text or 'Version 3' not in license_text:raise ValueError('Unexpected license; manual source audit required')
    with zipfile.ZipFile(directory/'dataset.zip') as archive:
        entries=archive.infolist()
        if sum(i.file_size for i in entries)>256*1024*1024:raise ValueError('Expanded archive exceeds limit')
        inventory=[dict(name=i.filename,bytes=i.file_size) for i in entries]
        if any(i.filename.lower().endswith(('license','license.txt','copying')) for i in entries):
            raise ValueError('Additional archive license notice requires audit')
    result=dict(source=SOURCE,assets=assets,archive_inventory=inventory)
    (directory/'acquisition.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',default='.studio-artifacts/m13/raw');p.add_argument('--lock');a=p.parse_args()
    print(json.dumps(acquire(a.directory,a.lock),indent=2))


if __name__=='__main__':main()
