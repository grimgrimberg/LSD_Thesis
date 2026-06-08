# 2026-05-31 Repository Audit And Roast

## Executive Summary

This repository is a Python 3.13 / uv research-engineering project for a transparent whole-brain surrogate model of altered-state-inspired macro-dynamics. It includes a FastAPI dashboard, static GitHub Pages export, publication/report generation, OpenNeuro data ingestion helpers, and Node/PptxGenJS deck tooling.

Current engineering health rating: 8.7/10. Release/thesis-submission readiness: B. The configured local and hosted quality gates are green: full pytest, ruff, mypy, dashboard preview preflight, package compatibility, npm audit, PPTX syntax checks, and hosted CI Quality have passed on the active branch. The rating is not higher because strict thesis completion still depends on external fMRIPrep FD/DVARS/censoring motion proof, and several research modules remain large enough to merit continued decomposition.

Top remaining risks:
- Strict thesis completion still fails closed on fMRIPrep FD/DVARS/censoring motion proof because the local ds003059 snapshot is derivative-like and lacks subject/session/run confounds.
- Architecture is improved but still has large modules, especially `fit.py`, `dynamic_mechanism.py`, `dynamic_robustness.py`, and `thesis_upgrade.py`.
- `web/app.py` is no longer carrying artifact policy, empirical-viewer policy, status payload policy, or structural-DTI payload policy, but it still owns multiple dashboard payload loaders and route orchestration.
- The regenerated thesis-upgrade artifact now says `research_demo_ready_not_completed_thesis`, but older generated artifacts still record historical dirty commit metadata and should be treated as provenance snapshots.
- The working directory has many pre-existing untracked generated artifacts; they were not deleted because repo instructions forbid deleting raw/generated outputs without confirmation.

## What Changed

- `.github/workflows/ci.yml`: added a CI Quality workflow for PRs, pushes to `main` and `codex/**`, and manual dispatch. It runs `uv pip check`, full `uv run ruff check .`, full `uv run mypy src`, full `uv run pytest`, `npm audit`, and the PPTX syntax test.
- `.gitignore`: added local secret and credential patterns such as `.env`, `.env.*`, `*.pem`, and `*.key`.
- `pyproject.toml`: added `.` to pytest `pythonpath` so tests can import repository `scripts/` consistently.
- Python cleanup: made full-repo ruff and mypy pass with explicit `zip(..., strict=...)`, dead-code/import cleanup, typed payload dictionaries, NumPy/nibabel boundary casts, safer optional handling, and line-wrapped research strings.
- `src/lsd_thesis/data/ds003059.py`: when raw run-file hashes change, cache validation now reports the specific raw-file fingerprint failure before the generic fingerprint mismatch.
- `src/lsd_thesis/publication_html.py`: publication figure image sources now pass through the same unsafe-scheme guard used for markdown links.
- `scripts/build_github_pages.py`: dashboard artifact copying now decodes and normalizes links, rejects traversal segments, resolves canonical paths, and verifies copied sources stay under allowed artifact roots.
- `COMMANDS.md`: refreshed stale environment notes and command-result evidence for the current 316-test, 67-source-file state.
- `README.md` and `results/thesis_upgrade/thesis_upgrade_status.json`: corrected stale run-02/motion boundary wording and regenerated thesis readiness so proxy/stress-test evidence no longer labels the whole project as a completed neuroscience thesis.
- Tests: added regressions for ignored secret files, unsafe publication image sources, dashboard artifact traversal links, and preserved q-value/import-order hygiene.
- Follow-up hardening through 2026-06-01: dashboard `innerHTML` injection sinks are now banned by repo-hygiene tests; generated-artifact policy is documented/tested; hosted CI has passed repeatedly; `web/app.py` has been split into artifact, empirical-viewer, status-payload, simulation-payload, and structural-DTI modules; `dynamic_mechanism.py` now delegates priors/masks, stat helpers, and paired metric-row collection to public helper modules.

## Validation Performed

Passing:
- `uv run ruff check .`: all checks passed.
- `uv run mypy src`: success, no issues in 76 source files.
- `uv run pytest`: 351 passed, 4 warnings, total coverage 79.90%.
- `uv run python scripts\preview_dashboard.py --check-only --strict`: required files and optional generated artifacts present; CV5 internal validation reports 5/5 folds.
- `uv pip check`: all installed packages compatible.
- `npm audit --prefix tools\pptx --audit-level=moderate`: 0 vulnerabilities.
- `npm test --prefix tools\pptx`: passed via `node --check build_defense_deck.mjs`.
- `git diff --check`: no whitespace errors; only Windows LF-to-CRLF warnings.
- Hosted CI Quality: latest checked branch run passed.

Still failing:
- No configured local quality gate is failing after this cleanup.

Not verified here:
- Manual browser inspection of the dashboard after these mostly non-visual changes.

## Independent Context-Free Audit

A context-free `gpt-5.5` auditor reviewed the cleaned repo after the local gate work. It did not have nested subagent execution available, so it used parallel read-only command lanes instead. Its rating was B-, primarily because local gates were green but provenance, generated-artifact hygiene, and claim/readiness wording still had release-readiness risk.

Findings folded into this pass:
- Fixed the strongest thesis-readiness contradiction: `results/thesis_upgrade/thesis_upgrade_status.json` no longer says `completed_neuroscience_thesis` while also requiring future FD/DVARS and external-validation upgrades.
- Fixed stale README wording about run-02 and committed-baseline provenance.
- Subsequent follow-up closed the broad dashboard `innerHTML` cleanup, generated-artifact policy, hosted CI verification, and several dashboard/dynamic-mechanism architecture splits. Remaining architecture work is now narrower and centered on still-large research modules.

## Roast

- The repo used to document full `ruff` and `mypy` commands while both were red. A command in docs is not a standard unless it can pass. This is now fixed.
- CI used to be basically a brochure printer. The Pages workflow could manually build a static site artifact, but no automated test/lint/type signal guarded code changes. The new workflow is the quality gate that should have existed already.
- `web/app.py` is still doing route handling and some dashboard payload orchestration. It is much smaller than before, but continued extraction is still worthwhile.
- The dashboard template no longer carries broad string-HTML injection sinks; keep the hygiene test in place so that does not regress.
- The static Pages artifact copier trusted prefix checks too much before this pass. Prefix checks are not path security; canonical resolution is path security.
- Publication HTML link sanitization protected markdown anchors but not image sources before this pass. That inconsistency is now fixed.
- The science framing remains better than average, but repeated caveats and current-rank wording still risk drifting across docs and payload builders.

## Prioritized Backlog

P0: before broad public/production demo
- Obtain or generate authorized subject/session/run fMRIPrep FD/DVARS/censoring confounds, then rerun the strict motion gate.
- Keep strict thesis status at `research_demo_ready_not_completed_thesis` until that motion gate passes.

P1: should fix soon
- Continue splitting residual dashboard payload loaders out of `src/lsd_thesis/web/app.py`.
- Continue splitting large dynamic-mechanism and robustness summary concerns behind public helper interfaces.
- Centralize run-02 wording and claim guardrail text in one module/doc source.
- Add a pre-commit config now that full lint/type/test policy is coherent enough to enforce.

P2: cleanup
- Remove duplicated `pytest-cov` dependency declaration only with a matching `uv.lock` update.
- Split fitting logic from reporting/artifact generation in `fit.py`.
- Add malformed JSON fallback tests for `/api/dashboard-data`.
- Add more URL-encoded traversal cases for `/artifacts`.

P3: nice-to-have
- Consider automatic GitHub Pages deployment if publishing from this repo is intended.
- Add a short architecture map for the dashboard/reporting pipeline.

## Recommended Scripts, Hooks, MCP, And Skills

- Keep as blocking gates: `uv run ruff check .`, `uv run mypy src`, `uv run pytest`, `uv pip check`, `npm audit --prefix tools\pptx --audit-level=moderate`, and `npm test --prefix tools\pptx`.
- Added: CI Quality workflow that enforces the full local gate set.
- Hooks: add pre-commit now that repeated hosted CI runs have confirmed Linux parity.
- MCP: a connected GitHub MCP would help inspect remote PR/CI context; depwire was available but not connected to this repo.
- Skills used: Superpowers planning/parallel-agent/debugging/TDD/verification; Codex Security guidance informed the security slice, but this was not a full exhaustive Codex Security ledger scan.

## Final Recommendation

This is now suitable for serious research development and controlled demos. Do not market it as a completed neuroscience thesis until the fMRIPrep FD/DVARS/censoring motion gate is satisfied, but the repository now has a real automated quality baseline and materially cleaner dashboard/mechanism architecture.
