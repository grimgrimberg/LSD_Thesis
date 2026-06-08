# Codebase Audit

## 1. Executive Summary

Implemented: this is a functioning Python research prototype with simulation, empirical target extraction, fitting, perturbation ranking, ablation, dashboard, tests, and publication helpers. The biggest immediate engineering risk was Git safety: there was no baseline commit, and the old `data/` ignore rule excluded `src/lsd_thesis/data/`. That has been fixed and committed in baseline `75218fc`.

## 2. Architecture Overview

The architecture is stage-oriented: configs feed graph/regime objects, simulator output feeds metrics, empirical ds003059 summaries feed targets, fitting calibrates sober dynamics, perturbation/ablation score model deltas, and reporting/dashboard/publication layers expose outputs.

## 3. Main Modules And Responsibilities

- `src/lsd_thesis/core.py`: Pydantic config/result models and module constants.
- `src/lsd_thesis/graph.py`: YAML graph loading.
- `src/lsd_thesis/simulator.py`: stochastic integration loop.
- `src/lsd_thesis/metrics.py`: FC, entropy, switching, metastability, and observable proxies.
- `src/lsd_thesis/data/ds003059.py`: OpenNeuro manifest, download, extraction, atlas audit, empirical targets.
- `src/lsd_thesis/fit.py`: sober random-search fitting.
- `src/lsd_thesis/perturbation.py`: mechanism operators and ranking.
- `src/lsd_thesis/ablation.py`: single and pairwise ablations.
- `src/lsd_thesis/web/app.py`: dashboard API and artifact serving.

## 4. Data Flow

Implemented: raw ds003059 files under `/data/` are reduced to module time series under generated result caches. Summaries become `results/stage_2/empirical_sober_targets.yaml` and `results/stage_2/empirical_perturbation_targets.yaml`.

## 5. Model/Dynamics Flow

Implemented: `scripts/run_pipeline.py` dispatches stages. Stage 1 runs baseline and perturbed configs. Stage 2 fits the sober baseline. Stage 3 applies perturbation mechanisms over strengths. Stage 4 evaluates single and pairwise mechanism combinations.

## 6. Visualization Flow

Implemented: Plotly HTML figures are written under `results/stage_*/figures/`, empirical viewer JSON is generated under `results/stage_2/empirical_viewer/`, and publication PNGs are generated under `output/doc/figures/`. These are generated artifacts, not baseline source.

## 7. CLI/UI Flow

Implemented: `scripts/run_pipeline.py` is the primary CLI. `scripts/run_dashboard.py` starts FastAPI. The dashboard template lives in `src/lsd_thesis/templates/dashboard.html`; static fallback links live in `web/index.html`.

## 8. Dependency Audit

Implemented: Python dependencies are explicit in `pyproject.toml`; `uv.lock` is present. Node deck tooling is isolated under `tools/pptx/`.

## 9. Security/Privacy Audit

Implemented: no credential files were found by filename search. Raw public neuroimaging data is excluded from Git. Local agent state, virtualenvs, generated output, and temp folders are ignored.

## 10. Performance Audit

Present but broken: full test collection is slow, partly due KMeans/numerical tests. Stage 2 raw extraction can be expensive because it downloads/processes several GB of NIfTI data.

## 11. Reproducibility Audit

Implemented: fixed seeds exist in configs and tests. Present but broken: before baseline `75218fc`, stage provenance had weak Git history. Proposed: record commit hashes in all regenerated stage summaries.

## 12. Testing Audit

Implemented: 98 tests collect. Smoke tests, Ruff, and mypy passed during planning. Proposed: add a Git hygiene regression test for ignored source directories.

## 13. Documentation Audit

Implemented: README, SPEC, methods, limitations, stage reports, and older plans exist. Proposed and implemented in this phase: root-level audit docs for thesis review and agent continuation.

## 14. Dead Code / Duplicate Code

Inferred: scratch folders and generated reports are not code. No source deletions are recommended yet. Generated probe outputs under `results/stage_2_probe*` should remain ignored unless intentionally promoted.

## 15. Biggest Correctness Risks

- KMeans-derived metrics may be seed/window sensitive.
- Stage 1 perturbed config does not improve all intended proxies.
- Random-search fitting may overfit stochastic trajectories without seed-panel rescoring.
- Existing summary files can become stale after code changes.

## 16. Biggest Research-Validity Risks

- Overclaiming biological mechanism from surrogate knobs.
- Treating the Harvard-Oxford 8-module proxy as canonical.
- Hiding sign conflicts in empirical deltas.
- Treating subjective or receptor-level claims as supported.

## 17. Highest-Leverage Improvements

- Add source ignore regression test.
- Make command/docs exact and environment-specific.
- Promote seed-panel robustness from optional to standard reporting.
- Add atlas sensitivity or at least stronger atlas limitations.

## 18. Recommended Rewrite/Refactor Phases

1. Safety/docs/test hardening.
2. Metric speed and slow-test marking.
3. Reproducibility packaging.
4. Atlas sensitivity.
5. Model perturbation redesign only after metrics and claims are locked.

## 19. Safely Automatic

- Documentation, command normalization, tests, `.gitignore`, small import/typing/logging fixes, and reproducibility scripts.

## 20. Requires Confirmation

- Deleting large files.
- Replacing architecture.
- Changing thesis claims.
- Changing dataset formats.
- Adding heavy dependencies.
- Removing notebooks or generated outputs that may be needed for submission.
