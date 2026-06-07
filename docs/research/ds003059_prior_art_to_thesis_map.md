# ds003059 Prior-Art to Thesis Map

## Purpose

This document maps prior OpenNeuro `ds003059` reuse projects into the current LSD_Thesis A+B+C+D+E evidence-loop framework. It treats those projects as design inspiration and benchmarking context for a transparent macro-dynamics surrogate, not as permission to strengthen receptor-level, subjective-experience, clinical, or consciousness claims.

This map uses the current repository artifacts plus the provided ds003059 reuse-landscape facts: `ds003059` is a BIDS derivative tied to the Imperial/Beckley LSD neuroimaging project; run-01 and run-03 are resting-state; run-02 is music-listening and must stay gated; 15 subjects remained for released BOLD analyses after exclusions; and most downstream reuse computes second-order derivatives such as ROI time series, FC matrices, dynamic state labels, entropy/complexity measures, gradients, receptor-informed maps, and control-energy landscapes.

## Executive recommendation

1. Robustness remains the first implementation priority before data-heavy extensions; the current first-pass robustness artifacts should be verified, refreshed, and extended before any stronger thesis claim.
2. Prior work should inspire benchmark panels and claim gates rather than new primary claims.
3. New data-heavy extensions should remain future/gated unless local artifacts exist.
4. The strongest near-term thesis contribution is a reproducible, claim-gated evidence loop.

## Current repo spine: A+B+C+D+E

- A transition-state proxy: PCA/quantile macro-state labels, occupancy, dwell, switching, barrier-like summaries, and trajectory step-distance proxies.
- B DMDc predictive baseline / negative control: a controlled-dynamics prediction layer that currently remains a negative or sanity baseline, not the main control-theory claim.
- C hierarchy/routing: sensory-transmodal, thalamic, hierarchy, receptor-prior-weighted routing, and related FC proxy metrics; currently the strongest implemented layer.
- D dynamic repertoire / graph metrics: dynamic FC, integration/segregation, efficiency, modularity, participation, and window-sensitive graph summaries.
- E network-control energy: a split claim surface where lower LSD transition-energy is a proxy-supported landscape-flattening result, while receptor-specific control placement remains unsupported unless receptor/PET priors beat uniform, random, degree, graph-rewire, and spatial nulls.

## Prior-art family map

| Prior-art family | Example works/repos | Main methods | Maps to layer(s) | What LSD_Thesis already covers | Safe next addition | Gated future work | Forbidden overclaim | Artifact paths |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Music + K-means brain states | Adamska/Finc music-state work; `igaadamska/LSD-music-brainstates` | K-means dynamic brain-state labels, fractional occupancy, dwell time, transition probabilities, rest/music/post-music comparisons | A, C, D | Resting run-01/run-03 transition proxies, hierarchy/routing summaries, dynamic repertoire metrics, and non-primary run-02 extraction inventory under `results/setting_seed/run02_extraction/` | Keep run-02/music status as `blocked_missing_motion_review` and record music-qualified subject requirements and claim labels | Music-subset masks, motion/context checks, technical-problem exclusions, and explicit approval for music-control analyses | Do not present music/run-02 as primary evidence or infer music-induced subjective experience from state metrics | `docs/research/ds003059_prior_art_to_thesis_map.md`; future `docs/research/music_state_extension_plan.md` |
| Receptor-informed network control energy | Singleton et al.; `singlesp/energy_landscape` | Recurrent brain states, transition-control energy, horizon sensitivity, structural-connectome graph, PET-derived 5-HT2A priors, permutation/spin nulls, atlas/GSR/clustering robustness | E | E horizon sensitivity and lower LSD transition-energy proxy on a macro-module graph; structural/PET status artifacts exist, but receptor-specific placement remains negative/not promoted | Keep E split visible in docs/dashboard and verify horizon/null status from cached artifacts | Claim promotion requires graph-rewire/spatial-null gates and receptor/PET priors beating uniform, random, degree, and spatial controls | Do not claim receptor-specific control placement or pharmacology from the current coarse proxy | `results/dynamic_mechanism_ranking/robustness/e_horizon_sensitivity.csv`; `results/receptor_priors/receptor_prior_status.json`; future `docs/stage_reports/network_control_energy_claim_split.md` |
| Ising/LZW entropy-complexity | Ruffini Ising/LZW complexity stack | Ising temperature, Lempel-Ziv complexity, entropy/complexity of brain dynamics | D, A | Entropy-like state occupancy, transition entropy, switching, dwell/barrier, dynamic repertoire metrics | Add a small transparent LZW-style complexity benchmark over cached module time series if the required cached time series are present | Ising-temperature claims, thermodynamic interpretations, or any algorithmic-complexity implementation that needs external code or heavy new data | Do not import thermodynamic truth claims or say the model measures neural entropy directly | future `src/lsd_thesis/complexity_benchmarks.py`; future `tests/test_complexity_benchmarks.py`; future `results/dynamic_mechanism_ranking/complexity/lzw_complexity_summary.json`; future `docs/stage_reports/complexity_benchmark.md` |
| Entropy/toolbox reproducibility demos | CopBET entropy toolbox/demo | Toolbox-style metric demos, example-data mode, metric comparisons, reproducible command recipes | A, D, project-wide | Command docs, dashboard payloads, generated JSON/CSV/XLSX artifacts, proxy metric definitions | Add metric cards and provenance tables for entropy/complexity metrics using independent implementations | Full toolbox reproduction, GPL or unclear-license code reuse, external example-data bundling | Do not copy GPL code or present toolbox demos as validated local results | future `docs/metric_cards/entropy_complexity_metrics.md`; future `scripts/run_entropy_complexity_benchmark.py`; future `results/entropy_benchmark/` |
| Cross-state altered-consciousness comparisons | Cross-state psychedelic/sleep/sedation/ketamine/propofol/HCP comparisons | Literature comparison across altered-state datasets and broader consciousness-theory contexts | Project-wide, C, D, E | Literature benchmark mapping and explicit external-data blockers; ds006072, structural, receptor, and parcellation statuses are tracked elsewhere in the evidence loop | Keep as context and backlog planning only; report blockers rather than implied validation | New external datasets, psilocybin expansion, HCP structural graphs, PET maps, and cross-state meta-analysis | Do not claim this repo proves, disproves, or settles theories of consciousness | future `docs/research/cross_state_benchmark_plan.md`; `results/thesis_evidence_loop/external_source_plan.md` |
| Standardized derivative/evidence package | Public reproducibility patterns across ds003059 reuse | Claim-gated derivative package, ROI/FC/state/metric artifacts, dashboards, reports, provenance | Project-wide | `results/dynamic_mechanism_ranking/summary.json`, robustness artifacts, exports, dashboard status payloads, thesis evidence loop, archive manifest | Make this map and future dashboard card the organizing layer for what is implemented, proxy-supported, mixed, blocked, or future | Any package that requires raw data redistribution, hidden provenance, or unreviewed external code | Do not publish raw/private data or treat derived proxy artifacts as timeless biological ground truth | `results/dynamic_mechanism_ranking/exports/`; `results/reproducible_archive/ARCHIVE_MANIFEST.json`; `docs/research/ds003059_prior_art_to_thesis_map.md` |

## Claim ladder

| Claim | Status | Evidence/artifact | Limitation | Next action |
| --- | --- | --- | --- | --- |
| C hierarchy/routing currently strongest | proxy-supported | `results/dynamic_mechanism_ranking/summary.json`; `results/dynamic_mechanism_ranking/robustness/robustness_summary.json` | Current support is still proxy-level and tied to available parcellations, confound controls, and metric definitions | Keep C as the main current layer while reporting robustness and remaining confound limits |
| E lower transition-energy proxy | proxy-supported | `results/dynamic_mechanism_ranking/robustness/e_horizon_sensitivity.csv`; `results/dynamic_mechanism_ranking/summary.json` | Macro-module graph proxy, not full receptor-informed network control theory | Refresh E horizon/null reporting before structural/PET upgrades |
| E receptor-specific placement | unsupported | `results/dynamic_mechanism_ranking/robustness/claim_verdicts.csv`; `results/receptor_priors/receptor_prior_status.json` | Coarse receptor priors do not establish receptor-specific control placement and must beat nulls before promotion | Keep claim split visible; require PET/neuromaps, uniform/random/degree/graph/spatial nulls |
| B DMDc negative baseline | implemented | `results/dynamic_mechanism_ranking/summary.json`; robustness claim verdicts | Negative or weak prediction does not invalidate the project; it blocks selling B as the main result | Preserve B as a negative/sanity baseline |
| D complexity/entropy benchmark | future | Existing proxy metrics in `METRICS.md` and dynamic repertoire outputs | No dedicated LZW/complexity benchmark exists yet; entropy-like measures are proxies | Add cached-only benchmark only if module time series are available and implementation is independent |
| run-02/music extension | blocked | README and setting/seed readiness artifacts; no primary run-02 evidence in current ranking | Music-qualified subset, technical-problem exclusions, motion/context checks, and explicit approval are required | Keep run-02 as gated future work |
| psilocybin/cross-dataset expansion | mixed | `results/psilocybin_ds006072/`; `results/thesis_evidence_loop/thesis_evidence_loop_status.json` | Local stress-test evidence is negative/partial and not an LSD replication | Report as external stress test; consider broader cross-state benchmark last |
| structural-connectome sensitivity | mixed | `results/structural_connectome/structural_connectome_status.json` | Structural graph sensitivity must not be promoted as full receptor-informed control proof unless local graph and null gates pass | Interpret E with graph provenance and graph-rewire/null status visible |
| PET/neuromaps receptor-prior upgrade | mixed | `results/receptor_priors/receptor_prior_status.json`; `results/cortical_maps/neuromaps_spatial_null_status.json` | PET/spatial-null status must beat controls before receptor-specific claims | Keep receptor-specific placement downgraded unless null gates pass |
| standardized derivative/evidence package | implemented | `results/reproducible_archive/ARCHIVE_MANIFEST.json`; `results/thesis_evidence_loop/exports/thesis_evidence_loop_tables.xlsx` | Generated outputs need provenance and public/private artifact boundaries | Use this as the thesis-facing contribution spine |

## Recommended execution order

1. Verify or implement robustness for current A+B+C+D+E.
2. Publish prior-art-to-thesis map.
3. Add small entropy/complexity benchmark only if cached time series exist.
4. Upgrade E horizon/null reporting.
5. Plan structural-connectome and PET/receptor upgrades.
6. Add run-02/music extension only after explicit approval.
7. Consider psilocybin/cross-state benchmark last.

## License and code-reuse notes

- Inspect every external repo license before copying code.
- Prefer method-level inspiration and independent implementation.
- GPL code must not be copied into this repo without explicit approval and license compatibility review.
- Cite prior work in docs/reports rather than copying code.

## Dashboard/report implications

The dashboard/report layer should either already expose or eventually add these cards:

- Current ranking: implemented current A+B+C+D+E layer scores and exports.
- Robustness: subject/bootstrap, run split, E horizon, state-label, D window, and sign-conflict/failure reporting.
- E split claim: lower transition-energy proxy versus receptor-specific control placement.
- Prior-art inspiration: prior-art family, mapped layers, status, safe-now work, gated future work, artifact path, and limitation.
- Music/run-02 gate: blocked/future unless explicit extraction approval, music-qualified masks, motion/context checks, and claim labeling exist.
- Entropy/complexity benchmark: future cached-only benchmark with independent implementation.
- External-data status: HCP structural sensitivity implemented/mixed, PET/neuromaps mixed/not promoted, additional cross-state/subcortical work blocked or future, and raw-data/publication boundaries.

## Next Codex prompts

1. Use the existing A+B+C+D+E ranking artifacts and the new ds003059 prior-art map to implement a cached-only robustness pass. Produce JSON/CSV/markdown outputs under `results/dynamic_mechanism_ranking/robustness/` and `docs/stage_reports/dynamic_mechanism_robustness.md`. Do not download raw data, do not run run-02 extraction, and do not change metric weights after seeing results.
2. Add a cached-only entropy/complexity benchmark over existing module time series, with an independent implementation, tests, JSON/CSV outputs, and a claim-safe stage report.
3. Upgrade E horizon/null reporting so lower transition-energy, receptor-specific placement, uniform/random/degree controls, graph-rewire status, and spatial-null blockers are shown as separate dashboard/report claims.
