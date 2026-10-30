# Human review package

No decisions are prefilled. Review source/contract and path evidence; do not confirm by line or warning count alone.
Assign root IDs and TP/FP/uncertain/unsupported/blocked decisions in decisions.json; record reviewer/date and disagreements.
The authored reference is a proposal, not an independently certified oracle. Corrected controls can also contain overlooked issues.
For every warning, distinguish duplicate/cascade/real root/review suggestion. Repair/isolation conditions must remain attached.
Inspect full raw per-configuration JSON under outputs/extended, including notes, exact commands and frontend status.

## C01_null
[
  {
    "id": "C01_null-R1",
    "line": 3,
    "column": 2,
    "source_evidence": "return bias + *probe;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "memory_safety",
    "allowed_ids": [
      "core.NullDereference",
      "-Wanalyzer-null-dereference",
      "nullPointer"
    ],
    "message_any": [
      "null",
      "dereference"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 0
  }
]
```c
001 | int read_probe(int bias) {
002 |  int *probe=0;
003 |  return bias + *probe;
004 | }
```

## C01_null_corrected
[]
```c
001 | int read_probe(int bias) {
002 |  int sample=11;
003 |  int *probe=&sample;
004 |  return bias + *probe;
005 | }
```

## C02_leak
[
  {
    "id": "C02_leak-R1",
    "line": 5,
    "column": 2,
    "source_evidence": "cells[0]=13;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "memory_safety",
    "allowed_ids": [
      "unix.Malloc",
      "-Wanalyzer-malloc-leak",
      "memleak"
    ],
    "message_any": [
      "leak"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 1
  }
]
```c
001 | #include <stdlib.h>
002 | void collect_cells(void) {
003 |  unsigned *cells=calloc(5,sizeof *cells);
004 |  if(!cells) return;
005 |  cells[0]=13;
006 | }
```

## C02_leak_corrected
[]
```c
001 | #include <stdlib.h>
002 | void collect_cells(void) {
003 |  unsigned *cells=calloc(5,sizeof *cells);
004 |  if(!cells) return;
005 |  cells[0]=13;
006 |  free(cells);
007 | }
```

## C03_double
[
  {
    "id": "C03_double-R1",
    "line": 6,
    "column": 2,
    "source_evidence": "free(saved);",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "memory_safety",
    "allowed_ids": [
      "unix.Malloc",
      "-Wanalyzer-double-free",
      "doubleFree"
    ],
    "message_any": [
      "free"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 0
  }
]
```c
001 | #include <stdlib.h>
002 | void release_pair(void) {
003 |  char *block=malloc(24);
004 |  char *saved=block;
005 |  free(block);
006 |  free(saved);
007 | }
```

## C03_double_corrected
[]
```c
001 | #include <stdlib.h>
002 | void release_pair(void) {
003 |  char *block=malloc(24);
004 |  free(block);
005 | }
```

## C04_uaf
[
  {
    "id": "C04_uaf-R1",
    "line": 9,
    "column": 2,
    "source_evidence": "return alias->code;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "memory_safety",
    "allowed_ids": [
      "unix.Malloc",
      "-Wanalyzer-use-after-free",
      "deallocuse"
    ],
    "message_any": [
      "free"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 0
  }
]
```c
001 | #include <stdlib.h>
002 | struct Entry { int code; };
003 | int release_entry(void) {
004 |  struct Entry *item=malloc(sizeof *item);
005 |  if(!item) return 0;
006 |  item->code=29;
007 |  struct Entry *alias=item;
008 |  free(item);
009 |  return alias->code;
010 | }
```

## C04_uaf_corrected
[]
```c
001 | #include <stdlib.h>
002 | struct Entry { int code; };
003 | int release_entry(void) {
004 |  struct Entry *item=malloc(sizeof *item);
005 |  if(!item) return 0;
006 |  item->code=29;
007 |  int code=item->code;
008 |  free(item);
009 |  return code;
010 | }
```

## C05_bounds
[
  {
    "id": "C05_bounds-R1",
    "line": 3,
    "column": 2,
    "source_evidence": "row[5]=31;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "bounds",
    "allowed_ids": [
      "alpha.security.ArrayBoundV2",
      "-Warray-bounds",
      "-Wanalyzer-out-of-bounds",
      "arrayIndexOutOfBounds"
    ],
    "message_any": [
      "bound",
      "overflow",
      "index"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 0
  }
]
```c
001 | int fill_row(void) {
002 |  int row[5]={0};
003 |  row[5]=31;
004 |  return row[0];
005 | }
```

## C05_bounds_corrected
[]
```c
001 | int fill_row(void) {
002 |  int row[5]={0};
003 |  row[4]=31;
004 |  return row[0];
005 | }
```

## C06_allocation
[
  {
    "id": "C06_allocation-R1",
    "line": 6,
    "column": 2,
    "source_evidence": "*cell=101;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "bounds",
    "allowed_ids": [
      "unix.Malloc",
      "alpha.security.ArrayBoundV2",
      "-Wanalyzer-out-of-bounds",
      "-Wanalyzer-allocation-size",
      "-Wstringop-overflow",
      "allocSize",
      "bufferAccessOutOfBounds"
    ],
    "message_any": [
      "size",
      "bound",
      "overflow"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 0
  }
]
```c
001 | #include <stdlib.h>
002 | _Static_assert(sizeof(short)>1,"requires multi-byte short");
003 | int store_cell(void) {
004 |  short *cell=malloc(1);
005 |  if(!cell) return 0;
006 |  *cell=101;
007 |  int value=*cell;
008 |  free(cell);
009 |  return value;
010 | }
```

## C06_allocation_corrected
[]
```c
001 | #include <stdlib.h>
002 | int store_cell(void) {
003 |  short *cell=malloc(sizeof *cell);
004 |  if(!cell) return 0;
005 |  *cell=101;
006 |  int value=*cell;
007 |  free(cell);
008 |  return value;
009 | }
```

## C07_resource
[
  {
    "id": "C07_resource-R1",
    "line": 5,
    "column": 2,
    "source_evidence": "fputs(\"record\",stream);",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "resource",
    "allowed_ids": [
      "unix.Stream",
      "-Wanalyzer-file-leak",
      "-Wanalyzer-malloc-leak",
      "resourceLeak"
    ],
    "message_any": [
      "leak",
      "close"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 1
  }
]
```c
001 | #include <stdio.h>
002 | void write_record(void) {
003 |  FILE *stream=fopen("m8-record.txt","w");
004 |  if(!stream) return;
005 |  fputs("record",stream);
006 | }
```

## C07_resource_corrected
[]
```c
001 | #include <stdio.h>
002 | void write_record(void) {
003 |  FILE *stream=fopen("m8-record.txt","w");
004 |  if(!stream) return;
005 |  fputs("record",stream);
006 |  fclose(stream);
007 | }
```

## C08_contradiction
[
  {
    "id": "C08_contradiction-R1",
    "line": 2,
    "column": 2,
    "source_evidence": "if(value>=-3 && value<=-3 && value==2)",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "program_logic",
    "allowed_ids": [
      "smartparse.semantic.contradictory_int_conjunction",
      "alpha.deadcode.UnreachableCode",
      "-Wlogical-op",
      "-Wtautological-overlap-compare",
      "incorrectLogicOperator",
      "knownConditionTrueFalse"
    ],
    "message_any": [
      "condition",
      "false",
      "intersection",
      "overlap"
    ],
    "required_contract": "As written; standard library calls modeled, successful allocation/open path where guarded.",
    "admissible_line_window": 0
  }
]
```c
001 | int classify_value(int value) {
002 |  if(value>=-3 && value<=-3 && value==2) return 1;
003 |  return 0;
004 | }
```

## C08_contradiction_corrected
[]
```c
001 | int classify_value(int value) {
002 |  if(value>=-3 && value<=-3 && value==-3) return 1;
003 |  return 0;
004 | }
```

## C09_repair_null
[
  {
    "id": "C09_repair_null-R1",
    "line": 3,
    "column": 1,
    "source_evidence": "}",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "syntax",
    "allowed_ids": [],
    "message_any": [
      "expected",
      ";"
    ]
  },
  {
    "id": "C09_repair_null-R2",
    "line": 6,
    "column": 2,
    "source_evidence": "return *p;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "memory_safety",
    "allowed_ids": [
      "core.NullDereference",
      "-Wanalyzer-null-dereference",
      "nullPointer"
    ],
    "message_any": [
      "null"
    ]
  }
]
```c
001 | int helper(void) {
002 |  return 17
003 | }
004 | int isolated_read(void) {
005 |  int *p=0;
006 |  return *p;
007 | }
```

## C10_isolate_null
[
  {
    "id": "C10_isolate_null-R1",
    "line": 2,
    "column": 2,
    "source_evidence": "return missing_m8_value;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "semantic/type",
    "allowed_ids": [],
    "message_any": [
      "undeclared",
      "not declared"
    ]
  },
  {
    "id": "C10_isolate_null-R2",
    "line": 6,
    "column": 2,
    "source_evidence": "return *p;",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "memory_safety",
    "allowed_ids": [
      "core.NullDereference",
      "-Wanalyzer-null-dereference",
      "nullPointer"
    ],
    "message_any": [
      "null"
    ]
  }
]
```c
001 | int unavailable_helper(void) {
002 |  return missing_m8_value;
003 | }
004 | int independent_read(void) {
005 |  int *p=0;
006 |  return *p;
007 | }
```

## C11_missing_header
[
  {
    "id": "C11_missing_header-R1",
    "line": 1,
    "column": 1,
    "source_evidence": "#include",
    "independently_verified": false,
    "reviewer": null,
    "review_status": "pending_human_review",
    "category": "configuration",
    "allowed_ids": [],
    "message_any": [
      "file not found",
      "No such file"
    ]
  }
]
```c
001 | #include "m8_absent_dependency_2026.h"
002 | int config_value(void) { return 7; }
```

## C12_valid_full
[]
```c
001 | #include <stddef.h>
002 | #define ROWS 3
003 | typedef struct { int slots[ROWS]; const char *name; } Record;
004 | int total_record(void) {
005 |  Record r={{2,4,6},"new evaluation"};
006 |  int total=0;
007 |  for(size_t i=0;i<ROWS;i++) total+=r.slots[i];
008 |  return total;
009 | }
```
