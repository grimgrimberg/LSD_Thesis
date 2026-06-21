# Methods And Data-Skills Summary

## Project Engineering

The repo is a Python project managed with `uv`. It uses a conventional package layout under `src/lsd_thesis/`, documented commands in `README.md`, and validation with `pytest`, `ruff`, `mypy`, `uv pip check`, dashboard preflight, and JavaScript syntax checks.

The current documented engineering baseline is strong enough for PI review:

- `ruff` passed.
- `mypy src` passed on 109 source files.
- `pytest --collect-only` collected 82 tests.
- Latest documented full pytest baseline is 82 passed with 82.69% coverage.
- Dashboard strict preflight passed.
- `node --check src\lsd_thesis\static\dashboard.js` passed.

## Python And Testing Practices

Applied skills visible in the repo:

- Python package organization.
- Pydantic-style structured config/result models.
- Deterministic tests for simulation and payload contracts.
- Characterization tests for dashboard routes, public payloads, artifact schemas, and status vocabulary.
- Focused validation notes that distinguish current baseline from historical notes.
- Safe CLI contract testing for scripts without running heavy scientific workflows.

## Dashboarding And Reporting

The repo uses:

- FastAPI for local dashboard routes and API payloads.
- Jinja templates and static assets for dashboard rendering.
- Plotly/JavaScript for charts.
- Local artifact serving with allowlisted `/artifacts/...` hrefs.
- Static/public payload schema `public_site.v1`.
- Figure payloads that keep source artifacts, formulas, caveats, and claim status together.

This package did not modify dashboard routes, templates, CSS, JavaScript, or public JSON schemas.

## Artifact Contracts

The project uses JSON/YAML/CSV/XLSX artifacts as reviewable contracts. Examples include:

- `results/dynamic_mechanism_ranking/summary.json`
- `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`
- `results/stage_2/empirical_viewer/group_overview.json`
- `results/thesis_upgrade/thesis_upgrade_status.json`
- `results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json`
- `results/reproducible_archive/ARCHIVE_MANIFEST.json`

The dashboard and tests consume these artifacts, so they should not be casually regenerated or cleaned.

## Artifact Security And Href Allowlisting

The dashboard artifact layer uses allowlisted paths and extensions. Subject-level empirical cache files are local-only and are not exposed as public static artifacts. This matters because the project can share derived summaries without exposing raw/private/cache data.

## fMRI Summary Data Handling

The empirical workflow handles paired `ses-LSD` and `ses-PLCB` ds003059 records. The primary resting-state runs are run-01 and run-03. Run-02/music is explicitly gated.

Current empirical summary surfaces include:

- 15 paired subjects in the group overview.
- run-01 and run-03 as primary runs.
- LSD-minus-placebo deltas for macro-dynamic metrics.
- subject/run/window local viewer cache for inspection.
- caveats about missing strict motion/confound proof.

## Paired LSD/Placebo Evidence Handling

The empirical viewer and dynamic ranking use cached paired summaries rather than raw data regeneration in this package. The PI package derives compact tables from existing artifacts only.

Examples:

- `assets/data/empirical_group_metric_deltas.csv`
- `assets/data/mechanism_ranking_values.csv`
- `assets/data/robustness_summary_values.csv`

## Graph / Surrogate Model Design

The surrogate model is an 8-module stochastic graph model with:

- latent module states,
- adaptation,
- bistability/barrier-like terms,
- graph coupling,
- hierarchy constraints,
- stochastic perturbation,
- proxy metrics such as FC, switching rate, entropy-like diversity, metastability, and barrier proxies.

All of these are model-level proxies, not direct biological parameters.

## Mechanism Ranking A-E

The current mechanism ranking compares:

- A: transition-state proxies.
- B: DMDc predictive baseline / negative control.
- C: hierarchy/routing proxies.
- D: dynamic repertoire / graph metrics.
- E: finite-horizon network-control energy proxy.

The current order is C, E, D, A, B. E must remain split between lower transition/control-energy proxy support and unsupported receptor-specific placement.

## Robustness And Internal Validation

The project records:

- subject bootstrap summaries,
- run sensitivity,
- E horizon sensitivity,
- D window sensitivity,
- state-label sensitivity,
- claim verdicts,
- internal subject-disjoint CV5 status.

Internal robustness does not replace external validation or motion/confound proof.

## Prior-Art Mapping

The repo includes a ds003059 prior-art landscape with 12 analysis families. It records code status, dependencies, inputs, outputs, reproducibility status, runbooks, and claim boundaries.

The purpose is scholarly positioning and reproducibility context. Prior-art wrappers are not treated as original local evidence.

## Reproducibility Practices

Visible reproducibility practices include:

- source-path columns in derived tables,
- artifact manifests,
- archive checksums,
- validation baseline docs,
- explicit no-touch boundaries,
- prior-art repository commit hashes,
- status labels such as implemented, proxy-supported, mixed, unsupported, blocked, and future.

## Codex / Autoresearch Framing

Codex helped with codebase cleanup, tests, reporting, documentation, dashboard guardrails, and this review package. It did not replace scientific approval. Scientific claim promotion still requires PI review and matching evidence artifacts.
