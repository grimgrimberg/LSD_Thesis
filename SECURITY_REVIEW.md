# Security Review

## Scope

Reviewed repository structure, ignore rules, obvious credential filenames, and broad secret-related keywords. No external services, credentials, or remote repositories were used.

## Findings

- Implemented: raw data under `/data/` is ignored by Git.
- Implemented: local virtualenv, caches, temp folders, generated outputs, and local agent state are ignored.
- Implemented: no `.env`, credential, token, SSH key, or PEM files were found by filename search outside ignored folders.
- Inferred: broad keyword matches in `tools/pptx/pptxgenjs_helpers/` appear to be source-code terminology rather than secrets.

## Current Git Safety

- Baseline commit: `75218fc`.
- Working branch: `refactor/research-audit-prototype-upgrade`.
- Local Git identity was set only for this repository: `Codex <codex@local.invalid>`.

## Data And Privacy

- ds003059 is a public OpenNeuro dataset, but raw downloaded files are large and should not be committed.
- Dashboard raw image previews are downsampled teaching/inspection artifacts, not clinical viewers.

## No-Secret Policy

- Do not print, edit, move, commit, or delete `.env`, keys, tokens, SSH material, cloud credentials, or local machine secrets.
- Do not add API keys or credentials for OpenNeuro, BioRender, Hugging Face, or any other service.
- If authentication is needed, stop and ask.

## Recommended Follow-Ups

- Add optional secret scanning in CI if the project moves to GitHub.
- Keep `/data/`, `/output/`, `.venv/`, `.codex/`, and `.superpowers/` ignored.
- Review generated publication packages manually before sharing outside the local machine.
