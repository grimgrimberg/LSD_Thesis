# Codex Runbook

Date: 2026-05-12

Scope: how to resume and execute the Set / Setting / Seed work without leaking data, overclaiming results, or skipping validation.

## How To Run PASS 1

PASS 1 is complete when the planning artifacts exist and no production implementation has started.

Expected PASS 1 actions:

1. Read project instructions and guardrails.
2. Inspect Git status.
3. Inventory MCPs and relevant skills.
4. Inspect package/test commands.
5. Inspect existing stage outputs.
6. Audit empirical module time series, run coverage, motion/confound availability, and dashboard stack.
7. Perform focused methods research.
8. Create or update:
   - `IMPLEMENTATION_PLAN.md`
   - `AGENT_STATUS.md`
   - `TASKS.md`
   - `docs/SET_SETTING_SEED_SPEC.md`
   - `docs/SCIENTIFIC_GUARDRAILS.md`
   - `docs/METHODS_RESEARCH.md`
   - `docs/MCP_USAGE_AND_SECURITY.md`
   - `docs/CODEX_RUNBOOK.md`
9. Stop before implementing PASS 2.

Recommended PASS 1 inspection commands:

```powershell
git -c safe.directory=D:/LSD_Thesis status --short --branch
codex mcp list
Get-ChildItem -Force -Name
Get-Content pyproject.toml
Get-ChildItem scripts -Name
Get-ChildItem results -Name
```

## How To Run PASS 2

PASS 2 should start with a checkpoint and a read-only data audit, not with model code.

Recommended start:

```powershell
git -c safe.directory=D:/LSD_Thesis status --short --branch
uv run pytest tests/test_dashboard_preview.py -q
```

Then implement the first slice:

1. `src/lsd_thesis/setting_seed/data.py`
2. `configs/setting_seed.yaml`
3. `scripts/run_setting_seed_reliability.py`
4. `tests/test_setting_seed_data.py`
5. `results/setting_seed/data_audit/RUN_COVERAGE.md`

Acceptance for first slice:

- `run-01` and `run-03` coverage reported.
- `run-02` current absence reported.
- `S03`, `S12`, and `S15` excluded only for music-specific analyses.
- Missing motion summaries reported.
- No model fitting.
- No raw data mutation.

## How To Run PASS 2A

PASS 2A is the safe empirical-foundation build. It does not download data or extract run-02.

```powershell
.venv\Scripts\python.exe scripts\run_setting_seed_pass2a.py
```

Individual steps:

```powershell
.venv\Scripts\python.exe scripts\run_setting_seed_data_audit.py
.venv\Scripts\python.exe scripts\run_setting_seed_reliability.py
.venv\Scripts\python.exe scripts\run_setting_seed_latent.py
.venv\Scripts\python.exe scripts\run_setting_seed_control_scaffold.py
.venv\Scripts\python.exe scripts\build_setting_seed_dashboard.py
```

Outputs:

- `results/setting_seed/data_audit/data_audit.json`
- `results/setting_seed/reliability/reliability_table.json`
- `results/setting_seed/latent/latent_coordinates.csv`
- `results/setting_seed/control/control_scaffold.json`
- `results/setting_seed/dashboard/dashboard_payload.json`
- `output/doc/set_setting_seed_microsite.html`

## How To Run PASS 2B-0

PASS 2B-0 is the readiness pass for future music-control work. It does not download data and does not extract run-02.

```powershell
uv run python scripts/run_setting_seed_pass2b0.py
```

Individual safe steps:

```powershell
uv run python scripts/run_setting_seed_motion_summary.py
uv run python scripts/run_setting_seed_data_audit.py
uv run python scripts/run_setting_seed_control_scaffold.py
uv run python scripts/build_setting_seed_dashboard.py
```

The explicit extraction command, after user approval only, is:

```powershell
uv run python scripts/run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 --stage2-output-dir results/setting_seed/run02_extraction/stage_2_music
```

Do not run that extraction command unless the user confirms the download/extraction cost. The command writes to a setting-seed extraction root rather than `results/stage_2`.

## PASS 2B Sequence

Use this sequence for the next implementation passes:

1. PASS 2B-0: run-02 + motion readiness.
2. PASS 2B-1: user-approved run-02 extraction.
3. PASS 2B-2: actual music-control analysis.
4. PASS 2B-3: reliability-weighted surrogate + ML baselines.
5. PASS 2B-4: thesis-level dashboard and final report.

Do not start PASS 2B-1 without explicit user approval for run-02 extraction/download. Do not start PASS 2B-2 until run-02 module time series are actually present and the music exclusions are enforced.

## One-Command Live Dashboard

Recommended safe live command:

```powershell
uv run python scripts/run_everything_live.py
```

This command:

1. rebuilds PASS 2B-0 setting-seed readiness artifacts,
2. runs dashboard preflight,
3. serves the dashboard on the first available local port starting at `8020`,
4. prints the main dashboard and Set / Setting / Seed microsite URLs.

Optional full legacy pipeline first:

```powershell
uv run python scripts/run_everything_live.py --with-legacy-pipeline
```

This can be slower because it runs the existing `run-everything` workflow before rebuilding the setting-seed artifacts.

Current canonical meanings:

- `uv run python scripts/run_everything_live.py`: fast safe live dashboard rebuild for PASS 2B-0 readiness.
- `uv run python scripts/run_everything_live.py --with-legacy-pipeline`: implemented safe everything plus live dashboard; this reruns Stage 1-4 and the existing ML benchmark scripts first.
- run-02 extraction and actual music-control analysis are not included in either command unless the user explicitly approves the gated extraction command in the PASS 2B-0 section above.

## Recommended Commands

Install:

```powershell
uv sync --extra dev
```

Run tests:

```powershell
uv run pytest
```

Run focused tests:

```powershell
uv run pytest tests/test_dashboard_preview.py -q
```

Lint:

```powershell
uv run ruff check .
```

Type check:

```powershell
uv run mypy src
```

Run all existing stages:

```powershell
uv run python scripts/run_pipeline.py run-all
```

Launch dashboard:

```powershell
uv run python scripts/run_dashboard.py
```

Export training windows:

```powershell
uv run python scripts/export_training_dataset.py
```

If `uv` is blocked by local cache or sandbox issues, use the local environment fallback:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\run_dashboard.py
```

## Test Commands For PASS 2

Minimum final gate:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/preview_dashboard.py --check-only --strict
```

Useful focused gates:

```powershell
uv run pytest tests/test_setting_seed_data.py -q
uv run pytest tests/test_setting_seed_ml_splits.py -q
uv run pytest tests/test_dashboard_preview.py -q
uv run pytest tests/test_web.py tests/test_web_integration.py -q
```

## How To Resume From `AGENT_STATUS.md`

1. Read `AGENT_STATUS.md`.
2. Read `IMPLEMENTATION_PLAN.md`.
3. Read `TASKS.md`.
4. Read `docs/SCIENTIFIC_GUARDRAILS.md`.
5. Inspect Git status.
6. Continue from the first unchecked PASS 2 task.

Do not infer that previous generated outputs are current unless the file timestamps and validation artifacts support that.

## How To Inspect Dashboard Locally

Preflight:

```powershell
uv run python scripts/preview_dashboard.py --check-only --strict
```

Run:

```powershell
uv run python scripts/run_dashboard.py
```

Open:

```text
http://127.0.0.1:8000/
```

Useful endpoints:

```text
http://127.0.0.1:8000/api/dashboard-data
http://127.0.0.1:8000/api/empirical-view
```

Browser/Playwright should be used for local dashboard inspection after UI changes. It was not needed for PASS 1 because no UI implementation changed.

## How To Collect Artifacts

Expected PASS 2 artifact root:

```text
results/setting_seed/
```

Every implemented stage should write:

- a machine-readable artifact (`.json`, `.csv`, or `.yaml`),
- a concise markdown summary,
- figures when relevant,
- provenance showing source files, run date, parameters, and validation state.

Do not overwrite historical Stage 1-5 outputs unless the command explicitly owns that stage and the user expects regeneration.

## How To Avoid Leakage

Rules:

- Use subject-disjoint splits for ML and model selection.
- Do not split windows from the same subject across train and test.
- Fit PCA, normalizers, feature selectors, and model hyperparameters only on train subjects.
- Treat full-cohort Stage 5 results as calibration/model comparison, not validation.
- Cite approved CV5 artifacts from `output/validation/cv5_subject_disjoint/results/`.
- Do not cite root `results/stage_3/stage_3_summary.json` as approved CV5 evidence.

Recommended test requirements:

- Assert train and test subject sets are disjoint.
- Assert every prediction row has `subject`, `session`, `run`, `fold`, and `split_role`.
- Assert fold-local transforms do not see held-out subjects.

## How To Avoid Overclaiming

Required language:

- "proxy"
- "surrogate"
- "macro-scale"
- "consistent with"
- "subject-disjoint validation"
- "exploratory"

Forbidden language:

- "the model is tripping"
- "the brain is Stable Diffusion"
- "hallucination decoder"
- "receptor-realistic" without receptor-map implementation
- "clinical prediction"
- "biological proof"

Every report should distinguish:

- implemented fact,
- empirical observation,
- proxy target,
- calibration result,
- subject-disjoint validation,
- hypothesis,
- analogy.
