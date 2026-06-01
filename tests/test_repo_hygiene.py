from __future__ import annotations

import ast
from pathlib import Path

from lsd_thesis.repo_hygiene import find_ignored_source_paths


def test_gitignore_does_not_ignore_source_data_package() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    watched_paths = (
        repo_root / "src" / "lsd_thesis" / "data" / "ds003059.py",
        repo_root / "src" / "lsd_thesis" / "data" / "targets.py",
    )

    assert find_ignored_source_paths(repo_root, watched_paths) == []


def test_gitignore_blocks_local_secret_files() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    watched_paths = (
        repo_root / ".env",
        repo_root / ".env.local",
        repo_root / "private.key",
        repo_root / "deploy.pem",
    )

    assert find_ignored_source_paths(repo_root, watched_paths) == [
        ".env",
        ".env.local",
        "private.key",
        "deploy.pem",
    ]


def test_artifact_policy_documents_and_ignores_generated_tiers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
    archive_policy = (repo_root / "docs" / "ARCHIVE_POLICY.md").read_text(encoding="utf-8")

    assert "Tier A tracked evidence" in gitignore
    assert "Tier B: generated artifacts" in gitignore
    assert "Tier C: raw data downloads" in gitignore
    assert "| A | Tracked evidence" in archive_policy
    assert "| B | Generated local outputs" in archive_policy
    assert "| C | Forbidden or private artifacts" in archive_policy
    assert "Serving a file locally does not make it safe to commit" in archive_policy

    watched_paths = (
        repo_root / ".playwright-mcp" / "page-2026-06-01T11-32-22-083Z.yml",
        repo_root / "output" / "doc" / "thesis_microsite.html",
        repo_root / "tmp" / "local_debug.json",
        repo_root / "codex_prompt_pack" / "manifest.json",
        repo_root / "RUN_NEXT_FULL_VALIDATION_PROMPT.md",
        repo_root / "dashboard-before-plot-cleanup.md",
        repo_root / "docs" / "codex_runs" / "2026-05-31-repo-audit-roast.md",
        repo_root / "mypy_cache_dynamic_20260519" / "cache.db",
        repo_root / "dashboard-smoke.png",
        repo_root / "docs" / "codex_runs" / "2026-05-17-frontend-verification" / "dashboard-desktop.png",
        repo_root / "results" / "external_data" / "external_data_manifest.json",
        repo_root / "results" / "nilearn_data" / "schaefer_2018" / "atlas.nii.gz",
        repo_root / "results" / "pytest_tmp_full_20260514" / "scratch.json",
        repo_root / "results" / "setting_seed" / "test_fixtures" / "motion.json",
        repo_root / "results" / "test_runs" / "pytest_full" / "junit.xml",
        repo_root / "results" / "stage_2" / "figures" / "group_metrics.html",
        repo_root / "results" / "stage_2" / "figures" / "group_metrics.png",
        repo_root / "results" / "stage_2" / "empirical_viewer" / "group_overview.json",
        repo_root / "data" / "ds003059" / "dataset_description.json",
    )

    assert find_ignored_source_paths(repo_root, watched_paths) == [
        ".playwright-mcp/page-2026-06-01T11-32-22-083Z.yml",
        "output/doc/thesis_microsite.html",
        "tmp/local_debug.json",
        "codex_prompt_pack/manifest.json",
        "RUN_NEXT_FULL_VALIDATION_PROMPT.md",
        "dashboard-before-plot-cleanup.md",
        "docs/codex_runs/2026-05-31-repo-audit-roast.md",
        "mypy_cache_dynamic_20260519/cache.db",
        "dashboard-smoke.png",
        "docs/codex_runs/2026-05-17-frontend-verification/dashboard-desktop.png",
        "results/external_data/external_data_manifest.json",
        "results/nilearn_data/schaefer_2018/atlas.nii.gz",
        "results/pytest_tmp_full_20260514/scratch.json",
        "results/setting_seed/test_fixtures/motion.json",
        "results/test_runs/pytest_full/junit.xml",
        "results/stage_2/figures/group_metrics.html",
        "results/stage_2/figures/group_metrics.png",
        "results/stage_2/empirical_viewer/group_overview.json",
        "data/ds003059/dataset_description.json",
    ]


def test_dashboard_template_avoids_html_string_injection_sinks() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    dashboard_template = (repo_root / "src" / "lsd_thesis" / "templates" / "dashboard.html").read_text(
        encoding="utf-8"
    )

    forbidden_patterns = (
        ".innerHTML",
        ".outerHTML",
        "insertAdjacentHTML",
        "dangerouslySetInnerHTML",
    )

    for pattern in forbidden_patterns:
        assert pattern not in dashboard_template


def test_dynamic_robustness_uses_public_dynamic_stat_helpers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source_path = repo_root / "src" / "lsd_thesis" / "dynamic_robustness.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    private_stat_imports: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module not in {"lsd_thesis.dynamic_mechanism", "lsd_thesis.dynamic_mechanism_stats"}:
            continue
        private_stat_imports.extend(alias.name for alias in node.names if alias.name.startswith("_"))

    assert private_stat_imports == []


def test_dynamic_mechanism_uses_public_paired_metric_collector() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source = (repo_root / "src" / "lsd_thesis" / "dynamic_mechanism.py").read_text(encoding="utf-8")

    assert "collect_paired_metric_rows as _collect_paired_metric_rows" in source
    assert "rows: list[dict[str, Any]] = []" not in source[source.index("def summarize_transition_proxy") : source.index("def _dynamic_samples")]
    assert "metric_deltas: dict[str, list[float]] = {metric: [] for metric in metric_names}" not in source


def test_dashboard_reporting_architecture_map_mentions_current_web_modules() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    architecture = (repo_root / "docs" / "architecture.md").read_text(encoding="utf-8")

    for expected in (
        "web/app.py",
        "web/artifacts.py",
        "web/empirical_viewer.py",
        "web/status_payload.py",
        "web/simulation_payload.py",
        "web/structural_dti.py",
        "web/thesis_payload.py",
    ):
        assert expected in architecture


def test_parcellation_doc_matches_current_schaefer_gate_status() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    parcellations_doc = (repo_root / "docs" / "parcellations.md").read_text(encoding="utf-8")

    stale_phrases = (
        "currently provides tested metadata and a dry-run plan",
        "Full fMRI extraction is not run automatically",
        "Full Extraction TODO",
        "Do not claim Schaefer/Yeo results exist until extraction",
    )
    for phrase in stale_phrases:
        assert phrase not in parcellations_doc

    for expected in (
        "results/stage_2/parcellations/schaefer_100_yeo_7/parcellation_extraction_summary.json",
        "results/stage_2/parcellations/schaefer_100_yeo_7/empirical_viewer/group_overview.json",
        "results/parcellation_sensitivity/schaefer_100_yeo_7/summary.json",
        "schaefer_200_yeo_7",
        "schaefer_100_yeo_17",
        "schaefer_200_yeo_17",
    ):
        assert expected in parcellations_doc


def test_validation_doc_declares_current_quality_baseline_before_historical_notes() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    validation_doc = (repo_root / "docs" / "VALIDATION.md").read_text(encoding="utf-8")

    current_index = validation_doc.index("## Current Quality Baseline")
    historical_index = validation_doc.index("## Historical Validation Log")
    pass_2a_index = validation_doc.index("## PASS 2A Validation Commands")

    assert current_index < historical_index < pass_2a_index
    assert "Older pass notes below are retained as historical implementation evidence" in validation_doc

    for expected in (
        "383 passed",
        "80.79%",
        "77 source files",
        "26780820028",
        "motion_confound_control_result",
        "project_phase",
        "fMRIPrep FD/DVARS/censoring motion proof",
        "research_demo_ready_not_completed_thesis",
    ):
        assert expected in validation_doc


def test_ci_quality_workflow_runs_documented_local_gates() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ci_workflow = (repo_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    for expected in (
        "uv run ruff check .",
        "uv run mypy src",
        "uv run pytest",
        "uv run python scripts/preview_dashboard.py --check-only --strict",
        "npm test --prefix tools/pptx",
    ):
        assert expected in ci_workflow


def test_thesis_readiness_gates_doc_matches_current_gate_status() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    gates_doc = (repo_root / "docs" / "THESIS_READINESS_GATES.md").read_text(encoding="utf-8")
    cross_dataset_doc = (repo_root / "docs" / "research" / "cross_dataset_thesis_loop.md").read_text(
        encoding="utf-8"
    )

    stale_phrases = (
        "`ds006072` is the target; metadata/manifest alone is not validation.",
        "E remains proxy-only until both layers exist.",
        "Metadata plus functional/CIFTI manifest implemented; empirical viewer still blocked",
        "HCP gate blocked; macro proxy graph controls and rewire nulls implemented",
        "PET gate blocked; coarse receptor-prior null board implemented",
        "ds006072 is ready for full ingestion. | Not yet.",
    )
    for phrase in stale_phrases:
        assert phrase not in gates_doc
        assert phrase not in cross_dataset_doc

    for expected in (
        "Thesis readiness gates: `6/9`",
        "Strict completion gates: `4/6`",
        "Package readiness gates: `1/2`",
        "Missing strict requirements: `motion_confound_control_result`, `project_phase`",
        "Missing package requirements: `reproducible_archive_publication`",
        "fMRIPrep FD/DVARS/censoring motion proof",
        "research_demo_ready_not_completed_thesis",
        "small-subject ds006072 Schaefer100/Yeo7 unchanged-scoring external stress test",
        "ds006072 top layer differs from the LSD reference top layer",
        "Implemented HCP structural graph and PET receptor-prior sensitivity layers exist",
        "receptor/myelin/gradient mechanism claim remains resolved negative/not promoted",
    ):
        assert expected in gates_doc

    for expected in (
        "Implemented Schaefer100/Yeo7 unchanged-scoring external stress test; top layer differs from LSD",
        "Implemented HCP structural graph sensitivity; still a sensitivity/control layer, not biological proof",
        "Implemented PET receptor-prior sensitivity and spatial-null map-prior checks",
        "Three paired psilocybin/MTP subjects were extracted through Schaefer100/Yeo7",
        "ds006072 top layer = E while LSD reference top layer = C",
    ):
        assert expected in cross_dataset_doc
