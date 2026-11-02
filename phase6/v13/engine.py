"""Frozen v12 ablations: the only input type has no correction/reference field."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import time
from phase6.v12 import engine as v12
from phase6.v12.history import assess
from phase6.v11.engine import MODES
from .history import RecoveryInput


def frozen_engine_hash():
    root=Path(__file__).resolve().parents[2]
    files=[p for folder in ('phase6/v11','phase6/v12') for p in (root/folder).glob('*.py')]
    return hashlib.sha256(b''.join(p.relative_to(root).as_posix().encode()+p.read_text(encoding='utf-8').encode() for p in sorted(files))).hexdigest()


def evaluate_input(request):
    if not isinstance(request,RecoveryInput):raise TypeError('Use the source/history-only recovery boundary')
    start=time.perf_counter();source=request.source
    if len(source)>16384:
        return dict(modes={m:v12.recover(source,request.history,m) for m in MODES},elapsed_ms=(time.perf_counter()-start)*1000,compiler_invocations=0)
    v=v12.Validator(max_calls=34);config=v12.Config();pool,generation=v12.generate(source,v,config)
    snapshots,reliability=assess(source,request.history);reference=v12.reference_for(snapshots,v)
    modes={};rank_ms={}
    for mode in MODES:
        t=time.perf_counter();modes[mode]=v12.rank(source,pool,snapshots,reference,reliability,mode,config);rank_ms[mode]=(time.perf_counter()-t)*1000
    return dict(modes=modes,rank_ms=rank_ms,elapsed_ms=(time.perf_counter()-start)*1000,
                compiler_invocations=v.calls,generation=generation,config=asdict(config),
                resources=dict(candidate_programs=len(pool),candidate_source_bytes=sum(len(c['source'].encode()) for c in pool),
                               ast_cache_programs=len(v.cache),peak_rss_bytes=None,cpu_seconds=None))
