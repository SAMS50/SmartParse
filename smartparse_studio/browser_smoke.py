"""Optional real-browser smoke test against already running local Studio servers.

Requires Playwright and an installed Chrome; never downloads a browser or runs C.
Artifacts contain real local paths and are written outside historical evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome', required=True, help='Installed Chrome executable')
    parser.add_argument('--output', default='.studio-artifacts/browser')
    parser.add_argument('--polish', action='store_true', help='Also verify layout and panel-state regressions')
    args = parser.parse_args()
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    checks = []; errors = []; geometry = []; scroll_evidence = None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chrome, headless=True)
        page = browser.new_page(viewport={'width': 1536, 'height': 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:5173', wait_until='domcontentloaded')
        analyze = page.get_by_role('button', name='Analyze', exact=True)
        expect(analyze).to_be_enabled(timeout=60000)
        expect(page.get_by_role('button', name='Valid C', exact=True)).to_be_visible()
        if args.polish:
            for width,height in [(1366,768),(1280,800),(1920,1080)]:
                page.set_viewport_size({'width':width,'height':height})
                expect(page.locator('.monaco-host')).to_be_visible()
                editor_height=page.locator('.monaco-host').bounding_box()['height']
                assert editor_height >= 344, (width,height,editor_height)
                assert page.evaluate('document.documentElement.scrollHeight <= innerHeight && document.documentElement.scrollWidth <= innerWidth')
                geometry.append(dict(width=width,height=height,editor_height=editor_height,visible_line_capacity=int((editor_height-14)//22)))
                page.screenshot(path=str(output/f'layout-{width}x{height}.png'),full_page=True)
            checks.append('desktop-and-laptop-layout-capacity')

        def run(name):
            with page.expect_response(lambda r: r.url.endswith('/api/analyze') and r.request.method == 'POST', timeout=65000) as received:
                analyze.click()
            response = received.value
            assert response.status == 200, response.text()
            body = response.json()
            assert body['report']['source']['original_unchanged']
            assert body['studio']['workspace_removed']
            expect(analyze).to_be_enabled(timeout=10000)
            (output / (name + '.json')).write_text(json.dumps(body, indent=2), encoding='utf-8')
            checks.append(name)
            return body

        valid = run('valid')
        assert valid['report']['status'] == 'completed'
        assert not valid['report']['diagnostics']
        expect(page.get_by_text('No primary diagnostics reported.')).to_be_visible()
        if args.polish: page.screenshot(path=str(output/'valid-overview.png'),full_page=True)
        page.get_by_role('button', name='Null pointer', exact=True).click()
        null = run('null')
        diagnostic = next(d for d in null['report']['diagnostics'] if d['diagnostic_id'] == 'core.NullDereference')
        finding = page.get_by_role('button', name=diagnostic['message'], exact=True)
        expect(finding).to_be_enabled()
        expect(page.locator('.monaco-editor .squiggly-warning').first).to_be_attached()
        finding.click()
        location = null['studio']['editor_locations'][diagnostic['id']]
        expect(page.get_by_text(f"Ln {location['line']}, Col {location['column']}", exact=True)).to_be_visible()
        checks.append('real-monaco-marker-and-navigation')
        if args.polish:
            node=page.locator('.editor-pane .monaco-editor').first.element_handle()
            cursor=page.locator('.editor-footer').inner_text()
            divider=page.get_by_role('separator',name='Resize editor and diagnostics')
            before=page.locator('.editor-pane').bounding_box()['width']
            box=divider.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-100,y,steps=8);page.mouse.up()
            assert page.locator('.editor-pane').bounding_box()['width'] < before-60
            divider.focus();page.keyboard.press('ArrowRight')
            checks.append('pointer-and-keyboard-width-resize')
            details=page.get_by_role('separator',name='Resize analysis details')
            before=page.locator('.inspector').bounding_box()['height']
            box=details.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x,y-50,steps=8);page.mouse.up()
            assert page.locator('.inspector').bounding_box()['height'] > before+25
            details.focus();page.keyboard.press('ArrowDown')
            checks.append('pointer-and-keyboard-height-resize')
            page.get_by_role('button',name='Reset panel sizes').click()
            assert node.evaluate("el=>el===document.querySelector('.editor-pane .monaco-editor')")
            assert page.locator('.editor-footer').inner_text() == cursor
            expect(page.locator('.monaco-editor .squiggly-warning').first).to_be_attached()
            checks.append('resize-preserves-monaco-cursor-and-markers')
        page.screenshot(path=str(output / 'null-pointer.png'), full_page=True)
        with page.expect_download() as download:
            page.get_by_role('button', name='Export JSON report').click()
        exported = json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
        assert exported == null
        checks.append('exact-json-download')
        with page.expect_download() as download:
            page.get_by_role('button', name='Export Markdown report').click()
        markdown = Path(download.value.path()).read_text(encoding='utf-8')
        assert diagnostic['diagnostic_id'] in markdown and 'Complete machine evidence' in markdown
        checks.append('markdown-evidence-download')
        page.locator('.editor-pane .monaco-editor .view-lines').click()
        page.keyboard.press('Control+End'); page.keyboard.press('Enter'); page.keyboard.type('// edited in browser')
        expect(page.get_by_text('Source changed since this report.', exact=False)).to_be_visible()
        expect(finding).to_be_disabled()
        expect(page.locator('.editor-pane .squiggly-warning')).to_have_count(0)
        page.get_by_role('button', name='Reset code').click()
        checks.append('real-editor-stale-highlight-protection')

        page.get_by_role('button', name='Missing semicolon', exact=True).click()
        malformed = run('malformed')
        assert malformed['report']['summary']['errors'] > 0
        page.get_by_role('button', name='Recovery-assisted', exact=True).click()
        repaired = run('recovery')
        assert repaired['studio']['previews']
        assert any(d['conditioning'] == 'repair-conditioned' for d in repaired['report']['diagnostics'])
        expect(page.locator('.monaco-diff-editor')).to_be_visible()
        expect(page.locator('.monaco-diff-editor .line-insert').first).to_be_attached(timeout=15000)
        for preview in repaired['studio']['previews']:
            assert hashlib.sha256(preview['source'].encode()).hexdigest() == preview['sha256']
        checks.append('hash-verified-accepted-diff')
        page.screenshot(path=str(output / 'recovery.png'), full_page=True)
        page.locator('.diff-wrap').scroll_into_view_if_needed()
        page.screenshot(path=str(output / 'accepted-diff.png'), full_page=True)

        page.get_by_role('button', name='Analysis settings').click()
        page.get_by_label('Compiler diagnostics').check()
        page.get_by_role('button', name='Apply configuration').click()
        comparison = run('comparison')
        assert len(comparison['report']['runs']) >= 2
        page.get_by_role('button', name='Comparison', exact=True).click()
        expect(page.get_by_text('Counts are diagnostic records, not independent defects.', exact=False)).to_be_visible()
        assert page.locator('.run-table tbody tr').count() == len(comparison['report']['runs'])
        checks.append('multi-pass-comparison')
        page.screenshot(path=str(output / 'comparison.png'), full_page=True)

        page.get_by_role('button', name='Isolation-assisted', exact=True).click()
        isolated = run('isolation')
        assert any(p['conditioning'] == 'isolation-conditioned' for p in isolated['studio']['previews'])
        page.get_by_role('button', name='SmartParse recovery', exact=True).click()
        research = run('research')
        assert any(d.get('suggestion') for d in research['report']['diagnostics'])
        page.get_by_role('button', name='Recovery', exact=True).click()
        if page.get_by_text('Raw repair suggestions',exact=True).count():
            page.get_by_text('Raw repair suggestions',exact=True).click()
        expect(page.locator('.recovery-content pre').first).to_be_visible()
        checks.append('actual-research-suggestions')
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(output / 'mobile.png'), full_page=True)
        checks.append('mobile-no-horizontal-overflow')
        if args.polish:
            page.set_viewport_size({'width':1366,'height':768})
            # A real existing long fixture, imported read-only, never analyzed here.
            path=Path(__file__).resolve().parents[1]/'acceptance/cleaned/c_error_detection_500_lines.c'
            source_before=path.read_bytes()
            page.locator('input[type=file]').set_input_files(str(path))
            expect(page.get_by_text('Imported UTF-8 text.',exact=False)).to_be_visible()
            host=page.locator('.monaco-host')
            expect(host.locator('.view-lines')).to_contain_text('Approximately',timeout=5000)
            host.hover()
            # Monaco normalizes/clamps individual wheel deltas. Repeated real
            # wheel events exercise scrolling reliably instead of assuming one
            # very large delta moves thousands of pixels.
            for _ in range(24):
                page.mouse.wheel(0,450);page.wait_for_timeout(50)
            page.wait_for_function("Number(document.querySelector('.monaco-host .line-numbers')?.textContent)>30",timeout=5000)
            # Wait for Monaco's scroll animation to settle before measuring.
            page.wait_for_timeout(500)
            first=host.locator('.view-line').first.inner_text()
            first_number=host.locator('.line-numbers').first.inner_text()
            top=host.locator('.view-lines').evaluate('el=>el.style.top')
            divider=page.get_by_role('separator',name='Resize editor and diagnostics')
            divider.focus();page.keyboard.press('ArrowLeft')
            page.get_by_role('separator',name='Resize analysis details').focus();page.keyboard.press('ArrowUp')
            page.wait_for_timeout(300)
            assert host.locator('.view-line').first.inner_text()==first
            assert host.locator('.line-numbers').first.inner_text()==first_number
            assert host.locator('.view-lines').evaluate('el=>el.style.top')==top
            assert path.read_bytes()==source_before
            scroll_evidence={'first_rendered_line_before':first_number,'first_rendered_line_after':host.locator('.line-numbers').first.inner_text()}
            checks.append('long-source-scroll-position-preserved')
        browser.close()
    assert not errors, errors
    result = {'checks': checks, 'count': len(checks), 'page_errors': errors, 'geometry':geometry,'scroll_evidence':scroll_evidence}
    (output / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
