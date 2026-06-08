# Changelog

## Unreleased

### Added

- Root-level goal, plan, repository inventory, thesis concept audit, codebase audit, architecture, commands, roadmap, security, test, metrics, visual, BioRender brief, executive summary, current state, and next steps documents.
- Repo hygiene helper and test to ensure source files are not hidden by Git ignore rules.
- Publication figure rendering CLI and tests.
- Degenerate metric tests for finite FC/observable outputs and constant-window eigenspectrum targets.

### Changed

- Tightened `.gitignore` for lean research-prototype tracking.
- Root-anchored `/data/` so source code under `src/lsd_thesis/data/` remains trackable.
- Sorted imports and removed unused lint-only code in `src/lsd_thesis/data/ds003059.py`.
- Reused a finite correlation matrix helper across summary metrics and condition-model FC features.

### Fixed

- Prevented raw data ignore rules from hiding empirical ingestion source files.
- Brought newly tracked data-ingestion source under Ruff compliance.
- Avoided NaN/Inf FC and single-state entropy outputs for degenerate time series.
- Avoided RuntimeWarnings for constant-window FC eigenspectrum targets.

### Safety

- Created baseline commit `75218fc` before audit/refactor work.
- Created working branch `refactor/research-audit-prototype-upgrade`.
