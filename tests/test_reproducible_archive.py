from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.reproducible_archive import build_archive_manifest, write_archive_manifest


def test_archive_manifest_records_publication_not_ready_without_release_and_doi(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = build_archive_manifest(tmp_path)

    assert manifest["artifact_count"] == 1
    assert manifest["release_url"] is None
    assert manifest["doi"] is None
    assert manifest["archive_publication_ready"] is False
    assert manifest["publication_metadata"]["release_url_valid"] is False
    assert manifest["publication_metadata"]["doi_valid"] is False


def test_archive_manifest_accepts_citable_release_url_and_zenodo_doi(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Thesis\n", encoding="utf-8")

    manifest = build_archive_manifest(
        tmp_path,
        release_url="https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0",
        doi="https://doi.org/10.5281/zenodo.1234567",
    )

    assert manifest["archive_publication_ready"] is True
    assert manifest["release_url"] == "https://github.com/grimgrimberg/LSD_Thesis/releases/tag/v1.0.0"
    assert manifest["doi"] == "https://doi.org/10.5281/zenodo.1234567"
    assert manifest["publication_metadata"]["release_url_valid"] is True
    assert manifest["publication_metadata"]["doi_valid"] is True


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
    )

    manifest_path = tmp_path / "results" / "reproducible_archive" / "ARCHIVE_MANIFEST.json"
    written = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["archive_publication_ready"] is True
    assert written["archive_publication_ready"] is True
    assert written["publication_metadata"]["doi_valid"] is True
