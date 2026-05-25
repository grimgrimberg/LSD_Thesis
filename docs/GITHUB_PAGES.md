# GitHub Pages Deployment

Purpose: publish a static, reviewer-facing version of the thesis microsite for this repository.

Audience: thesis reviewer, potential MSc supervisor, or technical reviewer who needs a stable web artifact without running the local dashboard.

## What Gets Published

- `index.html`: static thesis microsite generated from the current publication pipeline.
- `defense.html`: static defense-presentation companion page when available.
- `artifacts/claim_evidence_matrix.csv`: hiring-readiness claim matrix.
- `artifacts/claim_evidence_matrix.md`: Markdown version of the claim matrix.
- `artifacts/thesis_evidence_loop_tables.xlsx`: Excel workbook with exported evidence-loop tables.
- `pages_manifest.json`: static-site manifest and claim guardrail.

## Local Build

```powershell
.\.venv\Scripts\python.exe scripts\build_github_pages.py
```

The generated site is written to `_site/`. `_site/` is a build artifact and should not be committed.

## GitHub Setup

1. Push this repo to GitHub.
2. In GitHub, open `Settings -> Pages`.
3. Set `Source` to `GitHub Actions`.
4. Run the `Deploy GitHub Pages` workflow manually, or push to `main`.

## Evidence Guardrail

The published site is a static presentation artifact. Blocked rows in the claim matrix remain blocked scientific work, not completed evidence. The local dashboard remains the stronger interactive review surface.
