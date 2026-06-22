# PI-Review Public Website Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/pi-review/` the canonical public entry and convert the public site into a PI-review-first, claim-gated research-demo website.

**Architecture:** Keep the existing Python/Jinja/static GitHub Pages architecture. Edit source templates, static PI-review package files, dashboard JavaScript labels, and `scripts/build_github_pages.py`; never hand-edit `_site/`.

**Tech Stack:** Python 3.13, uv, Jinja2, FastAPI dashboard templates, static HTML/CSS PI package, Plotly JavaScript renderer, pytest contract tests.

---

## File Structure

- Modify `tests/test_dashboard_redesign_contract.py`: add contract coverage for the new root router, PI summary status strip, claim ledger, decision gates, figure atlas semantics, and dashboard wording.
- Modify `scripts/build_github_pages.py`: generate a sparse public root router, keep `/dashboard/` as the technical console, improve generated figure atlas semantics, and publish manifest entries for decision gates and claim ledger.
- Modify `docs/reports/pi_thesis_share_package/deliverable_website/OPEN_ME_FIRST.html`: add top status strip, not-thesis-complete badge, provenance card, reviewer ask, claim-status legend, and primary route links.
- Modify `docs/reports/pi_thesis_share_package/deliverable_website/assets/css/site.css`: add styles for status strip, provenance, legends, warning cards, and root router.
- Add `docs/reports/pi_thesis_share_package/deliverable_website/pages/decision-gates.html`: public blocker/status route.
- Add `docs/reports/pi_thesis_share_package/deliverable_website/pages/claim-ledger.html`: claim-to-evidence route.
- Modify `docs/reports/pi_thesis_share_package/deliverable_website/pages/evidence-and-calculations.html`: add evidence ledger and motion-sensitive wording.
- Modify `docs/reports/pi_thesis_share_package/deliverable_website/pages/full-package.html`: add deep-audit warning and what-not-to-say guardrail near the top.
- Modify `docs/reports/pi_thesis_share_package/deliverable_website/pages/pitch-slides.html`: qualify ranking language and E split.
- Add or copy `docs/reports/pi_thesis_share_package/deliverable_website/pages/methods.html`: methods route replacing methods-and-skills for public nav.
- Modify `src/lsd_thesis/templates/pages/mechanism_ranking.html`, `thesis.html`, `empirical.html`, `prior_art.html`, `robustness.html`, `simulator.html`: public heading caveats.
- Modify `src/lsd_thesis/templates/components/sidebar.html` and/or dashboard nav source if necessary: visible nav labels become technical-console/proxy labels.
- Modify `src/lsd_thesis/static/dashboard.js`: user-visible wording changes for C/E/B, robustness, prior-art, simulator, and link labels.
- Modify `src/lsd_thesis/dynamic_robustness.py`: replace the high-risk generated C sentence.

## Task 1: Contract Tests First

- [ ] Add assertions to `tests/test_dashboard_redesign_contract.py` for root router markers in `scripts/build_github_pages.py`.
- [ ] Add assertions for `OPEN_ME_FIRST.html`: `not thesis-complete`, `Research-demo evidence package`, `Subject-level FD/DVARS/censoring motion-confound proof absent`, `GitHub release exists`, `Zenodo DOI`, reviewer ask, provenance fields, and status vocabulary.
- [ ] Add assertions for `decision-gates.html`, `claim-ledger.html`, and `methods.html` existence/content.
- [ ] Add assertions for figure atlas builder strings: `Claim supported`, `Figure role`, `Source data`, `Calculation note`, `Required next check`, and controlled link verbs.
- [ ] Add wording assertions that public labels use `Mechanism-Proxy Ranking` and C/E/B caveats.
- [ ] Run:

```powershell
uv run pytest tests/test_dashboard_redesign_contract.py -q -o addopts=
```

Expected before implementation: failure for missing markers.

## Task 2: Public Root Router

- [ ] Add a helper in `scripts/build_github_pages.py` to render a sparse static root page.
- [ ] Make `_write_static_public_site()` write the root router to `_site/index.html` while preserving `_site/dashboard/index.html` as the technical evidence console.
- [ ] Change static dashboard nav href for overview to `dashboard/index.html` when depth is 0, and `index.html` when already inside `/dashboard/`.
- [ ] Keep legacy static routes (`ranking.html`, `robustness.html`, etc.) working.

## Task 3: PI-Review First Viewport

- [ ] Update `OPEN_ME_FIRST.html` with status strip, badge, provenance card, reviewer ask, status legend, and primary links to `decision-gates.html`, `claim-ledger.html`, `figure-atlas.html`, `evidence-and-calculations.html`, `methods.html`, and `full-package.html`.
- [ ] Update `site.css` for the new layout without introducing gradients, remote assets, or text overflow.
- [ ] Keep the page concise enough that the first screen answers project/result/blocker/ask.

## Task 4: Public PI Subpages

- [ ] Add `decision-gates.html` from the current problems/next-steps content, with four gate cards: motion/confound, DOI/archive, atlas replication, and external validation/cross-dataset stress test.
- [ ] Add `claim-ledger.html` with claim, status, evidence, caveat, and next check rows for static workbench, dataset provenance, A-E ranking, C, E1, E2, B, literature alignment, motion/confound, and archive.
- [ ] Add `methods.html` as the public methods route, based on methods-and-skills but framed around what decisions the methods can support.
- [ ] Preserve old deep pages as secondary links or compatibility pages.

## Task 5: Figure Atlas Semantics

- [ ] Expand `VISUAL_ATLAS_HIGHLIGHTS` with claim, role, source data, calculation note, and required next check.
- [ ] Update `_visual_atlas_highlight_cards()` so curated cards render those fields.
- [ ] Replace generic curated-card `Open full artifact` text with controlled verbs.
- [ ] Keep the generated full inventory as a deep visual inventory.

## Task 6: Evidence, Full Package, Slides, And Dashboard Wording

- [ ] Add an evidence ledger at the top of `evidence-and-calculations.html`.
- [ ] Add motion-sensitive tags to FC-derived sections where present.
- [ ] Add deep-audit warning and a concise what-not-to-say block near the top of `full-package.html`.
- [ ] Update `pitch-slides.html`: proxy ranking before motion-proof completion, badge on ranking slide, E lower-energy vs receptor-specific split.
- [ ] Update dashboard template headings and `dashboard.js` user-facing text to use mechanism-proxy ranking and technical evidence console wording.
- [ ] Replace the high-risk generated C sentence in `src/lsd_thesis/dynamic_robustness.py`.

## Task 7: Build And Verification

- [ ] Run focused tests:

```powershell
uv run pytest tests/test_dashboard_redesign_contract.py tests/test_public_site_payload_contract.py tests/test_dashboard_route_contract.py tests/test_dashboard_payload_contract.py tests/test_figure_payload.py tests/test_static_pages_payload_refresh.py tests/test_web_security.py -q -o addopts=
```

- [ ] Run syntax/lint checks:

```powershell
node --check src\lsd_thesis\static\dashboard.js
uv run ruff check scripts\build_github_pages.py src\lsd_thesis\web tests
```

- [ ] Build static site:

```powershell
uv run python scripts\build_github_pages.py --repo-root D:\LSD_Thesis --site-dir D:\LSD_Thesis\_site
```

- [ ] Search for suspicious overclaims and review remaining hits:

```powershell
rg -n -i "strongest implemented LSD mechanism layer|proven mechanism|validated by prior art|robust proof|bootstrap confidence|completed thesis|receptor-specific proof|Zenodo DOI/archive publication is complete" src docs scripts _site --glob "!_site/static/**"
rg -n -i "mechanism ranking" _site src\lsd_thesis\templates src\lsd_thesis\static scripts docs\reports\pi_thesis_share_package
```

- [ ] Serve `_site` locally and inspect root plus key routes with Playwright MCP.

## Self-Review

- Spec coverage: P0/P1 items map to Tasks 1-7. P2 route cleanup is covered where low-risk; P3 science is explicitly future.
- Placeholder scan: no `TBD`/`TODO` implementation placeholders.
- Type consistency: no new public Python API is planned; changes are source HTML/CSS/JS/build-script content and contract tests.
