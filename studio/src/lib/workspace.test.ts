import {expect, test, vi} from 'vitest'
import {dirtyFile, downloadSource, sourceFile, uniqueName, validateName} from './workspace'

test('new files are empty and become dirty only after editing',()=>{
  const file=sourceFile('untitled-1.c');expect(file.text).toBe('');expect(dirtyFile(file)).toBe(false)
  file.text='int value;';expect(dirtyFile(file)).toBe(true)
  file.exportedText=file.text;expect(dirtyFile(file)).toBe(false)
})
test('imports have a baseline; editable example copies remain unsaved',()=>{
  expect(dirtyFile(sourceFile('a.h','int x;','import'))).toBe(false)
  expect(dirtyFile(sourceFile('a.c','int x;','example'))).toBe(true)
})
test.each(['../x.c','C:\\x.c','NUL.c','file.txt','bad?.h'])('rejects unsafe filename %s',name=>{
  expect(validateName(name,[])).not.toBeNull()
})
test('names are unique ignoring case, with bounded suffixes',()=>{
  const file=sourceFile('a.c');expect(validateName('A.c',[file])).toMatch(/Another/)
  expect(uniqueName('a.c',[file])).toBe('a-2.c')
  expect(validateName('a.c',[file],file.id)).toBeNull()
})
test('save requests a truthful browser download containing exact source',()=>{
  const create=vi.spyOn(URL,'createObjectURL').mockReturnValue('blob:source'),revoke=vi.spyOn(URL,'revokeObjectURL').mockImplementation(()=>{})
  const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){expect(this.download).toBe('new.c')})
  downloadSource(sourceFile('new.c','int main(void) { return 0; }'))
  expect(create).toHaveBeenCalledWith(expect.any(Blob));expect(click).toHaveBeenCalledOnce()
  create.mockRestore();revoke.mockRestore();click.mockRestore()
})
