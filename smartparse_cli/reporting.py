"""Stable JSON and safe terminal/Markdown rendering of unified reports."""
import html
import json


def safe(value):
    return ''.join(c if c.isprintable() or c=='\n' else f'\\x{ord(c):02x}' for c in str(value))


def version_of(run):
    raw=run['raw']
    if raw.get('compiler'):return raw['compiler']['version']
    if raw.get('observed_version'):return raw['observed_version'].strip().splitlines()[0]
    if raw.get('tool'):return str(raw['tool'].get('version','unknown'))
    if raw.get('schema')=='smartparse.semantic_analysis':raw=raw['upstream']
    cap=raw.get('capabilities') or {}
    return cap.get('compiler',{}).get('version') or 'not recorded / not applicable'


def terminal(report):
    lines=[f'SmartParse {report["version"]} — {report["status"]}',f'Source: {report["source"]["path"]}',
           f'Original source unchanged: {report["source"]["original_unchanged"]}']
    for run in report['runs']:
        lines.append(f'{run["id"]}: {run["status"]}; {version_of(run)}')
        if run.get('reason'):lines.append('  '+run['reason'])
        if run.get('recovery'):lines.append('  Recovery: '+str(run['recovery']['stop_reason']))
        if run.get('isolation'):lines.append('  Isolation: '+str(run['isolation'].get('status'))+'; '+str(run['isolation'].get('reason')))
    byid={d['id']:d for d in report['diagnostics']}
    for group in report['groups']:
        record=byid[group['diagnostic_ids'][0]]
        if record['context_note']:continue
        loc=record['location'];location=loc.get('file') or '<unknown file>'
        if loc.get('line') is not None:location+=':'+str(loc['line'])
        if loc.get('column') is not None:location+=':'+str(loc['column'])
        identifier=f' [{record["diagnostic_id"]}]' if record['diagnostic_id'] else ''
        lines.append(f'{location}: {record["severity"]} ({record["category"]}; {record["analyzer"]}; {record["conditioning"]}): {record["message"]}{identifier}')
        if record['evidence']['source_snippet']:lines.append('  '+record['evidence']['source_snippet'])
        if record['suggestion']:lines.append('  Suggestion only (not applied): '+json.dumps(record['suggestion'],ensure_ascii=True))
        if len(group['diagnostic_ids'])>1:lines.append(f'  {len(group["diagnostic_ids"])} contributing records retained in JSON')
    for issue in report['tool_issues']:lines.append(f'Tool/configuration issue ({issue["analyzer"]}, {issue["status"]}): {issue["message"]}')
    s=report['summary'];lines.append(f'Diagnostic records: {s["errors"]} errors, {s["warnings"]} warnings, {s["notes"]} notes')
    lines.append('Categories: '+', '.join(f'{k}={v}' for k,v in s['categories'].items()))
    lines.append('Conditioning: '+', '.join(f'{k}={v}' for k,v in s['conditioning'].items()))
    lines.append('Analyzer availability is checked only for requested passes; use doctor for installation/version inventory.')
    lines.append('Counts are evidence, not confirmed defects. Function/path coverage is uncertified; zero findings does not prove safety.')
    return safe('\n'.join(lines))


def markdown(report):
    def esc(value):return html.escape(safe(value)).replace('|','\\|').replace('`','\\`').replace('\n','<br>')
    lines=['# SmartParse analysis', '', f'**Status:** {report["status"]}',
           f'**Source:** {esc(report["source"]["path"])}',
           f'**Original unchanged:** {report["source"]["original_unchanged"]}', '',
           '| Analyzer | Completion | Version |','|---|---|---|']
    for run in report['runs']:lines.append(f'| {run["id"]} | {run["status"]} | {esc(version_of(run))} |')
    lines+=['','## Diagnostics','','| Location | Severity/category | Analyzer | Provenance | Message |','|---|---|---|---|---|']
    for d in report['diagnostics']:
        if d['context_note']:continue
        loc=d['location'];location=f'{loc.get("file")}:{loc.get("line")}:{loc.get("column")}'
        lines.append(f'| {esc(location)} | {esc(d["severity"])} / {esc(d["category"])} | {esc(d["analyzer"])} | {d["conditioning"]} | {esc(d["message"])} |')
    lines+=['','## Summary','',esc(json.dumps(report['summary'],ensure_ascii=True)),'','## Completeness and tool issues','']
    for issue in report['tool_issues']:lines.append(f'- {esc(issue["analyzer"])}: {esc(issue["status"])}; {esc(issue["message"])}')
    lines+=['','Function/path coverage is uncertified. Conditional findings retain variant assumptions. Zero findings does not prove safety.',
            'Independent human review remains pending; no accuracy metrics are inferred. Use JSON for all raw records, notes, grouping and provenance.']
    return '\n'.join(lines)


def render(report,format='terminal'):
    if format=='json':return json.dumps(report,indent=2,ensure_ascii=True,allow_nan=False)
    if format=='markdown':return markdown(report)
    return terminal(report)
