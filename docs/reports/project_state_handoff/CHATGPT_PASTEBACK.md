# LSD Thesis Current-State Pasteback

## 1. Project Snapshot

Repo: `D:\LSD_Thesis`

Snapshot date: 2026-06-17

Branch: `audit/full-cleanup-and-prior-art`

Commit: `69b0397a64fb7ec6f5b19cc07f00565cec97c53b`

Initial git status was clean. This handoff package is report-only and should be the only untracked path afterward: `docs/reports/project_state_handoff/`.

## 2. What The Project Does

The repo builds a transparent 8-module stochastic graph surrogate model for altered-state-inspired macro-dynamics and compares it with cached paired LSD/placebo ds003059 fMRI summary evidence. It also maintains a structured ds003059 prior-art reproducibility landscape. The safe framing is mechanism ranking over model-level proxies, not receptor-level realism, subjective-experience simulation, biological ground truth, clinical validation, or original prior-art reanalysis.

## 3. Current Validation State

Latest documented full baseline in `docs/VALIDATION.md`:

- Date: 2026-06-17
- `ruff`: passed
- `mypy src`: passed, 109 source files
- `pytest --collect-only`: 82 tests collected
- Full `pytest`: 82 passed, 82.69% coverage
- `uv pip check`: passed
- Dashboard strict preflight: passed
- `node --check src\lsd_thesis\static\dashboard.js`: passed

Checks rerun for this handoff:

- `uv run --frozen pytest --collect-only -q -o addopts=`: passed, 82 tests collected
- `uv run --frozen ruff check .`: passed
- `uv run --frozen mypy src`: passed, 109 source files
- `uv pip check`: passed, 76 packages compatible
- `uv run --frozen python scripts\preview_dashboard.py --check-only --strict`: passed
- `node --check src\lsd_thesis\static\dashboard.js`: passed

Full pytest was not rerun in this handoff; use the documented baseline above.

## 4. Architecture Summary

Main areas:

- `src/lsd_thesis/`: core Python package.
- `src/lsd_thesis/dynamic_mechanism/`: A-E mechanism ranking.
- `src/lsd_thesis/thesis_upgrade/`: thesis readiness gates and strict/package requirements.
- `src/lsd_thesis/thesis_loop/`: evidence loop and claim matrix helpers.
- `src/lsd_thesis/web/`: dashboard, public-site, artifact, figure, status, empirical-viewer payloads.
- `src/lsd_thesis/templates/` and `src/lsd_thesis/static/`: dashboard HTML/CSS/JS.
- `scripts/`: pipeline, dashboard, export, archive, evidence loop, motion/confound, external-data helpers.
- `tests/`: 19 files, 82 collected tests.
- `results/`: curated tracked evidence plus ignored generated/cache outputs.
- `output/` and `_site/`: ignored generated local/public outputs.
- `prior_art/`: ds003059 reproducibility inventory.

## 5. Dashboard And Artifact Summary

Local dashboard routes include `/`, `/ranking`, `/robustness`, `/prior-art`, `/empirical`, `/simulator`, `/thesis`, `/figures`, `/dashboard`, `/local-dashboard`, `/dashboard/full`, `/methods`, `/appendix`, and API routes for dashboard, public-site, prior-art, empirical-view, simulation, and artifacts.

Public payload schema: `public_site.v1`.

Artifact links use `/artifacts/...`, forward slashes, allowlisted roots/extensions, and security headers. Subject-level empirical cache paths under `results/stage_2/empirical_viewer/subject_views/` are denied.

High-risk/no-touch artifact areas: Stage 2 caches, dynamic mechanism outputs, parcellation/data-fetch, run-02/music, neuromaps/PET/SC, raw/private/cache data, `_site/`, `output/`, archive manifests/checksums, dashboard/public JSON schemas, route aliases, claim wording, claim labels, and gate/status semantics.

`autoresearch-results/` exists and is ignored/untracked; it was not staged or modified.

## 6. Images And Screenshots Included

Screenshots:

- `docs/reports/project_state_handoff/assets/screenshots/dashboard-overview.png`
- `docs/reports/project_state_handoff/assets/screenshots/dashboard-ranking.png`
- `docs/reports/project_state_handoff/assets/screenshots/dashboard-robustness.png`
- `docs/reports/project_state_handoff/assets/screenshots/dashboard-prior-art.png`
- `docs/reports/project_state_handoff/assets/screenshots/dashboard-empirical.png`
- `docs/reports/project_state_handoff/assets/screenshots/dashboard-figures.png`

Representative existing figures copied:

- `docs/reports/project_state_handoff/assets/representative_figures/stage1_metric_shift.png`
- `docs/reports/project_state_handoff/assets/representative_figures/stage2_fit_robustness.png`
- `docs/reports/project_state_handoff/assets/representative_figures/pass2a_microsite.png`
- `docs/reports/project_state_handoff/assets/representative_figures/set_setting_seed_live_8020.png`

Skipped visuals:

- Full-page screenshots timed out, so viewport screenshots were captured.
- Static `_site` screenshot was skipped because Browser blocked `file://` navigation by policy.
- Mermaid rendering was skipped because `mmdc` was unavailable and dependencies must not be installed.

## 7. Recent Cleanup Passes And Commits

Recent sequence verified from git log:

- `e930888` docs truth pass: refreshed stale repo commands and paths.
- `1859b64` characterization tests: dashboard, public-site, route, artifact schema, and thesis status contracts.
- `19e57aa` figure payload refactor.
- `d2e71e1` artifact/results inventory report.
- `1c562bc` thesis upgrade gate/status helper extraction.
- `744de04` dashboard payload decomposition out of `app.py`.
- `af9d2ca` script CLI/import characterization tests.
- `466382f` selected script `SRC_ROOT` bootstrap cleanup.
- `69b0397` docs validation baseline sync.

## 8. Biggest Remaining Risks

- Strict motion/confound proof is incomplete: FD/DVARS/censoring predicate remains blocked.
- Zenodo DOI is missing, so archive publication is not complete even with a verified GitHub release URL.
- External validation, PET/receptor priors, neuromaps, structural-connectome, parcellation, and run-02/music work can easily overclaim if status labels are changed.
- Ignored generated outputs are not necessarily unused; dashboard/public artifacts may consume them.
- Pages/static payloads can drift if builds are run casually.
- Full pytest was not rerun in this handoff.

## 9. Suggested Next Steps

1. Add an artifact-tier README or docs note that points to the inventory and defines tracked evidence versus generated/cache/raw surfaces.
2. Do a dashboard visual review using screenshots and existing contract tests, without changing routes or schemas.
3. Prepare a motion-proof planning pack that lists exact FD/DVARS/censoring evidence needed before any C claim promotion.
4. Audit `_site/` versus local dashboard payloads without rebuilding Pages.
5. Decide whether package entry points or pre-commit are worth adding later.
6. Extend the producer/consumer artifact map before any cleanup.
7. Only with explicit approval, do a bounded external/PET/SC/neuromaps evidence audit.

## 10. What To Ask ChatGPT Next

Paste this brief and ask for one focused track at a time. Good prompts:

- "Review the artifact-tier policy proposal and turn it into a concise docs-only patch plan."
- "Review the dashboard screenshots and suggest low-risk UI improvements that do not change routes, schemas, or claim labels."
- "Draft a motion-proof evidence checklist without promoting any blocked status."
- "Design a no-regeneration `_site` drift audit plan for this repo."

Do not ask ChatGPT to run cleanup, regenerate artifacts, change claim wording, update dependencies, run scientific workflows, or modify result artifacts unless you explicitly approve that track.

