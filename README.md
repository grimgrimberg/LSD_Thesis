# LSD Thesis — Macro-Dynamic Surrogate Model & Prior-Art Landscape

A transparent, explainable framework for ranking control-theoretic and graph-dynamic
surrogate mechanisms against paired psychedelic fMRI macro-dynamic evidence.
This repository contains two complementary components: a stochastic surrogate model
of altered-state-inspired brain dynamics, and a comprehensive reproducibility landscape
of all known ds003059-based analyses from the literature.

> **Framing note:** This is a surrogate model and macro-scale analogue, not a receptor
> model or subjective-experience simulator. All metrics are model-level proxies.

---

## Quick Start

```bash
# Install (requires Python ≥3.13 and uv)
uv sync --extra dev

# Run tests
uv run pytest

# Run the full pipeline (stages 1–4)
uv run python scripts/run_pipeline.py run-all

# Launch the interactive dashboard
uv run python scripts/run_dashboard.py

# Run dynamic mechanism ranking (A+B+C+D+E)
uv run python scripts/run_dynamic_mechanism_ranking.py

# Lint and type-check
uv run ruff check .
uv run mypy src
```

---

## Project Structure

```
├── src/lsd_thesis/          # Core Python package
│   ├── core.py              #   Pydantic config/result models
│   ├── simulator.py         #   Stochastic integration loop
│   ├── metrics.py           #   Proxy observable computation
│   ├── fit/                 #   Sober regime fitting
│   ├── perturbation.py      #   Mechanism operators and ranking
│   ├── ablation.py          #   Ablation studies
│   ├── dynamic_mechanism/   #   A+B+C+D+E mechanism ranking
│   ├── dynamic_robustness.py#   Dynamic mechanism robustness helpers
│   ├── data/                #   Dataset ingestion (ds003059, ds006072)
│   ├── web/                 #   Dashboard FastAPI application
│   ├── templates/           #   Dashboard HTML templates
│   ├── static/              #   Dashboard CSS/JS assets
│   └── models/              #   Model variants
│
├── prior_art/               # ds003059 literature landscape
│   ├── code_inventory.md    #   Master table of all studies
│   ├── reproducibility_matrix.md
│   ├── runbooks/            #   Per-analysis-family guides
│   ├── repositories/        #   Cloned external repos (gitignored)
│   └── scripts/             #   Clone and verification scripts
│
├── configs/                 # YAML configuration files
│   ├── graphs/              #   Module graph definitions
│   ├── regimes/             #   Sober and perturbed regimes
│   └── targets/             #   Empirical target signatures
│
├── scripts/                 # Pipeline and utility scripts
├── tests/                   # Test suite
├── results/                 # Generated outputs (gitignored binaries)
├── docs/                    # Documentation
│   ├── reference/           #   Archived project history
│   └── stage_reports/       #   Generated stage summaries
│
├── SPEC.md                  # Model specification and equations
├── ARCHITECTURE.md          # System architecture and data flow
└── AGENTS.md                # Project rules and conventions
```

---

## The Surrogate Model

An 8-module stochastic graph model with bistable dynamics, adaptation, and
hierarchical constraint. Each module's latent state evolves as:

```
dx_i = ( barrier * (x - x³) - rigidity * (x - baseline) - adaptation
         + cross_scale * Σ W_ij tanh(x_j)
         + constraint_scale * (Hx - x) ) / τ dt + temperature * dW
```

The model runs two regimes (sober baseline, altered-state perturbation) and
compares proxy metrics: functional connectivity, entropy-like diversity,
switching rate, metastability, and hierarchical compression.

**Current mechanism ranking (A+B+C+D+E):**

| Rank | Layer | Role |
|------|-------|------|
| 1 | C — Hierarchy/routing | Strongest implemented evidence layer |
| 2 | E — Network-control energy | Supports landscape-flattening proxy only |
| 3 | D — Dynamic repertoire | Supportive but window-sensitive |
| 4 | A — Transition-state proxy | Supportive but state-label dependent |
| 5 | B — DMDc baseline | Negative control (retained intentionally) |

See [SPEC.md](SPEC.md) for the full mathematical formulation.

---

## The Prior-Art Landscape

A structured inventory of all known research reusing the OpenNeuro ds003059
dataset, covering 12 analysis families:

| Family | Key Method |
|--------|-----------|
| Ising thermodynamics | Monte Carlo spin models, Ising temperature |
| Entropy (CopBET) | Multi-metric entropy evaluation |
| Energy landscape | Network control theory, 5-HT2A-informed control |
| REACT connectivity | Receptor-enriched functional connectivity |
| Neuroreceptor eigenmodes | Geometric eigenmodes, receptor density maps |
| Dynamic integration | Cartographic profiling, time-varying FC |
| Cortical gradients | Diffusion map embedding (BrainSpace) |
| Music brain states | K-means clustering, transition matrices |
| GNW/IIT consciousness | Anterior-posterior connectivity, gain ratio |
| Mesoscale ReHo | Regional homogeneity, subcortical sync |
| Traveling waves | Complex principal components |
| DLPFC Granger causality | Theta-band thalamus-to-DLPFC flow |

See [prior_art/README.md](prior_art/README.md) for the full inventory,
reproducibility matrix, and per-family runbooks.

---

## Dataset

**Primary anchor:** [OpenNeuro ds003059](https://openneuro.org/datasets/ds003059) v1.0.0

- 15 subjects, paired LSD and placebo sessions
- Resting-state fMRI: run-01 and run-03 (primary), run-02 music (secondary)
- BIDS-formatted, requires ~50 GB storage for raw data

> **Note:** The pipeline can run from cached summary statistics without
> downloading the full dataset. See `src/lsd_thesis/data/` for details.

---

## Citation

```bibtex
@software{grimberg2026lsd_thesis,
  author    = {Grimberg, Yuval},
  title     = {LSD Thesis: Macro-Dynamic Surrogate Model},
  year      = {2026},
  url       = {https://github.com/grimgrimberg/LSD_Thesis}
}
```

See [CITATION.cff](CITATION.cff) for the full citation file.

---

## License

See repository license file for details.
