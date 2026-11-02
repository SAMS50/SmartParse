"""Real edit/history regression plus adaptive standard-header fallback in Studio."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from playwright.sync_api import sync_playwright,expect


def main():
    p=argparse.ArgumentParser();p.add_argument('--chrome',required=True);p.add_argument('--output',default='.studio-artifacts/m14/browser');a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-m','phase6.v11.browser_smoke','--chrome',a.chrome,'--output',str(out/'edit-undo')],check=True,timeout=180)
    source='#include <stdio.h>\nint main(){return 0}\n'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=a.chrome,headless=True);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:5173');analyze=page.get_by_role('button',name='Analyze',exact=True)
        expect(analyze).to_be_enabled(timeout=60000)
        page.locator('input[type=file]').set_input_files(dict(name='header-demo.c',mimeType='text/x-c',buffer=source.encode()))
        expect(page.get_by_role('tab',name='header-demo.c')).to_have_attribute('aria-selected','true')
        page.get_by_role('button',name='Analysis settings').click();page.get_by_role('checkbox',name='Intent-aware recovery').check()
        page.get_by_role('button',name='Apply configuration').click()
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as received:analyze.click()
        response=received.value;assert response.status==200,response.text();result=response.json();request=response.request.post_data_json
        r=result['report']['intent_recovery'];assert request['intent_version']=='v14';assert r['decision_mode']=='SYNTAX_ONLY',r
        c=next(c for c in r['candidates'] if c['id']==r['recommendation']);assert 'clang_fixit' in c['origins']
        assert c['source']==source.replace('0}','0;}');assert request['source']==source
        evidence=page.get_by_label('Intent-aware recovery evidence')
        expect(evidence).to_contain_text('lower-assurance');expect(evidence).to_contain_text('Clang compiler');expect(evidence).to_contain_text('Unavailable:')
        expect(page.get_by_label('Proposed correction diff')).to_be_visible()
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as repeated:analyze.click()
        assert repeated.value.request.post_data_json['source']==source
        assert not errors,errors
        page.screenshot(path=str(out/'adaptive-fallback.png'),full_page=True)
        (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (out/'checks.json').write_text(json.dumps(dict(history_edit_undo_regression=True,adaptive_header_recovery=True,
            clang_origin_visible=True,evidence_availability_visible=True,original_source_unchanged=True,read_only_comparison=True,browser_errors=errors),indent=2),encoding='utf-8')
        browser.close()
    print('Passed: adaptive real-C fallback, attribution, evidence availability, comparison and existing edit/undo workflow')


if __name__=='__main__':main()
