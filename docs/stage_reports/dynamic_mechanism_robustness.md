# Dynamic Mechanism Robustness

Generated from cached `ds003059` empirical viewer artifacts with:

```bash
uv run python scripts/run_dynamic_mechanism_ranking.py
```

This command reads `results/stage_2/empirical_viewer` and refreshes `results/dynamic_mechanism_ranking/`. It does not download raw data and does not run guarded run-02/music extraction.

## Scope

These are in-sample stress tests on the current cached LSD run-01/run-03 evidence layer. They are cached sensitivity intervals, not population confidence intervals, not receptor-level validation, and not a substitute for motion/confound gates, structural-connectome controls, PET receptor maps, Schaefer/Yeo sensitivity, or external dataset stress tests.

## Artifacts

- `results/dynamic_mechanism_ranking/summary.json`
- `results/dynamic_mechanism_ranking/robustness/robustness_summary.json`
- `results/dynamic_mechanism_ranking/robustness/bootstrap_layer_summary.csv`
- `results/dynamic_mechanism_ranking/robustness/bootstrap_score_rows.csv`
- `results/dynamic_mechanism_ranking/robustness/run_sensitivity.csv`
- `results/dynamic_mechanism_ranking/robustness/e_horizon_sensitivity.csv`
- `results/dynamic_mechanism_ranking/robustness/state_label_sensitivity.csv`
- `results/dynamic_mechanism_ranking/robustness/d_window_sensitivity.csv`
- `results/dynamic_mechanism_ranking/robustness/literature_benchmark.csv`
- `results/dynamic_mechanism_ranking/robustness/claim_verdicts.csv`
- `docs/stage_reports/dynamic_mechanism_ranking.md`

## Subject-bootstrap summary

| Layer | Current score | Bootstrap mean | Cached sensitivity interval | Median rank | Rank-1 fraction | Claim status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A transition-state proxy | 0.149 | 0.164 | -0.132 to 0.494 | 3 | 0.078 | Mixed and state-label dependent |
| B DMDc baseline | -0.074 | -0.074 | -0.166 to 0.012 | 5 | 0.000 | Negative baseline, not main claim |
| C hierarchy/routing | 0.333 | 0.349 | 0.222 to 0.520 | 1 | 0.602 | Leading current macro-dynamic proxy, still motion-gated |
| D dynamic repertoire | 0.151 | 0.148 | -0.019 to 0.330 | 3 | 0.020 | Supportive but window-sensitive |
| E network-control energy | 0.272 | 0.299 | 0.052 to 0.535 | 2 | 0.301 | E1 lower-energy proxy supported; E2 receptor placement unsupported |

## E horizon sensitivity

| Horizon | E support score | LSD receptor-profile transition-energy reduction % | LSD uniform transition-energy reduction % | Receptor vs random energy reduction % |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 0.348 | 2.307 | 5.249 | 3.232 |
| 8 | 0.281 | 2.466 | 5.071 | -1.197 |
| 12 | 0.225 | 2.358 | 4.752 | -4.028 |
| 16 | 0.243 | 2.269 | 4.538 | -3.223 |

Interpretation: E supports a lower-transition/control-energy proxy across tested horizons, but receptor-specific control placement remains mixed-to-unsupported because the receptor profile does not consistently beat random controls and still lacks the required structural/PET/spatial-null promotion gate.

## Claim verdicts

| Claim | Verdict | Evidence | Next action |
| --- | --- | --- | --- |
| C is the provisional leading macro-dynamic proxy under the current cached ds003059 analysis, pending motion/confound control and atlas-level replication. | proxy-supported | Bootstrap rank-1 fraction = 0.602. | Re-run C under Schaefer/Yeo and motion-sensitive exclusions before final thesis claims. |
| E supports a landscape-flattening proxy. | proxy-supported | Default-horizon receptor transition-energy reduction = 2.466%. | Replace macro graph with structural connectome and add graph-rewire nulls. |
| E supports receptor-specific control placement. | unsupported | Receptor-vs-random energy reduction = -1.844%. | Replace coarse priors with PET 5-HT2A maps and spatial nulls before making receptor claims. |
| Current LSD patterns align with the transmodal-unimodal benchmark. | proxy-supported | C sensory-transmodal mean delta = 0.0473. | Test the same benchmark in ds006072 and Schaefer/Yeo parcellations. |
| Current LSD patterns address striatal/unimodal effects. | future | The current proxy lacks the required striatal parcel. | Add striatal parcels before comparing this benchmark. |
| Rejected candidate: B DMDc as the main control-theory result. | unsupported | B bootstrap rank-1 fraction = 0.000. | Keep B as a negative/sanity baseline unless held-out prediction improves clearly. |

## Guardrails

- Treat all transition, entropy-like, metastability, switching-barrier, hierarchy/routing, and control-energy metrics as proxy constructs.
- Do not infer subjective experience, clinical effects, receptor pharmacology, or consciousness-theory conclusions from these metrics.
- Do not hide B/DMDc: it remains a negative baseline in the current ranking.
- Keep E split into lower-transition-energy proxy and receptor-specific placement until structural/PET/null gates are satisfied.
- Keep run-02/music gated and outside the primary evidence until explicit approval, subject masks, motion/context checks, and claim labeling exist.
