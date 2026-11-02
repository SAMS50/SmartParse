"""Supported structural evidence, distinct from behavioral equivalence.

Extend v11 with scalar globals and expression-statement ownership. Pointers,
preprocessing, records and unknown AST kinds remain unsupported.
"""
import re
from phase6.v11.semantics import Validator, CHECKS, ALLOWED, compare


def projection(source, validation):
    if validation['status']!='VALID':return None
    if not source.isascii() or re.search(r'#|\b(?:volatile|_Atomic|asm|__attribute__)\b',source):return None
    nodes=[n for n in validation['tree'].get('inner',[]) if n.get('loc',{}).get('offset') is not None and not n.get('isImplicit')]
    if not nodes or any(n.get('kind') not in ('FunctionDecl','VarDecl') for n in nodes):return None
    out={k:[] for k in CHECKS};decls={};refs=[];supported=True
    def shape(n):
        return (n.get('kind'),n.get('opcode'),n.get('name'),n.get('value'),
                n.get('type',{}).get('qualType'),tuple(shape(c) for c in n.get('inner',[]) if c.get('kind')))
    def walk(n,path,blocks,owners,function,parent=None,slot=0):
        nonlocal supported
        kind=n.get('kind');typ=n.get('type',{}).get('qualType','')
        if kind not in ALLOWED:supported=False
        if ('*' in typ and n.get('castKind')!='FunctionToPointerDecay') or '[' in typ or re.search(r'\b(?:struct|union|volatile|_Atomic)\b',typ):supported=False
        children=[c for c in n.get('inner',[]) if c.get('kind')]
        if kind=='FunctionDecl':
            function=n.get('name')
            # Direct body inventory detects membership/count changes, not value equivalence.
            bodies=[c for c in children if c['kind']=='CompoundStmt']
            inventory=tuple(tuple((s.get('kind'),s.get('name')) for s in b.get('inner',[])) for b in bodies)
            out['function_boundaries'].append((function,typ,inventory))
        if kind=='CompoundStmt':
            blocks=blocks+(path,);out['block_boundaries'].append((function,path,tuple(c['kind'] for c in children)))
        statement_slot=parent=='CompoundStmt' or (parent in ('IfStmt','WhileStmt') and slot>0) or parent=='ForBody'
        if kind.endswith('Stmt') and kind not in ('CompoundStmt','DeclStmt') or (statement_slot and kind in ('BinaryOperator','UnaryOperator','CallExpr')):
            out['statement_ownership'].append((function,path,kind,owners))
        if kind in ('IfStmt','ForStmt','WhileStmt'):out['control_flow'].append((function,path,shape(n)))
        if kind in ('VarDecl','ParmVarDecl'):
            decls[n.get('id')]=(function,path,n.get('name'))
            out['variable_scope'].append((function,n.get('name'),typ,blocks))
        if kind=='DeclRefExpr':refs.append((function,path,n.get('referencedDecl',{})))
        if kind in ('BinaryOperator','UnaryOperator','ParenExpr','IntegerLiteral','FloatingLiteral','CallExpr'):
            out['expression_grouping'].append((function,path,shape(n)))
        for i,c in enumerate(children):
            child_owners=owners+((kind,path,i),) if kind in ('IfStmt','ForStmt','WhileStmt') else owners
            parent_kind='ForBody' if kind=='ForStmt' and i==len(children)-1 else kind
            walk(c,path+(i,),blocks,child_owners,function,parent_kind,i)
    for i,n in enumerate(nodes):walk(n,(i,),(),(),None)
    for function,path,ref in refs:
        target=decls.get(ref.get('id'))
        if target is None and ref.get('kind')!='FunctionDecl':supported=False
        out['variable_binding'].append((function,path,target or ('function',ref.get('name'))))
    return out if supported else None
