"""Bounded syntax-only compiler baselines; reliable machine edits only."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from phase6.v3.execution import bounded_run
from phase6.v3.policy import fixits,point_offset
from smartparse_cli.tools import locate
from .ingest import privacy_or_safety,sha


def classify(message):
    text=message.lower()
    if any(s in text for s in ('file not found','no such file','cannot open include')):return 'include/environment'
    if any(s in text for s in ('expected','extraneous','unterminated','unclosed','missing terminating','stray')):return 'syntax/delimiter'
    if any(s in text for s in ('undeclared','not declared','unknown type','implicit declaration')):return 'name/type'
    if any(s in text for s in ('incompatible','invalid operands','too few arguments','too many arguments','called object')):return 'type/expression'
    return 'other'


def diagnostics(stderr):
    result=[]
    for line in stderr.splitlines():
        m=re.match(r'^(.*?):(\d+):(\d+):\s*(fatal error|error|warning|note):\s*(.*)$',line)
        if m:result.append(dict(file=m[1],line=int(m[2]),column=int(m[3]),severity=m[4],message=m[5],category=classify(m[5])))
    return result


def apply_fixits(source,edits):
    data=source.encode('utf-8');patches=[]
    if not edits:return None,'no machine fix-it edits'
    if len(edits)>24:return None,'fix-it edit budget exceeded'
    try:
        for e in edits:
            if e['file'] not in ('<stdin>','-'):return None,'edit outside physical stdin source'
            a=point_offset(data,e['start_line'],e['start_column']);b=point_offset(data,e['end_line'],e['end_column'])
            if a>b:return None,'reversed source range'
            # Decoding prefixes verifies that byte coordinates do not split UTF-8.
            data[:a].decode('utf-8');data[:b].decode('utf-8')
            patches.append((a,b,e['replacement'].encode('utf-8')))
        patches=sorted(patches)
        if len(set(patches))!=len(patches):return None,'duplicate edit hints require disambiguation'
        if any(b>c or a==c for (a,b,_),(c,d,__) in zip(patches,patches[1:])):return None,'overlapping or alternative edit hints'
        repaired=data
        for a,b,value in reversed(patches):repaired=repaired[:a]+value+repaired[b:]
        text=repaired.decode('utf-8')
        if privacy_or_safety(text):return None,'result fails supported input policy'
        return text,'applied nonoverlapping physical byte-range edits'
    except (KeyError,TypeError,ValueError,UnicodeError):return None,'invalid fix-it encoding or physical range'


class Compiler:
    def __init__(self,name,timeout=3,execute=bounded_run):
        self.name=name;self.path=locate(name);self.timeout=timeout;self.execute=execute
        self.flags=['-x','c','-std=c11','-fsyntax-only','-fdiagnostics-color=never']
        self.identity=dict(name=name,status='unavailable',version=None,flags=self.flags[:],fixit_format=None)
        if not self.path:return
        try:
            version=self._call(['--version'])
            text=version.stdout.decode(errors='replace')
            if version.returncode or name not in text.lower():return
            probe=self._call(self.flags+['-'],b'int capability_probe;\n')
            if probe.returncode:return
            fixprobe=self._call(self.flags+['-fdiagnostics-parseable-fixits','-'],b'int capability_probe;\n')
            if not fixprobe.returncode:self.flags.append('-fdiagnostics-parseable-fixits')
            self.identity.update(status='available',version=text.splitlines()[0],flags=self.flags[:],
                fixit_format='compiler parseable physical edits' if not fixprobe.returncode else 'unsupported')
        except (OSError,subprocess.TimeoutExpired):pass

    def _call(self,args,data=None):
        # Only an evaluator-owned temporary .c copy is passed as a file. No
        # downloaded filename becomes a compiler argument, and no code is run.
        with tempfile.TemporaryDirectory(prefix='smartparse-v13-compiler-') as work:
            argv=list(args);path=Path(work)/'input.c'
            if data is not None:
                if not argv or argv[-1]!='-':raise ValueError('Source calls must name stdin placeholder')
                path.write_bytes(data);argv[-1]=str(path)
            p=self.execute([self.path,*argv],capture_output=True,shell=False,timeout=self.timeout)
            # Explicit one-file coordinate mapping for reliable fix-it extraction.
            # Preserve unmodified diagnostics locally as well.
            p.raw_stderr=p.stderr
            for encoded in (str(path).replace('\\','\\\\').encode(),str(path).encode(),path.as_posix().encode()):
                p.stderr=p.stderr.replace(encoded,b'<stdin>')
            return p

    def check(self,source):
        if self.identity['status']!='available':return dict(status='unavailable',accepted=None,diagnostics=[],fixits=[],elapsed_ms=0)
        rejection=privacy_or_safety(source)
        if rejection:return dict(status='excluded',reason=rejection,accepted=None,diagnostics=[],fixits=[],elapsed_ms=0)
        start=time.perf_counter()
        command=[self.path,*self.flags,'-']
        try:
            p=self._call([*self.flags,'-'],source.encode('utf-8'));stderr=p.stderr.decode('utf-8',errors='replace')
            hints=[];hint_reason=None
            try:hints=fixits(p.stderr) if '-fdiagnostics-parseable-fixits' in self.flags else []
            except (ValueError,UnicodeError):hint_reason='invalid or excessive machine fix-it output'
            ds=diagnostics(stderr)
            status='completed' if p.returncode in (0,1) else 'failed'
            environmental=any(d['category']=='include/environment' for d in ds)
            return dict(status=status,accepted=p.returncode==0 if status=='completed' else None,exit_status=p.returncode,
                command=p.args,diagnostics=ds,stderr=stderr,raw_stderr=p.raw_stderr.decode('utf-8',errors='replace'),fixits=hints,fixit_issue=hint_reason,
                environment_failure=environmental,elapsed_ms=(time.perf_counter()-start)*1000,
                resources=dict(stdout_bytes=len(p.stdout),stderr_bytes=len(p.stderr),compiler_invocations=1,peak_rss_bytes=None,cpu_seconds=None))
        except (OSError,subprocess.TimeoutExpired) as error:
            return dict(status='timed_out' if isinstance(error,subprocess.TimeoutExpired) else 'unavailable',accepted=None,
                reason=type(error).__name__,command=command,diagnostics=[],fixits=[],elapsed_ms=(time.perf_counter()-start)*1000)

    def repair(self,source,original=None):
        original=original or self.check(source)
        repaired,reason=apply_fixits(source,original.get('fixits',[]))
        validation=self.check(repaired) if repaired is not None else None
        return dict(original=original,applicable=repaired is not None,applicability_reason=reason,
                    repaired_source=repaired,repaired_sha256=sha(repaired) if repaired is not None else None,validation=validation)
