# AGENTS.md

## Project Identity

This repository hosts two complementary components:

1. **Surrogate model** — A transparent 8-module stochastic graph model that
   produces psychedelic-like macro-dynamic signatures for mechanism ranking.
2. **Prior-art landscape** — A structured reproducibility inventory of all known
   ds003059-based analyses from the literature (12 analysis families).

### Preferred Framing

- surrogate model, macro-scale analogue
- altered-state-inspired perturbation
- graph-modulated dynamics
- prior-art reproducibility landscape

### Avoid

- claims about subjective experience
- claims about receptor-level realism
- anthropomorphic language ("the model is tripping")
- presenting prior-art wrappers as original analysis

---

## Working Loops

### RALPH (every increment)

1. **R**esearch repo, environment, constraints
2. **A**ssess the simplest defensible path
3. **L**og assumptions, risks, open questions
4. **P**atch/build the next increment
5. **H**andoff a concise summary

### BRATING (empirical work)

1. **B**enchmark against baseline
2. **R**ank candidate mechanisms
3. **A**blate one mechanism at a time
4. **T**est quantitatively
5. **I**nterpret macro-level plausibility
6. **N**ote failure modes
7. **G**uardrail claims

---

## Directory Structure

```
src/lsd_thesis/         Core Python package
prior_art/              ds003059 literature landscape (runbooks, inventory)
prior_art/repositories/ Cloned external repos (gitignored)
scripts/                Pipeline and utility scripts
configs/                YAML configuration files
tests/                  Test suite
results/                Generated outputs (gitignored binaries)
docs/                   Documentation
docs/reference/         Archived historical project docs
```

---

## Repo Commands

```bash
# Install
uv sync --extra dev

# Test
uv run pytest                    # Full suite
uv run pytest -m "not slow"      # Fast tests only

# Lint and type-check
uv run ruff check .
uv run mypy src

# Pipeline
uv run python scripts/run_pipeline.py run-all
uv run python scripts/run_dynamic_mechanism_ranking.py

# Dashboard
uv run python scripts/run_dashboard.py

# Exports
uv run python scripts/export_training_dataset.py
uv run python scripts/export_dynamic_mechanism_tables.py
```

---

## Read First

1. `README.md` — Project overview and quick start
2. `SPEC.md` — Model equations and stage definitions
3. `ARCHITECTURE.md` — System architecture and data flow
4. `prior_art/README.md` — Prior-art landscape overview
5. `prior_art/code_inventory.md` — Master analysis inventory

---

## Engineering Rules

- Work in small, verifiable steps
- Use test-first for production code changes when practical
- Keep Python typed where reasonable
- Save every generated figure and report to disk
- Keep configs explicit; no unexplained magic constants
- Every pipeline stage must produce: figures, logs, markdown summary, dashboard data

---

## Scientific Rules

- Keep all claims at macro-dynamics / proxy level
- Treat switching barriers, metastability, and integration metrics as model-level
  proxies, not biological ground truth
- Be explicit about what is fitted quantitatively vs matched qualitatively
- Prefer cached `ds003059` empirical targets in `results/stage_2/` once generated
- Treat the 8-module anatomical extraction as a transparent proxy, not a canonical
  network definition
- Separate: implemented facts, hypotheses, analogies, assumptions, and speculation
- Report sign conflicts and model failures directly
- Do not strengthen thesis claims without explicit user confirmation

---

## Safe Editing Rules

- Work only inside this repository unless explicitly approved
- Create or confirm a Git checkpoint before meaningful edits
- Do not rewrite Git history
- Do not delete raw data, generated outputs, or notebooks without confirmation
- Do not commit: `/data/`, `/output/`, `.venv/`, `tmp/`, `node_modules/`,
  `prior_art/repositories/`, NPY/NPZ caches, generated figures, credentials
- Treat artifacts by tier:
  - **Tier A** — Curated evidence: may be tracked
  - **Tier B** — Generated outputs: ignored/regenerable
  - **Tier C** — Raw data, secrets, machine-local state: never committed

---

## No-Secret Policy

- Do not expose, print, edit, move, delete, or commit `.env` files, API keys,
  private tokens, SSH keys, cloud credentials, or machine-local secrets
- If a task needs authentication, stop and ask

---

## Prior-Art Rules

- Do not modify cloned repositories in `prior_art/repositories/`
- Wrapper scripts go in `prior_art/scripts/`, not inside cloned repos
- Always record commit hashes for cloned repositories
- Clearly separate verified facts (from repo inspection) from inferences (from papers)
- Mark code availability honestly: public, partial, unavailable, or author-only
