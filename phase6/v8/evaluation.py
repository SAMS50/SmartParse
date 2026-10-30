"""Descriptive matching only. No automated claim of human-confirmed accuracy."""
from pathlib import Path
import re
from .prepare import digest


def unavailable_metrics():
    return dict(TP=None, FP=None, FN=None, precision=None, recall=None, F1=None,
                reason='Independent complete human-adjudicated labels unavailable')


def source_bound(diagnostic, path):
    file = (diagnostic.get('original_location') or {}).get('file') or diagnostic.get('file')
    return bool(file) and str(file).replace('\\','/').casefold() == str(path).replace('\\','/').casefold()


def match(case, source, diagnostics):
    if digest(source) != case['sha256']:
        raise ValueError('Source hash does not match frozen reference')
    roots = case['roots']; candidates=[]; unmatched=[]; ambiguous=[]
    for index, d in enumerate(diagnostics):
        if d.get('severity') not in ('error','fatal error','warning') or d.get('context_note'):
            continue
        if not source_bound(d, case['absolute_path']):
            unmatched.append(index); continue
        location=d.get('original_location') or d
        lines={int(location.get('line') or 0)}
        for related in d.get('related',[]):
            if source_bound(related,case['absolute_path']):lines.add(int(related.get('line') or 0))
        possible=[]
        for root in roots:
            # Root meaning must be supported by identifier or frontend category,
            # not proximity or severity alone. A diagnostic may support only one root.
            category=root['category']; identifier=d.get('diagnostic_id') or ''
            id_ok=identifier in root.get('allowed_ids',[])
            frontend=category in ('syntax','semantic/type','configuration')
            category_ok=(d.get('category')==category or category=='configuration' and d.get('severity')=='fatal error')
            meaning=any(word.casefold() in d.get('message','').casefold() for word in root.get('message_any',[]))
            if not (id_ok or frontend and category_ok and meaning):continue
            window=root.get('admissible_line_window',0)
            if not any(abs(line-root['line'])<=window for line in lines):continue
            if root['source_evidence'] not in source.decode('utf-8'):continue
            if not frontend and d.get('_blocked'):continue
            possible.append(root['id'])
        if len(possible)==1:
            candidates.append(dict(root=possible[0],diagnostic=index,
                                   conditioned=bool(d.get('_conditioned')),status='pending_human_review'))
        elif possible:ambiguous.append(dict(diagnostic=index,possible_roots=possible))
        else:unmatched.append(index)
    original=sorted({m['root'] for m in candidates if not m['conditioned']})
    conditioned=sorted({m['root'] for m in candidates if m['conditioned']})
    return dict(original_supported_proposals=original,conditioned_supported_proposals=conditioned,
                matches=candidates,ambiguous=ambiguous,unmatched_primary_indices=unmatched,
                duplicate_support_records=max(0,len(candidates)-len({m['root'] for m in candidates})),
                unobserved_proposals=sorted({r['id'] for r in roots}-set(original)-set(conditioned)),
                metrics=unavailable_metrics(),confirmed_defect_roots=None)


def replay(tokens, repairs):
    from smartparse import Token
    result=[(token,False) for token in tokens]
    for repair in repairs:
        anchors=[i for i,(t,generated) in enumerate(result) if not generated and
                 (t.line,t.col)==(repair['line'],repair['column'])]
        if len(anchors)!=1:raise ValueError('Repair anchor not uniquely reconstructible')
        i=anchors[0]; token=result[i][0]; op=repair['operation']; value=repair['token']
        if op=='insert':result.insert(i,(Token(value,value,token.line,token.col),True))
        elif op=='substitute':result[i]=(Token(value,value,token.line,token.col),True)
        elif op=='delete':result.pop(i)
        else:raise ValueError('Unknown repair operation')
    return [t for t,_ in result]


def syntax_case(case, source, configuration, intended):
    import time
    from smartparse import Parser, StrictParser, tokenize, LexError, ParseError
    from baseline import PanicModeParser
    traces=[]
    class Trace:
        def _statement(self):
            entry=dict(start=self.i,line=self.peek().line,column=self.peek().col,returned=False)
            traces.append(entry)
            try:
                value=super()._statement();entry['returned']=True;return value
            finally:entry['end']=self.i
    class Context(Trace,Parser):pass
    class Panic(Trace,PanicModeParser):pass
    started=time.monotonic()
    result=dict(configuration=configuration,matching_protocol='1.1',metrics=unavailable_metrics(),confirmed_defect_roots=None)
    try:
        tokens=tokenize(source)
        parser=Panic(tokens) if configuration=='panic' else Context(tokens,validate_repairs=configuration!='validation_off')
        parser.parse()
        roots=case['roots'];matched=[];exact=[]
        for root in roots:
            for d in parser.diagnostics:
                token=root.get('token')
                expected_wording=bool(token) and (repr(token) in d['message'] or d['message'].startswith('Expected '+token+' before '))
                if (d['line'],d['column'])==(root['line'],root['column']) and expected_wording:
                    matched.append(root['id']);break
            for r in parser.repairs:
                if (r['line'],r['column'],r['operation'],r['token'])==(root['line'],root['column'],root['operation'],root['token']):
                    exact.append(root['id']);break
        repaired=replay(tokens,parser.repairs)
        strict_ok=True
        try:StrictParser(repaired).parse()
        except (ParseError,IndexError):strict_ok=False
        intended_valid=None;equal=None
        if intended is not None:
            intended_tokens=tokenize(intended);intended_valid=True
            try:StrictParser(intended_tokens).parse()
            except (ParseError,IndexError):intended_valid=False
            equal=[t.value for t in repaired]==[t.value for t in intended_tokens]
        result.update(status='completed',diagnostics=parser.diagnostics,repairs=parser.repairs,
                      author_location_matches=sorted(set(matched)),author_exact_repairs=sorted(set(exact)),
                      additional_diagnostics=max(0,len(parser.diagnostics)-len(set(matched))),
                      reached_eof=parser.peek().kind=='EOF',error_cap_reached=len(parser.diagnostics)>=parser.max_errors,
                      replay_strictly_valid=strict_ok,intended_reference_valid=intended_valid,intended_token_stream_equal=equal,
                      statement_attempts=traces,skipped_tokens=getattr(parser,'skipped_tokens',None),
                      validation_stats=parser.validation_stats)
    except LexError as error:result.update(status='unsupported_lexer',reason=str(error),diagnostics=[],repairs=[])
    result['elapsed_seconds']=round(time.monotonic()-started,6)
    return result
