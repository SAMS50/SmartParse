"""Bounded private worker: delegate directly to the existing unified engine."""
import json
from pathlib import Path
import sys
from smartparse_cli import analyze


def main():
    config=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    report=analyze(config['path'],analyzers=config['analyzers'],standard=config['standard'],
        recovery=config['recovery'],isolation=config['isolation'],timeout=5,total_timeout=45,max_invocations=96)
    text=json.dumps(report,ensure_ascii=True,allow_nan=False)
    if len(text)>16*1024*1024:
        print(json.dumps({'worker_error':'Analysis report exceeds the 16 MiB Studio response limit; use the CLI.'}));return 1
    print(text);return 0


if __name__=='__main__':sys.exit(main())
