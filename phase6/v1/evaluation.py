"""Review-aware evaluation of stored diagnostics. Never invokes a compiler.

Candidate rules locate admissible evidence; they do not establish a true defect.
Only explicit reviewed matches can establish detection. Contracts and oracle
uncertainty remain independent of whether a matching diagnostic exists.
"""
from collections import Counter
import hashlib
import json
import re

OUTCOMES = ('detected', 'missed', 'blocked', 'unsupported', 'conditional', 'uncertain')
CATEGORIES = ('syntax', 'semantic/type', 'memory safety', 'bounds', 'undefined behavior', 'program logic')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()


def validate_dataset(dataset):
    if dataset['schema_version'] != '1.0' or dataset['dataset_version'] != '1.0.0':
        raise ValueError('unsupported reference version')
    ids = [d['id'] for d in dataset['defects']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate defect ID')
    for defect in dataset['defects']:
        if defect['category'] not in CATEGORIES or defect['oracle_status'] not in ('established', 'conditional', 'uncertain'):
            raise ValueError('invalid category or oracle status')
        if defect['source_id'] not in dataset['sources']:
            raise ValueError('unknown source')
        for key in ('source_locations', 'sink_locations', 'diagnostic_anchors'):
            if not defect[key] or any(type(line) is not int or line < 1 for line in defect[key]):
                raise ValueError('invalid source/sink location')
        if not defect['triggering_conditions'] or not defect['admissible_evidence']['meaning']:
            raise ValueError('missing trigger or evidence meaning')
        if defect['oracle_status']=='conditional' and not defect['required_contracts']:
            raise ValueError('conditional reference requires an explicit contract')
        for rule in defect['admissible_evidence']['rules']:
            for pattern in rule['message_all']:
                re.compile(pattern)
            if not rule['message_all']:
                raise ValueError('empty meaning rule')
        for relation in defect['relationships']:
            if relation['target'] not in ids or relation['target'] == defect['id']:
                raise ValueError('invalid relationship')
    if set(d['historical_entry'] for d in dataset['defects']) != set(range(1, dataset['historical_baseline']['entries'] + 1)):
        raise ValueError('historical lineage is incomplete')


def normalize_runs(dataset, runs):
    """Bind exact reported paths to source hashes; never use basename proximity."""
    evidence, duplicates, coverage = {}, [], {}
    for run in runs:
        for source_id, binding in run['source_bindings'].items():
            if binding['sha256'] != dataset['sources'][source_id]['sha256']:
                raise ValueError('source content differs from reference')
        for item in run['coverage']:
            key = (item['source_id'], item['analysis'])
            if item['status'] not in ('completed', 'blocked', 'unsupported', 'unknown'):
                raise ValueError('invalid coverage status')
            coverage.setdefault(key, []).append(item)
        for path, report in [('compiler', run['report'])] + ([('analyzer', run['report']['static_analysis'])] if 'static_analysis' in run['report'] else []):
            for collection in ('diagnostics', 'findings'):
                for diagnostic in report.get(collection, []):
                    source_ids = [sid for sid, b in run['source_bindings'].items() if diagnostic['file'] in b['reported_paths']]
                    if len(source_ids) > 1:
                        raise ValueError('ambiguous source binding')
                    item = {'run_id': run['id'], 'pass': path, 'collection': collection,
                            'source_id': source_ids[0] if source_ids else None, 'diagnostic': diagnostic}
                    eid = 'E-' + fingerprint(item)[:24]
                    if eid in evidence:
                        duplicates.append(eid)
                    else:
                        evidence[eid] = item
    return evidence, duplicates, coverage


def admissible(defect, evidence):
    d = evidence['diagnostic']
    if d['severity'] == 'note' or evidence['source_id'] != defect['source_id']:
        return False
    if d['line'] not in defect['diagnostic_anchors']:
        return False
    for rule in defect['admissible_evidence']['rules']:
        if d['backend'] not in rule['backends'] or d['severity'] not in rule['severities']:
            continue
        if rule.get('identifiers') and d.get('diagnostic_id') not in rule['identifiers']:
            continue
        if all(re.search(pattern, d['message'], re.I) for pattern in rule['message_all']):
            return True
    return False


def evaluate(dataset, runs, review):
    validate_dataset(dataset)
    scope = {'dataset': fingerprint(dataset), 'runs': fingerprint(runs)}
    if review.get('scope') != scope:
        raise ValueError('review scope does not match dataset/evidence')
    evidence, duplicates, coverage = normalize_runs(dataset, runs)
    defects = {d['id']: d for d in dataset['defects']}
    decisions, adjudications = {}, {}
    for entry in review.get('matches', []):
        pair = (entry['defect_id'], entry['evidence_id'])
        if pair in decisions or pair[0] not in defects or pair[1] not in evidence:
            raise ValueError('duplicate or unknown review target')
        if not entry.get('reviewer') or not entry.get('rationale'):
            raise ValueError('review requires reviewer and rationale')
        if entry['decision'] not in ('match', 'reject', 'ambiguous'):
            raise ValueError('invalid match decision')
        if entry['decision'] == 'match' and not admissible(defects[pair[0]], evidence[pair[1]]):
            defect, item = defects[pair[0]], evidence[pair[1]]
            diagnostic = item['diagnostic']
            override = entry.get('semantic_override', {})
            scoped = (item['source_id']==defect['source_id'] and diagnostic['line'] in defect['diagnostic_anchors']
                      and any(diagnostic['backend'] in rule['backends'] and diagnostic['severity'] in rule['severities']
                              for rule in defect['admissible_evidence']['rules']) and diagnostic['severity']!='note')
            if not (scoped and override.get('claim') and override.get('evidence_explanation')):
                raise ValueError('reviewed match lacks admissible semantic evidence or an explicit scoped semantic override')
        decisions[pair] = entry
    for entry in review.get('adjudications', []):
        eid = entry['evidence_id']
        if eid in adjudications or eid not in evidence or not entry.get('reviewer') or not entry.get('rationale'):
            raise ValueError('invalid finding adjudication')
        if entry['decision'] not in ('false_positive', 'unknown', 'cascade', 'non_defect', 'duplicate'):
            raise ValueError('invalid finding decision')
        if evidence[eid]['diagnostic']['severity'] == 'note' and entry['decision'] == 'false_positive':
            raise ValueError('a context note is not an independent false positive')
        if entry['decision'] == 'false_positive' and not entry.get('finding_group_id'):
            raise ValueError('false positive requires an adjudicated finding group')
        if entry['decision'] == 'duplicate' and (entry.get('duplicate_of') not in evidence or entry['duplicate_of'] == eid):
            raise ValueError('duplicate requires distinct existing evidence target')
        adjudications[eid] = entry
    approved = {}
    for pair, entry in decisions.items():
        if entry['decision'] == 'match':
            if pair[1] in adjudications:
                raise ValueError('finding has conflicting match/adjudication')
            approved.setdefault(pair[1], []).append(pair[0])
    # One diagnostic cannot silently confirm multiple atomic issues.
    if any(len(ids) > 1 for ids in approved.values()):
        raise ValueError('one diagnostic cannot confirm multiple atoms')
    results = []
    for defect in dataset['defects']:
        did = defect['id']
        candidates = [eid for eid, item in evidence.items() if admissible(defect, item) or
                      decisions.get((did,eid),{}).get('decision')=='match']
        matches = [eid for eid in candidates if decisions.get((did, eid), {}).get('decision') == 'match']
        pending = [eid for eid in candidates if eid not in adjudications and
                   decisions.get((did, eid), {}).get('decision') not in ('match', 'reject')]
        contract_reviews = [review.get('contracts', {}).get(c['id'], {}) for c in defect['required_contracts']]
        if any(item and (not item.get('reviewer') or not item.get('rationale')) for item in contract_reviews):
            raise ValueError('contract decision requires reviewer and rationale')
        states = [item.get('state', 'unknown') for item in contract_reviews]
        if any(state not in ('satisfied', 'unknown', 'refuted') for state in states):
            raise ValueError('invalid contract state')
        contract_unknown = any(state != 'satisfied' for state in states)
        statuses = coverage.get((defect['source_id'], defect['required_analysis']), [])
        if defect['oracle_status'] == 'uncertain':
            outcome, reason = 'uncertain', 'Reference intent/precondition remains unresolved; a warning does not resolve it.'
        elif contract_unknown:
            outcome, reason = 'conditional', 'Required contract is unknown or refuted; no unconditional detection claim.'
        elif matches:
            outcome, reason = 'detected', 'Admissible evidence explicitly matched by a named reviewer.'
        elif pending:
            outcome, reason = 'uncertain', 'Meaning-compatible evidence awaits review or was reviewed as ambiguous.'
        elif any(c['status'] == 'completed' for c in statuses):
            outcome, reason = 'missed', 'Declared applicable analysis completed without a reviewed match.'
        elif any(c['status'] == 'blocked' for c in statuses):
            outcome, reason = 'blocked', 'Applicable analysis could not complete; see coverage evidence.'
        elif statuses and all(c['status'] == 'unsupported' for c in statuses):
            outcome, reason = 'unsupported', 'No supported applicable check was enabled.'
        else:
            outcome, reason = 'uncertain', 'Analysis coverage is unknown; absence of output is not a miss.'
        results.append({'defect_id': did, 'category': defect['category'], 'outcome': outcome, 'reason': reason,
                        'oracle_status': defect['oracle_status'],
                        'applicability': 'excluded_by_contract' if 'refuted' in states else 'unresolved_contract' if contract_unknown else 'established',
                        'root_cause_id': defect['root_cause_id'], 'candidates': candidates, 'reviewed_matches': matches,
                        'coverage': statuses, 'contracts': dict(zip((c['id'] for c in defect['required_contracts']), states))})
    findings = []
    for eid, item in evidence.items():
        if item['diagnostic']['severity'] == 'note':
            disposition = 'context_note'
        elif eid in adjudications:
            disposition = adjudications[eid]['decision']
        elif eid in approved:
            disposition = 'reviewed_support'  # May support an uncertain or conditional reference.
        else:
            disposition = 'unknown'
        findings.append({'evidence_id': eid, 'disposition': disposition, 'matched_defects': approved.get(eid, []),
                         'evidence': item, 'adjudication': adjudications.get(eid)})
    def counts(rows):
        c = Counter(r['outcome'] for r in rows)
        return {key: c[key] for key in OUTCOMES}
    detected_roots = sorted({r['root_cause_id'] for r in results if r['outcome'] == 'detected'})
    return {'schema_version': '1.0', 'evaluator_version': '1.0.0', 'dataset_version': dataset['dataset_version'], 'scope': scope,
            'dataset_sources': dataset['sources'], 'reference_review': dataset.get('reference_review','unspecified'),
            'input_manifest': [{key: run[key] for key in ('id','artifact_path','artifact_sha256','source_bindings','coverage') if key in run} for run in runs],
            'historical_baseline': dataset['historical_baseline'], 'defects': results, 'findings': findings,
            'summary': {'atomic_issues': len(results), 'outcomes': counts(results),
                        'categories': {category: counts([r for r in results if r['category'] == category]) for category in CATEGORIES},
                        'detected_root_cause_ids': detected_roots, 'detected_root_cause_count': len(detected_roots),
                        'exact_duplicates_not_counted': len(duplicates),
                        'confirmed_false_positive_group_count': len({a['finding_group_id'] for a in adjudications.values() if a['decision']=='false_positive'}),
                        'finding_dispositions': dict(Counter(f['disposition'] for f in findings))},
            'review': review,
            'metrics': {'precision': None, 'recall': None,
                        'reason': 'Partial non-exhaustive oracle and pending adjudications; do not interpret issue dispositions as precision/recall.'}}
