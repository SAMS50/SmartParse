"""Explicit provisional source review, preserving the old v1 reference exactly."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'outputs'


def main():
    reference_path=ROOT/'phase6/v1/reference.json';reference=json.loads(reference_path.read_text())
    defects={d['id']:d for d in reference['defects']};source=ROOT/'acceptance/cleaned/c_error_detection_500_lines.c'
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest==reference['sources']['sample-500-cleaned']['sha256']
    r=json.loads((OUT/'comparison/cppcheck/benchmark.json').read_text());assert r['source']['sha256']==digest
    # These are source-review bindings, not general detection heuristics.
    bindings={
      (129,'returnDanglingLifetime'):('SP6-L0129-01','Returned buffer is a local array; lifetime ends on return.'),
      (236,'returnDanglingLifetime'):('SP6-L0236-01','Returned address belongs to the local int.'),
      (263,'autoVariables'):('SP6-L0263-01','*pointer stores &value into caller-visible storage; value has automatic lifetime.'),
      (74,'bufferAccessOutOfBounds'):('SP6-L0074-01','Literal copied into error.message exceeds its 32-byte extent.'),
      (368,'incorrectLogicOperator'):('SP6-L0368-01','Date.month is an ordinary int; <1 and >12 cannot both hold. No OR-intent inference.'),
      (292,'invalidScanfArgType_int'):('SP6-L0292-01','%d requires int*; value is passed as int, not its address.'),
      (421,'invalidPrintfArgType_sint'):('SP6-L0421-01','%d expects int; total is long, even where widths coincide.'),
      (299,'invalidscanf'):('SP6-L0299-01','Eight-byte name with unbounded %s; external input-length contract remains unknown.'),
      (252,'doubleFree'):('SP6-L0252-01','Both calls free the same pointer, but nonnull owned-allocation entry contract is unresolved.'),
      (271,'memleak'):('SP6-L0271-01','Successful malloc allocation loses its only local owner at function exit without free.'),
      (287,'resourceLeak'):('SP6-L0287-01','Successful fopen path writes and exits without fclose.'),
      (307,'resourceLeak'):('SP6-L0307-01','Successful fopen branch returns 1 before closing the stream.'),
      (308,'nullPointer'):('SP6-L0308-01','Only the failed-open/null path reaches fclose: nonnull branch returned.'),
      (308,'nullPointerRedundantCheck'):('SP6-L0308-01','Same null fclose operation; redundant-check wording is not a separate root.'),
      (108,'nullPointerRedundantCheck'):('SP6-L0104-02','Assignment student=NULL at 104 is false; execution falls through to member access at 108.'),
      (134,'nullPointer'):('SP6-L0081-01','Concrete reset_student(NULL) call at 81 reaches first member store at 134.'),
      (134,'ctunullpointer'):('SP6-L0081-01','CTU call evidence confirms same null argument/sink; no second root.'),
      (135,'nullPointer'):('SP6-L0081-01','Same null argument in reset_student; later field operations are duplicates, not independent reachable paths.'),
      (136,'nullPointer'):('SP6-L0081-01','Same null argument/root as 134; no independent root credit.'),
      (137,'nullPointer'):('SP6-L0081-01','Same null argument/root as 134; no independent root credit.'),
      (99,'zerodiv'):('SP6-L0065-01','average(scores,0) at 65 supplies zero count to integer division at 99.'),
      (142,'zerodiv'):('SP6-L0078-01','unsafe_divide(5,0) at 78 supplies the zero divisor at 142.'),
      (404,'missingReturn'):('SP6-L0405-01','Source function 401–405 falls through on nonpositive values; consuming missing value remains a required unknown contract. Tool anchors return at 404, not old anchor 405.'),
    }
    # Roots already warned by current Clang or preserved GCC6; counting an
    # additional consequence at a shared warned root would inflate the gain.
    already_warned={'ROOT-L0074','ROOT-L0129','ROOT-L0236','ROOT-L0292','ROOT-L0421','ROOT-L0104'}
    legacy=json.loads((ROOT/'acceptance/output/sample.json').read_text())
    assert any(d['line']==421 and 'format' in d['message'] for d in legacy['diagnostics'])
    reviews=[];roots={};conditional=set();unknown=[]
    for d in r['diagnostics']:
        binding=bindings.get((d['line'],d['diagnostic_id']))
        if not binding:
            unknown.append(d['id']);reviews.append({'evidence_id':d['id'],'decision':'unknown','reason':'No strict source-reviewed reference binding; uninitialized return after invalid sscanf call is not automatically a separate root.'});continue
        did,rationale=binding;defect=defects[did];root=defect['root_cause_id']
        state='conditional_support' if defect['oracle_status']!='established' else 'agent_source_supported'
        duplicate=root in roots
        reviews.append({'evidence_id':d['id'],'reference_id':did,'root_id':root,'decision':state,
                        'same_root_duplicate':duplicate,'previously_warned_root':root in already_warned,
                        'outside_old_diagnostic_anchors':d['line'] not in defect['diagnostic_anchors'],
                        'reviewer':'Codex-source-review','rationale':rationale})
        if state=='conditional_support':conditional.add(did)
        else:roots.setdefault(root,[]).append(d['id'])
    result={'schema':'smartparse.external_benchmark_source_review','schema_version':'1.0','source_sha256':digest,
            'reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),'tool':'cppcheck 2.16.0',
            'tool_status':r['status'],'source_edits':False,'reviewer':'Codex-source-review','independent_human_review_pending':True,
            'scope':'Local potential operation defects; no successful whole-program execution past earlier undefined behavior is asserted.',
            'reviews':reviews,'source_supported_root_ids':sorted(roots),'previously_warned_source_supported_roots':sorted(set(roots)&already_warned),
            'new_source_supported_root_ids':sorted(set(roots)-already_warned),'conditional_reference_ids':sorted(conditional),
            'unmatched_unknown_evidence_ids':unknown,'root_duplicate_records':sum(max(0,len(e)-1) for e in roots.values()),
            'region_coverage':'unknown; tool completion and findings do not certify every region or path',
            'precision':None,'recall':None,'historical_scores_replaced':False}
    (OUT/'benchmark_source_review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(len(roots),'supported roots;',len(result['new_source_supported_root_ids']),'new vs warned roots;',len(conditional),'conditional;',len(unknown),'unknown')


if __name__=='__main__':main()
