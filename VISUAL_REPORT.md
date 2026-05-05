# Visual Report

## Existing Visual Assets

Generated assets are ignored by Git but available locally when the pipeline has been run:

- `results/stage_1/figures/graph_overview.html`
- `results/stage_1/figures/baseline_node_activity.html`
- `results/stage_1/figures/perturbed_node_activity.html`
- `results/stage_1/figures/baseline_fc_matrix.html`
- `results/stage_1/figures/perturbed_fc_matrix.html`
- `results/stage_2/figures/sober_metric_fit.html`
- `results/stage_2/figures/empirical_metric_deltas.html`
- `results/stage_2/figures/empirical_fc_delta.html`
- `results/stage_3/figures/mechanism_ranking.html`
- `results/stage_3/figures/mechanism_ranking_seed_panel.html`
- `results/stage_4/figures/single_mechanism_ablation.html`
- `results/stage_4/figures/pairwise_ablation_heatmap.html`
- `output/doc/figures/stage1_metric_shift.png`
- `output/doc/figures/stage2_fit_robustness.png`

## Visual Storyboard

1. Architecture diagram: data/configs to simulator to metrics to reports.
2. 8-module graph diagram: modules, groups, and thalamic gateway.
3. Sober vs altered-state-inspired comparison: time series and FC matrices.
4. Empirical delta panel: placebo vs LSD ds003059 deltas with sign conflicts marked.
5. Perturbation ranking: one-shot and seed-panel rankings.
6. Ablation panel: single mechanisms and pairwise heatmap.
7. Demo dashboard: model explorer plus empirical explorer.

## Current Visual Risks

- Generated HTML/PNG files can be stale relative to source.
- Empirical raw previews are downsampled summaries, not diagnostic images.
- Dashboard payloads can become large if regenerated with bigger preview windows.
- Some plots may visually suggest stronger biological validity than the data supports unless captions are explicit.

## Recommended Captions

- "Macro-module graph used by the surrogate model; node names are coarse proxies."
- "Sober and perturbed traces from the model; values are latent states, not neural recordings."
- "Paired ds003059 LSD-minus-placebo summary deltas under the current 8-module proxy."
- "Perturbation ranking by mismatch score; lower is better, not proof of mechanism."
- "Ablation results identify which model knobs reduce mismatch under this proxy."

## Demo Validation

Proposed before thesis demo:

- Run `uv run python scripts/run_pipeline.py run-all`.
- Run `uv run python scripts/run_dashboard.py`.
- Open `http://127.0.0.1:8000/`.
- Check that model explorer, empirical explorer, gallery links, and provenance block load.
