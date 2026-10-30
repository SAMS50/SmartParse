import {expect,test} from 'vitest'
import {serviceReady} from './serviceReady'
const clang={name:'clang',status:'available',path:'test-clang',version:'test-version'}
test('unreachable/checking service never shows Ready',()=>{
  expect(serviceReady(false,false,['compiler'],[clang])).toBe(false)
  expect(serviceReady(true,true,['compiler'],[clang])).toBe(false)
})
test('only selected dependencies are required',()=>{
  expect(serviceReady(true,false,['compiler'],[clang])).toBe(true)
  expect(serviceReady(true,false,['static'],[])).toBe(false)
  expect(serviceReady(true,false,['gcc14'],[clang])).toBe(false)
  expect(serviceReady(true,false,['smartparse'],[])).toBe(true)
})
test('unavailable inventory entry does not count as available',()=>{
  expect(serviceReady(true,false,['memory'],[{...clang,status:'unavailable'}])).toBe(false)
})
