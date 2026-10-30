"""Bounded local discovery; no installation, registry changes or whole-disk scan."""
import itertools
import json
import os
from pathlib import Path
import shutil
from phase6.v3.execution import Budget, Limits, LimitReached


def locate(name, explicit=None):
    if explicit is not None:
        return shutil.which(str(explicit)) or str(explicit)
    configured=os.environ.get('SMARTPARSE_'+name.upper())
    if configured:return shutil.which(configured) or configured
    executable='gcc' if name=='gcc14' else name
    # Preserve the pinned external profiles before considering PATH substitutes.
    if name in ('gcc14','cppcheck'):
        catalog=json.loads((Path(__file__).resolve().parents[1]/'phase6/v7/catalog.json').read_text())
        entry=next(t for t in catalog if t['id']==name)
        if Path(entry['path']).is_file():return entry['path']
    found=shutil.which(executable)
    if found:return found
    if os.name=='nt':
        candidates=[]
        program=Path(os.environ.get('ProgramFiles',r'C:\Program Files'))
        if name=='clang':
            candidates += [program/'LLVM/bin/clang.exe']
            roots=[Path(r'C:\android-sdk')]
            roots += [Path(os.environ[k]) for k in ('ANDROID_HOME','ANDROID_SDK_ROOT') if os.environ.get(k)]
            for root in roots[:3]:
                try:ndks=list(itertools.islice((root/'ndk').glob('*'),8))
                except OSError:ndks=[]
                for ndk in sorted(ndks,reverse=True):
                    candidates.append(ndk/'toolchains/llvm/prebuilt/windows-x86_64/bin/clang.exe')
        if name=='gcc':candidates += [Path(r'C:\MinGW\bin\gcc.exe'),program/'CodeBlocks/MinGW/bin/gcc.exe']
        for path in candidates:
            if path.is_file():return str(path)
    return None


def doctor(overrides=None, timeout=5):
    overrides=overrides or {}
    budget=Budget(Limits(invocations=4,total_seconds=min(120,timeout*4),call_seconds=timeout))
    tools=[]
    for name in ('gcc','clang','gcc14','cppcheck'):
        path=locate(name,overrides.get(name))
        entry=dict(name=name,path=path,status='unavailable',version=None,capabilities='not probed; analysis validates required capabilities')
        if path:
            try:
                p=budget.call('doctor_version',[path,'--version'])
                text=(p.stdout+p.stderr).decode('utf-8',errors='replace').strip()
                recognized=('clang' in text.lower() if name=='clang' else 'cppcheck' in text.lower() if name=='cppcheck' else 'gcc' in text.lower())
                entry.update(status='available' if p.returncode==0 and recognized else 'unavailable',
                             version=text.splitlines()[0] if text else None,returncode=p.returncode,raw_version=text)
            except LimitReached as error:entry.update(status='timed_out' if 'timed out' in str(error) else 'not_attempted',reason=str(error))
            except (OSError,RuntimeError) as error:entry['reason']=str(error)
        else:entry['reason']='Not found on PATH or bounded known installation paths; supply an explicit executable.'
        tools.append(entry)
    return dict(schema='smartparse.doctor',schema_version='1.0',tools=tools,usage=budget.usage(),
                scope='PATH, explicit/environment overrides, pinned v7 external paths, common Windows LLVM/MinGW and at most eight NDKs per SDK root',
                limitation='Version availability is not checker capability, compatible headers, or complete analysis.')
