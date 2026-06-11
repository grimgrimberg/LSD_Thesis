from __future__ import annotations

from pathlib import Path
from typing import Any

from lsd_thesis.data import ds003059
from lsd_thesis.data.ds003059.models import Ds003059RestManifest, Ds003059RunRecord


def test_query_snapshot_files_uses_package_level_graphql_hook(monkeypatch) -> None:
    calls: list[str] = []

    def fake_graphql(query: str) -> dict[str, Any]:
        calls.append(query)
        return {"data": {"snapshot": {"files": [{"filename": "sub-001", "id": "node", "directory": True}]}}}

    monkeypatch.setattr(ds003059, "_run_graphql_query", fake_graphql)

    files = ds003059.query_snapshot_files("ds-test", "v1.0.0")

    assert files == [{"filename": "sub-001", "id": "node", "directory": True, "key": "node"}]
    assert calls and "ds-test" in calls[0]


def test_download_rest_runs_uses_package_level_download_hook(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, Path, int]] = []

    def fake_download(url: str, destination: Path, expected_size: int) -> Path:
        calls.append((url, destination, expected_size))
        return destination

    monkeypatch.setattr(ds003059, "_download_url_to_path", fake_download)
    manifest = Ds003059RestManifest(
        subjects=("sub-001",),
        runs=(
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-LSD",
                run="run-01",
                filename="sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                url="https://example.test/run.nii.gz",
                size=123,
            ),
        ),
        sidecars=(),
    )

    paths = ds003059.download_ds003059_rest_runs(manifest, tmp_path)

    assert paths == (tmp_path / manifest.runs[0].relative_path,)
    assert calls == [("https://example.test/run.nii.gz", tmp_path / manifest.runs[0].relative_path, 123)]
