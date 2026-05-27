# Thesis Upgrade Evidence Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add thesis-readiness gates, archive scaffolding, and stronger dashboard evidence panels for motion/confounds, canonical parcellation, ROCKET, external validation, receptor/structural integration, and reproducible archiving.

**Architecture:** Add a small evidence-status builder that reads existing artifacts and emits conservative gate states. Keep dashboard changes additive by adding a new payload key and panels. Add an archive manifest builder that hashes selected derived artifacts without bundling raw neuroimaging data.

**Tech Stack:** Python, FastAPI payload builder, static Jinja/HTML dashboard, Plotly, JSON/Markdown artifacts.

---

### Task 1: Thesis upgrade evidence status

**Files:**
- Create: `src/lsd_thesis/thesis_upgrade.py`
- Create: `scripts/build_thesis_upgrade_status.py`

- [ ] Build a pure status payload from existing artifact paths.
- [ ] Write JSON and Markdown summaries under `results/thesis_upgrade/`.
- [ ] Keep missing motion, receptor, structural, and external data as blockers rather than failed tests.

### Task 2: Reproducible archive manifest

**Files:**
- Create: `src/lsd_thesis/reproducible_archive.py`
- Create: `scripts/build_reproducible_archive.py`
- Create: `CITATION.cff`
- Create: `.zenodo.json`
- Create: `docs/ARCHIVE_POLICY.md`

- [ ] Hash selected source, config, docs, and derived result artifacts.
- [ ] Exclude raw data, local environments, private files, caches, and bulky array outputs.
- [ ] Record dataset identifiers and source-data provenance rather than republishing OpenNeuro raw files.

### Task 3: Dashboard and static Pages surface

**Files:**
- Modify: `src/lsd_thesis/web/app.py`
- Modify: `src/lsd_thesis/templates/dashboard.html`
- Modify: `scripts/build_github_pages.py`
- Modify: `docs/GITHUB_PAGES.md`

- [ ] Add `thesis_upgrade` payload.
- [ ] Add artifact links for thesis upgrade and archive manifests.
- [ ] Add Plotly readiness bar and ROCKET radar panels.
- [ ] Add public guardrails for static snapshot versus citable archive.

### Task 4: Public documentation

**Files:**
- Create: `docs/THESIS_READINESS_GATES.md`
- Modify: `README.md`
- Modify: `docs/open_source_demo.md`

- [ ] Explain which gates are thesis-ready, proxy-only, or blocked.
- [ ] Document the canonical Schaefer/Yeo target.
- [ ] Document how ROCKET becomes stronger without leaking.

### Task 5: Verification handoff

- [ ] Suggested checks after implementation: `uv run pytest --no-cov tests/test_web.py tests/test_github_pages.py`.
- [ ] Suggested generation commands: `uv run python scripts/build_thesis_upgrade_status.py` and `uv run python scripts/build_reproducible_archive.py`.
- [ ] Do not claim tests passed unless they were explicitly run.
