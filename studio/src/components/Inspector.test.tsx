import {render, screen} from '@testing-library/react'
import {expect, test, vi} from 'vitest'
import {Inspector, type InspectorTab} from './Inspector'
import {result} from '../test-data'
import type {StudioResult} from '../types/report'

vi.mock('./CodeEditor',()=>({RecoveredDiff:()=> <div>Verified diff component</div>}))
function show(report:StudioResult,tab:InspectorTab='recovery') {
  render(<Inspector result={report} source="int x;" tab={tab} onTab={vi.fn()} height={320} onReset={vi.fn()}/> )
}

test('intent abstention, alternatives and supported impact remain explicit',()=>{
  const report=result()
  report.report.intent_recovery={decision:'ambiguous repair',reason:'Programmer confirmation is recommended.',recommendation:null,history_status:'Missing history',original_sha256:'source',candidates:[{
    id:'repair1',source:'int x;',status:'ambiguous repair',score:10,explanation:'Missing supported reference',
    changes:[{offset:5,end_offset:5,deleted:'',inserted:';',line:1,column:6}],
    validation:{status:'VALID',reason:''},history:{explanation:'No verified recent editing evidence'},
    semantic:{statement_ownership:{status:'UNKNOWN',explanation:'No supported valid reference'}}}]}
  report.report.intent_recovery.reliability={status:'verified replay',intent_support:'ambiguous: end-of-source block deletion',reason:'Verified replay',mapping_verified:true}
  report.report.intent_recovery.evidence_basis='valid historical structural comparison'
  show(report)
  expect(screen.getByText(/Evidence reliability: ambiguous: end-of-source block deletion/)).toBeInTheDocument()
  expect(screen.getByLabelText('Intent-aware recovery evidence')).toHaveTextContent('ambiguous repair')
  expect(screen.getByText('Syntax validation: VALID')).toBeInTheDocument()
  expect(screen.getByText(/statement_ownership: UNKNOWN/)).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Compare correction repair1'})).toBeInTheDocument()
})
test('overview exposes real execution, counts, duration, preservation and limits',()=>{
  show(result(),'overview')
  expect(screen.getByText('0 errors · 1 warning')).toBeInTheDocument()
  expect(screen.getByText('1.25 s')).toBeInTheDocument()
  expect(screen.getByText('Source preserved')).toBeInTheDocument()
  expect(screen.getByLabelText('Analyzer execution summary')).toHaveTextContent('memorycompleted')
  expect(screen.queryByText(/Completion does not certify/)).not.toBeInTheDocument()
})

test('adaptive evidence and Clang attribution distinguish unverified suggestions',()=>{
  const report=result()
  report.report.intent_recovery={decision:'suggested alternatives',decision_mode:'INSUFFICIENT_EVIDENCE',recommendation:null,
    reason:'Some alternatives remain unverified.',history_status:'Missing history',original_sha256:'hash',
    available_evidence:['compiler-validated syntax'],missing_evidence:['reliable edit history'],candidates:[{
      id:'unverified',source:'int x;',status:'unverified suggestion',score:0,explanation:'Not eligible for recommendation',
      changes:[],validation:{status:'UNVERIFIED',reason:'Compiler unavailable'},history:{explanation:'No history'},
      semantic:{},origins:['clang_fixit'],semantic_risk:{status:'CHECK_FAILED',reason:'Structural analysis did not complete'}}]}
  report.report.intent_recovery.candidates.push({...report.report.intent_recovery.candidates[0],id:'invalid',status:'rejected repair',validation:{status:'INVALID',reason:'Compiler rejected this source'}})
  show(report)
  expect(screen.getByText(/Available evidence: compiler-validated syntax/)).toBeInTheDocument()
  expect(screen.getAllByText(/Proposal from: Clang compiler/)).toHaveLength(2)
  expect(screen.getByText(/Unverified suggestion · unverified suggestion/)).toBeInTheDocument()
  expect(screen.getByText(/Rejected correction · rejected repair/)).toBeInTheDocument()
  expect(screen.queryByText('Suggested correction')).not.toBeInTheDocument()
})
test('no recovery evidence never produces a source preview',()=>{
  show(result())
  expect(screen.getByText(/No recovery pass was requested/)).toBeInTheDocument()
  expect(screen.getByText('No verified source comparison')).toBeInTheDocument()
  expect(screen.queryByText('Verified diff component')).not.toBeInTheDocument()
})
test.each([[';',2,11,'Insertion'],['',2,12,'Deletion'],[';',2,12,'Substitution']])(
  'machine range describes %s at %i:%i as %s', (replacement,end_line,end_column,kind)=>{
    const report=result('repair-conditioned'),candidate=report.report.runs[0].recovery!.candidates[0]
    candidate.fixit={start_line:2,start_column:11,end_line:Number(end_line),end_column:Number(end_column),replacement:String(replacement)}
    show(report)
    expect(screen.getByText(`C1 · ${kind}`)).toBeInTheDocument()
    expect(screen.getByText(/Accepted for a temporary analysis variant/)).toBeInTheDocument()
    expect(screen.getByText('repair-conditioned')).toBeInTheDocument()
    expect(screen.queryByText('Verified diff component')).not.toBeInTheDocument()
})
test('rejected candidate, abstention and missing ranges remain explicit',()=>{
  const report=result('repair-conditioned'),recovery=report.report.runs[0].recovery!
  recovery.stop_reason='ambiguous_boundary';recovery.candidates[0].status='rejected'
  show(report)
  expect(screen.getByText('C1 · Proposed edit (range unavailable)')).toBeInTheDocument()
  expect(screen.getByText('ambiguous_boundary')).toBeInTheDocument()
  expect(screen.getByText('Not applied to an accepted variant.')).toBeInTheDocument()
  expect(screen.queryByText(/Reported score/)).not.toBeInTheDocument()
})
test('actual preview and original syntax diagnostics are rendered independently',()=>{
  const report=result('repair-conditioned'),original=structuredClone(report.report.diagnostics[0])
  original.id='syntax';original.category='syntax';original.conditioning='original-source';original.message='Missing semicolon'
  report.report.diagnostics.unshift(original)
  report.studio.previews=[{run_id:'memory',variant_id:'V1',source:'int x;',sha256:'hash-verified-by-api',conditioning:'repair-conditioned',basis:'Existing accepted source hash'}]
  show(report)
  expect(screen.getByText('Original syntax diagnostics')).toBeInTheDocument()
  expect(screen.getByText('Missing semicolon')).toBeInTheDocument()
  expect(screen.getByText('Verified diff component')).toBeInTheDocument()
  expect(screen.getByText(/not unconditional baseline findings/)).toBeInTheDocument()
})
