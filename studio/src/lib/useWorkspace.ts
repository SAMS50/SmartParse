import {useEffect, useRef, useState} from 'react'
import {dirtyFile, sourceFile, uniqueName, validateName, type SourceFile} from './workspace'

export function useWorkspace() {
  const [files,setFiles]=useState(()=>[sourceFile('untitled-1.c')])
  const [activeId,setActiveId]=useState<string|null>(null)
  const next=useRef(2)
  const active=files.find(f=>f.id===activeId)||files[0]
  useEffect(()=>{
    const warn=(event:BeforeUnloadEvent)=>{if(files.some(dirtyFile)){event.preventDefault();event.returnValue=''}}
    window.addEventListener('beforeunload',warn);return()=>window.removeEventListener('beforeunload',warn)
  },[files])
  function add(name:string,text:string,origin:SourceFile['origin']) {
    if(files.length>=20) throw new Error('Workspace limit: 20 files. Close a tab before opening another.')
    const error=validateName(name,[]);if(error) throw new Error(error)
    const file=sourceFile(uniqueName(name,files),text,origin)
    setFiles(current=>[...current,file]);setActiveId(file.id);return file
  }
  function update(id:string,patch:Partial<SourceFile>) {setFiles(current=>current.map(f=>f.id===id?{...f,...patch}:f))}
  function rename(id:string,name:string) {
    const error=validateName(name,files,id);if(error)return error
    if(files.find(file=>file.id===id)?.name!==name)update(id,{name,exportedText:null})
    return null
  }
  function close(id:string) {
    const remaining=files.filter(f=>f.id!==id)
    if(!remaining.length){const blank=sourceFile(`untitled-${next.current++}.c`);setFiles([blank]);setActiveId(blank.id)}
    else {setFiles(remaining);if(active.id===id)setActiveId(remaining[Math.max(0,files.findIndex(f=>f.id===id)-1)]?.id||remaining[0].id)}
  }
  return {files,active,select:setActiveId,update,rename,close,add,newFile:()=>add(`untitled-${next.current++}.c`,'','new')}
}
