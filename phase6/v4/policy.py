"""Fail-closed physical AST isolation policy. No replacement semantics."""
import re
from phase6.v2.regions import same_path
from phase6.v3.policy import point_offset, TOKEN, unescape


def walk(node):
    pending=[node]
    while pending:
        item=pending.pop()
        if not isinstance(item,dict):raise ValueError('malformed AST node')
        yield item
        children=item.get('inner',[])
        if not isinstance(children,list):raise ValueError('malformed AST children')
        pending.extend(reversed(children))


def inventory(tree,path,data):
    """Allow invalid bodies to be excluded, never infer that they are analyzable."""
    data.decode('utf-8-sig')
    if tree.get('kind')!='TranslationUnitDecl' or not isinstance(tree.get('inner'),list):
        raise ValueError('missing translation-unit AST')
    if re.search(rb'^\s*#\s*(?!include\b)\S',data,re.M):
        raise ValueError('main-file preprocessing directives other than includes are not supported')
    regions=[];current_file=None;header_references=set()
    for node in tree['inner']:
        loc=node.get('loc',{})
        if not isinstance(loc,dict):raise ValueError('malformed declaration location')
        origin=loc.get('file') or loc.get('expansionLoc',{}).get('file') or loc.get('spellingLoc',{}).get('file')
        if origin:current_file=origin
        main=same_path(current_file,str(path)) and not loc.get('includedFrom')
        if not main:
            header_references.update(n.get('referencedDecl',{}).get('name') for n in walk(node)
                                     if n.get('referencedDecl',{}).get('kind')=='FunctionDecl')
            continue
        kind=node.get('kind')
        if kind=='VarDecl':raise ValueError('main-file global state/initialization prevents isolation')
        # Attributes, aliases, asm, and unfamiliar top-level semantics abstain.
        if kind not in ('FunctionDecl','TypedefDecl','RecordDecl','EnumDecl','EmptyDecl'):
            raise ValueError('unsupported main-file declaration: '+str(kind))
        if kind!='FunctionDecl':
            if any(n.get('referencedDecl') for n in walk(node)):
                raise ValueError('non-function declaration has value/function dependencies')
            if any('spellingLoc' in n.get('loc',{}) or 'expansionLoc' in n.get('loc',{}) for n in walk(node)):
                raise ValueError('macro-dependent main-file declarations')
            continue
        bodies=[n for n in node.get('inner',[]) if n.get('kind')=='CompoundStmt']
        if not bodies:
            # A function-looking declaration with a physical opening brace but
            # no AST body cannot be treated as an ordinary prototype.
            if node.get('isInvalid') or node.get('isInvalidDecl'):raise ValueError('invalid function declaration without a reliable body')
            continue
        if len(bodies)!=1:raise ValueError('ambiguous function body')
        def offset(location):
            if not isinstance(location,dict) or 'spellingLoc' in location or 'expansionLoc' in location:
                raise ValueError('macro or missing physical function boundary')
            if location.get('file') and not same_path(location['file'],str(path)):raise ValueError('non-main boundary')
            x=location.get('offset')
            if type(x) is not int or not 0<=x<len(data):raise ValueError('invalid physical boundary')
            return x
        start=offset(node['range']['begin']);end=offset(node['range']['end'])+1
        left=offset(bodies[0]['range']['begin']);right=offset(bodies[0]['range']['end'])
        name=node.get('name');at=offset(loc)
        if not isinstance(name,str) or data[at:at+len(name.encode())]!=name.encode():raise ValueError('function name mismatch')
        if not start<=at<left<=right==end-1 or data[left:left+1]!=b'{' or data[right:right+1]!=b'}':
            raise ValueError('inconsistent physical body boundaries')
        if re.search(rb'^\s*#',data[start:end],re.M):raise ValueError('preprocessing within function range')
        # Entire physical lines only; no shared declarations/comments erased.
        line_start=data.rfind(b'\n',0,start)+1
        line_end=data.find(b'\n',end);line_end=len(data) if line_end<0 else line_end
        if data[line_start:start].strip() or data[end:line_end].strip():raise ValueError('function shares a boundary line')
        refs=set();unsafe=[]
        local_ids={n.get('id') for n in walk(node) if n.get('kind') in ('VarDecl','ParmVarDecl')}
        for child in walk(node):
            if child.get('kind','').endswith('Attr'):unsafe.append('function attributes are unsupported')
            if child.get('kind') in ('GCCAsmStmt','MSAsmStmt','IndirectGotoStmt','AddrLabelExpr'):
                unsafe.append('assembly/computed control flow is unsupported')
            for location in (child.get('loc',{}),child.get('range',{}).get('begin',{}),child.get('range',{}).get('end',{})):
                if 'spellingLoc' in location or 'expansionLoc' in location:unsafe.append('macro-expanded function content')
            ref=child.get('referencedDecl',{})
            if ref.get('kind')=='FunctionDecl':refs.add(ref.get('name'))
            if ref.get('kind')=='VarDecl' and ref.get('id') not in local_ids:
                unsafe.append('reference to external/global state')
            if child.get('kind')=='CallExpr':
                # Reject indirect calls: points-to/callback dependencies cannot
                # be inferred reliably from an incomplete frontend AST.
                callee=child.get('inner',[])[:1]
                if not callee or not any(n.get('referencedDecl',{}).get('kind')=='FunctionDecl' for n in walk(callee[0])):
                    unsafe.append('indirect call dependency is unsupported')
            if child.get('storageClass') in ('static','extern') and child.get('kind')=='VarDecl':
                unsafe.append('persistent/external function-local state')
        regions.append({'id':'function:'+str(start)+':'+name,'name':name,'start_byte':start,'end_byte_exclusive':end,
                        'body_start_byte':left,'start_line':data.count(b'\n',0,start)+1,
                        'end_line':data.count(b'\n',0,end-1)+1,'references':sorted(refs),
                        'unsafe':sorted(set(unsafe)), 'reliability':'physical_ast_boundary',
                        'recovery_body':any(n.get('kind')=='RecoveryExpr' or n.get('isInvalid') or n.get('isInvalidDecl') for n in walk(node))})
    regions.sort(key=lambda r:r['start_byte'])
    if len({r['name'] for r in regions})!=len(regions):raise ValueError('duplicate function definitions')
    if header_references & {r['name'] for r in regions}:raise ValueError('header declarations depend on main-file function definitions')
    if any(a['end_byte_exclusive']>b['start_byte'] for a,b in zip(regions,regions[1:])):raise ValueError('overlapping function ranges')
    return regions


def plan(regions,diagnostics,path,data,max_exclusions):
    reasons={}; blockers=[]
    for diagnostic in diagnostics:
        if diagnostic.severity not in ('error','fatal error'):continue
        if not same_path(diagnostic.file,str(path)) or not diagnostic.line or not diagnostic.column:
            raise ValueError('frontend blocker outside reliably mapped main-file bodies')
        at=point_offset(data,diagnostic.line,diagnostic.column)
        matches=[r for r in regions if r['body_start_byte']<at<r['end_byte_exclusive']]
        if len(matches)!=1:raise ValueError('frontend blocker outside a unique physical function body')
        region=matches[0];reasons.setdefault(region['name'],[]).append('frontend blocker: '+diagnostic.message)
        blockers.append({'function':region['name'],'line':diagnostic.line,'column':diagnostic.column,'message':diagnostic.message})
    for region in regions:
        if region['recovery_body']:reasons.setdefault(region['name'],[]).append('recovery/invalid AST body')
        if region['unsafe']:raise ValueError(region['name']+': '+', '.join(region['unsafe']))
    # All callers/address-takers of removed definitions are excluded as well.
    # No missing definition is replaced by a prototype, stub, or opaque call.
    changed=True
    while changed:
        changed=False
        for region in regions:
            dependencies=sorted(set(region['references']) & reasons.keys())
            if dependencies and region['name'] not in reasons:
                reasons[region['name']]=['depends on excluded function(s): '+', '.join(dependencies)];changed=True
    if len(reasons)>max_exclusions:raise ValueError('exclusion budget exceeded')
    excluded=[{**r,'exclusion_reasons':reasons[r['name']],
               'dependency_assumptions':['entire definition omitted; no replacement semantics',
                                         'all retained direct references to excluded names are prohibited']} for r in regions if r['name'] in reasons]
    retained=[{**r,'dependency_assumptions':['main-file declarations and included headers retained unchanged',
                 'external function contracts unchanged; no whole-program/path-completeness claim']} for r in regions if r['name'] not in reasons]
    if not excluded:raise ValueError('no blocked function requires isolation')
    if not retained:raise ValueError('no independent function remains')
    return excluded,retained,blockers


def mask(data,excluded):
    result=bytearray(data)
    for r in excluded:
        for at in range(r['start_byte'],r['end_byte_exclusive']):
            if result[at] not in (10,13):result[at]=32
    return bytes(result)


def preprocess_signature(output,path,excluded):
    """Compare -E token streams outside excluded physical main-file lines.

    Clang numeric line markers map preprocessed lines; no textual C boundary
    inference is used. Unknown/non-UTF-8 markers fail closed.
    """
    current=None;line=None;kept=[]
    marker=re.compile(rb'^#\s+(\d+)\s+"((?:\\.|[^"\\])*)"(?:\s+\d+)*\s*$')
    for raw in output.splitlines():
        if raw.startswith(b'#'):
            m=marker.fullmatch(raw)
            if not m:raise ValueError('unrecognized preprocessor line marker')
            line=int(m[1]);current=unescape(m[2]).decode('utf-8');continue
        if line is None:raise ValueError('preprocessor output lacks physical line markers')
        omitted=same_path(current,str(path)) and any(r['start_line']<=line<=r['end_line'] for r in excluded)
        if not omitted:kept.extend(m.group() for m in TOKEN.finditer(raw) if not m.group().isspace())
        line+=1
    return kept
