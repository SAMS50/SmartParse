"""Only prior, provenance-bearing history can cross the recovery boundary."""
from dataclasses import dataclass
from datetime import datetime
from phase6.v11.history import replay


@dataclass(frozen=True,slots=True)
class RecoveryInput:
    source:str
    history:dict|None=None
    history_condition:str='none'


def build_input(source,source_time,evidence=None):
    if evidence is None:return RecoveryInput(source)
    kind=evidence.get('kind')
    if kind not in ('recorded','partial','reconstructed'):raise ValueError('History origin must be explicit')
    if kind!='reconstructed' and not evidence.get('provenance_url','').startswith('https://'):raise ValueError('Prior-history provenance URL required')
    history=evidence.get('history');times=evidence.get('event_times',[])
    if not isinstance(history,dict) or len(times)!=len(history.get('events',[])):raise ValueError('History timestamps/events do not match')
    try:
        cutoff=datetime.fromisoformat(source_time)
        timeline=[datetime.fromisoformat(evidence['base_time'])]+[datetime.fromisoformat(t) for t in times]
        if any(t>cutoff for t in timeline) or timeline!=sorted(timeline):raise ValueError('Future or nonchronological history is forbidden')
    except (KeyError,TypeError):raise ValueError('Usable history chronology is required') from None
    snapshots,_=replay(source,history)
    if not snapshots:raise ValueError('Prior history does not reproduce submitted source')
    return RecoveryInput(source,history,kind)
