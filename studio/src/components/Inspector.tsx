import {AlertCircle, CheckCircle2, Clock3, FileJson, GitCompareArrows, RotateCcw, ShieldCheck, TerminalSquare, WandSparkles} from 'lucide-react'
import type {Candidate, Diagnostic, Run, StudioResult} from '../types/report'
import {RecoveredDiff} from './CodeEditor'

export type InspectorTab = 'overview' | 'runs' | 'recovery' | 'comparison' | 'raw'
const tabs: [InspectorTab, string, typeof ShieldCheck][] = [['overview','Overview',ShieldCheck],['recovery','Recovery',WandSparkles],['runs','Execution',TerminalSquare],['comparison','Comparison',GitCompareArrows],['raw','Raw evidence',FileJson]]

export function Inspector({result, source, tab, onTab, height, onReset}: {
  result: StudioResult | null; source: string; tab: InspectorTab; onTab: (t: InspectorTab) => void;
  height: number; onReset: () => void;
}) {
  const recoveryCount = result?.report.runs.reduce((n,r) => n + (r.recovery?.candidates.length || 0),0) || 0
  return <section className={`inspector inspector-${tab}`} style={{height}} aria-label="Analysis details">
    <header className="inspector-header"><nav className="inspector-tabs" aria-label="Inspector views">{tabs.map(([id,label,Icon]) => <button key={id} onClick={() => onTab(id)} className={id === tab ? 'active' : ''} aria-pressed={id === tab}><Icon size={14}/>{label}{id === 'recovery' && recoveryCount > 0 && <b className="tab-count">{recoveryCount}</b>}</button>)}</nav>
      <button className="icon-button reset-layout" title="Restore default panel sizes" aria-label="Reset panel sizes" onClick={onReset}><RotateCcw size={14}/></button></header>
    <div className="inspector-content">{!result ? <div className="inspector-empty"><TerminalSquare size={20}/><span>Execution evidence will appear here after analysis.</span><small>Source preserved · no C binaries run</small></div> : <Content result={result} source={source} tab={tab}/>}</div>
  </section>
}

function Content({result,source,tab}: {result: StudioResult; source: string; tab: InspectorTab}) {
  const report = result.report
  if (tab === 'raw') return <pre className="raw-evidence" aria-label="Raw JSON evidence">{JSON.stringify(report, null, 2)}</pre>
  if (tab === 'runs' || tab === 'comparison') return <>
    <table className="run-table"><thead><tr><th>Analyzer / pass</th><th>Status</th><th>Original</th><th>Conditional</th><th>Time</th></tr></thead>
      <tbody>{report.runs.map(run => {
        const records = report.diagnostics.filter(d => d.raw_reference.run_id === run.id && !d.context_note)
        return <tr key={run.id}><td><strong>{run.id}</strong><small>{run.reason || 'See raw report for tool configuration'}</small></td><td><span className={`status-badge ${run.status}`}>{run.status}</span></td><td>{records.filter(d => d.conditioning === 'original-source').length}</td><td>{records.filter(d => d.conditioning !== 'original-source').length}</td><td>{run.elapsed_seconds.toFixed(2)} s</td></tr>
      })}</tbody></table>
    {tab === 'comparison' && <div className="comparison-notes"><p>Requested: {report.requested_analyzers.join(', ')} · Effective: {report.effective_analyzers.join(', ')}</p><p>{report.groups.filter(g => g.analyzers.length > 1).length} evidence-supported multi-analyzer groups. Cross-backend root equivalence is not automatically adjudicated.</p><p>Counts are diagnostic records, not independent defects. Agreement is not proof; function/path coverage remains uncertified.</p></div>}
  </>
  if (tab === 'recovery') return <Recovery result={result} source={source}/>
  return <div className="overview-summary">
    <div className="summary-facts"><div className="summary-status"><span className={`status-badge ${report.status}`}>{report.status}</span><span><strong>{report.summary.errors} {report.summary.errors === 1 ? 'error' : 'errors'} · {report.summary.warnings} {report.summary.warnings === 1 ? 'warning' : 'warnings'}</strong><small>{report.summary.notes} context notes · diagnostic records, not confirmed defects</small></span></div>
      <span className="summary-fact"><Clock3 size={14}/>{report.usage.elapsed_seconds.toFixed(2)} s</span>
      <span className="summary-fact"><CheckCircle2 size={14}/>{report.source.original_unchanged ? 'Source preserved' : 'Preservation unverified'}</span>
      <span className="summary-fact"><ShieldCheck size={14}/>{result.studio.workspace_removed ? 'Workspace removed' : 'Cleanup unverified'}</span></div>
    <div className="summary-runs" aria-label="Analyzer execution summary">{report.runs.map(run => <span key={run.id}><strong>{run.id}</strong><span className={`status-badge ${run.status}`}>{run.status}</span></span>)}<small>{report.usage.compiler_invocations} compiler invocations</small></div>
    <p className="coverage-note"><AlertCircle size={13}/>Completion does not certify path coverage or bug freedom. Independent review pending.</p>
    {report.tool_issues.map((issue,i) => <p className="issue-line" key={i}>{issue.analyzer}: {issue.message}</p>)}
  </div>
}

function repairType(candidate: Candidate) {
  const fix = candidate.fixit
  if (!fix) return 'Proposed edit'
  if (fix.end_line === undefined || fix.end_column === undefined) return 'Proposed edit (range unavailable)'
  if (fix.start_line === fix.end_line && fix.start_column === fix.end_column) return 'Insertion'
  return fix.replacement === '' ? 'Deletion' : 'Substitution'
}

function Recovery({result,source}: {result: StudioResult; source: string}) {
  const report = result.report
  const runs = report.runs.filter(r => r.recovery || r.isolation || r.id === 'smartparse')
  const originals = report.diagnostics.filter(d => !d.context_note && d.conditioning === 'original-source' && d.category === 'syntax')
  const conditioned = report.diagnostics.filter(d => !d.context_note && d.conditioning !== 'original-source')
  return <div className="recovery-content">
    <div className="recovery-heading"><span><WandSparkles size={15}/><strong>Recovery evidence</strong></span><small>Temporary analysis copies only · editor and files unchanged</small></div>
    <div className="recovery-layout"><div className="recovery-story">
      {originals.length > 0 && <section className="recovery-block"><h3>Original syntax diagnostics</h3>{originals.map(d => <p className="original-error" key={d.id}><span>Line {d.location.line ?? '?'} · {d.analyzer}</span>{d.message}</p>)}</section>}
      {runs.map(run => <RecoveryRun key={run.id} run={run} diagnostics={report.diagnostics}/>)}
      {runs.length === 0 && <p className="recovery-empty">No recovery pass was requested. Enable punctuation recovery explicitly in Settings, then analyze again. No source changes have been applied.</p>}
      {conditioned.length > 0 && <details className="conditioned-findings" open><summary>{conditioned.length} conditional downstream record{conditioned.length === 1 ? '' : 's'}</summary>{conditioned.map(d => <p key={d.id}><span className="provenance-label">{d.conditioning}</span><span>Line {d.location.line ?? '?'} · {d.analyzer}</span><strong>{d.message}</strong></p>)}<small>These findings depend on the recorded variant assumptions; they are not unconditional baseline findings.</small></details>}
    </div><div className="preview-stack">{result.studio.previews.length > 0 ? result.studio.previews.map(p => <RecoveredDiff key={p.run_id + p.variant_id} original={source} preview={p}/>) : <div className="no-preview"><ShieldCheck size={21}/><strong>No verified source comparison</strong><p>No hash-verified accepted source variant is available. Suggestions are not applied to the editor.</p></div>}</div></div>
  </div>
}

function RecoveryRun({run,diagnostics}: {run: Run; diagnostics: Diagnostic[]}) {
  return <section className="recovery-block"><h3>{run.id} <span>analysis pass</span></h3>
    {run.recovery && <p className="recovery-outcome"><strong>Recovery outcome</strong><code>{run.recovery.stop_reason || 'Not reported'}</code></p>}
    {(run.recovery?.candidates || []).map(c => <article className="repair-candidate" key={c.id}>
      <header><strong>{c.id} · {repairType(c)}</strong><span className={`status-badge ${c.status}`}>{c.status}</span></header>
      {c.fixit && <p className="proposed-operation">{c.fixit.replacement === '' ? 'Remove reported range' : <>Proposed text <code>{JSON.stringify(c.fixit.replacement)}</code></>}<span>Reported snapshot · line {c.fixit.start_line}:{c.fixit.start_column}</span></p>}
      <p>{c.status === 'accepted' ? 'Accepted for a temporary analysis variant. Original source unchanged.' : 'Not applied to an accepted variant.'}</p>
      <p className="candidate-reason">{c.reason}</p>{c.score !== undefined && <small>Reported score: {c.score}</small>}
    </article>)}
    {run.id === 'smartparse' && <><p className="suggestion-note">Suggested token repairs only. No source edits applied.</p>{diagnostics.filter(d => d.raw_reference.run_id === run.id && d.suggestion).map(d => <div key={d.id}>{Array.isArray(d.suggestion) && d.suggestion.map((suggestion,index) => {
      if (!suggestion || typeof suggestion !== 'object') return null
      const s=suggestion as Record<string,unknown>
      return <p className="research-suggestion" key={index}><strong>{String(s.operation || 'Unspecified operation')}</strong><code>{JSON.stringify(s.token)}</code><span>Line {String(s.line ?? '?')}:{String(s.column ?? '?')}</span>{typeof s.score === 'number' && <span>Reported score: {s.score}</span>}</p>
    })}<details><summary>Raw repair suggestions</summary><pre>{JSON.stringify(d.suggestion,null,2)}</pre></details></div>)}</>}
    {run.recovery && <p className="eligibility-change">Frontend newly eligible: <strong>{String(run.recovery.eligibility_change.frontend_newly_eligible)}</strong> · Analyzer newly completed: <strong>{String(run.recovery.eligibility_change.analyzer_newly_completed)}</strong></p>}
    {run.isolation && <details><summary>Isolation: {run.isolation.status}</summary><p>{run.isolation.reason}</p><pre>{JSON.stringify(run.isolation.excluded_functions,null,2)}</pre></details>}
  </section>
}
