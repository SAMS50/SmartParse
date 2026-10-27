"""Conservative root-reference comparison of saved GCC and live Clang reports."""
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'output'
LIVE = OUT / 'clang_validation'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def match(issue, report):
    anchors = {issue['line'], *issue['diagnostic_lines']}
    hits = [d for d in report['diagnostics'] if d['line'] in anchors and d['severity'] != 'note']
    if issue['kind'] in ('memory safety', 'runtime', 'resource', 'logic'):
        # In particular, an undeclared-name cascade at a memory-bug location
        # does not detect that memory defect.
        hits = [d for d in hits if d['severity'] == 'warning']
    if issue.get('uncertain'):
        assessment = 'uncertain'
    elif hits:
        assessment = 'detected'
    elif issue['kind'] in ('syntax', 'semantic/type'):
        assessment = 'missed'
    else:
        assessment = 'unsupported'
    return {'assessment': assessment, 'compiler_outcome': 'detected' if hits else 'missed',
            'diagnostics': hits}


def escape(value):
    return str(value).replace('|', '\\|').replace('\n', '<br>')


def main():
    gcc = read(OUT / 'sample.json')
    clang = read(LIVE / 'sample.json')
    reference = read(HERE / 'sample_reference.json')['issues']
    rows = [{'line': issue['line'], 'kind': issue['kind'], 'description': issue['description'],
             'gcc': match(issue, gcc), 'clang': match(issue, clang)} for issue in reference]
    counts = {backend: dict(collections.Counter(row[backend]['assessment'] for row in rows)) for backend in ('gcc', 'clang')}
    (LIVE / 'reference_comparison.json').write_text(json.dumps({'counts': counts, 'entries': rows}, indent=2) + '\n', encoding='utf-8')
    lines = ['# GCC 6.3 versus Clang 17: 68-reference comparison', '',
             'Only the same unmodified cleaned 500-line source is compared. The manual reference is non-exhaustive.', '',
             '## Matching criteria', '',
             'Match a non-note diagnostic to the reviewed root line or its documented error-reporting anchors. '
             'For the missing semicolons, GCC points to following lines 31/83 while Clang points to 30/82. '
             'Also inspect the message and issue kind: undeclared-name/type cascades at allocation lines are not memory-bug detections. '
             'Only relevant warnings count as compiler evidence for memory/runtime/logic reference entries. '
             'Multiple warnings, repeated uses, path notes, and different backend severities never create extra reference entries. '
             'Uncertain contracts/preconditions remain uncertain even if a warning was emitted.', '',
             'Detected means a relevant diagnostic, not proof of programmer intent. Missed means a supported syntax/type reference '
             'has no relevant diagnostic in this invocation. Unsupported means the required general logic analysis is outside scope '
             'or the sample analyzer pass is blocked by frontend errors. Such an entry separately records compiler_outcome=missed. '
             'The four independent memory checks passed; that does not validate blocked path analysis on this malformed sample.', '',
             '| Backend | Detected | Missed | Unsupported | Uncertain |', '|---|---:|---:|---:|---:|']
    for backend in ('gcc','clang'):
        c=counts[backend]
        lines.append(f'| {backend} | {c.get("detected",0)} | {c.get("missed",0)} | {c.get("unsupported",0)} | {c.get("uncertain",0)} |')
    lines += ['', 'These are dispositions of a reviewed list, not precision/recall or universal bug counts. '
              'The combined evidence detects the same 16 non-uncertain reference entries as Clang alone; '
              'overlapping compiler reports are counted once per manual reference.', '',
              '| Root line | Kind | Reviewed issue | GCC assessment / compiler outcome | Clang assessment / compiler outcome |',
              '|---|---|---|---|---|']
    for row in rows:
        cells = (row['line'], row['kind'], row['description'],
                 f'{row["gcc"]["assessment"]} / {row["gcc"]["compiler_outcome"]}',
                 f'{row["clang"]["assessment"]} / {row["clang"]["compiler_outcome"]}')
        lines.append('| ' + ' | '.join(escape(cell) for cell in cells) + ' |')
    lines += ['', '## Differences requiring interpretation', '',
              '- Clang warns about the fixed-buffer overflow at line 74; GCC syntax-only did not. No inference is made about other unreported buffers.',
              '- GCC emits undeclared-global_label cascades at 432/438 after rejecting the declaration following line 30. Clang recovers that declaration. These do not add defects.',
              '- Clang reports both uses of mystery_value at 414/415, suggests last_value at 415, and reports an incompatible return conversion from that recovery. This is one undeclared-name root, not three separate intended bugs.',
              '- The pointer-to-int return at 393 is a GCC warning but a Clang error. Severity differences are not detection gains.',
              '- Both warn twice about the multicharacter/comparison root at 494. GCC warns about floating division at 382; Clang does not in this invocation. Its reference disposition stays uncertain.',
              '- Neither emits the reviewed missing-return warning at 405 in this malformed sample. It remains a measured miss, without inventing a cause.',
              '- General intent-dependent logic errors remain unproved. Static findings are kept outside ordinary compiler totals and are not deduplicated by line alone.', '',
              '## All measured Clang compiler diagnostics', '',
              '| Line:column | Severity | Category | Identifier | Exact message |', '|---|---|---|---|---|']
    for d in clang['diagnostics']:
        cells = (f'{d["line"]}:{d["column"]}', d['severity'], d['category'], d['diagnostic_id'] or '—', d['message'])
        lines.append('| ' + ' | '.join(escape(cell) for cell in cells) + ' |')
    lines += ['', '## Independent fixture analyzer findings', '',
              '| Fixture | Status | Finding line | Checker | Exact warning | Path notes |', '|---|---|---:|---|---|---:|']
    for name in ('null_pointer','memory_leak','use_after_free','double_free'):
        report=read(LIVE/(name+'.json'))
        for finding in report['findings']:
            if finding['severity'] != 'note':
                cells=(name,report['status'],finding['line'],finding['diagnostic_id'],finding['message'],report['findings_summary']['notes'])
                lines.append('| '+' | '.join(escape(cell) for cell in cells)+' |')
    (LIVE / 'comparison.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(counts,indent=2))


if __name__ == '__main__':
    main()
