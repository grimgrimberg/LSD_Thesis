# Dynamic Mechanism Robustness

Generated from cached `ds003059` empirical viewer artifacts with:

```bash
uv run python scripts/run_dynamic_mechanism_ranking.py
```

This command reads `results/stage_2/empirical_viewer` and refreshes `results/dynamic_mechanism_ranking/`. It does not download raw data and does not run guarded run-02/music extraction.

## Scope

These are in-sample stress tests on the current cached LSD run-01/run-03 evidence layer. They are not population confidence intervals, not receptor-level validation, and not a substitute for motion/confound gates, structural-connectome controls, PET receptor maps, Schaefer/Yeo sensitivity, or external dataset stress tests.

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

| Layer | Current score | Bootstrap mean | 95% interval | Median rank | Rank-1 fraction | Claim status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A transition-state proxy | 0.149 | 0.164 | -0.132 to 0.494 | 3 | 0.117 | Mixed and state-label dependent |
| B DMDc baseline | -0.074 | -0.074 | -0.166 to 0.012 | 5 | 0.000 | Negative baseline, not main claim |
| C hierarchy/routing | 0.333 | 0.349 | 0.222 to 0.520 | 1 | 0.844 | Strongest current layer |
| D dynamic repertoire | 0.151 | 0.148 | -0.019 to 0.330 | 3 | 0.020 | Supportive but window-sensitive |
| E network-control energy | 0.183 | 0.196 | -0.016 to 0.393 | 3 | 0.020 | Proxy-supported only after claim split |

## E horizon sensitivity

| Horizon | E support score | LSD receptor-profile transition-energy reduction % | LSD uniform transition-energy reduction % | Receptor vs random energy reduction % |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 0.206 | 4.767 | 7.296 | -12.753 |
| 8 | 0.190 | 4.702 | 6.936 | -12.696 |
| 12 | 0.161 | 4.478 | 6.507 | -14.143 |
| 16 | 0.179 | 4.316 | 6.222 | -13.620 |

Interpretation: E supports a lower-transition-energy landscape-flattening proxy across tested horizons, but receptor-specific control placement remains unsupported because the receptor profile does not beat random controls.

## Claim verdicts

| Claim | Verdict | Evidence | Next action |
| --- | --- | --- | --- |
| C hierarchy/routing is currently the strongest implemented LSD mechanism layer. | supported_first_pass | Bootstrap rank-1 fraction = 0.844. | Re-run C under Schaefer/Yeo and motion-sensitive exclusions before final thesis claims. |
| E supports a landscape-flattening proxy. | supported_proxy | Default-horizon receptor transition-energy reduction = 4.702%. | Replace macro graph with structural connectome and add graph-rewire nulls. |
| E supports receptor-specific control placement. | not_supported_yet | Receptor-vs-random energy reduction = -15.434%. | Replace coarse priors with PET 5-HT2A maps and spatial nulls before making receptor claims. |
| Current LSD patterns align with the transmodal-unimodal benchmark. | directionally_aligned | C sensory-transmodal mean delta = 0.0473. | Test the same benchmark in ds006072 and Schaefer/Yeo parcellations. |
| Current LSD patterns address striatal/unimodal effects. | not_testable_current_proxy | The current 8-module proxy lacks the required striatal parcel. | Add striatal parcels before comparing this benchmark. |
| B DMDc is the main control-theory result. | reject_as_main_claim | B bootstrap rank-1 fraction = 0.000. | Keep B as a negative/sanity baseline unless held-out prediction improves clearly. |

## Guardrails

- Treat all transition, entropy-like, metastability, switching-barrier, hierarchy/routing, and control-energy metrics as proxy constructs.
- Do not infer subjective experience, clinical effects, receptor pharmacology, or consciousness-theory conclusions from these metrics.
- Do not hide B/DMDc: it remains a negative baseline in the current ranking.
- Keep E split into lower-transition-energy proxy and receptor-specific placement until structural/PET/null gates are satisfied.
- Keep run-02/music gated and outside the primary evidence until explicit approval, subject masks, motion/context checks, and claim labeling exist.
