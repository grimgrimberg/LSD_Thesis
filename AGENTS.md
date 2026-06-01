# AGENTS.md

## Project Intent

This repository hosts a transparent surrogate model of psychedelic-like macro-dynamics. It is not a receptor model, not a subjective-consciousness model, and not a simulator of an actual LSD or psilocybin experience.

Preferred framing:
- surrogate model
- macro-scale analogue
- altered-state-inspired perturbation
- graph-modulated dynamics

Avoid:
- claims about subjective experience
- claims about receptor-level realism
- anthropomorphic language such as "the model is tripping"

## Working Style

Use the RALPH loop on every increment:
1. Research repo/environment/constraints.
2. Assess the simplest defensible path.
3. Log assumptions, risks, and open questions.
4. Patch/build the next increment.
5. Handoff a concise summary before moving on.

Use the BRATING loop on empirical work:
1. Benchmark against baseline.
2. Rank candidate perturbation mechanisms.
3. Ablate one mechanism at a time.
4. Test quantitatively.
5. Interpret macro-level plausibility carefully.
6. Note failure modes.
7. Guardrail claims.

## Engineering Rules

- Work in small verifiable steps.
- Use test-first for production code changes whenever practical.
- Keep Python typed where reasonable.
- Save every generated figure and report to disk.
- Keep configs explicit; no unexplained magic constants.
- Every stage must produce:
  - figures
  - logs
  - markdown summary
  - runnable dashboard updates

## Scientific Rules

- Keep all claims at macro-dynamics level.
- Treat switching barriers and metastability as model-level proxies, not biological ground truth.
- Be explicit about what is fitted quantitatively vs matched qualitatively.
- Prefer the cached `ds003059` empirical targets in `results/stage_2/` once they have been generated.
- Treat the current 8-module anatomical extraction as a transparent proxy, not a canonical network definition.

## Repo Commands

- Install: `uv sync --extra dev`
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Type check: `uv run mypy src`
- Run all stages: `uv run python scripts/run_pipeline.py run-all`
- Launch dashboard: `uv run python scripts/run_dashboard.py`
- Export training windows: `uv run python scripts/export_training_dataset.py`

## Docs To Read First

1. `EXECUTIVE_SUMMARY.md`
2. `GOAL.md`
3. `THESIS_CONCEPT_AUDIT.md`
4. `AUDIT.md`
5. `ARCHITECTURE.md`
6. `COMMANDS.md`
7. `METRICS.md`
8. `NEXT_STEPS.md`

## Safe Editing Rules

- Work only inside this repository unless explicitly approved.
- Create or confirm a Git checkpoint before meaningful edits.
- Do not rewrite Git history.
- Do not delete raw data, generated outputs, notebooks, or large artifacts without confirmation.
- Do not commit `/data/`, `/output/`, `.venv/`, `tmp/`, `.codex/`, `.superpowers/`, `node_modules/`, NPY/NPZ caches, generated figures, or credential-like files.
- Treat artifacts by tier: Tier A curated evidence may be tracked; Tier B generated outputs are ignored/regenerable; Tier C raw data, secrets, and machine-local state must never be committed.
- Keep `src/lsd_thesis/data/` tracked; it is source code, not raw data.

## No-Secret Policy

- Do not expose, print, edit, move, delete, or commit `.env` files, API keys, private tokens, SSH keys, cloud credentials, or machine-local secrets.
- If a task needs authentication, stop and ask.

## Research Honesty Policy

- Separate implemented facts, hypotheses, analogies, assumptions, and speculation.
- Use "proxy" for entropy-like, metastability, switching-barrier, and integration metrics unless empirical validation is shown.
- Report sign conflicts and model failures directly.
- Do not strengthen thesis claims without explicit user confirmation.

## Preferred Coding Style

- Keep Python typed where practical.
- Prefer small, explicit functions and config-driven experiments.
- Add tests before production behavior changes.
- Keep generated outputs organized under `results/` or `output/`.
- Avoid magical constants; document research constants in configs or metric docs.
