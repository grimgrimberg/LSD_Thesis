# Methods

## Project Scope

This project is a transparent macro-dynamics surrogate. It is not a receptor model, not a pharmacokinetic model, and not a model of subjective psychedelic experience. The analysis asks whether a small graph-modulated stochastic system can reproduce coarse resting-state fMRI summary deltas extracted from OpenNeuro `ds003059`.

## Data Anchor

The empirical bridge uses the public OpenNeuro `ds003059` derivative dataset. The current extraction uses resting-state runs only:

- `ses-PLCB`, `task-rest`, `run-01` and `run-03`
- `ses-LSD`, `task-rest`, `run-01` and `run-03`
- `run-02` is excluded because the local dataset notes identify it as a music run

The extraction collapses fMRI signals into eight coarse macro-modules using a Harvard-Oxford-derived anatomical proxy. This proxy is intentionally inspectable, but it is not a canonical functional-network atlas.

## Model

The simulator evolves eight latent module states connected by a weighted macro-module graph. Regime files define global coupling, hierarchy constraint, module rigidity, barrier, temperature, and time constants. Perturbation operators alter these graph/model parameters and are treated as hypothesis toggles:

- `more_cross_talk`
- `less_hierarchical_constraint`
- `more_stochasticity`
- `lower_switching_barrier`

These names describe model operations. They should not be read as direct biological mechanisms.

## Observables

The shared metrics are:

- within-network stability
- cross-network communication
- thalamic coupling
- hierarchical compression
- entropy/diversity
- switching rate
- metastability proxy
- effective barrier proxy

Entropy/diversity, switching, metastability, and barrier are computed proxies from module time series. Several depend on KMeans-derived state labels, so seed and clustering sensitivity must be reported before making strong claims.

## Fitting And Ranking

Stage 2 fits a sober reference regime against placebo summaries and the placebo FC matrix. Stage 3 ranks perturbation operators against paired LSD-minus-placebo empirical deltas. Plan B adds a fixed seed-panel evaluation:

1. Fit the sober regime.
2. For each candidate perturbation and strength, run paired sober/perturbed simulations over a fixed seed panel.
3. Compute delta metrics per seed.
4. Report mean score, score standard deviation, mean delta metrics, delta standard deviations, and target-sign agreement.
5. Compare against a seed-noise null built from sober-vs-sober runs at offset seeds.

This makes the ranking less dependent on a single stochastic trajectory.

## Known Empirical Conflict

Under the current 8-module proxy, the empirical ds003059 deltas conflict with literature-style target signs for:

- `within_network_stability`
- `entropy_diversity`
- `metastability_proxy`

That conflict is part of the result. The project should present it directly as a limitation and as motivation for atlas sensitivity, not hide it behind a cleaner narrative.

## Validation Gates

Minimum validation for a thesis-demo run:

```bash
uv run ruff check .
uv run mypy src
uv run pytest tests/test_simulator.py tests/test_ds003059.py tests/test_perturbation.py tests/test_web.py tests/test_web_integration.py -q -o addopts=
```

Metric-heavy tests can be slow because of clustering. Pin BLAS/OpenMP threads on machines that oversubscribe CPU workers.
