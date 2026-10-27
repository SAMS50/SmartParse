"""Render measured diagnostics and conservative manual-reference comparison."""
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'output'


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', '<br>')


def main():
    sample = json.loads((OUTPUT / 'sample.json').read_text(encoding='utf-8'))
    reference = json.loads((HERE / 'sample_reference.json').read_text(encoding='utf-8'))
    comparisons = []
    for issue in reference['issues']:
        hits = [d for d in sample['diagnostics'] if d['line'] in issue['diagnostic_lines'] and d['severity'] != 'note']
        # Review provenance, not just line overlap: undeclared global_label is
        # a syntax-recovery cascade, not detection of the allocation/ownership bug.
        if issue['kind'] in ('memory safety', 'runtime', 'resource', 'logic'):
            hits = [d for d in hits if d['severity'] == 'warning']
        if issue.get('uncertain'):
            status = 'uncertain'
            reason = 'Contract, preconditions, or runtime environment are not fully specified.'
        elif hits:
            status = 'detected'
            reason = 'Relevant compiler diagnostic; warnings are evidence, not observed execution.'
        elif issue['kind'] in ('syntax', 'semantic/type'):
            status = 'missed'
            reason = 'No relevant diagnostic in this GCC invocation; serious earlier errors can suppress warnings.'
        else:
            status = 'unsupported'
            reason = ('General programmer-intent/contract checking is outside implemented scope.' if issue['kind'] == 'logic'
                      else 'Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result).')
        comparisons.append({**issue, 'assessment': status, 'compiler_outcome': 'detected' if hits else 'missed',
                            'observed_diagnostics': hits, 'reason': reason})
    (OUTPUT / 'sample_comparison.json').write_text(json.dumps(comparisons, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    counts = dict(collections.Counter(row['assessment'] for row in comparisons))
    lines = ['# Measured diagnostic inventory', '',
             'Generated from saved CLI JSON. Every diagnostic, including notes and cascades, is retained.', '']
    for name in ('sample', 'broken_records', 'pointer_and_logic', 'valid_inventory', 'semantic', 'missing_header'):
        report = json.loads((OUTPUT / (name + '.json')).read_text(encoding='utf-8'))
        lines += [f'## {name}', '', f'Backend: GCC; status: {report["status"]}; summary: `{json.dumps(report["summary"])}`.', '',
                  '| Line:column | Severity | Category | Identifier | Exact diagnostic message |',
                  '|---|---|---|---|---|']
        for d in report['diagnostics']:
            lines.append('| ' + ' | '.join(cell(v) for v in (f'{d["line"]}:{d["column"]}', d['severity'], d['category'], d['diagnostic_id'] or '—', d['message'])) + ' |')
        if not report['diagnostics']:
            lines.append('| — | — | — | — | No compiler diagnostics; not proof of bug-free behavior |')
        lines.append('')
    (OUTPUT / 'diagnostics.md').write_text('\n'.join(lines), encoding='utf-8')
    lines = ['# Sample: manual reference versus measured GCC output', '',
             'Reference established before compiler execution; non-exhaustive. Counts describe this reviewed list only, not accuracy/recall.', '',
             f'Assessment counts: `{json.dumps(counts)}`; total reviewed reference entries: {len(comparisons)}.', '',
             'The assessment and compiler outcome answer different questions. An unsupported analyzer check can be missed by the compiler pass. '
             'An uncertain contract can still have a warning. No unavailable analysis is counted as a completed negative check.', '',
             '| Reference line | Kind | Reference issue | Compiler outcome | Assessment | Observed diagnostic lines | Explanation |',
             '|---|---|---|---|---|---|---|']
    for row in comparisons:
        values = (row['line'], row['kind'], row['description'], row['compiler_outcome'], row['assessment'],
                  ', '.join(str(d['line']) for d in row['observed_diagnostics']) or '—', row['reason'])
        lines.append('| ' + ' | '.join(cell(v) for v in values) + ' |')
    lines += ['', 'The diagnostics at 432 and 438 are undeclared-global_label cascades from the declaration rejected after line 30. '
              'They do not establish detection of allocation overflow, allocation failure, leaks, or use-after-free at those sites.', '',
              'The two warnings at line 164 and two warnings at 494 are multiple pieces of evidence for their respective root issues. '
              'The three notes are context, not three additional defects. Compiler-warning categories are intentionally preserved even '
              'when the reference describes a type or memory defect.', '',
              'Floating division at 382 is warned about by GCC. It is not automatically classified as integer division-by-zero UB; '
              'floating semantics and the desired contract need review. The possible threading issue at 427 is not established by this '
              'single-threaded sample. No runtime experiment was performed.']
    (OUTPUT / 'sample_comparison.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'reference_entries': len(comparisons), 'assessments': counts}, indent=2))


if __name__ == '__main__':
    main()
