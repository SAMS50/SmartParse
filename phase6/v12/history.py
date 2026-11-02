"""Source-version reliability is distinct from evidence of current intent."""
from phase6.v11.history import replay, HistoryConfig, score


def assess(source,history,window=8):
    try:snapshots,reason=replay(source,history,HistoryConfig(window=window))
    except (KeyError,TypeError,ValueError,AttributeError):snapshots=[];reason='Malformed history'
    mapping=history is None or bool(snapshots)
    result=dict(mapping_verified=mapping,status='missing' if history is None else 'verified replay' if snapshots else 'unreliable mapping',
                reason=reason,intent_support='unavailable',boundary_deletion=False,broad_edit=False)
    if len(snapshots)>1:
        latest=history['events'][-1]
        result['boundary_deletion']=(latest['deleted'].strip()=='}' and not latest['inserted'].strip() and not source[latest['offset']:].strip())
        result['broad_edit']=len(latest['deleted'])+len(latest['inserted'])>8
        result['intent_support']='weak: broad replacement' if result['broad_edit'] else 'conditional: local edit, not proof of intent'
        if result['boundary_deletion']:result['intent_support']='ambiguous: end-of-source block deletion'
    return snapshots,result
