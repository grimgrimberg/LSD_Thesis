# TASKS

Date: 2026-05-12

Scope: Set / Setting / Seed extension. PASS 1 created this task list only. PASS 2 should implement incrementally with tests.

## PASS 2B Roadmap

- [x] PASS 2B-0: run-02 + motion readiness.
- [ ] PASS 2B-1: user-approved run-02 extraction.
- [ ] PASS 2B-2: actual music-control analysis.
- [ ] PASS 2B-3: reliability-weighted surrogate + ML baselines.
- [ ] PASS 2B-4: thesis-level dashboard and final report.

## PASS 1 Documentation

- [x] Inspect repo status before edits.
- [x] Inventory package manager, scripts, tests, dashboard stack, configs, outputs, and cache conventions.
- [x] Determine current empirical module time-series location.
- [x] Determine whether `run-02` music module time series exist.
- [x] Determine whether subject-level motion confound summaries exist.
- [x] Determine whether dashboard/microsite generator exists.
- [x] Inventory available MCP servers.
- [x] Inventory available skills from session/local registry where possible.
- [x] Perform focused methods research.
- [x] Write PASS 2 implementation plan.
- [x] Write scientific guardrails.
- [x] Write MCP/security usage notes.
- [x] Write Codex runbook.

## Post-PASS 2A Life Science Research Review

- [x] Use Life Science Research router to select relevant evidence lanes.
- [x] Use NCBI Entrez skill for public PubMed checks.
- [x] Review repo/results against scientific guardrails.
- [x] Record that the targeted LSD music/setting PubMed query returned zero records.
- [x] Write `docs/LIFE_SCIENCE_RESEARCH_REVIEW.md`.
- [x] Add the most relevant PubMed/scholarly sources to `docs/METHODS_RESEARCH.md` with thesis-use labels.

## PASS 2 Milestone 0: Checkpoint And Safety

- [x] Inspect `git -c safe.directory=D:/LSD_Thesis status --short --branch`.
- [x] Re-read `AGENT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, and `docs/SCIENTIFIC_GUARDRAILS.md`.
- [x] Confirm no raw data, generated arrays, secrets, or large outputs are staged.
- [ ] Ask whether to create a branch/worktree before any future broad code-changing pass.

## PASS 2 Milestone 1: Data Audit

- [x] Create `src/lsd_thesis/setting_seed/__init__.py`.
- [x] Create `src/lsd_thesis/setting_seed/data.py`.
- [x] Create `configs/setting_seed.yaml`.
- [x] Create `scripts/run_setting_seed_data_audit.py` as a read-only audit runner.
- [x] Create `tests/test_setting_seed_data.py`.
- [x] Inventory `results/stage_2/module_time_series`.
- [x] Confirm `run-01` and `run-03` rest coverage.
- [x] Confirm `run-02` absence or presence from actual files.
- [x] Encode music-specific exclusions: `S03`, `S12`, `S15`.
- [x] Confirm rest-only analyses do not exclude those subjects solely because music failed.
- [x] Inventory subject/run JSON views.
- [x] Inventory subject-level motion/confound summaries.
- [x] Produce `results/setting_seed/data_audit/data_audit.md`.

## PASS 2 Milestone 2: Reliability And Target Eligibility

- [x] Create `src/lsd_thesis/setting_seed/reliability.py`.
- [x] Read Stage 2 targets with typed schemas.
- [x] Mark primary targets:
  - `cross_network_communication`
  - `thalamic_coupling`
- [x] Mark candidate target:
  - `hierarchical_compression`
- [x] Mark sign-conflicted diagnostics:
  - `within_network_stability`
  - `entropy_diversity`
  - `metastability_proxy`
- [x] Mark exploratory targets:
  - `effective_barrier_proxy`
  - `switching_rate`
- [x] Add tests that diagnostic metrics are not primary optimization targets by default.
- [x] Produce `results/setting_seed/reliability/reliability_report.md`.

## PASS 2 Milestone 3: Latent Dynamics

- [x] Create `src/lsd_thesis/setting_seed/latent.py`.
- [x] Label full-data PCA as visualization-only.
- [x] Add PCA trajectory summaries.
- [x] Add latent spread, transition speed, and displacement summaries.
- [x] Separate visualization-only labels from ML claims.
- [x] Add synthetic tests for shape, determinism, and finite values.
- [x] Produce `results/setting_seed/latent/latent_report.md`.

## PASS 2 Milestone 4: Control-Theoretic Analysis

- [x] Create `src/lsd_thesis/setting_seed/control_input.py`.
- [x] Add honest music-control scaffold without DMD/DMDc fitting.
- [x] Add rest carryover and drug carryover interaction from available rest runs.
- [x] Keep Koopman and SINDy optional until DMDc is tested.
- [x] Add synthetic control tests.
- [x] Avoid fitted control transforms in PASS 2A.
- [x] Produce `results/setting_seed/control/music_control_report.md`.

## PASS 2 Milestone 5: Surrogate Mechanism Extension

- [ ] Create `src/lsd_thesis/setting_seed/surrogate_extension.py`.
- [ ] Define mechanism registry for:
  - `noise_only`
  - `lower_barrier_only`
  - `cross_talk_only`
  - `thalamic_routing_only`
  - `hierarchy_precision_only`
  - `music_input_gain_only`
  - `carryover_tau_only`
  - `routing_plus_music_gain`
  - `noise_plus_routing`
  - `full_guided_latent_model`
- [ ] Keep mechanisms config-driven.
- [ ] Add deterministic seed handling.
- [ ] Add parameter bounds and no-magic-constant documentation.
- [ ] Add scoring tests.
- [ ] Produce `results/setting_seed/surrogate/MECHANISM_RANKING.md`.

## PASS 2 Milestone 6: Scoring And Subject-Disjoint Validation

- [ ] Create `src/lsd_thesis/setting_seed/scoring.py`.
- [ ] Create `src/lsd_thesis/setting_seed/validation.py`.
- [ ] Reuse approved CV5 split manifest where appropriate.
- [ ] Hard-fail train/test subject overlap.
- [ ] Do not cite root `results/stage_3/stage_3_summary.json` as approved CV5 evidence.
- [ ] Make Stage 5-style ranking CV-aware before making validation claims.
- [ ] Add output-level tests for split manifests and prediction CSVs.

## PASS 2 Milestone 7: ML Models

- [ ] Create `src/lsd_thesis/setting_seed/ml_models.py`.
- [ ] Use `LeaveOneGroupOut(subject)` or approved CV5 subject splits.
- [ ] Fit normalization and feature selection only on train subjects.
- [ ] Forbid naive random window-level splits.
- [ ] Add tests that one subject cannot appear in train and test.
- [ ] Treat classification/regression outputs as diagnostic, not proof of mechanism.
- [ ] Produce `results/setting_seed/ml/SUBJECT_DISJOINT_ML_SUMMARY.md`.

## PASS 2 Milestone 8: Dashboard And Reporting

- [x] Create `src/lsd_thesis/setting_seed/dashboard_payload.py`.
- [x] Create `src/lsd_thesis/setting_seed/plotting.py`.
- [x] Add a backward-compatible `set_setting_seed` block to `/api/dashboard-data`.
- [x] Add visible data warnings for missing music and motion artifacts.
- [x] Add set, setting, seed, substance, routing, and guidance panels in the static microsite and main dashboard navigation.
- [x] Add dashboard payload tests.
- [x] Add strict preview check after full dashboard integration.
- [x] Add browser smoke test after UI changes.
- [x] Produce `results/setting_seed/dashboard/dashboard_payload.json`.
- [ ] Produce `results/setting_seed/figures/*.png` if a plotting pass is needed.
- [x] Produce `results/setting_seed/PASS2A_REPORT.md`.

## PASS 2A Follow-Ups

- [x] Add disabled-by-default run-02 extraction support behind explicit flags.
- [x] Add a non-legacy recommended output root for first run-02 extraction.
- [x] Add structured motion-summary parser and unavailable status.
- [x] Refresh data audit readiness fields for run-02 and motion.
- [x] Refresh dashboard payload with support/presence/readiness states.
- [x] Extract run-02 music module time series only after explicit user confirmation.
- [ ] Extract or compute subject/run-level motion summaries if authorized local files exist.
- [x] Investigate local mypy hang/blank failure before claiming type-check success.
- [x] Run live Browser/Playwright dashboard smoke test if visual verification is required.

## PASS 2 Final Validation

- [x] `uv run ruff check .` or equivalent `.venv\Scripts\ruff.exe check .`
- [x] `uv run mypy src` or equivalent `.venv\Scripts\mypy.exe src`
- [x] `uv run pytest` or equivalent full-suite pytest with external temp root
- [x] `uv run python scripts/preview_dashboard.py --check-only --strict`
- [x] If dashboard changed, launch/inspect the local dashboard. Latest verified URL: `http://127.0.0.1:8020/`.
