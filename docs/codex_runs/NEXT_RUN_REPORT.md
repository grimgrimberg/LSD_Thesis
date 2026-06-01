# Next Run Report

## Current State

Date: 2026-06-01

The branch `codex/thesis-evidence-pages` is synced with GitHub and the current quality baseline is green locally and in hosted CI.

Current thesis-upgrade status:

- Readiness gates: `8/8`.
- Strict completion gates: `4/6`.
- Missing strict requirements: `motion_confound_control_result`, `project_phase`.
- Real remaining hard requirement: fMRIPrep FD/DVARS/censoring motion proof.
- Project phase: `research_demo_ready_not_completed_thesis`.

The missing `project_phase` item is derived from the motion-proof blocker. It is not an independent science task.

## Current High-Leverage Fixes Already Landed

- Hosted CI now runs the quality gate and has passed repeatedly on this branch.
- Dashboard artifact policy was split out of `src/lsd_thesis/web/app.py` into `src/lsd_thesis/web/artifacts.py`.
- Dynamic mechanism prior/mask policy was split out of `src/lsd_thesis/dynamic_mechanism.py` into `src/lsd_thesis/dynamic_mechanism_priors.py`.
- Dashboard string-HTML cleanup is guarded by a repo-hygiene test: the dashboard template must not contain `.innerHTML`, `.outerHTML`, `insertAdjacentHTML`, or `dangerouslySetInnerHTML`.
- Generated-artifact policy is documented and tested through `.gitignore`, `docs/ARCHIVE_POLICY.md`, and `tests/test_repo_hygiene.py`.
- fMRIPrep motion proof now has an explicit preflight artifact and fail-closed status instead of an implicit missing gate.

## Fresh Verification Evidence

Latest local checks:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts\preview_dashboard.py --check-only --strict
```

Observed results:

- Ruff: all checks passed.
- mypy: no issues found in 73 source files.
- pytest: 333 passed, 4 warnings, total coverage 79.70%.
- dashboard preview preflight: required files present, optional generated artifacts present, CV5 internal validation reported as 5/5 folds.

Hosted CI after the Node-24 action-major bump:

- `3d3370e` / `Bump actions to Node 24 majors`
- CI Quality run `26759481922`
- Result: success.
- Node 20 action-runtime annotation: not present.

Recent hosted-CI annotation addressed in this branch:

- Earlier runs warned that `actions/checkout@v4`, `actions/setup-node@v4`, and `actions/setup-python@v5` were running on Node.js 20.
- `.github/workflows/ci.yml` now uses `actions/checkout@v5`, `actions/setup-python@v6`, `actions/setup-node@v5`, and Node 24 for the PPTX toolchain.
- `.github/workflows/pages.yml` now uses the same Node-24 action family plus `actions/upload-artifact@v7`.
- The first hosted run after the action-major bump stayed green and did not emit the Node 20 action-runtime annotation.

## Remaining Real Blocker

The strict motion gate is still incomplete because the current local ds003059 snapshot is derivative-like and does not contain subject/session/run fMRIPrep FD, DVARS, and censoring confounds.

Current proof artifacts:

- `results/confound_controls/fmriprep_motion_proof_plan.json`
- `results/confound_controls/motion_confound_control_status.json`
- `results/thesis_upgrade/thesis_upgrade_status.json`

Correct next action:

1. Obtain authorized subject/run motion confounds or the original raw BIDS inputs that preceded the derivative release.
2. Run fMRIPrep/MRIQC in a supported container/HPC environment.
3. Ingest `desc-confounds_timeseries.tsv` files with `scripts/run_setting_seed_motion_summary.py`.
4. Rebuild `scripts/build_motion_confound_controls.py`.
5. Rebuild `scripts/build_thesis_upgrade_status.py`.

Do not mark the strict motion gate complete from raw-BOLD image QC, published aggregate FD context, design controls, or module-DVARS proxies. Those layers are useful controls, not full fMRIPrep motion proof.

## Recommended Next Engineering Work

Priority order:

1. Split another large dashboard payload concern out of `src/lsd_thesis/web/app.py`.
2. Extract public transition/dynamic summary helpers so `dynamic_robustness.py` stops importing private helpers from `dynamic_mechanism.py`.
3. Add a compact dashboard/reporting architecture map.
4. Continue reducing stale generated-run reports; only commit tracked docs and curated evidence.

## Claim Boundaries To Preserve

Use:

- macro-dynamic proxy
- surrogate model
- graph-modulated dynamics
- altered-state-inspired perturbation
- model comparison and mismatch analysis

Avoid:

- receptor-level realism claims
- simulated subjective experience claims
- consciousness claims
- clinical claims
- presenting proxy motion/QC controls as full fMRIPrep FD/DVARS/censoring proof
