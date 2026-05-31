# Dashboard Thesis Site Scratch Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the cluttered public dashboard/thesis site with a clean multi-route static site: PI pitch homepage first, thesis story second, evidence dashboard third, methods/reproducibility fourth, appendix fifth.

**Architecture:** Keep the validated scientific data and artifact-generation pipeline, but introduce a compact presentation adapter and new static templates instead of continuing to grow the old monolithic dashboard. GitHub Pages root becomes a clear PI pitch homepage; the data-science dashboard is a separate evidence route with only four to six primary panels and expandable appendix depth.

**Tech Stack:** Python 3.13, FastAPI/Jinja-style static templates, vanilla HTML/CSS/JS, Plotly for limited evidence charts, pytest, Node `--check` for inline JavaScript syntax, GitHub Pages static publish.

---

## Backup Baseline

Rollback branches already exist:

- `backup/dashboard-before-scratch-rewrite-20260531-104146-source`
- `backup/dashboard-before-scratch-rewrite-20260531-104146-gh-pages`

Do not delete these branches during implementation.

## File Structure

Create:

- `src/lsd_thesis/web/site_payload.py`
  - Compact presentation adapter built from existing dashboard payload and thesis-upgrade status.
- `src/lsd_thesis/templates/public_site.html`
  - PI pitch homepage and main GitHub Pages root.
- `src/lsd_thesis/templates/thesis_story.html`
  - Narrative thesis idea page.
- `src/lsd_thesis/templates/evidence_dashboard.html`
  - Clean evidence dashboard with claim ladder, mechanism ranking, validation, confounds, negative controls, artifact search.
- `src/lsd_thesis/templates/methods_reproducibility.html`
  - Pipeline, commands, provenance, reproducibility boundary.
- `src/lsd_thesis/templates/appendix.html`
  - Dense artifact browser and preserved detailed links.
- `tests/test_public_site_payload.py`
  - Unit tests for compact adapter.
- `tests/test_public_site_templates.py`
  - Template contract and JS syntax tests.

Modify:

- `scripts/build_github_pages.py`
  - Build new route structure and publish compact JSON.
- `src/lsd_thesis/web/app.py`
  - Add local FastAPI routes for new templates while preserving existing API/data routes.
- `tests/test_github_pages.py`
  - Update static Pages contract.
- `tests/test_web.py`
  - Stop treating the old monolithic dashboard as the primary public UX.

Avoid:

- Do not rewrite scientific result-generation modules.
- Do not delete the old `src/lsd_thesis/templates/dashboard.html` until the new routes are verified and the appendix route links the preserved detailed material.

---

## Task 1: Compact Site Payload Adapter

**Files:**
- Create: `src/lsd_thesis/web/site_payload.py`
- Test: `tests/test_public_site_payload.py`

- [ ] **Step 1: Write failing payload adapter tests**

Create `tests/test_public_site_payload.py` with:

```python
from __future__ import annotations

from lsd_thesis.web.site_payload import build_public_site_payload


def test_public_site_payload_has_pitch_claims_and_routes() -> None:
    payload = build_public_site_payload()

    assert payload["homepage"]["headline"] == "AI tools for explaining psychedelic brain dynamics"
    assert "altered transition dynamics" in payload["homepage"]["thesis_claim"]
    assert {route["id"] for route in payload["routes"]} == {
        "home",
        "thesis",
        "dashboard",
        "methods",
        "appendix",
        "repo",
    }
    assert payload["claim_ladder"]["strict_complete"] == 6
    assert payload["claim_ladder"]["strict_total"] == 6
    assert len(payload["claim_ladder"]["requirements"]) == 6


def test_public_site_payload_separates_pitch_dashboard_and_appendix() -> None:
    payload = build_public_site_payload()

    assert payload["homepage"]["primary_cta"]["href"] == "thesis.html"
    assert payload["homepage"]["secondary_cta"]["href"] == "dashboard/"
    assert len(payload["dashboard"]["primary_panels"]) <= 6
    assert any(panel["id"] == "mechanism-ranking" for panel in payload["dashboard"]["primary_panels"])
    assert any(panel["id"] == "confounds" for panel in payload["dashboard"]["primary_panels"])
    assert len(payload["appendix"]["artifact_links"]) >= 8
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-public-site tests/test_public_site_payload.py
```

Expected:

- FAIL with `ModuleNotFoundError: No module named 'lsd_thesis.web.site_payload'`.

- [ ] **Step 3: Implement minimal payload adapter**

Create `src/lsd_thesis/web/site_payload.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from lsd_thesis.web.app import REPO_ROOT, build_dashboard_payload


def _artifact_links(dashboard: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    artifact_links = dashboard.get("artifact_links", {})
    if isinstance(artifact_links, dict):
        for kind, items in artifact_links.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and item.get("href") and item.get("label"):
                    links.append(
                        {
                            "kind": str(kind),
                            "label": str(item["label"]),
                            "href": str(item["href"]).replace("/artifacts/", "artifacts/"),
                        }
                    )
    return links


def build_public_site_payload(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    dashboard = build_dashboard_payload(repo_root)
    thesis_upgrade = dashboard.get("thesis_upgrade", {})
    summary = thesis_upgrade.get("readiness_summary", {}) if isinstance(thesis_upgrade, dict) else {}
    requirements = thesis_upgrade.get("strict_completion_requirements", []) if isinstance(thesis_upgrade, dict) else []
    artifacts = _artifact_links(dashboard)

    return {
        "homepage": {
            "headline": "AI tools for explaining psychedelic brain dynamics",
            "subheadline": (
                "A data-science thesis project combining interpretable ML, control-inspired dynamics, "
                "perception, and psychedelic fMRI."
            ),
            "thesis_claim": (
                "This project tests whether LSD-like empirical macro-dynamics are better explained by "
                "altered transition dynamics than by generic noise, motion, or static-connectivity changes."
            ),
            "primary_cta": {"label": "Read the thesis idea", "href": "thesis.html"},
            "secondary_cta": {"label": "Open evidence dashboard", "href": "dashboard/"},
        },
        "routes": [
            {"id": "home", "label": "PI Pitch", "href": "index.html"},
            {"id": "thesis", "label": "Thesis Story", "href": "thesis.html"},
            {"id": "dashboard", "label": "Evidence Dashboard", "href": "dashboard/"},
            {"id": "methods", "label": "Methods", "href": "methods.html"},
            {"id": "appendix", "label": "Appendix", "href": "appendix.html"},
            {"id": "repo", "label": "GitHub", "href": "https://github.com/grimgrimberg/LSD_Thesis"},
        ],
        "claim_ladder": {
            "strict_complete": int(summary.get("strict_complete_gates") or 0),
            "strict_total": int(summary.get("strict_total_gates") or len(requirements)),
            "thesis_status": str(summary.get("thesis_status") or summary.get("completion_status") or "unknown"),
            "requirements": requirements,
        },
        "dashboard": {
            "primary_panels": [
                {"id": "claim-ladder", "label": "Claim ladder"},
                {"id": "mechanism-ranking", "label": "Mechanism ranking"},
                {"id": "validation", "label": "Validation gates"},
                {"id": "confounds", "label": "Motion and confounds"},
                {"id": "negative-controls", "label": "Negative controls"},
                {"id": "artifacts", "label": "Artifacts"},
            ],
            "dynamic_mechanism": dashboard.get("dynamic_mechanism", {}),
            "thesis_upgrade": thesis_upgrade,
        },
        "methods": {
            "commands": [
                ".\\.venv\\Scripts\\python.exe -m pytest -o addopts= tests/test_github_pages.py tests/test_web.py",
                ".\\.venv\\Scripts\\python.exe scripts\\build_github_pages.py",
                ".\\.venv\\Scripts\\python.exe scripts\\run_dashboard.py",
            ],
            "reproducibility_boundary": (
                "GitHub Pages publishes derived/static artifacts. Raw OpenNeuro data is cited and not bundled."
            ),
        },
        "appendix": {"artifact_links": artifacts},
    }
```

- [ ] **Step 4: Run tests to verify adapter passes**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-public-site tests/test_public_site_payload.py
```

Expected:

- PASS.

- [ ] **Step 5: Commit adapter**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis add src/lsd_thesis/web/site_payload.py tests/test_public_site_payload.py
git -c safe.directory=D:/LSD_Thesis commit -m "Add compact public site payload"
```

---

## Task 2: New Public Templates

**Files:**
- Create: `src/lsd_thesis/templates/public_site.html`
- Create: `src/lsd_thesis/templates/thesis_story.html`
- Create: `src/lsd_thesis/templates/evidence_dashboard.html`
- Create: `src/lsd_thesis/templates/methods_reproducibility.html`
- Create: `src/lsd_thesis/templates/appendix.html`
- Test: `tests/test_public_site_templates.py`

- [ ] **Step 1: Write failing template contract tests**

Create `tests/test_public_site_templates.py`:

```python
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "src" / "lsd_thesis" / "templates"


def _template(name: str) -> str:
    return (TEMPLATE_ROOT / name).read_text(encoding="utf-8")


def test_public_site_templates_have_clean_route_contract() -> None:
    homepage = _template("public_site.html")
    thesis = _template("thesis_story.html")
    dashboard = _template("evidence_dashboard.html")
    methods = _template("methods_reproducibility.html")
    appendix = _template("appendix.html")

    assert "AI tools for explaining psychedelic brain dynamics" in homepage
    assert "Read the thesis idea" in homepage
    assert "Open evidence dashboard" in homepage
    assert "What I need from a lab" in homepage
    assert "Thesis Story" in thesis
    assert "What this does not claim" in thesis
    assert "Evidence Dashboard" in dashboard
    assert "Mechanism ranking" in dashboard
    assert "Motion and confounds" in dashboard
    assert "Methods / Reproducibility" in methods
    assert "GitHub Pages publishes derived/static artifacts" in methods
    assert "Appendix" in appendix
    assert "Artifact Browser" in appendix


def test_new_templates_do_not_recreate_monolithic_dashboard() -> None:
    homepage = _template("public_site.html")
    dashboard = _template("evidence_dashboard.html")

    assert homepage.count("<section") <= 8
    assert dashboard.count("plot-shell") <= 4
    assert "subject-level fMRI previews require the local FastAPI dashboard" not in homepage
    assert "Empirical/fMRI Explorer: Subject Module Traces" not in dashboard


def test_evidence_dashboard_javascript_syntax(tmp_path: Path) -> None:
    html = _template("evidence_dashboard.html")
    script_start = html.index("<script>") + len("<script>")
    script_end = html.rindex("</script>")
    script_path = tmp_path / "evidence_dashboard.js"
    script_path.write_text(html[script_start:script_end], encoding="utf-8")
    result = subprocess.run(["node", "--check", str(script_path)], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-public-site tests/test_public_site_templates.py
```

Expected:

- FAIL because templates do not exist.

- [ ] **Step 3: Create homepage template**

Create `src/lsd_thesis/templates/public_site.html` with:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI tools for explaining psychedelic brain dynamics</title>
  <link rel="stylesheet" href="site.css" />
</head>
<body data-route="home">
  <header class="site-header">
    <a class="brand" href="index.html">LSD Thesis</a>
    <nav aria-label="Primary">
      <a href="thesis.html">Thesis Story</a>
      <a href="dashboard/">Evidence Dashboard</a>
      <a href="methods.html">Methods</a>
      <a href="appendix.html">Appendix</a>
    </nav>
  </header>
  <main>
    <section class="hero">
      <p class="eyebrow">AI + engineering + perception + psychedelic fMRI</p>
      <h1>AI tools for explaining psychedelic brain dynamics</h1>
      <p class="lede">
        A data-science thesis project that tests whether psychedelic fMRI changes are better
        described as altered transition dynamics than generic noise, motion, or static-connectivity differences.
      </p>
      <div class="actions">
        <a class="button primary" href="thesis.html">Read the thesis idea</a>
        <a class="button" href="dashboard/">Open evidence dashboard</a>
      </div>
    </section>
    <section class="proof-grid" aria-label="Project proof points">
      <article><h2>Data</h2><p>Uses ds003059 LSD/placebo as the empirical anchor and ds006072 psilocybin as an external stress-test layer.</p></article>
      <article><h2>Models</h2><p>Ranks interpretable mechanism families with control-inspired and graph-dynamic features.</p></article>
      <article><h2>Validation</h2><p>Surfaces subject-disjoint validation, motion/QC sensitivity, spatial nulls, and negative controls.</p></article>
    </section>
    <section>
      <h2>What I need from a lab</h2>
      <p>Neuroscience supervision, stronger biological priors, better external validation, and help turning a rigorous data-science prototype into a master's thesis.</p>
    </section>
  </main>
</body>
</html>
```

- [ ] **Step 4: Create thesis, dashboard, methods, appendix templates**

Use the route responsibilities from the spec. Keep each page readable and short. The evidence dashboard should load `dashboard-data.json` and render claim cards plus artifact search with vanilla JavaScript.

- [ ] **Step 5: Run template tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-public-site tests/test_public_site_templates.py
```

Expected:

- PASS.

- [ ] **Step 6: Commit templates**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis add src/lsd_thesis/templates/public_site.html src/lsd_thesis/templates/thesis_story.html src/lsd_thesis/templates/evidence_dashboard.html src/lsd_thesis/templates/methods_reproducibility.html src/lsd_thesis/templates/appendix.html tests/test_public_site_templates.py
git -c safe.directory=D:/LSD_Thesis commit -m "Add scratch public thesis site templates"
```

---

## Task 3: Static Pages Builder Rewrite

**Files:**
- Modify: `scripts/build_github_pages.py`
- Modify: `tests/test_github_pages.py`

- [ ] **Step 1: Write failing static contract test**

Update `tests/test_github_pages.py` so the main test asserts:

```python
assert (tmp_path / "_site" / "index.html").exists()
assert (tmp_path / "_site" / "thesis.html").exists()
assert (tmp_path / "_site" / "dashboard" / "index.html").exists()
assert (tmp_path / "_site" / "methods.html").exists()
assert (tmp_path / "_site" / "appendix.html").exists()
assert (tmp_path / "_site" / "dashboard" / "dashboard-data.json").exists()

index_html = (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
dashboard_html = (tmp_path / "_site" / "dashboard" / "index.html").read_text(encoding="utf-8")
assert "AI tools for explaining psychedelic brain dynamics" in index_html
assert "Evidence Dashboard" in dashboard_html
assert "Empirical/fMRI Explorer: Subject Module Traces" not in dashboard_html

manifest = json.loads((tmp_path / "_site" / "pages_manifest.json").read_text(encoding="utf-8"))
assert manifest["entrypoints"] == {
    "index": "index.html",
    "thesis": "thesis.html",
    "dashboard": "dashboard/index.html",
    "methods": "methods.html",
    "appendix": "appendix.html",
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-pages tests/test_github_pages.py
```

Expected:

- FAIL because methods/appendix/new templates are not yet wired.

- [ ] **Step 3: Modify builder**

In `scripts/build_github_pages.py`:

- Import `build_public_site_payload`.
- Render/copy:
  - `public_site.html` to `_site/index.html`
  - `thesis_story.html` to `_site/thesis.html`
  - `evidence_dashboard.html` to `_site/dashboard/index.html`
  - `methods_reproducibility.html` to `_site/methods.html`
  - `appendix.html` to `_site/appendix.html`
- Write compact JSON to `_site/dashboard/dashboard-data.json`.
- Keep Plotly asset at `_site/dashboard/assets/plotly.min.js`.
- Keep artifact copying.
- Update manifest entrypoints.

Expected implementation shape:

```python
from lsd_thesis.web.site_payload import build_public_site_payload


def _write_template(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_with_static_favicon(source.read_text(encoding="utf-8")), encoding="utf-8")
    return destination
```

- [ ] **Step 4: Run static builder tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-pages tests/test_github_pages.py
```

Expected:

- PASS.

- [ ] **Step 5: Commit builder**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis add scripts/build_github_pages.py tests/test_github_pages.py
git -c safe.directory=D:/LSD_Thesis commit -m "Build scratch public thesis site routes"
```

---

## Task 4: Local FastAPI Route Parity

**Files:**
- Modify: `src/lsd_thesis/web/app.py`
- Modify: `tests/test_web.py`

- [ ] **Step 1: Write failing route tests**

Add to `tests/test_web.py`:

```python
def test_public_site_routes_render_clean_pages() -> None:
    from fastapi.testclient import TestClient
    from lsd_thesis.web.app import create_app

    client = TestClient(create_app())
    routes = {
        "/": "AI tools for explaining psychedelic brain dynamics",
        "/thesis": "Thesis Story",
        "/dashboard": "Evidence Dashboard",
        "/methods": "Methods / Reproducibility",
        "/appendix": "Artifact Browser",
    }
    for route, expected in routes.items():
        response = client.get(route)
        assert response.status_code == 200
        assert expected in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-web tests/test_web.py::test_public_site_routes_render_clean_pages
```

Expected:

- FAIL because new routes are not present.

- [ ] **Step 3: Add local routes**

In `src/lsd_thesis/web/app.py`, update `create_app()`:

```python
def _template_response(name: str) -> HTMLResponse:
    html = (REPO_ROOT / "src" / "lsd_thesis" / "templates" / name).read_text(encoding="utf-8")
    return HTMLResponse(html, headers=_dashboard_security_headers())


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return _template_response("public_site.html")


@app.get("/thesis", response_class=HTMLResponse)
async def thesis() -> HTMLResponse:
    return _template_response("thesis_story.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    return _template_response("evidence_dashboard.html")


@app.get("/methods", response_class=HTMLResponse)
async def methods() -> HTMLResponse:
    return _template_response("methods_reproducibility.html")


@app.get("/appendix", response_class=HTMLResponse)
async def appendix() -> HTMLResponse:
    return _template_response("appendix.html")
```

Keep `/api/dashboard-data`, `/api/empirical-view`, and `/api/simulate` available for local interactive use.

- [ ] **Step 4: Run route tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-web tests/test_web.py::test_public_site_routes_render_clean_pages
```

Expected:

- PASS.

- [ ] **Step 5: Commit routes**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis add src/lsd_thesis/web/app.py tests/test_web.py
git -c safe.directory=D:/LSD_Thesis commit -m "Serve scratch public thesis routes locally"
```

---

## Task 5: End-to-End Static Build and Browser Verification

**Files:**
- Modify if needed: template/build files from previous tasks.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider --basetemp tmp\pytest-public-site tests/test_public_site_payload.py tests/test_public_site_templates.py tests/test_github_pages.py tests/test_web.py
```

Expected:

- PASS.

- [ ] **Step 2: Rebuild static Pages**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\build_github_pages.py
```

Expected:

- `_site/index.html`
- `_site/thesis.html`
- `_site/dashboard/index.html`
- `_site/methods.html`
- `_site/appendix.html`
- `_site/dashboard/dashboard-data.json`
- `_site/pages_manifest.json`

- [ ] **Step 3: Serve static site locally**

Run:

```powershell
.\.venv\Scripts\python.exe -m http.server 8787 --directory _site
```

Expected:

- `http://127.0.0.1:8787/` opens the PI pitch homepage.
- `http://127.0.0.1:8787/dashboard/` opens the clean evidence dashboard.

- [ ] **Step 4: Browser verify**

Use Playwright/browser tool to verify:

```javascript
({
  title: document.title,
  homepageHeadline: !!document.body.textContent.includes("AI tools for explaining psychedelic brain dynamics"),
  routes: [...document.querySelectorAll("a")].map(a => a.getAttribute("href")).filter(Boolean)
})
```

Expected:

- Homepage title matches PI pitch.
- Routes include `thesis.html`, `dashboard/`, `methods.html`, and `appendix.html`.

- [ ] **Step 5: Commit any verification fixes**

Only if browser verification finds needed source changes:

```powershell
git -c safe.directory=D:/LSD_Thesis add src scripts tests
git -c safe.directory=D:/LSD_Thesis commit -m "Polish scratch public site verification"
```

---

## Task 6: Publish Source and GitHub Pages

**Files:**
- Source branch commit history.
- `.deploy-gh-pages` worktree.

- [ ] **Step 1: Push source branch**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis push origin codex/thesis-evidence-pages
```

Expected:

- Remote branch updates.

- [ ] **Step 2: Mirror `_site` to gh-pages worktree**

Run:

```powershell
$src=(Resolve-Path _site).Path
$dst=(Resolve-Path .deploy-gh-pages).Path
$repo=(Resolve-Path .).Path
if (-not $dst.StartsWith($repo)) { throw "Refusing to mirror outside repo: $dst" }
robocopy $src $dst /MIR /XD .git /XF .git .nojekyll /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -le 7) { exit 0 } else { exit $LASTEXITCODE }
```

Expected:

- `.deploy-gh-pages/index.html` is the PI pitch homepage.
- `.deploy-gh-pages/dashboard/index.html` is the evidence dashboard.

- [ ] **Step 3: Commit Pages snapshot**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis -c safe.directory=D:/LSD_Thesis/.deploy-gh-pages -C .deploy-gh-pages add -A
git -c safe.directory=D:/LSD_Thesis -c safe.directory=D:/LSD_Thesis/.deploy-gh-pages -C .deploy-gh-pages commit -m "Publish scratch public thesis site"
```

Expected:

- New `gh-pages` commit.

- [ ] **Step 4: Push Pages**

Run:

```powershell
git -c safe.directory=D:/LSD_Thesis -c safe.directory=D:/LSD_Thesis/.deploy-gh-pages -C .deploy-gh-pages push origin gh-pages
```

Expected:

- `gh-pages` remote updates.

- [ ] **Step 5: Live verify**

Use no-cache request:

```powershell
.\.venv\Scripts\python.exe -c "import urllib.request, time; url='https://grimgrimberg.github.io/LSD_Thesis/?v=scratch-'+str(int(time.time())); data=urllib.request.urlopen(url, timeout=60).read().decode('utf-8', errors='replace'); print({'pitch':'AI tools for explaining psychedelic brain dynamics' in data, 'old_dashboard':'Empirical/fMRI Explorer: Subject Module Traces' in data[:5000], 'dashboard_link':'dashboard/' in data})"
```

Expected:

- `pitch` is `True`.
- `old_dashboard` is `False`.
- `dashboard_link` is `True`.

---

## Completion Criteria

The scratch redesign is complete only when all are true:

- Remote backup branches still exist.
- Source branch is pushed.
- `gh-pages` is pushed.
- Live GitHub Pages root is the PI pitch homepage.
- Evidence dashboard is a secondary route.
- Thesis story, methods, and appendix routes exist.
- Focused tests pass.
- Browser/no-cache live verification proves the new root is not the old cluttered dashboard or old thesis microsite.

## Execution Recommendation

Use inline execution for this repo because the work touches tightly coupled templates, static builder contracts, and tests. Commit after each task.
