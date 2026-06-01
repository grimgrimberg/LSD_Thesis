# GitHub Pages Deployment

Purpose: publish a static, reviewer-facing version of the thesis microsite for this repository.

Audience: thesis reviewer, potential MSc supervisor, or technical reviewer who needs a stable web artifact without running the local dashboard.

## What Gets Published

- `index.html`: static thesis microsite generated from the current publication pipeline.
- `defense.html`: static defense-presentation companion page when available.
- `artifacts/claim_evidence_matrix.csv`: hiring-readiness claim matrix.
- `artifacts/claim_evidence_matrix.md`: Markdown version of the claim matrix.
- `artifacts/thesis_evidence_loop_tables.xlsx`: Excel workbook with exported evidence-loop tables.
- `artifacts/results/training/rocket_condition_benchmark/benchmark_report.md`: leak-proof ROCKET-style condition benchmark report when the local artifact exists.
- `artifacts/results/training/rocket_condition_benchmark/comparison_summary.json`: machine-readable ROCKET benchmark summary when the local artifact exists.
- `artifacts/results/thesis_upgrade/thesis_upgrade_status.md`: thesis-readiness gate report when generated.
- `artifacts/results/reproducible_archive/ARCHIVE_MANIFEST.json`: derived-artifact archive manifest when generated.
- `pages_manifest.json`: static-site manifest and claim guardrail.

## Local Build

```powershell
.\.venv\Scripts\python.exe scripts\build_github_pages.py
```

The generated site is written to `_site/`. `_site/` is a build artifact and should not be committed.

Before the public-dashboard package gate can pass, `_site` must be fresh against the current thesis-readiness artifact. Rebuild `results/thesis_upgrade/thesis_upgrade_status.json` first, then rebuild `_site`; the gate compares the copied `_site/artifacts/results/thesis_upgrade/thesis_upgrade_status.json` and embedded `_site/dashboard/dashboard-data.json` thesis status against the current strict readiness summary, non-dashboard gate states, strict requirements, and non-dashboard package requirements. File existence alone is not enough.

## GitHub Setup

1. Push this repo to GitHub.
2. In GitHub, open `Settings -> Pages`.
3. Set `Source` to `GitHub Actions`.
4. Run the `Deploy GitHub Pages` workflow manually, or push to `main`.

## Evidence Guardrail

The published site is a static presentation artifact. Blocked rows in the claim matrix remain blocked scientific work, not completed evidence. ROCKET benchmark rows are internal subject-disjoint proxy diagnostics only, not receptor-level, clinical, subjective-experience, or external-validation evidence. The reproducible archive target is a GitHub release plus Zenodo DOI backed by `results/reproducible_archive/ARCHIVE_MANIFEST.json`; GitHub Pages alone is not the citable archive. The local dashboard remains the stronger interactive review surface.
