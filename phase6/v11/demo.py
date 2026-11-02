"""Reproducible reconstructed edit; all decisions come from the actual engine."""
import json
from .engine import recover,MODES
from .history import reconstruct


def main():
    initial='int f(int x){if(x){x++;}return x;}'
    editor=initial.replace('}return','return');saved=editor
    event=reconstruct(initial,editor)
    print(json.dumps(dict(initial_source=initial,editor_source=editor,history=event,
        runs={mode:recover(editor,event,mode) for mode in MODES},editor_unchanged=editor==saved),indent=2))


if __name__=='__main__':main()
