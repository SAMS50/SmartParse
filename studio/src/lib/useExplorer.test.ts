import {act,cleanup,renderHook} from '@testing-library/react'
import {afterEach,beforeEach,expect,test,vi} from 'vitest'
import {EXPLORER_SESSION_KEY,useExplorer} from './useExplorer'

beforeEach(()=>{sessionStorage.removeItem(EXPLORER_SESSION_KEY);Object.defineProperty(window,'innerWidth',{value:1366,writable:true,configurable:true})})
afterEach(()=>{cleanup();vi.restoreAllMocks()})
test('session restores collapsed state and previous width',()=>{
  sessionStorage.setItem(EXPLORER_SESSION_KEY,JSON.stringify({collapsed:true,width:300}))
  const first=renderHook(useExplorer);expect(first.result.current.visible).toBe(false)
  act(()=>first.result.current.toggle());expect(first.result.current.width).toBe(300)
  first.unmount();const next=renderHook(useExplorer)
  expect(next.result.current.visible).toBe(true);expect(next.result.current.width).toBe(300)
})
test('resize is bounded and collapse does not discard width',()=>{
  const {result}=renderHook(useExplorer)
  act(()=>result.current.resize(1000));expect(result.current.width).toBe(360)
  act(()=>result.current.toggle());act(()=>result.current.toggle())
  expect(result.current.width).toBe(360)
  act(()=>result.current.resize(50));expect(result.current.width).toBe(180)
})
test('mobile drawer and desktop preference are independent',()=>{
  window.innerWidth=390;const {result}=renderHook(useExplorer)
  expect(result.current.visible).toBe(false)
  act(()=>result.current.toggle());expect(result.current.visible).toBe(true)
  act(()=>result.current.dismissMobile());expect(result.current.visible).toBe(false)
  act(()=>{window.innerWidth=1366;window.dispatchEvent(new Event('resize'))})
  expect(result.current.visible).toBe(true)
})
test('blocked session storage still permits in-memory toggling',()=>{
  vi.spyOn(Storage.prototype,'getItem').mockImplementation(()=>{throw new Error('blocked')})
  vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('blocked')})
  const {result}=renderHook(useExplorer)
  act(()=>result.current.toggle());expect(result.current.visible).toBe(false)
})
