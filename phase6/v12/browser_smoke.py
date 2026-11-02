"""Actual browser v11 workflow regression plus v12 ambiguous-history behavior."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from playwright.sync_api import sync_playwright,expect


def main():
    p=argparse.ArgumentParser();p.add_argument('--chrome',required=True);p.add_argument('--output',default='.studio-artifacts/m12/browser')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-m','phase6.v11.browser_smoke','--chrome',a.chrome,'--output',str(out/'regression')],check=True,timeout=180)
    initial='int f(int x){if(x){x++;return x;}}'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=a.chrome,headless=True);page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:5173');analyze=page.get_by_role('button',name='Analyze',exact=True)
        expect(analyze).to_be_enabled(timeout=60000)
        page.locator('.monaco-host .view-lines').click()
        page.evaluate("""source=>{const data=new DataTransfer();data.setData('text/plain',source);
          document.activeElement.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}))}""",initial)
        page.keyboard.press('Control+End');page.keyboard.press('Backspace')
        page.get_by_role('button',name='Analysis settings').click();page.get_by_role('checkbox',name='Intent-aware recovery').check()
        page.get_by_role('button',name='Apply configuration').click()
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as received:analyze.click()
        response=received.value;assert response.status==200,response.text();result=response.json();submitted=response.request.post_data_json['source']
        assert submitted==initial[:-1]
        evidence=result['report']['intent_recovery'];assert evidence['algorithm']=='milestone-12'
        assert evidence['recommendation'] is None;assert 'End-of-source' in evidence['reason']
        expect(page.get_by_text('Evidence reliability:',exact=False)).to_be_visible()
        expect(page.get_by_label('Intent-aware recovery evidence')).to_contain_text('programmer confirmation')
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as repeated:analyze.click()
        assert repeated.value.request.post_data_json['source']==submitted
        assert not errors,errors
        page.screenshot(path=str(out/'ambiguous-history.png'),full_page=True)
        (out/'ambiguous-history.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (out/'checks.json').write_text(json.dumps(dict(v11_workflow_regression=True,history_reliability_visible=True,
            ambiguous_history_abstention=True,original_unchanged=True,browser_errors=errors),indent=2),encoding='utf-8')
        browser.close()
    print('Passed v12 browser: existing edit/diff/undo workflow, real boundary-history abstention and reliability display')


if __name__=='__main__':main()
