"""Extend the pinned family ranking without reusing exposed final families."""
import csv
import io
import json
from pathlib import Path
import zipfile
from phase6.v13.ingest import ingest_rows,prior_benchmark_keys,sha


def prepare():
    old=json.loads(Path('phase6/v13/sample-manifest.json').read_text(encoding='utf-8'))
    lock=json.loads(Path('phase6/v13/acquisition-lock.json').read_text(encoding='utf-8'))
    archive=Path('.studio-artifacts/m13/raw/dataset.zip')
    if sha(archive.read_bytes())!=lock['assets']['dataset.zip']['sha256']:raise ValueError('Pinned archive hash mismatch')
    csv.field_size_limit(2*1024*1024)
    with zipfile.ZipFile(archive) as z:
        with io.TextIOWrapper(z.open('dataset.csv'),encoding='utf-8-sig',newline='') as stream:
            cases,meta=ingest_rows(csv.DictReader(stream),development=20,final=160,prior_keys=prior_benchmark_keys())
    known={r['id']:r for r in old['cases']};found={r['id']:r for r in cases}
    if not set(known)<=found.keys():raise ValueError('Extended sampling did not preserve old sample')
    oldfamilies={r['family'] for r in old['cases']}
    for c in cases:
        c['split']=known[c['id']]['split'] if c['id'] in known else 'independent'
        if c['split']=='final':c['split']='exposed'
        if c['split']=='independent' and c['family'] in oldfamilies:raise ValueError('Exposed family leakage')
    public={**meta,'cases':[{k:v for k,v in c.items() if k not in ('source','reference','raw_source','raw_reference','source_time','target_time','history')} for c in cases]}
    from collections import Counter
    public['split_counts']=dict(Counter(c['split'] for c in cases))
    output=Path('.studio-artifacts/m14/prepared');output.mkdir(parents=True,exist_ok=True)
    (output/'cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps(public,indent=2),encoding='utf-8')
    Path('phase6/v14/sample-manifest.json').write_text(json.dumps(public,indent=2),encoding='utf-8')
    print(public['split_counts'])


if __name__=='__main__':prepare()
