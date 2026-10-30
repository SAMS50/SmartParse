"""Single user-facing entry point, preserving every legacy command."""
import argparse
import json
from pathlib import Path
import sys
from . import __version__
from .engine import ANALYZERS, analyze, exit_code
from .reporting import render,safe
from .tools import doctor


def build_parser():
    p=argparse.ArgumentParser(prog='python -m smartparse_cli',description='SmartParse: restricted-grammar research and compiler-backed C analysis. Never runs C programs or applies source edits.')
    p.add_argument('--version',action='version',version='SmartParse '+__version__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('analyze',help='analyze one .c translation unit')
    a.add_argument('source',help='.c path; quote Windows paths containing spaces')
    a.add_argument('--analyzers',default='compiler',help='comma-separated: '+', '.join(ANALYZERS)+' (default: compiler)')
    a.add_argument('--compiler',default='auto',help='auto, gcc, clang, or explicit compiler executable')
    a.add_argument('--clang',help='Clang executable for static/memory/semantic passes')
    a.add_argument('--gcc14',help='explicit executable for the existing pinned GCC14 analyzer profile')
    a.add_argument('--cppcheck',help='explicit executable for the existing pinned Cppcheck profile')
    a.add_argument('--std',default='c11',dest='standard',help='C standard accepted by selected tool(s), default c11')
    a.add_argument('-I','--include-dir',dest='include_dirs',action='append',default=[])
    a.add_argument('-D','--define',dest='defines',action='append',default=[])
    a.add_argument('--recovery',action='store_true',help='opt in to bounded semicolon recovery; adds memory pipeline if needed')
    a.add_argument('--isolation',action='store_true',help='opt in to experimental unaffected-function isolation; adds memory pipeline if needed')
    a.add_argument('--timeout',type=float,default=10,help='per tool call, 0 < seconds <= 30; default 10')
    a.add_argument('--total-timeout',type=float,default=120,help='shared overall budget, 0 < seconds <= 240; default 120')
    a.add_argument('--max-invocations',type=int,default=256,help='shared tool-call budget, 1..512; default 256')
    for item in (a,sub.add_parser('doctor',help='bounded tool installation/version inventory; no installation')):
        item.add_argument('--format',choices=('terminal','json','markdown'),default='terminal')
        item.add_argument('-o','--output',help='new report file (UTF-8); existing files are never overwritten')
    d=sub.choices['doctor']
    for name in ('gcc','clang','gcc14','cppcheck'):d.add_argument('--'+name,help='explicit '+name+' executable')
    return p


def emit(text,path):
    if path:
        # Exclusive creation prevents overwriting sources, hard links, research or review artifacts.
        with Path(path).open('x',encoding='utf-8',newline='\n') as stream:stream.write(text+'\n')
    else:
        if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
        print(text)


def main(argv=None):
    p=build_parser();a=p.parse_args(argv)
    try:
        if a.output and Path(a.output).exists():
            print('Output error: destination exists; choose a new file. No files overwritten.',file=sys.stderr);return 3
        if a.command=='doctor':
            r=doctor({name:getattr(a,name) for name in ('gcc','clang','gcc14','cppcheck')})
            if a.format=='json':text=json.dumps(r,indent=2,ensure_ascii=True)
            else:
                text=('SmartParse tool inventory\n' if a.format=='terminal' else '# SmartParse tool inventory\n\n')
                text+='\n'.join(f'{t["name"]}: {t["status"]}; {t["version"] or t.get("reason", "unknown")}; {t["path"]}' for t in r['tools'])
                text+='\nVersion availability does not certify checker capability or analysis coverage.'
                text=safe(text)
            code=0
        else:
            selected=[n.strip() for n in a.analyzers.split(',')]
            options={k:getattr(a,k) for k in ('compiler','clang','gcc14','cppcheck','standard','include_dirs','defines','recovery','isolation','timeout','total_timeout','max_invocations')}
            try:r=analyze(a.source,analyzers=selected,**options)
            except ValueError as error:p.error(str(error))
            text=render(r,a.format);code=exit_code(r)
        emit(text,a.output)
        return code
    except (OSError,RuntimeError,ValueError,TypeError,UnicodeError) as error:
        print('Tool/output failure: '+safe(error),file=sys.stderr);return 3


if __name__=='__main__':sys.exit(main())
