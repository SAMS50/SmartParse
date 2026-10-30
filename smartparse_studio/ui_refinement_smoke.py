"""Real UI checks against running local servers; no C programs are executed."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright,expect


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome',required=True)
    parser.add_argument('--output',default='.studio-artifacts/ui-refinement/browser')
    args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=args.chrome,headless=True)
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:5173')
        service=page.get_by_label('Analysis service status')
        expect(service).to_have_text('Ready',timeout=60000)
        assert not page.get_by_text(re.compile('tools available')).count()
        checks.append('live-service-ready')
        page.get_by_role('button',name='About Studio').click()
        expect(page.get_by_role('heading',name='Analysis limitations')).to_be_visible()
        expect(page.get_by_text('SmartParse checks your code without running it. Some errors may not be detected.')).to_be_visible()
        page.get_by_role('button',name='Close about').click()
        assert not page.get_by_text('Static analysis only',exact=False).count()
        checks.append('help-limitations-not-persistent')
        source='int read_value(void) {\n int *p=0;\n return *p;\n}\n'+'// retained scroll context\n'*180
        page.locator('.monaco-host .view-lines').click()
        page.evaluate("""source=>{const data=new DataTransfer();data.setData('text/plain',source);
          document.activeElement.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}))}""",source)
        page.get_by_role('button',name='Analysis settings').click()
        page.get_by_label(re.compile('Memory & resources')).check()
        page.get_by_label('Compiler diagnostics',exact=False).uncheck()
        page.get_by_role('button',name='Apply configuration').click()
        held=[];page.route('**/api/analyze',lambda route:held.append(route))
        page.get_by_role('button',name='Analyze',exact=True).click()
        loading=page.locator('.analysis-loading')
        expect(loading).to_have_text('Analyzing your source')
        assert loading.locator('svg').count()==1 and loading.locator('p').count()==1
        page.screenshot(path=str(out/'loading.png'),full_page=True)
        with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=65000) as response:held[0].continue_()
        assert response.value.status==200,response.value.text()
        body=response.value.json();submitted=response.value.request.post_data_json['source']
        assert body['report']['source']['sha256']==hashlib.sha256(submitted.encode()).hexdigest()
        assert body['studio']['workspace_removed'] and body['report']['source']['original_unchanged']
        checks.append('minimal-loading-real-analysis')
        record=next(d for d in body['report']['diagnostics'] if d['diagnostic_id']=='core.NullDereference')
        diagnostic=page.get_by_role('button',name=record['message'],exact=True)
        expect(diagnostic).to_be_enabled();diagnostic.click()
        expect(page.locator('.monaco-host .squiggly-warning').first).to_be_attached()
        cursor=page.locator('.editor-footer').inner_text()
        model_node=page.locator('.monaco-host .monaco-editor').first.element_handle()
        page.locator('.examples-section > summary').click()
        divider=page.get_by_role('separator',name='Resize Explorer')
        box=divider.bounding_box();page.mouse.move(box['x']+2,box['y']+100);page.mouse.down();page.mouse.move(box['x']+62,box['y']+100,steps=8);page.mouse.up()
        width=page.locator('.explorer').bounding_box()['width']
        assert width>260
        host=page.locator('.monaco-host');host.hover()
        for _ in range(24):page.mouse.wheel(0,450);page.wait_for_timeout(50)
        page.wait_for_function("Number(document.querySelector('.monaco-host .line-numbers')?.textContent)>30")
        page.wait_for_timeout(300)
        first_line=host.locator('.line-numbers').first.inner_text()
        main_width=page.locator('.main-workspace').bounding_box()['width']
        toggle=page.get_by_role('button',name='Toggle Explorer')
        page.keyboard.press('Control+b')
        expect(toggle).to_have_attribute('aria-expanded','false')
        expect(page.locator('.explorer')).not_to_be_visible()
        expect(page.get_by_role('separator',name='Resize Explorer')).to_have_count(0)
        assert page.locator('.activity-rail').is_visible()
        assert page.locator('.main-workspace').bounding_box()['width']>main_width+width-2
        page.wait_for_timeout(300)
        assert host.locator('.line-numbers').first.inner_text()==first_line
        assert model_node.evaluate("el=>el===document.querySelector('.monaco-host .monaco-editor')")
        assert abs(host.bounding_box()['width']-host.locator('.monaco-editor').first.bounding_box()['width'])<=2
        checks.extend(['explorer-pointer-resize','ctrl-b-reclaims-space','monaco-layout-and-scroll-retained'])
        toggle.click();expect(toggle).to_have_attribute('aria-expanded','true')
        assert abs(page.locator('.explorer').bounding_box()['width']-width)<=1
        assert page.locator('.examples-section').evaluate('el=>el.open')
        assert page.locator('.editor-footer').inner_text()==cursor
        diagnostic.click();expect(page.locator('.monaco-host .squiggly-warning').first).to_be_attached()
        with page.expect_download() as exported:page.get_by_role('button',name='Export JSON report').click()
        assert json.loads(Path(exported.value.path()).read_text())==body
        checks.append('files-cursor-markers-results-and-width-retained')
        page.screenshot(path=str(out/'expanded.png'),full_page=True)
        with page.expect_download() as saved:page.keyboard.press('Control+s')
        assert Path(saved.value.path()).read_bytes()==submitted.encode()
        toggle.click();page.screenshot(path=str(out/'collapsed.png'),full_page=True)
        page.reload();expect(service).to_have_text('Ready',timeout=60000)
        expect(toggle).to_have_attribute('aria-expanded','false')
        toggle.click();assert abs(page.locator('.explorer').bounding_box()['width']-width)<=1
        checks.append('session-preference-restored')
        page.set_viewport_size({'width':390,'height':844})
        expect(page.locator('.activity-rail')).to_be_visible()
        page.keyboard.press('Control+b');expect(page.locator('.explorer')).to_be_visible()
        page.keyboard.press('Control+b');expect(page.locator('.explorer')).not_to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        expect(service).to_have_text('Ready')
        checks.append('mobile-activity-bar-and-ready-visible')
        # Controlled network failure, without stopping the user's API server.
        page.route('**/api/health',lambda route:route.fulfill(status=503,json={'detail':'test service unreachable'}))
        expect(service).to_have_text('Unavailable',timeout=22000)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(out/'unavailable-mobile.png'),full_page=True)
        checks.append('unreachable-health-is-unavailable')
        browser.close()
    assert not errors,errors
    result={'checks':checks,'passed':len(checks),'page_errors':errors,'preserved_scroll_line':first_line}
    (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':main()
