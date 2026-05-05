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
