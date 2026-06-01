from __future__ import annotations

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
