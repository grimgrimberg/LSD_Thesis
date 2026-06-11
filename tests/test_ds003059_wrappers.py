from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from lsd_thesis.data import ds003059
from lsd_thesis.data.ds003059.models import (
    Ds003059EmpiricalRecord,
    Ds003059RestManifest,
    Ds003059RunRecord,
)


def _run_record(subject: str, session: str, run: str, *, url: str = "") -> Ds003059RunRecord:
    filename = f"{subject}_{session}_task-rest_{run}_bold.nii.gz"
    return Ds003059RunRecord(
        subject=subject,
        session=session,
        run=run,
        filename=filename,
        relative_path=f"{subject}/{session}/func/{filename}",
        url=url,
        size=123,
    )


def _write_minimal_cache_artifacts(output_path: Path, manifest: Ds003059RestManifest) -> dict[str, Any]:
    output_path.mkdir(parents=True, exist_ok=True)
    record = {
        "subject": manifest.runs[0].subject,
        "session": manifest.runs[0].session,
        "run": manifest.runs[0].run,
        "relative_path": manifest.runs[0].relative_path,
        "timepoints": 12,
        "metrics": {"within_network_stability": 0.2},
        "fc_matrix": np.eye(8).tolist(),
        "time_series_path": "module_time_series/sub-001_plcb.npy",
    }
    (output_path / "empirical_sober_targets.yaml").write_text("dataset_anchor: test\n", encoding="utf-8")
    (output_path / "empirical_perturbation_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (output_path / "ds003059_rest_manifest.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    (output_path / "empirical_run_summaries.json").write_text(json.dumps([record]), encoding="utf-8")
    return record


def test_query_snapshot_files_uses_package_level_graphql_hook(monkeypatch) -> None:
    calls: list[str] = []

    def fake_graphql(query: str) -> dict[str, Any]:
        calls.append(query)
        return {"data": {"snapshot": {"files": [{"filename": "sub-001", "id": "node", "directory": True}]}}}

    monkeypatch.setattr(ds003059, "_run_graphql_query", fake_graphql)

    files = ds003059.query_snapshot_files("ds-test", "v1.0.0")

    assert files == [{"filename": "sub-001", "id": "node", "directory": True, "key": "node"}]
    assert calls and "ds-test" in calls[0]


def test_run_selector_defaults_to_rest_and_requires_explicit_music_flag() -> None:
    assert ds003059.normalize_ds003059_runs() == ds003059.DS003059_DEFAULT_RUNS
    assert ds003059.normalize_ds003059_runs(include_music=True) == ("run-01", "run-02", "run-03")
    assert ds003059.normalize_ds003059_runs(("run-03", "run-01")) == ("run-01", "run-03")

    with pytest.raises(ValueError, match="requires include_music=True"):
        ds003059.normalize_ds003059_runs(("run-01", "run-02", "run-03"))


def test_build_rest_manifest_filters_music_and_appledouble_files() -> None:
    root_listing = [
        {"filename": "sub-001", "key": "subject-001", "directory": True},
        {"filename": "sub-002", "key": "subject-002", "directory": True},
    ]
    tree_lookup = {
        "subject-001": [
            {"filename": "ses-LSD", "key": "sub-001-lsd", "directory": True},
            {"filename": "ses-PLCB", "key": "sub-001-plcb", "directory": True},
        ],
        "sub-001-lsd": [{"filename": "func", "key": "sub-001-lsd-func", "directory": True}],
        "sub-001-plcb": [{"filename": "func", "key": "sub-001-plcb-func", "directory": True}],
        "sub-001-lsd-func": [
            {
                "filename": "._sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                "key": "bad-appledouble",
                "directory": False,
                "urls": ["https://example.test/bad"],
                "size": 4096,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_bold.json",
                "key": "json-1",
                "directory": False,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                "key": "lsd-run-01",
                "directory": False,
                "urls": ["https://example.test/lsd-run-01"],
                "size": 101,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_run-02_bold.nii.gz",
                "key": "lsd-run-02",
                "directory": False,
                "urls": ["https://example.test/lsd-run-02"],
                "size": 102,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_run-03_bold.nii.gz",
                "key": "lsd-run-03",
                "directory": False,
                "urls": ["https://example.test/lsd-run-03"],
                "size": 103,
            },
            {
                "filename": "sub-001_ses-LSD_task-music_run-01_bold.nii.gz",
                "key": "wrong-task",
                "directory": False,
                "urls": ["https://example.test/wrong-task"],
                "size": 104,
            },
        ],
        "sub-001-plcb-func": [
            {
                "filename": "sub-001_ses-PLCB_task-rest_bold.json",
                "key": "json-2",
                "directory": False,
            },
            {
                "filename": "sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                "key": "plcb-run-01",
                "directory": False,
                "urls": ["https://example.test/plcb-run-01"],
                "size": 201,
            },
            {
                "filename": "sub-001_ses-PLCB_task-rest_run-02_bold.nii.gz",
                "key": "plcb-run-02",
                "directory": False,
                "urls": ["https://example.test/plcb-run-02"],
                "size": 202,
            },
            {
                "filename": "sub-001_ses-PLCB_task-rest_run-03_bold.nii.gz",
                "key": "plcb-run-03",
                "directory": False,
                "urls": ["https://example.test/plcb-run-03"],
                "size": 203,
            },
        ],
        "subject-002": [],
    }

    manifest = ds003059.build_rest_manifest_from_listing(root_listing=root_listing, tree_lookup=tree_lookup)

    assert manifest.subjects == ("sub-001",)
    assert len(manifest.runs) == 4
    assert {run.run for run in manifest.runs} == {"run-01", "run-03"}
    assert not any("run-02" in run.filename for run in manifest.runs)
    assert not any(run.filename.startswith("._") for run in manifest.runs)
    assert set(manifest.sidecars) == {
        "sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_bold.json",
        "sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_bold.json",
    }


def test_build_rest_manifest_can_include_music_only_when_flagged() -> None:
    root_listing = [{"filename": "sub-001", "key": "subject-001", "directory": True}]
    tree_lookup = {
        "subject-001": [{"filename": "ses-LSD", "key": "sub-001-lsd", "directory": True}],
        "sub-001-lsd": [{"filename": "func", "key": "sub-001-lsd-func", "directory": True}],
        "sub-001-lsd-func": [
            {
                "filename": f"sub-001_ses-LSD_task-rest_{run}_bold.nii.gz",
                "key": run,
                "directory": False,
                "urls": [f"https://example.test/{run}"],
                "size": 100,
            }
            for run in ("run-01", "run-02", "run-03")
        ],
    }

    manifest = ds003059.build_rest_manifest_from_listing(root_listing, tree_lookup, include_music=True)

    assert tuple(run.run for run in manifest.runs) == ("run-01", "run-02", "run-03")


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


def test_cache_metadata_sanitizes_urls_and_invalidates_changed_artifacts(tmp_path: Path) -> None:
    manifest = Ds003059RestManifest(
        subjects=("sub-001",),
        runs=(_run_record("sub-001", "ses-PLCB", "run-01", url="https://example.test/run.nii.gz"),),
        sidecars=(),
    )
    sanitized = ds003059.sanitize_rest_manifest_for_cache(manifest)
    output_path = tmp_path / "stage_2"
    record = _write_minimal_cache_artifacts(output_path, sanitized)

    metadata = ds003059.build_empirical_cache_metadata(
        output_path=output_path,
        manifest=sanitized,
        records=[record],
        requested_subjects=("sub-001",),
    )
    metadata_path = output_path / ds003059.EMPIRICAL_CACHE_METADATA_FILENAME
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    validated = ds003059.validate_empirical_cache_metadata(output_path, requested_subjects=("sub-001",))

    assert sanitized.runs[0].url == ""
    assert validated["cache_fingerprint"] == metadata["cache_fingerprint"]
    with pytest.raises(ValueError, match="requested-subject mismatch"):
        ds003059.validate_empirical_cache_metadata(output_path, requested_subjects=("sub-002",))

    (output_path / "empirical_sober_targets.yaml").write_text("dataset_anchor: changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        ds003059.validate_empirical_cache_metadata(output_path, requested_subjects=("sub-001",))


def test_cache_metadata_detects_raw_run_file_provenance_changes(tmp_path: Path) -> None:
    manifest = Ds003059RestManifest(
        subjects=("sub-001",),
        runs=(
            _run_record("sub-001", "ses-PLCB", "run-01"),
            _run_record("sub-001", "ses-LSD", "run-01"),
        ),
        sidecars=(),
    )
    output_path = tmp_path / "stage_2"
    dataset_root = tmp_path / "dataset"
    record = _write_minimal_cache_artifacts(output_path, manifest)
    for run in manifest.runs:
        run_path = dataset_root / run.relative_path
        run_path.parent.mkdir(parents=True, exist_ok=True)
        run_path.write_bytes(f"initial-{run.session}".encode())

    metadata = ds003059.build_empirical_cache_metadata(
        output_path=output_path,
        manifest=manifest,
        records=[record],
        requested_subjects=("sub-001",),
        dataset_dir=dataset_root,
    )
    (output_path / ds003059.EMPIRICAL_CACHE_METADATA_FILENAME).write_text(json.dumps(metadata), encoding="utf-8")

    ds003059.validate_empirical_cache_metadata(
        output_path,
        requested_subjects=("sub-001",),
        dataset_dir=dataset_root,
    )
    (dataset_root / manifest.runs[0].relative_path).write_bytes(b"tampered-run")

    with pytest.raises(ValueError, match="raw run-file fingerprints changed"):
        ds003059.validate_empirical_cache_metadata(
            output_path,
            requested_subjects=("sub-001",),
            dataset_dir=dataset_root,
        )


def test_build_empirical_target_payloads_uses_paired_subject_deltas() -> None:
    records = [
        {
            "subject": "sub-001",
            "session": "ses-PLCB",
            "run": "run-01",
            "metrics": {
                "within_network_stability": 0.40,
                "cross_network_communication": 0.10,
                "effective_barrier_proxy": 12.0,
            },
            "fc_matrix": np.full((8, 8), 0.10),
        },
        {
            "subject": "sub-001",
            "session": "ses-LSD",
            "run": "run-01",
            "metrics": {
                "within_network_stability": 0.25,
                "cross_network_communication": 0.22,
                "effective_barrier_proxy": 9.0,
            },
            "fc_matrix": np.full((8, 8), 0.20),
        },
        {
            "subject": "sub-002",
            "session": "ses-PLCB",
            "run": "run-03",
            "metrics": {
                "within_network_stability": 0.35,
                "cross_network_communication": 0.08,
                "effective_barrier_proxy": 14.0,
            },
            "fc_matrix": np.full((8, 8), 0.08),
        },
        {
            "subject": "sub-002",
            "session": "ses-LSD",
            "run": "run-03",
            "metrics": {
                "within_network_stability": 0.19,
                "cross_network_communication": 0.18,
                "effective_barrier_proxy": 10.0,
            },
            "fc_matrix": np.full((8, 8), 0.18),
        },
    ]

    sober_payload, perturbation_payload = ds003059.build_empirical_target_payloads(
        records=records,
        module_names=tuple(ds003059.MODULE_NAMES),
    )

    assert sober_payload["dataset_anchor"].startswith("OpenNeuro ds003059")
    assert sober_payload["metrics"]["within_network_stability"]["target"] == 0.375
    assert sober_payload["metrics"]["cross_network_communication"]["target"] == 0.09
    assert sober_payload["fc_matrix"][0][0] == 0.09
    assert perturbation_payload["target_deltas"]["within_network_stability"] == pytest.approx(-0.155)
    assert perturbation_payload["target_deltas"]["cross_network_communication"] == pytest.approx(0.11)
    assert perturbation_payload["target_deltas"]["effective_barrier_proxy"] == pytest.approx(-3.5)


def test_generate_empirical_targets_regenerates_when_cache_metadata_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "stage_2"
    output_path.mkdir()
    (output_path / "empirical_sober_targets.yaml").write_text("dataset_anchor: stale\n", encoding="utf-8")
    (output_path / "empirical_perturbation_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (output_path / "ds003059_rest_manifest.json").write_text('{"subjects": [], "runs": [], "sidecars": []}', encoding="utf-8")
    (output_path / "empirical_run_summaries.json").write_text("[]", encoding="utf-8")

    manifest = Ds003059RestManifest(
        subjects=("sub-001",),
        runs=(
            _run_record("sub-001", "ses-PLCB", "run-01", url="https://example.test/plcb.nii.gz"),
            _run_record("sub-001", "ses-LSD", "run-01", url="https://example.test/lsd.nii.gz"),
        ),
        sidecars=(),
    )
    records = (
        Ds003059EmpiricalRecord(
            subject="sub-001",
            session="ses-PLCB",
            run="run-01",
            relative_path=manifest.runs[0].relative_path,
            timepoints=12,
            metrics={"within_network_stability": 0.2, "cross_network_communication": 0.1},
            fc_matrix=np.eye(8),
            time_series_path="module_time_series/sub-001_plcb.npy",
        ),
        Ds003059EmpiricalRecord(
            subject="sub-001",
            session="ses-LSD",
            run="run-01",
            relative_path=manifest.runs[1].relative_path,
            timepoints=12,
            metrics={"within_network_stability": 0.3, "cross_network_communication": 0.15},
            fc_matrix=np.eye(8),
            time_series_path="module_time_series/sub-001_lsd.npy",
        ),
    )
    fetch_calls: list[tuple[tuple[str, ...] | None, tuple[str, ...] | None, bool]] = []
    extract_manifests: list[Ds003059RestManifest] = []

    def fake_fetch(
        subjects: tuple[str, ...] | None = None,
        runs: tuple[str, ...] | None = None,
        *,
        include_music: bool = False,
    ) -> Ds003059RestManifest:
        fetch_calls.append((subjects, runs, include_music))
        return manifest

    def fake_extract(**kwargs: Any) -> tuple[Ds003059EmpiricalRecord, ...]:
        extract_manifests.append(kwargs["manifest"])
        return records

    monkeypatch.setattr(ds003059, "fetch_ds003059_rest_manifest", fake_fetch)
    monkeypatch.setattr(ds003059, "download_ds003059_rest_runs", lambda manifest, target_dir: ())
    monkeypatch.setattr(ds003059, "extract_empirical_run_records", fake_extract)

    result = ds003059.generate_empirical_targets(
        dataset_dir=tmp_path / "dataset",
        output_dir=output_path,
        subjects=("sub-001",),
    )

    assert fetch_calls == [(("sub-001",), ds003059.DS003059_DEFAULT_RUNS, False)]
    assert extract_manifests and all(run.url == "" for run in extract_manifests[0].runs)
    assert result["manifest"].subjects == ("sub-001",)
    assert (output_path / ds003059.EMPIRICAL_CACHE_METADATA_FILENAME).exists()
    assert "stale" not in (output_path / "empirical_sober_targets.yaml").read_text(encoding="utf-8")
    assert result["cache_metadata"]["requested_subjects"] == ["sub-001"]
