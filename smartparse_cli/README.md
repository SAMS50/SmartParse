# Unified SmartParse API and JSON contract

Use `python -m smartparse_cli analyze SOURCE.c` or `python -m smartparse_cli doctor`. Existing parser/backend APIs are not replaced. Python:

```python
from smartparse_cli import analyze
from smartparse_cli.engine import exit_code
report = analyze("input.c", analyzers=("compiler", "memory"), standard="c11")
code = exit_code(report)
```

The programmatic API validates analyzer/configuration/budget values with `ValueError`. Input/tool failures become structured reports. The CLI translates invalid arguments to exit 2; report/input/output failures to 3. Ordinary warnings yield 1 in this new CLI, while older CLI policies remain unchanged. No installation dependency is added.

## Schema 1.0

`schema.json` documents `smartparse.unified_analysis`, schema version `1.0`. Additive fields are permitted. Consumers should check the schema/version before interpreting nested raw reports, which retain their own existing versioned schemas.

| Field | Meaning |
|---|---|
| `source` | Resolved path, original byte SHA-256, size, empty-file flag and post-run preservation check |
| `requested_analyzers`, `effective_analyzers` | Explicit selection and effective dependencies; semantic subsumes memory; recovery/isolation may add memory |
| `status` | `completed`, `partial`, `failed`: requested operational completion, not defect absence |
| `runs` | Analyzer ID, independent status/reason, timing/counts, tool version/raw command/output reports, eligibility and variant provenance |
| `diagnostics` | Normalized evidence records, including context notes; underlying raw records are retained |
| `groups` | Conservative exact evidence groups with contributing diagnostic IDs/analyzers; never confirmed defect counts |
| `tool_issues` | Tool/configuration/input/incomplete-analysis issues, separate from source evidence |
| `summary` | Diagnostic severity/category/conditioning counts, evidence-group count; confirmed defect roots remain null |
| `coverage` | Explicit uncertified function/path completeness; consult per-run eligibility for frontend/analyzer state |
| `configuration`, `usage` | Standard, includes, defines, compiler choice, recovery/isolation flags, runtime and invocation budgets |

Each diagnostic includes `id`, `raw_reference` (run ID plus JSON-pointer-like path relative to `run.raw`), `raw_record`, original `reported_location`, selected `location`, `location_space`, severity/category/message, analyzer/backend/diagnostic ID, source hash, suggestion, evidence, completeness, review status and provenance. Unknown diagnostic IDs/severities/confidence stay unavailable; no accuracy is invented. Source snippets may be added from the bound input as evidence without changing the raw record. Notes remain context, not independent defects.

Locations use `mapped-original` where an upstream physical mapping is available, `original-tool-reported` otherwise, or `variant-reported; not mapped` for conditional records without a verified map. Raw byte ranges, column conventions and upstream mappings are not silently converted. Header/presumed locations may be unverified. Foreign header contents are not read to invent source snippets.

Conditioning is `original-source`, `repair-conditioned`, `isolation-conditioned`, or `repair-and-isolation-conditioned`. Provenance retains both flags, snapshot hashes, edit/variant IDs, source maps and exclusions where provided. Baseline compiler/analyzer results stay immutable within `run.raw`; current-variant evidence stays conditional. GCC14/Cppcheck run on the original file only. Excluded findings are not promoted: only the upstream accepted observation lists are normalized as findings; suppressed/unmapped records remain in raw reports with their limitations.

The normalized surface emphasizes baseline compiler evidence and accepted memory/semantic observations. Intermediate variant reports, checker inventories and suppressed records remain in the complete raw envelope. Consumers must not treat the normalized list as an exhaustive enumeration of every intermediate compiler pass.

Grouping requires an identical source hash, backend, file/line/column, severity/category, diagnostic ID, message and full provenance. Notes and unknown locations remain separate. Different backend findings never group automatically. A null `root_id` means root cause is not adjudicated; two groups can still describe one defect, and a group can require review. There is no line-only or warning-count deduplication.

`smartparse.doctor` 1.0 is a separate inventory schema: tool names, discovered paths, version status/raw text, bounded probe usage and discovery scope. Version availability is not analyzer capability. Missing optional tools do not make doctor fail; selecting an unavailable analyzer for analysis does yield exit 3. Environment overrides and explicit paths take priority. Existing v7 optional profiles remain version-pinned.

## Safety and operational limits

`category_basis` distinguishes a backend category from a conservative known-checker-ID display mapping or unknown classification. It does not change raw categories or introduce detection rules. `diagnostic_kind` distinguishes unlocated driver/configuration errors and compiler frontend blockers from other diagnostic evidence; such unlocated errors cause an incomplete/failure exit rather than being treated as successful source analysis.

All subprocess work reuses existing no-shell bounded runners. Compiler-only mode is syntax-only. GCC analyzer objects are private and never linked/run. Source is never rewritten. Report destinations use exclusive creation; an existing file, symlink or hard link is not overwritten. Parent directories are not created implicitly, and write failures return 3.

Shared runtime/invocation accounting stops subsequent work when exhausted. Per-tool/profile restrictions can cause earlier abstention. Cleanup has finite extra grace. The wrapper is not a build-system executor, CTU project analyzer or resource sandbox. Each requested pipeline can repeat capability/compiler checks; budgets count them. Defaults request only ordinary compiler diagnostics. `doctor` discovers installed tools but installs nothing.

Terminal/Markdown reports are for inspection; JSON is the authoritative provenance/raw-evidence format. A successful compiler diagnostic pass may reject the source; later analyzer completion must be considered separately. Repair or isolation may leave blockers unresolved. No confirmed bug, full path coverage, safety guarantee, human approval or universal error detection is inferred.
