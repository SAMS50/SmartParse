"""Render research reports from safe observed records; never include student code."""
from collections import Counter
import json
from pathlib import Path
from .engine import frozen_engine_hash

ROOT=Path(__file__).resolve().parent


def frac(r):return f"{r['numerator']}/{r['denominator']}"+(' (unavailable)' if not r['denominator'] else '')


def table_systems(data):
    lines=['| System | Exact | Token match | Wrong exact match | Recommendations | Abstentions | Top-3 exact | Accuracy among recommendations |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,s in data['systems'].items():lines.append('| '+name+' | '+' | '.join(frac(s[k]) for k in ('exact','token_match','wrong','recommended','abstained','top3','accuracy_when_recommended'))+' |')
    return lines


def main():
    dev=json.loads((ROOT/'results/development.json').read_text(encoding='utf-8'))
    final=json.loads((ROOT/'results/final.json').read_text(encoding='utf-8'))
    lock=json.loads((ROOT/'experiment-lock.json').read_text(encoding='utf-8'))
    if any(d['frozen_engine_hash']!=frozen_engine_hash() for d in (dev,final)) or lock['engine_hash']!=frozen_engine_hash():raise ValueError('Recovery engine differs from frozen experiments')
    primary=[r for r in final['cases'] if r['category']=='A'];n=len(primary);full=final['systems']['full'];base=final['systems']['existing']
    lines=['# Milestone 13 evaluation: genuine student C errors','',
        '**No measurable advantage for full intent-aware recovery is demonstrated on this sample.** The frozen full mode abstains on every primary case. Existing scoring and Clang machine fixes recover the same number of exact references. Reduced wrong recommendations are achieved by zero recommendation coverage, not useful selective recovery.','',
        '## Provenance and denominators','',
        'Pinned TEGCER archive: 21,995 upstream human-pair records; 100 deterministic inferred families selected, without compiler-outcome filtering. Development has 20 category-A pairs. The final sample has 79 category-A pairs and one category-B pair whose published correction is not accepted locally. No synthetic cases enter primary metrics. There are zero actual recorded prior histories or usable earlier snapshots; corrected endpoints are future information and are never recovery inputs. See `REAL_WORLD_DATASET.md` and the frozen manifest.','',
        'Primary intended-repair denominator is final category A only. A verifies source rejection and corrected compilation on the same compiler, not assignment/behavioral correctness. B remains in compatibility and qualitative records, never silently mixed into accuracy. Family deduplication is inferred from token structure, not verified assignment/student identity.','',
        '## Development outcomes (separate from final)','',*table_systems(dev),'',
        'No recovery tuning followed development outcomes. The preregistered engine, 24-candidate/240-trial budgets and margin 12 remain unchanged.','',
        '## Final primary outcomes','',*table_systems(final),'',
        'Every ablation receives the identical candidate pool. All 24 eligible candidate pools have one valid program, all with seven UNKNOWN semantic checks; full/semantic modes cannot certify supported structure. The other 55 A cases have no validated candidate. Exact intended-candidate coverage and top-3 coverage are both 20/79. These are pool limitations, not evidence that a different ranking of many candidates would solve them.','',
        f"Existing-score recommendations compile independently in {frac(base['compilation_when_recommended'])}; compilable exact-intent mismatches are {frac(base['compilable_incorrect'])}. One of the four exact mismatches is token-equivalent, three differ in tokens; none has established behavioral equivalence. Full-mode conditional accuracy and conditional compilation are undefined (0 recommendations), not perfect. No student program or compiled binary was executed.",'',
        '## Research questions','',
        '* RQ1: no improved intended-repair accuracy: full 0/79 versus existing 20/79.',
        '* RQ2: wrong exact-source recommendations fall from 4/79 to 0/79, but coverage falls from 24/79 to 0/79. Useful coverage is not maintained.',
        '* RQ3: not identifiable without real prior editing history. Equal zero outcomes across enhanced modes do not establish that history is useless.',
        '* RQ4: Clang produces 36/79 applicable edit bundles, 24/36 compile and 20/36 exactly match the correction. Existing scoring exactly matches on the same 20 cases. Installed GCC 6.3 has no supported machine fix-it mode; diagnostic rejection remains separately reported.',
        '* RQ5: supported-subset and candidate-generation failures dominate; detailed category/length/diagnostic-count breakdowns follow. No claim generalizes to all C or all students.','',
        '## Generalization breakdowns','',
        '| Dimension | Group | N | Existing exact | Full exact | Full recommendations | Mean engine ms |','|---|---|---:|---:|---:|---:|---:|']
    for dimension in ('error_category','length','error_diagnostics','plausible_candidates','compiler_compatibility','semantic_unknown','history'):
        for name,group in final['subgroups'][dimension].items():
            lines.append(f"| {dimension} | {name} | {group['n']} | {frac(group['systems']['existing']['exact'])} | {frac(group['systems']['full']['exact'])} | {frac(group['systems']['full']['recommended'])} | {group['engine_runtime_ms']['mean']:.2f} |")
    lines+=['','Error categories are deterministic diagnostic-keyword labels, not independent human annotations. Error counts are emitted error-diagnostic counts and may include cascades, not counts of independent defects. Each selected source family contributes one case; all are from TEGCER, so a second source-project comparison is unavailable.','',
        '## Uncertainty and paired comparisons','',
        f"Existing exact rate: {base['exact']['estimate']:.3f}, Wilson 95% interval [{base['exact']['wilson95'][0]:.3f}, {base['exact']['wilson95'][1]:.3f}]. Full exact and wrong rates are both zero, Wilson upper bound {full['exact']['wilson95'][1]:.3f}; zero wrong predictions with no recommendations provide no conditional safety guarantee.",'',
        'Paired 2,000-replicate seeded family-bootstrap exact-rate differences:','',
        '| Left → right | Mean difference | 95% percentile interval | Right-only / left-only successes |','|---|---:|---|---|']
    pairs=[*final['paired_comparisons'].values(),*final['paired_compiler_comparisons'].values(),final['history_beyond_semantic']]
    for p in pairs:lines.append(f"| {p['left']} → {p['right']} | {p['mean_difference']:.3f} | {p['interval95']} | {p['right_only']} / {p['left_only']} |")
    lines+=['','Intervals describe this sampled family distribution under approximate independence. Inferred families may share assignments/templates, and the deterministic representative rule is not uniform sampling of all errors. No formal significance or population-wide superiority/non-inferiority claim is made. Degenerate zero/zero comparisons are not evidence of equivalence.','',
        '## Selective prediction','',
        'Diagnostic-only post-hoc selectors retain existing issued recommendations whose finite top-two score gap exceeds a threshold; singleton pools have infinite gaps. They never issue previously withheld predictions or tune the deployed policy.','',
        '| Minimum gap | Existing coverage | Existing selective accuracy | Full coverage | Full selective accuracy |','|---:|---:|---:|---:|---:|']
    for threshold in ('0','12','60','120','240'):
        a=final['selective_diagnostic_curves']['existing'][threshold];b=final['selective_diagnostic_curves']['full'][threshold]
        lines.append('| '+threshold+' | '+' | '.join((frac(a['coverage']),frac(a['accuracy']),frac(b['coverage']),frac(b['accuracy'])))+' |')
    lines+=['','The curve is flat because valid candidate pools are singletons. Margin calibration cannot recover missing candidates or resolve unsupported semantics. Abstention changes across the main policies are explicitly reported rather than treated as accuracy at equal coverage.','',
        '## Runtime and resources','',
        '| Measurement | N | Mean ms | Median ms | p95 ms |','|---|---:|---:|---:|---:|']
    for name,d in [('Shared SmartParse full evidence construction',final['runtime_ms']),*[(n+' original diagnostics',r['original_runtime_ms']) for n,r in final['compiler_comparison'].items()]]:
        lines.append(f"| {name} | {d['n']} | {d['mean']:.2f} | {d['median']:.2f} | {d['p95']:.2f} |")
    inv=final['compiler_invocations']
    lines+=['',f"SmartParse compiler calls per A input: mean {inv['mean']:.2f}, median {inv['median']}, p95 {inv['p95']}. Public records include retained candidate/source-byte counts and compiler stdout/stderr byte counts. Peak RSS and process-tree CPU are not instrumented on this Windows run (null, never assumed zero). End-to-end evidence time is shared across ablations; tiny per-mode ranking times are reported separately. Compiler diagnostic timing excludes fix-it validation, reference validation and capability probes; these scopes are not presented as equivalent work or a speedup claim. Single-run timings include startup, filesystem and concurrent test activity.",'',
        '## Reproduction and limitations','',
        'Use the commands in `MILESTONE_13_REPORT.md`. Acquisition is pinned by revision and SHA-256. Raw original/corrected source and private diagnostics are kept locally; public reports contain only hashes, aggregates and safe metadata. Known threats: one novice dataset, screen/compatibility bias, inferred families, missing history, no behavioral oracle, old GCC profile, and an intentionally narrow recovery subset. Results falsify generalization on this sample rather than justify a claim of research superiority.','']
    (ROOT/'EVALUATION_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    compiler=['# GCC/Clang comparison','',
        'No student binary is linked or executed. Source is copied to an evaluator-owned temporary `input.c`; only standard headers and simple numeric defines are allowed. The bounded runner has a three-second call limit and process-tree timeout cleanup. This is not an OS sandbox; trusted compilers can read local headers. Actual commands and raw diagnostics are private; public commands explicitly substitute `$COMPILER` and `<INPUT.C>` for local paths.','',
        '## Observed identities and capability probes','']
    for name,identity in final['compiler_identities'].items():compiler.extend([f"* {name}: `{identity['version']}`; status {identity['status']}; fix-its: {identity['fixit_format']}.",f"  Arguments: `{identity['flags']} <INPUT.C>`."])
    compiler+=['','The parseable-fix-it flag was probed on valid test-owned C before corpus use. GCC 6.3 rejects the flag, so it is omitted; no GCC diagnostic prose is converted to a repair. Clang structured physical edit records are parsed by existing policy helpers. Diagnostics retain parsed severity/location/category plus private original messages and exact byte counts. Lack of JSON diagnostics does not turn prose into an applicable edit.','',
        '## Actual primary results','',
        '| Split / tool | Diagnostic rejection | Applicable bundles / A | Exact / A | Exact / applicable | Token match / applicable | Compiles / validated applicable |','|---|---:|---:|---:|---:|---:|---:|']
    for split,data in (('Development',dev),('Final',final)):
        for name,s in data['compiler_comparison'].items():compiler.append('| '+split+' / '+name+' | '+' | '.join(frac(s[k]) for k in ('diagnostic_rejection','applicable_output_coverage','exact_over_all_A','exact_when_applicable','token_when_applicable','compile_when_applicable'))+' |')
    compiler+=['','Reference-compatibility-conditioned final results (rather than silently counting incompatible reference dialects as repair failures):','',
               '| Tool | A references accepted by this tool | Applicable outputs | Exact repairs |','|---|---:|---:|---:|']
    for name in ('gcc','clang'):
        compatible=[r for r in primary if r['reference_compatibility'][name] is True]
        compiler.append(f"| {name} | {len(compatible)} | {sum(r['compilers'][name]['applicable'] for r in compatible)}/{len(compatible)} | {sum(r['compilers'][name]['exact'] for r in compatible)}/{len(compatible)} |")
    compiler+=['','Diagnostic rejection is a compatibility-specific compiler response, not human-rated message quality or automatic-repair accuracy. GCC accepts one final category-A source that Clang rejects under these settings. Exact intended accuracy for GCC conditioned on available repair output has denominator zero and is unavailable; 0/A output coverage does not penalize its diagnostic quality. A modern GCC may expose different capabilities, so these observations apply to the recorded installation only.','',
        'Fix-its must target the explicitly mapped physical input, have valid UTF-8 byte boundaries and nonoverlapping ranges, and fit a 24-edit bound. Duplicate/overlapping hints are rejected conservatively rather than guessed. Applicable means the extracted bundle can be applied, not that it compiles or is intended. On final A inputs, 36 Clang bundles apply, 24 compile, 20 exactly match, 21 are token-equivalent, and 12 still fail compilation. Four compiling outputs differ exactly from the reference; one is token-equivalent. Compilation, token match and behavioral equivalence are distinct.','',
        'Corrected-reference diagnostics never enter SmartParse. References are compiled only after the recovery boundary finishes, using separate compiler calls. Raw/normalized source hashes are verified on ingestion. Individual per-case application and compilation outcomes are in `results/final.json`; private raw diagnostics include source snippets and are intentionally excluded from Git.','']
    (ROOT/'COMPILER_COMPARISON.md').write_text('\n'.join(compiler),encoding='utf-8')
    empty=sum(r['systems']['full']['candidates']==0 for r in primary)
    invalid=sum(r['systems']['full']['candidates']>0 and r['systems']['full']['valid_candidates']==0 for r in primary)
    failures=['# Real-world failure analysis','',
        f'Final primary set: {n} A cases. {empty} have an empty generated pool; {invalid} generate programs but none validates; 24 have one validated program with seven UNKNOWN semantic checks. Full mode abstains on all. No candidate-budget truncation is reported. This does not imply exhaustive coverage: generation is deliberately restricted to existing rules/fix-its and bounded supplements.','',
        '## Root causes','',
        '* All 24 validated pools retain preprocessing directives. The frozen semantic projection rejects preprocessing before claiming preservation; history is also missing. These are unsupported-analysis abstentions, not proven safety failures.',
        '* Candidate coverage is only 20/79 exact intended programs. Header-bearing full C bypasses much of the custom lexer/grammar search, and identifier/type, expression and multi-diagnostic errors often lack applicable complete fixes.',
        '* Four existing-score outputs compile but differ from intended text: `3a49b8cd3127bac31f6fb79f`, `baac60b36d43bc0a34566abc`, `a4bb70e0d77b8dbd3bcf6653`, `d0c8e27867f77176cdb1bd35`. The second is token-equivalent; the others differ in tokens. No behavioral oracle justifies calling them semantically wrong/equivalent.',
        '* Valid pools are singletons, so changing relative ranking or margin cannot supply missing evidence. The full policy avoids four exact mismatches by withholding twenty correct repairs too. This is not useful coverage-preserving error reduction.',
        '* Final case `c23cde4be2a55ede8b3da081` is category B: both installed compilers reject its target. Its intended-repair label remains locally unverified and is excluded from primary accuracy, with no replacement case.',
        '* Clang machine hints sometimes address only some errors: twelve of its 36 applicable bundles still fail compilation. GCC 6.3 lacks the probed machine-edit flag; source rejection remains measured separately.',
        '* Real-history contribution is unidentifiable; constructing edits from future corrected endpoints would artificially favor SmartParse and was forbidden. No post-final algorithm changes were made.','',
        '## Complete final case ledger','',
        '| Case hash | Class | Error category | Lines | Error diagnostics | Valid candidates | Intended generated | Existing exact / token | Full reason |',
        '|---|---|---|---:|---:|---:|---|---|---|']
    for r in final['cases']:
        s=r['systems']['full'];b=r['systems']['existing']
        failures.append(f"| {r['id']} | {r['category']} | {r['error_category']} | {r['lines']} | {r['error_diagnostic_count']} | {s['valid_candidates']} | {s['candidate_coverage']} | {b['exact']} / {b['token_match']} | {s['reason']} |")
    failures+=['','Cases are identified by source-derived hashes and frozen CSV ordinals, not student identifiers. No source snippets are reproduced. Error categories are diagnostic heuristics and reported counts can include cascades. This sample is insufficient to classify all remaining failures as programmer-intent ambiguity; many are simply outside supported generation/analysis.','']
    (ROOT/'FAILURE_ANALYSIS.md').write_text('\n'.join(failures),encoding='utf-8')


if __name__=='__main__':main()
