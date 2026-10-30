# SmartParse Studio

## Real code workspace (Milestone 10.2)

Studio starts with an empty `untitled-1.c` buffer. Use New File, write or paste C,
choose analyzers, and Analyze; examples are optional. New/Open/Save are available
in the top toolbar. On a narrow screen, Toggle Explorer opens the file list and
Examples. Escape dismisses it.

- Open imports one UTF-8 `.c` or `.h` file into a new tab. It does not upload user
  source to the backend until Analyze is clicked (or Ctrl+Enter).
- Tabs have stable identities and separate Monaco models/undo/view state. Switch
  with a click or Left/Right/Home/End on a focused tab. Explorer supports rename
  and remove. Renaming does not overwrite or rename the original disk file.
- Save and Ctrl+S **request a browser download** of the active buffer. They do not
  overwrite an imported file. The indicator tracks changes since import or the
  last requested download; it cannot certify the browser completed a disk write.
  Closing a changed/renamed file asks before discarding its in-memory copy.
- Files are held in browser memory, not a real folder. Refresh/closing the page
  loses the workspace; download source first. A before-unload warning protects
  modified buffers where the browser supports it. The workspace supports up to
  20 tabs; source/import requests remain limited to 128 KiB UTF-8 per file.
- Only the active buffer is submitted. Other open `.c`/`.h` buffers are **not**
  linked, compiled together or supplied as include files. Header buffers use a
  standalone `.c` analysis copy; the raw report retains that actual temporary
  compiler filename. This is not a project/build-system interface.
- Reports belong to file IDs and submitted source snapshots. Switching files
  restores their retained reports. Editing or renaming marks findings stale and
  disables navigation/markers until reanalysis. Save/Analyze read the current
  Monaco model so rapid edits cannot submit an older React state value.
- Problems has a compact summary and source-navigation list. Details collapse
  to a tab strip; choosing a tab expands them. Recovery/isolation remain explicit
  opt-ins and work with manually entered source. Conditional evidence, accepted
  temporary previews and raw exports retain the existing backend provenance.
- Examples are in a collapsible section. Every selection opens an editable copy,
  with a unique name if needed; frozen fixtures are never modified.

The palette is neutral charcoal with a muted blue active accent. Red/amber/green
indicate actual diagnostic or operational states; syntax highlighting retains its
language colors. No accuracy metric or simulated diagnostic is shown.

For the real browser demonstration (already running API and Vite required):

```powershell
python -m smartparse_studio.workspace_smoke --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe" --output .studio-artifacts/m10-2/browser
```

It exercises New File → paste invalid C → actual compiler diagnostic/navigation
→ correction → reanalysis → source download, plus rapid typing, manual recovery,
headers, tabs, unsaved protection, comparison, isolation and mobile navigation.
It verifies submitted hashes and downloaded bytes using the editor's actual line
endings. Its paste event uses test-owned data without replacing the OS clipboard.

Frontend tests use one isolated VM worker to avoid repeated expensive jsdom
startup on constrained Windows hosts. Assertions remain intact, with a 15-second
per-test bound; automated validation commands also use overall supervisors.
Run browser and full regression checks sequentially on low-memory machines.

Studio is a local React workbench for the existing SmartParse unified engine. It
does not add detection rules or change CGAR, compiler recovery, or isolation.
Independent human adjudication of research findings remains pending.

## Minimal analysis states and Explorer

The analysis loading panel contains only a subtle spinner and **Analyzing your
source**. Existing cancellation, analyzer deadlines, errors and raw reports are
unchanged. No simulated progress percentage is shown.

The top status is **Ready** when the API health check succeeds and the selected
analyzers' required tools are reported available by existing discovery. Otherwise
it is **Unavailable**. Health is rechecked every 15 seconds with a three-second
request bound. Tool names, exact versions and availability remain in Analyzer
Settings. Ready indicates service/tool availability, not validated checker
capabilities, complete coverage, or an error-free program.

Genuinely partial reports show the compact **Partial analysis — Some checks could
not complete.** link, which opens Execution. Failed/unavailable/timed-out reports
retain a separate failure link and exact underlying statuses. Execution includes
failure reasons and expandable raw execution evidence. The persistent coverage
footer has moved to Help/About under **Analysis limitations**:

> SmartParse checks your code without running it. Some errors may not be detected.

Use the Explorer icon in the left activity bar or **Ctrl+B** (Cmd+B on macOS) to
collapse/expand Explorer. Collapsing removes both its width and resize divider;
the narrow activity bar stays visible. Files, active buffers, example expansion,
cursor/scroll state, markers and reports are retained. Drag the Explorer divider,
or focus it and use Left/Right, to resize it (180–360 pixels, viewport permitting).
Previous width and visibility are kept in session storage; no source code is
stored there. Desktop visibility and the mobile drawer use separate preferences.
On narrow screens, Escape or choosing a file dismisses the drawer.

Optional real-browser regression, with existing local servers running:

```powershell
python -m smartparse_studio.ui_refinement_smoke --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

This checks actual analysis/loading and layout retention. Its offline check
intercepts a health request; it never stops the user's server. Partial/failure
display tests use explicit frontend fixtures and are not claimed as new live
static-analysis findings. Screenshots/logs remain in `.studio-artifacts/`.

## Install (Windows PowerShell)

Use Python 3.12 and Node.js 22.12+ (Node 24 was tested). Install GCC or Clang with
working target C headers for compiler-backed checks. No compiler is installed by
these commands. The original research parser works without a compiler.

From the repository root:

```powershell
python -m venv .studio-venv
.\.studio-venv\Scripts\python.exe -m pip install -r .\smartparse_studio\requirements-lock.txt
Set-Location studio
npm ci
Set-Location ..
.\.studio-venv\Scripts\python.exe -m smartparse_cli doctor
```

The lock file includes backend test dependencies. `requirements.txt` and
`requirements-dev.txt` describe the direct runtime/development requirements;
`requirements-lock.txt` pins the tested transitive environment. Frontend versions
are pinned in `package-lock.json`; the DOMPurify override supplies the patched
version used by Monaco. Neither install command changes global Python packages.

**Terminal 1, repository root:**

```powershell
.\.studio-venv\Scripts\python.exe -m uvicorn smartparse_studio.api.main:app --host 127.0.0.1 --port 8000
# Optional development reload, restricted to backend source:
# .\.studio-venv\Scripts\python.exe -m uvicorn smartparse_studio.api.main:app --reload --reload-dir smartparse_studio --host 127.0.0.1 --port 8000
```

**Terminal 2, repository root:**

```powershell
Set-Location studio
npm run dev
```

Open **http://127.0.0.1:5173**. Keep the default ports: the API explicitly permits
only the localhost/127.0.0.1 frontend on port 5173. Stop servers with Ctrl+C.
For a local production-bundle check, stop Vite dev, run `npm run build`, then
`npm run preview` on the same port. Preview still requires the separate API.
On POSIX, replace `.studio-venv\Scripts\python.exe` with `.studio-venv/bin/python`.

## Workflow and analyzers

Select one of eleven examples read directly from existing fixtures, write C, or
import a UTF-8 `.c` file. Imports never write back to disk. Settings select passes
and a C standard. Analyze or Ctrl+Enter submits one snapshot; typing does not run
analyzers. Editing a result's source hides stale markers and disables navigation.

| Selection | Existing implementation |
|---|---|
| Compiler diagnostics | GCC/Clang syntax, type errors and supported warnings |
| Clang Static Analyzer | Existing default path-sensitive checks |
| Memory & resources | Existing capability-probed Phase 6 memory profile |
| Semantic review | Existing semantic profile, including memory checks |
| GCC 14 analyzer | Optional existing version-constrained 14.2.0 profile |
| Cppcheck | Optional existing version-constrained 2.16.0 profile |
| SmartParse research / Panic baseline | Original restricted C-like grammars |

Tool availability is an actual version probe, cached for 30 seconds, and does
not certify checker availability. Each analysis performs the existing capability
checks. Missing tools and partial/blocked passes stay visible in Execution and
raw evidence; they are not converted into successful empty results.

Punctuation recovery and unaffected-region isolation are explicit opt-ins. The
Recovery inspector shows actual candidates, acceptance/rejection reasons,
eligibility changes, isolation exclusions, and existing research repair scores
when present. Candidate fix-it coordinates refer to the compiler's reported
snapshot; raw provenance retains original mappings. A read-only diff is shown
only if applying the engine's recorded edits/masking to the submitted bytes
reproduces the **accepted variant hash**. Preview reconstruction does not rerun
or invent repairs, and never changes the editor. Unverifiable previews are absent.

Diagnostic cards retain analyzer attribution, categories, conditioning, snippets,
IDs and raw evidence. Notes remain in the full report. Source mappings use
verified original UTF-8 byte mappings or unambiguous ASCII columns; tabs/unknown
Unicode conventions use line-only navigation. Foreign headers, unverified variant
locations and `#line` remapping are not projected onto the editor.

Comparison displays real passes, statuses, original/conditional record counts,
and the engine's conservative multi-analyzer groups. These are not adjudicated
unique-defect counts, accuracy metrics, or proof from analyzer agreement. A
completed process and zero findings never certify path coverage or bug freedom.

JSON export contains the whole response. Markdown uses the existing renderer's
summary and appends the complete unified report as JSON so raw records, IDs,
locations, groups, assumptions and conditioning remain available. Exports can
contain local compiler and temporary paths; review them before sharing.

## Architecture and API

React/Vite/TypeScript/Tailwind/Lucide render the workbench. Monaco and its C
language support/worker are bundled locally with no editor CDN. FastAPI validates
a request with Pydantic, writes a private temporary source/configuration, then
runs a bounded Python worker. That worker calls **`smartparse_cli.analyze`**;
diagnostics, grouping, detection and recovery come from the existing engine.

| Endpoint | Result |
|---|---|
| `GET /api/health` | Service availability, not compiler readiness |
| `GET /api/tools` | Existing doctor inventory, paths and versions |
| `GET /api/examples` | Actual fixture text, hashes and default settings |
| `POST /api/analyze` | Unified analysis plus thin Studio presentation wrapper |
| `GET /api/openapi.json` | Request schema (interactive API docs disabled) |

Example request (JSON content type and `X-SmartParse-Studio: 1` required):

```json
{"source":"int main(void) { return 0; }\n","filename":"example.c","analyzers":["compiler"],"recovery":false,"isolation":false,"standard":"c11"}
```

Response schema **`smartparse.studio_response` / `1.0`** contains:

- `report`: unchanged **`smartparse.unified_analysis` / `1.0`** object, including
  diagnostics, runs, groups, raw records, tool issues and provenance.
- `studio`: request ID, safe display filename, submitted SHA-256, conservative
  `editor_locations` indexed by diagnostic ID, hash-verified `previews`, verified
  `workspace_removed`, limits and presentation limitations.
- `markdown`: the existing engine's summary rendering.

HTTP 200 may contain source errors or partial analysis; inspect `report.status`
and each run. HTTP 403 means local-host/origin/header rejection; 408 body timeout;
413 oversized body; 415 wrong media type; 422 invalid input; 429 worker busy;
502 invalid/failed worker response or preservation failure; 503 startup/cleanup
failure; 504 worker deadline. Tool issues stay distinct from source diagnostics.

## Local security and limits

This is for **trusted local source**. Loopback IP/Host checks, exact CORS origins,
a required custom POST header and JSON content type limit browser-driven access.
No arbitrary executable path, compiler flags, include/output paths or filesystem
path is accepted through the API. Filenames reject traversal, drives and Windows
device names. Source is capped at 128 KiB UTF-8; the JSON body at 256 KiB and ten
seconds. Exactly one analysis is admitted per API process; other requests get 429.

The existing engine gets 45 seconds, five seconds per subprocess and 96 compiler
invocations; the containing worker has a 55-second deadline and process-tree
cleanup. Serialized reports over 16 MiB are rejected, never silently truncated.
These are time/count/size bounds, **not OS memory or filesystem isolation**.
Compilers and preprocessors can read local headers/files and run their own
trusted toolchain components. Temporary copies do not constitute a sandbox.
Do not bind/proxy this service publicly, use multiple worker processes to bypass
the concurrency limit, or submit untrusted hostile source. No authentication,
database or cloud service is provided.

Submitted C is never linked or executed. The existing GCC analyzer can produce a
private object file for analysis; it never runs it. Original files, baseline
diagnostics and conditional provenance remain separate. Stop waiting aborts the
browser request only: the server may finish its bounded run and reject another
request until then. No fabricated percentage or real-time compiler progress is
displayed.

## Testing and demonstration

```powershell
# Backend targeted tests (includes real Clang integration if installed):
.\.studio-venv\Scripts\python.exe -m unittest test_smartparse_studio -v
# Complete suite, supervised for 600 seconds, with legacy CSV restoration:
.\.studio-venv\Scripts\python.exe -m smartparse_studio.validate
Set-Location studio
npm test
npm run build
npm audit
Set-Location ..
```

The new validator writes `.studio-artifacts/regression/`; it verifies exact
pre/post bytes of tracked files and local acceptance evidence, restores existing
legacy-test CSV writes in `finally`, and reports missing/changed files as failures.
It does not refresh or replace Milestone 9's frozen release manifest. That older
manifest describes its historical release, not subsequently added Studio files.

Optional real-browser automation uses Playwright and an **already installed**
Chrome. Install the Python test client in a suitable environment (`python -m pip
install playwright`); do not download browsers if Chrome is already present.
Start both servers first, then:

```powershell
python -m smartparse_studio.browser_smoke --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

This checks valid/malformed/null-pointer examples, real Monaco markers/navigation,
accepted recovery diffs, isolation, research suggestions, multi-pass comparison,
actual JSON/Markdown downloads and a narrow viewport. Artifacts stay under
`.studio-artifacts/browser/`, separate from historical evaluation evidence.
Manual demonstration follows the same gallery sequence: Valid C → Null pointer
→ Missing semicolon → Recovery-assisted → Settings (add compiler) → Comparison
→ Export JSON. Scroll the Recovery inspector to see its accepted-source diff.

Known UI limits: one translation unit and UTF-8 imports only; no project/build
database editing; no live streaming or server cancellation endpoint; some
locations deliberately lack precise markers; previews require verifiable hashes;
Monaco's production bundle triggers a large-chunk warning. Browser testing here
uses Chrome on Windows; other browsers/platforms require separate validation.
Historical Milestone 10 validation records remain local, separate from release source.

## UI polish (Milestone 10.1)

Overview now uses a compact status/count/execution summary to leave more room
for code. On a 1366×768 laptop the default code viewport holds about 15 lines;
the measured 1920×1080 viewport holds 29. More room for analysis details trades
off against editor height. Resizing and changing inspector tabs keep the source
editor mounted.

- Drag the divider between editor and diagnostics, or focus it and use Left/Right.
- Drag the grip above the details panel, or focus it and use Up/Down.
- Home/End select the divider's limits. The reset icon restores default widths
  and the current tab's default details height. Recovery defaults to a larger
  details area than Overview.
- Recovery separates original syntax diagnostics, machine-range repair types,
  accepted/rejected candidate evidence, research suggestions, conditional
  findings and verified read-only comparisons. Raw repair suggestions and
  preview provenance can be expanded. Acceptance means a temporary analysis
  variant was accepted; the editor and original file remain unchanged.
- On narrow screens the panels stack. Page scrolling is intentional there;
  desktop views keep editor, diagnostics and details in their own working areas.

Run the extended real-browser regression against the running development servers:

```powershell
python -m smartparse_studio.browser_smoke --chrome "C:\Program Files\Google\Chrome\Application\chrome.exe" --polish --output .studio-artifacts/polish/browser
```

The optional `--polish` checks add pointer/keyboard resizing, editor state and
long-source scroll preservation, plus three desktop/laptop viewport measurements.
The long benchmark is imported without analyzing or modifying it in that check.
Historical Milestone 10.1 validation records remain local.
