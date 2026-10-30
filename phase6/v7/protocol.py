"""Strict diagnostic formats for experiments. Warnings are not defect proofs."""
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse,unquote
from phase6.v2.regions import same_path
from phase6.v1.evaluation import fingerprint

CATEGORIES={
    '-Walloc-size':'bounds','-Wanalyzer-allocation-size':'semantic/type','-Wreturn-local-addr':'memory safety',
    '-Wanalyzer-out-of-bounds':'bounds','-Wanalyzer-use-after-free':'memory safety',
    '-Wanalyzer-double-free':'memory safety','-Wanalyzer-malloc-leak':'memory safety',
    '-Wanalyzer-null-dereference':'memory safety','-Wanalyzer-possible-null-dereference':'memory safety',
    '-Wanalyzer-file-leak':'resource management','-Wanalyzer-overlapping-buffers':'undefined behavior',
    'bufferAccessOutOfBounds':'bounds','memleak':'memory safety','nullPointer':'memory safety',
    'doubleFree':'memory safety','deallocuse':'memory safety','resourceLeak':'resource management',
    'overlappingWriteFunction':'undefined behavior','integerOverflow':'undefined behavior',
    'returnDanglingLifetime':'memory safety','autoVariables':'memory safety','ctunullpointer':'memory safety',
    'invalidScanfArgType_int':'semantic/type','invalidPrintfArgType_sint':'semantic/type',
    'incorrectLogicOperator':'program logic','invalidscanf':'bounds','zerodiv':'undefined behavior','uninitvar':'undefined behavior',
    'bugprone-misplaced-widening-cast':'semantic/type','bugprone-integer-division':'program logic',
}


def uri_path(value):
    if not isinstance(value,str):return None
    if re.match(r'^[A-Za-z]:[\\/]',value):return value
    p=urlparse(value)
    if p.scheme=='file':
        path=unquote(p.path)
        if re.match(r'^/[A-Za-z]:/',path):path=path[1:]
        return path
    return unquote(value) if not p.scheme else None


def record(file,line,column,severity,message,identifier,related=None,**extra):
    if line is not None and (type(line) is not int or line<1):raise ValueError('invalid diagnostic line')
    if column is not None and (type(column) is not int or column<1):column=None
    if not isinstance(message,str):raise ValueError('invalid diagnostic message')
    return {'file':file,'line':line,'column':column,'severity':severity,'message':message,
            'diagnostic_id':identifier,'category':CATEGORIES.get(identifier,'unknown'),'related':related or [],**extra}


def gcc_json(text):
    data=json.loads(text)
    if not isinstance(data,list):raise ValueError('GCC diagnostics must be a JSON list')
    results=[]
    def visit(d,context=False):
        if not isinstance(d,dict):raise ValueError('invalid GCC diagnostic')
        caret=(d.get('locations') or [{}])[0].get('caret',{})
        results.append(record(caret.get('file'),caret.get('line'),caret.get('byte-column',caret.get('column')),
                        d.get('kind','unknown'),d['message'],d.get('option'),d.get('path',[]),
                        context_note=context or d.get('kind')=='note',column_kind='byte' if 'byte-column' in caret else 'compiler-reported'))
        for child in d.get('children',[]):visit(child,True)
    for d in data:visit(d)
    return results,[]


def gcc_sarif(text):
    data=json.loads(text)
    if not isinstance(data,dict) or data.get('version')!='2.1.0' or not isinstance(data.get('runs'),list):raise ValueError('invalid SARIF envelope')
    results=[];issues=[]
    for run in data['runs']:
        for invocation in run.get('invocations',[]):
            for notice in invocation.get('toolExecutionNotifications',[]):issues.append(notice)
        for item in run.get('results',[]):
            physical=((item.get('locations') or [{}])[0]).get('physicalLocation',{})
            artifact=physical.get('artifactLocation',{});region=physical.get('region',{})
            if 'uri' not in artifact and 'index' in artifact:
                artifact=run.get('artifacts',[])[artifact['index']].get('location',{})
            message=item.get('message',{});message=message.get('text',message.get('markdown'))
            level=item.get('level','warning');severity={'error':'error','warning':'warning','note':'note','none':'information'}.get(level,'unknown')
            results.append(record(uri_path(artifact.get('uri')),region.get('startLine'),region.get('startColumn'),severity,message,item.get('ruleId'),
                                  item.get('codeFlows',[]),context_note=severity=='note',column_kind=run.get('columnKind','unicodeCodePoints'),
                                  sarif_properties=item.get('properties',{})))
    return results,issues


def cppcheck_xml(text):
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():raise ValueError('XML declarations/entities are not allowed')
    root=ET.fromstring(text)
    if root.tag!='results' or root.get('version')!='2':raise ValueError('invalid Cppcheck XML envelope')
    results=[]
    for error in root.findall('./errors/error'):
        locations=[dict(n.attrib) for n in error.findall('location')];loc=locations[0] if locations else {}
        results.append(record(loc.get('file'),int(loc['line']) if loc.get('line') and int(loc['line'])>0 else None,
                              int(loc['column']) if loc.get('column') else None,error.get('severity','unknown'),
                              error.get('verbose',error.get('msg')),error.get('id'),locations[1:],
                              inconclusive=error.get('inconclusive')=='true',context_note=False,column_kind='tool-reported',
                              short_message=error.get('msg'),cwe=error.get('cwe')))
    return results,[]


HEADER=re.compile(r'^(.*):(\d+):(\d+): (fatal error|error|warning|note): (.*?)(?: \[([^\]]+)\])?$')
def tidy_text(text):
    results=[];unrecognized=[];active=None
    for line in text.splitlines():
        match=HEADER.match(line)
        if match:
            file,row,col,severity,message,identifier=match.groups()
            active=record(file,int(row),int(col),severity,message,identifier,context_note=severity=='note',column_kind='compiler-reported')
            results.append(active)
        elif line.strip():
            if active is not None:active.setdefault('raw_continuation',[]).append(line)
            elif not re.match(r'^\d+ (?:warnings?|errors?) generated\.',line):unrecognized.append(line)
    return results,unrecognized


PARSERS={'gcc-json':gcc_json,'gcc-sarif':gcc_sarif,'cppcheck-xml':cppcheck_xml,'tidy-text':tidy_text}
def normalize(format,text,source,source_bytes,tool,configuration):
    if len(text)>16*1024*1024:raise ValueError('diagnostic output budget exceeded')
    try:rows,unknown=PARSERS[format](text)
    except (ET.ParseError,TypeError,KeyError,IndexError) as error:raise ValueError('malformed diagnostic structure: '+str(error)) from error
    seen={};duplicates=[]
    presumed=bool(re.search(rb'^\s*#\s*(?:line\b|\d)',source_bytes,re.M))
    for d in rows:
        d['source_bound']=not presumed and same_path(d['file'],str(source))
        d['mapping_status']='unverified_presumed_locations' if presumed else 'reported_location_bound_to_input' if d['source_bound'] else 'external_or_unknown_location'
        d['source_snippet']=None
        if d['source_bound'] and d['line']:
            lines=source_bytes.splitlines()
            if d['line']<=len(lines):d['source_snippet']=lines[d['line']-1].decode('utf-8',errors='replace')
            else:d['source_bound']=False
        key=fingerprint([d['file'],d['line'],d['column'],d['severity'],d['diagnostic_id'],d['message']])
        d.update(id='X-'+key[:20],tool=tool,configuration=configuration,review_status='tool_reported_unverified',
                 confidence='review_suggestion',provenance={'original_source':True,'repair_conditioned':False,'isolation_conditioned':False},
                 duplicates_existing='unknown_pending_root_review')
        if key in seen:duplicates.append(d['id'])
        else:seen[key]=d
    return list(seen.values()),duplicates,unknown
