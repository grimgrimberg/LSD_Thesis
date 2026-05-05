# Test Report

## Environment

- Repository path: `/mnt/d/LSD_Thesis`.
- Windows path: `D:\LSD_Thesis`.
- Python via Windows uv: 3.13.13.
- Windows uv: 0.9.21.
- Linux-shell `uv`: unavailable on `PATH`; use `cmd.exe /C "uv ..."`.

## Planning Verification Already Performed

- `cmd.exe /C "uv run python --version"`: passed, Python 3.13.13.
- `cmd.exe /C "uv run pytest --collect-only -q -o addopts="`: passed, 98 tests collected.
- `cmd.exe /C "uv run pytest tests/test_imports.py tests/test_simulator.py tests/test_metrics.py tests/test_perturbation.py -q -o addopts="`: passed, 8 tests.
- `cmd.exe /C "uv run ruff check ."`: passed.
- `cmd.exe /C "uv run mypy src"`: passed, 25 source files.

## Coverage Areas Present

- Import smoke tests.
- Deterministic simulation and seed behavior.
- Effective coupling matrix behavior.
- Metric shape/range checks.
- Observable summaries.
- Multi-seed metric summaries.
- ds003059 manifest, atlas audit, target payloads, extraction error paths.
- Fitting, perturbation ranking, seed-panel robustness, ablation ranking.
- CLI dispatch.
- FastAPI dashboard payload and security checks.
- Publication report, HTML, PPTX, figure, and DOCX generation helpers.
- Training feature and benchmark helpers.

## Gaps To Close

- Add regression test that source directories are not ignored by Git. Completed in `tests/test_repo_hygiene.py`.
- Split slow numerical tests from fast smoke tests if full suite remains slow.
- Add explicit no-NaN/no-Inf assertions for simulation and metrics if not already covered by existing shape/range tests. Partially completed with degenerate metric and constant-window eigenvalue tests.
- Add command-level smoke for `scripts/run_pipeline.py stage1` if runtime is acceptable. Existing reporting tests cover Stage 1 generation in a temp path; full `run-everything` also completed.

## Current Phase Validation

- `cmd.exe /C "uv run pytest tests/test_repo_hygiene.py -q -o addopts="`: red step failed first with `ModuleNotFoundError: No module named 'lsd_thesis.repo_hygiene'`; green step passed after adding the helper.
- `cmd.exe /C "uv run pytest tests/test_imports.py tests/test_simulator.py tests/test_metrics.py tests/test_perturbation.py tests/test_repo_hygiene.py -q -o addopts="`: passed, 9 tests in 19.95s.
- `cmd.exe /C "uv run ruff check ."`: initially failed after `src/lsd_thesis/data/` became tracked, exposing import ordering, blank-line whitespace, and one unused variable in `src/lsd_thesis/data/ds003059.py`; passed after minimal lint fixes.
- `cmd.exe /C "uv run mypy src"`: passed, no issues in 26 source files.
- `cmd.exe /C "uv run pytest"`: passed, 99 tests, 84.84% coverage, 17 warnings in 47.56s.

## Full Workflow Run - 2026-05-05

- `cmd.exe /C "uv run python scripts/run_pipeline.py run-everything"`: passed.
- Completed Stage 1, Stage 2, Stage 3, Stage 4, training window export, condition benchmark, and multitask benchmark.
- Condition benchmark summary: best model `temporal_cnn`, balanced accuracy mean `0.595`, ROC AUC mean `0.719`.
- Multitask benchmark summary: best classification model `multitask_temporal_cnn`, balanced accuracy `0.62`; best regression model `hist_gradient_multitask`, eigen R2 `0.2616183098354279`.
- `cmd.exe /C "uv run python scripts/render_publication_figures.py --all"`: passed and rendered the current publication figure bundle.
- `cmd.exe /C "uv run pytest tests/test_render_publication_figures_script.py -q -o addopts="`: passed, 2 tests.
- `cmd.exe /C "uv run python scripts/build_publication_package.py"`: passed and rebuilt `output/doc/` publication artifacts.

## No-NaN/No-Inf Hardening

- Red test: `tests/test_metrics.py::test_degenerate_time_series_metrics_stay_finite` failed on NaN FC values and entropy warnings.
- Red test: `tests/test_condition_models.py::test_constant_window_eigenvalue_targets_are_finite_without_runtime_warnings` failed on RuntimeWarnings from constant-window correlations.
- Fix: added finite `safe_correlation_matrix`, reused it for metrics and condition-model FC features, and guarded the single-state entropy denominator.
- Green verification: both new tests passed.

## Final Validation After Full Workflow Follow-Up

- `cmd.exe /C "uv run pytest tests/test_metrics.py tests/test_condition_models.py tests/test_render_publication_figures_script.py -q -o addopts="`: passed, 9 tests in 128.51s.
- `cmd.exe /C "uv run ruff check ."`: passed.
- `cmd.exe /C "uv run mypy src"`: passed, no issues in 26 source files.
- `cmd.exe /C "uv run pytest"`: passed, 103 tests, 84.88% coverage, 3 warnings in 175.87s.

## Warnings To Track

Full pytest currently emits three numerical warnings in tests that intentionally exercise small or degenerate empirical fixtures:

- SciPy precision-loss warning for nearly identical paired values.
- NumPy degrees-of-freedom and invalid-divide warnings in an empirical viewer fixture with a single grouped row.

The previous degenerate FC/entropy warnings are resolved by `safe_correlation_matrix` and single-state entropy guarding.
