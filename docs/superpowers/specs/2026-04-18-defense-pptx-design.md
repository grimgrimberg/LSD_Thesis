# Defense PPTX Design

## Goal

Add a real `.pptx` defense deck to the publication package so the repository produces an editable PowerPoint presentation in addition to the long-form report, microsite, HTML defense deck, and PDF.

## Scope

- Use the long-form thesis report as the canonical source.
- Generate a presentation-oriented deck, not a one-section-per-slide report mirror.
- Reuse the saved Stage 1 and Stage 2 figure PNGs.
- Save both the editable JS source and the generated `.pptx`.
- Expose the `.pptx` in the publication package outputs and dashboard artifact links.

## Approach

Use a small Python slide-spec layer to derive a defense deck outline from the existing long-form report parsing path. Feed that slide spec into a Node/PptxGenJS generator kept in a task-local repo directory with explicit dependencies. Keep the slide count constrained to a presentable defense deck that groups related report sections into a smaller number of speaking slides.

## Deliverables

- A typed Python builder for a defense slide spec derived from the long-form report.
- A PptxGenJS authoring script and local Node package for deck generation.
- A generated PowerPoint deck under `output/doc/`.
- Publication package wiring so the deck is built alongside the existing report artifacts.

## Validation

- Focused pytest coverage for the slide-spec builder and package wiring.
- `mypy` and `ruff` for touched Python files.
- Successful `.pptx` generation with a non-empty output file.
- Structural verification that the deck artifact is present in the package output set.
