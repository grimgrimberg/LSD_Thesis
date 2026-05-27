# Stage 4 Report

## Plan

- Run one-at-a-time ablations at the best currently available mechanism strengths.
- Run pairwise combinations to see whether combinations help more than any single mechanism.
- Rank the mechanisms by ds003059 empirical-delta mismatch score.

## Results

- Best single mechanism: `lower_switching_barrier` with score `5028.2029`
- Best pairwise mechanism: `less_hierarchical_constraint+lower_switching_barrier` with score `4819.2698`
- Strengths selected from seed-panel ranking over seeds: `11, 12, 13, 14, 15`

## Critical Review

- Pairwise combinations should be judged against the best single-mechanism score, not treated as automatically better.
- Because Stage 3 fits remain weak, this ablation ranking should be interpreted as provisional.
- The strongest value of this stage is identifying which mechanisms are ineffective or noisy under the current simulator.
- Ablation rankings should be shown with the Stage 2 sign-mismatch warning.
