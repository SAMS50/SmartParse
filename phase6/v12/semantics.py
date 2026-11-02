"""Supported structural evidence, distinct from behavioral equivalence.

Extend v11 with scalar globals and expression-statement ownership. Pointers,
preprocessing, records and unknown AST kinds remain unsupported.
"""
import re
from phase6.v11.semantics import Validator as CompilerValidator, CHECKS, ALLOWED, compare


class Validator(CompilerValidator):
    def inspect(self,source):
        result=super().inspect(source)
        # Older Clang versions may diagnose this C99+ constraint as a warning and
        # still return zero. A recovery candidate must not depend on that extension.
        if self.standard!='c89' and result['status']=='VALID' and re.search(r'implicit declaration of function|call to undeclared function',result['reason']):
            return dict(status='INVALID',reason='C99+ undeclared-function constraint: '+result['reason'],tree=None)
        if self.standard!='c89' and result['status']=='VALID':
            declarations=set();references=[];pending=[result['tree']]
            while pending:
                node=pending.pop();pending.extend(node.get('inner',[]))
                if node.get('kind')=='FunctionDecl':declarations.add(node.get('id'))
                ref=node.get('referencedDecl',{})
                if ref.get('kind')=='FunctionDecl':references.append(ref)
            missing=[r for r in references if r.get('id') not in declarations]
            if missing:
                builtin=any(r.get('name','').startswith('__builtin_') for r in missing)
                return dict(status='UNVERIFIED' if builtin else 'INVALID',
                            reason='No function declaration in complete AST for: '+', '.join(sorted({r.get('name','?') for r in missing})),tree=None)
        return result


def projection(source, validation):
    if validation['status']!='VALID':return None
    if not source.isascii() or re.search(r'#|\b(?:volatile|_Atomic|asm|__attribute__)\b',source):return None
    nodes=[n for n in validation['tree'].get('inner',[]) if n.get('loc',{}).get('offset') is not None and not n.get('isImplicit')]
    if not nodes or any(n.get('kind') not in ('FunctionDecl','VarDecl') for n in nodes):return None
    out={k:[] for k in CHECKS};decls={};refs=[];supported=True
    declared_functions={n.get('id') for n in nodes if n.get('kind')=='FunctionDecl'}
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
        if target is None and (ref.get('kind')!='FunctionDecl' or ref.get('id') not in declared_functions):supported=False
        out['variable_binding'].append((function,path,target or ('function',ref.get('name'))))
    return out if supported else None
