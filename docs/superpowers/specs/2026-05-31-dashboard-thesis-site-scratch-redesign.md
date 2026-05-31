# Dashboard + Thesis Site Scratch Redesign Spec

## Decision

Rebuild the public GitHub Pages experience from scratch around a hybrid goal:

- Primary surface: PI pitch homepage.
- Secondary surface: thesis-defense narrative.
- Tertiary surface: data-science evidence dashboard.

The current dashboard is too dense because it tries to be the pitch, thesis, evidence explorer, artifact browser, and appendix at the same time. The redesign must separate those jobs.

## Current-State Backup

Before this redesign starts, the current committed and published state is backed up in remote branches:

- Source backup: `backup/dashboard-before-scratch-rewrite-20260531-104146-source`
- Source SHA: `660b6d36886cd75921f086e10208bbf94b7808ba`
- Pages backup: `backup/dashboard-before-scratch-rewrite-20260531-104146-gh-pages`
- Pages SHA: `4e0fb890111efb0e8ff1e858d5553dafb57bfcd0`

These branches are the rollback point if the scratch redesign goes in the wrong direction.

## Product Goal

Create a public project site that helps a prospective PI understand the project in under two minutes, then lets them drill into thesis-quality evidence and data-science artifacts without being overwhelmed.

The site should communicate:

- The applicant is combining AI, engineering, perception, and psychedelic-state neuroscience.
- The project has a defendable scientific question.
- The project is a data-science project, not only a neuroscience webpage.
- The evidence is real but bounded by conservative claim gates.
- The dashboard exists to prove and inspect claims, not to be the first thing the reader must decode.

## Audience

Primary audience:

- A PI deciding whether this project and applicant are a good fit for a master's research direction.

Secondary audience:

- Thesis committee / academic reviewer.
- Technical collaborator evaluating the analysis and code.
- The user reviewing their own project story.

## Core Positioning

Homepage sentence:

> This project uses explainable AI and control-inspired time-series modeling to test whether psychedelic fMRI changes are better described as altered transition dynamics than as generic noise, motion, or static-connectivity differences.

Shorter public headline:

> AI tools for explaining psychedelic brain dynamics.

Claim boundary:

> This is a macro-dynamics and data-science project. It does not claim to simulate subjective experience, prove receptor-level mechanisms, or provide clinical conclusions.

## Site Architecture

### Route 1: Home / PI Pitch

Purpose:

- Explain the project quickly.
- Make the applicant look focused, rigorous, and technically capable.
- Give the PI obvious next clicks.

Required sections:

1. Hero
   - Headline: `AI tools for explaining psychedelic brain dynamics`
   - Subheadline: one paragraph connecting AI, engineering, perception, and psychedelics.
   - Buttons:
     - `Read the thesis idea`
     - `Open evidence dashboard`
     - `View methods and reproducibility`
     - `Open GitHub repo`

2. Research question
   - One clear falsifiable question.
   - One sentence explaining why LSD/psilocybin fMRI is a useful testbed.

3. Why this fits a PI
   - Computational modeling.
   - Interpretable ML.
   - Dynamical systems / control theory.
   - Perception and altered-state science.

4. What has been built
   - Data ingestion and provenance.
   - Mechanism ranking.
   - Subject-disjoint validation.
   - External psilocybin stress test.
   - Motion/QC sensitivity layer.
   - Conservative claim ladder.

5. What I need from a lab
   - Neuroscience supervision.
   - Better priors / datasets.
   - Stronger validation and interpretation.

6. Claim boundary
   - Supported now.
   - Proxy-supported.
   - Exploratory.
   - Future work.

Design rule:

- This page should have almost no plots.
- Use three to five evidence cards, not a dashboard grid.
- Every paragraph should be understandable to a PI who is not already inside the repo.

### Route 2: Thesis Story

Purpose:

- Explain the thesis idea as a coherent academic narrative.
- Bridge the PI pitch and the evidence dashboard.

Required sections:

1. Problem
   - Psychedelic fMRI effects are often described with broad biological interpretations.
   - This project asks whether simple interpretable dynamic mechanisms can explain empirical macro-patterns.

2. Data
   - ds003059 LSD/placebo as empirical anchor.
   - ds006072 psilocybin as external stress-test layer.
   - Receptor/myelin/gradient and structural layers as priors / controls, not proof.

3. Method
   - Raw fMRI / cached empirical summaries.
   - Parcellation and module summaries.
   - Dynamic features.
   - Mechanism candidates.
   - Subject-disjoint validation.
   - Claim gates.

4. Findings
   - Mechanism ranking result.
   - Validation status.
   - Negative receptor/myelin/gradient result framed as credibility, not failure.
   - Motion/QC caveat.

5. Limitations
   - Not subjective experience.
   - Not receptor mechanism proof.
   - Raw-BOLD image QC is not fMRIPrep FD.
   - Current claims are macro-dynamics and data-science claims.

6. Next work
   - Higher-resolution surfaces.
   - Better external validation.
   - Better motion/confound derivatives.
   - PI/lab-guided neuroscience interpretation.

Design rule:

- This page can include diagrams and a few key tables.
- It must not be an artifact dump.

### Route 3: Evidence Dashboard

Purpose:

- Prove the story with data-science evidence.
- Keep the default view small and explainable.
- Put secondary plots into appendix drawers.

Required top-level dashboard sections:

1. Claim Ladder
   - Six strict gates.
   - Status.
   - Evidence link.
   - What would downgrade the claim.

2. Mechanism Ranking
   - One chart: family score or rank.
   - One table: mechanism family, support, uncertainty, claim tier.
   - One paragraph: how to read this.

3. Validation Gates
   - CV5 subject-disjoint status.
   - ds006072 status.
   - Schaefer/Yeo status.
   - Neuromaps spatial-null status.

4. Confound Controls
   - Motion/QC status.
   - Run/design confounds.
   - Module-DVARS.
   - Raw-BOLD image QC.
   - Explicit caveat: not full fMRIPrep FD proof.

5. Negative Controls
   - Receptor/myelin/gradient status.
   - Structural/receptor prior status.
   - Random/control priors.
   - Negative result explanation.

6. Artifact Browser
   - Search and filter links to JSON, CSV, HTML, XLSX, MD, and figures.

Design rule:

- Default dashboard should fit in four to six major panels.
- Plot count visible on first load should be low.
- All detailed plots go into `Appendix` accordions.
- Every chart must have a one-sentence “what this means” and one-sentence “what this does not mean.”

### Route 4: Methods / Reproducibility

Purpose:

- Make the project credible as a data-science and engineering project.

Required sections:

1. Pipeline diagram
   - Data source.
   - Cache / preprocessing.
   - Features.
   - Models.
   - Validation.
   - Dashboard / artifacts.

2. Commands
   - Build dashboard.
   - Run focused tests.
   - Rebuild Pages.
   - Run thesis evidence loop.

3. Artifacts
   - Where JSON/CSV/XLSX outputs live.
   - Which are source vs derived.
   - Which are excluded from git.

4. Reproducibility boundary
   - Raw OpenNeuro data is not bundled.
   - Derived/static artifacts are published.
   - GitHub Pages is presentation, not full raw-data archive.

### Route 5: Appendix

Purpose:

- Preserve depth without cluttering the pitch or main dashboard.

Contains:

- Existing detailed plots.
- Old dashboard-style panels.
- Full artifact tables.
- Figure gallery.
- Supplemental status JSON links.

Design rule:

- The appendix can be dense.
- The homepage and primary dashboard cannot be dense.

## Information Hierarchy

The new site must answer questions in this order:

1. What is this project?
2. Why should a PI care?
3. What has already been built?
4. What is the strongest claim?
5. What evidence supports it?
6. What weakens or limits it?
7. How can someone inspect/reproduce it?

Any page section that does not answer one of these questions should move to the appendix.

## Visual Direction

Tone:

- Serious, technical, and clear.
- More research-lab portfolio than neuroscience poster.
- No decorative psychedelic visuals.

Style:

- Light background with strong dark editorial blocks.
- One accent color for evidence / signal.
- One warning color for caveats.
- Monospace only for commands/artifact paths.
- Large readable typography.

Avoid:

- Dense nav bars.
- More than one dashboard sidebar.
- Plot grids on first load.
- Purple-on-white default AI aesthetic.
- Generic brain/psychedelic imagery.
- Hover-only explanations.

## Data and Payload Strategy

Keep current Python payload generation, but create a simpler presentation adapter.

Planned source module:

- `src/lsd_thesis/web/site_payload.py`

Responsibilities:

- Build a compact homepage payload from existing dashboard data.
- Build claim ladder rows.
- Build evidence-card summaries.
- Build artifact index.
- Provide stable keys for templates.

Existing source should remain available:

- `src/lsd_thesis/web/app.py`
- `src/lsd_thesis/templates/dashboard.html`
- `scripts/build_github_pages.py`

But new templates should be introduced instead of continuing to expand the old dashboard template.

Planned templates:

- `src/lsd_thesis/templates/public_site.html`
- `src/lsd_thesis/templates/evidence_dashboard.html`
- `src/lsd_thesis/templates/methods_reproducibility.html`
- `src/lsd_thesis/templates/appendix.html`

## Static Pages Contract

GitHub Pages should publish:

- `index.html`: PI pitch homepage.
- `thesis.html`: thesis story.
- `dashboard/index.html`: evidence dashboard.
- `methods.html`: methods / reproducibility.
- `appendix.html`: appendix and artifact browser.
- `dashboard/dashboard-data.json`: compact site/dashboard payload.
- `dashboard/assets/plotly.min.js`: local Plotly asset.
- `artifacts/...`: selected derived artifacts only.

The previous public dashboard state is recoverable through the backup branches, not by keeping the old page as the main UX.

## Testing Requirements

Focused tests should prove:

1. Static Pages root is the PI pitch homepage.
2. Homepage links to thesis, dashboard, methods, appendix, repo, and core artifacts.
3. Evidence dashboard renders claim ladder and four main sections.
4. Methods page contains exact commands and reproducibility boundary.
5. Appendix contains artifact browser / detailed links.
6. Static build copies only selected derived artifacts.
7. Inline JavaScript syntax passes `node --check`.
8. A local rendered page check verifies:
   - title is correct,
   - key sections are visible,
   - claim status loads,
   - artifact search works.

## Implementation Boundaries

Do:

- Start new templates instead of patching the large existing dashboard as the main surface.
- Keep current data-generation code where it works.
- Add a compact adapter layer.
- Keep old detailed content accessible through appendix links.
- Rebuild and publish Pages only after focused tests pass.

Do not:

- Delete raw data.
- Delete existing generated artifacts.
- Rewrite scientific results.
- Make receptor/clinical/subjective claims stronger.
- Hide limitations for pitch polish.
- Build a single-page everything-dashboard again.

## Approval State

The user approved:

- Primary mode: `PI pitch homepage`.
- Required mix: thesis-defense evidence and data-science dashboard.
- Scratch redesign, after backup.

## Self-Review

Placeholder scan:

- No unresolved TBD/TODO placeholders.

Internal consistency:

- The homepage explains, the thesis story narrates, the dashboard proves, the methods page reproduces, and the appendix preserves depth.

Scope check:

- This is one coherent site redesign with clear route boundaries. It is large but suitable for one implementation plan split into route-sized tasks.

Ambiguity check:

- “Dashboard” is defined as the evidence dashboard, not the entire public site.
- “Thesis website” is defined as a multi-route static GitHub Pages site.
- “From scratch” means new public templates and presentation structure while reusing existing validated data artifacts and Python generation code.
