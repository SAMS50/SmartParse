"""Conservative physical Clang AST projections; never analyze a rejected AST.

Supported: self-contained ASCII C functions with scalar locals, arithmetic,
if/else/for/while, blocks, calls and returns. Preprocessing, pointers, arrays,
records, casts, goto/switch, volatile/atomic and compiler extensions abstain.
Projection equality is structural evidence, not semantic equivalence.
"""
import json
import re
import subprocess
from phase6.v3.execution import bounded_run
from smartparse_cli.tools import locate

CHECKS = ('statement_ownership','block_boundaries','variable_scope','variable_binding',
          'expression_grouping','function_boundaries','control_flow')
ALLOWED = set('TranslationUnitDecl FunctionDecl ParmVarDecl VarDecl CompoundStmt DeclStmt IfStmt ForStmt WhileStmt ReturnStmt BinaryOperator UnaryOperator DeclRefExpr IntegerLiteral FloatingLiteral ImplicitCastExpr ParenExpr CallExpr NullStmt BreakStmt ContinueStmt'.split())


class Validator:
    def __init__(self, standard='c11', max_calls=32, seconds=15):
        import time
        self.compiler=locate('clang');self.standard=standard;self.max_calls=max_calls
        self.calls=0;self.cache={};self.deadline=time.monotonic()+seconds

    def inspect(self, source):
        import time
        if source in self.cache:return self.cache[source]
        if not self.compiler or self.calls>=self.max_calls or time.monotonic()>=self.deadline:
            return dict(status='UNVERIFIED',reason='Clang unavailable or validation budget exhausted',tree=None)
        self.calls+=1
        try:
            p=bounded_run([self.compiler,'-x','c',f'-std={self.standard}','-fsyntax-only',
                '-Wno-everything','-fdiagnostics-parseable-fixits','-Xclang','-ast-dump=json','-'],input=source.encode('utf-8'),
                capture_output=True,shell=False,timeout=max(.01,min(2,self.deadline-time.monotonic())))
            tree=json.loads(p.stdout) if p.returncode==0 else None
            diagnostic=p.stderr.decode('utf-8',errors='replace')[:2000]
            status='VALID' if tree else 'INVALID' if p.returncode==1 and 'fatal error:' not in diagnostic else 'UNVERIFIED'
            result=dict(status=status,reason=diagnostic,tree=tree)
        except (OSError,ValueError,subprocess.TimeoutExpired):
            result=dict(status='UNVERIFIED',reason='Clang invocation or AST unavailable',tree=None)
        self.cache[source]=result
        return result


def projection(source, validation):
    if validation['status']!='VALID':return None
    if not source.isascii() or re.search(r'#|\b(?:volatile|_Atomic|asm|__attribute__)\b',source):return None
    tree=validation['tree']
    functions=[n for n in tree.get('inner',[]) if n.get('kind')=='FunctionDecl']
    # Reject user globals/types instead of silently excluding them.
    if any(n.get('loc',{}).get('offset') is not None and n.get('kind')!='FunctionDecl' for n in tree.get('inner',[])):return None
    out={k:[] for k in CHECKS};decls={};refs=[]
    def shape(n):
        return (n.get('kind'),n.get('opcode'),n.get('name'),n.get('value'),
                n.get('type',{}).get('qualType'),tuple(shape(c) for c in n.get('inner',[]) if c))
    supported=True
    def walk(n,path,blocks,owners,function):
        nonlocal supported
        kind=n.get('kind')
        if not kind:return
        if kind not in ALLOWED:supported=False
        typ=n.get('type',{}).get('qualType','')
        if ('*' in typ and n.get('castKind')!='FunctionToPointerDecay') or '[' in typ or re.search(r'\b(?:struct|union|volatile|_Atomic)\b',typ):supported=False
        children=[c for c in n.get('inner',[]) if c.get('kind')]
        if kind=='FunctionDecl':
            function=n.get('name');out['function_boundaries'].append((function,typ))
        if kind=='CompoundStmt':
            blocks=blocks+(path,);out['block_boundaries'].append((function,path,tuple(c['kind'] for c in children)))
        if kind in ('IfStmt','ForStmt','WhileStmt'):
            out['control_flow'].append((function,path,shape(n)))
            owners=owners+((kind,path),)
        if kind.endswith('Stmt') and kind not in ('CompoundStmt','DeclStmt'):
            out['statement_ownership'].append((function,path,kind,owners))
        if kind in ('VarDecl','ParmVarDecl'):
            decls[n.get('id')]=(function,path,n.get('name'))
            out['variable_scope'].append((function,n.get('name'),typ,blocks))
        if kind=='DeclRefExpr':refs.append((function,path,n.get('referencedDecl',{})))
        if kind in ('BinaryOperator','UnaryOperator','ParenExpr','IntegerLiteral','FloatingLiteral','CallExpr'):
            out['expression_grouping'].append((function,path,shape(n)))
        for i,c in enumerate(children):walk(c,path+(i,),blocks,owners,function)
    for i,n in enumerate(functions):walk(n,(i,),(),(),None)
    for function,path,ref in refs:
        target=decls.get(ref.get('id'))
        if target is None and ref.get('kind')!='FunctionDecl':supported=False
        out['variable_binding'].append((function,path,target or ('function',ref.get('name'))))
    return out if supported and functions else None


def compare(reference, candidate):
    if reference is None or candidate is None:
        return {k:dict(status='UNKNOWN',explanation='No supported valid reference/candidate AST') for k in CHECKS}
    return {k:dict(status='NOT_APPLICABLE' if not reference[k] and not candidate[k] else
                         'PRESERVED' if reference[k]==candidate[k] else 'CHANGED',
                   explanation='Compared supported physical AST projections against valid history snapshot') for k in CHECKS}
