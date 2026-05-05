# Defense PPTX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an editable `.pptx` defense deck to the publication package, derived from the long-form thesis report.

**Architecture:** Build a typed Python slide spec from the existing long-form report parser, then generate the PowerPoint deck with a local PptxGenJS script that reuses saved figures. Wire the resulting `.pptx` into the existing publication package and dashboard artifact surface.

**Tech Stack:** Python, pytest, Jinja-backed report content, Node.js, PptxGenJS

---

### Task 1: Add defense slide-spec builder

**Files:**
- Create: `src/lsd_thesis/publication_pptx.py`
- Test: `tests/test_publication_pptx.py`

- [ ] **Step 1: Write failing tests for grouped defense slide generation**
- [ ] **Step 2: Run the new test file and confirm failure**
- [ ] **Step 3: Implement the minimal slide-spec builder from the long-form report**
- [ ] **Step 4: Re-run the slide-spec tests and confirm pass**

### Task 2: Add PptxGenJS deck generator

**Files:**
- Create: `tools/pptx/package.json`
- Create: `tools/pptx/build_defense_deck.mjs`
- Create: `tools/pptx/pptxgenjs_helpers/*`

- [ ] **Step 1: Add the local Node package and generator script**
- [ ] **Step 2: Install the Node dependency needed for deck generation**
- [ ] **Step 3: Generate a `.pptx` from a sample slide spec**
- [ ] **Step 4: Verify the generated file exists and is non-empty**

### Task 3: Wire deck build into the publication package

**Files:**
- Modify: `scripts/build_publication_package.py`
- Modify: `src/lsd_thesis/web/app.py`
- Test: `tests/test_web.py`

- [ ] **Step 1: Add package wiring to emit the `.pptx` path**
- [ ] **Step 2: Add dashboard artifact exposure for the deck**
- [ ] **Step 3: Run focused package and web tests**

### Task 4: Build and verify final artifacts

**Files:**
- Output: `output/doc/defense_presentation.pptx`
- Output: `output/doc/defense_presentation.html`
- Output: `output/doc/thesis_report_revised.*`

- [ ] **Step 1: Run the package build**
- [ ] **Step 2: Confirm the `.pptx` exists and has content**
- [ ] **Step 3: Run focused pytest, mypy, and ruff checks**
