# Whole-Brain Surrogate MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible surrogate-model repository with four staged outputs, empirical summary-statistics hooks, and a lightweight dashboard.

**Architecture:** Use a typed Python package with config-driven graph dynamics, explicit feature extraction, and stage-wise reporting. Keep empirical ingestion summary-first but stable enough to swap in raw OpenNeuro-derived features later.

**Tech Stack:** Python 3.13, NumPy, SciPy, pandas, Plotly, scikit-learn, FastAPI, pytest, ruff, mypy, uv

---

### Task 1: Repository Scaffold

**Files:**
- Create: `D:\LSD_Thesis\pyproject.toml`
- Create: `D:\LSD_Thesis\src\lsd_thesis\__init__.py`
- Create: `D:\LSD_Thesis\README.md`
- Create: `D:\LSD_Thesis\AGENTS.md`
- Test: `D:\LSD_Thesis\tests\test_imports.py`

- [ ] Write the failing import test.
- [ ] Run `uv run pytest tests/test_imports.py -v` and confirm failure.
- [ ] Add the package scaffold.
- [ ] Re-run the import test and confirm pass.

### Task 2: Stage 1 Simulator

**Files:**
- Create: `D:\LSD_Thesis\src\lsd_thesis\core.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\graph.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\simulator.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\metrics.py`
- Test: `D:\LSD_Thesis\tests\test_simulator.py`
- Test: `D:\LSD_Thesis\tests\test_metrics.py`

- [ ] Write failing tests for deterministic seeded simulation and metric shape assumptions.
- [ ] Run those tests and confirm failure.
- [ ] Implement the minimal simulator and metrics.
- [ ] Re-run tests and confirm pass.

### Task 3: Stage Reports and Plotting

**Files:**
- Create: `D:\LSD_Thesis\src\lsd_thesis\reporting.py`
- Create: `D:\LSD_Thesis\docs\stage_reports\stage_1.md`
- Test: `D:\LSD_Thesis\tests\test_reporting.py`

- [ ] Write a failing test for figure/report payload generation.
- [ ] Run the reporting test and confirm failure.
- [ ] Implement report generation and figure persistence.
- [ ] Re-run tests and confirm pass.

### Task 4: Sober Fit and Empirical Hooks

**Files:**
- Create: `D:\LSD_Thesis\src\lsd_thesis\data\openneuro.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\data\targets.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\fit.py`
- Create: `D:\LSD_Thesis\docs\stage_reports\stage_2.md`
- Test: `D:\LSD_Thesis\tests\test_fit.py`

- [ ] Write failing tests for target loading and sober-objective consistency.
- [ ] Run those tests and confirm failure.
- [ ] Implement the minimal summary-statistics-first sober fit path.
- [ ] Re-run tests and confirm pass.

### Task 5: Perturbation Search and Ablation

**Files:**
- Create: `D:\LSD_Thesis\src\lsd_thesis\perturbation.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\ablation.py`
- Create: `D:\LSD_Thesis\docs\stage_reports\stage_3.md`
- Create: `D:\LSD_Thesis\docs\stage_reports\stage_4.md`
- Test: `D:\LSD_Thesis\tests\test_perturbation.py`

- [ ] Write failing tests for mechanism application and ablation ranking.
- [ ] Run those tests and confirm failure.
- [ ] Implement mechanism search and ablation ranking.
- [ ] Re-run tests and confirm pass.

### Task 6: CLI and Dashboard

**Files:**
- Create: `D:\LSD_Thesis\src\lsd_thesis\cli.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\web\app.py`
- Create: `D:\LSD_Thesis\src\lsd_thesis\templates\dashboard.html`
- Test: `D:\LSD_Thesis\tests\test_cli.py`

- [ ] Write failing tests for CLI dispatch and dashboard data payload generation.
- [ ] Run those tests and confirm failure.
- [ ] Implement the minimal CLI and dashboard server.
- [ ] Re-run tests and confirm pass.

