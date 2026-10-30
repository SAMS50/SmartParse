import {forwardRef, useImperativeHandle, useRef, useEffect} from 'react'
import Editor, {loader} from '@monaco-editor/react'
import * as monaco from 'monaco-editor/editor/editor.api.js'
import 'monaco-editor/languages/definitions/cpp/register.js'
import EditorWorker from 'monaco-editor/editor/editor.worker.js?worker'
import type {Diagnostic, EditorLocation, Preview} from '../types/report'

// Bundle workers locally; no CDN or external editor service is used.
self.MonacoEnvironment = {getWorker: () => new EditorWorker()}
loader.config({monaco})

export interface EditorHandle {navigate: (location: EditorLocation) => void}
interface Props {
  value: string; onChange: (value: string) => void; diagnostics: Diagnostic[];
  locations: Record<string, EditorLocation>; onCursor: (line: number, column: number) => void;
}
const options: monaco.editor.IStandaloneEditorConstructionOptions = {
  fontFamily: 'Cascadia Code, Consolas, monospace', fontSize: 13, lineHeight: 22,
  minimap: {enabled: false}, padding: {top: 14}, scrollBeyondLastLine: false,
  tabSize: 4, automaticLayout: true, smoothScrolling: true,
  overviewRulerBorder: false, renderLineHighlight: 'all', ariaLabel: 'C source editor',
  bracketPairColorization: {enabled: true}, fixedOverflowWidgets: true,
}

export const CodeEditor = forwardRef<EditorHandle, Props>(function CodeEditor(props, ref) {
  const editor = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  function markers() {
    const model = editor.current?.getModel(); if (!model) return
    monaco.editor.setModelMarkers(model, 'smartparse', props.diagnostics.flatMap(d => {
      const at = props.locations[d.id]; if (!at || d.context_note) return []
      const max = model.getLineMaxColumn(at.line)
      return [{startLineNumber: at.line, endLineNumber: at.line,
        startColumn: Math.min(at.column, max), endColumn: Math.min(at.precision === 'line' ? max : at.column + 1, max),
        message: `${d.message}\n${d.analyzer} · ${d.conditioning}`, source: d.analyzer,
        severity: d.severity === 'warning' ? monaco.MarkerSeverity.Warning :
          ['error', 'fatal error'].includes(d.severity || '') ? monaco.MarkerSeverity.Error : monaco.MarkerSeverity.Info}]
    }))
  }
  useEffect(markers, [props.diagnostics, props.locations, props.value])
  useImperativeHandle(ref, () => ({navigate(at) {
    editor.current?.setPosition({lineNumber: at.line, column: at.column})
    editor.current?.revealLineInCenter(at.line); editor.current?.focus()
  }}))
  return <Editor height="100%" language="c" theme="vs-dark" value={props.value} options={options}
    loading={<div className="editor-loading">Loading local code editor…</div>}
    beforeMount={m => m.editor.defineTheme('smartparse-dark', {base: 'vs-dark', inherit: true, rules: [], colors: {
      'editor.background': '#151719', 'editorLineNumber.foreground': '#717985', 'editorLineNumber.activeForeground': '#E5E7EB',
      'editor.lineHighlightBackground': '#20242A', 'editor.selectionBackground': '#304253', 'editorCursor.foreground': '#6E8FB3'}})}
    onMount={(instance) => {editor.current = instance; monaco.editor.setTheme('smartparse-dark');
      instance.onDidChangeCursorPosition(e => props.onCursor(e.position.lineNumber, e.position.column)); markers()}}
    onChange={value => props.onChange(value || '')}/>
})

export function RecoveredDiff({original, preview}: {original: string; preview: Preview}) {
  const host = useRef<HTMLDivElement>(null)
  useEffect(() => {
    let dispose = () => {}
    // Defer browser-resource allocation past React's speculative StrictMode
    // setup/cleanup cycle, so a worker never receives already disposed models.
    const frame = requestAnimationFrame(() => {
      if (!host.current) return
      const originalModel = monaco.editor.createModel(original, 'c')
      const modifiedModel = monaco.editor.createModel(preview.source, 'c')
      const diff = monaco.editor.createDiffEditor(host.current, {theme: 'smartparse-dark',
        readOnly: true, originalEditable: false, minimap: {enabled: false}, automaticLayout: true, renderSideBySide: true})
      diff.setModel({original: originalModel, modified: modifiedModel})
      dispose = () => {
        diff.setModel(null); diff.dispose(); originalModel.dispose(); modifiedModel.dispose()
      }
    })
    return () => {
      // Monaco 0.57 requires detachment before model disposal. The React diff
      // wrapper currently disposes models first, causing errors on tab changes.
      cancelAnimationFrame(frame); dispose()
    }
  }, [original, preview.source])
  return <div className="diff-wrap"><header><strong>Verified source comparison</strong><span className="provenance-label">{preview.conditioning}</span></header><div className="diff-labels"><span>Original · unchanged</span><span>Accepted temporary variant · read-only</span></div><div ref={host} style={{height: 210}} aria-label="Accepted source variant diff"/>
    <details className="preview-provenance"><summary>Verified variant provenance · {preview.variant_id}</summary><p>{preview.basis}</p><code>SHA-256 {preview.sha256}</code></details></div>
}
