import {useCallback, useEffect, useMemo, useRef, useState} from 'react'
import {AlertCircle, ArrowDownToLine, ArrowRight, Braces, Check, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, Code2, FileCode2, FlaskConical, GitCompareArrows, LoaderCircle, Play, RotateCcw, Search, Settings2, ShieldCheck, Square, Upload, WandSparkles, X} from 'lucide-react'
import {CodeEditor, type EditorHandle} from './components/CodeEditor'
import {Inspector, type InspectorTab} from './components/Inspector'
import {PanelDivider} from './components/PanelDivider'
import {SettingsPanel} from './components/SettingsPanel'
import * as api from './lib/api'
import type {Diagnostic, Example, Settings, StudioResult, Tool} from './types/report'

const DEFAULTS: Settings = {analyzers: ['compiler'], recovery: false, isolation: false, standard: 'c11'}
export default function App() {
  const [examples,setExamples] = useState<Example[]>([]), [tools,setTools] = useState<Tool[]>([])
  const [connected,setConnected] = useState(false), [checking,setChecking] = useState(true)
  const [code,setCode] = useState('// Select an example or write C source here.\n'), [filename,setFilename] = useState('untitled.c')
  const [loaded,setLoaded] = useState(code), [selected,setSelected] = useState('')
  const [settings,setSettings] = useState<Settings>(DEFAULTS), [settingsOpen,setSettingsOpen] = useState(false)
  const [result,setResult] = useState<StudioResult | null>(null), [snapshot,setSnapshot] = useState({source: '', filename: ''})
  const [busy,setBusy] = useState(false), [error,setError] = useState(''), [notice,setNotice] = useState('')
  const [filter,setFilter] = useState('all'), [query,setQuery] = useState(''), [shown,setShown] = useState(100)
  const [tab,setTab] = useState<InspectorTab>('overview'), [cursor,setCursor] = useState({line: 1, column: 1})
  const [split,setSplit] = useState(58), [pendingExample,setPendingExample] = useState<Example | null>(null)
  const [detailsHeight,setDetailsHeight] = useState<number | null>(null)
  const main = useRef<HTMLElement>(null)
  const detailSize = detailsHeight ?? (tab === 'overview' ? 144 : tab === 'recovery' ? 320 : 240)
  const [help,setHelp] = useState(false)
  const initialized = useRef(false), controller = useRef<AbortController | null>(null)
  const editor = useRef<EditorHandle>(null), fileInput = useRef<HTMLInputElement>(null), workspace = useRef<HTMLDivElement>(null)
  const dirty = code !== loaded
  const closeSettings = useCallback(() => setSettingsOpen(false), [])
  const stale = !!result && (code !== snapshot.source || filename !== snapshot.filename)

  function load(example: Example) {
    initialized.current = true;setCode(example.source);setLoaded(example.source);setFilename(example.filename);setSelected(example.id)
    setSettings(s => ({...s, analyzers: example.analyzers, recovery: example.recovery, isolation: example.isolation}))
    setResult(null);setError('');setNotice('');setTab(example.recovery || example.isolation ? 'recovery' : 'overview')
  }
  function choose(example: Example) {if (dirty) setPendingExample(example);else load(example)}
  const connect = useCallback(async () => {
    setChecking(true)
    try {
      await api.health();setConnected(true)
      const [gallery, inventory] = await Promise.all([api.getExamples(), api.getTools()])
      setExamples(gallery.examples);setTools(inventory.tools)
      if (!initialized.current && gallery.examples.length) load(gallery.examples[0])
    } catch (e) {setConnected(false);setError(`Backend unavailable. Start the local API, then reconnect. ${e instanceof Error ? e.message : ''}`)}
    finally {setChecking(false)}
  }, [])
  useEffect(() => {void connect();return () => controller.current?.abort()}, [connect])

  const runAnalysis = useCallback(async () => {
    if (controller.current || !connected) return
    if (new TextEncoder().encode(code).length > 128 * 1024) {setError('Source exceeds the 128 KiB limit.');return}
    const request = new AbortController();controller.current = request
    setBusy(true);setResult(null);setError('');setNotice('');setShown(100)
    const submitted = {source: code, filename};setSnapshot(submitted)
    try {
      const answer = await api.analyze({...submitted, ...settings}, request.signal)
      if (controller.current === request) setResult(answer)
    } catch (e) {
      if (controller.current === request && !request.signal.aborted) setError(e instanceof Error ? e.message : 'Analysis request failed')
    } finally {
      if (controller.current === request) {controller.current = null;setBusy(false)}
    }
  }, [code,filename,settings,connected])
  useEffect(() => {
    const key = (event: KeyboardEvent) => {if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {event.preventDefault();void runAnalysis()}}
    window.addEventListener('keydown',key);return () => window.removeEventListener('keydown',key)
  }, [runAnalysis])

  function stopWaiting() {
    controller.current?.abort();controller.current = null;setBusy(false)
    setNotice('Stopped waiting. The server may finish its bounded run before accepting another analysis.')
  }
  async function importFile(file?: File) {
    if (!file) return
    if (!/\.c$/i.test(file.name) || file.size > 128 * 1024) {setError('Choose a .c file no larger than 128 KiB.');return}
    if (dirty && !window.confirm('Discard unsaved editor changes and import this file?')) return
    try {
      const text = new TextDecoder('utf-8', {fatal: true}).decode(await file.arrayBuffer())
      initialized.current = true;setCode(text);setLoaded(text);setFilename(file.name);setSelected('');setResult(null);setError('')
      setNotice('Imported UTF-8 text. The original file on disk is unchanged.')
    } catch {setError('This file is not valid UTF-8. Convert a copy before importing.')}
  }
  const diagnostics = result?.report.diagnostics || []
  const groups = useMemo(() => {
    if (!result) return []
    const records = new Map(diagnostics.map(d => [d.id,d]))
    return result.report.groups.flatMap(g => {
      const first = g.diagnostic_ids.map(id => records.get(id)).find(d => d && !d.context_note)
      return first ? [{group: g, diagnostic: first}] : []
    }).filter(({diagnostic:d}) => (filter === 'all' || (filter === 'error' ? ['error','fatal error'].includes(d.severity || '') : d.severity === filter)) &&
      `${d.message} ${d.category} ${d.analyzer} ${d.diagnostic_id}`.toLowerCase().includes(query.toLowerCase()))
  }, [result,diagnostics,filter,query])
  const primary = diagnostics.filter(d => !d.context_note).length
  function resizeDetails(value: number) {
    const height = main.current?.getBoundingClientRect().height || 760
    setDetailsHeight(Math.max(120,Math.min(420,height * .55,value)))
  }


  return <div className="studio-shell antialiased">
    <header className="topbar"><a className="brand" href="#workspace" aria-label="SmartParse Studio workspace"><span className="brand-mark"><Braces size={21}/></span><strong>SmartParse</strong><span className="studio-label">STUDIO</span></a>
      <div className="top-breadcrumb"><span>Workspace</span><ChevronRight size={13}/><span title={filename} style={{maxWidth: '25ch', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{filename}</span></div>
      <div className="top-actions"><span className={`connection ${connected ? 'connected' : ''}`}><i/>{checking ? 'Checking tools' : connected ? `${tools.filter(t => t.status === 'available').length} tools available` : 'API offline'}</span>
        {!connected && <button className="text-button" onClick={() => void connect()}>Reconnect</button>}
        <button className="icon-button" aria-label="Analysis settings" onClick={() => setSettingsOpen(true)} disabled={busy}><Settings2 size={18}/></button>
        {busy ? <button className="stop-button" onClick={stopWaiting}><Square size={12}/>Stop waiting</button> : <button className="primary-button" aria-label="Analyze" onClick={() => void runAnalysis()} disabled={!connected || checking}><Play size={14} fill="currentColor"/>Analyze<span className="shortcut">Ctrl ↵</span></button>}
      </div>
    </header>
    <div className="workbench">
      <aside className="activity-rail" aria-label="Workspace navigation"><button className="rail-button selected" title="Code workspace" aria-label="Code workspace" onClick={() => setTab('overview')}><Code2 size={22}/></button><button className="rail-button" title="Recovery evidence" aria-label="Recovery evidence" onClick={() => setTab('recovery')}><WandSparkles size={20}/></button><button className="rail-button" title="Analyzer comparison" aria-label="Analyzer comparison" onClick={() => setTab('comparison')}><GitCompareArrows size={20}/></button><span className="rail-spacer"/><button className="rail-button" aria-label="About Studio" onClick={() => setHelp(true)}><CircleHelp size={20}/></button></aside>
      <aside className="explorer"><div className="explorer-heading"><span>EXPLORER</span><FlaskConical size={14}/></div><div className="workspace-folder"><ChevronDown size={13}/><span>SMARTPARSE WORKSPACE</span></div>
        <button className="current-file" onClick={() => editor.current?.navigate({line: 1,column: 1,precision: 'line',reason: 'File start'})}><FileCode2 size={15}/><span>{filename}</span>{dirty && <i className="unsaved-dot"/>}</button>
        <div className="gallery-heading">EXAMPLE GALLERY <span>{examples.length}</span></div>
        <nav aria-label="C examples">{examples.map(example => <button key={example.id} className={`example-button ${selected === example.id ? 'active' : ''}`} disabled={busy} onClick={() => choose(example)}><FileCode2 size={14}/><span>{example.title}</span>{selected === example.id && <ChevronRight size={12}/>}</button>)}</nav>

      </aside>
      <main id="workspace" className="main-workspace" ref={main}>
        {(error || notice) && <div className={`message-banner ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}><AlertCircle size={16}/><span>{error || notice}</span><button className="icon-button" aria-label="Dismiss message" onClick={() => {setError('');setNotice('')}}><X size={15}/></button></div>}
        <div className="workspace-panes" ref={workspace}>
          <section className="editor-pane" style={{width: `${split}%`}} aria-label="Source editor"><div className="pane-header"><div className="file-tab"><FileCode2 size={15}/><strong>{filename}</strong>{dirty && <i className="unsaved-dot"/>}</div><div className="editor-tools"><span className="language-chip">{settings.standard.toUpperCase()}</span><button className="icon-button" title="Import a local C file" aria-label="Import C file" disabled={busy} onClick={() => fileInput.current?.click()}><Upload size={14}/></button><button className="icon-button" title="Reset to loaded source" aria-label="Reset code" disabled={!dirty || busy} onClick={() => {setCode(loaded);setNotice('Editor reset to the loaded source.')}}><RotateCcw size={14}/></button></div></div>
            <div className="editor-config"><select aria-label="Example selector" value={selected} disabled={busy} onChange={e => {const example = examples.find(x => x.id === e.target.value);if (example) choose(example)}}><option value="">Custom source</option>{examples.map(e => <option value={e.id} key={e.id}>{e.title}</option>)}</select><span>{settings.analyzers.join(' + ')}{settings.recovery ? ' · recovery' : ''}{settings.isolation ? ' · isolation' : ''}</span></div>
            <div className="monaco-host"><CodeEditor ref={editor} value={code} onChange={value => {initialized.current = true;setCode(value)}} diagnostics={stale || busy ? [] : diagnostics} locations={result?.studio.editor_locations || {}} onCursor={(line,column) => setCursor({line,column})}/></div>
            <div className="editor-footer"><span>{dirty ? 'Unsaved editor changes' : 'UTF-8'}</span><span>Ln {cursor.line}, Col {cursor.column}</span></div>
          </section>
          <PanelDivider axis="vertical" label="Resize editor and diagnostics" value={split} min={34} max={72} step={2}
            onChange={setSplit} onDrag={event => {const box=workspace.current?.getBoundingClientRect();if (box) setSplit(Math.max(34,Math.min(72,(event.clientX-box.left)/box.width*100)))}}/>
          <section className="diagnostics-pane" aria-label="Diagnostics"><header className="pane-header"><span className="pane-title"><AlertCircle size={16}/>Diagnostics <b>{result ? primary : '—'}</b></span><div className="export-controls"><button className="icon-button" aria-label="Export JSON report" title="Download complete JSON report" disabled={!result} onClick={() => result && api.downloadReport(result,'json')}><ArrowDownToLine size={16}/></button><button className="text-button" aria-label="Export Markdown report" disabled={!result} onClick={() => result && api.downloadReport(result,'markdown')}>MD</button></div></header>
            <div className="diagnostic-toolbar"><div className="severity-tabs"><button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>All</button><button className={filter === 'error' ? 'active error-count' : 'error-count'} onClick={() => setFilter('error')}><span/>Errors {result?.report.summary.errors ?? '—'}</button><button className={filter === 'warning' ? 'active warning-count' : 'warning-count'} onClick={() => setFilter('warning')}><span/>Warnings {result?.report.summary.warnings ?? '—'}</button></div><label className="search-box"><Search size={14}/><input aria-label="Filter diagnostics" placeholder="Filter findings…" value={query} onChange={e => setQuery(e.target.value)}/></label></div>
            {result && result.report.status !== 'completed' && <div className="partial-banner" role="status"><AlertCircle size={15}/><span><strong>Analysis {result.report.status}.</strong> Some passes may be blocked or unavailable. Inspect Execution for details; displayed findings do not imply full coverage.</span></div>}
            {stale && <div className="stale-banner" role="status">Source changed since this report. Highlights are hidden until you analyze again.</div>}
            <div className="findings-list" aria-live="polite">
              {busy ? <div className="empty-state"><LoaderCircle className="spin" size={28}/><h2>Analyzing your source</h2><p>Running the requested passes. Results will appear when the backend responds.</p><small>No simulated progress. The worker has a bounded deadline.</small></div> : !result ? <div className="empty-state"><p>No analysis results.</p><button className="text-button" onClick={() => setSettingsOpen(true)}>Analyzer settings</button></div> : groups.length ? <>
                <div className="findings-caption"><span>{groups.length} evidence groups · {result.report.summary.notes} context notes</span><span className={`status-badge ${result.report.status}`}>{result.report.status}</span></div>
                {groups.slice(0,shown).map(({group,diagnostic}) => <Finding key={group.id} diagnostic={diagnostic} records={group.diagnostic_ids.length} canNavigate={!stale && !!result.studio.editor_locations[diagnostic.id]} onNavigate={() => editor.current?.navigate(result.studio.editor_locations[diagnostic.id])}/>)}
                {shown < groups.length && <button className="secondary-button full" onClick={() => setShown(s => s+100)}>Show next findings ({groups.length-shown} remaining)</button>}
              </> : <div className="empty-state"><CheckCircle2 size={30}/><h2>{query || filter !== 'all' ? 'No findings match this filter.' : result.report.status === 'completed' ? 'No primary diagnostics reported.' : 'Analysis is incomplete.'}</h2><p>{result.report.status === 'completed' ? 'Completion and zero findings do not prove the program is safe or defect-free.' : 'Review execution status and tool issues below. No complete coverage is claimed.'}</p></div>}
            </div><footer className="findings-footer"><ShieldCheck size={13}/><span>Static analysis only · coverage is not exhaustive</span></footer>
          </section>
        </div>
        <PanelDivider axis="horizontal" label="Resize analysis details" value={detailSize} min={120} max={420} step={20}
          onChange={resizeDetails} onDrag={event => {const box=main.current?.getBoundingClientRect();if (box) resizeDetails(box.bottom-event.clientY-12)}}/>
        <Inspector result={result} source={snapshot.source} tab={tab} onTab={setTab} height={detailSize}
          onReset={() => {setSplit(58);setDetailsHeight(null)}}/>
      </main>
    </div>
    <footer className="statusbar"><span><i className={`status-dot ${connected ? 'online' : ''}`}/>{connected ? 'Local backend connected' : 'Local backend offline'}</span><span>UTF-8</span></footer>
    <input ref={fileInput} type="file" accept=".c,text/x-c" hidden onChange={e => {void importFile(e.target.files?.[0]);e.target.value = ''}}/>
    {settingsOpen && <SettingsPanel value={settings} tools={tools} onChange={setSettings} onClose={closeSettings}/>}
    {pendingExample && <div className="modal-backdrop"><div className="confirm-dialog" role="alertdialog" aria-labelledby="discard-title"><h2 id="discard-title">Discard editor changes?</h2><p>Your original file is untouched. Loading another example replaces the current editor text.</p><div><button className="secondary-button" onClick={() => setPendingExample(null)}>Keep editing</button><button className="primary-button" onClick={() => {load(pendingExample);setPendingExample(null)}}>Load example</button></div></div></div>}
    {help && <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setHelp(false)}><div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="about-title"><header><h2 id="about-title">Built for evidence, not guesses.</h2><button className="icon-button" aria-label="Close about" onClick={() => setHelp(false)}><X size={17}/></button></header><p>SmartParse Studio uses the existing compiler and recovery engine. Compiler findings belong to GCC/Clang; research recovery and conditional findings retain their provenance.</p><p>Ctrl+Enter runs analysis. Edit freely; stale reports never highlight changed source. Independent human adjudication remains pending.</p><p>Local trusted use only. Compiler temporary files are not a security sandbox.</p></div></div>}
  </div>
}

function Finding({diagnostic:d,records,canNavigate,onNavigate}: {diagnostic: Diagnostic; records: number; canNavigate: boolean; onNavigate: () => void}) {
  const error = ['error','fatal error'].includes(d.severity || '')
  return <article className={`finding ${error ? 'is-error' : d.severity === 'warning' ? 'is-warning' : 'is-info'}`}><div className="finding-top"><span className="finding-severity"><AlertCircle size={14}/>{d.severity || 'unknown'}</span><span className="finding-location" title={d.location.file || 'No file location'}>{d.location.file?.split(/[\\/]/).pop()} {d.location.line ? `· Line ${d.location.line}${d.location.column ? `:${d.location.column}` : ''}` : 'No location'}</span></div>
    <button className="finding-message" disabled={!canNavigate} onClick={onNavigate} title={canNavigate ? 'Navigate to source location' : 'No reliable current-editor location available'}>{d.message}</button>
    <div className="finding-tags"><span title="Analyzer">{d.analyzer}</span><span title="Category">{d.category}</span><span className={d.conditioning !== 'original-source' ? 'conditional' : 'original'}>{d.conditioning}</span></div>
    {d.evidence.source_snippet && <code className="source-snippet">{d.evidence.source_snippet.trim()}</code>}
    <details><summary>Technical evidence <ChevronDown size={12}/></summary><div className="technical-details"><p>Diagnostic ID: {d.diagnostic_id || 'Not provided'}</p><p>Mapping: {d.location_space}</p><p>{records} contributing record{records !== 1 ? 's' : ''}; root cause not independently confirmed.</p><pre>{JSON.stringify({provenance: d.provenance, raw_reference: d.raw_reference, raw_record: d.raw_record},null,2)}</pre></div></details>
  </article>
}
