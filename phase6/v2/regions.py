"""Physical source-region inventory from validated Clang AST JSON offsets.

No regex function detection, diagnostic-proximity coverage, or recovery ASTs
are treated as evidence of a function having undergone static analysis.
"""
import ntpath
import os


def same_path(left, right):
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    if ntpath.splitdrive(left)[0] or ntpath.splitdrive(right)[0]:
        return ntpath.normcase(ntpath.normpath(left)) == ntpath.normcase(ntpath.normpath(right))
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def functions_from_ast(tree, source_path, source_bytes):
    if not isinstance(tree, dict) or tree.get('kind') != 'TranslationUnitDecl' or not isinstance(tree.get('inner'), list):
        raise ValueError('not a Clang translation-unit AST')
    regions, exclusions = [], []
    current_file = None

    def offset(location):
        if not isinstance(location, dict) or 'spellingLoc' in location or 'expansionLoc' in location:
            raise ValueError('macro-expanded or missing physical location')
        if location.get('file') and not same_path(location['file'], source_path):
            raise ValueError('range location is outside main source')
        value = location.get('offset')
        if type(value) is not int or not 0 <= value < len(source_bytes):
            raise ValueError('invalid physical byte offset')
        return value

    def line(value):
        return source_bytes.count(b'\n', 0, value) + 1

    for node in tree['inner']:
        if not isinstance(node, dict):
            raise ValueError('malformed AST declaration')
        loc = node.get('loc', {})
        if not isinstance(loc, dict):
            raise ValueError('malformed declaration location')
        if any(key in loc and not isinstance(loc[key],dict) for key in ('spellingLoc','expansionLoc')):
            raise ValueError('malformed macro location')
        if isinstance(loc, dict) and loc.get('file'):
            current_file = loc['file']
        elif isinstance(loc.get('expansionLoc'),dict) or isinstance(loc.get('spellingLoc'),dict):
            # Clang may print the physical filename only in the first macro
            # name's nested location and omit it on later ordinary declarations.
            # This carries file identity, never trust in macro-generated ranges.
            expansion=loc.get('expansionLoc',{})
            spelling=loc.get('spellingLoc',{})
            origin=expansion.get('file') or spelling.get('file')
            if origin: current_file=origin
        if node.get('kind') != 'FunctionDecl':
            continue
        children=node.get('inner',[])
        if not isinstance(children,list):
            raise ValueError('malformed function children')
        bodies = [item for item in children if isinstance(item, dict) and item.get('kind') == 'CompoundStmt']
        if not bodies:
            continue  # Function declarations are not function bodies.
        if loc.get('includedFrom') or (current_file and not same_path(current_file, source_path)):
            continue  # Never treat a header's body as a main-file body.
        try:
            if current_file is None:
                raise ValueError('no physical main-file identity')
            if node.get('isInvalid') or node.get('isInvalidDecl'):
                raise ValueError('invalid declaration in recovery AST')
            start = offset(node['range']['begin'])
            end = offset(node['range']['end'])
            body_start = offset(bodies[0]['range']['begin'])
            body_end = offset(bodies[0]['range']['end'])
            name_offset = offset(loc)
            name = node.get('name')
            if not isinstance(name, str) or not name:
                raise ValueError('missing function name')
            spelling = name.encode('utf-8')
            if source_bytes[name_offset:name_offset+len(spelling)] != spelling:
                raise ValueError('name spelling does not match source bytes')
            if not start <= name_offset < body_start <= body_end == end:
                raise ValueError('inconsistent declaration/body ranges')
            if source_bytes[body_start:body_start+1] != b'{' or source_bytes[body_end:body_end+1] != b'}':
                raise ValueError('body boundaries do not match source bytes')
            # AST recovery nodes are inventoried only as uncertain exclusions.
            pending = [bodies[0]]
            while pending:
                child = pending.pop()
                if child.get('kind') == 'RecoveryExpr' or child.get('isInvalid'):
                    raise ValueError('body contains recovery AST nodes')
                children=child.get('inner',[])
                if not isinstance(children,list):
                    raise ValueError('malformed body children')
                pending.extend(item for item in children if isinstance(item, dict))
            regions.append({'id':f'function:{start}:{name}', 'kind':'function', 'name':name,
                            'mapping':'physical-main-file-byte-offsets', 'start_byte':start, 'end_byte_exclusive':end+1,
                            'start_line':line(start), 'end_line':line(end),
                            'reliability':'validated_ast_range'})
        except (KeyError, TypeError, ValueError) as error:
            exclusions.append({'name':node.get('name'), 'reason':str(error)})
    regions.sort(key=lambda r:r['start_byte'])
    for left, right in zip(regions,regions[1:]):
        if left['end_byte_exclusive'] > right['start_byte']:
            raise ValueError('overlapping main-file function ranges')
    return regions, exclusions
