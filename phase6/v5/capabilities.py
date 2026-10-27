"""Probe the installed driver, never assume checker or warning availability."""
import re
from dataclasses import asdict
from phase6.v1.evaluation import fingerprint

CHECKERS=('alpha.security.ArrayBoundV2','alpha.unix.cstring.OutOfBounds',
          'alpha.unix.Stream','alpha.security.MallocOverflow')
WARNINGS=('-Warray-bounds','-Wsizeof-pointer-memaccess','-Wreturn-stack-address','-Walloc-size')


def checker_names(text,help_output=False):
    pattern=r'^\s{2}([A-Za-z]\w*(?:\.\w+)+)\s' if help_output else r'^([A-Za-z]\w*(?:\.\w+)+)\s*$'
    return sorted(set(re.findall(pattern,text,re.M)))


def audit(controller,compiler,config):
    result={'schema':'smartparse.memory_capabilities','schema_version':'1.0','compiler':asdict(compiler),
            'config':list(config),'binding':fingerprint([asdict(compiler),list(config)]),'raw':{},
            'available':[],'default_enabled':[],'checker_probes':[],'warning_probes':[]}
    for name,flag in [('available','-analyzer-checker-help'),('alpha_available','-analyzer-checker-help-alpha'),('default_enabled','-analyzer-list-enabled-checkers')]:
        p=controller.call('checker_inventory',[compiler.path,'--analyze','-x','c',*config,'-Xclang',flag,'-o',__import__('os').devnull,'-'],b'int probe;\n')
        text=p.stdout.decode('utf-8',errors='replace');err=p.stderr.decode('utf-8',errors='replace')
        result['raw'][name]={'returncode':p.returncode,'stdout':text,'stderr':err}
        if p.returncode==0:
            values=checker_names(text,help_output=name!='default_enabled')
            if name=='default_enabled':result['default_enabled']=values
            else:result['available']+=values
    result['available']=sorted(set(result['available']))
    for checker in CHECKERS:
        supported=False;reason='not advertised by installed driver'
        if checker in result['available']:
            p=controller.call('checker_capability',[compiler.path,'--analyze','-x','c',*config,'-Xclang','-analyzer-checker='+checker,'-o',__import__('os').devnull,'-'],b'int probe;\n')
            supported=p.returncode==0 and not p.stderr.strip()
            reason='advertised and clean invocation probe' if supported else p.stderr.decode('utf-8',errors='replace')
        result['checker_probes'].append({'checker':checker,'supported':supported,'experimental':True,
                                         'already_default':checker in result['default_enabled'],'reason':reason})
    for flag in WARNINGS:
        p=controller.call('warning_capability',[compiler.path,'-x','c','-fsyntax-only',*config,flag,'-'],b'int probe;\n')
        result['warning_probes'].append({'flag':flag,'supported':p.returncode==0 and not p.stderr.strip(),
                                         'stderr':p.stderr.decode('utf-8',errors='replace'),'returncode':p.returncode})
    return result


def selected_options(capability,compiler,config):
    if capability['binding']!=fingerprint([asdict(compiler),list(config)]):raise ValueError('capability cache compiler/config mismatch')
    checks=[p['checker'] for p in capability['checker_probes'] if p['supported'] and p['checker'] in CHECKERS and not p['already_default']]
    warnings=[p['flag'] for p in capability['warning_probes'] if p['supported'] and p['flag'] in WARNINGS]
    return checks,warnings
