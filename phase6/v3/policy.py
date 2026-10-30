"""Byte-oriented recovery policy. No general C parser or semantic repairs."""
import re
from phase6.v2.regions import same_path

FIXIT=re.compile(rb'^fix-it:"((?:\\.|[^"\\])*)":\{(\d+):(\d+)-(\d+):(\d+)\}:"((?:\\.|[^"\\])*)"$')
HEADER=re.compile(rb'^(.*):(\d+):(\d+): (fatal error|error|warning|note): (.*)$')
TOKEN=re.compile(rb'\s+|(?:u8|u|U|L)?"(?:\\.|[^"\\])*"|(?:u|U|L)?\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|[0-9][A-Za-z_0-9.]*|.',re.S)


def unescape(data):
    result=bytearray(); i=0
    escapes={ord('n'):10,ord('r'):13,ord('t'):9,ord('b'):8,ord('f'):12,ord('v'):11,ord('a'):7,ord('\\'):92,ord('"'):34}
    while i<len(data):
        value=data[i]; i+=1
        if value!=92: result.append(value); continue
        if i==len(data): raise ValueError('trailing C escape')
        value=data[i]; i+=1
        if 48<=value<=55:
            digits=bytes([value])
            while i<len(data) and len(digits)<3 and 48<=data[i]<=55: digits+=data[i:i+1]; i+=1
            number=int(digits,8)
            if number>255: raise ValueError('invalid octal escape')
            result.append(number)
        elif value in escapes: result.append(escapes[value])
        else: raise ValueError('unsupported C escape')
    return bytes(result)


def fixits(stderr):
    found=[]; active=None
    for raw in stderr.splitlines():
        header=HEADER.match(raw)
        if header:
            file,row,col,severity,message=header.groups()
            active={'file':file.decode('utf-8'),'line':int(row),'column':int(col),
                    'severity':severity.decode(),'message':message.decode('utf-8')}
        match=FIXIT.fullmatch(raw)
        if not match: continue
        if len(found)>=64: raise ValueError('machine fix-it inventory exceeds 64 records')
        file,a,b,c,d,text=match.groups()
        if any(len(x)>9 for x in (a,b,c,d)): raise ValueError('invalid fix-it coordinate')
        found.append({'file':unescape(file).decode('utf-8'),'start_line':int(a),'start_column':int(b),
                      'end_line':int(c),'end_column':int(d),'replacement':unescape(text).decode('utf-8'),
                      'diagnostic':active})
    return found


def point_offset(data,line,column):
    lines=data.splitlines(keepends=True)
    if not 1<=line<=len(lines) or column<1: raise ValueError('coordinate outside physical source')
    body=lines[line-1].rstrip(b'\r\n')
    if column>len(body)+1: raise ValueError('column outside physical source line')
    return sum(map(len,lines[:line-1]))+column-1


def original_offset(offset, edits):
    shift=0
    for edit in sorted(edits,key=lambda e:e['original_offset']):
        generated=edit['original_offset']+shift
        if offset==generated: return None
        if offset<generated: break
        shift+=1
    return offset-shift


def apply_edits(original,edits):
    offsets=sorted(e['original_offset'] for e in edits)
    if len(offsets)!=len(set(offsets)) or any(type(x) is not int or not 0<=x<=len(original) for x in offsets):
        raise ValueError('overlapping or invalid insertion offsets')
    data=original
    for offset in reversed(offsets): data=data[:offset]+b';'+data[offset:]
    return data


def source_map(original,edits):
    parts=[]; previous=0; shift=0
    for edit in sorted(edits,key=lambda e:e['original_offset']):
        offset=edit['original_offset']
        if previous<offset:
            parts.append({'variant_start':previous+shift,'variant_end_exclusive':offset+shift,
                          'original_start':previous,'original_end_exclusive':offset})
        parts.append({'variant_start':offset+shift,'variant_end_exclusive':offset+shift+1,
                      'original_start':None,'original_end_exclusive':None,'anchor_original_offset':offset,'generated':';'})
        shift+=1; previous=offset
    if previous<len(original):parts.append({'variant_start':previous+shift,'variant_end_exclusive':len(original)+shift,
                                           'original_start':previous,'original_end_exclusive':len(original)})
    return parts


def only_inserted_semicolon(before,after):
    left=[m.group() for m in TOKEN.finditer(before) if not m.group().isspace()]
    right=[m.group() for m in TOKEN.finditer(after) if not m.group().isspace()]
    if len(right)!=len(left)+1:return False
    i=j=skipped=0
    while j<len(right):
        if i<len(left) and left[i]==right[j]:i+=1; j+=1
        elif right[j]==b';' and skipped==0:j+=1; skipped=1
        else:return False
    return i==len(left) and skipped==1


def boundary_candidate(fix,tree,path,data):
    """Require machine insertion + complete physical AST statement + lexical guard."""
    if not same_path(fix['file'],str(path)):raise ValueError('fix-it is not in the main source')
    if fix['replacement']!=';' or (fix['start_line'],fix['start_column'])!=(fix['end_line'],fix['end_column']):
        raise ValueError('only zero-length semicolon insertion is permitted')
    if not fix['diagnostic'] or fix['diagnostic']['severity']!='error':raise ValueError('not an error-associated repair')
    data.decode('utf-8-sig')  # Never guess byte coordinates for another encoding.
    if re.search(rb'^\s*#\s*(?:line\b|\d)',data,re.M):raise ValueError('presumed-line directives make fix-it mapping ambiguous')
    offset=point_offset(data,fix['start_line'],fix['start_column'])
    if tree.get('kind')!='TranslationUnitDecl':raise ValueError('missing AST envelope')
    eligible=[]
    def physical(loc):
        if not isinstance(loc,dict) or 'spellingLoc' in loc or 'expansionLoc' in loc:return None
        if loc.get('file') and not same_path(loc['file'],str(path)):return None
        number=loc.get('offset'); length=loc.get('tokLen')
        if type(number) is not int or type(length) is not int:return None
        return number,length
    def macro_or_recovery(node):
        stack=[node]
        while stack:
            child=stack.pop()
            if not isinstance(child,dict):return True
            if child.get('kind')=='RecoveryExpr' or child.get('isInvalid') or child.get('isInvalidDecl'):return True
            for value in (child.get('loc',{}),child.get('range',{}).get('begin',{}),child.get('range',{}).get('end',{})):
                if not isinstance(value,dict) or 'spellingLoc' in value or 'expansionLoc' in value:return True
            children=child.get('inner',[])
            if not isinstance(children,list):return True
            stack.extend(children)
        return False
    def visit(node,parent=None,current_file=None):
        if not isinstance(node,dict):raise ValueError('malformed AST node')
        loc=node.get('loc',{})
        if not isinstance(loc,dict):raise ValueError('malformed AST location')
        current_file=loc.get('file',current_file)
        kind=node.get('kind')
        region=node.get('range',{})
        if not isinstance(region,dict):raise ValueError('malformed AST range')
        start=physical(region.get('begin')); end=physical(region.get('end'))
        allowed=(kind=='VarDecl' and parent=='TranslationUnitDecl') or (kind=='ReturnStmt' and parent=='CompoundStmt')
        if allowed and start and end and end[0]+end[1]==offset and same_path(current_file,str(path)) and not loc.get('includedFrom'):
            begin=start[0]; segment=data[begin:offset]
            if macro_or_recovery(node):raise ValueError('candidate contains macro/recovery source locations')
            if any(x in segment for x in (b'\n',b'\r',b'\\',b'#',b'/*',b'//')):raise ValueError('multi-line, escaped, or commented boundary is not whitelisted')
            following=data[offset:]
            # Only trivia before a close brace (return) or a new top-level
            # builtin declaration is allowed; no control/initializer guessing.
            if kind=='ReturnStmt':
                if not segment.startswith(b'return') or not re.match(rb'^\s*}',following):raise ValueError('return is not at a closing-block boundary')
            else:
                declaration=rb'(?:(?:static|const|volatile|unsigned|signed|long|short|int|char|float|double)\s+)+[A-Za-z_]\w*(?:\s*=\s*[^;,{}\[\]]+)?'
                if not re.fullmatch(declaration,segment) or not re.match(rb'^\s*(?:int|char|float|double|void|static|const|unsigned|signed|long|short)\b',following):
                    raise ValueError('not an unambiguous builtin scalar declaration boundary')
            eligible.append({'offset':offset,'kind':'return_statement' if kind=='ReturnStmt' else 'top_level_scalar_declaration',
                             'statement_start':begin,'statement_bytes_hex':segment.hex()})
        children=node.get('inner',[])
        if not isinstance(children,list):raise ValueError('malformed AST children')
        # Clang elides file names between sibling declarations. Retain physical
        # context, but never accept macro locations as candidate ranges.
        for child in children:
            if isinstance(child,dict) and isinstance(child.get('loc'),dict):current_file=child['loc'].get('file',current_file)
            visit(child,kind,current_file)
    visit(tree)
    if len(eligible)!=1:raise ValueError('no unique admissible AST boundary')
    return eligible[0]
