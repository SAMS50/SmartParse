import {useCallback, useEffect, useMemo, useRef, useState} from 'react'
import {AlertCircle, ArrowDownToLine, ArrowRight, Braces, Check, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, Code2, FileCode2, FlaskConical, GitCompareArrows, LoaderCircle, Play, RotateCcw, Search, Settings2, ShieldCheck, Square, Upload, WandSparkles, X, FilePlus2, Save, Pencil, FolderOpen} from 'lucide-react'
import {CodeEditor, type EditorHandle} from './components/CodeEditor'
import {Inspector, type InspectorTab} from './components/Inspector'
import {FileDialog} from './components/FileDialog'
import {useWorkspace} from './lib/useWorkspace'
import {dirtyFile, downloadSource} from './lib/workspace'
import {PanelDivider} from './components/PanelDivider'
import {SettingsPanel} from './components/SettingsPanel'
import * as api from './lib/api'
import type {Diagnostic, Example, Settings, StudioResult, Tool} from './types/report'

const DEFAULTS: Settings = {analyzers: ['compiler'], recovery: false, isolation: false, standard: 'c11'}
export default function App() {
  const [examples,setExamples] = useState<Example[]>([]), [tools,setTools] = useState<Tool[]>([])
  const [connected,setConnected] = useState(false), [checking,setChecking] = useState(true)
  const documents=useWorkspace(), active=documents.active
  const code=active.text, filename=active.name, loaded=active.openedText
  const setCode=(text:string)=>documents.update(active.id,{text})
  const [fileDialog,setFileDialog]=useState<{mode:'rename'|'close';id:string}|null>(null)
  const [settings,setSettings] = useState<Settings>(DEFAULTS), [settingsOpen,setSettingsOpen] = useState(false)
  const [analyses,setAnalyses] = useState<Record<string,{result:StudioResult;snapshot:{source:string;filename:string}}>>({})
  const retained=analyses[active.id], result=retained?.result||null, snapshot=retained?.snapshot||{source:'',filename:''}
  const [busy,setBusy] = useState(false), [error,setError] = useState(''), [notice,setNotice] = useState('')
  const [filter,setFilter] = useState('all'), [query,setQuery] = useState(''), [shown,setShown] = useState(100)
  const [tab,setTab] = useState<InspectorTab>('overview'), [cursor,setCursor] = useState({line: 1, column: 1})
  const [split,setSplit] = useState(58)
  const [detailsCollapsed,setDetailsCollapsed]=useState(false),[explorerOpen,setExplorerOpen]=useState(false)
  const [detailsHeight,setDetailsHeight] = useState<number | null>(null)
  const main = useRef<HTMLElement>(null)
  const detailSize = detailsHeight ?? (tab === 'overview' ? 144 : tab === 'recovery' ? 320 : 240)
  const [help,setHelp] = useState(false)
  const controller = useRef<AbortController | null>(null)
  const editor = useRef<EditorHandle>(null), fileInput = useRef<HTMLInputElement>(null), workspace = useRef<HTMLDivElement>(null)
  const dirty = dirtyFile(active)
  const closeSettings = useCallback(() => setSettingsOpen(false), [])
  const stale = !!result && (code !== snapshot.source || filename !== snapshot.filename)

  function resetReport(){setError('');setNotice('')}
  function selectFile(id:string){setExplorerOpen(false);if(id!==active.id){documents.select(id);resetReport()}}
  function newFile(){try{setExplorerOpen(false);documents.newFile();resetReport()}catch(e){setError(String(e))}}
  function saveFile(){const text=editor.current?.getText?.()??code;downloadSource({...active,text});documents.update(active.id,{text,exportedText:text});setNotice(`Download requested: ${filename}. Original disk file not overwritten.`)}
  function choose(example:Example){
    try{setExplorerOpen(false);documents.add(example.filename,example.source,'example');resetReport();setSettings(s=>({...s,analyzers:example.analyzers,recovery:example.recovery,isolation:example.isolation}));setTab(example.recovery||example.isolation?'recovery':'overview')}
    catch(e){setError(String(e))}
  }
  function closeFile(id:string){const file=documents.files.find(f=>f.id===id);if(file&&dirtyFile(file))setFileDialog({mode:'close',id});else{documents.close(id);resetReport()}}
  const connect = useCallback(async () => {
    setChecking(true)
    try {
      await api.health();setConnected(true)
      const [gallery, inventory] = await Promise.all([api.getExamples(), api.getTools()])
      setExamples(gallery.examples);setTools(inventory.tools)

    } catch (e) {setConnected(false);setError(`Backend unavailable. Start the local API, then reconnect. ${e instanceof Error ? e.message : ''}`)}
    finally {setChecking(false)}
  }, [])
  useEffect(() => {void connect();return () => controller.current?.abort()}, [connect])

  const runAnalysis = useCallback(async () => {
    if (controller.current || !connected) return
    const submittedText=editor.current?.getText?.()??code
    if (new TextEncoder().encode(submittedText).length > 128 * 1024) {setError('Source exceeds the 128 KiB limit.');return}
    const request = new AbortController();controller.current = request
    setBusy(true);setAnalyses(previous=>{const copy={...previous};delete copy[active.id];return copy});setError('');setNotice('');setShown(100)
    const submitted = {source: submittedText, filename}, submittedId=active.id
    try {
      const answer = await api.analyze({...submitted,filename:filename.replace(/\.h$/i,'.c'), ...settings}, request.signal)
      if (controller.current === request) {setAnalyses(previous=>({...previous,[submittedId]:{result:answer,snapshot:submitted}}));if(settings.recovery||settings.isolation){setTab('recovery');setDetailsCollapsed(false)}}
    } catch (e) {
      if (controller.current === request && !request.signal.aborted) setError(e instanceof Error ? e.message : 'Analysis request failed')
    } finally {
      if (controller.current === request) {controller.current = null;setBusy(false)}
    }
  }, [active.id,code,filename,settings,connected])
  useEffect(()=>{
    const ids=new Set(documents.files.map(f=>f.id))
    setAnalyses(previous=>Object.keys(previous).some(id=>!ids.has(id))?Object.fromEntries(Object.entries(previous).filter(([id])=>ids.has(id))):previous)
  },[documents.files])
  useEffect(()=>{
    if(!explorerOpen)return
    const close=(event:KeyboardEvent)=>{if(event.key==='Escape')setExplorerOpen(false)}
    window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close)
  },[explorerOpen])
  const runRef=useRef(runAnalysis);runRef.current=runAnalysis
  useEffect(() => {
    const key = (event: KeyboardEvent) => {if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {event.preventDefault();void runRef.current()}}
    window.addEventListener('keydown',key);return () => window.removeEventListener('keydown',key)
  }, [])

  function stopWaiting() {
    controller.current?.abort();controller.current = null;setBusy(false)
    setNotice('Stopped waiting. The server may finish its bounded run before accepting another analysis.')
  }
  async function importFile(file?:File) {
    if(!file)return
    if(!/\.[ch]$/i.test(file.name)||file.size>128*1024){setError('Choose a .c or .h file no larger than 128 KiB.');return}
    try{
      const text=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer())
      documents.add(file.name,text,'import');setExplorerOpen(false);resetReport()
      setNotice('Imported UTF-8 text. File remains in memory until downloaded.')
    }catch(e){setError(`Could not open file: ${e instanceof Error?e.message:'invalid UTF-8'}`)}
  }
  const saveRef=useRef(saveFile);saveRef.current=saveFile
  useEffect(()=>{
    const save=(event:KeyboardEvent)=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='s'){event.preventDefault();saveRef.current()}}
    window.addEventListener('keydown',save);return()=>window.removeEventListener('keydown',save)
  },[])
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
      <div className="top-actions"><button className="icon-button explorer-toggle" aria-label="Toggle Explorer" aria-expanded={explorerOpen} aria-controls="workspace-explorer" onClick={()=>setExplorerOpen(value=>!value)}><FolderOpen size={17}/></button><button className="icon-button" aria-label="New File" title="New File" disabled={busy} onClick={newFile}><FilePlus2 size={17}/></button><button className="icon-button" aria-label="Open File" title="Open .c or .h file" disabled={busy} onClick={()=>fileInput.current?.click()}><Upload size={17}/></button><button className="icon-button" aria-label="Save" title="Download active file (Ctrl+S)" onClick={saveFile}><Save size={17}/></button><span className={`connection ${connected ? 'connected' : ''}`}><i/>{checking ? 'Checking tools' : connected ? `${tools.filter(t => t.status === 'available').length} tools available` : 'API offline'}</span>
        {!connected && <button className="text-button" onClick={() => void connect()}>Reconnect</button>}
        <button className="icon-button" aria-label="Analysis settings" onClick={() => setSettingsOpen(true)} disabled={busy}><Settings2 size={18}/></button>
        {busy ? <button className="stop-button" onClick={stopWaiting}><Square size={12}/>Stop waiting</button> : <button className="primary-button" aria-label="Analyze" onClick={() => void runAnalysis()} disabled={!connected || checking}><Play size={14} fill="currentColor"/>Analyze<span className="shortcut">Ctrl ↵</span></button>}
      </div>
    </header>
    <div className="workbench">
      <aside className="activity-rail" aria-label="Workspace navigation"><button className="rail-button selected" title="Code workspace" aria-label="Code workspace" onClick={() => setTab('overview')}><Code2 size={22}/></button><button className="rail-button" title="Recovery evidence" aria-label="Recovery evidence" onClick={() => setTab('recovery')}><WandSparkles size={20}/></button><button className="rail-button" title="Analyzer comparison" aria-label="Analyzer comparison" onClick={() => setTab('comparison')}><GitCompareArrows size={20}/></button><span className="rail-spacer"/><button className="rail-button" aria-label="About Studio" onClick={() => setHelp(true)}><CircleHelp size={20}/></button></aside>
      <aside id="workspace-explorer" className={`explorer ${explorerOpen?'drawer-open':''}`}><div className="explorer-heading">Explorer</div><p className="workspace-kind">In-memory files</p><nav aria-label="Open files">{documents.files.map(file=><div className={`explorer-file ${active.id===file.id?'active':''}`} key={file.id}><button disabled={busy} onClick={()=>selectFile(file.id)} title={file.name}><FileCode2 size={14}/><span>{file.name}</span>{dirtyFile(file)&&<i className="unsaved-dot"/>}</button><button className="icon-button" aria-label={`Rename ${file.name}`} disabled={busy} onClick={()=>setFileDialog({mode:'rename',id:file.id})}><Pencil size={12}/></button><button className="icon-button" aria-label={`Remove ${file.name}`} disabled={busy} onClick={()=>closeFile(file.id)}><X size={13}/></button></div>)}</nav><details className="examples-section"><summary>Examples ({examples.length})</summary><nav aria-label="C examples">{examples.map(example=><button key={example.id} className="example-button" disabled={busy} onClick={()=>choose(example)}><FileCode2 size={14}/><span>{example.title}</span></button>)}</nav></details></aside>
      <main id="workspace" className="main-workspace" ref={main}>
        {(error || notice) && <div className={`message-banner ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}><AlertCircle size={16}/><span>{error || notice}</span><button className="icon-button" aria-label="Dismiss message" onClick={() => {setError('');setNotice('')}}><X size={15}/></button></div>}
        <div className="workspace-panes" ref={workspace}>
          <section className="editor-pane" style={{width: `${split}%`}} aria-label="Source editor"><div className="pane-header file-tabs" role="tablist" aria-label="Editor files" onKeyDown={event=>{
              if((event.target as HTMLElement).getAttribute('role')!=='tab'||busy)return
              const at=documents.files.findIndex(file=>file.id===active.id)
              const next=event.key==='ArrowRight'?(at+1)%documents.files.length:event.key==='ArrowLeft'?(at+documents.files.length-1)%documents.files.length:event.key==='Home'?0:event.key==='End'?documents.files.length-1:-1
              if(next>=0){event.preventDefault();selectFile(documents.files[next].id);event.currentTarget.querySelectorAll<HTMLButtonElement>('[role=tab]')[next]?.focus()}
            }}>{documents.files.map(file=><div className={`editor-tab ${file.id===active.id?'active':''}`} key={file.id}><button role="tab" tabIndex={file.id===active.id?0:-1} aria-selected={file.id===active.id} disabled={busy} onClick={()=>selectFile(file.id)}><FileCode2 size={13}/>{file.name}{dirtyFile(file)&&<i className="unsaved-dot"/>}</button><button className="tab-close" aria-label={`Close ${file.name}`} disabled={busy} onClick={()=>closeFile(file.id)}><X size={12}/></button></div>)}</div>
            <div className="editor-config"><span>{settings.standard.toUpperCase()} | {settings.analyzers.join(' + ')} | Active file only{filename.toLowerCase().endsWith('.h')?' (header as C)':''}{settings.recovery?' | recovery':''}{settings.isolation?' | isolation':''}</span><button className="icon-button" aria-label="Reset code" title="Reset to opened contents" disabled={!dirty||busy} onClick={()=>documents.update(active.id,{text:loaded,revision:active.revision+1})}><RotateCcw size={13}/></button></div>
            <div className="monaco-host"><CodeEditor ref={editor} documentId={active.id} revision={active.revision} openDocumentIds={documents.files.map(f=>f.id)} value={code} onChange={setCode} diagnostics={stale || busy ? [] : diagnostics} locations={result?.studio.editor_locations || {}} onCursor={(line,column) => setCursor({line,column})}/></div>
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
        {!detailsCollapsed&&<PanelDivider axis="horizontal" label="Resize analysis details" value={detailSize} min={120} max={420} step={20}
          onChange={resizeDetails} onDrag={event => {const box=main.current?.getBoundingClientRect();if (box) resizeDetails(box.bottom-event.clientY-12)}}/>}
        <Inspector result={result} source={snapshot.source} tab={tab} onTab={value=>{setTab(value);setDetailsCollapsed(false)}} height={detailSize} collapsed={detailsCollapsed} onCollapse={()=>setDetailsCollapsed(value=>!value)} stale={stale} onNavigate={id=>{const location=result?.studio.editor_locations[id];if(location&&!stale)editor.current?.navigate(location)}}
          onReset={() => {setSplit(58);setDetailsHeight(null);setDetailsCollapsed(false)}}/>
      </main>
    </div>
    <footer className="statusbar"><span><i className={`status-dot ${connected ? 'online' : ''}`}/>{connected ? 'Local backend connected' : 'Local backend offline'}</span><span>UTF-8</span></footer>
    <input ref={fileInput} type="file" accept=".c,.h,text/x-c,text/x-chdr" hidden onChange={e => {void importFile(e.target.files?.[0]);e.target.value = ''}}/>
    {settingsOpen && <SettingsPanel value={settings} tools={tools} onChange={setSettings} onClose={closeSettings}/>}
    {fileDialog && <FileDialog mode={fileDialog.mode} name={documents.files.find(f=>f.id===fileDialog.id)?.name||''} onCancel={()=>setFileDialog(null)} onSubmit={value=>{
      if(fileDialog.mode==='rename'){const error=documents.rename(fileDialog.id,value);if(error)return error}
      else {documents.close(fileDialog.id);resetReport()}
      setFileDialog(null);return null
    }}/>}
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
