# Audit And Production Plan

Date: 2026-06-23

This plan follows `docs/CODEBASE_IMAGE.md`. Implementation remains scoped to
small, verifiable increments. The project should be polished as a
PI-review-ready research-demo package while preserving the explicit boundary
that it is not a completed thesis until the motion/confound and archive DOI
gates close.

## Definition Of Done

- `docs/CODEBASE_IMAGE.md` and this plan exist and reflect the current repo.
- Public claim labels use only `implemented`, `proxy-supported`, `mixed`,
  `unsupported`, `blocked`, and `future`, except when quoting raw artifact
  implementation status explicitly.
- C is presented as the provisional leading macro-dynamic proxy, pending
  motion/confound proof and atlas-level replication.
- E is split into E1 lower transition/control-energy proxy support and E2
  receptor-specific placement, which remains unsupported/future.
- B remains visible as an implemented negative-control baseline and unsupported
  as the main control-theory claim.
- The dashboard preflight passes and the static site builds.
- Focused tests, full pytest, static build, and searches pass; any lint, type,
  dependency, or push/PR blocker is documented with exact command output.
- A coherent change set is committed and pushed, or the exact push/PR blocker is
  documented.

## Audit Tracks

Run these after the codebase image exists. Subagents may be used because the
user explicitly allowed them; delegated tracks should be read-only until this
plan's first implementation increment is selected.

| Track | Scope | Output |
| --- | --- | --- |
| Architecture/code quality | `src/lsd_thesis/`, `scripts/`, build side effects, generated artifact boundaries | File-specific risks and minimal patches |
| Scientific validity/reproducibility | claim grammar, motion/confound gates, ds003059/ds006072 wording, prior-art boundaries | Claim-safe wording and artifact provenance fixes |
| Dashboard/visualization/UX | FastAPI routes, static Pages, PI-review package, contract tests | Route/render/status-label issues |
| Testing/CI/build | pytest timeout, CI branch trigger, Pages workflow, focused tests | Verification matrix and CI blockers |
| Security/secrets/deployment | artifact serving, raw data boundaries, `.gitignore`, generated outputs, push readiness | Safety checklist and staging exclusions |
| Academic submission/docs | README, SPEC, PI review, evidence pages, email, meeting script | Professor-facing coherence fixes |

## Critical Issues

### C1. Public claim statuses leak raw implementation labels

Files:

- `results/dynamic_mechanism_ranking/summary.json`
- `docs/stage_reports/dynamic_mechanism_ranking.md`
- `docs/reports/pi_thesis_share_package/assets/data/mechanism_ranking_values.csv`
- `docs/reports/pi_thesis_share_package/deliverable_website/assets/data/mechanism_ranking_values.csv`
- `src/lsd_thesis/dynamic_mechanism/core.py`
- `src/lsd_thesis/dynamic_mechanism/hierarchy.py`
- `src/lsd_thesis/dynamic_mechanism/repertoire.py`
- `scripts/run_dynamic_mechanism_ranking.py`

Problem:

Public reports and PI-package CSVs show statuses such as
`implemented_first_pass` and `implemented_proxy_control_energy`, while project
rules allow only controlled public claim labels unless raw artifact status is
explicitly being quoted.

Proposed change:

- Preserve raw implementation status when needed for machine state.
- Add or use a public display status for ranking/report/export surfaces.
- Regenerate dynamic mechanism reports, exports, and PI-review derived CSVs.

Verification:

```powershell
uv run pytest tests/test_next_action_evidence_gates.py tests/test_result_artifact_schema_contract.py tests/test_dashboard_redesign_contract.py -q -o addopts=
uv run python scripts\run_dynamic_mechanism_ranking.py
uv run python scripts\export_dynamic_mechanism_tables.py
rg -n "supported_first_pass|implemented_first_pass|not_supported_yet|reject_as_main_claim|supported_proxy" docs\stage_reports docs\reports\pi_thesis_share_package _site
```

Current status:

- Implemented for public reports, stage report ranking tables, PI-review CSVs,
  and dashboard-visible ranking rows. Raw implementation status remains in
  internal JSON/source fields where it is machine-state metadata.

Rollback:

- Revert source changes and rerun the generator from the previous commit.
- Do not hand-edit `_site/` or individual generated copies.

### C2. Motion/confound gate must stay first-visible

Files:

- `results/thesis_upgrade/thesis_upgrade_status.json`
- `src/lsd_thesis/thesis_upgrade/gates.py`
- `src/lsd_thesis/templates/pages/submission.html`
- `docs/reports/pi_thesis_share_package/deliverable_website/OPEN_ME_FIRST.html`
- `docs/reports/pi_thesis_share_package/deliverable_website/pages/decision-gates.html`

Problem:

The strict motion gate remains blocked because fMRIPrep FD/DVARS/censoring
proof is missing. Polished dashboard language can make this look secondary.

Proposed change:

- Keep the blocker in first-read and decision-gate surfaces.
- Reject any wording that says motion artifacts are ruled out.
- Avoid introducing stronger C language until subject/run confounds exist.

Verification:

```powershell
uv run python scripts\build_thesis_upgrade_status.py
uv run python scripts\build_github_pages.py --repo-root D:\LSD_Thesis --site-dir D:\LSD_Thesis\_site
rg -n "motion|FD|DVARS|censor|blocked" _site\pi-review _site\dashboard
```

### C3. Archive publication gate is incomplete

Files:

- `results/reproducible_archive/ARCHIVE_MANIFEST.json`
- `docs/THESIS_READINESS_GATES.md`
- `docs/GITHUB_PAGES.md`
- PI-review package pages that mention archive status

Problem:

The archive manifest records the GitHub release URL, but DOI and publication
metadata fields are currently null. GitHub Pages and GitHub release status must
not be conflated with a citable archive.

Proposed change:

- Keep DOI missing unless a real DOI is provided.
- Make Pages/release/archive distinctions consistent in public pages.

Verification:

```powershell
uv run python scripts\build_reproducible_archive.py --release-url https://github.com/grimgrimberg/LSD_Thesis/releases/tag/thesis-evidence-2026-06-02
uv run python scripts\build_thesis_upgrade_status.py
rg -n "Zenodo|DOI|GitHub release|archive" docs README.md _site
```

## High Issues

### H1. Pytest collection timeout

Problem:

An initial `uv run pytest --collect-only -q -o addopts=` guard timed out after
120 seconds. The later cache-disabled collection probe and full pytest run
resolved this for the current pass.

Proposed investigation:

```powershell
uv run pytest --collect-only -vv -o addopts= tests
uv run pytest tests/test_next_action_evidence_gates.py -q -o addopts=
uv run pytest tests/test_dashboard_redesign_contract.py -q -o addopts=
```

If the timeout is import-time work, isolate the module and add a regression test
or lazy-load boundary.

Current status:

- Resolved for this pass with
  `uv run pytest --collect-only -q -o addopts= -p no:cacheprovider tests`
  collecting 87 tests in 36.87s.
- Full pytest also passed: `uv run pytest -q` reported 87 passed.

### H2. Generated artifact churn must be reviewed before staging

Problem:

`scripts/build_github_pages.py` and ranking/export scripts touch tracked result
JSON, CSV/XLSX, docs, and PI package copies. The current dirty tree already has
over 100 modified files.

Proposed handling:

- Review `git diff --stat` after every generator run.
- Stage coherent source/docs/generated bundles together.
- Do not stage `_site/`, raw `/data/`, `.venv/`, caches, or generated arrays.

Verification:

```powershell
git status --short
git diff --stat
git diff --check
```

### H3. Branch and CI trigger mismatch

Problem:

The current branch is `audit/full-cleanup-and-prior-art`. Push CI runs for
`main` and `codex/**`; PR CI should still run, but a plain push to the current
branch will not match the push branch pattern.

Proposed handling:

- Prefer a PR to trigger CI, or create/switch to a `codex/` branch before final
  push if that does not endanger existing dirty work.
- Do not force-push.

Verification:

```powershell
git branch --show-current
git remote -v
git status --short --branch
```

## Medium Issues

| Issue | Files | Proposed action | Verification |
| --- | --- | --- | --- |
| Context vocabulary | `CONTEXT.md`, public docs | Add canonical terms for PI-review-ready research demo and production academic submission | `rg -n "Production Academic Submission|PI-Review-Ready" CONTEXT.md` |
| Mechanism-proxy wording | `README.md`, `SPEC.md`, templates, stage reports | Keep "mechanism-proxy ranking" in public text | `rg -n "mechanism ranking|Mechanism Ranking" README.md SPEC.md AGENTS.md src scripts docs` |
| PI-review first-read hierarchy | `OPEN_ME_FIRST.html`, root router, Pages docs | Keep `/pi-review/` canonical and dashboard as technical console | Local route and Playwright/HTTP checks |
| Accessibility/static route quality | PI-review pages, dashboard templates | Check headings, links, wrapping, status labels | Playwright snapshots and static link checks |
| Dependency/security baseline | `pyproject.toml`, `uv.lock`, artifact serving | Run installed audits if available; otherwise document absence | `uv pip check`, `ruff`, guarded artifact tests |

## Verification Matrix

Minimum checks for the next implementation increment:

```powershell
node --check src\lsd_thesis\static\dashboard.js
uv run pytest tests/test_next_action_evidence_gates.py tests/test_result_artifact_schema_contract.py tests/test_dashboard_redesign_contract.py -q -o addopts=
uv run python scripts\preview_dashboard.py --check-only --strict
uv run python scripts\run_dynamic_mechanism_ranking.py
uv run python scripts\export_dynamic_mechanism_tables.py
uv run python scripts\build_github_pages.py --repo-root D:\LSD_Thesis --site-dir D:\LSD_Thesis\_site
uv run pytest --collect-only -q -o addopts= -p no:cacheprovider tests
uv run pytest -q
```

Search checks:

```powershell
rg -n "strongest implemented LSD mechanism layer|supported_first_pass|implemented_first_pass|not_supported_yet|reject_as_main_claim|supported_proxy|completed thesis" README.md SPEC.md AGENTS.md src scripts docs\stage_reports docs\reports\pi_thesis_share_package _site
rg -n "mechanism ranking|Mechanism Ranking" README.md SPEC.md AGENTS.md src scripts docs\stage_reports docs\reports\pi_thesis_share_package _site
```

Broader checks before commit/push, if the timeout is resolved or explained:

```powershell
uv run ruff check .
uv run mypy src
uv run pytest
uv pip check
```

## Dashboard Deliverables

- Local dashboard remains the full interactive FastAPI surface.
- Static `/dashboard/` remains the technical evidence console on Pages.
- `/pi-review/` remains the canonical first-read supervisor route.
- All dashboard and PI-review status labels must use public claim grammar.
- Data provenance and reproducibility sections must distinguish cached derived
  artifacts from raw neuroimaging data and from unavailable gates.

## GitHub Pages Deliverables

- Build `_site/` from `scripts/build_github_pages.py`.
- Verify root, `/pi-review/`, `/dashboard/`, decision gates, claim ledger,
  figure atlas, and evidence calculations locally.
- Keep `.nojekyll` generated if needed.
- Keep raw data, arrays, caches, and private state out of the site and commit.
- Preserve the archive statement: Pages is not the citable archive.

## Release And PR Plan

1. Finish the critical public-status cleanup.
2. Run focused verification and static build.
3. Inspect `git diff --stat`, `git diff --check`, and staged files.
4. Commit a coherent bundle with source, docs, tests, and generated tracked
   artifacts that are intentionally refreshed.
5. Push to a branch that can be reviewed. Prefer a PR path that triggers CI.
6. If push or PR creation fails, document the exact command and blocker instead
   of claiming publication.
