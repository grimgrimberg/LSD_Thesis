# Audit Repo Map

This map records the current Plan A target: a credible professor demo for a transparent macro-dynamics surrogate, not a mechanistic claim about LSD, receptors, or subjective experience.

## Defensible Story

The project is strongest when framed as:

- a transparent 8-module stochastic surrogate
- a graph-modulated macro-scale analogue
- a bridge from public ds003059 resting-state derivatives to coarse summary observables
- a mismatch analysis that shows where simple perturbation hypotheses fail

The project is weakest if it claims to reproduce psychedelic brain mechanisms. The empirical extraction and model deltas do not currently justify that claim.

## Repository Structure

| Path | Role | Audit Notes |
|---|---|---|
| `src/lsd_thesis/simulator.py` | Stochastic 8-module simulator | Core surrogate dynamics; keep claims at model level. |
| `src/lsd_thesis/metrics.py` | Observable summaries | Several dynamic proxies depend on KMeans state labels. Treat as metric definitions, not biology. |
| `src/lsd_thesis/fit/` | Sober-regime search | Candidate scoring uses stochastic simulations; top candidates need fixed multi-seed evaluation. |
| `src/lsd_thesis/perturbation.py` | Perturbation operators | Four scalar operators; use as hypothesis toggles only. |
| `src/lsd_thesis/data/ds003059/` | OpenNeuro ds003059 extraction | Real-data bridge; Harvard-Oxford macro mapping is transparent but coarse and overlapping. |
| `src/lsd_thesis/web/app.py` | FastAPI dashboard API | Local demo surface and artifact serving. |
| `src/lsd_thesis/templates/base.html` and `src/lsd_thesis/templates/pages/` | Dashboard UI | Multipage professor-facing visual surface. |
| `scripts/run_pipeline.py` | Stage runner | Primary staged workflow. |
| `scripts/run_dashboard.py` | Dashboard runner | Local viewer entry point. |
| `scripts/export_training_dataset.py` | Training-window export | Later benchmark/DNN bridge; not needed for Plan A. |
| `configs/` | Graph, regime, and target YAML | Literature-style target file should be contrasted with ds003059 target signs. |
| `results/` | Generated outputs and caches | Useful local artifacts; provenance remains weak until baseline commit/hash discipline exists. |
| `docs/stage_reports/` | Stage summaries | Must expose mismatch, not hide it. |
| `tests/` | Unit and smoke tests | Full collection is currently slow; keep a fast focused command documented. |

## Empirical Target Cross-Check

Current ds003059 target deltas come from 15 paired subjects under the coarse 8-module extraction.

| Metric | ds003059 delta | Literature-style target | Sign Status |
|---|---:|---:|---|
| `within_network_stability` | +0.066 | -0.300 | conflict |
| `cross_network_communication` | +0.074 | +0.250 | aligned |
| `thalamic_coupling` | +0.120 | +0.200 | aligned |
| `hierarchical_compression` | +0.054 | +0.200 | aligned |
| `entropy_diversity` | -0.002 | +0.250 | conflict |
| `switching_rate` | +0.012 | +0.400 | aligned but weak |
| `metastability_proxy` | -0.054 | +0.200 | conflict |
| `effective_barrier_proxy` | -0.149 | -0.250 | aligned |

The demo should lead with this table or a visual equivalent. It makes the work more defensible because it shows the empirical bridge and the failure modes in the same view.

## Atlas Mapping Audit

The current Harvard-Oxford proxy includes duplicate labels:

| Atlas | Label | Modules |
|---|---:|---|
| cortical | 31 | `visual`, `default_mode` |
| cortical | 42 | `auditory`, `sensorimotor` |

The label-image builder assigns modules in `MODULE_NAMES` order; later assignments overwrite earlier overlapping voxels. This is not automatically wrong for a transparent proxy, but it must be reported and ideally paired with voxel counts in the next stage.

## Current Validation Reality

Fast checks known to be useful:

```bash
uv run ruff check .
uv run mypy src
uv run pytest tests/test_ds003059_wrappers.py tests/test_dynamic_mechanism.py tests/test_figure_payload.py tests/test_metrics.py tests/test_web_security.py -q -o addopts=
```

Full pytest collection and metric-heavy tests are currently too slow for fast iteration on this machine. Metric tests should eventually be split into fast synthetic checks and explicitly marked slow numerical checks.

## Provenance Risks

- Stage summaries report an unborn git branch and no commit hash.
- Generated outputs live under `results/` and `output/`; some are local cache-dependent.
- The lockfile should be treated as part of the reproducibility story.
- Submission packages should either include required generated artifacts or document exact regeneration commands.

## Source Anchors

- OpenNeuro ds003059: `https://openneuro.org/datasets/ds003059/versions/1.0.0`
- Carhart-Harris et al. 2016 PNAS: `https://pmc.ncbi.nlm.nih.gov/articles/PMC4855588/`
- Tagliazucchi et al. 2016: `https://pubmed.ncbi.nlm.nih.gov/27085214/`
- Lebedev et al. 2016: `https://pubmed.ncbi.nlm.nih.gov/27151536/`
- Psychedelic resting-state review: `https://www.sciencedirect.com/science/article/pii/S0149763422001786`
- Network control theory paper: `https://www.nature.com/articles/s41467-022-33578-1`
- Whole-brain entropy model: `https://pubmed.ncbi.nlm.nih.gov/37069186/`
- OpenNeuro ds006072 psilocybin PFM: `https://openneuro.org/datasets/ds006072`
