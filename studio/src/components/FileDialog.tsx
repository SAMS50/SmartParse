import {useEffect, useRef, useState} from 'react'

export function FileDialog({mode,name,onCancel,onSubmit}: {mode:'rename'|'close';name:string;onCancel:()=>void;onSubmit:(value:string)=>string|null}) {
  const [value,setValue]=useState(name),[error,setError]=useState('')
  const panel=useRef<HTMLDivElement>(null)
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement
    panel.current?.querySelector<HTMLElement>('input,button')?.focus()
    return()=>previous?.focus()
  },[])
  return <div className="modal-backdrop"><div className="confirm-dialog" ref={panel} role="dialog" aria-modal="true" aria-labelledby="file-dialog-title" onKeyDown={event=>{
    if(event.key==='Escape')onCancel()
    if(event.key==='Tab'){
      const items=Array.from(panel.current?.querySelectorAll<HTMLElement>('input,button')||[]),first=items[0],last=items[items.length-1]
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
      if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
    }
  }}><h2 id="file-dialog-title">{mode==='rename'?'Rename file':`Close ${name}?`}</h2>
    {mode==='rename'?<form onSubmit={event=>{event.preventDefault();setError(onSubmit(value)||'')}}><label>File name<input aria-label="File name" value={value} onChange={e=>setValue(e.target.value)}/></label>{error&&<p role="alert">{error}</p>}<div><button type="button" className="secondary-button" onClick={onCancel}>Cancel</button><button className="primary-button" type="submit">Rename</button></div></form>:<><p>This file has changes not included in its last import or download. Closing discards this in-memory copy.</p><div><button className="secondary-button" onClick={onCancel}>Keep editing</button><button className="primary-button" onClick={()=>onSubmit('')}>Close without saving</button></div></>}
  </div></div>
}
