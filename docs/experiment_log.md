# Experiment Log

## 2026-04-08

- Initialized greenfield repository for a whole-brain surrogate MVP.
- Chosen baseline architecture: graph-coupled stochastic bistable modules with adaptation and optional top-down constraint.
- Initial empirical strategy: summary-statistics-first pipeline anchored to OpenNeuro `ds003059`, with raw-ingestion hooks kept explicit.
- Stage 1 completed with reproducible simulator tests, saved figures, and a report. Critical failure logged: the current perturbation increases entropy and switching but still underperforms on the static cross-group FC proxy.
- Stage 2 completed with a sober summary-target loader, ds003059 subset plan, transparent random-search fitter, saved fit figures, and a report. Critical limitation logged: targets are curated placeholders rather than direct dataset-derived statistics.
- Stage 3 completed with four one-at-a-time perturbation mechanisms ranked against literature-derived delta targets. Current rankings remain weak because the surrogate still underexpresses altered-state deltas.
- Stage 4 completed with single and pairwise ablation rankings plus a dashboard-ready JSON/result layer.
- Dashboard verified in browser through the local FastAPI server. Only observed browser error was a missing `favicon.ico`, which is cosmetic.
- Replaced the placeholder empirical path with actual OpenNeuro `ds003059` resting-state ingestion through the OpenNeuro GraphQL API and exact-file downloads for 15 subjects / 60 runs.
- Added cached extraction of 8 coarse module time series and generated real `empirical_sober_targets.yaml` plus `empirical_perturbation_targets.yaml`.
- Stage 2 sober fit improved from `4.4884` to `2.6917` after widening the search space and allowing stronger thalamic / cross-network candidate regimes.
- Tried a bundled multi-parameter perturbation operator to strengthen altered-state sensitivity. It made Stage 3 worse (`10.16` versus `8.49`), so it was reverted. Failure retained in the log instead of hidden.
- Added training export infrastructure: windowed ds003059 module trajectories now export to `results/training/ds003059_windows.npz`, and a cloud-ready GRU autoencoder scaffold was added under `cloud/hf_jobs/`.
