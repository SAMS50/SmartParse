# Sample: manual reference versus measured GCC output

Reference established before compiler execution; non-exhaustive. Counts describe this reviewed list only, not accuracy/recall.

Assessment counts: `{"detected": 15, "unsupported": 37, "uncertain": 15, "missed": 1}`; total reviewed reference entries: 68.

The assessment and compiler outcome answer different questions. An unsupported analyzer check can be missed by the compiler pass. An uncertain contract can still have a warning. No unavailable analysis is counted as a completed negative check.

| Reference line | Kind | Reference issue | Compiler outcome | Assessment | Observed diagnostic lines | Explanation |
|---|---|---|---|---|---|---|
| 30 | syntax | Missing semicolon after global_count declaration | detected | detected | 31 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 55 | memory safety | Inclusive loop writes students[10] and reads scores[10] | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 65 | runtime | Passes zero count to average, causing integer division by zero at 99 | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 71 | memory safety | Uses label after free; duplicate_text also returned a dangling stack address | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 74 | memory safety | Copies string longer than error.message capacity | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 78 | runtime | unsafe_divide called with zero divisor | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 81 | memory safety | reset_student called with null pointer | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 82 | syntax | Missing semicolon after return 0 | detected | detected | 83 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 88 | logic | add_numbers subtracts instead of adding (name-based intended contract) | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 96 | memory safety | average inclusive loop reads beyond count elements | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 99 | logic | Integer division truncates before conversion to double | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 104 | logic | Assigns null instead of comparing; subsequent dereference null | detected | detected | 104 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 114 | memory safety | find_student inclusive loop reads past count elements | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 115 | logic | Assigns id instead of comparing | detected | detected | 115 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 119 | logic | Returns 1 when not found; expected sentinel not specified | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 128 | memory safety | Unbounded copy into fixed stack buffer for arbitrary input | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 129 | memory safety | Returns address of local buffer | detected | detected | 129 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 149 | logic | Assigns active instead of checking it | detected | detected | 149 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 164 | logic | Semicolon makes if body empty; following block executes unconditionally | detected | detected | 164, 164 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 173 | logic | maximum returns a even when b is larger | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 179 | logic | is_even returns nonzero for odd values (name-based contract) | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 187 | logic | clamp returns low rather than high for values above high | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 194 | runtime | Negating INT_MIN overflows signed int | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 202 | memory safety | sum_array inclusive loop reads one element too far | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 209 | memory safety | strncpy may leave destination unterminated | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 214 | memory safety | Indexes length rather than length-1 under length-element contract | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 219 | memory safety | Writes size+1 bytes under size-byte buffer contract | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 224 | logic | Compares pointer identity rather than string contents; intended equality uncertain | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 229 | memory safety | strcat capacity precondition not checked; caller may supply insufficient space | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 236 | memory safety | Returns address of local int | detected | detected | 236 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 245 | memory safety | Writes terminator outside size-byte allocation | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 252 | memory safety | Double-free for nonnull allocated pointer | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 257 | memory safety | Null dereference possible unless caller guarantees valid pointer | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 263 | memory safety | Stores escaping address of local variable | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 271 | memory safety | Allocation leaked at function exit | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 278 | memory safety | Unchecked fopen failure passed to fscanf; unchecked conversion may leave value uninitialized | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 286 | memory safety | Unchecked fopen failure passed to fprintf | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 287 | resource | write_report does not fclose successful stream | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 292 | semantic/type | sscanf %d expects int pointer, receives int | detected | detected | 292 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 299 | memory safety | Unbounded scanf %s can overflow 8-byte name | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 307 | resource | file_exists leaks successful fopen stream | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 308 | memory safety | fclose called on null after failed fopen | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 317 | logic | Factorial loop comparison reversed for typical n>1; possible signed overflow for others | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 330 | logic | binary_search low=mid can prevent progress | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 342 | memory safety | reverse_array indexes length on first iteration | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 340 | logic | Reverse loop iterates entire array rather than half | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 351 | logic | Assigns target instead of comparing | detected | detected | 351 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 368 | logic | Month less than 1 AND greater than 12 is impossible | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 377 | logic | Accepts int outside named enum values; legal C, domain contract uncertain | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 382 | runtime | Floating division by zero: behavior depends on floating implementation/environment, not integer UB | detected | uncertain | 382 | Contract, preconditions, or runtime environment are not fully specified. |
| 387 | memory safety | Unbounded strcpy may overflow student name for long input | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 393 | semantic/type | Returns string pointer from int-returning function | detected | detected | 393 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 405 | semantic/type | Nonvoid function falls through for nonpositive value; using absent return value is problematic | missed | missed | — | No relevant diagnostic in this GCC invocation; serious earlier errors can suppress warnings. |
| 409 | semantic/type | Too few arguments to add_numbers | detected | detected | 409 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 414 | semantic/type | mystery_value undeclared (later use is same root issue) | detected | detected | 414 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 421 | semantic/type | printf %d expects int but receives long; type mismatch even on Windows equal-width types | detected | detected | 421 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 427 | logic | Concurrent global increment is unsafe only if threads actually share it; no threading in sample | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 432 | memory safety | Allocation omits terminator byte and failure is unchecked; overwrite may leak previous allocation | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 439 | memory safety | Writes through freed global_label; pointer may also be null | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 445 | logic | Returns comparison to 2 after toggling to 0 or 1; intended return contract uncertain | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 451 | logic | Integer division before multiply loses fractional percentage | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 456 | runtime | Modulo zero possible unless caller guarantees nonzero b | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 464 | logic | sign_of returns positive 1 for negatives (name-based contract) | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 474 | memory safety | initialize_scores writes count index beyond count elements | missed | unsupported | — | Missed by GCC syntax-only checking; live Clang analysis unavailable (not a negative analyzer result). |
| 479 | memory safety | Allows index MAX_ITEMS for a MAX_ITEMS-element array; actual parameter capacity unspecified | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |
| 486 | logic | swap loses original a before storing into b | missed | unsupported | — | General programmer-intent/contract checking is outside implemented scope. |
| 494 | logic | Uses multicharacter literal backslash-zero instead of null character | detected | detected | 494, 494 | Relevant compiler diagnostic; warnings are evidence, not observed execution. |
| 496 | logic | Returns length-1 rather than length (name-based contract) | missed | uncertain | — | Contract, preconditions, or runtime environment are not fully specified. |

The diagnostics at 432 and 438 are undeclared-global_label cascades from the declaration rejected after line 30. They do not establish detection of allocation overflow, allocation failure, leaks, or use-after-free at those sites.

The two warnings at line 164 and two warnings at 494 are multiple pieces of evidence for their respective root issues. The three notes are context, not three additional defects. Compiler-warning categories are intentionally preserved even when the reference describes a type or memory defect.

Floating division at 382 is warned about by GCC. It is not automatically classified as integer division-by-zero UB; floating semantics and the desired contract need review. The possible threading issue at 427 is not established by this single-threaded sample. No runtime experiment was performed.
