"""Bound validation commands without risking inherited-pipe deadlocks.

Only processes created here are stopped. Output goes directly to a log file so
an orphaned descendant cannot hold a captured stdout/stderr pipe open forever.
"""
import os
from pathlib import Path
import signal
import subprocess
import time


def run_logged(command, log, *, timeout, env=None, cwd=None):
    if timeout<=0:raise ValueError('supervisor timeout must be positive')
    started=time.monotonic()
    options={'creationflags':subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    with Path(log).open('wb') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,shell=False,env=env,cwd=cwd,**options)
        timed_out=False;cleanup=None
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name=='nt':
                try:
                    killed=subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=stream,stderr=stream,timeout=5,shell=False)
                    cleanup=f'taskkill exit {killed.returncode}'
                except (OSError,subprocess.TimeoutExpired) as error:cleanup=str(error)
            else:
                try:os.killpg(child.pid,signal.SIGKILL);cleanup='owned process group killed'
                except ProcessLookupError:cleanup='already exited'
            try:code=child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                try:code=child.wait(timeout=2)
                except subprocess.TimeoutExpired:code=None
    return {'command':list(command),'exit_code':code,'timed_out':timed_out,
            'timeout_seconds':timeout,'elapsed_seconds':round(time.monotonic()-started,3),'cleanup':cleanup,'log':str(log)}
