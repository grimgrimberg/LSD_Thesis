# Pipeline Scripts

This directory contains the entry points for the LSD_Thesis analysis pipeline.
The core scripts have been refactored for clarity and scalability.

## Core Pipelines

* **`run_pipeline.py`** — The primary surrogate-model pipeline. Runs stages 1-4 (simulation, empirical extraction, perturbation fitting, ablation). 
  * Usage: `uv run python scripts/run_pipeline.py run-all`
* **`run_dynamic_mechanism_ranking.py`** — Runs the final A+B+C+D+E mechanism ranking evaluation.
* **`run_dashboard.py`** — Serves the interactive evidence dashboard locally via FastAPI.
  * Usage: `uv run python scripts/run_dashboard.py`
* **`run_cv5_validation.py`** — Runs cross-validation for the models.

## Publishing and Exports

* **`build_github_pages.py`** — Builds the static HTML site for GitHub Pages deployment.
* **`build_publication_package.py`** — Packages final figures and data for publication.
* **`export_dynamic_mechanism_tables.py`** / **`export_thesis_loop_tables.py`** — Generates Excel/CSV exports of the main findings.

## Data Utilities

* **`download_ds006072_metadata.py`**
* **`ingest_external_priors.py`**
* **`prepare_external_data.py`**
