# Measured diagnostic inventory

Generated from saved CLI JSON. Every diagnostic, including notes and cascades, is retained.

## sample

Backend: GCC; status: completed; summary: `{"total_diagnostics": 23, "errors": 6, "warnings": 14, "notes": 3, "categories": {"syntax": 2, "semantic/type": 4, "compiler warning": 14, "unknown": 3}}`.

| Line:column | Severity | Category | Identifier | Exact diagnostic message |
|---|---|---|---|---|
| 31:1 | error | syntax | — | expected ',' or ';' before 'char' |
| 83:1 | error | syntax | — | expected ';' before '}' token |
| 104:5 | warning | compiler warning | -Wparentheses | suggest parentheses around assignment used as truth value |
| 115:9 | warning | compiler warning | -Wparentheses | suggest parentheses around assignment used as truth value |
| 129:12 | warning | compiler warning | -Wreturn-local-addr | function returns address of local variable |
| 149:9 | warning | compiler warning | -Wparentheses | suggest parentheses around assignment used as truth value |
| 164:38 | warning | compiler warning | -Wempty-body | suggest braces around empty body in an 'if' statement |
| 164:5 | warning | compiler warning | -Wmisleading-indentation | this 'if' clause does not guard... |
| 164:40 | note | unknown | — | ...this statement, but the latter is misleadingly indented as if it is guarded by the 'if' |
| 236:12 | warning | compiler warning | -Wreturn-local-addr | function returns address of local variable |
| 292:20 | warning | compiler warning | -Wformat= | format '%d' expects argument of type 'int *', but argument 3 has type 'int' |
| 351:9 | warning | compiler warning | -Wparentheses | suggest parentheses around assignment used as truth value |
| 382:26 | warning | compiler warning | -Wdiv-by-zero | division by zero |
| 393:12 | warning | compiler warning | -Wint-conversion | return makes integer from pointer without a cast |
| 409:12 | error | semantic/type | — | too few arguments to function 'add_numbers' |
| 85:5 | note | unknown | — | declared here |
| 414:5 | error | semantic/type | — | 'mystery_value' undeclared (first use in this function) |
| 414:5 | note | unknown | — | each undeclared identifier is reported only once for each function it appears in |
| 421:14 | warning | compiler warning | -Wformat= | format '%d' expects argument of type 'int', but argument 2 has type 'long int' |
| 432:5 | error | semantic/type | — | 'global_label' undeclared (first use in this function) |
| 438:10 | error | semantic/type | — | 'global_label' undeclared (first use in this function) |
| 494:28 | warning | compiler warning | -Wmultichar | multi-character character constant |
| 494:25 | warning | compiler warning | -Wtype-limits | comparison is always true due to limited range of data type |

## broken_records

Backend: GCC; status: completed; summary: `{"total_diagnostics": 6, "errors": 4, "warnings": 0, "notes": 2, "categories": {"syntax": 2, "semantic/type": 2, "compiler warning": 0, "unknown": 2}}`.

| Line:column | Severity | Category | Identifier | Exact diagnostic message |
|---|---|---|---|---|
| 4:22 | error | syntax | — | expected expression before ';' token |
| 9:28 | error | syntax | — | expected expression before ';' token |
| 13:12 | error | semantic/type | — | 'unknown_record' undeclared (first use in this function) |
| 13:12 | note | unknown | — | each undeclared identifier is reported only once for each function it appears in |
| 17:33 | error | semantic/type | — | too many arguments to function 'accepts' |
| 16:5 | note | unknown | — | declared here |

## pointer_and_logic

Backend: GCC; status: completed; summary: `{"total_diagnostics": 1, "errors": 0, "warnings": 1, "notes": 0, "categories": {"syntax": 0, "semantic/type": 0, "compiler warning": 1, "unknown": 0}}`.

| Line:column | Severity | Category | Identifier | Exact diagnostic message |
|---|---|---|---|---|
| 38:5 | warning | compiler warning | -Wparentheses | suggest parentheses around assignment used as truth value |

## valid_inventory

Backend: GCC; status: completed; summary: `{"total_diagnostics": 0, "errors": 0, "warnings": 0, "notes": 0, "categories": {"syntax": 0, "semantic/type": 0, "compiler warning": 0, "unknown": 0}}`.

| Line:column | Severity | Category | Identifier | Exact diagnostic message |
|---|---|---|---|---|
| — | — | — | — | No compiler diagnostics; not proof of bug-free behavior |

## semantic

Backend: GCC; status: completed; summary: `{"total_diagnostics": 6, "errors": 3, "warnings": 1, "notes": 2, "categories": {"syntax": 0, "semantic/type": 3, "compiler warning": 1, "unknown": 2}}`.

| Line:column | Severity | Category | Identifier | Exact diagnostic message |
|---|---|---|---|---|
| 3:55 | error | semantic/type | — | incompatible types when returning type 'struct Item' but 'int' was expected |
| 5:17 | error | semantic/type | — | 'missing_identifier' undeclared (first use in this function) |
| 5:17 | note | unknown | — | each undeclared identifier is reported only once for each function it appears in |
| 6:5 | error | semantic/type | — | too many arguments to function 'takes_int' |
| 1:5 | note | unknown | — | declared here |
| 7:5 | warning | compiler warning | -Wparentheses | suggest parentheses around assignment used as truth value |

## missing_header

Backend: GCC; status: partial; summary: `{"total_diagnostics": 1, "errors": 1, "warnings": 0, "notes": 0, "categories": {"syntax": 0, "semantic/type": 0, "compiler warning": 0, "unknown": 1}}`.

| Line:column | Severity | Category | Identifier | Exact diagnostic message |
|---|---|---|---|---|
| 1:52 | fatal error | unknown | — | smartparse_intentionally_absent_header.h: No such file or directory |
