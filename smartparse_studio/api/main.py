"""Loopback-only API. Do not bind this unsandboxed compiler service publicly."""
import asyncio
import ipaddress
import json
import re
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse, Response
from .models import AnalysisRequest
from . import service

ORIGINS=('http://127.0.0.1:5173','http://localhost:5173')
MAX_BODY=256*1024


class LocalOnly:
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        headers={k.lower():v for k,v in scope['headers']}
        async def reject(code,message):
            await JSONResponse({'detail':message},status_code=code)(scope,receive,send)
        client=(scope.get('client') or ('',0))[0]
        try:local=ipaddress.ip_address(client).is_loopback
        except ValueError:local=False
        host=headers.get(b'host',b'').decode('ascii',errors='replace').lower()
        if not local or not re.fullmatch(r'(?:localhost|127\.0\.0\.1|\[::1\])(?::[0-9]{1,5})?',host):
            return await reject(403,'Studio accepts loopback clients and hosts only')
        origin=headers.get(b'origin',b'').decode('ascii',errors='replace')
        if origin and origin not in ORIGINS:return await reject(403,'Origin is not an approved local Studio frontend')
        if scope['method']=='POST':
            if headers.get(b'x-smartparse-studio')!=b'1':return await reject(403,'Studio request header is required')
            if not headers.get(b'content-type',b'').lower().startswith(b'application/json'):return await reject(415,'Use application/json')
        size=0;parts=[];deadline=asyncio.get_running_loop().time()+10
        while True:
            try:message=await asyncio.wait_for(receive(),max(.001,deadline-asyncio.get_running_loop().time()))
            except TimeoutError:return await reject(408,'Request body timed out')
            if message['type']=='http.disconnect':return
            body=message.get('body',b'');size+=len(body)
            if size>MAX_BODY:return await reject(413,'Request exceeds the 256 KiB body limit')
            parts.append(body)
            if not message.get('more_body',False):break
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:delivered=True;return {'type':'http.request','body':b''.join(parts),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)


app=FastAPI(title='SmartParse Studio',version='0.1.0',docs_url=None,redoc_url=None,openapi_url='/api/openapi.json')
app.add_middleware(CORSMiddleware,allow_origins=list(ORIGINS),allow_methods=['GET','POST','OPTIONS'],
                   allow_headers=['Content-Type','X-SmartParse-Studio'],allow_credentials=False)
app.add_middleware(LocalOnly)


@app.exception_handler(RequestValidationError)
async def invalid_request(request, error):
    # JSON permits escaped lone surrogates. Keep the ordinary validation envelope
    # but escape invalid Unicode so error rendering cannot itself raise a 500.
    return Response(json.dumps({'detail': jsonable_encoder(error.errors())}, ensure_ascii=True),
                    status_code=422, media_type='application/json')


@app.get('/api/health')
def health():return {'status':'ok','service':'SmartParse Studio','schema_version':'1.0','local_only':True}


@app.get('/api/tools')
def tools():return service.tools()


@app.get('/api/examples')
def examples():return {'examples':service.examples()}


@app.post('/api/analyze')
async def analyze(request:AnalysisRequest):return await run_in_threadpool(service.analyze_request,request)
