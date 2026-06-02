# ROCKET Condition Benchmark

- CV: `approved CV5 subject-disjoint manifest`
- Primary unit: `subject_session_run_aggregated_windows`
- Window-random reporting: `false`
- Kernels: 512 (1024 features)
- Subjects: 15
- Windows: 600

## Primary Subject/Run Aggregated Metrics

- Accuracy: 0.667 +/- 0.053
- Balanced accuracy: 0.667 +/- 0.053
- ROC AUC: 0.711 +/- 0.078

## Fold Metrics

| Fold | Held-out subjects | Aggregation units | Balanced accuracy | ROC AUC |
| ---: | --- | ---: | ---: | ---: |
| 1 | sub-011, sub-015, sub-020 | 12 | 0.667 | 0.667 |
| 2 | sub-002, sub-017, sub-018 | 12 | 0.667 | 0.806 |
| 3 | sub-001, sub-003, sub-012 | 12 | 0.667 | 0.583 |
| 4 | sub-004, sub-009, sub-019 | 12 | 0.750 | 0.750 |
| 5 | sub-006, sub-010, sub-013 | 12 | 0.583 | 0.750 |

## Guardrails

- Primary reporting aggregates window probabilities to subject/session/run units.
- Raw window-level metrics are secondary diagnostics only.
- No random window-level train/test split is used.
- ROCKET results are internal subject-disjoint proxy classification diagnostics. They are not receptor-level, clinical, subjective-experience, or external-validity evidence.
