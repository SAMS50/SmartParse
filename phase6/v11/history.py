"""Offsets are Unicode code points, versions are consecutive local revisions.

Events describe replacement [offset:offset+len(deleted)] in the preceding version.
Replay, including exact deleted text, is required before any history is trusted.
"""
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher


@dataclass(frozen=True)
class HistoryConfig:
    window: int = 8
    proximity_scale: int = 40


def replay(source, history, config=HistoryConfig()):
    if not history:
        return [], 'Missing history'
    events = history.get('events', [])
    text = history.get('base_source', '')
    version = history.get('base_version', 0)
    snapshots = [text]
    for event in events:
        offset = event['offset']; deleted = event['deleted']; inserted = event['inserted']
        if (event['version'] != version + 1 or offset < 0 or offset > len(text)
                or text[offset:offset+len(deleted)] != deleted):
            return [], 'Unreliable version or offset mapping'
        text = text[:offset] + inserted + text[offset+len(deleted):]
        snapshots.append(text); version += 1
    if text != source or version != history.get('source_version'):
        return [], 'History does not reproduce submitted source version'
    return snapshots[-config.window-1:], 'Verified replay of submitted source'


def distance(a, b):
    # Deterministic changed-character mass, not Levenshtein distance.
    return sum(max(i2-i1, j2-j1) for tag,i1,i2,j1,j2 in
               SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != 'equal')


def score(source, repaired, snapshots, config=HistoryConfig()):
    if len(snapshots) < 2:
        return {'score': 0, 'restored_snapshot': False, 'explanation': 'No verified recent editing evidence'}
    before = snapshots[-2]
    edits = [x for x in SequenceMatcher(None,before,source,autojunk=False).get_opcodes() if x[0]!='equal']
    repairs = [x for x in SequenceMatcher(None,source,repaired,autojunk=False).get_opcodes() if x[0]!='equal']
    separation = min((abs(e[3]-r[1]) for e in edits for r in repairs), default=len(source))
    restored = repaired in snapshots[:-1]
    improvement = distance(source,before)-distance(repaired,before)
    proximity = max(0, 1-separation/config.proximity_scale)
    value = 40*int(restored) + 10*max(-2,min(2,improvement)) + 5*proximity
    return dict(score=round(value,6), restored_snapshot=restored,
                distance_delta=improvement, separation=separation,
                explanation=f'Exact recent snapshot restoration={restored}; changed-character distance delta={improvement}; proximity={proximity:.3f}. Recency alone is not intent proof.')
