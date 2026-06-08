# Set, Setting, and Seed Implementation Plan

Date: 2026-05-12

Scope: PASS 1 planning only. This file prepares PASS 2. It does not implement the new system, rewrite core code, or change generated neuroimaging outputs.

## Objective

Extend the existing LSD whole-brain surrogate and empirical fMRI project into a reliability-gated, control-theoretic, diffusion-inspired analysis of seed, setting, substance, routing, and latent brain dynamics.

The extension should test whether LSD-associated dynamics in OpenNeuro `ds003059` are better explained by:

1. Unstructured endogenous stochasticity.
2. Lowered switching barriers or a flattened control-energy landscape.
3. Altered thalamocortical and cross-network routing.
4. Altered hierarchical guidance or prior precision.
5. Increased sensitivity to external context, especially music.
6. A combination of routing and context sensitivity.

All claims must remain at the transparent surrogate and macro-dynamics level.

## Current Repo Grounding

### Stack

- Package manager: `uv`.
- Python target: `>=3.13`.
- Build backend: Hatchling.
- Main app package: `src/lsd_thesis`.
- Dashboard stack: FastAPI, Uvicorn, Jinja2 templates, vanilla JavaScript, Plotly CDN.
- Scientific stack: NumPy, SciPy, pandas, NetworkX, Nilearn, NiBabel, scikit-learn, Matplotlib, Plotly.
- Existing command style: script entrypoints under `scripts/`; no `pyproject.toml` console scripts.

### Existing Commands

```powershell
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src
uv run python scripts/run_pipeline.py run-all
uv run python scripts/run_dashboard.py
uv run python scripts/export_training_dataset.py
```

If `uv` is blocked by a local cache or sandbox issue, prefer the local environment fallback:

```powershell
.venv\Scripts\python.exe scripts\run_dashboard.py
.venv\Scripts\python.exe -m pytest
```

### Existing Empirical Anchors

- Dataset: OpenNeuro `ds003059`.
- Conditions: `ses-PLCB` and `ses-LSD`.
- Cached rest runs: `run-01` (`Rest1`) and `run-03` (`Rest3`).
- Cached music run: not present in current `results/stage_2/module_time_series`.
- Current paired rest cohort: 15 subjects, 60 records, 217 timepoints per run.
- Modules:
  - `visual`
  - `auditory`
  - `salience`
  - `default_mode`
  - `executive_frontoparietal`
  - `limbic_affective`
  - `thalamic_gateway`
  - `sensorimotor`

### Current Empirical Targets

From `results/stage_2/empirical_perturbation_targets.yaml`:

| Metric | LSD-minus-placebo delta | Confidence | PASS 2 usage |
|---|---:|---|---|
| `cross_network_communication` | `+0.07407619939923198` | strong | Primary target |
| `thalamic_coupling` | `+0.11991820431751381` | strong | Primary target |
| `hierarchical_compression` | `+0.054149688768586765` | weak | Candidate target |
| `within_network_stability` | `+0.06609328671299261` | moderate | Diagnostic, sign-conflicted |
| `entropy_diversity` | `-0.0022526077494528915` | weak | Diagnostic, sign-conflicted |
| `metastability_proxy` | `-0.053960353741377386` | moderate | Diagnostic, sign-conflicted |
| `effective_barrier_proxy` | `-0.1491923940892797` | weak | Exploratory target |
| `switching_rate` | `+0.012345679012345678` | weak | Exploratory target |

### Current Model-Ranking Anchors

- Stage 5 full-cohort, non-quick best candidate: `thalamic_routing_only`, loss `0.762443`.
- Approved CV5 validation artifact: `output/validation/cv5_subject_disjoint/results/cv5_aggregate_validation.json`.
- CV5 selected `more_cross_talk @ 0.1` in all five folds.
- CV5 is subject-disjoint; generic root `results/stage_3/stage_3_summary.json` is not the approved CV5 validation result.

## PASS 2 Architecture

Adapt the requested file structure to the existing package convention by placing new code under `src/lsd_thesis/setting_seed/`, not a new top-level `src/setting_seed/` package.

```text
src/
  lsd_thesis/
    setting_seed/
      __init__.py
      data.py
      reliability.py
      latent.py
      control_input.py
      surrogate_extension.py
      scoring.py
      ml_models.py
      dashboard_payload.py
      plotting.py
      validation.py

configs/
  setting_seed.yaml

scripts/
  run_setting_seed_reliability.py
  run_setting_seed_latent.py
  run_setting_seed_music_control.py
  run_setting_seed_surrogate.py
  run_setting_seed_ml.py
  build_setting_seed_dashboard.py

docs/
  SET_SETTING_SEED_SPEC.md
  SCIENTIFIC_GUARDRAILS.md
  METHODS_RESEARCH.md
  MCP_USAGE_AND_SECURITY.md
  CODEX_RUNBOOK.md
  DASHBOARD_GUIDE.md

results/
  setting_seed/
    data_audit/
    reliability/
    latent/
    control/
    surrogate/
    ml/
    dashboard/
    figures/
    FINAL_REPORT.md

tests/
  test_setting_seed_data.py
  test_setting_seed_reliability.py
  test_setting_seed_latent.py
  test_setting_seed_control.py
  test_setting_seed_scoring.py
  test_setting_seed_ml_splits.py
```

## PASS 2 Milestones

### Milestone 0: Safety And Checkpoint

1. Inspect `git status` with `git -c safe.directory=D:/LSD_Thesis status --short --branch`.
2. Confirm whether the user wants a branch or worktree before code changes.
3. Re-read `AGENT_STATUS.md`, `TASKS.md`, and the guardrail docs.
4. Do not delete or mutate `/data`, `/output`, caches, or generated artifacts.

Verification:

```powershell
git -c safe.directory=D:/LSD_Thesis status --short --branch
```

### Milestone 1: Data Audit And Music Availability

Goal: create a reproducible `results/setting_seed/data_audit/` report before modeling.

Implementation targets:

- Add a read-only inventory function for:
  - cached module time series,
  - subject/session/run coverage,
  - run-02 availability,
  - music exclusions (`S03`, `S12`, `S15`),
  - empirical viewer JSON consistency,
  - motion/confound file presence.
- Fail closed for music analyses if run-02 module time series are absent.
- Keep rest-only analyses allowed for all valid paired rest subjects.

Tests:

- `test_setting_seed_data.py`
- Assert run labels are parsed correctly.
- Assert music exclusion does not remove subjects from rest-only analysis.
- Assert no music model runs if `run-02` time series are absent.

### Milestone 2: Reliability Layer

Goal: make target eligibility explicit before extending objectives.

Implementation targets:

- Build `reliability.py` around existing Stage 2 and Stage 2b artifacts.
- Label targets as primary, candidate, diagnostic, or exploratory.
- Carry confidence labels into downstream scoring and dashboard payloads.
- Preserve sign-conflicted metrics as diagnostics rather than optimizing them as primary objectives.

Tests:

- Verify strong targets are selected by default.
- Verify sign-conflicted metrics are excluded from primary objective unless explicitly enabled.
- Verify missing reliability files produce a clear, non-destructive error.

### Milestone 3: Latent And Control Baselines

Goal: start with interpretable methods before neural sequence models.

Implementation targets:

- Latent summaries:
  - PCA or factor-analysis trajectories over eight modules,
  - condition deltas in latent spread, transition speed, and state dwell time.
- Linear dynamics:
  - DMD for condition-specific dynamics,
  - DMDc with control variables for `substance`, `run`, and optional `music_input`,
  - simple state-space/control-energy proxies.
- Keep DMDc, Koopman, and SINDy as scalar summaries first; do not make them the thesis claim.

Tests:

- Synthetic linear system with known control effect.
- Subject-disjoint split test for all fitted transforms.
- Shape and finite-value checks for short time series.

### Milestone 4: Mechanism Extension

Goal: map candidate mechanisms to explicit parameter perturbations and empirical signatures.

Candidate mechanisms:

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

Implementation targets:

- Add a new mechanism registry without disturbing existing Stage 5 mechanisms.
- Compute mechanism signatures against primary targets and optional setting-specific targets.
- Preserve old Stage 5 outputs as historical baseline artifacts.

Tests:

- Each mechanism has explicit config, seed handling, parameter bounds, and output schema.
- Mechanism scoring is deterministic for fixed seeds.
- No mechanism accesses held-out subject targets during selection.

### Milestone 5: Subject-Disjoint ML

Goal: allow ML only as a leakage-controlled analysis layer.

Implementation targets:

- Reuse existing `LeaveOneGroupOut(subject)` patterns.
- Add explicit split manifests for every ML output.
- Hard-fail naive window-level random splitting.
- Use nested or fixed hyperparameters; do not tune on held-out subjects.
- Treat classification as diagnostic, not proof of mechanism.

Tests:

- No subject appears in both train and test.
- Normalization and feature selection fit only on train subjects.
- Prediction CSVs include `subject`, `session`, `run`, `fold`, and `split_role`.

### Milestone 6: Dashboard Payload And UI

Goal: make the existing dashboard explain set, setting, seed, substance, routing, and guidance without creating a marketing page.

Implementation targets:

- Extend `/api/dashboard-data` with a backward-compatible `set_setting_seed` block.
- Add panels:
  - Set: subject baseline geometry and placebo/rest reference.
  - Setting: run context, music availability, and exclusion state.
  - Seed: stochastic seed, initial condition, and subject-specific latent state.
  - Substance: PLCB/LSD perturbation.
  - Guidance: routing, hierarchy, precision, and context sensitivity.
- Add visible warnings when music data or motion summaries are absent.
- Keep all source text scientifically restrained.

Tests:

- Payload schema test.
- Dashboard preflight strict check.
- Browser smoke test with local dashboard once UI changes exist.

### Milestone 7: Reporting And Publication Artifacts

Goal: produce disk artifacts for every stage.

Outputs:

- `results/setting_seed/data_audit/RUN_COVERAGE.md`
- `results/setting_seed/reliability/RELIABILITY_SUMMARY.md`
- `results/setting_seed/latent/LATENT_SUMMARY.md`
- `results/setting_seed/control/CONTROL_SUMMARY.md`
- `results/setting_seed/surrogate/MECHANISM_RANKING.md`
- `results/setting_seed/ml/SUBJECT_DISJOINT_ML_SUMMARY.md`
- `results/setting_seed/dashboard/dashboard_payload.json`
- `results/setting_seed/figures/*.png`
- `results/setting_seed/FINAL_REPORT.md`

## Validation Gate For PASS 2

Minimum before declaring PASS 2 complete:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/preview_dashboard.py --check-only --strict
```

If full `pytest` is too expensive during intermediate work, run focused tests first, then full validation before final handoff.

## Design Decisions And Rubric

Scores are 1 to 5. Higher is better except overclaiming risk, where lower is better.

| Decision | Scientific validity | Interpretability | Leakage resistance | Reproducibility | Implementation risk | Compute cost | Thesis relevance | UI value | Novelty | Overclaiming risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Start from cached rest-only reliability extension | 4 | 5 | 5 | 5 | 2 | 1 | 5 | 3 | 3 | 1 |
| Add run-02 music extraction only after data audit | 4 | 4 | 4 | 4 | 3 | 3 | 5 | 5 | 4 | 2 |
| Use DMDc and linear state-space before neural SDE | 4 | 4 | 4 | 4 | 3 | 2 | 5 | 4 | 4 | 2 |
| Keep neural ODE/CDE/SDE exploratory | 3 | 2 | 3 | 3 | 5 | 5 | 4 | 3 | 4 | 3 |
| Require subject-disjoint ML only | 4 | 3 | 5 | 4 | 3 | 2 | 4 | 3 | 3 | 2 |
| Revamp dashboard around set/setting/seed panels | 3 | 5 | 4 | 4 | 3 | 2 | 5 | 5 | 3 | 1 |

## Immediate PASS 2 Starting Point

Start with `src/lsd_thesis/setting_seed/data.py`, `configs/setting_seed.yaml`, `scripts/run_setting_seed_reliability.py`, and `tests/test_setting_seed_data.py`.

The first implemented behavior should be a read-only data-audit command that proves:

1. Rest module time series exist for `run-01` and `run-03`.
2. `run-02` module time series are absent in current cached Stage 2 outputs.
3. Music-specific analyses must exclude `S03`, `S12`, and `S15` once music data exist.
4. Motion summaries are not currently available as subject-level FD/DVARS/confound artifacts.
5. No downstream model can silently train or validate on leaked subject windows.
