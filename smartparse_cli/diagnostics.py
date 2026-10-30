"""Normalize and group exact evidence, never infer roots from proximity."""
from collections import Counter
import hashlib
import json

# Presentation taxonomy for existing checker IDs, not new detection rules.
CHECKER_CATEGORIES={
    'core.NullDereference':'memory safety','core.StackAddressEscape':'memory safety',
    'unix.Malloc':'memory safety','unix.MallocSizeof':'memory safety',
    'alpha.security.ArrayBoundV2':'bounds','alpha.unix.cstring.OutOfBounds':'bounds',
    'alpha.unix.Stream':'resource management','alpha.security.MallocOverflow':'bounds',
    'SP6.contradictory_int_conjunction':'program logic','SP6.fixed_buffer_input':'bounds',
}


def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True).encode()).hexdigest()[:20]


def condition(provenance):
    if provenance.get('isolation_conditioned') and provenance.get('repair_conditioned'):return 'repair-and-isolation-conditioned'
    if provenance.get('isolation_conditioned'):return 'isolation-conditioned'
    if provenance.get('repair_conditioned'):return 'repair-conditioned'
    return 'original-source'


def normalize(raw, *, run_id, reference, source_hash, provenance=None, completeness='unknown', suggestion=None):
    provenance=provenance or dict(repair_conditioned=False,isolation_conditioned=False)
    mapped=raw.get('original_location')
    location=mapped if mapped else {k:raw.get(k) for k in ('file','line','column')}
    backend=raw.get('backend') or raw.get('tool',{}).get('id') or run_id
    if isinstance(backend,dict):backend=backend.get('id')
    label={'clang':'Clang','gcc':'GCC','clang-static-analyzer':'Clang Static Analyzer',
           'smartparse-semantic-ast':'SmartParse Semantic AST','smartparse':'SmartParse restricted grammar',
           'panic':'Panic restricted grammar'}.get(backend,backend)
    snippet=raw.get('source_snippet')
    category=raw.get('category') or 'unknown'
    category_basis='backend_category'
    if category=='unknown':
        category=CHECKER_CATEGORIES.get(raw.get('diagnostic_id'),'unknown')
        category_basis='known_checker_identifier' if category!='unknown' else 'unknown'
    return dict(id='D-'+identity([run_id,reference,raw,provenance]),raw_reference=dict(run_id=run_id,path=reference),
        raw_record=raw,location=location,reported_location={k:raw.get(k) for k in ('file','line','column')},
        location_space='mapped-original' if mapped else 'variant-reported; not mapped' if condition(provenance)!='original-source' else 'original-tool-reported',
        source_sha256=source_hash,severity=raw.get('severity'),category=category,category_basis=category_basis,
        message=raw.get('message',''),analyzer=label,backend=backend,diagnostic_id=raw.get('diagnostic_id'),
        suggestion=suggestion,root_id=None,group_id=None,provenance=provenance,conditioning=condition(provenance),
        evidence=dict(source_snippet=snippet,original_range=raw.get('original_range'),physical_range=raw.get('physical_range'),
                      related=raw.get('related',[]),source_mapping=raw.get('coordinate_space','tool-reported; unverified column convention')),
        completeness=completeness,review_status='unreviewed',confirmed_defect=None,
        diagnostic_kind='driver_or_configuration_error' if run_id in ('compiler','static') and raw.get('severity') in ('error','fatal error') and not raw.get('file') else
                        'frontend_blocker' if backend in ('gcc','clang') and raw.get('severity') in ('error','fatal error') else 'diagnostic_evidence',
        context_note=bool(raw.get('context_note') or raw.get('severity')=='note'))


def group(records):
    groups={}
    for record in records:
        # Exact diagnostic + backend + source + snapshot provenance only.
        # Unknown locations and notes stay separate; different tools never merge.
        loc=record['location']
        exact=bool(loc.get('file') and loc.get('line') and loc.get('column') and not record['context_note'])
        key=[record['source_sha256'],record['backend'],loc,record['severity'],record['category'],
             record['diagnostic_id'],record['message'],record['provenance']]
        if not exact:key.append(record['id'])
        gid='G-'+identity(key)
        record['group_id']=gid
        if gid not in groups:
            groups[gid]=dict(id=gid,root_id=None,basis='exact same-backend diagnostic and source/provenance identity' if exact else 'ungrouped context or insufficient location evidence',
                diagnostic_ids=[],analyzers=[],conditioning=record['conditioning'],confirmed_defect=None)
        groups[gid]['diagnostic_ids'].append(record['id'])
        if record['analyzer'] not in groups[gid]['analyzers']:groups[gid]['analyzers'].append(record['analyzer'])
    return list(groups.values())


def summarize(records,groups):
    primary=[d for d in records if not d['context_note']]
    return dict(raw_normalized_records=len(records),errors=sum(d['severity'] in ('error','fatal error') for d in records),
        warnings=sum(d['severity']=='warning' for d in records),notes=sum(d['severity']=='note' for d in records),
        categories=dict(sorted(Counter(d['category'] for d in primary).items())),
        conditioning=dict(sorted(Counter(d['conditioning'] for d in primary).items())),
        evidence_groups=len(groups),confirmed_defect_roots=None,
        limitation='Counts are diagnostics/evidence groups, not independently confirmed defects. No complete coverage or safety claim.')
