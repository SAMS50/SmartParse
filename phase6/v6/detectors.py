"""Narrow AST proofs and review targets, never a general C parser."""
import re
from phase6.v2.regions import functions_from_ast
from phase6.v3.policy import unescape


def walk(node,check=lambda:None):
    stack=[node];count=0
    while stack:
        n=stack.pop();count+=1
        if count>100000:raise ValueError('AST node budget exceeded')
        if count%64==0:check()
        if not isinstance(n,dict) or not isinstance(n.get('inner',[]),list):raise ValueError('malformed AST node')
        yield n
        stack.extend(reversed(n.get('inner',[])))


def strip(n):
    while n.get('kind')=='ParenExpr' or (n.get('kind')=='ImplicitCastExpr' and n.get('castKind') in ('LValueToRValue','NoOp','ArrayToPointerDecay','FunctionToPointerDecay')):
        if len(n.get('inner',[]))!=1:raise ValueError('ambiguous AST wrapper')
        n=n['inner'][0]
    return n


def integer(n):
    n=strip(n)
    if n.get('type',{}).get('qualType')!='int':return None
    if n.get('kind')=='IntegerLiteral':return int(n['value'])
    if n.get('kind')=='UnaryOperator' and n.get('opcode')=='-' and len(n.get('inner',[]))==1:
        c=n['inner'][0]
        if c.get('kind')=='IntegerLiteral' and c.get('type',{}).get('qualType')=='int':return -int(c['value'])
    return None


def contradiction(node,local_ids):
    terms=[]
    def flatten(n):
        n=strip(n)
        if n.get('kind')=='BinaryOperator' and n.get('opcode')=='&&':
            if len(n.get('inner',[]))!=2:return False
            return all(flatten(c) for c in n['inner'])
        terms.append(n);return len(terms)<=8
    if not flatten(node) or len(terms)<2:return None
    symbol=None;lower=None;upper=None;proof=[]
    for term in terms:
        if term.get('kind')!='BinaryOperator' or term.get('opcode') not in ('<','<=','>','>=','==') or len(term.get('inner',[]))!=2:return None
        left,right=map(strip,term['inner']);op=term['opcode']
        if left.get('kind')!='DeclRefExpr':
            left,right=right,left;op={'<':'>','<=':'>=','>':'<','>=':'<=','==':'=='}[op]
        ref=left.get('referencedDecl',{});value=integer(right)
        if (left.get('kind')!='DeclRefExpr' or ref.get('id') not in local_ids or value is None or
                left.get('type',{}).get('qualType')!='int' or ref.get('type',{}).get('qualType')!='int'):return None
        if symbol is None:symbol=ref['id']
        if symbol!=ref['id']:return None
        lo=value+1 if op=='>' else value if op in ('>=','==') else None
        hi=value-1 if op=='<' else value if op in ('<=','==') else None
        if lo is not None:lower=lo if lower is None else max(lower,lo)
        if hi is not None:upper=hi if upper is None else min(upper,hi)
        proof.append({'operator':op,'constant':value,'operand_type':'int'})
    if lower is not None and upper is not None and lower>upper:
        return {'symbol_decl_id':symbol,'constraints':proof,'intersection_lower':lower,'intersection_upper':upper,
                'assumptions':['ordinary nonvolatile signed int reads; no intervening side effects',
                               'defined C execution; no claim about programmer intent or arbitrary reachability']}
    return None


def precision(node,local_ids):
    if node.get('kind')!='ImplicitCastExpr' or node.get('castKind')!='IntegralToFloating' or len(node.get('inner',[]))!=1:return None
    division=strip(node['inner'][0])
    if division.get('kind')!='BinaryOperator' or division.get('opcode')!='/' or division.get('type',{}).get('qualType')!='int':return None
    operands=division.get('inner',[])
    if len(operands)!=2:return None
    values=[]
    for operand in operands:
        n=strip(operand);value=integer(n);ref=n.get('referencedDecl',{})
        if n.get('type',{}).get('qualType')!='int':return None
        if value is None and not (n.get('kind')=='DeclRefExpr' and ref.get('id') in local_ids and ref.get('type',{}).get('qualType')=='int'):return None
        values.append(value)
    if values[1]==0:return None # Existing zero-division diagnostics are a separate issue.
    if all(v is not None for v in values) and values[0]%values[1]==0:return None
    return {'operand_types':['int','int'],'division_type':'int','conversion_type':node.get('type',{}).get('qualType'),
            'constant_operands':values,'assumptions':['division must be defined, including nonzero divisor and representable quotient',
                  'floating context suggests review only; intentional truncation remains possible'],
            'explanation':'Integer division occurs before the implicit floating conversion; any fractional part is already discarded.'}


def input_capacity(node,local_ids,stdio_ids):
    if node.get('kind')!='CallExpr' or len(node.get('inner',[]))!=3:return None
    callee,fmt,destination=map(strip,node['inner'])
    if callee.get('referencedDecl',{}).get('id') not in stdio_ids:return None
    if fmt.get('kind')!='StringLiteral':return None
    value=fmt.get('value','')
    if not (value.startswith('"') and value.endswith('"')):return None
    literal=unescape(value[1:-1].encode('utf-8'));match=re.fullmatch(rb'%([0-9]{0,8})s',literal)
    if not match:return None
    ref=destination.get('referencedDecl',{});array=re.fullmatch(r'char\[([0-9]+)\]',destination.get('type',{}).get('qualType',''))
    if destination.get('kind')!='DeclRefExpr' or ref.get('id') not in local_ids or not array:return None
    capacity=int(array[1]);width=int(match[1]) if match[1] else None
    if not 0<capacity<=1048576 or width==0:return None
    if width is not None and width+1<=capacity:return None
    return {'capacity_bytes':capacity,'format':literal.decode(),'maximum_characters':width,'terminator_bytes':1,
            'maximum_required_bytes':width+1 if width is not None else None,
            'assumptions':['compiler-recognized included scanf obeys the standard C library contract',
                           'a sufficiently long successfully converted input would be required for overflow'],
            'explanation':'No conversion width bounds input to this known char array.' if width is None else 'Conversion width plus terminating NUL can exceed the known array capacity.'}


def scan(tree,path,data,check=lambda:None):
    data.decode('utf-8-sig')
    if re.search(rb'^\s*#\s*(?:line\b|\d)',data,re.M):raise ValueError('presumed source locations unsupported')
    nodes=list(walk(tree,check));regions,excluded=functions_from_ast(tree,str(path),data)
    functions={n.get('name'):n for n in tree.get('inner',[]) if n.get('kind')=='FunctionDecl' and any(c.get('kind')=='CompoundStmt' for c in n.get('inner',[]))}
    stdio_ids=set()
    # Builtin + format attributes and included declaration, not spelling alone.
    lookalike=any(n.get('kind')=='FunctionDecl' and n.get('name')=='scanf' and any(c.get('kind')=='CompoundStmt' for c in n.get('inner',[])) for n in nodes)
    if not lookalike:
        for n in tree.get('inner',[]):
            attrs={c.get('kind') for c in n.get('inner',[])}
            if n.get('kind')=='FunctionDecl' and n.get('name')=='scanf' and n.get('loc',{}).get('includedFrom') and {'BuiltinAttr','FormatAttr'}<=attrs:
                stdio_ids.add(n['id'])
    found=[];abstentions=[]
    for region in regions:
        function=functions.get(region['name'])
        if function is None:continue
        local_ids={n['id'] for n in walk(function,check) if n.get('kind') in ('VarDecl','ParmVarDecl') and n.get('type',{}).get('qualType') in ('int',) and n.get('storageClass') not in ('extern','static')}
        array_ids={n['id'] for n in walk(function,check) if n.get('kind')=='VarDecl' and re.fullmatch(r'char\[[0-9]+\]',n.get('type',{}).get('qualType',''))}
        for node in walk(function,check):
            kind=node.get('kind');candidate=None;proof=None;rule=None;level='review_suggestion'
            if kind=='IfStmt' and node.get('inner'):
                candidate=node['inner'][0];proof=contradiction(candidate,local_ids);rule='SP6.contradictory_int_conjunction';level='proven_predicate_false'
            elif kind=='ImplicitCastExpr':
                candidate=node;proof=precision(node,local_ids);rule='SP6.integer_division_to_float'
            elif kind=='CallExpr':
                candidate=node;proof=input_capacity(node,array_ids,stdio_ids);rule='SP6.fixed_buffer_input'
            if not proof:continue
            try:
                for child in walk(candidate,check):
                    if child.get('kind')=='RecoveryExpr' or child.get('isInvalid') or child.get('isInvalidDecl'):raise ValueError('invalid AST evidence')
                    for loc in (child.get('loc',{}),child.get('range',{}).get('begin',{}),child.get('range',{}).get('end',{})):
                        if 'spellingLoc' in loc or 'expansionLoc' in loc:raise ValueError('macro-expanded evidence')
                begin=candidate['range']['begin'];end=candidate['range']['end']
                start=begin['offset'];stop=end['offset']+end['tokLen']
                if not region['start_byte']<=start<stop<=region['end_byte_exclusive']:raise ValueError('invalid physical candidate range')
                if begin.get('file') or end.get('file'):
                    from phase6.v2.regions import same_path
                    if any(l.get('file') and not same_path(l['file'],str(path)) for l in (begin,end)):raise ValueError('non-main evidence')
                found.append({'rule_id':rule,'category':'bounds' if rule.endswith('fixed_buffer_input') else 'program logic',
                              'confidence':level,'start_byte':start,'end_byte_exclusive':stop,'function':region['name'],
                              'proof':proof,'statement_range':node.get('range')})
            except (KeyError,TypeError,ValueError) as error:abstentions.append({'rule_id':rule,'function':region['name'],'reason':str(error)})
    return found,{'regions':regions,'unreliable_regions':excluded,'candidate_abstentions':abstentions,
                  'ast_nodes':len(nodes),'unsupported_policy':'Only direct signed-int comparisons/division and single builtin scanf %s to local char[N].'}
