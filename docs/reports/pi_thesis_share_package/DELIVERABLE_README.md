# PI Thesis Share Deliverable

Hosted URL after GitHub Pages deployment:

https://grimgrimberg.github.io/LSD_Thesis/pi-review/

For local/offline review, open `deliverable_website/OPEN_ME_FIRST.html` in a browser.

Attach or upload `dist/LSD_THESIS_PI_REVIEW_WEBSITE.zip`. The ZIP contains `OPEN_ME_FIRST.html` at its root plus all local pages, screenshots, figures, data tables, source Markdown downloads, manifest, and QA report.

## What Changed

- Created `deliverable_website/` as a self-contained, relative-link-only mini-site that can be copied into the GitHub Pages build.
- Added pitch slides and a generated hosted figure-atlas target.
- Copied existing package screenshots, figures, CSV tables, and Markdown docs into the deliverable website.
- Created `README_FOR_PI.txt`, `EMAIL_BODY.txt`, `manifest.json`, and `qa_report.json` inside the website.
- Added `pages/ae-math-metadata.html` and `MECHANISM_RUBBER_DUCK_GUIDE.md` for plain-English A-E mechanism, math, and metadata explanation.
- Created `SEND_THIS_EMAIL.md` in this package folder.
- Created the final ZIP in `dist/`.

## What Did Not Change

The original package pass did not change source code, tests, scripts outside this package, dashboard templates, dashboard CSS/JS, dashboard routes, schemas, existing result artifacts, raw data, caches, dependencies, `docs/reference`, staging, commits, Pages builds, external data downloads, uploads, email, or scientific workflows. A later hosting pass wires this static package into `scripts/build_github_pages.py` for GitHub Pages publication.

## Caveat

This is a PI-review package, not a completed thesis. FD/DVARS/censoring motion proof remains incomplete, and the archive DOI remains missing.
