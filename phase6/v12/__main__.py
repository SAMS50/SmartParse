"""Read-only intent recovery entry point; the v11 CLI remains unchanged."""
import argparse
import json
from pathlib import Path
from .engine import recover,MODES


def main():
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--history');p.add_argument('--mode',choices=MODES,default='full');p.add_argument('--output')
    a=p.parse_args();path=Path(a.source);text=path.read_bytes().decode('utf-8')
    h=json.loads(Path(a.history).read_text(encoding='utf-8')) if a.history else None
    result=recover(text,h,a.mode);data=json.dumps(result,indent=2)
    if a.output:
        out=Path(a.output)
        if out.resolve()==path.resolve() or (out.exists() and out.samefile(path)) or (a.history and out.resolve()==Path(a.history).resolve()):p.error('Output must differ from inputs')
        out.write_text(data,encoding='utf-8')
    else:print(data)


if __name__=='__main__':main()
