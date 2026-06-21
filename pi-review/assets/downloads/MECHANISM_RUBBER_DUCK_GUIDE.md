# Mechanism Rubber-Duck Guide

## One-Sentence Version

The project compares five families of model-level macro-dynamic proxies against paired LSD/placebo summary evidence, ranks them by existing support scores, stress-tests the ranking, and records what can and cannot be claimed.

## Say This Out Loud

"I am not saying the model experiences anything or proves receptor biology. I am asking which transparent proxy family best tracks the paired LSD/placebo macro-dynamic changes already summarized in the repo. A through E are five candidate explanations. Each one converts the same evidence into a different measurable signature, then the package ranks those signatures and keeps the caveats visible."

## A-E In Plain English

| Layer | Plain meaning | Math idea | Current read |
|---|---|---|---|
| A | Transition-state proxy: does the system move between macro-states more easily or less rigidly? | occupancy, transition rate, transition entropy, dwell/barrier proxies, step distance | rank 4, score 0.148906 |
| B | DMDc predictive baseline: does a simple controlled-dynamics predictor explain one-step changes? | `x_next ~= A x + B u`; leave-one-subject-out RMSE change | rank 5, score -0.074064; negative sanity baseline |
| C | Hierarchy/routing: do changes look like altered routing across sensory, associative, transmodal, and thalamic-gateway structure? | aggregate signed support across hierarchy/routing metrics | rank 1, score 0.332606; strongest current proxy |
| D | Dynamic repertoire: does the system explore a broader or different network repertoire? | graph/dynamic-FC features such as integration, segregation, modularity, participation, variance, step distance | rank 3, score 0.150619 |
| E | Control-energy proxy: how hard is it for a coarse macro graph to move from placebo-like to LSD-like state under candidate priors? | finite-horizon control energy, squared L2 norm of control input | rank 2, score 0.182875; useful lower transition/control-energy proxy, not receptor-specific proof |

## How Everything Comes Together

1. Start with cached paired run-01/run-03 LSD/placebo summaries.
2. Convert the evidence into five interpretable proxy families: A, B, C, D, and E.
3. Aggregate feature support into a score for each family.
4. Stress-test the ranking with bootstrap and run-sensitivity artifacts.
5. Gate the claims using verdict and thesis-status tables.
6. Present the proposed next track: solve the FD/DVARS/censoring motion-proof blocker before claim promotion or scope expansion.

## Metadata Trail

| Question | Local file |
|---|---|
| What are A-E and their scores? | `deliverable_website/assets/data/mechanism_ranking_values.csv` |
| Is C stable? | `deliverable_website/assets/data/robustness_summary_values.csv` |
| Do run-01 and run-03 agree? | `deliverable_website/assets/data/robustness_run_sensitivity_values.csv` |
| What empirical deltas feed the story? | `deliverable_website/assets/data/empirical_group_metric_deltas.csv` |
| Which claims are allowed? | `deliverable_website/assets/data/dynamic_claim_verdicts.csv` |
| Which blockers remain? | `deliverable_website/assets/data/thesis_gate_summary.csv` |

## What Not To Say

- Do not say the model simulates subjective experience.
- Do not say the ranking proves receptor biology.
- Do not say internal robustness closes the motion/confound blocker.
- Do not say run-02/music is primary evidence.
- Do not say the thesis is finished.
