# Reproducible Archive Policy

## Purpose

GitHub Pages is a presentation surface. The thesis also needs a citable, reproducible archive that records source code, commands, derived aggregate artifacts, and checksums.

## Recommended Archive Stack

1. Public GitHub repository.
2. GitHub release for the exact thesis snapshot.
3. Zenodo DOI minted from the GitHub release.
4. Static GitHub Pages snapshot for reviewer browsing.
5. Archive manifest under `results/reproducible_archive/`.

## Artifact Tiers

| Tier | Role | Examples | Git policy |
| --- | --- | --- | --- |
| A | Tracked evidence and reproducibility metadata | Source code, configs, command docs, stage reports, selected JSON/YAML summaries, archive manifest, checksums, dataset identifiers, source URLs | May be tracked when curated and reviewable |
| B | Generated local outputs | `output/`, temporary review folders, Plotly HTML, generated figures, CSV exports, NPY/NPZ caches, empirical viewer payloads | Ignored by default; regenerate from commands |
| C | Forbidden or private artifacts | Raw OpenNeuro data, local `.venv/`, machine logs, `.env` files, tokens, SSH keys, cloud credentials | Never commit or archive |

## What Goes Into The Archive

- Tier A source code, configs, command docs, and stage reports.
- Publication-facing reports and static microsite snapshots when intentionally curated.
- Derived aggregate JSON/CSV/Markdown outputs selected for reproducibility.
- Claim/evidence matrices.
- Checksums for included artifacts.
- Dataset identifiers and source URLs.

## What Does Not Go Into The Archive

- Tier C raw OpenNeuro NIfTI/CIFTI files.
- Local `.venv/`, caches, temporary files, and machine-specific logs.
- `.env` files, tokens, credentials, SSH keys, or secrets.
- Tier B large generated files such as figures, Plotly HTML, NPY/NPZ caches, or empirical viewer payloads unless explicitly curated and justified.

## Serving And Export Rule

The dashboard may serve selected Tier A or curated Tier B files through `/artifacts/`, but only from allowlisted report/output/result roots. Serving a file locally does not make it safe to commit or include in an archive.

## Commands

```powershell
uv run python scripts/build_thesis_upgrade_status.py
uv run python scripts/build_reproducible_archive.py
```

After a real GitHub release exists and Zenodo has minted a DOI for that release, rebuild the manifest with citable publication metadata:

```powershell
uv run python scripts/build_reproducible_archive.py --release-url https://github.com/<owner>/<repo>/releases/tag/<tag> --doi 10.<prefix>/<suffix>
uv run python -c "from pathlib import Path; from lsd_thesis.thesis_upgrade import write_thesis_upgrade_status; write_thesis_upgrade_status(Path.cwd())"
```

Do not use placeholders. The archive gate only counts as ready when the manifest records a GitHub release URL shaped like `https://github.com/<owner>/<repo>/releases/tag/<tag>` and a DOI shaped like `10.<prefix>/<suffix>` or `https://doi.org/10.<prefix>/<suffix>`.

## Claim Guardrail

The archive improves reproducibility for code and derived aggregate artifacts. It does not create external validation, receptor-level validation, clinical evidence, or subjective-experience evidence.
