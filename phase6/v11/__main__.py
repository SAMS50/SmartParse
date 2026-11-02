import argparse
import json
from pathlib import Path
from .engine import MODES, recover


def main():
    p=argparse.ArgumentParser(description='Read-only intent-aware C recovery')
    p.add_argument('source');p.add_argument('--history');p.add_argument('--mode',choices=MODES,default='full');p.add_argument('--output')
    a=p.parse_args();source=Path(a.source).read_bytes().decode('utf-8')
    history=json.loads(Path(a.history).read_text(encoding='utf-8')) if a.history else None
    result=recover(source,history,a.mode);text=json.dumps(result,indent=2)
    if a.output:
        if Path(a.output).resolve()==Path(a.source).resolve() or (a.history and Path(a.output).resolve()==Path(a.history).resolve()):
            p.error('Output must differ from source and history files')
        Path(a.output).write_text(text,encoding='utf-8')
    else:print(text)


if __name__=='__main__':main()
