# Set / Setting / Seed Dashboard Guide

Date: 2026-05-12

## Artifacts

PASS 2A writes:

- `results/setting_seed/dashboard/dashboard_payload.json`
- `results/setting_seed/dashboard/index.html`
- `results/setting_seed/dashboard/screenshots/pass2a_microsite.png`
- `output/doc/set_setting_seed_microsite.html`

The FastAPI dashboard now also exposes an optional `set_setting_seed` key in `/api/dashboard-data` when the payload exists.

## Local Build

```powershell
.venv\Scripts\python.exe scripts\run_setting_seed_pass2a.py
.venv\Scripts\python.exe scripts\build_setting_seed_dashboard.py
```

## Local Server

```powershell
.venv\Scripts\python.exe scripts\run_dashboard.py
```

Open:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html
```

For the unified live launcher, prefer:

```powershell
uv run python scripts/run_everything_live.py
```

That launcher starts at port `8020` by default to avoid common local `8000` conflicts, and prints the actual selected URLs.

## What PASS 2A Shows

- Rest-only data audit.
- Reliability tier table.
- Descriptive PCA latent geometry.
- Music-control scaffold with blocked status.
- Previous mechanism context as proxy-ranking artifacts.
- Guardrail badges:
  - Not clinical.
  - Not subjective decoding.
  - Not receptor proof.
  - Diffusion analogy only.

## What PASS 2A Does Not Show

- No run-02 empirical music effect.
- No motion sensitivity.
- No deep learning model.
- No new mechanism leaderboard.
- No clinical or subjective-experience claim.

## UI Security

The static microsite is served through the existing `/artifacts/` route under `output/doc`. For static HTML artifacts outside result figure directories, the existing server sends a CSP with `script-src 'none'` and `sandbox`.

The main dashboard page remains the interactive FastAPI/Jinja2/Plotly page at `/`.

## PASS 2A Smoke

Playwright MCP loaded the local static microsite route:

```text
http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html
```

The page title was `Set / Setting / Seed`, and a full-page screenshot was saved under `results/setting_seed/dashboard/screenshots/`.

## PASS 2B-0 Readiness Panels

PASS 2B-0 updates the static microsite and dashboard payload to separate readiness states:

- run-02 extraction support available,
- run-02 data present,
- run-02 analysis ready,
- motion-summary support available,
- motion files present,
- motion analysis ready.

The dashboard shows the exact command to run only after user approval:

```powershell
uv run python scripts/run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 --stage2-output-dir results/setting_seed/run02_extraction/stage_2_music
```

The dashboard also shows:

```powershell
uv run python scripts/run_setting_seed_motion_summary.py
```

Current status remains blocked:

- run-02 data present: false,
- run-02 analysis ready: false,
- motion data present: false,
- motion analysis ready: false.

PASS 2B-0 Playwright MCP smoke loaded:

```text
http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html
http://127.0.0.1:8000/
```

Results:

- static microsite title: `Set / Setting / Seed`,
- main dashboard title: `Whole-Brain Surrogate Dashboard`,
- local snapshots were recorded by Playwright MCP.

## 2026-05-14 Live Smoke

After rerunning the implemented safe workflow, the dashboard was verified locally at:

```text
http://127.0.0.1:8020/
http://127.0.0.1:8020/artifacts/output/doc/set_setting_seed_microsite.html
```

Results:

- main dashboard title: `Whole-Brain Surrogate Dashboard`,
- static microsite title: `Set / Setting / Seed`,
- Playwright screenshot: `results/setting_seed/dashboard/screenshots/set_setting_seed_live_8020.png`.
