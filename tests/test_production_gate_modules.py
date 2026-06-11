from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.fmriprep_motion_proof import build_fmriprep_motion_proof_plan
from lsd_thesis.reproducible_archive import (
    build_archive_manifest,
    collect_archive_artifacts,
    existing_publication_metadata_args,
    verify_publication_metadata,
    write_archive_manifest,
)
from lsd_thesis.setting_seed.motion import build_motion_summary, summarize_motion_tsv


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload))


def _confound_text() -> str:
    return "\n".join(
        [
            "framewise_displacement\tstd_dvars\tmotion_outlier00",
            "0.10\t1.0\t0",
            "0.70\t2.0\t1",
            "0.20\t1.5\t0",
        ]
    )


def _write_paired_confound_set(root: Path) -> Path:
    motion_root = root / "data" / "ds003059" / "derivatives" / "fmriprep"
    for subject in range(1, 5):
        for session in ("ses-LSD", "ses-PLCB"):
            _write_text(
                motion_root
                / f"sub-{subject:03d}"
                / session
                / "func"
                / f"sub-{subject:03d}_{session}_task-rest_run-01_desc-confounds_timeseries.tsv",
                _confound_text(),
            )
    return motion_root


def test_archive_manifest_excludes_private_inputs_and_fails_closed_without_doi(tmp_path: Path) -> None:
    _write_text(tmp_path / "README.md", "release notes")
    _write_text(tmp_path / "docs" / "ARCHIVE_POLICY.md", "policy")
    _write_text(tmp_path / "data" / "raw.txt", "raw data")
    _write_text(tmp_path / ".env", "SECRET=blocked")

    artifacts = collect_archive_artifacts(
        tmp_path,
        include_files=("README.md", "docs/ARCHIVE_POLICY.md", "data/raw.txt", ".env"),
    )
    manifest = build_archive_manifest(
        tmp_path,
        release_url="https://github.com/grimgrimberg/LSD_Thesis/releases/tag/test",
        doi=None,
        publication_verification={"release_url_verified": True},
    )

    assert [row["path"] for row in artifacts] == ["README.md", "docs/ARCHIVE_POLICY.md"]
    assert manifest["publication_metadata"]["release_url_valid"] is True
    assert manifest["publication_metadata"]["doi_valid"] is False
    assert manifest["archive_publication_ready"] is False
    assert "raw OpenNeuro neuroimaging data" in manifest["claim_guardrail"]


def test_archive_manifest_marks_publication_ready_only_after_release_and_doi_verify(tmp_path: Path) -> None:
    _write_text(tmp_path / "README.md", "release notes")

    manifest = write_archive_manifest(
        tmp_path,
        release_url="https://github.com/grimgrimberg/LSD_Thesis/releases/tag/test",
        doi="10.5281/zenodo.12345",
        publication_verification={
            "release_url_verified": True,
            "doi_verified": True,
            "release_url_verification_method": "test",
            "doi_verification_method": "test",
            "publication_verification_status": "verified",
        },
    )
    args = existing_publication_metadata_args(tmp_path)

    assert manifest["archive_publication_ready"] is True
    assert manifest["recommended_publication"]["doi_status"] == "verified"
    assert (tmp_path / manifest["manifest_path"]).exists()
    assert (tmp_path / manifest["checksum_path"]).exists()
    assert args["doi"] == "10.5281/zenodo.12345"
    assert args["publication_verification"]["doi_verified"] is True


def test_publication_metadata_shape_validation_does_not_hit_network_for_invalid_inputs() -> None:
    metadata = verify_publication_metadata(release_url="https://example.test/release", doi="not-a-doi")

    assert metadata["release_url_verified"] is False
    assert metadata["doi_verified"] is False
    assert metadata["release_url_verification_method"] == "shape_invalid"
    assert metadata["doi_verification_method"] == "shape_invalid"


def test_motion_summary_and_fmriprep_proof_pass_with_paired_fd_dvars_censoring(tmp_path: Path) -> None:
    _write_json(tmp_path / "data" / "ds003059" / "dataset_description.json", {"DatasetType": "raw"})
    motion_root = _write_paired_confound_set(tmp_path)

    first_file = next(motion_root.rglob("*desc-confounds_timeseries.tsv"))
    first_summary = summarize_motion_tsv(first_file)
    motion_summary = build_motion_summary(tmp_path, roots=(motion_root,))
    proof = build_fmriprep_motion_proof_plan(
        tmp_path,
        roots=(motion_root,),
        runtime_availability={"docker": False, "apptainer": False, "singularity": False, "fmriprep": False},
    )

    assert first_summary["status"] == "available_parsed"
    assert first_summary["fd_column"] == "framewise_displacement"
    assert first_summary["dvars_column"] == "std_dvars"
    assert first_summary["scrubbed_volume_count"] == 1
    assert motion_summary["motion_analysis_ready"] is True
    assert motion_summary["motion_pairing_ready"] is True
    assert motion_summary["paired_subject_run_count"] == 4
    assert proof["analysis_status"] == "structured_subject_level_confounds_available"
    assert proof["fmriprep_motion_proof_ready"] is True
    assert proof["existing_motion_confounds"]["motion_feature_family_coverage"] == {
        "fd": True,
        "dvars": True,
        "censoring": True,
    }


def test_fmriprep_preflight_fails_closed_for_derivative_snapshot_without_confounds(tmp_path: Path) -> None:
    _write_json(tmp_path / "data" / "ds003059" / "dataset_description.json", {"DatasetType": "derivative"})

    proof = build_fmriprep_motion_proof_plan(tmp_path, runtime_availability={})

    assert proof["analysis_status"] == "blocked_derivative_snapshot_not_valid_raw_fmriprep_input"
    assert proof["fmriprep_motion_proof_ready"] is False
    assert proof["existing_motion_confounds"]["missing_motion_feature_families"] == [
        "fd",
        "dvars",
        "censoring",
    ]
    assert "preprocessing/acquisition preflight" in proof["claim_guardrail"]
