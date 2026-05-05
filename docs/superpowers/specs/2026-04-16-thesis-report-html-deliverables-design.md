# Thesis Report And HTML Deliverables Design

## Problem Frame

The repository already contains a working surrogate-model pipeline, empirical `ds003059` ingestion, stage summaries, saved figures, a dashboard, and a first-pass long report. What is missing is a defense-ready publication package that presents the work at an academic level across multiple formats without drifting away from the verified repo evidence.

The user wants a stronger scholarly narrative plus visually rich deliverables:

- a more thesis-chapter style report with formal academic voice
- a defense-oriented outline with slide-by-slide talking points
- plots with clear explanations of what each figure shows
- result discussion for each major figure cluster
- an HTML artifact that is impressive enough to function as a standalone presentation or report

## Goal

Create a single-source publication package that turns the existing repo evidence into coordinated academic deliverables:

1. a revised thesis-style report in Markdown, DOCX, and PDF
2. a thesis microsite in HTML
3. a defense-presentation HTML artifact
4. a defense outline document with slide-by-slide talking points
5. a curated static figure pack with captions and interpretive discussion

The package must stay faithful to the repository's scientific guardrails and must not exaggerate what the model demonstrates.

## Constraints And Guardrails

- Keep all claims at the macro-dynamics level.
- Frame the model as a transparent surrogate or macro-scale analogue, not a receptor model or subjective-experience simulator.
- Treat switching barriers and metastability as model-level proxies.
- Use the saved Stage 2 empirical targets and summaries as the primary empirical anchor.
- Prefer static reproducible figures built from saved results artifacts instead of screenshotting interactive plots.
- Preserve consistency across DOCX, HTML report, and HTML presentation by using the same underlying figure captions and evidence summaries.
- Explicitly surface failures, mismatches, and robustness weaknesses rather than smoothing them over.

## Approaches Considered

### Approach A: Single-source publishing

Build one canonical evidence layer from the saved repo artifacts and generate all output formats from it.

Pros:
- highest consistency across deliverables
- easiest to defend academically
- lowest risk of contradictory captions or claims
- scales cleanly to DOCX, PDF, HTML report, and HTML presentation

Cons:
- requires some up-front restructuring of the current report pipeline
- figure generation and content generation need shared conventions

### Approach B: Document-first adaptation

Rewrite the long report first, then manually adapt it into HTML and presentation formats.

Pros:
- straightforward writing flow
- low conceptual overhead

Cons:
- high drift risk between report and presentation
- duplicated figure explanation work
- harder to keep the HTML artifacts synchronized

### Approach C: Dashboard-first narrative layer

Use the existing dashboard as the main narrative product, then derive the other outputs from it.

Pros:
- highly interactive
- visually interesting

Cons:
- weakest academic format
- too tightly coupled to the app instead of the thesis narrative
- harder to cite or export cleanly

## Recommendation

Use Approach A.

The deliverables should be generated from one evidence-centered content model so that the same plot, interpretation, and caveat appears consistently in the report, microsite, and defense presentation. This is the most defensible path for a thesis-style package.

## Evidence Base

The content should be grounded in verified repo artifacts, not reconstructed from memory. The primary evidence sources are:

- `results/stage_1/stage_1_summary.json`
- `results/stage_2/stage_2_summary.json`
- `results/stage_2/empirical_perturbation_targets.yaml`
- `configs/targets/empirical_lsd_signatures.yaml`
- `results/stage_3/stage_3_summary.json`
- `results/stage_4/stage_4_summary.json`
- `results/training/condition_benchmark/comparison_summary.json`
- `results/training/multitask_benchmark/comparison_summary.json`
- stage figure directories under `results/stage_1/figures/` through `results/stage_4/figures/`
- core implementation files under `src/lsd_thesis/`

The external literature layer should remain lightweight and support framing rather than override the repo's actual findings.

## Deliverable Set

### 1. Revised thesis report

Outputs:
- `output/doc/thesis_report_revised.md`
- `output/doc/thesis_report_revised.docx`
- `output/doc/thesis_report_revised.pdf`

Content shape:
- executive summary
- abstract
- introduction
- research questions and claim boundaries
- repository architecture and methods
- empirical data pathway
- stage-by-stage results
- integrated discussion
- limitations and threats to validity
- defendable claims versus non-defendable claims
- reproducibility and provenance
- references

Tone:
- formal and thesis-like
- explicit about quantitative versus qualitative matching
- explicit about negative results and robustness failures

### 2. Thesis microsite

Output:
- `output/doc/thesis_microsite.html`

Structure:
- long-form academic report layout
- persistent navigation
- embedded static figures
- figure captions plus explanatory text
- section-level discussion blocks
- links to exported DOCX and PDF

Purpose:
- a polished HTML report that can stand alone as a professional presentation of the work

### 3. Defense presentation HTML

Output:
- `output/doc/defense_presentation.html`

Structure:
- slide-style pages or sections
- one primary claim per slide
- large visuals
- compact supporting evidence
- explicit takeaway and caveat per slide

Purpose:
- a presentation-friendly artifact for oral defense preparation

### 4. Defense outline document

Outputs:
- `output/doc/defense_outline.md`
- `output/doc/defense_outline.docx`

Structure:
- slide-by-slide outline
- speaking points
- transition lines
- likely committee challenges
- short recommended responses grounded in repo evidence

### 5. Curated static figure pack

Output directory:
- `output/doc/figures/`

Each figure should have:
- a stable filename
- a formal caption
- a short "what this figure shows" explanation
- a short "why this matters" or "limitation" discussion

## Planned Figure Set

The default figure pack should contain at least the following:

1. `stage1_metric_shift.png`
   - baseline versus perturbed model metrics
   - used to show that the hand-designed altered-state regime is only partially aligned with expectations

2. `stage2_sober_fit.png`
   - placebo target metrics versus best fitted sober metrics
   - used to demonstrate that the fitter can substantially improve the sober score

3. `stage2_fit_robustness.png`
   - best single-seed fit versus multi-seed mean and spread
   - used to show the fit is not robust enough yet

4. `empirical_delta_signs.png`
   - empirical LSD-minus-placebo deltas against literature-style expected signs
   - used to show where the current 8-module extraction supports or reverses expected directions

5. `stage3_mechanism_ranking.png`
   - mechanism scores across tested perturbation families
   - used to show which mechanism is least bad rather than strongly validated

6. `stage3_best_delta_comparison.png`
   - best mechanism deltas versus empirical deltas
   - used to show overshoot, sign errors, and barrier mismatch

7. `stage4_single_vs_pair.png`
   - best single mechanism versus best pairwise mechanism score
   - used to show that pairwise combinations do not improve the current result

8. `training_benchmark.png`
   - classifier and multitask benchmark comparison
   - used to show modest condition signal and uneven predictive performance

9. `thesis_claims_matrix.png`
   - optional summary matrix of what worked, what partially worked, and what failed
   - used for conclusion and defense slides

## Figure Commentary Strategy

Each figure should be accompanied by three short text blocks:

1. Observation
   - what is visibly happening in the figure

2. Interpretation
   - what the figure implies about the model or pipeline

3. Limitation or caution
   - why the result should not be overstated

This structure should be reused across report, microsite, and presentation to maintain consistency.

## HTML Content Model

The HTML report and HTML presentation should share the same underlying content primitives:

- section title
- thesis claim
- supporting figure
- caption
- observation
- interpretation
- limitation
- source provenance

This allows the same evidence unit to be rendered differently in long-form and presentation-style outputs.

## Proposed Chapter Logic For The Revised Report

1. Introduction
   - what problem the repo addresses
   - why a surrogate model is useful
   - what the model does not claim

2. Model And Methods
   - 8-module dynamical system
   - graph structure
   - observable definitions
   - fitting and perturbation workflow

3. Empirical Grounding
   - `ds003059`
   - rest-run selection
   - module extraction logic
   - why the mapping is transparent but coarse

4. Results
   - Stage 1 exploratory surrogate behavior
   - Stage 2 sober calibration and empirical extraction
   - Stage 3 mechanism search
   - Stage 4 ablation and pairwise testing
   - training benchmark outputs

5. Discussion
   - what the repo actually demonstrates
   - which findings are partial successes
   - which findings are negative but informative
   - where the current model class fails

6. Limitations And Future Work
   - coarse network extraction
   - seed sensitivity
   - weak provenance due missing commit history
   - lack of full mechanistic success

7. Conclusion
   - defendable thesis claim stated precisely

## Verification Plan

The publication package should be verified in layers:

1. Data consistency
   - the generated figures must match the saved results artifacts

2. Rendering
   - DOCX rendered and visually checked
   - PDF exported successfully
   - HTML files open locally without broken asset paths

3. Narrative consistency
   - no contradiction between report, microsite, and presentation
   - no unsupported claims beyond macro-dynamics framing

4. Repo quality checks
   - keep the existing report generator or replacement scripts lint-clean
   - run targeted checks on any new generation scripts

## Risks

- Figure generation may drift from the saved numeric summaries if plotting code pulls the wrong fields.
- The current report generator may be too limited for figure-rich DOCX layout and may need targeted extension.
- HTML presentation styling can become flashy and undermine the academic tone if not restrained.
- Existing markdown stage reports may contain stale claims that conflict with the authoritative JSON summaries.

## Non-Goals

- Do not claim mechanistic confirmation of psychedelic brain dynamics.
- Do not present the surrogate as a biologically realistic receptor model.
- Do not replace the dashboard as an exploratory tool; the HTML deliverables are publication layers, not full app rewrites.
- Do not smooth over Stage 3 and Stage 4 failures for presentation polish.

## Implementation Direction

The implementation should proceed by:

1. generating a clean static figure set from saved result artifacts
2. building a canonical structured content layer for figure captions and discussion
3. rewriting the report around that structure
4. generating DOCX and PDF from the revised report
5. generating a microsite HTML report from the same content
6. generating a presentation-style HTML deck from the same content
7. generating a defense outline document from the same evidence base

## Success Criteria

This design is successful if:

- the report reads like a serious academic document rather than a project log
- every major stage has at least one figure with explanation and discussion
- the HTML microsite is polished enough to share directly
- the HTML presentation is usable for defense rehearsal
- the defense outline gives a coherent speaking path through the work
- all outputs remain aligned with the repo's actual evidence and limitations
