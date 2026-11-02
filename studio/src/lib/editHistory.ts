// Offsets count Unicode code points, including when Monaco uses UTF-16.
export interface EditEvent {version:number;offset:number;deleted:string;inserted:string}
export interface EditHistory {base_source:string;base_version:number;source_version:number;events:EditEvent[]}
export function recordEdit(previous:EditHistory|undefined,before:string,after:string):EditHistory {
  let h=previous
  if(!h||replay(h)!==before)h={base_source:before,base_version:0,source_version:0,events:[]}
  if(before===after)return h
  const a=Array.from(before),b=Array.from(after);let start=0,end=0
  while(start<Math.min(a.length,b.length)&&a[start]===b[start])start++
  while(end<Math.min(a.length,b.length)-start&&a[a.length-end-1]===b[b.length-end-1])end++
  const event={version:h.source_version+1,offset:start,deleted:a.slice(start,a.length-end).join(''),inserted:b.slice(start,b.length-end).join('')}
  h={...h,source_version:event.version,events:[...h.events,event]}
  while(h.events.length>8){const first:EditEvent=h.events[0];h={...h,base_source:apply(h.base_source,first),base_version:first.version,events:h.events.slice(1)}}
  if(JSON.stringify(h).length>48000||h.base_source.length>32768||event.deleted.length>32768||event.inserted.length>32768)
    return {base_source:after.length<=32768?after:'',base_version:0,source_version:0,events:[]}
  return h
}
function apply(source:string,e:EditEvent){const a=Array.from(source);return a.slice(0,e.offset).join('')+e.inserted+a.slice(e.offset+Array.from(e.deleted).length).join('')}
export function replay(h:EditHistory){return h.events.reduce(apply,h.base_source)}
