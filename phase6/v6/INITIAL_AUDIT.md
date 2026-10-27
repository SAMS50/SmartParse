# Mandatory preimplementation audit

Completed before detector implementation. Repository branch/checkpoint verified as `feature/phase6-recovery`, `38a44fa`. Existing untracked Phase 5 acceptance files are retained. No older implementation is to be changed.

Reviewed: Extended C syntax/type and analyzer execution/normalization, v1 source/hash/review/duplicate model, v2 physical AST eligibility, v3 machine-fix-it recovery/budgets/mapping, v4 dependency-aware exclusion policy, v5 capability probing/profile/provenance and its 6-to-8-of-9 fixture comparison. V5's generic alpha observations remain review suggestions; source-level human adjudication is pending.

## Measured tooling and baseline

Installed Clang 17.0.2 supports JSON ASTs via its driver, including physical byte locations, declaration IDs, builtin/format attributes, operand types and implicit-cast kinds. `clang-check`, `clang-tidy` and `llvm-config` executables are adjacent/on the audit child PATH; no adjacent libclang DLL was found. No Python libclang dependency, new tool, or extra analyzer installation is needed. The existing bounded compiler runner and AST JSON are sufficient; no custom C parser will be built.

Before implementation, 34 proposed fixtures were analyzed through unchanged v5. Five additional range/value-flow boundary fixtures were separately frozen before implementation. The immutable cohorts have their own source/report hashes under `outputs/frozen_baseline/` and `outputs/frozen_extension/`. They must not be overwritten. Default Clang/GCC warnings and optional flag experiments are retained in `outputs/preimplementation_audit.json` and `outputs/frozen_extension/additional_tool_probes.json`.

Measured existing coverage:

- Clang already emits `-Wtautological-overlap-compare` for two mutually exclusive comparisons. GCC 6.3 supports `-Wlogical-op` and diagnoses that case when requested. Neither those warnings nor Clang `-Wconversion` diagnoses the three-term case `x >= 5 && x <= 5 && x == 6`.
- Installed `alpha.deadcode.UnreachableCode`, when explicitly enabled, **does** report the impossible three-term branch. Prefer this supported capability, with a narrow AST interval proof to establish the reason rather than treating every unreachable statement as a logic bug.
- Clang already reports `%4s` into a four-byte `char` array through `-Wfortify-source`, explaining the fifth byte needed for NUL. Unbounded `%s` into that array receives no diagnostic. A new bounded input adapter may report that as a capacity/contract review suggestion, not an inevitable overflow. Unknown capacities and programmer-defined functions named `scanf` must not match.
- Integer division implicitly converted to floating point receives no measured default or `-Wconversion` diagnostic. AST `IntegralToFloating` cast evidence supports an intent-review suggestion; it does not prove a programming mistake. Explicit casts and exact constant divisions are legitimate controls.
- Default `deadcode.DeadStores` already reports a separately assigned value overwritten before use. It does not report the analogous initialization in the measured fixture. No custom swap or initialization-intent detector is justified by that observation; reuse existing evidence and abstain about programmer intent.

## Remaining v5 allocation miss

Raw outputs, not only matched results, were inspected:

| Source structure | Installed v5 profile result |
| --- | --- |
| `int *p=malloc(1); ... *p=1` | No compiler or analyzer finding |
| `int *p=malloc(sizeof(char)); ... *p=1` | `unix.MallocSizeof` reports incompatible sizeof operand/type |
| `int *p=malloc(1); ... p[1]=1` | `alpha.security.ArrayBoundV2` reports bounds error |
| `int *p=malloc(sizeof *p); ... *p=1` | No finding, corrected control |

`-Wconversion` also does not report the literal-size case in either measured compiler. AST evidence confirms `malloc` has compiler builtin/allocation-size attributes and the dereference stores an `int`. Thus this is not a diagnostic-matching omission or failure to enable the existing v5 checks: it is an observed source-structure-sensitive backend gap. The precise analyzer implementation mechanism is unverified; do not claim a proven internal root cause. A hypothesis is that start-offset bounds reasoning and sizeof-specific diagnostics do not cover the full width of this scalar store.

This investigation is documented **before** any custom allocation detector. No custom allocation-size detector is planned for v6; a sound target-width/alias/extent proof needs separately bounded design, not a name-based malloc rule.

## Selected scope

1. Narrow signed-`int` conjunction interval proof, attached to existing compiler/analyzer evidence where available. Two-term warnings are duplicates, not new roots; the proven three-term branch is the measured opportunity from enabling an existing Clang checker.
2. Compiler-builtin/format-attributed stdio call plus physical AST fixed `char[N]` destination and single literal `%s` conversion. Width plus terminator is explicit; missing width is only a risk suggestion. Unknown formats/capacities/types, macro expansions and locally defined lookalikes abstain.
3. Direct implicit integer-to-floating conversion of integer division: retain operand/conversion types and original ranges, suggest review only; exclude explicit cast, macro, volatile, zero-divisor and exact-constant controls.
4. Reuse upstream dead-store evidence; omit general swap, alias/value-flow and programmer-intent inference.

All custom processing requires a successfully accepted frontend and physically validated main-file function regions. No invalid/recovery AST is treated as eligible. Existing repair/isolation policies remain unchanged and independently opt-in; all conditioned evidence stays in separate cohorts. Unknown inputs/features remain unknown. Use finite process/node/finding/time budgets and private overlays, never source edits or C execution.
