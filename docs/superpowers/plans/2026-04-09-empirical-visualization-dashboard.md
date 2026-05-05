# Empirical Visualization Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an empirical viewer that connects raw ds003059 fMRI previews to 8-module traces, FC summaries, windowed comparisons, and a report/gallery inside the existing dashboard.

**Architecture:** Extend Stage 2 preprocessing to emit a cached empirical viewer dataset, add FastAPI payload loaders/endpoints for group and subject views, and expand the existing single-page dashboard with an empirical explorer and gallery section. Keep raw previews precomputed and downsampled.

**Tech Stack:** Python 3.13, NumPy, nibabel, Plotly, FastAPI, pytest, ruff, mypy, uv

---

### Task 1: Red tests for empirical viewer data builders

**Files:**
- Create: `D:\LSD_Thesis\tests\test_empirical_viewer.py`
- Modify: `D:\LSD_Thesis\tests\test_web.py`
- Test: `D:\LSD_Thesis\tests\test_empirical_viewer.py`
- Test: `D:\LSD_Thesis\tests\test_web.py`

- [ ] Add failing tests for per-run empirical viewer payload generation from a small synthetic 4D NIfTI and module time series.
- [ ] Add a failing test for group/subject viewer cache structure and window metadata.
- [ ] Add a failing web-payload test asserting the dashboard includes empirical overview and gallery metadata.
- [ ] Run `uv run pytest tests/test_empirical_viewer.py tests/test_web.py -v` and confirm failure.

### Task 2: Backend empirical viewer cache

**Files:**
- Create: `D:\LSD_Thesis\src\lsd_thesis\data\empirical_viewer.py`
- Modify: `D:\LSD_Thesis\src\lsd_thesis\data\ds003059.py`
- Test: `D:\LSD_Thesis\tests\test_empirical_viewer.py`

- [ ] Implement minimal typed helpers for normalized windows, downsampled raw slice previews, per-window FC summaries, and run-level metric snapshots.
- [ ] Implement group aggregation and subject-view serialization helpers.
- [ ] Extend Stage 2 empirical generation to build and persist the viewer cache under `results/stage_2/empirical_viewer/`.
- [ ] Re-run `uv run pytest tests/test_empirical_viewer.py -v` and confirm pass.

### Task 3: Empirical gallery figures

**Files:**
- Modify: `D:\LSD_Thesis\src\lsd_thesis\fit.py`
- Modify: `D:\LSD_Thesis\src\lsd_thesis\data\empirical_viewer.py`
- Test: `D:\LSD_Thesis\tests\test_fit.py`

- [ ] Generate saved empirical HTML figures for group traces, condition FC heatmaps, FC deltas, and metric deltas.
- [ ] Include gallery metadata in the Stage 2 summary so the dashboard can render links cleanly.
- [ ] Re-run targeted tests that cover Stage 2 summaries.

### Task 4: Dashboard API integration

**Files:**
- Modify: `D:\LSD_Thesis\src\lsd_thesis\web\app.py`
- Modify: `D:\LSD_Thesis\tests\test_web.py`

- [ ] Add typed loader logic for empirical viewer cache files.
- [ ] Expose a dashboard overview payload and a subject/run/window empirical detail endpoint.
- [ ] Re-run `uv run pytest tests/test_web.py -v` and confirm pass.

### Task 5: Dashboard UI

**Files:**
- Modify: `D:\LSD_Thesis\src\lsd_thesis\templates\dashboard.html`

- [ ] Add an empirical explorer section with:
- [ ] group overview cards and plots
- [ ] subject picker and run picker
- [ ] window slider
- [ ] raw preview panel
- [ ] module trace panel with window highlight
- [ ] FC comparison and delta heatmaps
- [ ] plain-English metric interpretation block
- [ ] gallery/report links
- [ ] Keep the existing model explorer intact.

### Task 6: Documentation and verification

**Files:**
- Modify: `D:\LSD_Thesis\README.md`
- Modify: `D:\LSD_Thesis\docs\stage_reports\stage_2.md`

- [ ] Update docs so a new user can understand what the empirical viewer shows and how to use it.
- [ ] Run `uv run pytest -v`.
- [ ] Run `uv run ruff check .`.
- [ ] Run `uv run mypy src`.
- [ ] Run `uv run python scripts/run_pipeline.py stage2`.
- [ ] Run `uv run python scripts/run_dashboard.py` and validate the new dashboard flow in a browser.
