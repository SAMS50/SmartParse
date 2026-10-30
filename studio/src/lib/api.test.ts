import {afterEach,expect,test,vi} from 'vitest'
import {analyze,downloadReport} from './api'
import {result} from '../test-data'
afterEach(()=>vi.unstubAllGlobals())
test('submits only the explicit source/settings with the local request header',async()=>{
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(result()),{status:200}));vi.stubGlobal('fetch',fetcher)
  const controller=new AbortController();await analyze({source:'int x;',filename:'input.c',analyzers:['compiler'],standard:'c11',recovery:false,isolation:false},controller.signal)
  expect(fetcher).toHaveBeenCalledWith('http://127.0.0.1:8000/api/analyze',expect.objectContaining({method:'POST',signal:controller.signal,headers:expect.objectContaining({'X-SmartParse-Studio':'1'})}))
})
test('preserves server timeout messages',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Analysis worker timed out'}),{status:504})))
  await expect(analyze({source:'',filename:'a.c',analyzers:['compiler'],standard:'c11',recovery:false,isolation:false},new AbortController().signal)).rejects.toThrow('timed out')
})
test('download keeps conditional provenance and all raw JSON evidence',async()=>{
  let captured:Blob | undefined
  vi.stubGlobal('URL',{createObjectURL:vi.fn((blob:Blob)=>{captured=blob;return 'blob:test'}),revokeObjectURL:vi.fn()})
  const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{})
  const answer=result('repair-conditioned');downloadReport(answer,'json')
  const text=await new Promise<string>(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result as string);reader.readAsText(captured!)})
  const exported=JSON.parse(text);expect(exported.report.diagnostics[0].conditioning).toBe('repair-conditioned');expect(exported.report.diagnostics[0].raw_record).toEqual(answer.report.diagnostics[0].raw_record)
  click.mockRestore()
})
