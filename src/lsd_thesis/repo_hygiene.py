from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path


def _relative_posix_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def find_ignored_source_paths(repo_root: str | Path, paths: Iterable[str | Path]) -> list[str]:
    """Return repo-relative source paths that Git ignore rules currently hide."""
    root = Path(repo_root)
    ignored_paths: list[str] = []
    for path in paths:
        relative_path = _relative_posix_path(root, Path(path))
        result = subprocess.run(
            ["git", "check-ignore", "-q", relative_path],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            ignored_paths.append(relative_path)
        elif result.returncode != 1:
            raise RuntimeError(f"git check-ignore failed for {relative_path}.")
    return ignored_paths
