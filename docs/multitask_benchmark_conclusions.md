# Multitask Benchmark Conclusions

Date: 2026-04-14

This note summarizes what the current local learning benchmarks actually show on the exported `ds003059` resting-state windows.

## Scope

Dataset:
- `results/training/ds003059_windows.npz`
- `600` windows
- `15` paired subjects
- window shape `64 x 8`
- evaluation: `LeaveOneGroupOut(subject)`

Benchmarks:
- condition-only benchmark in `results/training/condition_benchmark/`
- multitask spectral benchmark in `results/training/multitask_benchmark/`

## Condition-Only Benchmark

Task:
- predict `LSD vs placebo` from each exported window

Ranking:

| Model | Balanced Accuracy | ROC AUC |
| --- | --- | --- |
| `temporal_cnn` | `0.595 ± 0.125` | `0.719 ± 0.176` |
| `logistic_regression` | `0.577 ± 0.115` | `0.645 ± 0.197` |
| `hist_gradient_boosting` | `0.565 ± 0.109` | `0.613 ± 0.172` |

Conclusion:
- the raw windows do contain usable condition signal
- the signal is modest, not strong
- a small temporal CNN is better than the engineered-feature classifiers for this task

## Multitask Spectral Benchmark

Task:
- predict `LSD vs placebo`
- regress the descending eigenvalues of each window's `8 x 8` FC matrix

Ranking:

| Model | Balanced Accuracy | ROC AUC | Eigen MAE | Eigen RMSE | Eigen R2 |
| --- | --- | --- | --- | --- | --- |
| `hist_gradient_multitask` | `0.573 ± 0.109` | `0.595 ± 0.150` | `0.096 ± 0.012` | `0.137 ± 0.018` | `0.262 ± 0.216` |
| `multitask_temporal_cnn` | `0.620 ± 0.110` | `0.712 ± 0.173` | `0.121 ± 0.012` | `0.178 ± 0.021` | `0.129 ± 0.193` |
| `ridge_multitask` | `0.580 ± 0.101` | `0.662 ± 0.181` | `0.116 ± 0.026` | `0.169 ± 0.043` | `0.043 ± 0.477` |

Conclusion:
- the multitask CNN is the best current condition classifier
- the engineered FC-feature boosting baseline is the best current eigenvalue regressor
- right now, the explicit FC geometry is a stronger route into spectral targets than the raw-window DNN alone

## What This Means

The repo now supports two defensible statements:

1. A small learned temporal model can extract some altered-state-inspired condition signal from the exported macro-module windows.
2. The current graph-informed engineered features remain the strongest bridge from empirical windows to FC eigenspectra.

The repo does not yet support a stronger claim that a raw-window DNN has learned the best graph-level projection of the empirical data. The spectral regression results still favor the engineered baseline.

## Recommended Next Step

The best next experiment is not a larger classifier. It is a hybrid model that combines:
- raw window input
- engineered FC / summary features
- multitask heads for condition and graph-level spectral targets

That keeps the project aligned with the surrogate-model framing:
- macro-scale analogue
- graph-modulated dynamics
- transparent empirical-to-graph projection

It does not require any claim about receptor realism or subjective-state decoding.
