"""Hash-bound source-reviewed roots, never warning-count recall."""
import json
import re
from pathlib import Path
from collections import Counter
from phase6.v1.evaluation import fingerprint

HERE=Path(__file__).resolve().parent;OUT=HERE/'outputs'
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def baseline_rows(r):
    rows=list(r['upstream']['analysis']['diagnostics'])
    rows+=(r['upstream']['analysis'].get('static_analysis') or {}).get('findings',[])
    rows+=[f['evidence'] for f in r['findings']]
    return rows


def evaluate():
    inputs=json.loads((HERE/'inputs.json').read_text())['inputs'];reference=json.loads((HERE/'reference.json').read_text())
    reference_hash=fingerprint(reference);catalog=json.loads((HERE/'catalog.json').read_text());cohorts={}
    cohorts['baseline']={sid:json.loads((OUT/'frozen_baseline'/(sid+'.json')).read_text()) for sid in inputs}
    for tool in catalog:cohorts[tool['id']]={sid:json.loads((OUT/'comparison'/tool['id']/(sid+'.json')).read_text()) for sid in inputs}
    results={};reviews=[]
    for name,reports in cohorts.items():
        matches={};duplicates=0
        for unit in reference['units']:
            evidence=[]
            for sid in unit['cases']:
                r=reports[sid];assert r['source']['sha256']==unit['source_sha256']
                rows=baseline_rows(r) if name=='baseline' else r['diagnostics']
                for d in rows:
                    if d['severity'] not in ('warning','error') or d.get('context_note') or d.get('line') not in unit['anchors']:continue
                    if name!='baseline' and not d.get('source_bound'):continue
                    identifier=d.get('diagnostic_id') or ''
                    if any(re.fullmatch(pattern,identifier) for pattern in unit['identifier_patterns']) and re.search(unit['message_pattern'],d['message'],re.I):
                        evidence.append({'case':sid,'diagnostic_id':identifier,'line':d['line'],'message':d['message'],
                                         'evidence_hash':fingerprint(d)})
            if evidence:
                matches[unit['id']]=evidence;duplicates+=max(0,len(evidence)-1)
                reviews.append({'tool':name,'root_id':unit['id'],'source_sha256':unit['source_sha256'],'evidence':evidence,
                                'decision':'conditional_support' if unit['conditional'] else 'agent_source_supported',
                                'reviewer':unit['reviewer'],'rationale':unit['description']+' Source inspection: '+unit['source_rationale'],
                                'independent_human_review_pending':True})
        established={u['id'] for u in reference['units'] if not u['conditional'] and u['id'] in matches}
        conditional={u['id'] for u in reference['units'] if u['conditional'] and u['id'] in matches}
        states=Counter(r['status'] for r in reports.values())
        primary=[];control=[]
        for sid,r in reports.items():
            rows=baseline_rows(r) if name=='baseline' else r['diagnostics']
            for d in rows:
                if d['severity'] not in ('warning','error','fatal error') or d.get('context_note'):continue
                primary.append(d)
                if sid.endswith('_good') or sid=='holdout-unsigned_modular_control':control.append({'case':sid,'diagnostic':d})
        results[name]={'established_root_ids':sorted(established),'conditional_support_ids':sorted(conditional),
                       'reviewed_same_root_duplicate_records':duplicates,'statuses':dict(states),
                       'total_diagnostic_records':sum(len(baseline_rows(r) if name=='baseline' else r['diagnostics']) for r in reports.values()),
                       'primary_diagnostic_groups':len(primary),'corrected_and_modular_control_warnings':control,
                       'invocations':sum(r['usage']['compiler_invocations'] for r in reports.values()),
                       'seconds':round(sum(r['usage']['elapsed_seconds'] for r in reports.values()),3)}
    baseline=set(results['baseline']['established_root_ids'])
    for name,r in results.items():
        roots=set(r['established_root_ids']);r['previous_roots']=sorted(roots&baseline);r['new_roots_vs_baseline']=sorted(roots-baseline)
        r['new_families']=sorted({u['family'] for u in reference['units'] if u['id'] in roots-baseline})
    write(OUT/'root_review.json',{'reference_fingerprint':reference_hash,'reviewer':'Codex-source-review','decisions':reviews,
                                'precision':None,'recall':None,'independent_human_adjudication_pending':True})
    write(OUT/'comparison_summary.json',results)
    return results


if __name__=='__main__':evaluate()
