# Next Steps

## Immediate

1. Keep the repo hygiene test green so source directories cannot be ignored accidentally. Done.
2. Run the final smoke/lint/type checks and update `TEST_REPORT.md`. Done for the audit phase; rerun after each new change.
3. Commit the audit and hardening phase. Done.

## Short-Term Engineering

1. Add a `slow` marker to metric-heavy or data-heavy tests if full pytest remains too slow.
2. Add no-NaN/no-Inf assertions for simulation and observable summaries. Partially done for degenerate metric inputs and constant-window eigen spectra.
3. Add a stage-1 command smoke test if runtime stays acceptable. Existing reporting tests cover temp-path Stage 1 generation; add command-level coverage only if needed.
4. Make generated stage summaries include current Git commit and dirty-state provenance after future regenerations. Current summaries now include branch and commit hash; dirty status reflects in-flight local changes during regeneration.

## Short-Term Research

1. Re-run Stage 3 and Stage 4 with fixed seed panels as default evidence.
2. Add atlas sensitivity planning or a second coarse module mapping.
3. Build a professor-facing visual script that starts with sign conflicts and mismatch analysis.
4. Keep perturbation mechanisms named as model operations, not biological mechanisms.
5. Consider committing a clean-provenance regeneration pass after the code/docs settle, if you want stage summaries to report a clean worktree.
6. Decide whether to suppress or explicitly assert the remaining single-row empirical viewer fixture warnings.

## Do Not Do Without Confirmation

- Delete raw data or generated outputs.
- Replace the model architecture.
- Change dataset formats.
- Add heavy dependencies.
- Strengthen thesis claims beyond macro-scale surrogate framing.
