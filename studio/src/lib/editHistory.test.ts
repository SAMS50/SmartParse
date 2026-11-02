import {test,expect} from 'vitest'
import {recordEdit,replay} from './editHistory'
test('capture replacement, Unicode offsets, undo and bounded source versions',()=>{
  let h=recordEdit(undefined,'a😀;','a😀')
  expect(h.events[0]).toEqual({version:1,offset:2,deleted:';',inserted:''})
  h=recordEdit(h,'a😀','a😀;');expect(replay(h)).toBe('a😀;')
  for(let i=0;i<12;i++){const s=replay(h);h=recordEdit(h,s,s+'x')}
  expect(h.events.length).toBe(8);expect(h.base_version).toBe(6);expect(h.source_version).toBe(14)
  expect(replay(h)).toBe('a😀;'+'x'.repeat(12))
})
test('mismatched external snapshot resets the chain',()=>{
  const h=recordEdit(recordEdit(undefined,'a','b'),'other','new')
  expect(h.base_source).toBe('other');expect(replay(h)).toBe('new')
})
