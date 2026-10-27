"""Independent synthetic evidence tests; no compiler or source mutation."""
import copy
import json
from pathlib import Path
import unittest

from phase6.v1.evaluation import evaluate, fingerprint, normalize_runs, validate_dataset


def fixture(*, oracle='established', contract=False, coverage='completed'):
    defect = {'id':'ATOM-A','historical_entry':1,'source_id':'unit','category':'memory safety',
              'source_locations':[10],'sink_locations':[20],'diagnostic_anchors':[20],
              'triggering_conditions':['the allocation has been released'],
              'required_contracts':[{'id':'C1','statement':'nonnull owning allocation'}] if contract else [],
              'oracle_status':oracle,'required_analysis':'analyzer','root_cause_id':'ROOT-A','relationships':[],
              'admissible_evidence':{'meaning':'use of a freed allocation',
                  'rules':[{'backends':['clang-static-analyzer'],'severities':['warning'],'message_all':[r'use.*after.*free|freed memory']}]}}
    dataset={'schema_version':'1.0','dataset_version':'1.0.0','sources':{'unit':{'sha256':'abc'}},
             'historical_baseline':{'entries':1},'defects':[defect]}
    diagnostic={'file':'C:\\new project\\unfamiliar.c','line':20,'column':2,'severity':'warning',
                'message':'Use of memory after it is freed','backend':'clang-static-analyzer',
                'category':'unknown','source_snippet':'return *p;','diagnostic_id':'unix.Malloc'}
    runs=[{'id':'run','source_bindings':{'unit':{'sha256':'abc','reported_paths':[diagnostic['file']]}},
           'coverage':[{'source_id':'unit','analysis':'analyzer','status':coverage,'reason':'test state'}],
           'report':{'diagnostics':[diagnostic]}}]
    return dataset,runs


def review_for(dataset,runs,decision=None):
    evidence,_,_=normalize_runs(dataset,runs)
    review={'scope':{'dataset':fingerprint(dataset),'runs':fingerprint(runs)},'matches':[],'adjudications':[],'contracts':{}}
    if decision:
        review['matches']=[{'defect_id':'ATOM-A','evidence_id':next(iter(evidence)),
                            'decision':decision,'reviewer':'independent test reviewer','rationale':'Inspected release and use evidence.'}]
    return review


class EvidenceModelTests(unittest.TestCase):
    def test_meaning_candidate_requires_review(self):
        data,runs=fixture()
        result=evaluate(data,runs,review_for(data,runs))
        self.assertEqual(result['defects'][0]['outcome'],'uncertain')
        self.assertEqual(result['summary']['detected_root_cause_count'],0)

    def test_reviewed_semantic_match_detected(self):
        data,runs=fixture()
        self.assertEqual(evaluate(data,runs,review_for(data,runs,'match'))['defects'][0]['outcome'],'detected')

    def test_same_line_wrong_meaning_is_not_detection(self):
        data,runs=fixture()
        runs[0]['report']['diagnostics'][0]['message']="use of undeclared identifier 'p'"
        result=evaluate(data,runs,review_for(data,runs))
        self.assertEqual(result['defects'][0]['outcome'],'missed')
        self.assertEqual(result['findings'][0]['disposition'],'unknown')
        with self.assertRaises(ValueError):
            evaluate(data,runs,review_for(data,runs,'match'))

    def test_note_cannot_confirm_or_be_false_positive(self):
        data,runs=fixture()
        runs[0]['report']['diagnostics'][0]['severity']='note'
        review=review_for(data,runs)
        result=evaluate(data,runs,review)
        self.assertEqual(result['findings'][0]['disposition'],'context_note')
        self.assertEqual(result['defects'][0]['outcome'],'missed')
        review['adjudications']=[{'evidence_id':result['findings'][0]['evidence_id'],'decision':'false_positive',
                                  'reviewer':'reviewer','rationale':'invalid','finding_group_id':'FP1'}]
        with self.assertRaises(ValueError): evaluate(data,runs,review)

    def test_exact_duplicate_does_not_multiply_evidence(self):
        data,runs=fixture()
        runs[0]['report']['diagnostics']*=2
        result=evaluate(data,runs,review_for(data,runs,'match'))
        self.assertEqual(len(result['findings']),1)
        self.assertEqual(result['summary']['exact_duplicates_not_counted'],1)
        self.assertEqual(result['summary']['outcomes']['detected'],1)

    def test_cross_backend_evidence_preserved_single_atom(self):
        data,runs=fixture()
        other=copy.deepcopy(runs[0]); other['id']='other-backend'
        runs.append(other)
        review=review_for(data,runs)
        for eid in normalize_runs(data,runs)[0]:
            review['matches'].append({'defect_id':'ATOM-A','evidence_id':eid,'decision':'match','reviewer':'reviewer','rationale':'same atomic issue'})
        result=evaluate(data,runs,review)
        self.assertEqual(len(result['findings']),2)
        self.assertEqual(result['summary']['detected_root_cause_count'],1)

    def test_conditions_not_assumed_from_diagnostic(self):
        data,runs=fixture(oracle='conditional',contract=True)
        review=review_for(data,runs,'match')
        self.assertEqual(evaluate(data,runs,review)['defects'][0]['outcome'],'conditional')
        review['contracts']['C1']={'state':'satisfied','reviewer':'contract reviewer','rationale':'Explicit caller precondition verified'}
        self.assertEqual(evaluate(data,runs,review)['defects'][0]['outcome'],'detected')

    def test_refuted_contract_not_counted_detected(self):
        data,runs=fixture(oracle='conditional',contract=True)
        review=review_for(data,runs,'match')
        review['contracts']['C1']={'state':'refuted','reviewer':'reviewer','rationale':'Caller guarantees a different state'}
        self.assertEqual(evaluate(data,runs,review)['defects'][0]['outcome'],'conditional')

    def test_uncertain_reference_stays_uncertain(self):
        data,runs=fixture(oracle='uncertain')
        self.assertEqual(evaluate(data,runs,review_for(data,runs,'match'))['defects'][0]['outcome'],'uncertain')

    def test_blocked_not_missed(self):
        data,runs=fixture(coverage='blocked'); runs[0]['report']['diagnostics']=[]
        self.assertEqual(evaluate(data,runs,review_for(data,runs))['defects'][0]['outcome'],'blocked')

    def test_unsupported_distinct_from_unknown_coverage(self):
        for status,expected in [('unsupported','unsupported'),('unknown','uncertain')]:
            data,runs=fixture(coverage=status); runs[0]['report']['diagnostics']=[]
            self.assertEqual(evaluate(data,runs,review_for(data,runs))['defects'][0]['outcome'],expected)

    def test_ambiguous_review_not_detection(self):
        data,runs=fixture()
        self.assertEqual(evaluate(data,runs,review_for(data,runs,'ambiguous'))['defects'][0]['outcome'],'uncertain')

    def test_unmatched_is_unknown_not_false_positive(self):
        data,runs=fixture(); runs[0]['report']['diagnostics'][0]['message']='unlisted potential issue'
        result=evaluate(data,runs,review_for(data,runs))
        self.assertEqual(result['findings'][0]['disposition'],'unknown')
        self.assertEqual(result['summary']['confirmed_false_positive_group_count'],0)

    def test_false_positive_requires_explicit_adjudication(self):
        data,runs=fixture(); review=review_for(data,runs)
        eid=next(iter(normalize_runs(data,runs)[0]))
        review['adjudications']=[{'evidence_id':eid,'decision':'false_positive','reviewer':'reviewer',
                                  'rationale':'release did not occur on the reported feasible path','finding_group_id':'FP-1'}]
        result=evaluate(data,runs,review)
        self.assertEqual(result['summary']['confirmed_false_positive_group_count'],1)
        self.assertIsNone(result['metrics']['precision'])

    def test_cascade_adjudication_never_confirms(self):
        data,runs=fixture(); review=review_for(data,runs)
        eid=next(iter(normalize_runs(data,runs)[0]))
        review['adjudications']=[{'evidence_id':eid,'decision':'cascade','reviewer':'reviewer','rationale':'caused by rejected declaration'}]
        self.assertEqual(evaluate(data,runs,review)['defects'][0]['outcome'],'missed')

    def test_wrong_source_same_basename_not_matched(self):
        data,runs=fixture(); runs[0]['report']['diagnostics'][0]['file']='D:\\other\\unfamiliar.c'
        self.assertEqual(evaluate(data,runs,review_for(data,runs))['defects'][0]['outcome'],'missed')

    def test_changed_source_hash_rejected(self):
        data,runs=fixture(); runs[0]['source_bindings']['unit']['sha256']='different'
        with self.assertRaises(ValueError): evaluate(data,runs,review_for(data,runs))

    def test_stale_review_rejected(self):
        data,runs=fixture(); review=review_for(data,runs,'match')
        runs[0]['report']['diagnostics'][0]['message']='changed evidence'
        with self.assertRaises(ValueError): evaluate(data,runs,review)

    def test_one_diagnostic_cannot_confirm_two_atoms(self):
        data,runs=fixture(); second=copy.deepcopy(data['defects'][0]); second['id']='ATOM-B'; data['defects'].append(second)
        review=review_for(data,runs,'match'); extra=copy.deepcopy(review['matches'][0]); extra['defect_id']='ATOM-B'; review['matches'].append(extra)
        with self.assertRaises(ValueError): evaluate(data,runs,review)

    def test_shared_root_is_not_two_independent_defects(self):
        data,runs=fixture(); second=copy.deepcopy(data['defects'][0]); second.update(id='ATOM-B',diagnostic_anchors=[30]); data['defects'].append(second)
        diagnostic=copy.deepcopy(runs[0]['report']['diagnostics'][0]); diagnostic['line']=30; runs[0]['report']['diagnostics'].append(diagnostic)
        review=review_for(data,runs)
        for eid,item in normalize_runs(data,runs)[0].items():
            review['matches'].append({'defect_id':'ATOM-A' if item['diagnostic']['line']==20 else 'ATOM-B','evidence_id':eid,
                                     'decision':'match','reviewer':'reviewer','rationale':'two manifestations, shared root'})
        result=evaluate(data,runs,review)
        self.assertEqual(result['summary']['outcomes']['detected'],2)
        self.assertEqual(result['summary']['detected_root_cause_count'],1)

    def test_real_reference_lineage_and_json(self):
        data=json.loads((Path(__file__).parent/'reference.json').read_text(encoding='utf-8'))
        validate_dataset(data)
        self.assertEqual(len(data['defects']),76)
        self.assertEqual(data['historical_baseline']['clang_matched_entries'],16)
        for line,count in [(55,2),(71,2),(104,2),(278,2),(317,2),(432,3),(439,2)]:
            self.assertEqual(len([d for d in data['defects'] if d['historical_line']==line]),count)

    def test_producer_warning_cannot_confirm_downstream_use(self):
        from phase6.v1.evaluation import admissible
        data=json.loads((Path(__file__).parent/'reference.json').read_text(encoding='utf-8'))
        use=next(d for d in data['defects'] if d['id']=='SP6-L0071-02')
        evidence={'source_id':use['source_id'],'diagnostic':{'line':129,'severity':'warning','backend':'clang',
                  'message':"address of stack memory associated with local variable 'buffer' returned"}}
        self.assertFalse(admissible(use,evidence))

    def test_checker_identifier_can_restrict_evidence(self):
        data,runs=fixture()
        data['defects'][0]['admissible_evidence']['rules'][0]['identifiers']=['other.Checker']
        self.assertEqual(evaluate(data,runs,review_for(data,runs))['defects'][0]['outcome'],'missed')

    def test_duplicate_false_positive_backends_share_one_adjudicated_group(self):
        data,runs=fixture(); extra=copy.deepcopy(runs[0]); extra['id']='backend-2'; runs.append(extra)
        review=review_for(data,runs)
        for eid in normalize_runs(data,runs)[0]:
            review['adjudications'].append({'evidence_id':eid,'decision':'false_positive','reviewer':'reviewer',
                'rationale':'Both records report the same infeasible path','finding_group_id':'FP-ONE'})
        self.assertEqual(evaluate(data,runs,review)['summary']['confirmed_false_positive_group_count'],1)

    def test_contract_satisfaction_requires_attributed_review(self):
        data,runs=fixture(oracle='conditional',contract=True); review=review_for(data,runs,'match')
        review['contracts']['C1']={'state':'satisfied'}
        with self.assertRaises(ValueError): evaluate(data,runs,review)

    def test_saved_assisted_review_remains_auditable(self):
        from phase6.v1.evaluate_saved import load_inputs
        data,runs=load_inputs()
        review=json.loads((Path(__file__).parent/'assisted_review.json').read_text(encoding='utf-8'))
        result=evaluate(data,runs,review)
        self.assertEqual(result['summary']['outcomes']['detected'],12)
        self.assertEqual(sum(result['summary']['outcomes'].values()),76)
        self.assertEqual(len(result['findings']),62)
        self.assertEqual(json.loads(json.dumps(result))['summary'],result['summary'])
        self.assertEqual(result['summary']['finding_dispositions']['cascade'],4)

    def test_explicit_semantic_review_can_accept_new_wording(self):
        data,runs=fixture()
        runs[0]['report']['diagnostics'][0]['message']='Allocation lifetime ended before this access'
        review=review_for(data,runs,'match')
        review['matches'][0]['semantic_override']={'claim':'use of freed allocation',
            'evidence_explanation':'Reviewed path trace establishes release before the access; new wording has no regex rule.'}
        result=evaluate(data,runs,review)
        self.assertEqual(result['defects'][0]['outcome'],'detected')
        self.assertIn('semantic_override',result['review']['matches'][0])

    def test_semantic_override_cannot_bypass_source_scope(self):
        data,runs=fixture(); runs[0]['report']['diagnostics'][0]['file']='different.c'
        review=review_for(data,runs,'match')
        review['matches'][0]['semantic_override']={'claim':'a defect','evidence_explanation':'wrong source'}
        with self.assertRaises(ValueError): evaluate(data,runs,review)


if __name__=='__main__': unittest.main()
