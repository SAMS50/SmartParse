import argparse
import json
from pathlib import Path
from .engine import recover


def main():
    p=argparse.ArgumentParser(description='Read-only evidence-adaptive C recovery')
    p.add_argument('source');p.add_argument('--history');p.add_argument('--provider',choices=('custom','compiler','combined'),default='combined');p.add_argument('--output')
    a=p.parse_args();path=Path(a.source);source=path.read_bytes().decode('utf-8')
    history=json.loads(Path(a.history).read_text(encoding='utf-8')) if a.history else None
    result=recover(source,history,provider=a.provider);text=json.dumps(result,indent=2)
    if a.output:
        out=Path(a.output)
        if out.resolve()==path.resolve() or (out.exists() and out.samefile(path)) or (a.history and out.resolve()==Path(a.history).resolve()):p.error('Output must differ from source/history inputs')
        out.write_text(text,encoding='utf-8')
    else:print(text)


if __name__=='__main__':main()
