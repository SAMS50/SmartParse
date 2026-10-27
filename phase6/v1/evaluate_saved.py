"""Evaluate frozen GCC/Clang evidence; writes only Phase 6 v1 outputs.

Usage: python -m phase6.v1.evaluate_saved [--review FILE]
Without a review file, compatible evidence remains unreviewed/uncertain.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .evaluation import evaluate, fingerprint, normalize_runs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load_inputs():
    dataset = json.loads((HERE/'reference.json').read_text(encoding='utf-8'))
    source = ROOT / dataset['sources']['sample-500-cleaned']['path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != dataset['sources']['sample-500-cleaned']['sha256']:
        raise ValueError('current source differs from frozen reference')
    runs = []
    for rid, path in [('gcc-6.3', 'acceptance/output/sample.json'),
                      ('clang-17', 'acceptance/output/clang_validation/sample_static.json')]:
        artifact = ROOT/path
        report = json.loads(artifact.read_text(encoding='utf-8'))
        if report['execution']['command'][-1] != str(source):
            raise ValueError('compiler report is not bound to expected cleaned source')
        coverage = [{'source_id':'sample-500-cleaned','analysis':'compiler','status':'completed',
                     'reason':'Measured syntax/type invocation completed; not a guarantee of exhaustive compiler warnings.'},
                    {'source_id':'sample-500-cleaned','analysis':'logic','status':'unsupported','reason':'No general contract/logic checker enabled.'}]
        analyzer = report.get('static_analysis')
        coverage.append({'source_id':'sample-500-cleaned','analysis':'analyzer',
                         'status':'blocked' if analyzer and analyzer['status']=='partial' else 'unsupported',
                         'reason':'Clang analyzer frontend errors prevented path analysis.' if analyzer else 'No GCC analyzer pass requested/supported in baseline.'})
        runs.append({'id':rid,'artifact_path':path,'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
                     'source_bindings':{'sample-500-cleaned':{'reported_paths':[str(source)],'sha256':dataset['sources']['sample-500-cleaned']['sha256']}},
                     'coverage':coverage,'report':report})
    return dataset,runs


def empty_review(dataset,runs):
    return {'scope':{'dataset':fingerprint(dataset),'runs':fingerprint(runs)},
            'review_kind':'unreviewed','matches':[],'adjudications':[],'contracts':{}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path)
    args=parser.parse_args()
    dataset,runs=load_inputs()
    review=json.loads(args.review.read_text(encoding='utf-8')) if args.review else empty_review(dataset,runs)
    result=evaluate(dataset,runs,review)
    output=HERE/'outputs'
    output.mkdir(exist_ok=True)
    filename='evaluation_reviewed.json' if args.review else 'evaluation_unreviewed.json'
    (output/filename).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result['summary'],indent=2))


if __name__=='__main__': main()
