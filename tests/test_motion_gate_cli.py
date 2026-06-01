from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_thesis_upgrade_status",
    ROOT / "scripts" / "build_thesis_upgrade_status.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_thesis_upgrade_status_threads_motion_roots_through_gate_refresh(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    motion_root = tmp_path / "author_confounds"
    repo_root = tmp_path / "repo"
    events: list[tuple[Any, ...]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_thesis_upgrade_status.py",
            "--repo-root",
            str(repo_root),
            "--motion-root",
            str(motion_root),
            "--fetch-motion-remote",
            "--fd-threshold",
            "0.25",
        ],
    )
    monkeypatch.setattr(
        MODULE,
        "write_motion_outputs",
        lambda repo_root, roots, fd_threshold: events.append(
            ("motion", Path(repo_root), tuple(Path(item) for item in roots), fd_threshold)
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "write_motion_confound_control_status",
        lambda repo_root: events.append(("control", Path(repo_root))),
    )
    monkeypatch.setattr(
        MODULE,
        "write_fmriprep_motion_proof_plan",
        lambda repo_root, roots, fetch_remote: events.append(
            ("preflight", Path(repo_root), tuple(Path(item) for item in roots), fetch_remote)
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "write_thesis_upgrade_status",
        lambda repo_root: events.append(("status", Path(repo_root)))
        or {
            "source_path": "results/thesis_upgrade/thesis_upgrade_status.json",
            "report_path": "results/thesis_upgrade/thesis_upgrade_status.md",
        },
    )

    MODULE.main()

    assert events == [
        ("motion", repo_root, (motion_root,), 0.25),
        ("control", repo_root),
        ("preflight", repo_root, (motion_root,), True),
        ("status", repo_root),
    ]
