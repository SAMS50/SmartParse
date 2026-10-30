"""Reproduce enriched comparison exports without rerunning or altering tools."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()))
from phase6.v1.evaluation import fingerprint

out=Path('phase6/v7/outputs');reviews=json.loads((out/'root_review.json').read_text());lookup={}
for decision in reviews['decisions']:
    for i,e in enumerate(decision['evidence']):
        lookup[(decision['tool'],e['case'],e['evidence_hash'])]={'root_id':decision['root_id'],'decision':decision['decision'],
            'reviewer':decision['reviewer'],'same_root_duplicate':i>0}
bench=json.loads((out/'benchmark_source_review.json').read_text());blookup={e['evidence_id']:e for e in bench['reviews']}
summary=json.loads((out/'comparison_summary.json').read_text());old=set(summary['baseline']['established_root_ids']);flat=[]
for p in sorted((out/'comparison').glob('*/*.json')):
    r=json.loads(p.read_text());sid=p.stem;tool=r['tool']
    for d in r['diagnostics']:
        review=lookup.get((tool['id'],sid,fingerprint(d)))
        if sid=='benchmark' and tool['id']=='cppcheck':review=blookup.get(d['id'])
        duplicate='unknown_pending_root_review'
        if review and 'previously_warned_root' in review:
            duplicate={'previously_warned_reference_root':review['previously_warned_root'],
                       'same_root_duplicate_evidence':review.get('same_root_duplicate',False),
                       'scope':'Explicit benchmark source review; conditional/unmatched items do not imply confirmed roots.'}
        elif review and 'root_id' in review:
            duplicate={'root_previously_supported_in_frozen_baseline':review['root_id'] in old,'same_root_duplicate':review.get('same_root_duplicate',False),
                       'scope':'Within this source-reviewed tool cohort versus the independent frozen reference; cross-tool merge uses root_id.'}
        flat.append({**d,'input_id':sid,'tool_name':{'gcc':'GCC Static Analyzer','cppcheck':'Cppcheck','tidy':'Clang-Tidy'}[tool['kind']],
                     'tool_version':tool['version'],'analysis_eligibility':r['eligibility'],'tool_completion':r['status'],
                     'original_file':r['source']['path'] if d['source_bound'] else None,'source_sha256':r['source']['sha256'],
                     'source_review':review,'duplicates_existing':duplicate,'observed_record_fingerprint':fingerprint(d),
                     'independent_human_review_pending':True})
(out/'normalized_findings.json').write_text(json.dumps({'schema':'smartparse.external_findings','schema_version':'1.0','records':flat,'precision':None,'recall':None},indent=2),encoding='utf-8')
selected=old|set(summary['gcc14']['established_root_ids'])|set(summary['cppcheck']['established_root_ids'])
(out/'aggregate_summary.json').write_text(json.dumps({'baseline_roots':len(old),'augmented_roots':len(selected),
    'new_program_root_ids':sorted(selected-old),'new_families':['allocation_extent','late_signed_widen','overlapping_copy'],
    'family_units_note':'One existing allocation root plus three new program variants share the allocation-extent family; source-identical v5/v6 copies are aliases, not extra roots.',
    'benchmark_new_source_supported_roots':bench['new_source_supported_root_ids'],'independent_human_review_pending':True,'precision':None,'recall':None},indent=2),encoding='utf-8')
