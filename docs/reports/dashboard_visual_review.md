# Dashboard Visual Review

Date: 2026-06-17

Repo: `D:\LSD_Thesis`

Scope: report-only visual/UI review of the screenshots in `docs/reports/project_state_handoff/assets/screenshots/`.

No UI changes were implemented in this pass.

## 1. Executive Summary

Overall quality: the dashboard is already coherent, readable, and unusually strong on scientific guardrails. The visual system has a consistent evidence-console identity: fixed left navigation, restrained dark surfaces, compact cards, clear active navigation state, and repeated status tokens that reinforce the claim-gated framing.

What is already working:

- The sidebar and topbar make the dashboard feel like one product rather than a pile of plots.
- The claim guardrail is visible on every captured page.
- The pages keep a stable information architecture: page title, panel heading, chart or table, then source/explainer detail below the fold.
- The color language is mostly useful: teal for supported/implemented, amber for mixed/proxy/future, rose for blocked/negative.
- The screenshots show no obvious broken asset, missing Plotly render, missing CSS, or blank chart state.
- Current tests protect the critical public contracts: routes, payload keys, artifact href conventions, `public_site.v1`, security headers, and claim-status vocabulary.

Highest-impact polish opportunities:

- Tighten status-token rendering so long machine-style statuses do not truncate or imply success by color alone.
- Improve first-viewport composition on dense pages so the primary chart and its gate/caveat remain visible together.
- Add chart label polish in a future UI pass: reduce overlap, shorten rendered labels, and improve export/screenshot clarity.
- Strengthen table and card affordances for long status strings, especially on Mechanism Ranking and Prior Art.
- Review mobile/responsive behavior with actual screenshots, because the captured desktop layout already shows places where content depends on horizontal room.

What should not change:

- Do not change routes, aliases, public/local route mapping, or `/artifacts/` href conventions.
- Do not change dashboard/public JSON schemas or `public_site.v1`.
- Do not change claim wording, claim labels, gate/status semantics, or status vocabulary.
- Do not promote any scientific claim from visual polish.
- Do not hide blocked, mixed, unsupported, future, or negative-baseline states.
- Do not regenerate figures, results, Pages output, or scientific artifacts for a visual-only improvement.

## 2. Screenshot-By-Screenshot Review

### Overview

Evidence: `docs/reports/project_state_handoff/assets/screenshots/dashboard-overview.png`

Purpose:

- Establish the project posture.
- Show strict gates, best current layer, benchmark match, subject count, and evidence flow.
- Teach the user that the dashboard is claim-gated before they inspect detailed pages.

Visual strengths:

- The hero statement is strong and appropriately conservative.
- The metric strip is readable and visually anchored.
- The evidence-flow cards are a good bridge between narrative and implementation.
- The sidebar claim note reinforces the same guardrail without competing with the hero.

Visual issues:

- The viewport cuts off the bottom of the evidence-flow cards, so the first captured view feels unfinished.
- The `Best layer` card shows `more_cross_talk`, which reads more like an internal metric key than a page-level dashboard answer.
- The hero panel uses a large amount of vertical space before the user sees the strict gate chart on the right.

Information-density issues:

- The overview carries four roles at once: status dashboard, onboarding story, evidence-flow map, and artifact browser. The first viewport handles the status layer well but does not expose enough of the chart/explainer layer.

Claim-safety risks:

- `Best layer` can sound like a resolved scientific answer if the nearby "current proxy ranking" detail is missed.
- The strong hero phrasing is safe because it says "claim gates", but it should continue to be visually paired with blocked gates and caveats.

Low-risk improvement ideas:

- In a future CSS/layout pass, reduce hero vertical padding or tighten metric-card height so the evidence-flow row is fully visible at 1280x720.
- Display a friendlier visible label for metric-key-like values while preserving the underlying payload and schema.
- Keep the strict-gate card visually close to the hero claim in desktop and mobile layouts.

Changes to avoid:

- Do not replace the current claim-gated hero with stronger thesis-completion language.
- Do not convert `Best layer` into an unqualified mechanism claim.
- Do not remove the sidebar guardrail to gain vertical space.

### Mechanism Ranking

Evidence: `docs/reports/project_state_handoff/assets/screenshots/dashboard-ranking.png`

Purpose:

- Show current A-E mechanism proxy ranking.
- Pair the chart with an inference gate and claim-verdict surfaces.
- Keep B visible as the negative/sanity baseline.

Visual strengths:

- The horizontal bar chart is easy to scan.
- Layer colors are distinct enough to separate C, E, D, A, and B.
- The negative B bar is visible and not hidden.
- The right-side Inference Gate table reinforces that ranking is not the same as unrestricted claim promotion.

Visual issues:

- The Plotly modebar overlays the chart area and makes the chart look less polished in screenshots.
- The Inference Gate table truncates long statuses, especially `implemented_proxy_control_...` and `implemented_negative_contr...`.
- The chart labels are lengthy and use title-cased mechanism names that are still technical.

Information-density issues:

- The first viewport has one large chart plus one dense table. It is clear, but status and interpretation text compete for too little horizontal room in the right panel.

Claim-safety risks:

- The status token `IMPLEMENTED_FIRST_PASS` can read as a positive completion badge without enough visible caveat.
- The table status strings are raw enough that a reader may miss the distinction between implemented code path and validated scientific claim.

Low-risk improvement ideas:

- Hide Plotly modebar in screenshot/export contexts or move chart actions to a less intrusive place while preserving export availability.
- Add CSS wrapping rules or a tooltip/title pattern for long table statuses.
- Use display labels for mechanism names in chart axis text, with detailed names retained in hover/explainer fields.

Changes to avoid:

- Do not remove the negative B row.
- Do not recolor mixed/proxy/implemented states into a single success color.
- Do not change ranking order, score semantics, or status values in payloads.

### Robustness

Evidence: `docs/reports/project_state_handoff/assets/screenshots/dashboard-robustness.png`

Purpose:

- Present internal robustness and sensitivity evidence.
- Keep robustness framed as in-sample stress testing, not external validation.
- Surface strict completion requirements and blocked gates below the fold.

Visual strengths:

- The left summary column is useful and makes the chart easier to interpret.
- The chart clearly highlights C as the strongest rank-1 fraction.
- The negative or near-zero B row remains visible.
- The `DESCRIPTIVE` token is a good claim-safety cue.

Visual issues:

- The long status token in the Robustness Summary heading appears truncated.
- The claim guardrail card in the summary column is cut off at the bottom of the screenshot.
- Error bars and labels are readable, but the chart is visually busy at 1280x720 with the modebar present.

Information-density issues:

- The page asks the viewer to parse a summary card, a large chart, error bars, rank labels, and caveat text in one viewport. The structure is good, but the hierarchy could be sharper.

Claim-safety risks:

- `Seed and Fold Stability` plus a strong C bar could be mistaken for external robustness if the in-sample caveat is below the fold.
- The label "implemented_first_pass_..." could over-signal completion if clipped.

Low-risk improvement ideas:

- Make the in-sample caveat visible above the fold, perhaps as a compact persistent microcopy line under the chart title.
- Improve wrapping or max-width behavior for heading tokens.
- Consider muted modebar display for static review screenshots.

Changes to avoid:

- Do not rename in-sample robustness into external validation.
- Do not hide confidence intervals or low/negative baselines.
- Do not change status semantics to make the page appear more complete.

### Prior Art

Evidence: `docs/reports/project_state_handoff/assets/screenshots/dashboard-prior-art.png`

Purpose:

- Show ds003059 prior-art families and their current claim relationship to this repo.
- Separate proxy-supported, mixed, future, and blocked prior-art mappings.
- Keep prior-art work framed as reproducibility landscape and design inspiration unless locally implemented.

Visual strengths:

- The card grid makes status distribution visible quickly.
- Status pills reinforce the claim vocabulary.
- The page makes future and blocked states visible, not hidden.
- The three-column grid works well for quick scanning on desktop.

Visual issues:

- Some family IDs are long and machine-like, causing awkward line breaks.
- Several descriptions are clipped at the bottom of the screenshot because card content extends beyond the first viewport.
- The all-lowercase/underscore family names feel less polished than the rest of the dashboard.

Information-density issues:

- A 13-family card grid is useful, but the first viewport does not show enough sorting/grouping context. Readers may not know whether cards are ordered by status, family name, or importance.

Claim-safety risks:

- The `proxy-supported` pill is safe but prominent; a casual reader could treat prior-art family support as thesis proof unless the limitation text remains visible.
- The `mixed` receptor/control-energy card needs the split-claim boundary to stay explicit.

Low-risk improvement ideas:

- Use display labels for family names while preserving IDs in hover/title or secondary text.
- Add a visual grouping or small count strip by status, without changing payload schema.
- Improve card min-height and text wrapping so the status and limitation are visible together.

Changes to avoid:

- Do not collapse `mixed`, `future`, and `blocked` into a positive prior-art summary.
- Do not present prior-art wrappers as original analysis.
- Do not remove the `lsd_music_brainstates` blocked state.

### Empirical Viewer

Evidence: `docs/reports/project_state_handoff/assets/screenshots/dashboard-empirical.png`

Purpose:

- Let local users inspect cached subject/run/window empirical summaries.
- Show group-level metric deltas.
- Keep run-02/music and subject-level cache caveats visible.

Visual strengths:

- The selector panel clearly separates subject/run controls from group summary.
- The run-02 warning text is visible and claim-safe.
- Positive/negative delta colors make the chart direction easy to parse.
- The disabled/gated source affordance is conceptually aligned with artifact policy.

Visual issues:

- X-axis labels are heavily angled and dense; the last labels push readability.
- The selected run is `run-02`, and the caveat is visible, but the page title and chart title still foreground "Group Metric Deltas" more strongly than "exploratory run-02 caveat".
- The Plotly modebar again distracts in a static screenshot.

Information-density issues:

- The chart is readable at desktop width, but long metric labels are already near the edge. This is a responsive risk.
- The selector panel mixes primary controls and important caveat text. The caveat is safe but visually secondary.

Claim-safety risks:

- Run-02 can be misread as equivalent to primary rest-run evidence if the caveat is not prominent enough.
- Group deltas can look like final empirical truth unless tied to "cached paired summary" and proxy wording.

Low-risk improvement ideas:

- Add a compact, visually prominent caveat band when run-02 is selected, without changing underlying text or status semantics.
- Use shorter display labels for x-axis metrics and keep full names in hover/explainer text.
- Consider a horizontal bar chart for metric deltas on narrow layouts.

Changes to avoid:

- Do not make run-02/music appear primary.
- Do not expose denied subject-level cache artifacts through public links.
- Do not change `/api/empirical-view` or artifact security behavior.

### Figure Deck

Evidence: `docs/reports/project_state_handoff/assets/screenshots/dashboard-figures.png`

Purpose:

- Provide an export-ready registry of figures with source paths, formulas, caveats, and claim gates.
- Surface production gates such as motion proof, archive DOI, and CV5 validation.

Visual strengths:

- The page has the strongest first-viewport claim safety: blocked cards are prominent.
- The three status cards are easy to understand.
- The `Main Figure Registry` section begins within the first viewport, which helps reveal next content.
- The copy states that caveats and claim gates stay attached to every figure.

Visual issues:

- The large hero takes substantial vertical space, though less harmfully than Overview because the gate cards remain visible.
- The blocked cards are strong, but there is a chance the `IMPLEMENTED` CV5 card reads as equal in strength to the blocked motion/archive cards unless its internal-only limitation stays visible below the fold.
- The figure registry itself is mostly below the fold in the screenshot.

Information-density issues:

- This page is well-structured for review, but it may need a print/export-specific check because it is explicitly "export-ready".

Claim-safety risks:

- `Publication-grade` and `Export-ready` are acceptable as figure-readiness wording, but they should not imply thesis completion or archive DOI readiness.
- The CV5 card should continue to say internal subject-disjoint CV5 rather than external validation.

Low-risk improvement ideas:

- Keep blocked cards prominent and add consistent microcopy on all status cards if future UI work touches this page.
- Review print styles and screenshot export settings for figure-card readability.
- Consider a compact top summary for "blocked vs implemented" counts if it can be done without schema changes.

Changes to avoid:

- Do not present the archive as publication complete until DOI verification exists.
- Do not downgrade the visible motion-proof blocker.
- Do not change figure payload schema or source artifact links.

## 3. Cross-Page Visual Patterns

Navigation/sidebar:

- Strengths: stable placement, clear active state, consistent icon/text pairing, visible claim guardrail.
- Issues: the sidebar consumes 264px on desktop and leaves dense content constrained; on mobile, horizontal nav already has a defined overflow strategy but needs screenshot verification.
- Safe future treatment: preserve nav IDs and routes, but review label wrapping and horizontal scroll affordance on mobile.

Typography:

- Strengths: strong hierarchy, zero letter-spacing, readable system font, good large headings.
- Issues: raw status IDs and underscored family names look less polished than headings and card labels.
- Safe future treatment: introduce display-only label formatting in templates/JS while preserving raw schema values and status vocabulary.

Spacing:

- Strengths: panels, cards, and charts use consistent 8px radius and 20px rhythm.
- Issues: first viewport often cuts off the next evidence section, especially Overview and Robustness.
- Safe future treatment: reduce top/bottom padding in hero panels or adjust first-row grid ratios; avoid content removal.

Cards:

- Strengths: cards are compact and scannable.
- Issues: long statuses and long IDs can clip or wrap awkwardly.
- Safe future treatment: add status-token wrapping rules, `max-width`, or title attributes; keep every status visible.

Badges/status pills:

- Strengths: recurring pill vocabulary helps claim safety.
- Issues: color mapping in `statusClass()` can classify values containing "complete" or "implemented" as teal even when the wider sentence includes caveats; long strings truncate in headings.
- Safe future treatment: improve visual wrapping and consider display grouping without changing underlying status labels.

Plots:

- Strengths: charts render reliably in screenshots; color language is consistent.
- Issues: Plotly modebar overlays charts; long axis labels are dense; export screenshots include UI chrome that weakens polish.
- Safe future treatment: make modebar less intrusive in static/screenshot contexts and shorten display labels.

Forms/controls:

- Strengths: empirical selector and simulator controls are clear, with good control grouping.
- Issues: caveat text in selector panels can become visually secondary even when scientifically important.
- Safe future treatment: use stronger caveat layout, not stronger claim wording.

Chart labels:

- Strengths: numeric annotations help interpretation.
- Issues: small labels on chart bars compete with grid lines and modebar.
- Safe future treatment: tune label placement, font size, and margins per chart type.

Mobile/responsive risk:

- Existing CSS has breakpoints at 1120px, 680px, and 420px, plus mobile modebar hiding.
- The desktop screenshots already show tight labels, so mobile should be manually checked before any visual claim.
- Highest-risk mobile pages: Mechanism Ranking, Empirical Viewer, Prior Art, and Figure Deck registry.

Accessibility/contrast risk:

- Text contrast appears generally strong on dark surfaces.
- Amber and rose outlines on dark backgrounds are readable in screenshots, but status pills should not rely on color alone.
- Existing `aria-label`, `role="img"`, focus styles, skip link, and reduced-motion support are good.
- Future audit should check keyboard focus on sidebar, filter inputs, empirical controls, and Plotly modebar.

Export/screenshot polish:

- Current screenshots are usable but not presentation-grade because Plotly modebars overlay charts and lower content is clipped.
- Figure Deck is closest to export-ready visually.
- A future screenshot pass should capture both desktop and mobile after any CSS-only changes.

## 4. Claim-Safety Review

Patterns that currently help:

- Every page carries the sidebar claim guardrail.
- Status labels such as blocked, future, mixed, proxy-supported, and implemented appear visibly.
- Figure Deck foregrounds blocked motion and archive DOI states.
- Prior Art keeps future and blocked families visible.
- Empirical Viewer shows a run-02 caveat in the selector panel.
- Mechanism Ranking retains the negative B baseline.

Patterns that could overclaim visually:

- Teal status tokens for raw `implemented_first_pass` strings can read like success badges.
- `Best layer` on Overview can sound like a final scientific winner if "current proxy ranking" is missed.
- The strong C bar in Robustness can look decisive if the in-sample caveat is below the fold.
- `Publication-grade` and `Export-ready` on Figure Deck can be mistaken for archive/thesis readiness unless blocked cards remain visible.
- Prior-art `proxy-supported` cards may look like external validation if limitation text is clipped.

Safer presentation patterns for future work:

- Keep blocked and caveat text above the fold on pages with strong positive charts.
- Pair any top-ranked layer display with the word "proxy" in nearby visible microcopy.
- Keep raw status values visible where needed, but add human display labels only as presentation aids.
- Do not hide negative, blocked, or unsupported states to reduce visual clutter.
- Keep run-02/music, receptor placement, external validation, motion proof, and archive DOI blockers visually explicit.

## 5. Prioritized Improvement Backlog

### Safe CSS/Layout Polish

| Priority | Title | Page(s) | Problem | Proposed treatment | Risk | Likely future files touched | Validation commands | Manual review |
|---:|---|---|---|---|---|---|---|---|
| 1 | Wrap long status tokens | Ranking, Robustness, Prior Art, Figure Deck | Long raw statuses truncate in panel headings and tables | CSS-only: allow status tokens to wrap or cap width with readable title/secondary line | Low | `src/lsd_thesis/static/dashboard.css` | dashboard contract tests, preview strict, `node --check`, ruff, mypy, collect-only | Check that raw status is still visible and not relabeled |
| 2 | First-viewport tightening | Overview, Robustness, Figure Deck | Important lower content is cut off in 1280x720 screenshots | CSS-only spacing and grid ratio adjustment for hero/summary panels | Low | `src/lsd_thesis/static/dashboard.css` | same UI validation set plus screenshot comparison | Confirm no content is removed |
| 3 | Modebar screenshot polish | Ranking, Robustness, Empirical | Plotly modebar overlays chart area | CSS/JS display treatment for modebar only in narrow/static/screenshot contexts | Medium | `src/lsd_thesis/static/dashboard.css`, maybe `dashboard.js` | `node --check`, dashboard tests, manual export check | Ensure export remains available |
| 4 | Card ID readability | Prior Art | Underscored family IDs reduce polish | Display-only typography treatment for family IDs, no schema change | Medium | `dashboard.js`, maybe CSS | public/dashboard payload tests, `node --check` | Confirm exact status labels unchanged |

### Safe Label/Display Polish

| Priority | Title | Page(s) | Problem | Proposed treatment | Risk | Likely future files touched | Validation commands | Manual review |
|---:|---|---|---|---|---|---|---|---|
| 1 | Display labels for metric keys | Overview | `more_cross_talk` looks internal | Add display-only label mapping while preserving payload value/source | Medium | `dashboard.js` | dashboard payload contract tests, `node --check` | Confirm no claim promotion |
| 2 | Short chart axis labels | Ranking, Empirical, Thesis | Long labels crowd chart axes | Use shorter display labels with full text in hover/explainer | Medium | `dashboard.js` | `node --check`, manual chart review | Confirm full metric definitions remain available |
| 3 | Prior-art family display names | Prior Art | Family IDs are machine-readable rather than reader-friendly | Format underscores to title labels, keep raw ID in secondary text/title | Medium | `dashboard.js` | prior-art tests if added, existing dashboard tests | Confirm family identity remains traceable |

### Plot/Export Polish

| Priority | Title | Page(s) | Problem | Proposed treatment | Risk | Likely future files touched | Validation commands | Manual review |
|---:|---|---|---|---|---|---|---|---|
| 1 | Chart margin tuning | Ranking, Empirical, Robustness | Labels and annotations are tight | Adjust chart margins and text positions per chart type | Medium | `dashboard.js` | `node --check`, screenshot review | Compare desktop and mobile screenshots |
| 2 | Export-friendly plot chrome | Figure Deck, all chart pages | Exports may include distracting UI chrome | Keep exports available but reduce overlay in presentation captures | Medium | `dashboard.js`, CSS | `node --check`, manual export | Verify no feature regression |
| 3 | Figure registry print check | Figure Deck | Figure Deck claims export-readiness | Review print CSS/card breaks | Low | CSS only | browser print preview, dashboard tests | Confirm blocked cards remain visible |

### Accessibility/Mobile Polish

| Priority | Title | Page(s) | Problem | Proposed treatment | Risk | Likely future files touched | Validation commands | Manual review |
|---:|---|---|---|---|---|---|---|---|
| 1 | Mobile screenshot pass | All pages | Current evidence is desktop-only | Capture mobile screenshots before changing mobile CSS | Low | report or screenshots only | no code validation unless changed | Manual visual review |
| 2 | Focus-state review | All pages | Sidebar, filters, and Plotly controls need keyboard review | Verify existing focus outline and tab order | Low | report-only first | none unless changes follow | Keyboard walkthrough |
| 3 | Status contrast check | All pages | Pills rely on color plus text, but contrast should be measured | Check teal/amber/rose contrast in dark theme | Low | CSS only if needed | screenshot/manual accessibility check | Preserve color/status mapping semantics |

### Requires Schema/Route Caution

| Priority | Title | Page(s) | Problem | Proposed treatment | Risk | Likely future files touched | Validation commands | Manual review |
|---:|---|---|---|---|---|---|---|---|
| 1 | Public/static display parity | All public pages | Local/static behavior can diverge | Audit display-only changes against static route mapping | Medium | templates, `dashboard.js`, maybe Pages builder later | public-site payload tests, route contract tests | Do not run Pages build unless approved |
| 2 | New card metadata | Any page | Some UI polish would be easier with extra display labels | Avoid schema changes unless explicitly approved | High | payload builders and tests | full dashboard/public contract suite | Human approval required |

### Do Not Touch Without Scientific Approval

| Title | Page(s) | Problem | Proposed treatment | Risk | Likely future files touched | Validation commands | Manual review |
|---|---|---|---|---|---|---|
| Claim label/status vocabulary | All pages | Visual simplification might tempt label changes | Do not change labels or status semantics | High | payload/status modules | full status and payload tests | Scientific approval required |
| Motion/confound gate wording | Robustness, Figure Deck, Thesis | Blocked gate is central scientific boundary | Do not soften or promote | High | status artifacts/docs/templates | thesis status tests | Scientific approval required |
| Run-02/music framing | Empirical, Prior Art | Run-02 is exploratory/gated | Do not make primary | High | data/status/dashboard modules | empirical and next-action tests | Scientific approval required |
| Receptor/control-energy split | Ranking, Prior Art | E is split between lower-energy proxy and unsupported receptor placement | Do not collapse into receptor proof | High | dynamic/status payloads | next-action tests | Scientific approval required |
| Artifact/public schema changes | All pages | Public contracts are test-protected | Do not change without migration | High | web payloads/tests/Pages builder | full contract suite | Human approval required |

## 6. Recommended First Implementation Pass

Recommended future pass: CSS-only status-token and first-viewport polish.

Goal:

- Make existing statuses more readable and reduce first-viewport clipping without changing payloads, templates, routes, schemas, claim wording, or JavaScript behavior.

Scope:

- `src/lsd_thesis/static/dashboard.css` only.
- Improve status-token wrapping/max-width behavior.
- Tune panel/hero/card spacing only where screenshots show clipping.
- Optionally add screenshot-only notes to a report, but no code outside CSS.

Why this is the safest first pass:

- It addresses the most visible issues: clipped statuses and cut-off first-viewport content.
- It does not require data, schemas, routes, artifacts, or scientific wording changes.
- It is easy to validate with the existing dashboard contract tests and screenshots.

Do not implement in that pass:

- No display-label mapping.
- No chart data or ranking changes.
- No payload builder changes.
- No status vocabulary changes.
- No Pages build.

## 7. Validation Plan For Any Future Dashboard UI Change

Run before editing:

```powershell
git status --short --untracked-files=all
```

Run after any future dashboard UI change:

```powershell
uv run --frozen pytest tests/test_dashboard_route_contract.py tests/test_dashboard_payload_contract.py tests/test_public_site_payload_contract.py tests/test_web_security.py -q -o addopts=
uv run --frozen python scripts\preview_dashboard.py --check-only --strict
node --check src\lsd_thesis\static\dashboard.js
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen pytest --collect-only -q -o addopts=
```

Manual review if UI files change:

- Reopen Overview, Ranking, Robustness, Prior Art, Empirical Viewer, and Figure Deck.
- Capture desktop screenshots at the same 1280x720 viewport if possible.
- Capture at least one mobile/narrow viewport screenshot.
- Confirm blocked/future/mixed/proxy statuses are still visible.
- Confirm Plotly charts render and exports still work.
- Confirm local/static route expectations still match tests.

## 8. No-Touch Confirmation

This report-only pass intentionally made no changes to:

- Routes or route aliases.
- Dashboard/public JSON schemas.
- `public_site.v1`.
- Claim wording.
- Claim labels.
- Gate/status semantics.
- Generated artifacts.
- Tracked result artifacts.
- Ignored generated outputs.
- Source code.
- Tests.
- Scripts.
- Templates.
- CSS.
- JavaScript.
- `docs/reference`.
- Dependencies, `pyproject.toml`, or `uv.lock`.

No scientific workflows, artifact generation, external downloads, or Pages/publication builds were run.
