# Evidence And Calculations

## Scope

This document explains the selected plots, screenshots, and copied figures in the PI package. Values were read from existing JSON/CSV artifacts only. No scientific workflow was rerun and no plot was regenerated.

Derived tables in `assets/data/` are labeled as derived for the PI package from existing artifacts; they are not regenerated scientific outputs.

## Derived Tables

| Table | Source |
|---|---|
| `assets/data/mechanism_ranking_values.csv` | `results/dynamic_mechanism_ranking/summary.json` |
| `assets/data/robustness_summary_values.csv` | `results/dynamic_mechanism_ranking/robustness/bootstrap_layer_summary.csv` |
| `assets/data/robustness_run_sensitivity_values.csv` | `results/dynamic_mechanism_ranking/robustness/run_sensitivity.csv` |
| `assets/data/dynamic_claim_verdicts.csv` | `results/dynamic_mechanism_ranking/robustness/claim_verdicts.csv` |
| `assets/data/empirical_group_metric_deltas.csv` | `results/stage_2/empirical_viewer/group_overview.json` |
| `assets/data/thesis_gate_summary.csv` | `results/thesis_upgrade/thesis_upgrade_status.json` |
| `assets/data/figure_deck_status_cards.csv` | `results/thesis_upgrade/thesis_upgrade_status.json`; CV5 and archive artifacts |
| `assets/data/literature_benchmark_values.csv` | `results/dynamic_mechanism_ranking/summary.json` |
| `assets/data/publication_figure_values.csv` | `results/stage_1/stage_1_summary.json`; `results/stage_2/stage_2_summary.json` |

## Exhibit A: Dashboard Overview

Image path in package: `assets/screenshots/dashboard-overview.png`

Original source path: `docs/reports/project_state_handoff/assets/screenshots/dashboard-overview.png`

Original status: dashboard screenshot copied from the project-state handoff package.

What it visually shows: The project posture, claim gates, strict gates, current ranking summary, and evidence-flow overview.

Data artifact or payload behind it: `src/lsd_thesis/web/dashboard_payload.py`, `src/lsd_thesis/web/figure_payload.py`, `src/lsd_thesis/web/site_payload.py`, `results/thesis_upgrade/thesis_upgrade_status.json`, and `results/dynamic_mechanism_ranking/summary.json`.

Calculation summary: The overview combines status cards and ranking/gate summaries read from existing artifacts. Strict completion is reported as complete count divided by total count.

Exact values safely extracted:

- Thesis readiness: 6/9.
- Strict completion: 4/6.
- Package readiness: 1/2.
- Current ranking: C, E, D, A, B.
- paired subject count in empirical viewer: 15.
- paired cached records for dynamic ranking: 30.

Likely responsible code: `build_dashboard_payload()` in `src/lsd_thesis/web/dashboard_payload.py`; figure/status helpers in `src/lsd_thesis/web/figure_payload.py`.

Claim status: mixed. The workbench is implemented; strict thesis completion remains blocked.

Caveat: Overview cards are presentation/status surfaces, not independent scientific validation.

Needed to strengthen claim: Complete the motion/confound proof and archive DOI gate.

Validation/test protection: Dashboard route/payload/public-site contract tests, figure payload tests, thesis upgrade status tests, and dashboard strict preflight.

## Exhibit B: Mechanism Ranking

Image path in package: `assets/screenshots/dashboard-ranking.png`

Original source path: `docs/reports/project_state_handoff/assets/screenshots/dashboard-ranking.png`

Original status: dashboard screenshot.

What it visually shows: A-E mechanism ranking with C leading and B retained as a negative baseline.

Data artifact or payload behind it: `results/dynamic_mechanism_ranking/summary.json`; `results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv`.

Calculation summary: The chart uses exported mechanism ranking rows sorted by rank. Bar length is the exported unitless support score.

Exact values safely extracted:

| Rank | Layer | Mechanism | Score | Status |
|---:|---|---|---:|---|
| 1 | C | hierarchy_routing_layer | 0.332606 | implemented_first_pass |
| 2 | E | receptor_informed_network_control_energy | 0.182875 | implemented_proxy_control_energy |
| 3 | D | dynamic_repertoire_layer | 0.150619 | implemented_first_pass |
| 4 | A | transition_state_proxy | 0.148906 | implemented_first_pass |
| 5 | B | dmdc_condition_interaction | -0.074064 | implemented_negative_control_baseline |

Meaning of A-E:

- A: transition-state proxy.
- B: DMDc predictive baseline / negative control.
- C: hierarchy/routing.
- D: dynamic repertoire.
- E: finite-horizon network-control energy proxy.

Likely responsible code: `src/lsd_thesis/dynamic_mechanism/`, `scripts/run_dynamic_mechanism_ranking.py`, dashboard payload builders, and chart rendering in dashboard JavaScript.

Claim status: proxy-supported for C as current strongest layer; mixed for E; implemented negative baseline for B.

Caveat: This is a model-level proxy ranking. It is not biological proof and not a receptor-level mechanism.

Freshness note: exact ranking values in this package are read from `results/dynamic_mechanism_ranking/summary.json`, because an older export CSV copy can contain a stale E score.

Needed to strengthen claim: Motion-sensitive exclusions first, followed by parcellation/null checks and any claim-promotion threshold agreed after the motion-proof plan is reviewed.

Validation/test protection: `tests/test_result_artifact_schema_contract.py`, `tests/test_dashboard_payload_contract.py`, `tests/test_figure_payload.py`.

## Exhibit C: Robustness

Image path in package: `assets/screenshots/dashboard-robustness.png`

Original source path: `docs/reports/project_state_handoff/assets/screenshots/dashboard-robustness.png`

Original status: dashboard screenshot.

What it visually shows: Subject-bootstrap and sensitivity evidence for the ranking.

Data artifact or payload behind it: `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`; `results/dynamic_mechanism_ranking/robustness/bootstrap_layer_summary.csv`.

Calculation summary: Bootstrap summary rows report current score, score mean/std, confidence interval bounds, median rank, and rank-1 fraction by layer.

Exact values safely extracted:

| Layer | Current score | Score mean | CI low | CI high | Median rank | Rank-1 fraction |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.148906 | 0.163748 | -0.131526 | 0.493676 | 3.0 | 0.117188 |
| B | -0.074064 | -0.074430 | -0.165982 | 0.012141 | 5.0 | 0.000000 |
| C | 0.332606 | 0.349477 | 0.222188 | 0.520315 | 1.0 | 0.843750 |
| D | 0.150619 | 0.148384 | -0.019302 | 0.329665 | 3.0 | 0.019531 |
| E | 0.182875 | 0.195633 | -0.016250 | 0.392784 | 3.0 | 0.019531 |

Likely responsible code: `scripts/run_dynamic_mechanism_ranking.py`; robustness helpers under `src/lsd_thesis/dynamic_robustness.py` and `src/lsd_thesis/dynamic_mechanism/`.

Claim status: proxy-supported internal robustness for C; not external validation.

Caveat: Robustness is an in-sample/internal stress test and does not remove motion/confound blockers.

Needed to strengthen claim: External stress tests, motion-sensitive exclusions, and approved fMRIPrep FD/DVARS/censoring proof.

Validation/test protection: Result artifact schema tests, figure payload tests, dashboard payload tests.

## Exhibit D: Empirical Viewer

Image path in package: `assets/screenshots/dashboard-empirical.png`

Original source path: `docs/reports/project_state_handoff/assets/screenshots/dashboard-empirical.png`

Original status: dashboard screenshot.

What it visually shows: Paired LSD/placebo group metric deltas and subject/run/window inspection controls.

Data artifact or payload behind it: `results/stage_2/empirical_viewer/group_overview.json`; subject-view cache under `results/stage_2/empirical_viewer/subject_views/` for local-only inspection.

Calculation summary: Group-level bars show LSD-minus-placebo deltas for macro-dynamic metrics read from the group overview artifact.

Exact values safely extracted:

| Metric | LSD minus placebo delta | Delta std |
|---|---:|---:|
| within_network_stability | 0.066093 | 0.108138 |
| cross_network_communication | 0.074076 | 0.083530 |
| thalamic_coupling | 0.119918 | 0.148357 |
| hierarchical_compression | 0.054150 | 0.136924 |
| entropy_diversity | -0.002253 | 0.023046 |
| switching_rate | 0.012346 | 0.032333 |
| metastability_proxy | -0.053960 | 0.079222 |
| effective_barrier_proxy | -0.149192 | 0.366374 |

Paired subject count: 15. Primary runs: run-01 and run-03.

Likely responsible code: `src/lsd_thesis/web/empirical_viewer.py`, `src/lsd_thesis/web/dashboard_payload.py`, and Stage 2 data helpers.

Claim status: proxy-supported aggregate summary inspection.

Caveat: Subject-level cache rows are local-only; run-02/music remains exploratory/audit-only unless explicitly approved.

Needed to strengthen claim: Motion/confound proof, parcellation sensitivity review, and subject/run-level caveat handling.

Validation/test protection: Empirical viewer payload contracts, artifact security tests, dashboard preflight.

## Exhibit E: Prior-Art Inventory

Image path in package: `assets/screenshots/dashboard-prior-art.png`

Original source path: `docs/reports/project_state_handoff/assets/screenshots/dashboard-prior-art.png`

Original status: dashboard screenshot.

What it visually shows: ds003059 prior-art families, labels such as proxy-supported/mixed/future/blocked, and claim boundaries.

Data artifact or payload behind it: `prior_art/README.md`, `prior_art/code_inventory.md`, `prior_art/comparison_extraction_plan.json`, `docs/research/ds003059_prior_art_to_thesis_map.md`, and public prior-art payload builders.

Calculation summary: This is primarily a structured inventory and status mapping, not a numeric scientific calculation.

Exact values safely extracted: 12 major ds003059 analysis families are documented in `prior_art/README.md` and `prior_art/code_inventory.md`, with an additional translational neuromodeling teaching resource listed in the inventory.

Likely responsible code: `src/lsd_thesis/web/site_payload.py`; prior-art API/payload routes.

Claim status: mixed/context-only. Prior art is design inspiration and scholarly positioning unless local artifacts promote a claim.

Caveat: Do not treat prior-art wrappers as original local evidence.

Needed to strengthen claim: For each prior-art family, implement or audit local evidence independently with license checks and tests.

Validation/test protection: public-site payload tests and prior-art payload contract surfaces.

## Exhibit F: Figure Deck

Image path in package: `assets/screenshots/dashboard-figures.png`

Original source path: `docs/reports/project_state_handoff/assets/screenshots/dashboard-figures.png`

Original status: dashboard screenshot.

What it visually shows: Export-ready figure registry and production gates.

Data artifact or payload behind it: `src/lsd_thesis/web/figure_payload.py`, `results/thesis_upgrade/thesis_upgrade_status.json`, `results/validation/cv5_subject_disjoint/cv5_aggregate_validation.json`, and `results/reproducible_archive/ARCHIVE_MANIFEST.json`.

Calculation summary: Figure deck status cards read strict thesis gates, motion proof status, archive DOI status, and internal CV5 status from existing artifacts.

Exact values safely extracted:

- Strict thesis gates: 4/6.
- Motion proof: `blocked_missing_fmriprep_fd_dvars_censoring_motion_proof`.
- Archive DOI: release verified true, DOI verified false.
- CV5: complete, 5/5 folds, 15 subjects.

Likely responsible code: `src/lsd_thesis/web/figure_payload.py`.

Claim status: implemented figure registry; blocked motion and archive gates.

Caveat: "Export-ready" means review/figure registry readiness, not completed thesis or completed archive publication.

Needed to strengthen claim: Complete motion/confound and Zenodo DOI gates.

Validation/test protection: `tests/test_figure_payload.py`, thesis status tests, dashboard payload tests.

## Exhibit G: Representative Figure - stage1_metric_shift.png

Image path in package: `assets/figures/stage1_metric_shift.png`

Original source path: `output/doc/figures/stage1_metric_shift.png`

Original status: ignored generated output copied into the project-state handoff package, then copied into this PI package.

What it visually shows: Stage 1 baseline versus perturbed surrogate values for state entropy and switching rate.

Data artifact behind it: `results/stage_1/stage_1_summary.json`.

Calculation summary: `src/lsd_thesis/publication_figures.py` reads baseline and perturbed values for `state_entropy` and `switching_rate` and plots side-by-side bars.

Exact values safely extracted:

| Metric | Baseline | Perturbed | Delta |
|---|---:|---:|---:|
| state_entropy | 0.989019 | 0.997577 | 0.008557 |
| switching_rate | 0.147147 | 0.203203 | 0.056056 |

Likely responsible code: `_build_stage1_metric_shift_figure()` in `src/lsd_thesis/publication_figures.py`.

Claim status: implemented surrogate demonstration.

Caveat: Stage 1 is surrogate macro-dynamics only; it does not prove receptor biology or subjective effects.

Needed to strengthen claim: Tie surrogate shifts to empirical targets and blockers through later-stage evidence.

Validation/test protection: publication figure/source artifact tests and broader package validation.

## Exhibit H: Representative Figure - stage2_fit_robustness.png

Image path in package: `assets/figures/stage2_fit_robustness.png`

Original source path: `output/doc/figures/stage2_fit_robustness.png`

Original status: ignored generated output copied into the project-state handoff package, then copied into this PI package.

What it visually shows: Stage 2 initial objective score versus selected score, plus repeatability summary text.

Data artifact behind it: `results/stage_2/stage_2_summary.json`.

Calculation summary: `src/lsd_thesis/publication_figures.py` plots initial score and selected score. Lower is better. It adds subject/run counts and multi-seed metric summary text.

Exact values safely extracted:

- Initial score: 1628.945399.
- Selected score: 2.053957.
- Change: decreased by 1626.891441.
- Selected iteration: 42.
- Empirical subjects: 15.
- Empirical run count: 60.
- Validation seed panel score mean: 2.455030.
- Validation seed panel score std: 0.651138.

Likely responsible code: `_build_stage2_fit_robustness_figure()` in `src/lsd_thesis/publication_figures.py`.

Claim status: implemented fit-quality summary.

Caveat: This is cached fit quality and limited repeatability evidence, not proof of generalization.

Needed to strengthen claim: Subject-disjoint and external validation, plus motion/confound proof.

Validation/test protection: publication figure/source artifact tests and validation baseline docs.

## Exhibit I: Representative Historical Dashboard Figures

Image paths in package:

- `assets/figures/pass2a_microsite.png`
- `assets/figures/set_setting_seed_live_8020.png`

Original source paths:

- `results/setting_seed/dashboard/screenshots/pass2a_microsite.png`
- `results/setting_seed/dashboard/screenshots/set_setting_seed_live_8020.png`

Original status: ignored generated PNG screenshots copied into the project-state handoff package, then copied into this PI package.

What they visually show: Historical local setting/seed dashboard surfaces.

Data artifact or payload behind them: `results/setting_seed/dashboard/dashboard_payload.json` and related setting/seed artifacts, if present.

Calculation summary: These are screenshots, not direct numeric calculations in this packaging pass.

Exact values safely extracted: Not safely recovered in this packaging pass beyond source paths and captions in the prior handoff manifest.

Likely responsible code: setting/seed dashboard scripts and web artifact routing.

Claim status: historical/context-only.

Caveat: These images are historical dashboard context. They are not live proof unless current artifacts confirm the same state.

Needed to strengthen claim: A dedicated setting/seed audit that checks current payloads, generated status, and no-touch run-02/music boundaries.

Validation/test protection: setting/seed tests are historical in `docs/VALIDATION.md`; current package did not rerun setting/seed workflows.
