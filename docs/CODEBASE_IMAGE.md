# Codebase Image

Date: 2026-06-23

## Executive Summary

This repository is a Python 3.13 + `uv` research software project with two
connected surfaces:

1. A transparent macro-dynamic surrogate model and A-E mechanism-proxy ranking
   workflow over cached psychedelic fMRI summaries.
2. A ds003059 prior-art reproducibility landscape used for claim boundaries,
   method comparison, and reviewer context.

The current defensible state is a PI-review-ready research-demo evidence
workbench, not a completed neuroscience thesis. Current generated thesis status
reports `4/6` strict completion gates complete and `1/2` package gates complete.
The missing strict requirements are the fMRIPrep FD/DVARS/censoring
motion-confound proof and the project-phase gate derived from that blocker. The
missing package requirement is the public reproducible archive DOI.

The current generated dynamic ranking artifact is based on cached ds003059
paired placebo/LSD empirical viewer records: 15 subjects, 30 paired subject/run
records, runs `run-01` and `run-03`. It ranks C first, followed by E, D, A, and
B. The ranking artifacts now preserve raw implementation status internally while
adding public claim-status labels for reports, exports, PI-review CSVs, and
dashboard-visible ranking rows.

## Evidence Basis

Local evidence checked in this pass:

- Branch: `audit/full-cleanup-and-prior-art`
- HEAD checkpoint before these docs: `1bab47ca0cb792c1cd714830f004a0ab3bbb07de`
- Remote: `origin https://github.com/grimgrimberg/LSD_Thesis.git`
- Worktree: large dirty tree with source, docs, generated PI package, result
  JSON, and untracked `CONTEXT.md`, `docs/audits/`, and `docs/specs/`
- Existing local docs read: `AGENTS.md`, `README.md`, `SPEC.md`,
  `ARCHITECTURE.md`, `CONTEXT.md`, `docs/SCIENTIFIC_GUARDRAILS.md`,
  `docs/THESIS_READINESS_GATES.md`, `docs/GITHUB_PAGES.md`,
  `docs/DASHBOARD_GUIDE.md`, `docs/audits/whole_project_roast_and_repair.md`,
  `docs/specs/whole_project_pi_review_repair_spec.md`,
  `prior_art/README.md`, and `prior_art/code_inventory.md`
- Local MCP/tool discovery found usable multi-agent, GitHub, Playwright, and
  Context7 tools. A Depwire file claim attempt failed because no project was
  loaded there.
- Requested skills used: `grill-with-docs` and
  `superpowers:using-superpowers`.

## Architecture Map

```text
configs/
  graphs, regimes, targets
        |
src/lsd_thesis/
  simulator, metrics, fit, perturbation, ablation
  dynamic_mechanism, dynamic_robustness
  data/ds003059, data/ds006072, parcellations
  thesis_loop, thesis_upgrade, reproducible_archive
  web FastAPI app, payload builders, templates, static assets
        |
scripts/
  run_pipeline.py
  run_dynamic_mechanism_ranking.py
  export_*_tables.py
  build_*_status.py
  build_github_pages.py
  run_dashboard.py
        |
results/
  cached generated summaries, status JSON, exports, figures
        |
docs/
  stage reports, guardrails, PI package, Pages guidance, prior-art maps
        |
FastAPI dashboard and static GitHub Pages build
```

Primary local runtime:

- `scripts/run_dashboard.py` serves `lsd_thesis.web.app:app` at
  `http://127.0.0.1:8000/`.
- `src/lsd_thesis/web/app.py` defines routes for overview, ranking, submission,
  robustness, prior art, empirical viewer, simulator, thesis, figures, dashboard
  aliases, guarded artifact serving, and JSON APIs.
- `scripts/build_github_pages.py` regenerates the static site in `_site/`.
  It also refreshes multiple evidence-loop, motion, archive, thesis-upgrade,
  publication-package, and static-dashboard artifacts before copying the
  PI-review package.

## Data And Result Flow

Primary empirical anchor:

- OpenNeuro `ds003059` v1.0.0.
- Current public ranking uses cached rest records, not raw-data download in this
  pass.
- Current primary ranking excludes run-02/music. Music remains gated.

Main generated result routes:

- `results/stage_2/empirical_viewer/` supplies cached subject/run empirical
  viewer records.
- `scripts/run_dynamic_mechanism_ranking.py` reads those records and writes
  `results/dynamic_mechanism_ranking/summary.json`, CSV tables, Plotly HTML
  figures, robustness JSON/CSVs, and
  `docs/stage_reports/dynamic_mechanism_ranking.md`.
- `scripts/export_dynamic_mechanism_tables.py` creates workbook/table exports.
- `scripts/build_github_pages.py` copies curated artifacts into `_site/` and
  generates static dashboard JSON and pages.

Current generated ranking snapshot:

| Field | Current value |
| --- | --- |
| Generated at | `2026-06-22T14:01:09.941091+03:00` |
| Dataset scope | cached ds003059 paired placebo/LSD empirical viewer records |
| Pair count | 30 |
| Subject count | 15 |
| Runs | `run-01`, `run-03` |
| Current top layer | C |
| C score | 0.3326057058836129 |
| C raw status | `implemented_first_pass` |
| C public status | `proxy-supported` |

Robustness snapshot:

| Layer | Rank-1 fraction | Median rank | Interpretation |
| --- | ---: | ---: | --- |
| A | 0.078125 | 3 | mixed/state-label dependent |
| B | 0 | 5 | negative baseline |
| C | 0.6015625 | 1 | leading current macro-dynamic proxy, motion-gated |
| D | 0.01953125 | 3 | supportive but window-sensitive |
| E | 0.30078125 | 2 | E1 supported, E2 receptor placement unsupported |

## Dashboard And Site Status

Local FastAPI dashboard:

- Source: `src/lsd_thesis/web/app.py`,
  `src/lsd_thesis/templates/pages/*.html`,
  `src/lsd_thesis/static/dashboard.css`, and
  `src/lsd_thesis/static/dashboard.js`.
- Command: `uv run python scripts/run_dashboard.py`.
- Preflight command checked in this pass:
  `uv run python scripts/preview_dashboard.py --check-only --strict`.
- Preflight result: passed. Required app/config files and optional generated
  artifacts were present. Subject-disjoint held-out validation was reported as
  completed CV5 internal validation, not external validation.

Static GitHub Pages:

- Source/build script: `scripts/build_github_pages.py`.
- Local build command:
  `uv run python scripts/build_github_pages.py --repo-root D:\LSD_Thesis --site-dir D:\LSD_Thesis\_site`.
- Expected local routes after serving `_site/`:
  `http://127.0.0.1:8766/pi-review/`,
  `http://127.0.0.1:8766/dashboard/`, and
  `http://127.0.0.1:8766/pi-review/pages/evidence-and-calculations.html`.
- Public guidance says GitHub Pages is a presentation artifact and does not
  complete the citable archive gate.
- Existing workflow `.github/workflows/pages.yml` uses GitHub Pages Actions and
  is manual (`workflow_dispatch`).

PI-review package:

- Source:
  `docs/reports/pi_thesis_share_package/deliverable_website/`.
- The canonical first read should be `/pi-review/`.
- The package currently includes data CSVs, downloads, screenshots, figure pages,
  decision-gate pages, claim-ledger pages, and an email body.

## Dependency, CI, And Verification Status

Package model:

- `pyproject.toml` with Hatchling build backend.
- Python requirement: `>=3.13`.
- Runtime dependencies include FastAPI, Plotly, Jinja2, NumPy, SciPy, pandas,
  scikit-learn, nilearn, nibabel, networkx, Typer, Pydantic, neuromaps, and
  brainspace.
- Dev dependencies include pytest, pytest-cov, ruff, and mypy.

CI:

- `.github/workflows/ci.yml` runs on pull requests and pushes to `main` and
  `codex/**`.
- CI steps: checkout, Python 3.13, install `uv`, `uv sync --frozen --extra dev`,
  `uv pip check`, `uv run ruff check .`, `uv run mypy src`,
  `uv run pytest`, and dashboard preflight.
- Current branch `audit/full-cleanup-and-prior-art` will not trigger the push
  workflow by branch pattern, but a PR should trigger CI.

Local checks in this pass:

| Check | Result |
| --- | --- |
| `uv run python scripts/preview_dashboard.py --check-only --strict` | Passed |
| `node --check src\lsd_thesis\static\dashboard.js` | Passed, no output |
| `uv run pytest tests/test_web_security.py tests/test_result_artifact_schema_contract.py tests/test_next_action_evidence_gates.py tests/test_dashboard_redesign_contract.py -q -o addopts=` | Passed, 28 tests |
| `uv run pytest --collect-only -q -o addopts= -p no:cacheprovider tests` | Passed, 87 tests collected |
| `uv run pytest -q` | Passed, 87 tests |
| `uv run python scripts\build_github_pages.py --repo-root D:\LSD_Thesis --site-dir D:\LSD_Thesis\_site` | Completed after the initial 5-minute guard expired; rebuilt `_site/` |
| Public-status search over PI-review/site report surfaces | No stale raw implementation-status or stale full-suite phrases found |

## Risk Register

| Priority | Risk | Evidence | Required handling |
| --- | --- | --- | --- |
| Critical | Motion/confound proof is incomplete | Thesis status misses `motion_confound_control_result`; docs require FD/DVARS/censoring proof | Keep blocker first-visible; do not promote C beyond proxy-supported |
| Critical | Public label mismatch | Raw implementation statuses remain in internal JSON/source fields but public reports, PI CSVs, and visible dashboard ranking rows now use controlled labels | Keep raw fields internal or explicitly raw; continue using public-status mapping for public prose/tables |
| Critical | Archive DOI missing | Archive manifest has release URL but no DOI and null publication metadata fields | Keep GitHub release and Zenodo DOI gates separate |
| High | Full pytest collection can be slow | Initial collect-only timed out after 120 seconds, but cache-disabled collection later passed with 87 tests in 36.87s | Keep the faster collection probe documented and avoid short guards |
| High | Build script has broad side effects | `build_github_pages.py` refreshes many result/status artifacts before writing `_site` | Review diff before staging and never hand-edit `_site` |
| High | Worktree is already dirty | 100+ modified files plus untracked context/audit/spec docs | Preserve existing changes; stage only intentional coherent sets |
| Medium | Branch naming and CI trigger mismatch | Current branch is not `codex/**` | Use PR CI or create a `codex/` branch before final push if needed |
| Medium | Prior-art wrappers can be overread | Prior-art docs explicitly separate public/partial/unavailable/author-only code | Keep prior-art as reproducibility landscape, not original analysis |
| Medium | External validation wording can overclaim | ds006072 is described as mixed/negative stress test | Say cross-dataset stress test unless strict comparability is proved |

## Unknowns And Immediate Blockers

- Whether all existing dirty changes are intended for the current repair pass.
- Whether GitHub credentials and repository permissions allow push/PR creation
  from this environment.
- Whether a Zenodo DOI has been minted outside the local manifest.
- Whether authorized fMRIPrep or author-provided confounds exist outside the
  repository; none were found or used in this pass.

## Recommended Production Path

1. Finish the phase-gate docs: this file and
   `docs/AUDIT_AND_PRODUCTION_PLAN.md`.
2. Run bounded audit tracks against architecture/code quality,
   scientific/reproducibility validity, dashboard/UX, tests/CI, security/secrets,
   and academic submission docs.
3. Patch only the highest-value public-facing mismatch first: normalize public
   claim-status labels while preserving raw implementation status where it is
   machine-state metadata.
4. Regenerate dynamic ranking exports and the static site from source scripts,
   not by hand-editing generated pages.
5. Re-run focused tests, dashboard preflight, static route checks, and legacy
   label searches.
6. Stage a coherent set after diff review, commit, and push through a PR path
   that triggers CI. If credentials or branch policy block push/PR creation,
   record the exact blocker and exact owner commands.
