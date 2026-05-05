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

- Add regression test that source directories are not ignored by Git.
- Split slow numerical tests from fast smoke tests if full suite remains slow.
- Add explicit no-NaN/no-Inf assertions for simulation and metrics if not already covered by existing shape/range tests.
- Add command-level smoke for `scripts/run_pipeline.py stage1` if runtime is acceptable.

## Current Phase Validation

- `cmd.exe /C "uv run pytest tests/test_repo_hygiene.py -q -o addopts="`: red step failed first with `ModuleNotFoundError: No module named 'lsd_thesis.repo_hygiene'`; green step passed after adding the helper.
- `cmd.exe /C "uv run pytest tests/test_imports.py tests/test_simulator.py tests/test_metrics.py tests/test_perturbation.py tests/test_repo_hygiene.py -q -o addopts="`: passed, 9 tests in 19.95s.
- `cmd.exe /C "uv run ruff check ."`: initially failed after `src/lsd_thesis/data/` became tracked, exposing import ordering, blank-line whitespace, and one unused variable in `src/lsd_thesis/data/ds003059.py`; passed after minimal lint fixes.
- `cmd.exe /C "uv run mypy src"`: passed, no issues in 26 source files.
- `cmd.exe /C "uv run pytest"`: passed, 99 tests, 84.84% coverage, 17 warnings in 47.56s.

## Warnings To Track

Full pytest currently emits numerical warnings in tests that intentionally exercise small or degenerate arrays:

- NumPy invalid-value warnings in correlation/eigenvalue fixture paths.
- scikit-learn KMeans convergence warnings for duplicate synthetic points.
- One divide-by-zero warning in normalized entropy on a degenerate label distribution.
- SciPy precision-loss warning for nearly identical paired values.

These warnings did not fail the test gate, but they support the roadmap recommendation to separate fast smoke tests from numerical edge-case tests and add clearer no-NaN/no-Inf validation where appropriate.
