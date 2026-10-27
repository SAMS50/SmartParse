# GCC 6.3 versus Clang 17: 68-reference comparison

Only the same unmodified cleaned 500-line source is compared. The manual reference is non-exhaustive.

## Matching criteria

Match a non-note diagnostic to the reviewed root line or its documented error-reporting anchors. For the missing semicolons, GCC points to following lines 31/83 while Clang points to 30/82. Also inspect the message and issue kind: undeclared-name/type cascades at allocation lines are not memory-bug detections. Only relevant warnings count as compiler evidence for memory/runtime/logic reference entries. Multiple warnings, repeated uses, path notes, and different backend severities never create extra reference entries. Uncertain contracts/preconditions remain uncertain even if a warning was emitted.

Detected means a relevant diagnostic, not proof of programmer intent. Missed means a supported syntax/type reference has no relevant diagnostic in this invocation. Unsupported means the required general logic analysis is outside scope or the sample analyzer pass is blocked by frontend errors. Such an entry separately records compiler_outcome=missed. The four independent memory checks passed; that does not validate blocked path analysis on this malformed sample.

| Backend | Detected | Missed | Unsupported | Uncertain |
|---|---:|---:|---:|---:|
| gcc | 15 | 1 | 37 | 15 |
| clang | 16 | 1 | 36 | 15 |

These are dispositions of a reviewed list, not precision/recall or universal bug counts. The combined evidence detects the same 16 non-uncertain reference entries as Clang alone; overlapping compiler reports are counted once per manual reference.

| Root line | Kind | Reviewed issue | GCC assessment / compiler outcome | Clang assessment / compiler outcome |
|---|---|---|---|---|
| 30 | syntax | Missing semicolon after global_count declaration | detected / detected | detected / detected |
| 55 | memory safety | Inclusive loop writes students[10] and reads scores[10] | unsupported / missed | unsupported / missed |
| 65 | runtime | Passes zero count to average, causing integer division by zero at 99 | unsupported / missed | unsupported / missed |
| 71 | memory safety | Uses label after free; duplicate_text also returned a dangling stack address | unsupported / missed | unsupported / missed |
| 74 | memory safety | Copies string longer than error.message capacity | unsupported / missed | detected / detected |
| 78 | runtime | unsafe_divide called with zero divisor | unsupported / missed | unsupported / missed |
| 81 | memory safety | reset_student called with null pointer | unsupported / missed | unsupported / missed |
| 82 | syntax | Missing semicolon after return 0 | detected / detected | detected / detected |
| 88 | logic | add_numbers subtracts instead of adding (name-based intended contract) | uncertain / missed | uncertain / missed |
| 96 | memory safety | average inclusive loop reads beyond count elements | unsupported / missed | unsupported / missed |
| 99 | logic | Integer division truncates before conversion to double | unsupported / missed | unsupported / missed |
| 104 | logic | Assigns null instead of comparing; subsequent dereference null | detected / detected | detected / detected |
| 114 | memory safety | find_student inclusive loop reads past count elements | unsupported / missed | unsupported / missed |
| 115 | logic | Assigns id instead of comparing | detected / detected | detected / detected |
| 119 | logic | Returns 1 when not found; expected sentinel not specified | uncertain / missed | uncertain / missed |
| 128 | memory safety | Unbounded copy into fixed stack buffer for arbitrary input | unsupported / missed | unsupported / missed |
| 129 | memory safety | Returns address of local buffer | detected / detected | detected / detected |
| 149 | logic | Assigns active instead of checking it | detected / detected | detected / detected |
| 164 | logic | Semicolon makes if body empty; following block executes unconditionally | detected / detected | detected / detected |
| 173 | logic | maximum returns a even when b is larger | uncertain / missed | uncertain / missed |
| 179 | logic | is_even returns nonzero for odd values (name-based contract) | uncertain / missed | uncertain / missed |
| 187 | logic | clamp returns low rather than high for values above high | unsupported / missed | unsupported / missed |
| 194 | runtime | Negating INT_MIN overflows signed int | unsupported / missed | unsupported / missed |
| 202 | memory safety | sum_array inclusive loop reads one element too far | unsupported / missed | unsupported / missed |
| 209 | memory safety | strncpy may leave destination unterminated | unsupported / missed | unsupported / missed |
| 214 | memory safety | Indexes length rather than length-1 under length-element contract | unsupported / missed | unsupported / missed |
| 219 | memory safety | Writes size+1 bytes under size-byte buffer contract | unsupported / missed | unsupported / missed |
| 224 | logic | Compares pointer identity rather than string contents; intended equality uncertain | uncertain / missed | uncertain / missed |
| 229 | memory safety | strcat capacity precondition not checked; caller may supply insufficient space | uncertain / missed | uncertain / missed |
| 236 | memory safety | Returns address of local int | detected / detected | detected / detected |
| 245 | memory safety | Writes terminator outside size-byte allocation | unsupported / missed | unsupported / missed |
| 252 | memory safety | Double-free for nonnull allocated pointer | unsupported / missed | unsupported / missed |
| 257 | memory safety | Null dereference possible unless caller guarantees valid pointer | uncertain / missed | uncertain / missed |
| 263 | memory safety | Stores escaping address of local variable | unsupported / missed | unsupported / missed |
| 271 | memory safety | Allocation leaked at function exit | unsupported / missed | unsupported / missed |
| 278 | memory safety | Unchecked fopen failure passed to fscanf; unchecked conversion may leave value uninitialized | unsupported / missed | unsupported / missed |
| 286 | memory safety | Unchecked fopen failure passed to fprintf | unsupported / missed | unsupported / missed |
| 287 | resource | write_report does not fclose successful stream | unsupported / missed | unsupported / missed |
| 292 | semantic/type | sscanf %d expects int pointer, receives int | detected / detected | detected / detected |
| 299 | memory safety | Unbounded scanf %s can overflow 8-byte name | unsupported / missed | unsupported / missed |
| 307 | resource | file_exists leaks successful fopen stream | unsupported / missed | unsupported / missed |
| 308 | memory safety | fclose called on null after failed fopen | unsupported / missed | unsupported / missed |
| 317 | logic | Factorial loop comparison reversed for typical n>1; possible signed overflow for others | unsupported / missed | unsupported / missed |
| 330 | logic | binary_search low=mid can prevent progress | unsupported / missed | unsupported / missed |
| 342 | memory safety | reverse_array indexes length on first iteration | unsupported / missed | unsupported / missed |
| 340 | logic | Reverse loop iterates entire array rather than half | unsupported / missed | unsupported / missed |
| 351 | logic | Assigns target instead of comparing | detected / detected | detected / detected |
| 368 | logic | Month less than 1 AND greater than 12 is impossible | unsupported / missed | unsupported / missed |
| 377 | logic | Accepts int outside named enum values; legal C, domain contract uncertain | uncertain / missed | uncertain / missed |
| 382 | runtime | Floating division by zero: behavior depends on floating implementation/environment, not integer UB | uncertain / detected | uncertain / missed |
| 387 | memory safety | Unbounded strcpy may overflow student name for long input | unsupported / missed | unsupported / missed |
| 393 | semantic/type | Returns string pointer from int-returning function | detected / detected | detected / detected |
| 405 | semantic/type | Nonvoid function falls through for nonpositive value; using absent return value is problematic | missed / missed | missed / missed |
| 409 | semantic/type | Too few arguments to add_numbers | detected / detected | detected / detected |
| 414 | semantic/type | mystery_value undeclared (later use is same root issue) | detected / detected | detected / detected |
| 421 | semantic/type | printf %d expects int but receives long; type mismatch even on Windows equal-width types | detected / detected | detected / detected |
| 427 | logic | Concurrent global increment is unsafe only if threads actually share it; no threading in sample | uncertain / missed | uncertain / missed |
| 432 | memory safety | Allocation omits terminator byte and failure is unchecked; overwrite may leak previous allocation | unsupported / missed | unsupported / missed |
| 439 | memory safety | Writes through freed global_label; pointer may also be null | unsupported / missed | unsupported / missed |
| 445 | logic | Returns comparison to 2 after toggling to 0 or 1; intended return contract uncertain | uncertain / missed | uncertain / missed |
| 451 | logic | Integer division before multiply loses fractional percentage | unsupported / missed | unsupported / missed |
| 456 | runtime | Modulo zero possible unless caller guarantees nonzero b | uncertain / missed | uncertain / missed |
| 464 | logic | sign_of returns positive 1 for negatives (name-based contract) | uncertain / missed | uncertain / missed |
| 474 | memory safety | initialize_scores writes count index beyond count elements | unsupported / missed | unsupported / missed |
| 479 | memory safety | Allows index MAX_ITEMS for a MAX_ITEMS-element array; actual parameter capacity unspecified | uncertain / missed | uncertain / missed |
| 486 | logic | swap loses original a before storing into b | unsupported / missed | unsupported / missed |
| 494 | logic | Uses multicharacter literal backslash-zero instead of null character | detected / detected | detected / detected |
| 496 | logic | Returns length-1 rather than length (name-based contract) | uncertain / missed | uncertain / missed |

## Differences requiring interpretation

- Clang warns about the fixed-buffer overflow at line 74; GCC syntax-only did not. No inference is made about other unreported buffers.
- GCC emits undeclared-global_label cascades at 432/438 after rejecting the declaration following line 30. Clang recovers that declaration. These do not add defects.
- Clang reports both uses of mystery_value at 414/415, suggests last_value at 415, and reports an incompatible return conversion from that recovery. This is one undeclared-name root, not three separate intended bugs.
- The pointer-to-int return at 393 is a GCC warning but a Clang error. Severity differences are not detection gains.
- Both warn twice about the multicharacter/comparison root at 494. GCC warns about floating division at 382; Clang does not in this invocation. Its reference disposition stays uncertain.
- Neither emits the reviewed missing-return warning at 405 in this malformed sample. It remains a measured miss, without inventing a cause.
- General intent-dependent logic errors remain unproved. Static findings are kept outside ordinary compiler totals and are not deduplicated by line alone.

## All measured Clang compiler diagnostics

| Line:column | Severity | Category | Identifier | Exact message |
|---|---|---|---|---|
| 30:21 | error | syntax | — | expected ';' after top level declarator |
| 82:13 | error | syntax | — | expected ';' after return statement |
| 74:5 | warning | compiler warning | -Wfortify-source | 'strcpy' will always overflow; destination buffer has size 32, but the source string has length 49 (including NUL byte) |
| 104:17 | warning | compiler warning | -Wparentheses | using the result of an assignment as a condition without parentheses |
| 104:17 | note | unknown | — | place parentheses around the assignment to silence this warning |
| 104:17 | note | unknown | — | use '==' to turn this assignment into an equality comparison |
| 115:28 | warning | compiler warning | -Wparentheses | using the result of an assignment as a condition without parentheses |
| 115:28 | note | unknown | — | place parentheses around the assignment to silence this warning |
| 115:28 | note | unknown | — | use '==' to turn this assignment into an equality comparison |
| 129:12 | warning | compiler warning | -Wreturn-stack-address | address of stack memory associated with local variable 'buffer' returned |
| 149:32 | warning | compiler warning | -Wparentheses | using the result of an assignment as a condition without parentheses |
| 149:32 | note | unknown | — | place parentheses around the assignment to silence this warning |
| 149:32 | note | unknown | — | use '==' to turn this assignment into an equality comparison |
| 164:38 | warning | compiler warning | -Wempty-body | if statement has empty body |
| 164:38 | note | unknown | — | put the semicolon on a separate line to silence this warning |
| 236:13 | warning | compiler warning | -Wreturn-stack-address | address of stack memory associated with local variable 'local' returned |
| 292:24 | warning | compiler warning | -Wformat | format specifies type 'int *' but the argument has type 'int' |
| 351:23 | warning | compiler warning | -Wparentheses | using the result of an assignment as a condition without parentheses |
| 351:23 | note | unknown | — | place parentheses around the assignment to silence this warning |
| 351:23 | note | unknown | — | use '==' to turn this assignment into an equality comparison |
| 393:12 | error | semantic/type | -Wint-conversion | incompatible pointer to integer conversion returning 'char[6]' from a function with result type 'int' |
| 409:25 | error | semantic/type | — | too few arguments to function call, expected 2, have 1 |
| 85:5 | note | unknown | — | 'add_numbers' declared here |
| 414:5 | error | semantic/type | — | use of undeclared identifier 'mystery_value' |
| 415:12 | error | semantic/type | — | use of undeclared identifier 'mystery_value'; did you mean 'last_value'? |
| 212:5 | note | unknown | — | 'last_value' declared here |
| 415:12 | error | semantic/type | -Wint-conversion | incompatible pointer to integer conversion returning 'int (int *, int)' from a function with result type 'int' |
| 421:20 | warning | compiler warning | -Wformat | format specifies type 'int' but the argument has type 'long' |
| 494:28 | warning | compiler warning | -Wmultichar | multi-character character constant |
| 494:25 | warning | compiler warning | -Wtautological-constant-out-of-range-compare | result of comparison of constant 23600 with expression of type 'const char' is always true |

## Independent fixture analyzer findings

| Fixture | Status | Finding line | Checker | Exact warning | Path notes |
|---|---|---:|---|---|---:|
| null_pointer | completed | 4 | core.NullDereference | Dereference of null pointer (loaded from variable 'pointer') | 2 |
| memory_leak | completed | 7 | unix.Malloc | Potential leak of memory pointed to by 'pointer' | 4 |
| use_after_free | completed | 7 | unix.Malloc | Use of memory after it is freed | 5 |
| double_free | completed | 6 | unix.Malloc | Attempt to free released memory | 5 |
