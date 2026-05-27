"""Shared helpers used across multiple pipeline modules."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go


def _run_git_command(args: list[str], repo_root: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None


def get_version_stamp(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Return UTC timestamp plus explicit git repository state."""
    timestamp = datetime.now(UTC).isoformat()
    resolved_root = Path.cwd() if repo_root is None else Path(repo_root)

    inside_worktree = _run_git_command(["rev-parse", "--is-inside-work-tree"], resolved_root)
    if inside_worktree is None or inside_worktree.returncode != 0 or inside_worktree.stdout.strip() != "true":
        return {
            "timestamp": timestamp,
            "git": {
                "repo_present": False,
                "branch": None,
                "head_present": False,
                "commit_hash": None,
                "worktree_status": "not_repo",
            },
        }

    branch_result = _run_git_command(["branch", "--show-current"], resolved_root)
    branch = None
    if branch_result is not None and branch_result.returncode == 0:
        branch = branch_result.stdout.strip() or None

    head_result = _run_git_command(["rev-parse", "--verify", "HEAD"], resolved_root)
    head_present = bool(head_result is not None and head_result.returncode == 0)
    commit_hash = head_result.stdout.strip() if head_present and head_result is not None else None

    if not head_present:
        worktree_status = "unborn"
    else:
        status_result = _run_git_command(["status", "--porcelain"], resolved_root)
        is_dirty = bool(status_result is not None and status_result.returncode == 0 and status_result.stdout.strip())
        worktree_status = "dirty" if is_dirty else "clean"

    try:
        return {
            "timestamp": timestamp,
            "git": {
                "repo_present": True,
                "branch": branch,
                "head_present": head_present,
                "commit_hash": commit_hash,
                "worktree_status": worktree_status,
            },
        }
    except Exception:
        return {
            "timestamp": timestamp,
            "git": {
                "repo_present": True,
                "branch": branch,
                "head_present": head_present,
                "commit_hash": commit_hash,
                "worktree_status": "unborn" if not head_present else "dirty",
            },
        }


def save_figure(figure: go.Figure, path: Path) -> None:
    """Write a Plotly figure to an HTML file, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(str(path), include_plotlyjs="cdn")


def resolve_under(root: str | Path, relative_path: str | Path) -> Path:
    """Resolve a user/cache-provided path while requiring it to stay under root."""
    resolved_root = Path(root).resolve()
    raw_path = str(relative_path)
    if "\\" in raw_path:
        raw_path = raw_path.replace("\\", "/")
    if len(raw_path) >= 2 and raw_path[1] == ":":
        raise ValueError(f"Path is outside the allowed root {resolved_root}: {relative_path}")
    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise ValueError(f"Path is outside the allowed root {resolved_root}: {candidate}")
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path is outside the allowed root {resolved_root}: {candidate}") from exc
    return resolved


def confidence_weight(label: str) -> float:
    """Map a confidence label to a numeric weight for scoring."""
    mapping = {
        "strong": 2.0,
        "strongest": 2.2,
        "moderate_strong": 1.8,
        "moderate": 1.4,
        "weak": 0.8,
    }
    return mapping.get(label, 1.0)


def mean_metric_dict(metric_dicts: list[dict[str, float]]) -> dict[str, float]:
    """Average a list of metric dicts into a single dict."""
    metric_names = metric_dicts[0].keys()
    return {
        name: float(np.mean([item[name] for item in metric_dicts]))
        for name in metric_names
    }


def std_metric_dict(metric_dicts: list[dict[str, float]]) -> dict[str, float]:
    """Compute sample standard deviation across a list of metric dicts."""
    metric_names = metric_dicts[0].keys()
    return {
        name: float(np.std([item[name] for item in metric_dicts], ddof=1))
        for name in metric_names
    }
