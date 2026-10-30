"""Presentation-only source mapping and hash-verified accepted variant previews."""
import hashlib
import re
from phase6.v3.policy import apply_edits
from phase6.v4.policy import mask


def same_file(a,b):
    return bool(a and b) and a.replace('\\','/').casefold()==b.replace('\\','/').casefold()


def editor_locations(report,source):
    locations={};lines=[line.removesuffix('\r') for line in source.split('\n')]
    if re.search(r'^\s*#\s*(?:line\b|\d)',source,re.M):return locations
    for d in report['diagnostics']:
        loc=d['location'];line=loc.get('line');column=loc.get('column')
        if not same_file(loc.get('file'),report['source']['path']) or not isinstance(line,int) or not 1<=line<=len(lines):continue
        if d['location_space'].startswith('variant-reported'):continue
        text=lines[line-1];precision='line';editor_column=1
        if isinstance(column,int) and column>0:
            if d['location_space']=='mapped-original':
                try:
                    prefix=text.encode('utf-8')[:column-1].decode('utf-8')
                    if column<=len(text.encode('utf-8'))+1:
                        editor_column=len(prefix.encode('utf-16-le'))//2+1;precision='column'
                except UnicodeError:pass
            elif text.isascii() and '\t' not in text and column<=len(text)+1:
                editor_column=column;precision='column'
        locations[d['id']]=dict(line=line,column=editor_column,precision=precision,
            reason='Verified byte mapping or unambiguous ASCII column' if precision=='column' else 'Tool column convention unverified; line navigation only')
    return locations


def recovered_previews(report,source):
    original=source.encode('utf-8');previews=[]
    for run in report['runs']:
        variants=(run.get('recovery') or {}).get('accepted_variants',[])
        iso=run.get('isolation') or {};variant=iso.get('variant')
        try:
            data=original;kind=None;expected=None;variant_id=None
            if variants:
                accepted=variants[-1];data=apply_edits(original,accepted['edits'])
                expected=accepted['source_sha256'];kind='repair-conditioned';variant_id=accepted['id']
                if hashlib.sha256(data).hexdigest()!=expected:continue
            if variant and variant.get('status')=='accepted':
                data=mask(data,iso['excluded_functions']);expected=variant['source_sha256']
                kind='repair-and-isolation-conditioned' if variants else 'isolation-conditioned';variant_id=variant['id']
            if kind and expected==hashlib.sha256(data).hexdigest():
                previews.append(dict(run_id=run['id'],variant_id=variant_id,source=data.decode('utf-8'),sha256=expected,
                    conditioning=kind,basis='Reconstructed with existing edit/masking functions; bytes match the actually accepted variant hash. Original not changed.'))
        except (ValueError,KeyError,TypeError,UnicodeError):continue
    return previews
