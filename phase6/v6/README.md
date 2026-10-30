# Phase 6 v6: targeted semantic evidence

This separate experiment uses Clang's validated AST and supported diagnostics to report selected semantic facts and review suggestions. It does not replace SmartParse/CGAR, alter earlier pipelines, modify sources, execute C programs, or use sanitizers. New analysis is **disabled by default**. The mandatory [initial audit](INITIAL_AUDIT.md), including allocation-gap investigation, preceded detector implementation.

## Usage

Python 3.12 and Clang with physical JSON AST support are required for semantic analysis. Explicit compiler paths work when LLVM is not on PATH. No software installation occurs. GCC 6.3 remains available for disabled-profile baseline analysis; this semantic implementation does not require modern GCC options or pretend GCC provides Clang ASTs.

```powershell
# Existing compiler baseline only; semantic profile disabled.
python -m phase6.v6 "C:\my sources\input.c" --compiler gcc --json

# Explicit semantic profile, including the existing v5 memory evidence.
python -m phase6.v6 "C:\my sources\input.c" --compiler "C:\Program Files\LLVM\bin\clang.exe" --semantic-analysis --std c11 -I "C:\my headers" -D FEATURE=1 --json

# Prior experimental stages are separately requested and retain all safeguards.
python -m phase6.v6 input.c --compiler clang --semantic-analysis --punctuation-recovery --isolate-unaffected --json
```

```python
from phase6.v6.engine import run_semantics
report = run_semantics("input.c", enabled=True, compiler="clang")
```

Readable terminal output is default; `--json` selects the versioned report. Exit 0 means requested analysis completed and the original compiler baseline has no errors; warnings/review suggestions can exist. Exit 1 preserves original source rejection, even if a conditioned variant succeeds. Exit 2 means invalid arguments/configuration. Exit 3 means blocked, failed, timed out, unavailable, exhausted or unverified requested analysis. A completed invocation is never proof of program correctness or exhaustive path/function coverage.

## Implemented checks

| Rule | Evidence | Limits and confidence |
| --- | --- | --- |
| `SP6.contradictory_int_conjunction` | Intersect constraints in a pure conjunction of comparisons against integer constants, using the same local declaration ID | Only ordinary signed `int`, up to eight terms, `< <= > >= ==`; empty intersection is a proven predicate fact under defined execution, not proof of programmer intent |
| `SP6.fixed_buffer_input` | Compiler-builtin/format-attributed included `scanf`, one literal `%s` conversion and a direct local `char[N]` destination | Width plus NUL explicitly compared with capacity; missing/oversized width is a review suggestion requiring an input contract, not an inevitable overflow |
| `SP6.integer_division_to_float` | Direct compiler `IntegralToFloating` implicit cast of a supported integer `/` expression | Reports operand/result/conversion types; only an intent-review suggestion, never automatic precision-loss bug confirmation |

The installed `alpha.deadcode.UnreachableCode` checker is advertised and clean-probed before use. Its three-term-branch diagnostic supplies independent backend support for the AST condition proof. It is an experimental/development checker, not promoted to a production guarantee. Generic unreachable reports are retained as raw backend output and do not become general logic findings. A missing checker is explicitly recorded; a valid narrow AST constraint proof can still stand independently, without a fabricated backend witness.

Two-term contradictions already diagnosed by Clang/GCC and oversized scanf widths already diagnosed by Clang are linked to the same operation and marked `duplicate_of_existing`. Different-root proximity is insufficient: supported diagnostic ID/meaning and the validated enclosing operation range must agree. Extra backend support and an AST proof of one condition are adjudicated as one root, not two.

Default Clang `deadcode.DeadStores` remains in the upstream report. V6 does not invent a second overwrite detector, infer swap intent from names, or claim the initialization-only case is diagnosed. No custom allocation detector was added. The literal-size allocation-width case remains a documented miss.

## Abstention policy

Custom scanning requires frontend acceptance of the exact snapshot and validated physical main-file function ranges. Any remaining frontend error blocks custom analysis of the entire snapshot. There is no attempt to treat an invalid recovery AST as a verified function. V3/v4 must separately produce an eligible variant to change this state.

Unsigned/mixed-conversion comparisons, volatile/atomic values, side-effecting expressions, different declaration IDs, nonlocal state, unsupported types and macro-expanded candidate nodes are outside the constraint whitelist. Typedef/desugaring, enums, general arithmetic/range analysis and general unreachable-code detection are not claimed. Negative constants are accepted only when Clang types the relevant expression/literal as `int`; no host ABI width is assumed.

Input analysis is limited to one compiler-recognized standard scanf `%s` call and a fixed local narrow-char array. Merely spelling a function `scanf` is insufficient: compiler builtin and format attributes, an included declaration, and absence of a local definition are required. User-defined lookalikes, indirect calls, pointer/unknown capacity, arbitrary formats, multiple conversions, scansets, `%c`, wide strings, suppression and unsupported widths are not diagnosed by this rule. The standard-library contract remains an explicit assumption; no claim is made that hostile redeclarations or replacement libraries obey it.

Precision suggestions exclude explicit casts of the quotient, exact constant divisions, integer-only consumers, macro-expanded expressions, volatile values, side effects and known zero divisors. Unknown divisors are not asserted nonzero: suggestions explicitly assume defined division and leave zero/overflow diagnostics separate. Deliberate truncation can still be intended in an implicit floating context; that is why these remain suggestions.

## Report model and provenance

Envelope: `schema: "smartparse.semantic_analysis"`, `schema_version: "1.0"`. Additional fields may be added. Unreadable/setup failures may return `failure` and exit 3.

| Field | Meaning |
| --- | --- |
| `source` | Resolved original path, exact-byte SHA-256 and final preservation result. |
| `enabled`, `status`, `reason` | Explicit request and `not_attempted`, `blocked`, `completed`, `partial`, `failed`, `timed_out` or `budget_exhausted` result. |
| `upstream` | Unmodified v5 report, nesting original compiler/default analyzer evidence, memory profile, v2 eligibility, v3 repairs and v4 exclusions. |
| `provenance` | Original/snapshot hash, repair/isolation flags and variant IDs, source map and excluded spans inherited from earlier stages. |
| `inventory` | Validated function ranges, unreliable-region exclusions, candidate abstentions and node count. Null when frontend-blocked. |
| `checker_capability`, `additional_backend` | Advertised/probed experimental unreachable checker and actual separate analyzer report, raw output and completion. |
| `findings` | Source/range/type/constraint evidence, rule/category/confidence, operation/region, linked backend witnesses, duplicate status and unreviewed adjudication. |
| `function_path_coverage_certified` | Always false; process completion does not prove function/path exploration. |
| `usage`, `temporary_workspace_removed` | Combined counts/deadlines, detailed new commands and verified cleanup. |

Each finding's backend is `smartparse-semantic-ast`; this identifies compiler-AST-based SmartParse analysis, **not CGAR recovery**. Independent diagnostics remain attributed to Clang/GCC/Clang Static Analyzer in `backend_witnesses` and upstream reports. Predicate facts are `proven_predicate_false`; input and precision targets are `review_suggestion`. Every finding starts `adjudication: unreviewed`, `confirmed_programmer_intent_bug: false`.

Lines/byte columns are 1-based; byte offsets are 0-based half-open ranges. `evidence.physical_range` explicitly refers to snapshot bytes, while `original_range` refers to original bytes. V3 insertion maps compose with v4 offset-preserving masks. An exclusive endpoint at an inserted semicolon maps to its original anchor, not a fictional original punctuation token. `original_location` preserves mapped file/line/column. CRLF, UTF-8 and Windows paths are tested. Unsupported encodings/presumed-line mappings abstain rather than transcode or guess.

Repair-only, isolation-only, combined and original-source cohorts remain distinguishable. Temporary snapshots use private Clang VFS overlays and are cleaned on error/success. Original files are never opened for writing by analysis. `evaluation.export_run` rejects conditioned or unverified evidence for unconditional v1 scoring. Conditional input/intent contracts remain conditional even when a message matches; supporting notes, extra backend witnesses and compiler duplicates cannot inflate confirmed roots.

## Limits and validation

Default combined command budget is 96 (hard maximum 120), analyzer driver invocations 20 (maximum 20), total deadline 120 seconds and per-command timeout 10 seconds (maximum 30). Upstream capability/inventory commands count. V5's fixed four-checker profile plus at most one semantic checker is used; no arbitrary checker expansion. AST traversal is capped at 100,000 nodes, conjunctions at eight terms and findings at 64 (configurable to 128). Exceeding the finding budget rejects the scan rather than silently claiming truncated success. CLI controls include `--max-invocations`, `--max-analyzer-invocations`, `--total-timeout`, `--timeout`, `--max-findings`.

All subprocesses use the inherited no-shell, file-backed, finite-timeout runner. Finite process-tree cleanup grace, OS suspension/scheduling and filesystem/Python work prevent hard real-time guarantees. No resource sandbox, external header snapshot, arbitrary C equivalence proof or complete coverage claim is made.

```powershell
python -m phase6.v6.run_validation --stage targeted --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v6.run_validation --stage compare --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v6.run_validation --stage benchmark --compiler "C:\Program Files\LLVM\bin\clang.exe"
python -m phase6.v6.run_validation --stage full --compiler "C:\Program Files\LLVM\bin\clang.exe"
```

The two preimplementation frozen cohorts are never regenerated by these stages; their hashes are verified. Comparison can reuse completed artifacts only after source/hash/configuration/preservation checks and records that reuse. Remaining comparison cases use separate 30-second internal / 45-second external processes. The comparison batch is externally limited to 240 seconds; targeted methods 75 seconds; benchmark cases 135 seconds; full regression 480 seconds. A failed/interrupted stage is reported rather than skipped. Earlier validation runners are not invoked, avoiding old acceptance-output overwrites. The legacy performance test's CSV writes are snapshotted/restored byte-for-byte in `finally` and disclosed.

See [MILESTONE_6_REPORT.md](MILESTONE_6_REPORT.md), [INITIAL_AUDIT.md](INITIAL_AUDIT.md), and [outputs/comparison.json](outputs/comparison.json). The new eight-unit reference contains four structural facts and four conditional review targets. It is separate from historical reference definitions. Counts are agent-reviewed and provisional until independent human adjudication; precision/recall remain null rather than being inferred from raw warnings.
