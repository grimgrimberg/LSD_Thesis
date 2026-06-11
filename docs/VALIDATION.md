# Validation Notes

Current status date: 2026-06-11

## Current Quality Baseline

Use this section and `results/thesis_upgrade/thesis_upgrade_status.json` as the current local validation baseline. Older pass notes below are retained as historical implementation evidence and should not be read as live gate status.

Latest local checks:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run python scripts\preview_dashboard.py --check-only --strict
node --check src\lsd_thesis\static\dashboard.js
```

Observed current results:

- Ruff: all checks passed.
- mypy: no issues found in 107 source files.
- pytest: 33 passed; selected production-surface coverage was 32.17%, satisfying the restored 30% coverage gate.
- dashboard preview preflight: required files present, optional generated artifacts present, thesis gate contract passed, and CV5 subject-disjoint validation reported as completed internal validation with 5/5 folds.
- JavaScript syntax check: `dashboard.js` parsed successfully.

Current dashboard-focused smoke slice:

```powershell
uv run pytest tests\test_web_security.py tests\test_dashboard_redesign_contract.py tests\test_validation_status.py -q -o addopts=
```

Current thesis-upgrade status:

- Thesis readiness gates: `6/9`.
- Strict completion gates: `4/6`.
- Package readiness gates: `1/2`.
- Missing strict requirements: `motion_confound_control_result`, `project_phase`.
- Missing package requirements: `reproducible_archive_publication`.
- Real remaining hard requirement: fMRIPrep FD/DVARS/censoring motion proof.
- Project phase: `research_demo_ready_not_completed_thesis`.

Archive publication status: GitHub prerelease `thesis-evidence-2026-06-02` is recorded and verified in `results/reproducible_archive/ARCHIVE_MANIFEST.json`; Zenodo DOI publication is still missing, so `reproducible_archive_publication` remains incomplete.

CV5 validation status: the tracked compact summary at `results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json` records the strict-check state. The full local aggregate under ignored `output/validation/cv5_subject_disjoint/results/` completed 5/5 folds with 15 subjects, n=3 held out per fold, zero selection/validation subject overlap, and every subject held out exactly once. This is internal validation only, not external cohort, receptor-level, subjective, or clinical validation. It remains caveated by the missing subject-level motion/FD/DVARS/confound/censoring strata.

The missing `project_phase` item is derived from the motion-proof blocker. Do not mark the strict motion gate complete from raw-BOLD image QC, published aggregate FD context, design controls, module-DVARS proxies, OpenNeuro filename hits, reachable derivative repositories, GitHub release publication, or archive manifests; those are useful context, not full fMRIPrep FD/DVARS/censoring proof.

Motion-gate completion requires the whole strict predicate, not just an implemented-looking status string: parsed motion analysis, paired motion summary rows, implemented dedicated motion-control status, paired/merged control rows at the configured minimum, non-empty association rows, and FD, DVARS, plus censoring/outlier family coverage.

## Historical Validation Log

Date: 2026-05-12

## PASS 2A Validation Commands

Targeted tests:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_setting_seed_data.py tests\test_setting_seed_reliability.py tests\test_setting_seed_latent.py tests\test_setting_seed_control.py tests\test_setting_seed_dashboard.py -q -o addopts= -p no:cacheprovider
```

Result:

```text
16 passed in 10.74s
16 passed in 16.05s
16 passed in 6.50s
```

The final run above followed the reliability eligibility guardrail update that keeps Tier A labels but blocks primary-fit eligibility until motion sensitivity is available.

PASS 2A artifact build:

```powershell
.venv\Scripts\python.exe scripts\run_setting_seed_pass2a.py
```

Result:

```text
PASS 2A artifacts written under results/setting_seed and output/doc/set_setting_seed_microsite.html
run_02_available=False motion_summaries_available=False
```

Script help smoke tests:

```powershell
.venv\Scripts\python.exe scripts\run_setting_seed_data_audit.py --help
.venv\Scripts\python.exe scripts\run_setting_seed_reliability.py --help
.venv\Scripts\python.exe scripts\run_setting_seed_latent.py --help
.venv\Scripts\python.exe scripts\run_setting_seed_control_scaffold.py --help
.venv\Scripts\python.exe scripts\build_setting_seed_dashboard.py --help
.venv\Scripts\python.exe scripts\run_setting_seed_pass2a.py --help
```

Result: all six commands exited 0 and printed expected help text.

Ruff targeted check:

```powershell
.venv\Scripts\python.exe -m ruff check src\lsd_thesis\setting_seed scripts\run_setting_seed_data_audit.py scripts\run_setting_seed_reliability.py scripts\run_setting_seed_latent.py scripts\run_setting_seed_control_scaffold.py scripts\build_setting_seed_dashboard.py scripts\run_setting_seed_pass2a.py tests\test_setting_seed_data.py tests\test_setting_seed_reliability.py tests\test_setting_seed_latent.py tests\test_setting_seed_control.py tests\test_setting_seed_dashboard.py
```

Result:

```text
All checks passed!
```

Ruff could not write cache files under `.ruff_cache` because of local access-denied warnings, but the check itself passed.

## Mypy Status

Targeted mypy attempts on `src\lsd_thesis\setting_seed` did not complete reliably in this Windows sandbox:

- one run timed out after an unexpectedly long hang,
- a follow-up with a local cache exited with status 1 but emitted no diagnostic text.

Treat PASS 2A mypy as not verified. The next pass should retry mypy with the repo's standard command or investigate the local mypy/sandbox behavior before claiming type-check success.

## Dashboard Preflight

After PASS 2A code changes, the dashboard preflight passed:

```powershell
.venv\Scripts\python.exe scripts\preview_dashboard.py --check-only --strict
```

Result summary: required app/config files were present, optional generated artifacts were present, local URL was `http://127.0.0.1:8000/`, and subject-disjoint held-out validation was reported as completed CV5 internal validation with 5/5 folds. The preflight explicitly does not imply external validation.

Live Playwright smoke was completed locally after the dashboard server started:

```text
http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html
```

Result: page loaded with title `Set / Setting / Seed`; screenshot saved to `results/setting_seed/dashboard/screenshots/pass2a_microsite.png`.

## Historical Web Test Slice (superseded)

The current dashboard-focused smoke slice is listed in the current baseline above. The older PASS 2A command below is retained only as historical context and references test names from that earlier implementation phase.

Attempted:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_web.py tests\test_web_integration.py -q -o addopts= -p no:cacheprovider
```

Result: `19 passed`, then `10 errors` during setup because pytest could not access `C:\Users\yuval\AppData\Local\Temp\pytest-of-yuval`.

A retry with `TEMP`, `TMP`, and `--basetemp` pointed at `results\setting_seed\web_pytest_tmp` also failed during pytest temp cleanup with access denied. Treat this as an environment/temp-permission blocker, not as evidence of a dashboard assertion failure.

## Leakage And Claim Status

- No ML was added.
- No run-02 extraction was run.
- No motion sensitivity was computed.
- Descriptive PCA is labeled visualization-only.
- Reliability tiers are proxy target-eligibility labels, not biological proof.

## PASS 2B-0 Validation Commands

MCP re-check:

```powershell
codex mcp list
```

Result: detected `depwire`, `playwright`, `context7`, `figma`, and `linear`. No remote MCP was used.

Functional targeted test slice:

```powershell
uv run pytest --no-cov tests/test_cli.py tests/test_setting_seed_reliability.py tests/test_setting_seed_motion.py tests/test_setting_seed_latent.py tests/test_setting_seed_data.py tests/test_setting_seed_dashboard.py tests/test_setting_seed_control.py tests/test_ds003059.py::test_run_selector_defaults_to_rest_and_requires_explicit_music_flag tests/test_ds003059.py::test_build_rest_manifest_can_include_music_only_when_flagged
```

Result:

```text
35 passed in 9.16s
```

Earlier targeted pytest without `--no-cov` also had all selected tests pass, then failed only the global coverage gate because the slice covered 9.06% of the full package.

PASS 2B-0 artifact build:

```powershell
uv run python scripts/run_setting_seed_pass2b0.py
```

Result:

```text
PASS 2B-0 readiness artifacts written under results/setting_seed and output/doc/set_setting_seed_microsite.html
run_02_files_present=False run_02_analysis_ready=False motion_status=unavailable_not_found
```

Generated readiness artifacts:

- `results/setting_seed/data_audit/data_audit.json`
- `results/setting_seed/motion/motion_summary.json`
- `results/setting_seed/motion/motion_report.md`
- `results/setting_seed/control/control_scaffold.json`
- `results/setting_seed/dashboard/dashboard_payload.json`
- `output/doc/set_setting_seed_microsite.html`

Repo-level ruff:

```powershell
uv run ruff check .
```

Result:

```text
All checks passed!
```

Full pytest:

```powershell
uv run pytest
```

Result:

```text
239 passed, 3 warnings in 143.27s
coverage: 84.67%
```

Full mypy:

```powershell
uv run mypy src
```

Result:

```text
Success: no issues found in 46 source files
```

Dashboard preflight:

```powershell
uv run python scripts/preview_dashboard.py --check-only --strict
```

Result: exited 0; required files and optional generated artifacts were present.

Playwright MCP local smoke:

```text
http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html
http://127.0.0.1:8000/
```

Result: static microsite title `Set / Setting / Seed`; main dashboard title `Whole-Brain Surrogate Dashboard`.

## 2026-05-14 Implemented Safe Everything Rerun

The implemented safe workflow was rerun after resolving two launcher/environment issues:

- `results/stage_2/empirical_cache_metadata.json` was restored from the existing Stage 2 manifest and empirical run summaries so Stage 2 did not attempt a network fetch.
- `scripts/run_pipeline.py run-everything` now calls the training-window export with the active Python interpreter instead of `uv run python`, avoiding the Windows uv cache ACL issue for that local script.

Full implemented pipeline:

```powershell
.venv\Scripts\python.exe scripts\run_pipeline.py run-everything
```

Result:

```text
[pipeline] finished stage1
[pipeline] finished stage2
[pipeline] finished stage3
[pipeline] finished stage4
D:\LSD_Thesis\results\training\ds003059_windows.npz
600
condition benchmark best_model=temporal_cnn balanced_accuracy_mean=0.595 roc_auc_mean=0.7190000000000001
multitask benchmark best_classification_model=multitask_temporal_cnn best_classification_balanced_accuracy=0.62 best_regression_model=hist_gradient_multitask best_regression_r2=0.26161830983528817
[pipeline] all requested stages completed
```

Thesis follow-ons:

```powershell
.venv\Scripts\python.exe scripts\run_pipeline.py stage-2b-target-validation
.venv\Scripts\python.exe scripts\run_pipeline.py run-stage-5
.venv\Scripts\python.exe scripts\run_setting_seed_pass2b0.py
.venv\Scripts\python.exe scripts\preview_dashboard.py --check-only --strict
```

Results:

```text
stage2b target validation complete: 13 metrics, 15 paired subjects
stage5 literature fit complete: 12 candidates, best=thalamic_routing_only
PASS 2B-0 readiness artifacts written under results/setting_seed and output/doc/set_setting_seed_microsite.html
run_02_files_present=False run_02_analysis_ready=False motion_status=unavailable_not_found
Dashboard preview preflight exited 0; required and optional artifacts present; CV5 internal validation 5/5 folds.
```

Repo-level validation:

```powershell
.venv\Scripts\ruff.exe check .
.venv\Scripts\mypy.exe src --cache-dir D:\mypy_cache_lsd_20260514 --show-traceback
$env:GIT_CONFIG_COUNT='1'; $env:GIT_CONFIG_KEY_0='safe.directory'; $env:GIT_CONFIG_VALUE_0='D:/LSD_Thesis'; .venv\Scripts\python.exe -m pytest --no-cov --basetemp D:\pytest_tmp_lsd_full_20260514
```

Results:

```text
ruff: All checks passed! (cache-write warnings only)
mypy: Success: no issues found in 46 source files
pytest: 241 passed, 3 warnings in 94.56s
```

Local dashboard evidence:

```text
http://127.0.0.1:8020/ -> Whole-Brain Surrogate Dashboard
http://127.0.0.1:8020/artifacts/output/doc/set_setting_seed_microsite.html -> Set / Setting / Seed
```

Screenshot:

- `results/setting_seed/dashboard/screenshots/set_setting_seed_live_8020.png`

Still not run:

- run-02 extraction/download,
- actual music-control analysis,
- motion sensitivity analysis from real confound files.

Reason: those remain explicitly approval-gated or blocked by missing local artifacts.

## 2026-05-14 Run-02 Extraction Fix And Completion

Observed user failure:

```text
urllib.error.HTTPError: HTTP Error 400: Bad Request
```

Root cause:

- OpenNeuro GraphQL rejected the query because `DatasetFile.key` is no longer a valid field.
- The current API returns `id`; the repo now aliases `id` back to `key` internally so the existing manifest traversal continues to work.

Patch validation:

```powershell
.venv\Scripts\python.exe -m pytest --no-cov tests\test_setting_seed_data.py tests\test_ds003059.py::test_query_snapshot_files_uses_current_openneuro_schema_and_aliases_tree_key
.venv\Scripts\ruff.exe check src\lsd_thesis\data\ds003059.py src\lsd_thesis\setting_seed\data.py tests\test_ds003059.py tests\test_setting_seed_data.py
```

Result:

```text
6 passed, 1 pytest cache warning
ruff: All checks passed
```

Live OpenNeuro manifest smoke:

```text
root listing count: 24
run_counts: run-01=30, run-02=30, run-03=30
```

Approved extraction rerun:

```powershell
.venv\Scripts\python.exe scripts\run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 --stage2-output-dir results\setting_seed\run02_extraction\stage_2_music
```

Result:

- `30` run-02 BOLD files are now present under `data/ds003059`.
- `90` module arrays are present under `results/setting_seed/run02_extraction/stage_2_music/module_time_series`.
- `30` of those module arrays are run-02 arrays.
- `stage_2_summary.json` and `stage_2_report.md` were written in the non-legacy music output root.

Extraction audit:

```powershell
.venv\Scripts\python.exe scripts\run_setting_seed_data_audit.py --stage-2-dir results\setting_seed\run02_extraction\stage_2_music --output-dir results\setting_seed\run02_extraction\data_audit
```

Result summary:

```text
record_count=90
subject_count=15
runs=run-01,run-02,run-03
run_02_file_count=30
run_02_expected_file_count=24
run_02_valid_file_count=24
run_02_analysis_ready=True
music_control=blocked_missing_motion_review
```

Note: a narrow mypy file check timed out in the local Windows environment after this fix; no mypy diagnostics were produced. The previous full mypy gate from the same day passed.
