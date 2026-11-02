"""Separate supported differences, unsupported checks, and failed analysis."""
from phase6.v12.semantics import projection
from phase6.v11.semantics import compare

STATUSES=('VERIFIED_STRUCTURAL_CHANGE','NO_DETECTED_STRUCTURAL_CHANGE','UNKNOWN','UNSUPPORTED','CHECK_FAILED')


def inserted_empty_body(source,candidate,tree):
    semicolons=set();shift=0
    for e in candidate['changes']:
        if not e['deleted']:
            semicolons.update(e['offset']+shift+i for i,c in enumerate(e['inserted']) if c==';')
        shift+=len(e['inserted'])-len(e['deleted'])
    if not semicolons:return False,False
    # Clang AST offsets count UTF-8 bytes; normalized editor edits count Unicode
    # code points. Convert only after applying cumulative character shifts.
    semicolons={len(candidate['source'][:at].encode('utf-8')) for at in semicolons}
    source_bytes=source.encode('utf-8')
    unknown_mapping=False
    for f in tree.get('inner',[]):
        loc=f.get('loc',{});at=loc.get('offset');name=f.get('name','')
        if f.get('kind')!='FunctionDecl' or 'includedFrom' in loc or at is None or source_bytes[at:at+len(name.encode('utf-8'))]!=name.encode('utf-8'):continue
        pending=[f]
        while pending:
            node=pending.pop();children=[c for c in node.get('inner',[]) if c.get('kind')];pending.extend(children)
            if node.get('kind') not in ('IfStmt','WhileStmt','ForStmt'):continue
            for child in children:
                if child.get('kind')!='NullStmt':continue
                begin=child.get('range',{}).get('begin',{})
                if 'offset' not in begin:unknown_mapping=True
                elif begin['offset'] in semicolons:return True,unknown_mapping
    return False,unknown_mapping


def analyze(source,candidate,reference=None):
    if candidate['validation']['status']!='VALID':return dict(status='CHECK_FAILED',reason='Candidate compilation/AST validation did not complete',checks={})
    tree=candidate.get('_tree')
    if tree is None:return dict(status='CHECK_FAILED',reason='Compiler AST missing after validation',checks={})
    try:
        hazard,mapping_unknown=inserted_empty_body(candidate['source'],candidate,tree)
        # Function offsets are in the repaired program; inserted positions are
        # computed from original-coordinate changes plus their cumulative shift.
        if hazard:return dict(status='VERIFIED_STRUCTURAL_CHANGE',reason='This inserted semicolon creates an empty if/loop body, changing statement ownership.',checks={'introduced_empty_control_body':'CHANGED'})
        if mapping_unknown:return dict(status='UNSUPPORTED',reason='Macro expansion prevents reliable control-body source mapping',checks={},mapping_reliable=False)
        p=projection(candidate['source'],dict(status='VALID',tree=tree));candidate['_projection']=p
        if reference is not None and p is not None:
            checks=compare(reference,p)
            changed=any(c['status']=='CHANGED' for c in checks.values())
            return dict(status='VERIFIED_STRUCTURAL_CHANGE' if changed else 'NO_DETECTED_STRUCTURAL_CHANGE',
                        reason='Compared supported structure with a valid historical snapshot; behavioral equivalence is not proved',checks=checks)
        if p is None:return dict(status='UNSUPPORTED',reason='Whole-program structural comparison does not support these C constructs or preprocessing',checks={})
        return dict(status='UNKNOWN',reason='Candidate AST is supported but no valid reference establishes preservation',checks={})
    except (ValueError,TypeError,KeyError,RecursionError):
        return dict(status='CHECK_FAILED',reason='Structural analysis failed; automatic fallback is blocked',checks={})
