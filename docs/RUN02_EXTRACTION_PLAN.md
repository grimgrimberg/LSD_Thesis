# Run-02 Music Extraction Plan

Date: 2026-05-12

Status: run-02 extraction completed in a non-legacy output root on 2026-05-14. Legacy `results/stage_2` semantics were not changed.

## Current Availability

- Local dataset notes exist in `data/ds003059/README`.
- Current cached Stage 2 module time series exist for `run-01` and `run-03`.
- No `run-02` module time series exist in `results/stage_2/module_time_series`.
- Current cached `empirical_run_summaries.json` contains 60 records: 15 subjects x 2 sessions x 2 rest runs.
- Current motion/confound files are not present as subject/run-level FD, DVARS, confound, or censoring tables.

## Dataset Design

- `run-01`: Rest1.
- `run-02`: Music.
- `run-03`: Rest3.

Music-specific exclusions:

- `S03` -> `sub-003`
- `S12` -> `sub-012`
- `S15` -> `sub-015`

These exclusions apply to music-specific analyses only. They should not remove valid rest-only observations.

## Existing Code Path

Current run filtering is in `src/lsd_thesis/data/ds003059/`.

Relevant behavior:

- The manifest builder keeps `ses-LSD` and `ses-PLCB`.
- It keeps `_task-rest_` BOLD files.
- It explicitly skips `_run-02_`.
- It keeps only `_run-01_` and `_run-03_`.
- `extract_empirical_run_records()` can write module arrays named `{subject}_{session}_{run}_modules.npy` once the manifest contains the run.

Primary modification points for a future pass:

- `src/lsd_thesis/data/ds003059/`: add an explicit run-selection option.
- `scripts/run_pipeline.py`: expose a guarded flag such as `--include-music` or `--runs run-01 run-02 run-03`.
- Tests in `tests/test_ds003059_wrappers.py`: assert default rest-only behavior remains unchanged.

## Feasible Future Flag

A future tiny code change could add one of these explicit flags:

```text
--include-music
--runs run-01 run-02 run-03
--allow-music-extraction
```

Default must remain rest-only to preserve legacy Stage 2 behavior.

## Expected Outputs If Extracted

If run-02 extraction is confirmed and run:

- `results/stage_2/module_time_series/*_run-02_modules.npy`
- updated or separate empirical run summary containing run-02 records
- updated or separate empirical viewer JSON for music runs
- new `results/setting_seed/data_audit/data_audit.json` with `run_02_available: true`
- future `results/setting_seed/control/` music-control empirical effects

Prefer a separate setting-seed extraction root first, for example:

```text
results/setting_seed/run02_extraction/
```

Only merge into legacy `results/stage_2/` after explicit confirmation.

## Required User Confirmation

Ask before:

- downloading additional neuroimaging data,
- running expensive NIfTI extraction,
- mutating legacy Stage 2 caches,
- adding large generated outputs,
- broadening the empirical cohort or changing inclusion rules.

## Guardrail

Music analyses are scaffolded only until run-02 module time series exist and the `sub-003`, `sub-012`, `sub-015` music exclusions are enforced. PASS 2A makes no empirical music-control claim.

## PASS 2B-0 Update

PASS 2B-0 added disabled-by-default run-selection support. Legacy Stage 2 still defaults to `run-01` and `run-03`.

Implemented safeguards:

- `src/lsd_thesis/data/ds003059/` exposes explicit run normalization and rejects `run-02` unless `include_music=True`.
- `scripts/run_pipeline.py` exposes `--include-music`, `--runs`, and `--stage2-output-dir`.
- `--include-music` is restricted to the `stage2` command.
- `--include-music` refuses the legacy `results/stage_2` output directory, so the first music extraction cannot overwrite the current rest-only Stage 2 cache.
- Target YAML generation remains rest-target based; a cache containing `run-02` does not silently average Music into the legacy rest target semantics.

After explicit user approval, the safe extraction command is:

```powershell
uv run python scripts/run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 --stage2-output-dir results/setting_seed/run02_extraction/stage_2_music
```

This command may download missing run-02 data and run expensive NIfTI extraction. Do not run it without user approval.

Current local status after PASS 2B-0:

- Local `data/ds003059` contains rest files but no discovered `run-02` files.
- `results/stage_2/module_time_series` contains no `run-02` module arrays.
- Motion/confounds files were not found locally.
- Music-control analysis remains `blocked_missing_run_02`.

## 2026-05-14 Extraction Result

The first approved extraction attempt failed before download because the OpenNeuro GraphQL schema no longer exposes the old `DatasetFile.key` field. The query now requests `id` and aliases it to the internal `key` value used by the existing manifest traversal code.

Patched files:

- `src/lsd_thesis/data/ds003059/`
- `tests/test_ds003059_wrappers.py`

Extraction command rerun:

```powershell
.venv\Scripts\python.exe scripts\run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 --stage2-output-dir results\setting_seed\run02_extraction\stage_2_music
```

Outputs:

- local downloaded run-02 BOLD files: `30`
- module time-series arrays: `90`
- run-02 module time-series arrays: `30`
- non-legacy Stage 2 root: `results/setting_seed/run02_extraction/stage_2_music`
- extraction audit: `results/setting_seed/run02_extraction/data_audit/data_audit.json`

Audit summary:

- subjects: `15`
- sessions: `ses-LSD`, `ses-PLCB`
- runs: `run-01`, `run-02`, `run-03`
- music-eligible subjects after excluding `sub-003`, `sub-012`, and `sub-015`: `12`
- music-eligible run-02 subject/session files expected: `24`
- valid music-eligible run-02 module files: `24`
- run-02 analysis ready: `true`
- music-control status: `blocked_missing_motion_review`

Remaining blocker:

- Motion summaries are still unavailable, so music-control analyses can move to descriptive/scaffolded comparisons only if they keep this limitation explicit. Primary-fit or motion-sensitive claims remain blocked.
