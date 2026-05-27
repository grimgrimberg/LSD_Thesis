# Stage 03 Result

## Status

Completed as a tested abstraction and dry-run preparation stage.

## Prompt

- `codex_prompt_pack/03_functional_parcellation_schaefer_yeo.md`

## Implemented

- Parcellation registry with `harvard_oxford_8` and `schaefer_100_yeo_7`.
- Node metadata schema for legacy and Schaefer/Yeo targets.
- Parcellation-specific output directories under `results/stage_2/parcellations/`.
- Dry-run CLI for metadata/plan generation.

## Partial Work

Full Schaefer/Yeo extraction was not run. No Schaefer/Yeo empirical target YAML files were fabricated.

## Validation

- Stage tests passed: `7 passed`.
- Dry-run CLI wrote metadata for both parcellations.
- Ruff passed on touched files.

