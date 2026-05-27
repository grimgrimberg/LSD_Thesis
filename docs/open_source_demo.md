# Open-source Demo Plan

## Demo promise

Show a reproducible surrogate-modeling workflow that connects real placebo/LSD resting-state fMRI summaries to transparent model comparisons.

## First screen

Use the existing dashboard for the legacy model and empirical explorer. Add static links to the new Stage 2b and Stage 5 artifacts before attempting a larger dashboard rewrite.

## Demo path

1. Run Stage 2b target validation.
2. Run quick Stage 5 receptor/gradient fit.
3. Open the Stage 2b report and Stage 5 report.
4. Open the leak-proof ROCKET benchmark report and note that condition prediction is subject-disjoint and aggregated at `subject/session/run`.
5. Open the thesis-upgrade gate report and archive manifest to show what is ready, proxy-only, or blocked.
6. Compare old Stage 4 failure modes against the new objective leaderboard.
7. Emphasize that the result is a macro-dynamic model comparison, not a subjective-experience model.

## Commands

```bash
uv run python scripts/run_pipeline.py stage-2b-target-validation --parcellation harvard_oxford_8
uv run python scripts/run_pipeline.py run-stage-5 --model receptor_gradient_neural_mass --quick
uv run python scripts/benchmark_rocket_condition_models.py --cv5-manifest output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json --n-kernels 128
uv run python scripts/build_thesis_upgrade_status.py
uv run python scripts/build_external_ingestion_status.py
uv run python scripts/build_reproducible_archive.py
uv run python scripts/run_dashboard.py
```

## Artifacts to show

- `docs/stage_reports/stage_2b.md`
- `docs/stage_reports/stage_5.md`
- `results/stage_2b/target_reliability_summary.json`
- `results/stage_5/ablation_leaderboard.csv`
- `results/stage_5/sign_match_table.csv`
- `results/stage_5/overshoot_table.csv`
- `results/training/rocket_condition_benchmark/benchmark_report.md`
- `results/training/rocket_condition_benchmark/comparison_summary.json`
- `results/thesis_upgrade/thesis_upgrade_status.md`
- `results/external_ingestion/external_ingestion_status.json`
- `results/reproducible_archive/ARCHIVE_MANIFEST.json`

## Guardrail language

"This is a transparent surrogate pipeline for macro-scale fMRI dynamics. It ranks model perturbation hypotheses and reports failures. It does not simulate receptors, consciousness, clinical outcomes, or subjective psychedelic experience."
