"""One invocation/deadline accountant for all recovery compiler work."""
from dataclasses import dataclass
from contextlib import ExitStack
import hashlib
import os
import signal
import subprocess
import tempfile
import time


class LimitReached(RuntimeError): pass


def bounded_run(command, *, input=None, capture_output=True, shell=False, env=None, timeout):
    """Regular-file capture avoids inherited-pipe EOF waits after timeouts.

    All waits are finite. On timeout stop only this invocation's process tree.
    Cleanup gets at most six additional seconds; no unbounded communicate().
    """
    if shell or not capture_output:raise ValueError('bounded compiler runner requires no shell and captured output')
    with ExitStack() as stack:
        out=stack.enter_context(tempfile.TemporaryFile())
        err=stack.enter_context(tempfile.TemporaryFile())
        stdin=subprocess.DEVNULL
        if input is not None:
            stdin=stack.enter_context(tempfile.TemporaryFile());stdin.write(input);stdin.seek(0)
        options={'creationflags':subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
        child=subprocess.Popen(command,stdin=stdin,stdout=out,stderr=err,shell=False,env=env,**options)
        expired=False
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            expired=True
            if os.name=='nt':
                try:
                    subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,timeout=3,shell=False)
                except (OSError,subprocess.TimeoutExpired):pass
            else:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            try:code=child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                try:code=child.wait(timeout=1)
                except subprocess.TimeoutExpired:code=None
        except BaseException:
            child.kill()
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:pass
            raise
        out.seek(0);err.seek(0)
        stdout,stderr=out.read(),err.read()
        if expired:raise subprocess.TimeoutExpired(command,timeout,output=stdout,stderr=stderr)
        return subprocess.CompletedProcess(command,code,stdout,stderr)


@dataclass(frozen=True)
class Limits:
    candidates:int=4
    rounds:int=3
    invocations:int=48
    retained_variants:int=4
    edits:int=4
    total_seconds:float=90
    call_seconds:float=10

    def validate(self):
        import math
        for key,ceiling in [('candidates',8),('rounds',4),('invocations',80),('retained_variants',4),('edits',4)]:
            value=getattr(self,key)
            if type(value) is not int or not 1<=value<=ceiling:raise ValueError(f'{key} must be 1..{ceiling}')
        if not math.isfinite(self.total_seconds) or not 0<self.total_seconds<=120:raise ValueError('total_seconds must be positive and at most 120')
        if not math.isfinite(self.call_seconds) or not 0<self.call_seconds<=30:raise ValueError('call_seconds must be positive and at most 30')


class Budget:
    def __init__(self,limits,*,clock=time.monotonic,execute=None):
        limits.validate();self.limits=limits;self.clock=clock;self.execute=execute or bounded_run
        self.start=clock();self.calls=[];self.stopped=None

    def check(self):
        if self.stopped:raise LimitReached(self.stopped)
        remaining=self.limits.total_seconds-(self.clock()-self.start)
        if remaining<=0:
            self.stopped='total runtime budget exhausted';raise LimitReached(self.stopped)
        return remaining

    def call(self,role,command,data=None):
        remaining=self.check()
        if len(self.calls)>=self.limits.invocations:
            self.stopped='compiler invocation budget exhausted';raise LimitReached(self.stopped)
        entry={'number':len(self.calls)+1,'role':role,'command':list(command),'status':'running'}
        self.calls.append(entry);started=self.clock()
        env=os.environ.copy();env.update(LC_ALL='C',LANG='C',GCC_COLORS='')
        try:
            result=self.execute(list(command),input=data,capture_output=True,shell=False,env=env,
                                timeout=min(remaining,self.limits.call_seconds))
            entry.update(status='completed',returncode=result.returncode,
                         stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),stderr=result.stderr.decode('utf-8',errors='replace'))
            self.check()
            return result
        except subprocess.TimeoutExpired as error:
            entry.update(status='timed_out',returncode=None,stderr=(error.stderr or b'').decode('utf-8',errors='replace'))
            self.stopped='compiler call timed out; recovery stopped without further invocations'
            raise LimitReached(self.stopped) from error
        except OSError as error:
            entry.update(status='failed',issue=str(error));raise
        finally:entry['elapsed_seconds']=round(self.clock()-started,6)

    def usage(self):
        return {'compiler_invocations':len(self.calls),'elapsed_seconds':round(self.clock()-self.start,6),'calls':self.calls}
