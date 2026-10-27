"""Reproduce the new reference without modifying the frozen Phase 5 oracle.

This is a documented manual migration, not an automatic defect detector.
Source review remains single-reviewer and provisional until independently audited.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE_ID = 'sample-500-cleaned'
BOUNDS = {55, 74, 96, 114, 128, 202, 209, 214, 219, 229, 245, 299, 342, 387, 432, 474, 479}
CONTRACTS = {
    96: 'count denotes the actual accessible element extent',
    114: 'count denotes the actual accessible element extent',
    128: 'input length may exceed BUFFER_SIZE-1; no external input bound is guaranteed',
    202: 'length is the accessible number of array elements',
    209: 'destination must be a NUL-terminated string for its subsequent consumer',
    214: 'length is the accessible number of array elements',
    219: 'size is the capacity in bytes, not the intended prefix length',
    229: 'text capacity is insufficient for the suffix including NUL',
    252: 'pointer is a nonnull live heap allocation owned by this call',
    257: 'a caller can pass a null or otherwise invalid pointer',
    299: 'input may contain a word longer than seven characters',
    342: 'length is the accessible number of array elements',
    387: 'name may exceed NAME_SIZE-1 characters',
    439: 'global_label refers to a previously successful allocation on entry',
    474: 'count is the number of accessible scores elements',
    479: 'scores contains exactly MAX_ITEMS elements',
    405: 'the missing return value is used when the nonpositive branch is taken',
    194: 'INT_MIN is permitted as an input',
    456: 'b may be zero under the caller contract',
    330: 'finite sorted array with accessible length elements; search must terminate',
}
TRIGGERS = {
    30:'Parse the global declaration before global_label.', 55:'Initialization reaches i == MAX_ITEMS.',
    65:'Examine average(scores, 0) with count == 0 and its integer division.',
    71:'A result from duplicate_text outlives its local buffer and is passed to free/printf.',
    74:'Execute the strcpy with the 49-byte literal and 32-byte field.',
    78:'Examine unsafe_divide(5, 0) with b == 0.',81:'Examine reset_student(NULL).',
    82:'Parse main return statement before its closing brace.',88:'Inputs a,b differ such that subtraction disagrees with the claimed addition contract.',
    96:'Inclusive loop reaches index count.',99:'Nonzero count does not divide the sum exactly; zero divisor is a separate issue.',
    104:'print_student is invoked; assignment sets student to null and condition is false.',
    114:'Search reaches index count before returning.',115:'Search condition executes and modifies an element id.',
    119:'No element matches the requested id.',128:'Non-null input exceeds the local buffer capacity.',
    129:'duplicate_text returns its local buffer address.',149:'An inactive element is examined and overwritten.',
    164:'Condition is false but the following block still runs.',173:'a < b under a maximum-value contract.',
    179:'An even value is passed under a nonzero-means-even contract.',187:'value > high and low != high under clamp contract.',
    194:'value == INT_MIN.',202:'Loop reaches index length.',209:'source length is at least NAME_SIZE.',
    214:'Index length is evaluated.',219:'memset writes size+1 bytes.',224:'Equal text exists at different addresses under content-equality contract.',
    229:'Suffix and terminator exceed available capacity.',236:'make_integer returns its local address.',
    245:'malloc succeeds and buffer[size] is written.',252:'First free releases a valid allocation; second free repeats release.',
    257:'pointer is invalid/null when dereferenced.',263:'Function returns after publishing address of local value.',
    271:'malloc succeeds and function exits without transfer/release.',278:'fopen fails, or conversion fails while stream is valid; separate atoms below.',
    286:'fopen fails before fprintf.',287:'fopen succeeds and write_report returns without fclose.',
    292:'Format %d consumes the variadic int value where int* is required.',299:'Input word is longer than the destination capacity.',
    307:'fopen succeeds and early return bypasses fclose.',308:'fopen fails and fclose receives null.',
    317:'n > 1 skips factorial loop; n <= 1 can enter a growing signed-arithmetic loop.',
    330:'Target is absent and an iteration computes mid == low without progressing.',
    342:'Nonempty reversal reaches first iteration with length-element extent.',340:'All-index swap loop processes both members of each pair.',
    351:'Loop condition assigns target to array element instead of testing equality.',368:'Any month is evaluated; conjunction requires mutually exclusive ranges.',
    377:'value is outside the named enum domain under an application-domain contract.',
    382:'Floating numerator divided by zero; environment and intended behavior are unresolved.',
    387:'Input name exceeds field capacity.',393:'Return string literal from int-returning function.',
    405:'value <= 0 falls through; caller uses return value.',409:'Call add_numbers with one argument against a two-argument prototype.',
    414:'Resolve either use of mystery_value; no declaration exists.',421:'Consume long with printf %d.',
    427:'Two threads access global_count without synchronization; no such threads are established here.',
    432:'Allocate strlen(text) bytes then copy terminator; allocation failure and prior ownership are separate atoms.',
    439:'Reset writes global_label after free; initial null state is a separate path.',
    445:'Toggle yields only 0/1, yet comparison to 2 is returned.',451:'part is not divisible by nonzero whole under fractional-percentage intent.',
    456:'b == 0 when modulo is evaluated.',464:'value < 0 under conventional sign contract.',
    474:'Write occurs at index count.',479:'index == MAX_ITEMS passes guard.',486:'Distinct a,b point to unequal values under swap contract.',
    494:'Compare char to multicharacter backslash-zero constant.',496:'Terminating loop completes under length-return contract.'
}
# Wording predicates are evidence filters, never automatic semantic truth.
PATTERNS = {
    30:[r'expected',r"';'|semicolon"],82:[r'expected',r"';'|semicolon"],
    55:[r'out.of.bounds|buffer overflow|array.*(index|bound)'],65:[r'division by zero|divide.*zero'],
    71:[r'non.heap|stack.*free|invalid.*free'],74:[r'overflow|destination.*size'],78:[r'division by zero|divide.*zero'],
    81:[r'null',r'dereference|access|argument'],88:[r'addition|subtract|postcondition|assertion'],
    96:[r'out.of.bounds|array.*bound'],99:[r'integer division|loss of precision|truncat'],
    104:[r'assignment',r'condition|truth value'],114:[r'out.of.bounds|array.*bound'],
    115:[r'assignment',r'condition|truth value'],119:[r'sentinel|postcondition|assertion'],
    128:[r'overflow|out.of.bounds'],129:[r'address',r'local|stack'],149:[r'assignment',r'condition|truth value'],
    164:[r'empty body|empty-body|does not guard'],173:[r'postcondition|identical.*branch|repeated.*branch'],
    179:[r'postcondition|assertion'],187:[r'postcondition|assertion|clamp'],194:[r'overflow',r'negat|signed|integer'],
    202:[r'out.of.bounds|array.*bound'],209:[r'terminat|strncpy.*truncat'],214:[r'out.of.bounds|array.*bound'],
    219:[r'out.of.bounds|overflow'],224:[r'pointer.*compar|compar.*pointer'],229:[r'overflow|out.of.bounds'],
    236:[r'address',r'local|stack'],245:[r'out.of.bounds|overflow'],252:[r'double.free|released memory|already.*freed'],
    257:[r'null|invalid pointer',r'dereference|access'],263:[r'stack.*address|address.*local|stack.*escap'],
    271:[r'leak',r'memory|allocation|values'],278:[r'null',r'stream|file|fscanf|argument'],
    286:[r'null',r'stream|file|fprintf|argument'],287:[r'leak|not closed',r'stream|file'],
    292:[r'format',r'int\s*\*|int\*|pointer'],299:[r'scanf|format',r'width|overflow|bound'],
    307:[r'leak|not closed',r'stream|file'],308:[r'null',r'fclose|stream|file|argument'],
    317:[r'loop|factorial',r'condition|progress|postcondition'],330:[r'infinite loop|no progress|non.terminat'],
    342:[r'out.of.bounds|array.*bound'],340:[r'reversal|reverse|postcondition'],351:[r'assignment',r'condition|truth value'],
    368:[r'always false|mutually exclusive|contradict|impossible'],377:[r'enum|domain'],382:[r'division by zero'],
    387:[r'overflow|out.of.bounds'],393:[r'pointer',r'integer|int'],405:[r'non.void|return',r'end|fall|not return'],
    409:[r'too few arguments|not enough arguments'],414:[r'undeclared',r'mystery_value'],
    421:[r'format',r'long'],427:[r'data race|race condition'],432:[r'overflow|out.of.bounds|allocation.*size'],
    439:[r'use.after.free|freed memory|released memory'],445:[r'always false|range|postcondition'],
    451:[r'precision|truncat|integer division'],456:[r'modulo.*zero|division by zero|remainder.*zero'],
    464:[r'postcondition|identical.*branch|repeated.*branch'],474:[r'out.of.bounds|array.*bound'],
    479:[r'out.of.bounds|array.*bound'],486:[r'swap|overwritten|lost.*value|postcondition'],
    494:[r'multi.character|multi-character|comparison.*always true'],496:[r'postcondition|length.*off.by.one']
}


def build():
    historical_path = ROOT / 'acceptance/sample_reference.json'
    historical = json.loads(historical_path.read_text(encoding='utf-8'))
    source = ROOT / 'acceptance/cleaned/c_error_detection_500_lines.c'
    defects = []
    uncertain_logic = {88,99,119,173,179,187,224,317,340,377,427,445,451,464,486,496,104,115,149,351}
    for index, old in enumerate(historical['issues'], 1):
        line = old['line']
        category = ('bounds' if line in BOUNDS else 'memory safety' if old['kind'] in ('memory safety','resource')
                    else 'undefined behavior' if old['kind']=='runtime' else 'program logic' if old['kind']=='logic' else old['kind'])
        contract = CONTRACTS.get(line)
        oracle = 'uncertain' if line in uncertain_logic or line==382 else 'conditional' if contract else 'established'
        if old.get('uncertain') and not contract:
            oracle = 'uncertain'
        if oracle=='uncertain' and not contract:
            contract = 'application contract must establish: ' + old['description']
        analysis = 'compiler' if line in (30,82,292,393,405,409,414,421,74,129,236,494,104,115,149,164,351) else 'logic' if category=='program logic' else 'analyzer'
        atom = {'id':f'SP6-L{line:04d}-01','historical_entry':index,'historical_line':line,
                'source_id':SOURCE_ID, 'category':category, 'tags':[old['kind']],
                'description':old['description'], 'source_locations':[line], 'sink_locations':[line],
                'diagnostic_anchors':sorted({line,*old['diagnostic_lines']}),
                'triggering_conditions':[TRIGGERS[line]],
                'required_contracts':[{'id':f'C-L{line:04d}', 'statement':contract,'basis':'explicit evaluation assumption, not inferred as satisfied'}] if contract else [],
                'oracle_status':oracle,'required_analysis':analysis,
                'root_cause_id':f'ROOT-L{line:04d}', 'relationships':[],
                'admissible_evidence':{'meaning':old['description'],
                    'rules':[{'backends':['gcc','clang','clang-static-analyzer'], 'severities':['error','fatal error','warning'],
                              'message_all':PATTERNS[line]}],
                    'rejected_evidence':['notes alone','line proximity without matching meaning','unrelated undeclared-name/type cascade']},
                'review_provenance':{'reviewer':'Codex source review','status':'provisional single-reviewer reference',
                                     'rationale':'Migrated from frozen oracle and inspected source; conditions/intent are explicit, not presumed.'}}
        defects.append(atom)
    byline = {d['historical_line']:d for d in defects}
    def split(line, suffix, description, source_lines, sink_lines, patterns, *, category=None, contracts=None, oracle=None, analysis='analyzer'):
        import copy
        original = byline[line]
        atom = copy.deepcopy(original)
        atom.update(id=f'SP6-L{line:04d}-{suffix:02d}', description=description,
                    source_locations=source_lines,sink_locations=sink_lines,
                    diagnostic_anchors=sorted(set(source_lines+sink_lines)), required_analysis=analysis,
                    root_cause_id=f'ROOT-L{line:04d}-{suffix:02d}')
        if category: atom['category']=category
        if contracts is not None:
            atom['required_contracts']=contracts
        if oracle: atom['oracle_status']=oracle
        atom['admissible_evidence']['meaning']=description
        atom['admissible_evidence']['rules'][0]['message_all']=patterns
        atom['relationships']=[{'kind':'split_from_same_historical_entry','target':original['id']}]
        original['relationships'].append({'kind':'split_from_same_historical_entry','target':atom['id']})
        defects.append(atom)
        return atom
    # Independent objects share a single erroneous loop-bound root.
    byline[55].update(description='Out-of-bounds writes to students at i == MAX_ITEMS',source_locations=[46,55],sink_locations=[56,57,59],diagnostic_anchors=[55,56,57,59])
    byline[55]['admissible_evidence']['rules'][0]['message_all']=[*PATTERNS[55],r'students']
    extra=split(55,2,'Out-of-bounds read of scores at i == MAX_ITEMS',[47,55],[58],[*PATTERNS[55],r'scores'],category='bounds')
    extra['root_cause_id']=byline[55]['root_cause_id']
    extra['triggering_conditions']=['Initialization reaches i == MAX_ITEMS and reads scores[i].']
    # Do not incorrectly assert successful heap release of a dangling stack address.
    byline[71].update(description='Invalid free of pointer returned from expired stack buffer',source_locations=[68,129],sink_locations=[70],diagnostic_anchors=[70],root_cause_id='ROOT-L0129')
    byline[71]['admissible_evidence']['meaning']=byline[71]['description']
    extra=split(71,2,'Use of pointer into expired duplicate_text stack buffer',[68,129],[71],[r'dangling|stack.*(expired|return)|use.after.scope'],contracts=[],oracle='established')
    extra['root_cause_id']='ROOT-L0129'
    extra['triggering_conditions']=['duplicate_text has returned and printf attempts to read its expired local buffer.']
    extra['diagnostic_anchors']=[71]
    # A suspicious assignment is not evidence of the subsequent null dereference.
    extra=split(104,2,'Dereference after unconditional assignment of null to student',[104],[108],[r'null',r'dereference|access'],category='memory safety',contracts=[],oracle='established')
    extra['root_cause_id']=byline[104]['root_cause_id']
    extra['triggering_conditions']=['student = NULL executes, false branch continues to student->id/name/score at 108.']
    byline[104]['description']='Assignment in condition; intended comparison requires application-intent review'
    extra=split(278,2,'Return of uninitialized value after failed input conversion on a valid stream',[277,278],[280],[r'uninitiali',r'value|return'],category='undefined behavior',contracts=[],oracle='established')
    extra['triggering_conditions']=['fopen succeeds; fscanf returns no assigned value; return reads uninitialized value.']
    byline[278].update(description='Use of null stream after failed fopen',source_locations=[276],sink_locations=[278])
    extra=split(317,2,'Signed arithmetic overflow on a sufficiently long entered factorial loop',[315,317],[318],[r'signed|integer',r'overflow'],category='undefined behavior',contracts=[],oracle='established')
    extra['triggering_conditions']=['n <= 1 permits repeated multiplication until signed result or loop index overflows.']
    byline[317]['description']='Loop condition inconsistent with intended factorial contract'
    # Allocation extent, failed allocation, and loss of prior ownership differ.
    byline[432].update(description='Allocation omits terminator byte consumed by strcpy',source_locations=[432],sink_locations=[433])
    extra=split(432,2,'Null destination passed to strcpy when allocation fails',[432],[433],[r'null',r'argument|destination|strcpy'],category='memory safety',contracts=[],oracle='established')
    extra['triggering_conditions']=['malloc returns NULL; strcpy is called with the null destination and valid text.']
    extra=split(432,3,'Loss of previously owned global allocation when pointer is overwritten',[432],[432],[r'leak',r'global_label|allocation|memory'],category='memory safety',
          contracts=[{'id':'C-L0432-PRIOR','statement':'global_label owns an unreleased allocation before this call','basis':'caller/global-state precondition not established'}],oracle='conditional')
    extra['triggering_conditions']=['global_label is the last owning reference to prior allocation; assignment overwrites that reference.']
    extra=split(439,2,'Null write when reset_global_label is called in initial null state',[31,438],[439],[r'null',r'dereference|access'],category='memory safety',
          contracts=[{'id':'C-L0439-NULL','statement':'reset_global_label is callable while global_label is null','basis':'entry contract not established'}],oracle='conditional')
    extra['triggering_conditions']=['global_label is NULL; free(NULL) is harmless, then global_label[0] dereferences null.']
    # Meaning strings must describe atoms, not their old bundled parent.
    for atom in defects:
        atom['admissible_evidence']['meaning']=atom['description']
    for line, target in ((71,129),(439,432)):
        byline[line]['relationships'].append({'kind':'causally_related','target':byline[target]['id']})
    return {'schema_version':'1.0','dataset_version':'1.0.0',
            'scope':'Potential operation defects; no successful whole-program execution is asserted past earlier undefined behavior.',
            'historical_baseline':{'entries':68,'clang_matched_entries':16,'reference_sha256':hashlib.sha256(historical_path.read_bytes()).hexdigest(),
                                   'reference_path':'acceptance/sample_reference.json','meaning':'Frozen Phase 5 comparison, not Phase 6 recall'},
            'sources':{SOURCE_ID:{'path':'acceptance/cleaned/c_error_detection_500_lines.c','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                                 'line_mapping':'identity with original numbered source; no source edits in Phase 6'}},
            'reference_review':'Single-reviewer provisional migration; independent oracle adjudication pending.',
            'defects':sorted(defects,key=lambda d:d['id'])}


if __name__ == '__main__':
    (HERE/'reference.json').write_text(json.dumps(build(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
