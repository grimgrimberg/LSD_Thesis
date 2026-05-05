# Six-Week Thesis/Prototype Roadmap

## Week 1 - Stabilize Repo And Baseline Model

- Milestones: Git baseline, `.gitignore` safety, command docs, audit docs, fast validation gate.
- Deliverables: root audit docs, test report, current state, next steps.
- Acceptance: source tracked, raw data ignored, smoke tests/lint/type checks documented.
- Risks: stale generated outputs, slow tests.
- Fallback: keep results as generated artifacts and use focused smoke gates.
- Advisor should inspect: claim boundaries and Stage 2 sign conflicts.
- Demo audience should understand: this is a transparent surrogate, not LSD realism.
- Candidate paper figure: pipeline overview.

## Week 2 - Formalize Model And Metrics

- Milestones: metric definitions, parameter table, no-NaN/no-Inf validation, slow-test marking.
- Deliverables: updated `METRICS.md`, stronger metric tests.
- Acceptance: every metric has definition, unit/scale, proxy caveat, and sensitivity note.
- Risks: KMeans proxy instability.
- Fallback: report KMeans metrics as exploratory and emphasize FC metrics.
- Paper figure: metric taxonomy and model equation panel.

## Week 3 - Sober Vs Perturbation Experiments

- Milestones: fixed seed panels for baseline and perturbation regimes.
- Deliverables: reproducible sober/perturbed comparison with mean/std deltas.
- Acceptance: seed-panel deltas and seed-noise nulls are visible.
- Risks: perturbation effects remain weak or sign-conflicted.
- Fallback: frame as mismatch result.
- Paper figure: sober vs perturbation regime comparison.

## Week 4 - Ablations And Sensitivity Analysis

- Milestones: one-at-a-time, pairwise, and parameter sweep sensitivity.
- Deliverables: ablation tables, heatmaps, robustness summaries.
- Acceptance: rankings include uncertainty and sign agreement.
- Risks: rankings unstable across seeds.
- Fallback: reduce claims to qualitative mechanism screening.
- Paper figure: ablation ranking and pairwise heatmap.

## Week 5 - Visualization, Demo, And Paper Figures

- Milestones: dashboard polish, static HTML fallback, publication figure bundle.
- Deliverables: visual report, demo script, figure storyboard.
- Acceptance: professor can follow data-to-model-to-mismatch flow in under 5 minutes.
- Risks: dashboard payloads stale or too large.
- Fallback: static report/microsite from generated figures.
- Paper figure: ds003059 target deltas and model mismatch.

## Week 6 - Thesis Writeup And Reproducibility Package

- Milestones: final methods, limitations, reproducibility checklist, advisor review package.
- Deliverables: thesis report, command log, environment lockfile, final executive summary.
- Acceptance: another researcher can run smoke tests and understand what is fitted versus speculative.
- Risks: raw data dependencies are heavy.
- Fallback: provide cached small summaries plus exact raw-data regeneration instructions.
- Paper figure: final conceptual model and result panels.
