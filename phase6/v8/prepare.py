"""Author the evaluation set once, before observing analyzer outputs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def prepare():
    if (HERE / 'freeze.json').exists():
        raise RuntimeError('Already frozen; do not regenerate the holdout.')
    cases = []

    def add(identifier, cohort, source, roots, intended=None):
        path = HERE / 'fixtures' / cohort / (identifier + '.c')
        path.write_bytes(source.encode('utf-8'))
        record = dict(id=identifier, cohort=cohort, path=str(path.relative_to(ROOT)), sha256=digest(path.read_bytes()),
                      provenance='new author-created evaluation case; not independent',
                      independently_verified=False, reviewer=None, review_status='pending_human_review', roots=[])
        for number, root in enumerate(roots, 1):
            marker = root.pop('marker')
            start = source.index(marker)
            line = source.count('\n', 0, start) + 1
            record['roots'].append(dict(id=f'{identifier}-R{number}', line=line,
                column=start-source.rfind('\n', 0, start), source_evidence=marker,
                independently_verified=False, reviewer=None, review_status='pending_human_review', **root))
        if intended is not None:
            ref = path.with_suffix('.intended.txt')
            ref.write_bytes(intended.encode('utf-8'))
            record.update(intended_path=str(ref.relative_to(ROOT)), intended_sha256=digest(ref.read_bytes()))
        cases.append(record)

    # Anchors and intended repairs are authored without running malformed parsers.
    syntax = [
        ('S01', 'int orbit(int n) {\n int total=0;\n while(n>0) { total=total+n; n=n-1; }\n return total;\n}\nint sentinel=9;\n', []),
        ('S02', 'int level=3;\nif(level>1) { level=level*2; } else { level=0; }\nint tail=8;\n', []),
        ('S03', 'int pebble=4\nint ending=7;\n', [('int ending', 'insert', ';', None)]),
        ('S04', 'int summit(void) {\n return 19\n}\nint tail=2;\n', [('}', 'insert', ';', None)]),
        ('S05', 'int n=2;\nif(n>1 { n=n-1; }\nint tail=7;\n', [('{', 'insert', ')', None)]),
        ('S06', 'int n=3;\nwhile(n>0] { n=n-1; }\nint tail=4;\n', [(']', 'substitute', ')', ']')]),
        ('S07', 'int valley(void) {\n return 23;\n', [('', 'insert', '}', None)]),
        ('S08', 'int n=2;\nif(n>0;) { n=n+1; }\nint tail=5;\n', [(';)', 'delete', ')', ';')]),
        ('S09', 'int dune=4,\nint tail=6;\n', [(',', 'substitute', ';', ',')]),
        ('S10', 'int a=1\nint b=2\nint tail=3;\n', [('int b', 'insert', ';', None), ('int tail', 'insert', ';', None)]),
        ('S11', 'int x=3;\nwhile(x>0 {\n if(x==2 { x=x-1; }\n x=x-1;\n}\nint tail=1;\n', [('{\n', 'insert', ')', None), ('{ x=', 'insert', ')', None)]),
        ('S12', 'int signal=2;\nsignal=@;\nint tail=6;\n', [('@', 'unsupported', None, '@')]),
    ]
    for identifier, source, specs in syntax:
        intended = source
        roots = []
        # Apply inverse edits from right to left; empty marker denotes EOF.
        positions = []
        for marker, operation, token, actual in specs:
            at = len(source) if marker == '' else source.index(marker)
            positions.append((at, operation, token))
            roots.append(dict(marker=marker or '\n', category='syntax', operation=operation, token=token, actual=actual,
                              anchor_offset=at, allowed_ids=[], message_any=[]))
        for at, operation, token in sorted(positions, reverse=True):
            if operation == 'insert': intended = intended[:at] + token + intended[at:]
            elif operation == 'substitute': intended = intended[:at] + token + intended[at+1:]
            elif operation == 'delete': intended = intended[:at] + intended[at+1:]
        add(identifier, 'syntax', source, roots, intended if identifier != 'S12' else None)
        for root in cases[-1]['roots']:
            at = root['anchor_offset']
            root.update(line=source.count('\n',0,at)+1, column=at-source.rfind('\n',0,at))

    pairs = [
        ('null', 'memory_safety', 'return bias + *probe;', ['core.NullDereference','-Wanalyzer-null-dereference','nullPointer'], ['null','dereference'],
         'int read_probe(int bias) {\n int *probe=0;\n return bias + *probe;\n}\n', 'int read_probe(int bias) {\n int sample=11;\n int *probe=&sample;\n return bias + *probe;\n}\n'),
        ('leak', 'memory_safety', 'cells[0]=13;', ['unix.Malloc','-Wanalyzer-malloc-leak','memleak'], ['leak'],
         '#include <stdlib.h>\nvoid collect_cells(void) {\n unsigned *cells=calloc(5,sizeof *cells);\n if(!cells) return;\n cells[0]=13;\n}\n', '#include <stdlib.h>\nvoid collect_cells(void) {\n unsigned *cells=calloc(5,sizeof *cells);\n if(!cells) return;\n cells[0]=13;\n free(cells);\n}\n'),
        ('double', 'memory_safety', 'free(saved);', ['unix.Malloc','-Wanalyzer-double-free','doubleFree'], ['free'],
         '#include <stdlib.h>\nvoid release_pair(void) {\n char *block=malloc(24);\n char *saved=block;\n free(block);\n free(saved);\n}\n', '#include <stdlib.h>\nvoid release_pair(void) {\n char *block=malloc(24);\n free(block);\n}\n'),
        ('uaf', 'memory_safety', 'return alias->code;', ['unix.Malloc','-Wanalyzer-use-after-free','deallocuse'], ['free'],
         '#include <stdlib.h>\nstruct Entry { int code; };\nint release_entry(void) {\n struct Entry *item=malloc(sizeof *item);\n if(!item) return 0;\n item->code=29;\n struct Entry *alias=item;\n free(item);\n return alias->code;\n}\n', '#include <stdlib.h>\nstruct Entry { int code; };\nint release_entry(void) {\n struct Entry *item=malloc(sizeof *item);\n if(!item) return 0;\n item->code=29;\n int code=item->code;\n free(item);\n return code;\n}\n'),
        ('bounds', 'bounds', 'row[5]=31;', ['alpha.security.ArrayBoundV2','-Warray-bounds','-Wanalyzer-out-of-bounds','arrayIndexOutOfBounds'], ['bound','overflow','index'],
         'int fill_row(void) {\n int row[5]={0};\n row[5]=31;\n return row[0];\n}\n', 'int fill_row(void) {\n int row[5]={0};\n row[4]=31;\n return row[0];\n}\n'),
        ('allocation', 'bounds', '*cell=101;', ['unix.Malloc','alpha.security.ArrayBoundV2','-Wanalyzer-out-of-bounds','-Wanalyzer-allocation-size','-Wstringop-overflow','allocSize','bufferAccessOutOfBounds'], ['size','bound','overflow'],
         '#include <stdlib.h>\n_Static_assert(sizeof(short)>1,"requires multi-byte short");\nint store_cell(void) {\n short *cell=malloc(1);\n if(!cell) return 0;\n *cell=101;\n int value=*cell;\n free(cell);\n return value;\n}\n', '#include <stdlib.h>\nint store_cell(void) {\n short *cell=malloc(sizeof *cell);\n if(!cell) return 0;\n *cell=101;\n int value=*cell;\n free(cell);\n return value;\n}\n'),
        ('resource', 'resource', 'fputs("record",stream);', ['unix.Stream','-Wanalyzer-file-leak','-Wanalyzer-malloc-leak','resourceLeak'], ['leak','close'],
         '#include <stdio.h>\nvoid write_record(void) {\n FILE *stream=fopen("m8-record.txt","w");\n if(!stream) return;\n fputs("record",stream);\n}\n', '#include <stdio.h>\nvoid write_record(void) {\n FILE *stream=fopen("m8-record.txt","w");\n if(!stream) return;\n fputs("record",stream);\n fclose(stream);\n}\n'),
        ('contradiction', 'program_logic', 'if(value>=-3 && value<=-3 && value==2)', ['smartparse.semantic.contradictory_int_conjunction','alpha.deadcode.UnreachableCode','-Wlogical-op','-Wtautological-overlap-compare','incorrectLogicOperator','knownConditionTrueFalse'], ['condition','false','intersection','overlap'],
         'int classify_value(int value) {\n if(value>=-3 && value<=-3 && value==2) return 1;\n return 0;\n}\n', 'int classify_value(int value) {\n if(value>=-3 && value<=-3 && value==-3) return 1;\n return 0;\n}\n'),
    ]
    for number,(name,category,marker,ids,words,bad,good) in enumerate(pairs,1):
        root=dict(marker=marker, category=category, allowed_ids=ids,message_any=words,
                  required_contract='As written; standard library calls modeled, successful allocation/open path where guarded.',
                  admissible_line_window=1 if name in ('leak','resource') else 0)
        add(f'C{number:02d}_{name}', 'c', bad, [root])
        add(f'C{number:02d}_{name}_corrected', 'c', good, [])
    add('C09_repair_null','c','int helper(void) {\n return 17\n}\nint isolated_read(void) {\n int *p=0;\n return *p;\n}\n',[
        dict(marker='}',category='syntax',allowed_ids=[],message_any=['expected',';']),
        dict(marker='return *p;',category='memory_safety',allowed_ids=['core.NullDereference','-Wanalyzer-null-dereference','nullPointer'],message_any=['null'])])
    add('C10_isolate_null','c','int unavailable_helper(void) {\n return missing_m8_value;\n}\nint independent_read(void) {\n int *p=0;\n return *p;\n}\n',[
        dict(marker='return missing_m8_value;',category='semantic/type',allowed_ids=[],message_any=['undeclared','not declared']),
        dict(marker='return *p;',category='memory_safety',allowed_ids=['core.NullDereference','-Wanalyzer-null-dereference','nullPointer'],message_any=['null'])])
    add('C11_missing_header','c','#include "m8_absent_dependency_2026.h"\nint config_value(void) { return 7; }\n',[
        dict(marker='#include',category='configuration',allowed_ids=[],message_any=['file not found','No such file'])])
    add('C12_valid_full','c','#include <stddef.h>\n#define ROWS 3\ntypedef struct { int slots[ROWS]; const char *name; } Record;\nint total_record(void) {\n Record r={{2,4,6},"new evaluation"};\n int total=0;\n for(size_t i=0;i<ROWS;i++) total+=r.slots[i];\n return total;\n}\n',[])
    manifest=dict(schema='smartparse.evaluation_manifest',schema_version='1.0',origin='author-created; not independent',
                  independently_validated_labels=False,random_seed=None,cases=cases)
    write_json(HERE/'manifest.json',manifest)
    write_json(HERE/'policy.json',dict(schema_version='1.0',
        matching='Source hash + input-file binding + root anchor/evidence + category/identifier/meaning. Pending proposals only.',
        line_window='Exact root line; leak/resource allow next line and related path locations. Syntax parser uses exact column.',
        duplicates='One root per diagnostic; multiple diagnostics/backends for same root collapse. Notes never establish roots.',
        blocked='Compiler syntax/type evidence can support a frontend root; blocked semantic passes cannot establish successful semantic detection.',
        conditioning='Repair/isolation findings remain separate; combined original-only excludes conditioned matches.',
        metrics=dict(TP=None,FP=None,FN=None,precision=None,recall=None,F1=None,
                     reason='Independent human-adjudicated complete labels unavailable.'),
        criteria='Descriptive author-proposal evidence only; unknown unmatched findings are not confirmed false positives.',
        uncertainty='No accuracy confidence intervals or significance without validated labels; timings descriptive.'))
    write_json(HERE/'configurations.json',dict(standard='c11',include_dirs=[],defines=[],
        syntax=['panic','context_default','validation_off','validation_on'],context_default_alias='validation_on',
        extended=['compiler_gcc6','compiler_clang','extended_baseline','recovery_assisted','isolation_assisted','gcc14','cppcheck'],
        derived='combined_optional: original-only root union; conditional cohorts separate',
        limits=dict(case_seconds=45,internal_seconds=30,call_seconds=5,invocations=96,analyzer_invocations=20),
        cohort_order='manifest order; configurations in listed order; no randomization',
        tools=json.loads((HERE/'outputs/environment.json').read_text())['tools']))
    frozen={str(p.relative_to(HERE)):digest(p.read_bytes()) for p in sorted((HERE/'fixtures').rglob('*')) if p.is_file()}
    for name in ('manifest.json','policy.json','configurations.json'):
        frozen[name]=digest((HERE/name).read_bytes())
    write_json(HERE/'freeze.json',dict(schema_version='1.0',frozen_before_analysis=True,files=frozen))
    print(f'Frozen {len(cases)} author-created cases, {sum(len(c["roots"]) for c in cases)} proposed roots.')


def verify_freeze():
    frozen=json.loads((HERE/'freeze.json').read_text())['files']
    # Frozen keys were recorded on Windows. Interpret relative separators on
    # either host without rewriting the frozen manifest or its byte hashes.
    paths={name:HERE.joinpath(*name.replace('\\','/').split('/')) for name in frozen}
    failures=[name for name,sha in frozen.items() if not paths[name].is_file() or digest(paths[name].read_bytes())!=sha]
    if failures:raise RuntimeError('Frozen inputs changed: '+repr(failures))
    return len(frozen)


if __name__=='__main__':prepare()
