# Next Run Report

## Current State

Date: 2026-06-01

The branch `codex/thesis-evidence-pages` is synced with GitHub and the current quality baseline is green locally and in hosted CI.

Current engineering health rating: `9.0/10`; release/thesis-submission readiness: `B`. The rating is higher because the dashboard HTML sink cleanup, generated-artifact policy, hosted CI gate, large-module splits, and stricter motion-gate intake contract are now landed. It is still capped by the missing external fMRIPrep FD/DVARS/censoring motion proof and residual large research modules.

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
- Dashboard empirical-viewer and run-02 music-run policy was split out of `src/lsd_thesis/web/app.py` into `src/lsd_thesis/web/empirical_viewer.py`.
- Dashboard provenance/model-selection/validation/audit-status payload policy was split out of `src/lsd_thesis/web/app.py` into `src/lsd_thesis/web/status_payload.py`.
- Dashboard structural-connectome graph payload policy was split out of `src/lsd_thesis/web/app.py` into `src/lsd_thesis/web/structural_dti.py`.
- Dashboard PI-pitch, claim-status, and thesis-loop expansion payload policy was split out of `src/lsd_thesis/web/app.py` into `src/lsd_thesis/web/thesis_payload.py`.
- `docs/architecture.md` now contains a compact dashboard/reporting map guarded by `tests/test_repo_hygiene.py`.
- Dynamic mechanism prior/mask policy was split out of `src/lsd_thesis/dynamic_mechanism.py` into `src/lsd_thesis/dynamic_mechanism_priors.py`.
- Dynamic robustness now uses the public `src/lsd_thesis/dynamic_mechanism_stats.py` helper interface instead of importing private stat helpers.
- Dynamic mechanism transition, hierarchy/routing, and repertoire summaries now share the public `collect_paired_metric_rows` helper for paired LSD-placebo row/delta aggregation.
- Dashboard string-HTML cleanup is guarded by a repo-hygiene test: the dashboard template must not contain `.innerHTML`, `.outerHTML`, `insertAdjacentHTML`, or `dangerouslySetInnerHTML`.
- Generated-artifact policy is documented and tested through `.gitignore`, `docs/ARCHIVE_POLICY.md`, and `tests/test_repo_hygiene.py`.
- fMRIPrep motion proof now has an explicit preflight artifact and fail-closed status instead of an implicit missing gate.
- Motion-confound ingestion now rejects FD/DVARS files that cannot be joined by subject/session/run metadata.
- Authorized external fMRIPrep/confound roots can now be threaded through `scripts/build_thesis_upgrade_status.py --motion-root ...`, so the preflight, motion summary, confound-control result, and strict thesis status refresh from the same evidence source.
- Parsed confounds are now kept below the strict-proof threshold until they cover at least four paired LSD and placebo/PLCB subject/run rows.
- The downstream motion-confound control result now rejects unpaired observed-only motion features; strict association tests require paired LSD-placebo motion features.
- Parsed fMRIPrep FD spike burden and scrub/censor/outlier burden now flow into the joined motion-control association table under strict-gate feature names.
- The dedicated motion-confound control artifact now fails closed unless association rows cover FD, DVARS, and censoring/outlier feature families.
- Author-style long-form confound metadata values such as `001`, `LSD`, and `1` now normalize to the repo's join keys (`sub-001`, `ses-LSD`, `run-01`) before motion summaries are joined to subject/run dynamic deltas.
- External motion roots are now threaded through the thesis-status refresh, source-availability check, and static Pages build so published/provenance artifacts can stay consistent with the same authorized confound root.
- Motion source availability now reports parser readiness, pairing readiness, parsed summary count, and unusable file count; a discovered local motion-like TSV does not count as available confounds unless it parses with joinable metadata.
- The thesis-upgrade strict motion gate now rejects implemented-looking motion-control status strings unless the evidence also has explicit paired-control readiness, enough paired/merged rows, and FD, DVARS, plus censor/outlier association-row coverage.
- The current OpenNeuro ds003059 snapshot check is recorded in `results/confound_controls/fmriprep_motion_proof_plan.json`: 250 snapshot files, 15 T1w files, and 0 confound-like files.

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
- mypy: no issues found in 77 source files.
- pytest: 360 passed, 4 warnings, total coverage 80.01%.
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
3. Ingest and rebuild the gate with `scripts/build_thesis_upgrade_status.py --fetch-motion-remote --motion-root <path-to-authorized-fmriprep-or-confounds-root>`.

Do not mark the strict motion gate complete from raw-BOLD image QC, published aggregate FD context, design controls, or module-DVARS proxies. Those layers are useful controls, not full fMRIPrep motion proof.

## Recommended Next Engineering Work

Priority order:

1. Continue splitting remaining dashboard payload concerns out of `src/lsd_thesis/web/app.py`.
2. Continue splitting large dynamic-mechanism summary concerns behind public helper interfaces.
3. Keep the dashboard/reporting architecture map current as new `web/` modules are extracted.
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
