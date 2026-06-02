from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.reproducible_archive import build_archive_manifest, existing_publication_metadata_args, write_archive_manifest


def test_archive_manifest_records_publication_not_ready_without_release_and_doi(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = build_archive_manifest(tmp_path)

    assert manifest["artifact_count"] == 1
    assert manifest["release_url"] is None
    assert manifest["doi"] is None
    assert manifest["archive_publication_ready"] is False
    assert manifest["publication_metadata"]["release_url_valid"] is False
    assert manifest["publication_metadata"]["doi_valid"] is False


def test_archive_manifest_includes_current_validation_baseline_when_present(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")
    validation_doc = tmp_path / "docs" / "VALIDATION.md"
    validation_doc.parent.mkdir(parents=True)
    validation_doc.write_text("# Validation Notes\n", encoding="utf-8")

    manifest = build_archive_manifest(tmp_path)

    assert {row["path"] for row in manifest["artifacts"]} == {
        "README.md",
        "docs/VALIDATION.md",
    }


def test_archive_manifest_keeps_unverified_release_url_and_zenodo_doi_below_publication_ready(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = build_archive_manifest(
        tmp_path,
        release_url="https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0",
        doi="https://doi.org/10.5281/zenodo.1234567",
    )

    assert manifest["archive_publication_ready"] is False
    assert manifest["release_url"] == "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0"
    assert manifest["doi"] == "https://doi.org/10.5281/zenodo.1234567"
    assert manifest["publication_metadata"]["release_url_valid"] is True
    assert manifest["publication_metadata"]["doi_valid"] is True
    assert manifest["publication_metadata"]["release_url_verified"] is False
    assert manifest["publication_metadata"]["doi_verified"] is False


def test_archive_manifest_accepts_verified_citable_release_url_and_zenodo_doi(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = build_archive_manifest(
        tmp_path,
        release_url="https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0",
        doi="https://doi.org/10.5281/zenodo.1234567",
        publication_verification={
            "release_url_verified": True,
            "doi_verified": True,
        },
    )

    assert manifest["archive_publication_ready"] is True
    assert manifest["publication_metadata"]["release_url_valid"] is True
    assert manifest["publication_metadata"]["doi_valid"] is True
    assert manifest["publication_metadata"]["release_url_verified"] is True
    assert manifest["publication_metadata"]["doi_verified"] is True


def test_existing_publication_metadata_args_preserves_release_verification(tmp_path: Path) -> None:
    archive_dir = tmp_path / "results" / "reproducible_archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        json.dumps(
            {
                "release_url": "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/thesis-evidence-2026-06-02",
                "doi": None,
                "publication_metadata": {
                    "release_url_verified": True,
                    "doi_verified": False,
                    "release_url_verification_method": "https_head_or_get",
                    "doi_verification_method": "missing",
                    "publication_verification_status": "not_verified",
                },
            }
        ),
        encoding="utf-8",
    )

    assert existing_publication_metadata_args(tmp_path) == {
        "release_url": "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/thesis-evidence-2026-06-02",
        "publication_verification": {
            "release_url_verified": True,
            "doi_verified": False,
            "release_url_verification_method": "https_head_or_get",
            "doi_verification_method": "missing",
            "publication_verification_status": "not_verified",
        },
    }


def test_archive_manifest_rejects_placeholder_publication_metadata(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = build_archive_manifest(
        tmp_path,
        release_url="GitHub public repository release",
        doi="Zenodo DOI minted from GitHub release",
    )

    assert manifest["archive_publication_ready"] is False
    assert manifest["publication_metadata"]["release_url_valid"] is False
    assert manifest["publication_metadata"]["doi_valid"] is False


def test_write_archive_manifest_writes_publication_metadata(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = write_archive_manifest(
        tmp_path,
        release_url="https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0",
        doi="10.5281/zenodo.1234567",
        publication_verification={
            "release_url_verified": True,
            "doi_verified": True,
        },
    )

    manifest_path = tmp_path / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"
    written = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["archive_publication_ready"] is True
    assert written["archive_publication_ready"] is True
    assert written["publication_metadata"]["doi_valid"] is True
