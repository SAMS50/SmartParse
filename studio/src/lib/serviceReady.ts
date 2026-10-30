import type {Tool} from '../types/report'

/** API health + discovery of selected dependencies, not coverage/capability proof. */
export function serviceReady(connected:boolean, checking:boolean, analyzers:string[], tools:Tool[]) {
  if(!connected||checking)return false
  const available=new Set(tools.filter(tool=>tool.status==='available').map(tool=>tool.name))
  return analyzers.every(analyzer=>{
    if(analyzer==='smartparse'||analyzer==='panic')return true
    if(analyzer==='compiler')return available.has('gcc')||available.has('clang')
    if(['static','memory','semantic'].includes(analyzer))return available.has('clang')
    return available.has(analyzer)
  })
}
