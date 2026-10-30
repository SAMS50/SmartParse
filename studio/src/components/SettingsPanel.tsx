import {useEffect, useRef} from 'react'
import {X, ShieldCheck} from 'lucide-react'
import type {Settings, Tool} from '../types/report'

const choices = [
  ['compiler', 'Compiler diagnostics', 'Syntax, types and available warnings', 'gcc'],
  ['static', 'Clang Static Analyzer', 'Default path-sensitive checks', 'clang'],
  ['memory', 'Memory & resources', 'Existing capability-probed memory profile', 'clang'],
  ['semantic', 'Semantic review', 'Existing semantic profile; includes memory', 'clang'],
  ['gcc14', 'GCC 14 analyzer', 'Optional version-pinned profile', 'gcc14'],
  ['cppcheck', 'Cppcheck', 'Optional version-pinned original-source profile', 'cppcheck'],
  ['smartparse', 'SmartParse research', 'Original restricted C-like grammar', ''],
  ['panic', 'Panic baseline', 'Restricted C-like recovery baseline', ''],
]

export function SettingsPanel({value, tools, onChange, onClose}: {value: Settings; tools: Tool[]; onChange: (v: Settings) => void; onClose: () => void}) {
  const panel = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const previous = document.activeElement as HTMLElement
    panel.current?.querySelector<HTMLButtonElement>('button')?.focus()
    function key(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Tab') {
        const items = Array.from(panel.current?.querySelectorAll<HTMLElement>('button,input,select') || [])
        const first = items[0], last = items[items.length - 1]
        if (e.shiftKey && document.activeElement === first) {e.preventDefault(); last?.focus()}
        if (!e.shiftKey && document.activeElement === last) {e.preventDefault(); first?.focus()}
      }
    }
    document.addEventListener('keydown', key)
    return () => {document.removeEventListener('keydown', key); previous?.focus()}
  }, [onClose])
  function toggle(id: string) {
    const list = value.analyzers.includes(id) ? value.analyzers.filter(x => x !== id) : [...value.analyzers, id]
    if (list.length) onChange({...value, analyzers: list})
  }
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
    <div className="settings-panel" ref={panel} role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <header><div><span className="eyebrow">ANALYSIS CONFIGURATION</span><h2 id="settings-title">Choose your toolchain</h2></div><button className="icon-button" aria-label="Close settings" onClick={onClose}><X size={18}/></button></header>
      <p className="muted">Select the passes to run. Availability is a version check; capabilities are verified during analysis.</p>
      <div className="analyzer-choices">{choices.map(([id, title, description, dependency]) => {
        const available = !dependency || tools.some(t => (t.name === dependency || id === 'compiler' && t.name === 'clang') && t.status === 'available')
        return <label className={`analyzer-choice ${value.analyzers.includes(id) ? 'selected' : ''}`} key={id}>
          <input type="checkbox" checked={value.analyzers.includes(id)} onChange={() => toggle(id)}/>
          <span><strong>{title}</strong><small>{description}</small></span><span className={`availability-dot ${available ? 'online' : ''}`} title={available ? 'Available or no external tool required' : 'Not discovered; requested analysis may be unavailable'}/>
        </label>
      })}</div>
      <details className="tool-inventory"><summary>Installed tool versions</summary>{tools.map(tool => <p key={tool.name}><strong>{tool.name}</strong>: {tool.status}<br/><small>{tool.version || tool.reason || 'No version reported'}</small></p>)}</details>
      <div className="setting-row"><label htmlFor="standard">C standard</label><select id="standard" value={value.standard} onChange={e => onChange({...value, standard: e.target.value})}>{['c89','c99','c11','c17','gnu11'].map(s => <option key={s}>{s}</option>)}</select></div>
      <label className="switch-row"><span><strong>Punctuation recovery</strong><small>Compiler-validated temporary semicolon repairs</small></span><input type="checkbox" checked={value.recovery} onChange={e => onChange({...value, recovery: e.target.checked})}/></label>
      <label className="switch-row"><span><strong>Unaffected-region isolation</strong><small>Experimental · conservative function exclusion</small></span><input type="checkbox" checked={value.isolation} onChange={e => onChange({...value, isolation: e.target.checked})}/></label>
      <div className="safety-note"><ShieldCheck size={18}/><span>Original source is never modified. Conditional findings retain their assumptions. Limits: 128 KiB source, 45 s engine / 55 s worker.</span></div>
      <button className="primary-button full" onClick={onClose}>Apply configuration</button>
    </div>
  </div>
}
