"""Real browser workspace demonstration; requires already running local servers.

No C is executed. Reports/screenshots stay outside distributed research evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright, expect


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome',required=True)
    parser.add_argument('--output',default='.studio-artifacts/m10-2/browser')
    args=parser.parse_args();output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[];submitted={}
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=args.chrome,headless=True)
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:5173')
        analyze=page.get_by_role('button',name='Analyze',exact=True)
        expect(analyze).to_be_enabled(timeout=60000)
        def write(source):
            page.locator('.monaco-host .view-lines').click()
            page.keyboard.press('Control+a')
            # Exercise Monaco's paste handler without changing the OS clipboard.
            # Multiline Input.insertText is a typing operation and triggers
            # auto-closing/indentation rather than normal paste semantics.
            page.evaluate("""source=>{const data=new DataTransfer();data.setData('text/plain',source);
                document.activeElement.dispatchEvent(new ClipboardEvent('paste',
                {clipboardData:data,bubbles:true,cancelable:true}))}""",source)
        def run(name):
            with page.expect_response(lambda r:r.url.endswith('/api/analyze') and r.request.method=='POST',timeout=65000) as response:analyze.click()
            assert response.value.status==200,response.value.text()
            result=response.value.json()
            submitted[name]=response.value.request.post_data_json
            assert result['report']['source']['sha256']==hashlib.sha256(submitted[name]['source'].encode('utf-8')).hexdigest()
            assert result['studio']['workspace_removed'] and result['report']['source']['original_unchanged']
            expect(analyze).to_be_enabled(timeout=10000)
            (output/(name+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
            checks.append(name);return result
        page.get_by_role('button',name='New File',exact=True).click()
        expect(page.get_by_role('tab',name='untitled-2.c')).to_have_attribute('aria-selected','true')
        checks.append('blank-new-file')
        write('int main(void) {\n return 0\n}\n')
        page.get_by_role('button',name='Rename untitled-2.c').click()
        page.get_by_role('textbox',name='File name').fill('manual.c')
        page.get_by_role('button',name='Rename',exact=True).click()
        invalid=run('manual-invalid')
        assert submitted['manual-invalid']['source'].replace('\r\n','\n')=='int main(void) {\n return 0\n}\n'
        errors_found=[d for d in invalid['report']['diagnostics'] if d['severity'] in ('error','fatal error') and not d['context_note']]
        assert errors_found
        diagnostic=next(d for d in errors_found if d['id'] in invalid['studio']['editor_locations'])
        page.get_by_role('button',name=diagnostic['message'],exact=True).click()
        location=invalid['studio']['editor_locations'][diagnostic['id']]
        expect(page.get_by_text(f"Ln {location['line']}, Col {location['column']}",exact=True)).to_be_visible()
        checks.append('manual-diagnostic-navigation')
        fixed='int main(void) {\n return 0;\n}\n';write(fixed)
        expect(page.get_by_text('Source changed since this report.',exact=False)).to_be_visible()
        checks.append('stale-source-protection')
        valid=run('manual-fixed')
        assert valid['report']['summary']['errors']==0
        with page.expect_download() as source:page.keyboard.press('Control+s')
        assert Path(source.value.path()).read_bytes()==submitted['manual-fixed']['source'].encode('utf-8')
        assert source.value.suggested_filename=='manual.c'
        checks.append('ctrl-s-exact-source-download')
        with page.expect_download() as report:page.get_by_role('button',name='Export JSON report').click()
        assert json.loads(Path(report.value.path()).read_text(encoding='utf-8'))==valid
        checks.append('exact-json-export')
        page.screenshot(path=str(output/'workspace.png'),full_page=True)
        page.get_by_role('button',name='New File',exact=True).click()
        expect(page.get_by_role('button',name='Export JSON report')).to_be_disabled()
        page.get_by_role('tab',name='manual.c').click()
        expect(page.get_by_role('button',name='Export JSON report')).to_be_enabled()
        checks.append('per-file-report-ownership')
        page.get_by_role('tab',name='untitled-3.c').click()
        write('int helper(void) {\n return 23\n}\nint read_value(void) {\n int *p=0;\n return *p;\n}\n')
        page.get_by_role('button',name='Analysis settings').click()
        page.get_by_label(re.compile('Memory & resources')).check()
        page.get_by_label('Compiler diagnostics',exact=False).uncheck()
        page.get_by_label('Punctuation recovery',exact=False).check()
        page.get_by_role('button',name='Apply configuration').click()
        repaired=run('manual-recovery')
        assert repaired['studio']['previews']
        assert any(d['conditioning']=='repair-conditioned' for d in repaired['report']['diagnostics'])
        expect(page.locator('.monaco-diff-editor .line-insert').first).to_be_attached(timeout=15000)
        checks.append('manual-conditioned-recovery-preview')
        page.screenshot(path=str(output/'recovery.png'),full_page=True)
        page.get_by_role('button',name='New File',exact=True).click()
        page.locator('.monaco-host .view-lines').click();page.keyboard.type('int fast_value = 123;')
        with page.expect_download() as typed:page.keyboard.press('Control+s')
        assert Path(typed.value.path()).read_text(encoding='utf-8')=='int fast_value = 123;'
        checks.append('rapid-typing-exact-buffer')
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(output/'mobile.png'),full_page=True)
        checks.append('mobile-no-horizontal-overflow')
        browser.close()
    assert not errors,errors
    result={'checks':checks,'passed':len(checks),'page_errors':errors}
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
