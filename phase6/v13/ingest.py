"""Deterministic, source-family-disjoint ingestion without target-to-engine leakage."""
from collections import Counter,defaultdict
import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from .acquire import SOURCE

SEED='smartparse-v13-2026-11-03'
TOKEN=re.compile(r'/\*[\s\S]*?\*/|//[^\n]*|(?:u8|u|U|L)?"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||\+\+|--|\S')
KEYWORDS=set('auto break case char const continue default do double else enum extern float for goto if inline int long register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while _Bool _Complex'.split())
HEADERS=set('stdio.h stdlib.h string.h math.h ctype.h limits.h float.h stdint.h stddef.h stdbool.h assert.h errno.h time.h stdarg.h inttypes.h'.split())


def sha(value):return hashlib.sha256(value.encode('utf-8') if isinstance(value,str) else value).hexdigest()


def normalize(source):
    return source.removeprefix('\ufeff').replace('\r\n','\n').replace('\r','\n')


def tokens(source,abstract=False):
    result=[]
    for m in TOKEN.finditer(source):
        t=m.group()
        if t.startswith(('//','/*')):continue
        if abstract:
            if re.fullmatch(r'[A-Za-z_]\w*',t) and t not in KEYWORDS:t='ID'
            elif t[0].isdigit():t='NUM'
            elif '"' in t or t.startswith("'"):t='LITERAL'
        result.append(t)
    return tuple(result)


def simhash(items):
    shingles=set(zip(*(items[i:] for i in range(min(5,len(items)))))) if items else {()}
    totals=[0]*64
    for shingle in shingles:
        value=int(sha('\0'.join(shingle))[:16],16)
        for bit in range(64):totals[bit]+=1 if value>>bit&1 else -1
    return sum((v>=0)<<i for i,v in enumerate(totals))


def privacy_or_safety(source):
    if '\0' in source or len(source)>16384:return 'unsupported size/NUL'
    if re.search(r'BEGIN .*PRIVATE KEY|github_pat_|ghp_[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b(?:roll\s*(?:no|number)|student\s*(?:id|name)|name)\s*[:=]',source,re.I):return 'privacy/credential screen'
    if '\\\n' in source or '%:' in source or '??=' in source or re.search(r'__has_include|_Pragma|__asm__',source):return 'unsupported preprocessing'
    # Comments are removed only for directive verification, never from engine input.
    cleaned=re.sub(r'/\*[\s\S]*?\*/|//[^\n]*',' ',source)
    for line in cleaned.splitlines():
        if not line.lstrip().startswith('#'):continue
        include=re.fullmatch(r'\s*#\s*include\s*<([^>]+)>\s*',line)
        numeric=re.fullmatch(r'\s*#\s*define\s+[A-Za-z_]\w*\s+[-+()0-9. \t]+\s*',line)
        if include and include[1] in HEADERS or numeric:continue
        return 'unsupported include/directive'
    return None


class Families:
    def __init__(self):self.bands=defaultdict(set);self.values=[]
    def group(self,value):
        possible=set()
        for i in range(4):possible.update(self.bands[(i,(value>>(i*16))&65535)])
        matches=[j for j in possible if (self.values[j]^value).bit_count()<=3]
        if matches:return min(matches)
        index=len(self.values);self.values.append(value)
        for i in range(4):self.bands[(i,(value>>(i*16))&65535)].add(index)
        return index


def prior_benchmark_keys():
    from phase6.v11.benchmark import cases as old
    from phase6.v12.dataset import manifest
    return {sha(' '.join(tokens(r['source'],True))) for r in old()+sum(manifest().values(),[])}


def ingest_rows(rows,development=20,final=80,prior_keys=()):
    families=Families();representatives={};seen=set();counts=Counter();prior_keys=set(prior_keys)
    for ordinal,row in enumerate(rows):
        counts['rows_seen']+=1
        if not all(k in row for k in ('sourceText','targetText','sourceTime','targetTime')):raise ValueError('Required provenance/code columns missing')
        original=row['sourceText'];corrected=row['targetText']
        if not isinstance(original,str) or not isinstance(corrected,str):counts['missing_source_or_target']+=1;continue
        source=normalize(original);target=normalize(corrected)
        if source==target:counts['identical_endpoints']+=1;continue
        rejection=privacy_or_safety(source) or privacy_or_safety(target)
        if rejection:counts[rejection]+=1;continue
        try:
            source_time=datetime.fromisoformat(row['sourceTime']);target_time=datetime.fromisoformat(row['targetTime'])
            if source_time>=target_time:counts['nonchronological_endpoints']+=1;continue
        except (ValueError,TypeError):counts['unusable_endpoint_times']+=1;continue
        st=tokens(source,True);tt=tokens(target,True);source_key=sha(' '.join(st));target_key=sha(' '.join(tt))
        if source_key in prior_keys:counts['prior_benchmark_overlap']+=1;continue
        pair=(source_key,target_key)
        if pair in seen:counts['normalized_duplicate_pair']+=1;continue
        seen.add(pair)
        family_index=families.group(simhash(tt))
        identity=sha(sha(source)+sha(target))[:24]
        case=dict(id=identity,source=source,reference=target,raw_source=original,raw_reference=corrected,
            source_sha256=sha(source),reference_sha256=sha(target),raw_source_sha256=sha(original),raw_reference_sha256=sha(corrected),
            canonical_source_sha256=source_key,canonical_reference_sha256=target_key,
            csv_ordinal=ordinal,provenance='TEGCER maintainer-documented human pair; chronology verified from endpoint timestamps',
            dataset='TEGCER',human_written=True,correction_known=True,history_condition='none',history=None,
            chronological_endpoints=True,source_time=source_time.isoformat(),target_time=target_time.isoformat(),
            lines=source.count('\n')+1,token_count=len(tokens(source)))
        old=representatives.get(family_index)
        if old is None or case['id']<old['id']:representatives[family_index]=case
    counts['normalized_unique_pairs']=len(seen);counts['inferred_families']=len(representatives)
    selected=[]
    ranked=sorted(representatives.items(),key=lambda pair:sha(SEED+str(families.values[pair[0]])))
    for rank,(index,case) in enumerate(ranked[:development+final]):
        case['family']=sha('family:'+str(families.values[index]))[:24]
        case['split']='development' if rank<development else 'final';selected.append(case)
    # Prevent near-identical erroneous programs crossing splits too. Keep the
    # earlier sample; do not replace exclusions based on compiler outcomes.
    source_families=Families();source_seen=set();filtered=[]
    for case in selected:
        group=source_families.group(simhash(tokens(case['source'],True)))
        if group in source_seen:counts['near_duplicate_selected_source']+=1;continue
        source_seen.add(group);filtered.append(case)
    counts['selected']=len(filtered)
    return filtered,dict(counts=counts,seed=SEED,requested_development=development,requested_final=final,
                         split_counts=dict(Counter(c['split'] for c in filtered)),source=SOURCE,
                         history='No prior snapshots/events; future corrected endpoints never used as history')


def prepare(raw,output,lock):
    raw=Path(raw);output=Path(output);expected=json.loads(Path(lock).read_text(encoding='utf-8'))
    archive_path=raw/'dataset.zip'
    if sha(archive_path.read_bytes())!=expected['assets']['dataset.zip']['sha256']:raise ValueError('Dataset archive provenance hash mismatch')
    csv.field_size_limit(2*1024*1024)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.namelist()!=['dataset.csv']:raise ValueError('Unexpected archive layout')
        if archive.getinfo('dataset.csv').file_size>256*1024*1024:raise ValueError('Expanded CSV too large')
        with io.TextIOWrapper(archive.open('dataset.csv'),encoding='utf-8-sig',newline='') as stream:
            cases,metadata=ingest_rows(csv.DictReader(stream),prior_keys=prior_benchmark_keys())
    output.mkdir(parents=True,exist_ok=True)
    (output/'cases.json').write_text(json.dumps(cases,ensure_ascii=True,indent=2),encoding='utf-8')
    # Public manifest excludes student source, raw timestamps, submission IDs and diagnostics.
    manifest={**metadata,'cases':[{k:v for k,v in c.items() if k not in ('source','reference','raw_source','raw_reference','source_time','target_time','history')} for c in cases]}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--raw',default='.studio-artifacts/m13/raw');p.add_argument('--output',default='.studio-artifacts/m13/prepared');p.add_argument('--lock',default='phase6/v13/acquisition-lock.json');a=p.parse_args()
    result=prepare(a.raw,a.output,a.lock);print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))


if __name__=='__main__':main()
