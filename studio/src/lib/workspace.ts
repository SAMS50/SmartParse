export interface SourceFile {
  id: string; name: string; text: string; openedText: string;
  exportedText: string | null; origin: 'new' | 'import' | 'example';
}
export const dirtyFile = (file: SourceFile) => file.exportedText === null ? file.text.length > 0 : file.text !== file.exportedText
export function validateName(name: string, files: SourceFile[], id?: string): string | null {
  if (!/^[^\\/:*?"<>|\x00-\x1f]{1,96}\.[ch]$/i.test(name) || name.includes('..')) return 'Use a .c or .h filename without paths (maximum 98 characters).'
  if (/^(con|prn|aux|nul|com[1-9]|lpt[1-9])\./i.test(name)) return 'Reserved device filename.'
  if (files.some(f => f.id !== id && f.name.toLowerCase() === name.toLowerCase())) return 'Another open file has that name.'
  return null
}
export function uniqueName(name: string, files: SourceFile[]) {
  const dot=name.lastIndexOf('.'),base=name.slice(0,dot),extension=name.slice(dot)
  let candidate=name,index=2
  while (files.some(f=>f.name.toLowerCase()===candidate.toLowerCase())) {
    const suffix=`-${index++}`;candidate=`${base.slice(0,96-suffix.length)}${suffix}${extension}`
  }
  return candidate
}
export function sourceFile(name: string, text='', origin: SourceFile['origin']='new'): SourceFile {
  return {id:crypto.randomUUID(),name,text,openedText:text,exportedText:origin==='import'?text:null,origin}
}
export function downloadSource(file: SourceFile) {
  const url=URL.createObjectURL(new Blob([file.text],{type:'text/plain;charset=utf-8'}))
  const link=document.createElement('a');link.href=url;link.download=file.name;link.click()
  setTimeout(()=>URL.revokeObjectURL(url),0)
}
