import type {AnalysisInput, Example, StudioResult, Tool} from '../types/report'
const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(BASE + path, init)
  let body: unknown
  try { body = await response.json() } catch { throw new Error(`Backend returned an unreadable response (${response.status}).`) }
  if (!response.ok) {
    const detail = (body as {detail?: unknown}).detail
    const message = Array.isArray(detail) ? detail.map(x => x.msg).join('; ') : String(detail || `Request failed (${response.status})`)
    throw new Error(message)
  }
  return body as T
}

export const health = () => request<{status: string}>('/api/health', {signal: AbortSignal.timeout(3000)})
export const getTools = () => request<{tools: Tool[]}>('/api/tools')
export const getExamples = () => request<{examples: Example[]}>('/api/examples')
export async function analyze(input: AnalysisInput, signal: AbortSignal) {
  const result = await request<StudioResult>('/api/analyze', {method: 'POST', signal,
    headers: {'Content-Type': 'application/json', 'X-SmartParse-Studio': '1'}, body: JSON.stringify(input)})
  if (result.schema !== 'smartparse.studio_response' || result.report.schema !== 'smartparse.unified_analysis') throw new Error('Unsupported backend report schema.')
  return result
}

export function downloadReport(result: StudioResult, format: 'json' | 'markdown') {
  const text = format === 'json' ? JSON.stringify(result, null, 2) : result.markdown + '\n\n## Complete machine evidence\n\n```json\n' + JSON.stringify(result.report, null, 2) + '\n```\n'
  const url = URL.createObjectURL(new Blob([text], {type: format === 'json' ? 'application/json' : 'text/markdown;charset=utf-8'}))
  const link = document.createElement('a'); link.href = url
  link.download = `${result.studio.filename.replace(/\.c$/i, '')}.smartparse.${format === 'json' ? 'json' : 'md'}`
  link.click(); URL.revokeObjectURL(url)
}
