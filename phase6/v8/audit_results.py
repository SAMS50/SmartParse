"""Audit saved executions and expose frozen-reference limitations without relabeling."""
import json
from pathlib import Path
from .prepare import HERE,ROOT,digest,write_json,verify_freeze


def walk(value):
    if isinstance(value,dict):
        if 'role' in value and isinstance(value.get('command'),list) and 'status' in value:yield value
        for child in value.values():yield from walk(child)
    elif isinstance(value,list):
        for child in value:yield from walk(child)


def main():
    verify_freeze()
    config=json.loads((HERE/'configurations.json').read_text());tools=config['tools']
    versions=[dict(tool=t['id'],path=t['path'],expected_binary_sha256=t['binary_sha256'],
                   unchanged=Path(t['path']).is_file() and digest(Path(t['path']).read_bytes())==t['binary_sha256']) for t in tools]
    expected={str(Path(t['path']).resolve()).casefold() for t in tools}
    reports=[];allcalls=[];supervisors=[]
    for path in sorted((HERE/'outputs/extended').rglob('*.json')):
        if path.name.endswith('.process.json'):
            supervisors.append(json.loads(path.read_text()));continue
        report=json.loads(path.read_text());calls=list(walk(report));allcalls.extend(calls)
        result=report['result']
        reports.append(dict(configuration=report['configuration'],case=path.stem,status=result.get('status'),
            counted_invocations=result.get('usage',{}).get('compiler_invocations',0),
            elapsed_seconds=report.get('elapsed_seconds'),source_sha256=report.get('source_sha256'),
            recorded_call_entries=len(calls)))
    commands=[dict(role=c['role'],command=c['command'],status=c['status'],returncode=c.get('returncode'),
                   elapsed_seconds=c.get('elapsed_seconds')) for c in allcalls]
    unexpected=[c for c in commands if str(Path(c['command'][0]).resolve()).casefold() not in expected]
    # Trace containers can repeat records; do not equate nested entry count with calls.
    write_json(HERE/'outputs/execution_audit.json',dict(
        expected_configurations=147,completed_worker_records=len(reports),supervisor_records=len(supervisors),
        externally_timed_out=sum(s['timed_out'] for s in supervisors),
        failed_workers=sum(s.get('exit_code')!=0 for s in supervisors),
        total_counted_tool_invocations=sum(r['counted_invocations'] for r in reports),
        summed_case_seconds=round(sum(r['elapsed_seconds'] or 0 for r in reports),3),
        unchanged_tool_binaries=versions,unexpected_command_executables=unexpected,
        no_user_binary_execution_observed=not unexpected,
        scope='Recorded tool calls only; compiler executables can spawn their compiler phases. GCC objects private, no linking/run commands.',
        runs_span_interruption=True,timing_limitations='Single passes across interrupted sessions; descriptive, no speed or significance claims.',
        configurations=reports,recorded_commands=commands))
    gaps=[
        dict(case='C07_resource',proposed_root='C07_resource-R1',configurations=['extended_baseline','recovery_assisted','isolation_assisted'],
             frozen_allowed_id='unix.Stream',actual_id='alpha.unix.Stream',
             reason='Checker ID omitted from authored allowlist; source-bound leak evidence exists, but strict frozen matching leaves it unmatched.'),
        dict(case='C08_contradiction',proposed_root='C08_contradiction-R1',configurations=['extended_baseline','recovery_assisted','isolation_assisted'],
             frozen_allowed_id='smartparse.semantic.contradictory_int_conjunction',actual_id='SP6.contradictory_int_conjunction',
             reason='Authored ID differs from actual existing detector ID. Cppcheck is NOT uniquely capable here despite exclusive automated matching.'),
        dict(case='C09_repair_null',proposed_root='C09_repair_null-R1',configurations=['compiler_clang','extended_baseline','recovery_assisted','isolation_assisted','gcc14'],
             frozen_anchor_line=3,actual_diagnostic_line=2,
             reason='Missing return semicolon is reported on preceding statement rather than next-token anchor; exact frozen line rule undercounts frontend evidence.'),
        dict(case='C06_allocation',proposed_root='C06_allocation-R1',configurations=['gcc14'],
             reason='Multiple allocation/store/read diagnostics can concern the same underallocation root; unmatched records are NOT independent false positives.'),
    ]
    for gap in gaps:gap.update(status='pending_human_review',independently_verified=False,rule_change_applied=False)
    write_json(HERE/'review/frozen_matching_limitations.json',dict(
        purpose='Expose evaluation uncertainty without post-hoc inflation or changing frozen rules.',issues=gaps))
    print(json.dumps(dict(runs=len(reports),invocations=sum(r['counted_invocations'] for r in reports),
                         seconds=round(sum(r['elapsed_seconds'] or 0 for r in reports),3),unexpected=len(unexpected),
                         binaries_unchanged=all(t['unchanged'] for t in versions)),indent=2))


if __name__=='__main__':main()
