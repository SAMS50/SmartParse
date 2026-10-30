import {act, fireEvent, render, screen, waitFor, within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {beforeEach, expect, test, vi} from 'vitest'
import App from './App'
import * as api from './lib/api'
import {examples, result} from './test-data'

const navigation = vi.hoisted(() => ({navigate:vi.fn()}))
vi.mock('./lib/api', () => ({health:vi.fn(),getExamples:vi.fn(),getTools:vi.fn(),analyze:vi.fn(),downloadReport:vi.fn()}))
vi.mock('./components/CodeEditor', async () => {
  const React = await import('react')
  return {CodeEditor:React.forwardRef(function FakeEditor(props: {value:string;onChange:(v:string)=>void;onCursor:(line:number,column:number)=>void;diagnostics:unknown[]},ref) {
    React.useImperativeHandle(ref,()=>({navigate:(at:{line:number;column:number})=>{navigation.navigate(at);props.onCursor(at.line,at.column)}}))
    return <><textarea aria-label="C source editor" value={props.value} onChange={e=>props.onChange(e.target.value)}/><span data-testid="marker-count">{props.diagnostics.length}</span></>
  }),RecoveredDiff:()=> <div>Hash-verified accepted preview</div>}
})

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(api.health).mockResolvedValue({status:'ok'})
  vi.mocked(api.getExamples).mockResolvedValue({examples})
  vi.mocked(api.getTools).mockResolvedValue({tools:[{name:'clang',status:'available',path:'mock-clang',version:'test version'}]})
  vi.mocked(api.analyze).mockResolvedValue(result())
})
async function ready() {render(<App/>);await waitFor(()=>expect(screen.getByRole('button',{name:'Analyze'})).toBeEnabled());await userEvent.click(screen.getByText('Examples (3)'))}
async function chooseNull() {await userEvent.click(screen.getByRole('button',{name:'Null pointer'}))}
async function submit() {await userEvent.click(screen.getByRole('button',{name:/^Analyze(?:\s|$)/}));await screen.findByRole('button',{name:'Dereference of null pointer'})}

test('loads real-gallery API data without running analysis',async()=>{await ready();expect(api.analyze).not.toHaveBeenCalled();expect(screen.getByText('No analysis results.')).toBeInTheDocument()})
test('editing is unsaved and does not trigger analyzers',async()=>{await ready();fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int changed;'}});expect(screen.getByText(/Unsaved editor changes/)).toBeInTheDocument();expect(api.analyze).not.toHaveBeenCalled()})
test('example selection changes source and analyzer defaults',async()=>{await ready();await chooseNull();expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue(examples[1].source);await submit();expect(api.analyze).toHaveBeenCalledWith(expect.objectContaining({source:examples[1].source,analyzers:['memory']}),expect.any(AbortSignal))})
test('settings select analyzers and explicit optional recovery',async()=>{await ready();await userEvent.click(screen.getByRole('button',{name:'Analysis settings'}));const dialog=screen.getByRole('dialog');await userEvent.click(within(dialog).getByLabelText(/Clang Static Analyzer/));await userEvent.click(within(dialog).getByLabelText(/Punctuation recovery/));await userEvent.click(within(dialog).getByRole('button',{name:'Apply configuration'}));await submit();expect(api.analyze).toHaveBeenCalledWith(expect.objectContaining({analyzers:['compiler','static'],recovery:true}),expect.any(AbortSignal))})
test('renders diagnostics with attribution and evidence',async()=>{await ready();await chooseNull();await submit();expect(screen.getByText('Clang Static Analyzer')).toBeInTheDocument();expect(screen.getByText('original-source')).toBeInTheDocument();expect(screen.getByText('return *p;')).toBeInTheDocument()})
test('clicking a diagnostic navigates the editor',async()=>{await ready();await chooseNull();await submit();await userEvent.click(screen.getByRole('button',{name:'Dereference of null pointer'}));expect(navigation.navigate).toHaveBeenCalledWith(expect.objectContaining({line:3,column:9}));expect(screen.getByText('Ln 3, Col 9')).toBeInTheDocument()})
test('changed source disables stale navigation and highlights',async()=>{await ready();await chooseNull();await submit();fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int newer;'}});expect(screen.getByText(/Source changed since this report/)).toBeInTheDocument();expect(screen.getByTestId('marker-count')).toHaveTextContent('0');expect(screen.getByRole('button',{name:'Dereference of null pointer'})).toBeDisabled()})
test('conditional finding and accepted candidate are not made unconditional',async()=>{vi.mocked(api.analyze).mockResolvedValue(result('repair-conditioned'));await ready();await userEvent.click(screen.getByRole('button',{name:'Recovery-assisted'}));await submit();expect(screen.getAllByText('repair-conditioned')).toHaveLength(2);expect(screen.getByText(/Machine fix-it and physical AST boundary/)).toBeInTheDocument();expect(screen.queryByText(/Reported score/)).not.toBeInTheDocument()})
test('backend errors are actionable without simulated results',async()=>{vi.mocked(api.analyze).mockRejectedValue(new Error('Clang unavailable'));await ready();await userEvent.click(screen.getByRole('button',{name:/^Analyze(?:\s|$)/}));expect(await screen.findByRole('alert')).toHaveTextContent('Clang unavailable');expect(screen.queryByText('Dereference of null pointer')).not.toBeInTheDocument()})
test('JSON and Markdown export use the actual retained result',async()=>{await ready();await chooseNull();await submit();await userEvent.click(screen.getByRole('button',{name:'Export JSON report'}));expect(api.downloadReport).toHaveBeenCalledWith(expect.objectContaining({schema:'smartparse.studio_response'}),'json');await userEvent.click(screen.getByRole('button',{name:'Export Markdown report'}));expect(api.downloadReport).toHaveBeenLastCalledWith(expect.anything(),'markdown')})
test('comparison reports actual execution with coverage qualifications',async()=>{await ready();await chooseNull();await submit();await userEvent.click(screen.getByRole('button',{name:'Comparison'}));expect(screen.getByText(/Cross-backend root equivalence/)).toBeInTheDocument();expect(screen.getByText(/Agreement is not proof/)).toBeInTheDocument()})
test('reset restores loaded source',async()=>{await ready();await userEvent.click(screen.getByRole('button',{name:'Valid C'}));fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int edit;'}});await userEvent.click(screen.getByRole('button',{name:'Reset code'}));expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue(examples[0].source)})
test('stop waiting aborts only the browser request and ignores a late response',async()=>{
  let resolve!:(value:ReturnType<typeof result>)=>void
  vi.mocked(api.analyze).mockImplementation(()=>new Promise(r=>{resolve=r}))
  await ready();await userEvent.click(screen.getByRole('button',{name:/^Analyze(?:\s|$)/}));await screen.findByText('Analyzing your source')
  await userEvent.click(screen.getByRole('button',{name:'Stop waiting'}));expect(screen.getByRole('status')).toHaveTextContent('server may finish its bounded run')
  await act(async()=>resolve(result()));expect(screen.queryByText('Dereference of null pointer')).not.toBeInTheDocument()
})


test('keyboard panel resizing preserves cursor, markers and editor instance',async()=>{
  await ready();await chooseNull();await submit()
  await userEvent.click(screen.getByRole('button',{name:'Dereference of null pointer'}))
  const editor=screen.getByRole('textbox',{name:'C source editor'})
  const divider=screen.getByRole('separator',{name:'Resize editor and diagnostics'})
  fireEvent.keyDown(divider,{key:'ArrowRight'});expect(divider).toHaveAttribute('aria-valuenow','60')
  expect(screen.getByRole('textbox',{name:'C source editor'})).toBe(editor)
  expect(screen.getByTestId('marker-count')).toHaveTextContent('1')
  expect(screen.getByText('Ln 3, Col 9')).toBeInTheDocument()
  const details=screen.getByRole('separator',{name:'Resize analysis details'})
  fireEvent.keyDown(details,{key:'ArrowUp'});expect(details).toHaveAttribute('aria-valuenow','164')
  await userEvent.click(screen.getByRole('button',{name:'Reset panel sizes'}))
  expect(divider).toHaveAttribute('aria-valuenow','58');expect(details).toHaveAttribute('aria-valuenow','144')
})

test('partial findings remain visible with an explicit coverage notice',async()=>{
  const report=result();report.report.status='partial';vi.mocked(api.analyze).mockResolvedValue(report)
  await ready();await chooseNull();await submit()
  expect(screen.getByText('Analysis partial.')).toBeInTheDocument()
  expect(screen.getByText(/Some passes may be blocked/)).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Dereference of null pointer'})).toBeEnabled()
})

test('filtering still controls diagnostic groups',async()=>{
  await ready();await chooseNull();await submit()
  await userEvent.type(screen.getByRole('textbox',{name:'Filter diagnostics'}),'not-present')
  expect(screen.getByText('No findings match this filter.')).toBeInTheDocument()
  await userEvent.clear(screen.getByRole('textbox',{name:'Filter diagnostics'}))
  expect(screen.getByRole('button',{name:'Dereference of null pointer'})).toBeInTheDocument()
})


test('blank start and New File create independent editable tabs',async()=>{
  await ready();expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('')
  fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int first;'}})
  await userEvent.click(screen.getByRole('button',{name:'New File'}))
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('')
  fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int second;'}})
  await userEvent.click(screen.getByRole('tab',{name:'untitled-1.c'}))
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('int first;')
  await userEvent.click(screen.getByRole('tab',{name:'untitled-2.c'}))
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('int second;')
  expect(api.analyze).not.toHaveBeenCalled()
})

test('rename validates extension and keeps edited contents',async()=>{
  await ready();fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int renamed;'}})
  await userEvent.click(screen.getByRole('button',{name:'Rename untitled-1.c'}))
  await userEvent.clear(screen.getByRole('textbox',{name:'File name'}));await userEvent.type(screen.getByRole('textbox',{name:'File name'}),'source.txt')
  await userEvent.click(screen.getByRole('button',{name:'Rename'}));expect(screen.getByRole('alert')).toHaveTextContent('.c or .h')
  await userEvent.clear(screen.getByRole('textbox',{name:'File name'}));await userEvent.type(screen.getByRole('textbox',{name:'File name'}),'my source.c')
  await userEvent.click(screen.getByRole('button',{name:'Rename'}))
  expect(screen.getByRole('tab',{name:'my source.c'})).toHaveAttribute('aria-selected','true')
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('int renamed;')
})

test('closing modified tabs requires an explicit discard decision',async()=>{
  await ready();fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int keep;'}})
  await userEvent.click(screen.getByRole('button',{name:'Close untitled-1.c'}))
  await userEvent.click(screen.getByRole('button',{name:'Keep editing'}))
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('int keep;')
  await userEvent.click(screen.getByRole('button',{name:'Close untitled-1.c'}))
  await userEvent.click(screen.getByRole('button',{name:'Close without saving'}))
  expect(screen.queryByRole('tab',{name:'untitled-1.c'})).not.toBeInTheDocument()
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('')
})

test('opening a local header reads contents without analysis',async()=>{
  await ready();const file=new File(['int declared;'],'local.h',{type:'text/plain'})
  Object.defineProperty(file,'arrayBuffer',{value:async()=>new TextEncoder().encode('int declared;').buffer})
  await userEvent.upload(document.querySelector('input[type=file]') as HTMLInputElement,file)
  expect(await screen.findByRole('tab',{name:'local.h'})).toBeInTheDocument()
  expect(screen.getByRole('textbox',{name:'C source editor'})).toHaveValue('int declared;')
  expect(api.analyze).not.toHaveBeenCalled()
})

test('Save and Ctrl+S request a source download',async()=>{
  const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{})
  vi.spyOn(URL,'createObjectURL').mockReturnValue('blob:download');vi.spyOn(URL,'revokeObjectURL').mockImplementation(()=>{})
  await ready();fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int downloaded;'}})
  await userEvent.click(screen.getByRole('button',{name:'Save'}))
  expect(screen.getByRole('status')).toHaveTextContent('Original disk file not overwritten')
  fireEvent.keyDown(window,{key:'s',ctrlKey:true});expect(click).toHaveBeenCalledTimes(2)
  click.mockRestore()
})


test('manual code submits the active buffer and reanalysis replaces stale results',async()=>{
  await ready();const input=screen.getByRole('textbox',{name:'C source editor'})
  fireEvent.change(input,{target:{value:'int main(void) { return 0 }'}});await submit()
  expect(api.analyze).toHaveBeenLastCalledWith(expect.objectContaining({filename:'untitled-1.c',source:'int main(void) { return 0 }'}),expect.any(AbortSignal))
  fireEvent.change(input,{target:{value:'int main(void) { return 0; }'}})
  expect(screen.getByText(/Source changed since this report/)).toBeInTheDocument()
  const clean=result();clean.report.diagnostics=[];clean.report.groups=[];clean.report.summary={...clean.report.summary,errors:0,warnings:0}
  vi.mocked(api.analyze).mockResolvedValue(clean)
  await userEvent.click(screen.getByRole('button',{name:'Analyze'}))
  expect(await screen.findByText('No primary diagnostics reported.')).toBeInTheDocument()
  expect(screen.queryByText(/Source changed since this report/)).not.toBeInTheDocument()
})

test('reports stay associated with their file and renames mark them stale',async()=>{
  await ready();await chooseNull();await submit()
  await userEvent.click(screen.getByRole('button',{name:'New File'}))
  expect(screen.queryByText('Dereference of null pointer')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('tab',{name:'null.c'}))
  expect(screen.getByRole('button',{name:'Dereference of null pointer'})).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button',{name:'Rename null.c'}))
  await userEvent.clear(screen.getByRole('textbox',{name:'File name'}));await userEvent.type(screen.getByRole('textbox',{name:'File name'}),'renamed.c')
  await userEvent.click(screen.getByRole('button',{name:'Rename'}))
  expect(screen.getByRole('button',{name:'Dereference of null pointer'})).toBeDisabled()
})

test('manual recovery preserves conditioned evidence without loading an example',async()=>{
  vi.mocked(api.analyze).mockResolvedValue(result('repair-conditioned'))
  await ready();fireEvent.change(screen.getByRole('textbox',{name:'C source editor'}),{target:{value:'int helper(void) { return 23 }'}})
  await userEvent.click(screen.getByRole('button',{name:'Analysis settings'}))
  await userEvent.click(screen.getByLabelText(/Punctuation recovery/));await userEvent.click(screen.getByRole('button',{name:'Apply configuration'}))
  await submit();expect(api.analyze).toHaveBeenLastCalledWith(expect.objectContaining({filename:'untitled-1.c',recovery:true}),expect.any(AbortSignal))
  expect(screen.getAllByText('repair-conditioned')).toHaveLength(2)
  expect(screen.getByText(/Accepted for a temporary analysis variant/)).toBeInTheDocument()
})
