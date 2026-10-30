from pathlib import PurePath
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator

MAX_SOURCE_BYTES=128*1024
Analyzer=Literal['compiler','static','memory','semantic','gcc14','cppcheck','smartparse','panic']


class AnalysisRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    source:str=Field(max_length=MAX_SOURCE_BYTES)
    filename:str=Field(default='untitled.c',min_length=3,max_length=100)
    analyzers:list[Analyzer]=Field(default_factory=lambda:['compiler'],min_length=1,max_length=8)
    recovery:bool=False
    isolation:bool=False
    standard:Literal['c89','c99','c11','c17','gnu11']='c11'

    @field_validator('source')
    @classmethod
    def source_size(cls,value):
        if '\0' in value:raise ValueError('NUL characters are not supported')
        if len(value.encode('utf-8'))>MAX_SOURCE_BYTES:raise ValueError('Source exceeds 128 KiB UTF-8 limit')
        return value

    @field_validator('filename')
    @classmethod
    def safe_filename(cls,value):
        if any(c in value for c in '/\\:\0\r\n<>"|?*') or '..' in value or PurePath(value).suffix.lower()!='.c':
            raise ValueError('Use a .c filename without paths, drives or traversal')
        stem=value.split('.')[0].upper()
        if stem in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
            raise ValueError('Reserved device filenames are not supported')
        if any(ord(c)<32 for c in value):raise ValueError('Control characters are not allowed')
        return value
