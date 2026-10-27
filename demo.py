"""Reproducible demonstrations of default and opt-in verified CGAR modes."""
import argparse
from smartparse import Parser, tokenize

EXAMPLES = {
    'multiple': 'int x = 1 if (x > 0] { x = 2; }',
    'operator': 'int x == 1;',
    'unsupported': 'int x = ;',
    'valid': 'int x = 1;',
    'ambiguous': 'int x = 1;;',
}

def run(source, verified=False):
    parser = Parser(tokenize(source), verified_cgar=verified)
    parser.parse()
    return parser

def main():
    ap = argparse.ArgumentParser(description='SmartParse reproducible demo')
    ap.add_argument('--example', choices=tuple(EXAMPLES), default='multiple')
    ap.add_argument('--mode', choices=('original', 'cgar'), default='cgar')
    ap.add_argument('--source', help='Optional source code instead of the built-in example')
    args = ap.parse_args()
    source = args.source if args.source is not None else EXAMPLES[args.example]
    p = run(source, verified=args.mode == 'cgar')
    print('SOURCE:', source)
    print('MODE:', args.mode)
    print('CGAR STATUS:', p.verified_cgar_status)
    print('DIAGNOSTICS:', len(p.diagnostics))
    for d in p.diagnostics: print('  ', d)
    print('SUGGESTED REPAIRS:', len(p.repairs))
    for r in p.repairs: print('  ', r)
    print('NOTE: repairs are suggestions; grammar validity does not establish intent.')

if __name__ == '__main__': main()
