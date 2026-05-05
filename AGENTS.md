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
