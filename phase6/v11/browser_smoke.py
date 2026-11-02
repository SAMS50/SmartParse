"""Real Studio editing-history demonstration; running API/Vite required."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    p=argparse.ArgumentParser();p.add_argument('--chrome',required=True);p.add_argument('--output',default='.studio-artifacts/m11/browser')
    args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    initial='int f(int x){if(x){x++;}return x;}'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.chrome,headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:5173');analyze=page.get_by_role('button',name='Analyze',exact=True)
        expect(analyze).to_be_enabled(timeout=60000)
        page.locator('.monaco-host .view-lines').click()
        page.evaluate("""source=>{const data=new DataTransfer();data.setData('text/plain',source);
          document.activeElement.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}))}""",initial)
        page.keyboard.press('Control+Home')
        for _ in range(initial.index('}return')):page.keyboard.press('ArrowRight')
        page.keyboard.press('Delete')
        page.get_by_role('button',name='Analysis settings',exact=True).click()
        page.get_by_role('checkbox',name='Intent-aware recovery').check()
        page.get_by_role('button',name='Apply configuration').click()
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as received:analyze.click()
        response=received.value;assert response.status==200,response.text()
        request=response.request.post_data_json;result=response.json()
        assert request['source']==initial.replace('}return','return'),request
        assert request['edit_history']['events'][-1]['deleted']=='}'
        evidence=result['report']['intent_recovery']
        assert evidence['decision']=='recommended repair',evidence
        chosen=next(c for c in evidence['candidates'] if c['id']==evidence['recommendation'])
        assert chosen['source']==initial
        assert result['studio']['submitted_sha256']==hashlib.sha256(request['source'].encode()).hexdigest()
        page.get_by_role('button',name='Recovery',exact=True).click()
        expect(page.get_by_label('Intent-aware recovery evidence')).to_be_visible()
        expect(page.get_by_label('Proposed correction diff')).to_be_visible()
        # An actual second request verifies that showing the proposal did not edit source.
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as second:analyze.click()
        assert second.value.request.post_data_json['source']==request['source']
        # Monaco undo restores the deleted delimiter using its normal undo stack.
        page.locator('.monaco-host .view-lines').click();page.keyboard.press('Control+z')
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=80000) as third:analyze.click()
        assert third.value.request.post_data_json['source']==initial
        assert not errors,errors
        page.screenshot(path=str(out/'recovery.png'),full_page=True)
        (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (out/'checks.json').write_text(json.dumps(dict(recorded_delimiter_deletion=True,actual_recommendation=True,
            read_only_proposal=True,monaco_undo_preserved=True,browser_errors=errors),indent=2),encoding='utf-8')
        browser.close()
    print('Passed: real edit capture, intended repair, read-only diff, original preservation and Monaco undo')


if __name__=='__main__':main()
