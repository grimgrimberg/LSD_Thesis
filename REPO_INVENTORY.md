# Repository Inventory

## Directory Summary

- `src/lsd_thesis/`: main Python package for configs, graph loading, simulator, metrics, fitting, perturbation search, ablation, reporting, publication helpers, training features, and dashboard API.
- `src/lsd_thesis/data/`: ds003059/OpenNeuro bridge, target payloads, empirical viewer cache generation. This is source code and must remain tracked.
- `configs/`: YAML graph, regime, and target definitions.
- `scripts/`: command entrypoints for the staged pipeline, dashboard, training export, benchmarks, and publication package.
- `tests/`: 98 collected pytest tests across simulator, metrics, fitting, perturbation, web, publication, ds003059, training, and error paths.
- `docs/`: existing architecture, methods, limitations, stage reports, experiment log, and older implementation plans/specs.
- `results/`: generated summaries and caches. Lean Git policy tracks small JSON/YAML summaries, not figures or numerical arrays.
- `data/`: raw ds003059 downloads, about 9.6 GB locally, ignored by Git.
- `output/`, `tmp/`, `tmp_*`: generated reports, previews, scratch artifacts, ignored by Git.
- `tools/pptx/`: Node/PptxGenJS defense deck generator and helper source.
- `web/`: static fallback HTML page for generated figures.

## Detected Languages And Frameworks

- Python 3.13 package using NumPy, SciPy, pandas, scikit-learn, Plotly, NetworkX, Pydantic, FastAPI, Jinja2, nibabel, nilearn, python-docx, and pytest.
- JavaScript/Node helper tooling under `tools/pptx/` using PptxGenJS.
- HTML/Jinja templates for dashboard, microsite, and defense presentation.
- YAML configs for graph, regimes, and targets.

## Package And Dependency Files

- `pyproject.toml`: Python package metadata, dependencies, pytest/ruff/mypy config.
- `uv.lock`: locked Python dependency set.
- `tools/pptx/package.json` and `tools/pptx/package-lock.json`: deck generation dependencies.

## Main Entry Points

- `scripts/run_pipeline.py`: primary staged workflow with `stage1`, `stage2`, `stage3`, `stage4`, `run-all`, `run-everything`, and serve variants.
- `scripts/run_dashboard.py`: FastAPI dashboard server.
- `scripts/export_training_dataset.py`: ds003059 window export.
- `scripts/benchmark_condition_models.py`: local condition classifiers.
- `scripts/benchmark_multitask_models.py`: condition plus FC eigenspectrum benchmark.
- `scripts/build_publication_package.py`: publication report, microsite, figures, and defense assets.

## Tests Found

- 98 tests collect under `tests/`.
- Focus areas: deterministic simulation, metrics, ds003059 extraction helpers, fitting, perturbation ranking, seed panels, ablations, CLI, dashboard API, publication HTML/PPTX/figures/content, docx export, and training feature extraction.

## Docs Found

- Conceptual docs: `README.md`, `SPEC.md`, `docs/methods.md`, `docs/limitations.md`, `docs/audit_repo_map.md`.
- Stage reports: `docs/stage_reports/stage_1.md` through `stage_4.md`.
- Prior design/plan docs: `docs/superpowers/specs/` and `docs/superpowers/plans/`.
- Operational docs: `docs/cloud_training.md`, `docs/experiment_log.md`, `docs/next_steps.md`.

## Generated/Cache Folders

- Raw data: `/data/`.
- Generated result figures and arrays: `results/**/figures/`, `results/**/module_time_series/`, `results/**/*.npy`, `results/**/*.npz`, `results/**/*.csv`.
- Publication outputs: `/output/`.
- Local caches: `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `__pycache__/`.
- Local agent state: `.codex/`, `.superpowers/`, `.agents/`.

## Suspicious, Dead, Or Duplicate Files

- `ruff_output.txt`: generated lint output, ignored after baseline policy update.
- `tmp/`, `tmp_review_figures*`: scratch and review outputs, ignored.
- `output/doc/~$esis_report_revised.docx`: temporary Office lock file, ignored by `/output/`.
- Stage 2 probe result directories are generated exploratory artifacts and not part of the canonical pipeline.

## Likely Main Execution Paths

- Fast local smoke: `uv run pytest tests/test_imports.py tests/test_simulator.py tests/test_metrics.py tests/test_perturbation.py -q -o addopts=`.
- Stage workflow: `uv run python scripts/run_pipeline.py run-all`.
- Full local workflow: `uv run python scripts/run_pipeline.py run-everything`.
- Dashboard: `uv run python scripts/run_dashboard.py`.
- Publication package: `uv run python scripts/build_publication_package.py`.

## Likely Research/Model Execution Paths

- Stage 1: synthetic graph and sober/perturbed simulation.
- Stage 2: ds003059 target extraction and sober fitting.
- Stage 3: perturbation ranking against LSD-minus-placebo deltas.
- Stage 4: single and pairwise ablation study.
- Training bridge: window export followed by condition and multitask benchmarks.
