# MCP Usage And Security

Date: 2026-05-12

Scope: PASS 1 inventory and safe usage policy for the Set / Setting / Seed extension.

## Detected MCP Servers

Command:

```powershell
codex mcp list
```

Detected servers:

| Server | Connection | Auth | PASS 1 decision |
|---|---|---|---|
| `depwire` | `npx -y depwire-cli mcp`, cwd `C:\` | unsupported | Avoided for private-code analysis |
| `playwright` | `npx -y @playwright/mcp@latest` | unsupported | Available, not used in PASS 1 |
| `context7` | `https://mcp.context7.com/mcp` | OAuth | Used for public package documentation |
| `figma` | `https://mcp.figma.com/mcp` | OAuth | Available, not used |
| `linear` | `https://mcp.linear.app/mcp` | OAuth | Available, not used |

Observed command warnings:

- Some stale temporary `arg0` paths were inaccessible.
- PATH update warning appeared.

These warnings did not block PASS 1.

## Detected Skills

`codex skills list` is not available in this environment. Skills were detected from the active session skill registry and local skill files.

Relevant available skills included:

- `superpowers:using-superpowers`
- `superpowers:dispatching-parallel-agents`
- `superpowers:writing-plans`
- `superpowers:verification-before-completion`
- `superpowers:systematic-debugging`
- `superpowers:test-driven-development`
- `life-science-research:research-router-skill`
- `security-best-practices`
- `frontend-testing-debugging`
- `playwright`
- `browser-use:browser`
- `figma`
- GitHub, Google Drive, Hugging Face, and other connector-oriented skills

Skills used in PASS 1:

- Superpowers process skills for planning, parallel read-only review, and verification discipline.
- Life-science research router for organizing literature lanes.
- Security and frontend-testing guidance for MCP/data-boundary and dashboard planning.

No skills were used to mutate production code.

## PASS 2A MCP And Tool Update

PASS 2A briefly re-checked MCP availability with `codex mcp list`; the detected server list remained `depwire`, `playwright`, `context7`, `figma`, and `linear`.

PASS 2A used:

- local shell commands for repo inspection, tests, scripts, and artifact generation,
- local skills from the session/filesystem for TDD, verification, frontend, and security guidance,
- read-only subagents for implementation planning and review,
- Playwright MCP for a local-only dashboard smoke test and screenshot after the dashboard/microsite build.

PASS 2A avoided:

- `depwire`, because private-code indexing was not necessary and remains a metadata-exfiltration risk,
- `context7`, because no new public package API lookup was needed,
- `figma` and `linear`, because no mockup or task-system action was needed.

No raw neuroimaging data, generated arrays, source trees, secrets, environment variables, or subject-level result bundles were sent to remote MCPs.

Playwright visited only:

- `http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html`

Screenshot artifact:

- `results/setting_seed/dashboard/screenshots/pass2a_microsite.png`

## PASS 2B-0 MCP And Skill Update

PASS 2B-0 re-checked MCP availability with:

```powershell
codex mcp list
```

Detected servers remained:

- `depwire`
- `playwright`
- `context7`
- `figma`
- `linear`

PASS 2B-0 used:

- local shell commands for repo inspection, tests, and artifact generation,
- `life-science-research:research-router-skill` to route the QC/scientific-readiness question,
- Superpowers TDD and verification skills from the local skill registry,
- read-only subagents for Stage 2 extraction, motion/QC, and scientific/security review.

PASS 2B-0 used Playwright MCP after the static dashboard artifact changed:

- `http://127.0.0.1:8000/artifacts/output/doc/set_setting_seed_microsite.html`
- `http://127.0.0.1:8000/`

Both routes loaded successfully. Playwright recorded local page snapshots; no raw neuroimaging data or external pages were used.

PASS 2B-0 otherwise avoided remote MCP calls:

- `depwire` avoided because private-code indexing was unnecessary and still a metadata-exfiltration risk,
- `context7` not needed because no public package API clarification was required,
- `figma` and `linear` not relevant.

No private source code, file trees, raw neuroimaging data, cached arrays, secrets, environment variables, or subject-level result bundles were sent to remote MCPs. Generated dashboard payloads expose readiness booleans and aggregate QC status only; raw motion traces and confound matrices must not be embedded in `/api/dashboard-data`.

## Life Science Research Review Update

After PASS 2A, the Life Science Research plugin was used explicitly for a repo/result scientific review.

Skills used:

- `life-science-research:research-router-skill`
- `life-science-research:ncbi-entrez-skill`

Safe usage:

- Entrez calls used public PubMed metadata queries only.
- No private source code, raw neuroimaging data, local file tree, local paths, subject-level outputs, generated arrays, secrets, or unpublished thesis drafts were sent.
- Initial Entrez calls failed in the sandbox because network access was routed to a disabled local proxy; public PubMed calls were then rerun with approved network escalation.

Queries:

- `LSD fMRI thalamic connectivity`
- `LSD music fMRI setting psychedelic`
- `psychedelic fMRI dynamic functional connectivity entropy brain`
- `network control theory psychedelics fMRI brain`
- `OpenNeuro ds003059 LSD fMRI`

Outcome:

- The targeted music-setting query returned zero PubMed records.
- The review reinforced that music-control analysis must remain scaffolded until local run-02 module time series exist.
- The review artifact is `docs/LIFE_SCIENCE_RESEARCH_REVIEW.md`.

## 2026-05-14 Rerun And Live Review Update

User-requested skills/plugins:

- `grill-with-docs`
- `life-science-research`
- Playwright MCP for local dashboard evidence after serving the page

Used:

- `grill-with-docs` local skill file to resolve the overloaded term "everything" into repo terminology and capture it in `CONTEXT.md`.
- `life-science-research:research-router-skill` local routing guidance to classify the scholarly scan into literature/methods lanes.
- Public web scholarly lookup for articles and DOI pages; no private repo data were sent.
- Playwright MCP only against `http://127.0.0.1:8020/` after the dashboard was served locally.

Avoided:

- `depwire`, because private-code indexing was not needed for this rerun and remains unnecessary for public literature lookup.
- `figma` and `linear`, because no UI mockup or task-system action was requested.
- remote data/dataset tools for local source-code or artifact inspection.

Playwright local evidence:

- dashboard route: `http://127.0.0.1:8020/`, title `Whole-Brain Surrogate Dashboard`;
- microsite route: `http://127.0.0.1:8020/artifacts/output/doc/set_setting_seed_microsite.html`, title `Set / Setting / Seed`;
- screenshot copied to `results/setting_seed/dashboard/screenshots/set_setting_seed_live_8020.png`.

Data not sent to remote tools:

- private source code,
- local file tree dumps,
- raw neuroimaging data,
- cached `.npy` arrays,
- subject-level result bundles,
- local paths beyond the localhost URLs needed for Playwright,
- secrets, tokens, or environment variables.

## MCPs Used In PASS 1

### Context7

Used for public package documentation only:

- PyDMD / DMDc documentation.
- PySINDy / SINDy with control documentation.
- FastAPI template and response documentation.

Appropriate because:

- Queries contained package names and public API questions.
- No private source tree, raw data, generated arrays, credentials, or unpublished thesis drafts were sent.

### Web Search

Used for live literature and methods research. This was not an MCP server, but it was an external research tool.

Appropriate because:

- Queries targeted primary papers, DOI pages, official docs, and reproducible package docs.
- No private source code or raw data were uploaded.

### Subagents

Used for read-only local review:

- Repo Cartographer.
- Security / MCP Gatekeeper.
- Neuroimaging Analyst.
- Literature Scout.
- ML Skeptic / Control Systems Engineer.
- UI/UX Strategist and QA Engineer.

Appropriate because:

- The user explicitly requested subagents if available.
- Tasks were bounded and inspection-only.
- No subagent was asked to implement PASS 2.

## MCPs Avoided

### Depwire

Avoided because the user flagged private-code analysis tools as a metadata-exfiltration risk unless clearly justified.

Safe future use would require:

- explicit user approval,
- a clear reason,
- package-manifest or dependency-level scope only,
- no private source upload or indexing.

### Playwright / Browser

Available but not used in PASS 1 because:

- No dashboard implementation changed.
- PASS 1 required architecture inspection, not a live visual regression test.

Safe future use:

- local dashboard only,
- `http://127.0.0.1:8000/`,
- screenshots of rendered dashboard state,
- no authenticated external pages,
- no raw neuroimaging files displayed or uploaded.

### Figma

Available but not used because PASS 1 did not require mockups.

Safe future use:

- UI ideation with abstract dashboard layouts,
- no private source-code upload,
- no subject-level data,
- no unpublished thesis text unless the user intentionally requests it.

### Linear

Available but not used because no Linear issue workflow was requested.

Safe future use:

- high-level task summaries only,
- no raw data, credentials, or generated artifacts.

### GitHub

No GitHub MCP/connector call was needed for PASS 1.

Safe future use:

- branch, PR, issue, or CI work for this exact repo only when authorized,
- never push raw `/data`, generated arrays, secrets, credentials, or large outputs.

### Hugging Face

Not used.

Safe future use:

- public package/model/dataset documentation lookup,
- never upload raw `/data` or cached `.npy/.npz` files without explicit user approval,
- cloud training only after visibility, license, and retention are confirmed.

### Google Drive

Not used.

Safe future use:

- only if the user's thesis docs or notes are intentionally stored there and already authorized,
- curated docs only,
- no raw data or secrets.

## Data That Must Not Be Sent To Remote Tools

Do not send, upload, index, paste, or expose:

- `.env` files,
- API keys,
- tokens,
- SSH keys,
- cloud credentials,
- raw `/data` neuroimaging files,
- generated arrays (`.npy`, `.npz`),
- subject-level derived time-series files unless explicitly approved,
- large generated results,
- private unpublished thesis drafts unless the user intentionally requests that destination,
- full private source-code trees,
- environment variables,
- local machine paths that reveal credentials or private infrastructure.

## Safe Usage Patterns

### GitHub

Use for:

- PRs,
- issues,
- CI status,
- branch publishing,
- review comments.

Guardrails:

- inspect staged files before commit or push,
- exclude `/data`, `/output`, `.venv`, `.codex`, `.superpowers`, caches, secrets, and generated arrays,
- do not publish unpublished thesis artifacts without user intent.

### Browser / Playwright

Use for:

- local dashboard smoke tests,
- local screenshots,
- route and interaction checks.

Guardrails:

- prefer `127.0.0.1`,
- avoid authenticated pages,
- avoid exposing raw subject data in screenshots,
- close or stop local servers after testing when no longer needed.

### Literature MCPs Or Web Search

Use for:

- primary papers,
- DOI metadata,
- official package docs,
- reproducible method documentation.

Guardrails:

- no private code or data,
- record source type and thesis-use boundary,
- distinguish facts, methods, hypotheses, and analogies.

### Hugging Face

Use for:

- documentation,
- public package examples,
- model/dataset metadata.

Guardrails:

- no raw data upload,
- no generated `.npz` upload without explicit approval,
- document visibility/license/retention before cloud jobs.

### Figma / Canva

Use for:

- dashboard visual ideation,
- abstract diagrams,
- public-safe mockups.

Guardrails:

- no private source-code analysis,
- no raw data,
- no subject-level artifacts,
- no unpublished thesis text unless user requests it.

### Google Drive

Use for:

- authorized thesis docs,
- curated summaries,
- user-requested shared documents.

Guardrails:

- confirm destination,
- avoid raw data and secrets,
- avoid broad folder scans unless required.

## Project-Scoped `.codex/config.toml` Recommendation

No project-scoped `.codex/config.toml` is necessary for PASS 1.

If PASS 2 repeatedly needs the same safe local commands, prefer documenting them in `docs/CODEX_RUNBOOK.md` first. Add project config only when there is a stable, low-risk repo-specific need that cannot be captured by docs or existing AGENTS instructions.
