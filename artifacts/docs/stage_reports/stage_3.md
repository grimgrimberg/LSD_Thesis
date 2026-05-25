# Stage 3 Report

## Plan

- Fit a sober reference regime.
- Apply four one-at-a-time perturbation mechanisms across a small strength grid.
- Rank them against ds003059-derived LSD minus placebo macro delta targets.

## Best Mechanism

- Mechanism: `less_hierarchical_constraint`
- Strength: `0.25`
- Score: `3481.5367`

## Seed-Panel Robustness

- Seed panel: `11, 12, 13, 14, 15`
- Robust best mechanism: `more_cross_talk`
- Robust best strength: `0.10`
- Robust mean score: `13.0935`
- Robust score standard deviation: `6.3777`
- Robust target-sign agreement: `0.75`
- Seed-noise null mean score: `36.9287`

## Sign-Mismatch Warning

- The current ds003059 extraction should be compared against the literature-style target signs before interpreting the ranking.
- Known conflicts under the current 8-module proxy are `within_network_stability`, `entropy_diversity`, and `metastability_proxy`.
- The useful Stage 3 result is the ranking and mismatch profile, not an absolute mechanistic match.

## Critical Review

- No subject-disjoint split file is configured for this Stage 3 run.
- The current surrogate still underexpresses the ds003059 delta magnitudes; the best mechanism moves in the right direction but too weakly.
- The coarse anatomical module mapping preserves some cross-network and thalamic shifts, but not a clean canonical psychedelic signature across all metrics.
- The result should be treated as a ranked hypothesis list, not a mechanistic conclusion.
- Candidate fit quality should be rechecked across a fixed seed panel before using the ranking as thesis evidence.
