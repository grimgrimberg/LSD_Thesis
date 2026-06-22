# PI-Review Public Website Rebuild Design

Source blueprint: `C:\Users\yuval\Documents\Codex\2026-06-22\https-grimgrimberg-github-io-lsd-thesis\outputs\lsd_thesis_second_pass_roast_reorg.md`

Design approval basis: user supplied the blueprint and directed "so do it" on 2026-06-22.

## Goal

Rebuild the public LSD Thesis website so the first public read is a PI-review-first, scientifically defensible evidence package: research-demo mechanism-proxy workbench; C is the current leading proxy; E is mixed; B is negative; motion/confound proof and DOI/archive completion remain blocking gates.

## Non-Goals

- Do not run new scientific analyses, large downloads, run-02/music extraction, PET/SC/neuromaps expansion, or external dataset stress tests.
- Do not claim a completed neuroscience thesis, receptor-level proof, subjective-experience simulation, clinical validation, or biological ground truth.
- Do not copy external code or modify cloned repositories under `prior_art/repositories/`.
- Do not publish, push, deploy, email, create a release, or mint a DOI in this pass.

## User Audiences

- PI/supervisor/committee: needs the project, strongest result, blocker, and ask in under 30 seconds.
- Scientific reviewer: needs a claim ledger, decision gates, figure-to-evidence mapping, and caveats.
- Technical auditor: needs source artifacts, calculations, dashboard payloads, and reproducible build/test gates.
- Project owner: needs the dashboard to remain usable as a technical evidence console.

## Route Map

- `/LSD_Thesis/`: sparse router page, not a dense dashboard cold start. Dominant action: "Start with the PI review summary."
- `/LSD_Thesis/pi-review/`: canonical public summary copied from `OPEN_ME_FIRST.html` to `index.html`.
- `/LSD_Thesis/pi-review/pages/decision-gates.html`: renamed/promoted replacement for problems/next-steps, with motion/confound, DOI/archive, atlas replication, and external validation gate cards.
- `/LSD_Thesis/pi-review/pages/claim-ledger.html`: claim-to-evidence table using the controlled statuses.
- `/LSD_Thesis/pi-review/pages/figure-atlas.html`: curated figure tour with claim, status, role, source data, calculation note, and next check.
- `/LSD_Thesis/pi-review/pages/evidence-and-calculations.html`: evidence ledger first; exact numbers after the ledger.
- `/LSD_Thesis/pi-review/pages/methods.html`: methods argument, not capability inventory.
- `/LSD_Thesis/pi-review/pages/full-package.html`: exhaustive deep audit package, explicitly not first read.
- `/LSD_Thesis/dashboard/` and legacy dashboard pages: technical evidence console, not final thesis chapters.

## Controlled Scientific Vocabulary

Use these statuses exactly where status labels appear:

- implemented
- proxy-supported
- mixed
- unsupported
- blocked
- future

Use "mechanism-proxy ranking" instead of unqualified "mechanism ranking" unless the context is explicitly hypothetical. Use "C is the provisional leading macro-dynamic proxy under the current cached 8-module LSD-placebo analysis, pending motion/confound control and atlas-level replication" for C summary language. Split E into lower transition/control-energy proxy support and receptor-specific placement non-support.

## Claim-Status Taxonomy

- implemented: pipeline or artifact exists and can be inspected.
- proxy-supported: current proxy analysis supports the claim within stated limits.
- mixed: one subclaim has support while another remains unsupported or conflicting.
- unsupported: current evidence does not support the claim.
- blocked: required evidence is absent.
- future: planned but not completed.

## Page-Level Changes

Root:
- Replace the dense dashboard cold start with a sparse router using existing dashboard CSS/templates.
- Make the PI-review route visually dominant.
- Include the status strip fields: project status, strongest implemented proxy, main blocker, archive state, best next action.
- Demote dashboard links as "Technical evidence console" and "Deep audit."

PI-review summary:
- Add visible "not thesis-complete" badge.
- Add compact provenance card: OpenNeuro ds003059, 15 subject/session averages, cached public derived artifacts, subject-level FD/DVARS/censoring absent, GitHub release yes and DOI/archive gate pending.
- Add reviewer ask: "Please evaluate whether the motion-proof-first validation plan is sufficient to convert this research-demo workbench into a defensible thesis analysis."
- Add claim-status legend and primary links to decision gates, claim ledger, figure atlas, evidence/calculations, methods, and full package.

Figure atlas:
- For curated highlights, expose claim supported, claim status, figure role, source data, calculation note, required next check.
- Use controlled link verbs: View figure, Source data, Calculation note, Claim ledger, Reproduce locally.
- Replace generic "Open full artifact" on curated cards.

Evidence/calculations:
- Add a top evidence ledger with columns: Evidence item, Supports, Does not support, Status, Source artifact.
- Tag FC-derived claims as motion-sensitive.

Full package:
- Add top warning: "This page is exhaustive; start with Executive Summary unless auditing artifacts."
- Keep or add "What Not To Say" near the top.

Pitch slides:
- Change "The current A-E ranking is C, E, D, A, B" to "Current proxy ranking, before motion-proof completion: C, E, D, A, B."
- Add "Proxy ranking; not final mechanism proof" badge on ranking slides.
- Split E into lower-energy proxy and receptor-specific non-support.

Methods:
- Rename `methods-and-skills.html` to `methods.html` in the public route, preserving backward compatibility if practical.
- Lead with decisions the methods can support, then separate implemented pipeline, proxy limitations, missing thesis-grade analyses, and future methods.

Scholarly context / prior art:
- Distinguish alignment from reproduction and validation.
- Use a matrix shape where feasible: literature claim, current proxy analogue, direction, method mismatch, allowed conclusion.

Dashboard:
- Rename visible dashboard/root framing to "Technical evidence console."
- Rename dashboard "Mechanism Ranking" headings to "Mechanism-Proxy Ranking."
- Add/ensure C, E, B, robustness, empirical, prior-art, simulator, and thesis caveats.

## Acceptance Criteria

- Cold reader landing on root understands project, current result, blocker, and ask within 30 seconds.
- `/pi-review/` is visibly canonical.
- Every C ranking mention carries proxy and motion-gate caveat.
- Every E mention distinguishes lower-energy support from receptor-specific non-support.
- "completed thesis" does not appear as a positive claim.
- Motion/confound status appears before detailed figures.
- GitHub release and DOI/archive state are visible and not conflated.
- Major figure cards have claim, status, source data, calculation route, and next check where available.
- Prior-art pages distinguish alignment from reproduction or validation.
- Build output and internal links pass or remaining warnings are documented.

## Test Plan

Fast local checks:

```powershell
uv run pytest tests/test_dashboard_redesign_contract.py -q
uv run pytest tests/test_public_site_payload_contract.py tests/test_static_pages_payload_refresh.py -q
node --check src\lsd_thesis\static\dashboard.js
uv run python scripts\build_github_pages.py
```

Claim/wording checks:

```powershell
rg -n "completed thesis|proven mechanism|validated mechanism|LSD mechanism|receptor-informed network control|external validation|robust proof|bootstrap confidence|ready|validated by prior art|explains LSD effects" src docs scripts
rg -n "Mechanism Ranking|mechanism ranking" src docs scripts
```

Rendered checks:
- Serve `_site/` locally.
- Inspect `/`, `/pi-review/`, `/pi-review/pages/decision-gates.html`, `/pi-review/pages/claim-ledger.html`, `/pi-review/pages/figure-atlas.html`, `/dashboard/`, `/ranking.html`, `/robustness.html`, `/empirical.html`, `/prior-art.html`, `/simulator.html`, and `/thesis.html`.
- Use Playwright MCP for page identity, nonblank render, console health, screenshots, responsive checks, and link navigation.

## Risks And Rollback Notes

- The PI package is currently static HTML; route renames can break relative links if aliases are not preserved. Keep compatibility redirects or duplicate thin wrappers for old names where low-risk.
- The Pages builder copies PI-review files and then regenerates the figure atlas; changes to source static files must be reflected by `scripts/build_github_pages.py`.
- Many dashboard labels are generated by `src/lsd_thesis/static/dashboard.js` from payload data; template-only changes will not catch all wording.
- Avoid broad result regeneration. Use current cached artifacts and current local truth.
- Rollback is straightforward: revert changes to PI-review static HTML/CSS, dashboard templates/JS, and `scripts/build_github_pages.py`; `_site/` is generated and should not be committed.
