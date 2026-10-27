"""Recovery report invariants; no new detector or change to historical scoring."""
import hashlib
import json
from phase6.v2.validation import validate_eligibility
from .policy import apply_edits,source_map


def validate_report(report,original):
    assert report['schema']=='smartparse.repair_for_analysis' and report['schema_version']=='1.0'
    assert hashlib.sha256(original).hexdigest()==report['source']['sha256']
    assert report['source']['original_unchanged'] is True
    recovery=report['recovery'];limits=recovery['limits'];usage=recovery['usage']
    assert usage['compiler_invocations']==len(usage['calls'])<=limits['invocations']
    assert len(recovery['candidates'])<=limits['candidates']
    assert recovery.get('rounds_attempted',0)<=limits['rounds']
    assert len(recovery['accepted_variants'])<=limits['retained_variants']
    assert recovery['temporary_workspace_removed'] is True
    baseline=report['baseline']
    if baseline is not None:
        expected=hashlib.sha256(json.dumps(baseline['analysis'],sort_keys=True).encode()).hexdigest()
        assert expected==baseline['analysis_sha256']
        validate_eligibility(baseline['eligibility'])
    variants={}
    for variant in recovery['accepted_variants']:
        assert variant['repair_conditioned'] and variant['temporary_files_removed']
        assert len(variant['edits'])<=limits['edits']
        assert all(edit['replacement']==';' for edit in variant['edits'])
        data=apply_edits(original,variant['edits'])
        assert hashlib.sha256(data).hexdigest()==variant['source_sha256']
        assert variant['source_map']==source_map(original,variant['edits'])
        assert len(data.splitlines())==len(original.splitlines())
        validate_eligibility(variant['eligibility'])
        variants[variant['id']]=variant
    assert all(item['repair_conditioned'] and item['variant_id'] in variants for item in report['repair_conditioned_findings'])
    assert recovery['eligibility_change']['function_path_coverage_certified'] is False
    if not recovery['enabled']:
        assert not variants and not recovery['candidates']
        assert not any(call['role'] in ('machine_fixit_capture','fixit_capability') for call in usage['calls'])
    return True
