# Reproducible Archive Policy

## Purpose

GitHub Pages is a presentation surface. The thesis also needs a citable, reproducible archive that records source code, commands, derived aggregate artifacts, and checksums.

## Recommended Archive Stack

1. Public GitHub repository.
2. GitHub release for the exact thesis snapshot.
3. Zenodo DOI minted from the GitHub release.
4. Static GitHub Pages snapshot for reviewer browsing.
5. Archive manifest under `results/reproducible_archive/`.

## What Goes Into The Archive

- Source code.
- Configs.
- Command docs.
- Thesis reports and static microsite.
- Derived aggregate JSON/CSV/Markdown outputs.
- Claim/evidence matrices.
- Checksums for included artifacts.
- Dataset identifiers and source URLs.

## What Does Not Go Into The Archive

- Raw OpenNeuro NIfTI/CIFTI files.
- Local `.venv/`, caches, temporary files, and machine-specific logs.
- `.env` files, tokens, credentials, SSH keys, or secrets.
- Large NPY/NPZ caches unless explicitly curated and justified.

## Commands

```powershell
uv run python scripts/build_thesis_upgrade_status.py
uv run python scripts/build_reproducible_archive.py
```

## Claim Guardrail

The archive improves reproducibility for code and derived aggregate artifacts. It does not create external validation, receptor-level validation, clinical evidence, or subjective-experience evidence.
