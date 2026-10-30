# Phase 6 Milestone 8: descriptive evaluation and research validation

Status: evaluation completed; independent accuracy validation remains pending. No detector, recovery heuristic, prior milestone or historical reference was changed. No commit, push, installation or subsequent milestone was performed.

## Scope, provenance and frozen protocol

The starting branch was `feature/phase6-recovery`, commit `9f8d005` (Milestone 7 committed). The initial audit covered Milestones 1–7 reports, original recovery/benchmark interfaces, historical labels, compiler configurations and protected hashes. Prior untracked acceptance outputs were retained. All new work is inside `phase6/v8/`.

The new set contains **32 author-created cases**, not an independently authored or human-adjudicated holdout: 12 restricted-grammar syntax cases and 20 full-C cases. There are 25 author-proposed roots: 12 syntax-cohort proposals and 13 full-C proposals. The latter include 12 program-defect proposals and one deliberately absent-header configuration blocker. Eight full-C corrected counterparts and one additional valid full-C control are included. No new source is byte-identical to a preserved prior file, but conceptual independence is not established by different hashes.

Membership, source bytes, intended syntax versions, proposed labels, configurations and matching rules were frozen before final analysis in **46 hashed files**. No random seed applies. `manifest.json`, `policy.json`, `configurations.json` and `freeze.json` retain that original protocol. All independent-verification flags are false; reviewer fields and human decisions remain blank/pending. No public dataset was downloaded.

One evaluation correction is explicit: protocol 1.1 recognizes equivalent quoted/unquoted expected punctuation in SmartParse and panic diagnostics. The initial implementation undercounted panic-mode matches because its expected-token wording lacks quotes. All 48 syntax runs were repeated; first-pass outputs are retained. See `protocol_amendment_1_1.json`. Frozen sources, intended repairs and extended-C matching rules were not changed.

## Original syntax recovery

Table I contains the full descriptive comparison:

| Configuration | Authored location matches | Exact authored repairs | Intended token streams reconstructed | Reached EOF | Additional unmatched diagnostics |
|---|---:|---:|---:|---:|---:|
| Panic mode | 6 | 0 | 2 | 11 | 9 |
| Context default | 8 | 8 | 8 | 11 | 4 |
| Validation disabled | 8 | 8 | 8 | 11 | 4 |
| Validation enabled | 8 | 8 | 8 | 11 | 4 |

There are 12 cases, including two valid controls. Eleven are lexable; S12's `@` is explicitly unsupported by the original lexer. The intended S04/S07 function versions use `void` parameter forms unsupported by the restricted grammar, so those two intended references fail strict validation. They remain frozen and explicitly unevaluable as intended-repair references. The grammar-supported cohort is nine cases, including the two valid controls and nine proposed punctuation roots across seven malformed cases. The eight matching repairs and eight equal intended streams include unchanged valid controls in the stream count. S09 is not reconstructed to its authored intended stream. These counts are author-reference comparisons, not validated TP/FP/FN.

`context_default` already enables local grammar validation, so it aliases `validation_on`. The equal validation-on/off outcomes do not establish that validation has no effect generally. Reaching EOF does not prove statement preservation or intended recovery. Trace-only subclasses record statement attempts without changing parsing decisions. Repair replay distinguishes insertion/substitution/deletion and does not remove the expected token during deletion. Strict grammar acceptance and equality to intended tokens are separate fields.

Additional diagnostics are review burden, not confirmed cascades or false positives. Single-pass syntax timings were below/coarse relative to the clock resolution on these tiny cases; they do not establish speed differences. Historical 12-program results and scores remain unchanged and are not reused as holdout measurements.

## Extended C comparison

Installed executables were GCC **6.3.0**, SDK Clang **17.0.2**, GCC **14.2.0** and Cppcheck **2.16.0**. Binary hashes were unchanged when rechecked. Every run uses explicit C11 with no additional includes or defines; tool-specific warnings/checkers are the unchanged existing profiles. The baseline is the prior v6 compiler/CSA/memory/semantic pipeline. Optional GCC14 and Cppcheck use the selected v7 adapters. Target/header/library models differ, limiting direct cross-tool comparisons.

**147 C configuration runs** completed as scheduled: 20 author-created cases plus the unchanged benchmark, each under seven configurations. Their reports account for **2,654 tool invocations**, including discovery, capability, AST, preprocessing, compiler and analyzer probes. Summed case wall time was **340.574 seconds** across interrupted sessions. There were **zero external worker timeouts and zero nonzero worker exits**; worker exit success means a report was saved, not that source analysis succeeded. Nested report status and return codes are authoritative. The execution audit records every available command and verifies no unexpected executable was launched as a tool. No C binary was executed.

| Configuration | Frozen original-source root proposals matched | Conditioned proposals matched | Frontend accepted | Analyzer completed |
|---|---:|---:|---:|---:|
| GCC6 compiler | 3 | 0 | 17/20 | not requested |
| Clang compiler | 3 | 0 | 17/20 | not requested |
| Previous extended baseline | 7 | 0 | 17/20 | 17/20 |
| Recovery-assisted | 7 | 1 | 18/20 | 18/20 |
| Isolation-assisted | 7 | 1 | 18/20 | 18/20 |
| GCC14 analyzer | 8 | 0 | not independently certified | 17/20 operational completion |
| Cppcheck | 7 | 0 | not certified by Cppcheck | 20/20 operational completion |
| Combined optional, derived original-only union | 13 | 0 | no aggregate certification | no new execution |

These are **strict frozen-matcher results, not accuracy or unique-capability measurements**. One of the 13 proposals is a configuration blocker, not a program defect. No 100% detection/recall claim follows from the union matching all proposals. The combined row is a deduplicated reuse of original-source evidence, not another analyzer or execution. Notes, cascades and repeated warnings do not add roots.

The frozen matcher has important false-negative risks, documented without changing its rules in `review/frozen_matching_limitations.json`:

- The authored allowlist says `unix.Stream`; actual existing v6 evidence is `alpha.unix.Stream`. The resource-leak finding is present in raw reports but remains unmatched automatically.
- The authored conjunction identifier differs from actual `SP6.contradictory_int_conjunction`. V6 already emits the contradiction evidence. **Cppcheck is not uniquely capable of finding that condition**, even though only its warning passes the frozen allowlist.
- Missing-return-semicolon Clang/GCC14 locations may point at the preceding statement, while the authored anchor is the next token. That location convention mismatch is not a genuine detector miss.
- GCC14 allocation-size, store and read warnings can share one underallocation cause. Its unmatched warnings must not become independent false positives or extra defects.

The resource and logic raw findings are pending source/root review in addition to the seven automatically matched baseline proposals. Counting unmatched evidence as absent capability would be misleading. Automated exclusivity lists identify exclusivity under the frozen matcher only. No matching rules were broadened after seeing these outcomes.

GCC14 supplies evidence for the concrete one-byte allocation/short-store case beyond the other strict original-source matches. Cppcheck supplies original malformed-source null-dereference evidence where Clang frontend rejection blocks the v6 semantic pipeline. Across strict matching, no proposal is shared by every configuration, since compiler-only rows have different scope. No full-C proposal is unobserved by the derived union; that does not establish absence of false negatives in the programs. All categories outside this small set are unevaluated. No undefined-behavior-wide or general logic coverage claim is made.

The nine corrected/valid full-C controls emit **zero primary errors/warnings in every configuration**. That is a descriptive control observation, not an independently established false-positive rate. Table IV keeps confirmed FP/FN blank and lists unmatched diagnostics and blocked cases separately.

## Conditional eligibility and findings

The missing-semicolon/null case C09 becomes frontend/analyzer eligible after bounded recovery and produces one **repair-conditioned** null-dereference proposal. The undeclared-helper/null case C10 becomes eligible after safe function exclusion and produces one **isolation-conditioned** null-dereference proposal. Neither enters the original-source cohort through those variants; Cppcheck separately reports original-source evidence for those operations with its own modeling limitations. No function/path completeness is certified.

The base v6 pipeline is blocked on three cases: missing semicolon, undeclared identifier and absent header. Recovery and isolation each unblock only their appropriate independent fixture. Configuration and semantic blockers remain explicit. Compiler diagnostic process completion can coexist with frontend rejection. Cppcheck returning normally on malformed code does not certify the source's type correctness or every region's interpretation.

## Unchanged 500-line benchmark

The cleaned 500-line source remains byte-identical, SHA-256 `c2b82ea25aa4e43da881e3894a923793ba4104eb2ad1446c9d91c889e0965c08`. The original source and historical acceptance artifacts are also protected. Table V records:

| Configuration | Primary diagnostics retained | Analysis result |
|---|---:|---|
| GCC6 compiler | 19 | diagnostics completed; frontend rejected |
| Clang compiler | 18 | diagnostics completed; frontend rejected |
| Extended baseline | 18 baseline compiler diagnostics | semantic pipeline blocked; analyzer partial |
| Recovery-assisted | 18 immutable baseline compiler diagnostics | still blocked; current variant kept separately |
| Isolation-assisted | 18 baseline compiler diagnostics | abstained/blocked |
| GCC14 | 22 | partial |
| Cppcheck | 24 | process completed; function/path coverage uncertified |

These counts are not distinct defects. Exact within-row duplicate count is zero, which does not rule out different messages about the same root, compiler cascades or cross-tool duplicates. All **24 prior Cppcheck diagnostic signatures reproduced exactly**. Their original source-reviewed relationships and **nine provisional incremental roots** remain separate: lines 65, 78, 81, 263, 271, 287, 307, 308 and 368. This is reproduction of prior tool evidence, not nine newly independently verified bugs. Prior duplicate/pre-existing-warning relationships are retained in `outputs/benchmark_prior_evidence_comparison.json`; no line/severity-only rematching inflates totals.

Two high-confidence semicolon edits were accepted in private variants, at original lines **30 and 82**. Baseline compiler evidence stays immutable; current variant diagnostics remain in the nested report with repair provenance. Remaining semantic blockers require assumptions, so recovery stops. Frontend eligibility and analyzer completion **did not improve**. Isolation excludes no function and abstains because main-file preprocessing directives beyond includes violate its current safety policy. No safeguards were weakened. The historical **16/68** baseline and Milestone 7's locally reviewed potential roots are not retroactively changed or combined into a new accuracy score.

## Human review, metrics and paper claims

All independent confirmation is pending. `review/REVIEW_PACKAGE.md` supplies line-numbered sources and proposed roots; `review/decisions.json` provides blank root/decision/reviewer/date/disagreement fields linked to exact diagnostic records. Full paths, notes, contracts, source mapping and provenance remain in per-configuration reports. Human review must resolve unknown findings, omitted/incorrect references, duplicate causes, conditional assumptions and whether suspicious logic reflects programmer intent.

**Confirmed TP, FP, FN, precision, recall and F1 are unavailable**, represented as null/blank with reasons. A mathematically contradictory condition proves a local fact, not a programmer-intent defect by itself. No confidence interval or statistical significance is asserted for accuracy. There are no validated labels or independent random sample, and one-pass interrupted timings do not support inferential speed comparisons.

The five CSV tables and five SVG/PDF/PNG figures support reproducible descriptive reporting. Figure captions flag frozen matching gaps and pending review. Suitable paper statements are limited to the observed configuration outcomes, exact reference-repair comparisons, source preservation, operational eligibility and reproduction of prior evidence. Independent real-project holdouts and human adjudication remain prerequisites for paper-level detection accuracy claims.

## Regression, preservation and deliverables

The 19 new targeted evaluation tests passed before final regression. They cover source identity, meaning versus proximity, duplicate roots, notes, conditional/blocked evidence, ambiguity, unavailable metrics, repair replay, frozen inputs, missing tools, configuration rejection and equivalent panic diagnostic wording.

The first default-PATH regression pass ran 413 tests with 28 skips because Clang was not on its test-child PATH; its log is retained as `initial_path_limited_regression.log`. The complete Clang-enabled rerun passed **452/452 tests: 0 failures, 0 errors, 0 skips**, in **236.812 seconds** (external supervisor 237.016 seconds; 600-second limit). That is all 433 prior tests plus 19 new evaluation tests. Results are recorded in `outputs/tests.json` and `outputs/regression.json`. The targeted 19 tests also passed again after final report generation.

Preservation checks cover **1,512 distinct pre-v8 files**, represented by 1,771 hash records because earlier manifests mix relative and absolute paths. All **17 historical CSVs** are included. The legacy performance test writes `results/verified_performance.csv`; its prior bytes are restored in `finally`. Byte preservation is claimed after testing, not unchanged timestamps or absence of transient legacy writes. Frozen sources/references/configuration files are checked separately. `outputs/preservation.json` records final verification.

New deliverables comprise authoring/freeze, evaluation, bounded runner, report, audit, plotting, validation and test modules; 32 source fixtures and 11 intended syntax counterparts; frozen manifest/policy/configuration/protocol amendment; per-configuration source/command/raw-output reports and supervisors; root and benchmark comparisons; human-review package; five tables; five figures in three formats; test logs; preservation audit and an exact file inventory. No existing implementation, fixture, historical CSV final bytes, prior output or detection rule was changed.

Remaining limitations are the small author-created dataset, non-independent ground truth, two unsupported intended references, frozen matching ID/location gaps, incomplete path/build/configuration coverage, differing platform/library models, conditional variant assumptions, and missing repeated timing samples. These are research limitations, not reasons to promote provisional findings to verified defects. Work stops at Milestone 8 for review.
