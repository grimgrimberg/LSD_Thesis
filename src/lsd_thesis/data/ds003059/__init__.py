from __future__ import annotations

from pathlib import Path
from typing import Any

from . import extraction as _extraction
from . import generation as _generation
from . import openneuro as _openneuro
from .atlas import (
    _build_macro_module_labels_image,
    atlas_label_overlap_rows,
    atlas_label_overlaps,
    atlas_module_label_rows,
    build_atlas_mapping_audit,
)
from .cache import (
    EMPIRICAL_CACHE_METADATA_FILENAME,
    _file_sha256,
    _manifest_core_payload,
    _stable_json_hash,
    build_empirical_cache_metadata,
    build_empirical_data_quality_payload,
    build_empirical_target_payloads,
    build_preprocessing_qc_summary,
    sanitize_rest_manifest_for_cache,
    validate_empirical_cache_metadata,
)
from .constants import (
    DS003059_ALLOWED_RUNS,
    DS003059_DATASET_ID,
    DS003059_DEFAULT_RUNS,
    DS003059_MUSIC_RUN,
    DS003059_MUSIC_RUNS,
    DS003059_SESSIONS,
    DS003059_VERSION,
    EMPIRICAL_CACHE_SCHEMA_VERSION,
    HARVARD_OXFORD_CORTICAL_FILENAME,
    HARVARD_OXFORD_SUBCORTICAL_FILENAME,
    MODULE_ATLAS_LABELS,
    MODULE_NAMES,
    OPENNEURO_GRAPHQL_URL,
)
from .extraction import extract_empirical_run_records
from .models import Ds003059EmpiricalRecord, Ds003059RestManifest, Ds003059RunRecord
from .openneuro import build_rest_manifest_from_listing
from .runs import normalize_ds003059_runs
from .serialization import _to_plain_python

nib = _extraction.nib
NiftiLabelsMasker = _extraction.NiftiLabelsMasker


def _run_graphql_query(query: str) -> dict[str, Any]:
    return _openneuro._run_graphql_query(query)


def query_snapshot_files(dataset_id: str, tag: str, tree: str | None = None) -> list[dict[str, Any]]:
    previous = _openneuro._run_graphql_query
    _openneuro._run_graphql_query = _run_graphql_query
    try:
        return _openneuro.query_snapshot_files(dataset_id, tag, tree=tree)
    finally:
        _openneuro._run_graphql_query = previous


def fetch_ds003059_rest_manifest(subjects: tuple[str, ...] | None = None, runs: Any = None, *, include_music: bool = False) -> Ds003059RestManifest:
    previous = _openneuro.query_snapshot_files
    _openneuro.query_snapshot_files = query_snapshot_files
    try:
        return _openneuro.fetch_ds003059_rest_manifest(subjects=subjects, runs=runs, include_music=include_music)
    finally:
        _openneuro.query_snapshot_files = previous


def _download_url_to_path(url: str, destination: Path, expected_size: int) -> Path:
    return _openneuro._download_url_to_path(url, destination, expected_size)


def download_ds003059_rest_runs(manifest: Ds003059RestManifest, target_dir: str | Path) -> tuple[Path, ...]:
    previous = _openneuro._download_url_to_path
    _openneuro._download_url_to_path = _download_url_to_path
    try:
        return _openneuro.download_ds003059_rest_runs(manifest, target_dir)
    finally:
        _openneuro._download_url_to_path = previous


def extract_module_time_series(run_path: str | Path, labels_img: Any = None) -> Any:
    previous_masker = _extraction.NiftiLabelsMasker
    previous_build = _extraction._build_macro_module_labels_image
    _extraction.NiftiLabelsMasker = NiftiLabelsMasker
    _extraction._build_macro_module_labels_image = _build_macro_module_labels_image
    try:
        return _extraction.extract_module_time_series(run_path, labels_img=labels_img)
    finally:
        _extraction.NiftiLabelsMasker = previous_masker
        _extraction._build_macro_module_labels_image = previous_build


def generate_empirical_targets(
    dataset_dir: str | Path,
    output_dir: str | Path,
    subjects: tuple[str, ...] | None = None,
    runs: Any = None,
    *,
    include_music: bool = False,
) -> dict[str, Any]:
    previous_fetch = _generation.fetch_ds003059_rest_manifest
    previous_download = _generation.download_ds003059_rest_runs
    previous_extract = _generation.extract_empirical_run_records
    _generation.fetch_ds003059_rest_manifest = fetch_ds003059_rest_manifest
    _generation.download_ds003059_rest_runs = download_ds003059_rest_runs
    _generation.extract_empirical_run_records = extract_empirical_run_records
    try:
        return _generation.generate_empirical_targets(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            subjects=subjects,
            runs=runs,
            include_music=include_music,
        )
    finally:
        _generation.fetch_ds003059_rest_manifest = previous_fetch
        _generation.download_ds003059_rest_runs = previous_download
        _generation.extract_empirical_run_records = previous_extract


__all__ = [
    "DS003059_ALLOWED_RUNS",
    "DS003059_DATASET_ID",
    "DS003059_DEFAULT_RUNS",
    "DS003059_MUSIC_RUN",
    "DS003059_MUSIC_RUNS",
    "DS003059_SESSIONS",
    "DS003059_VERSION",
    "EMPIRICAL_CACHE_METADATA_FILENAME",
    "EMPIRICAL_CACHE_SCHEMA_VERSION",
    "HARVARD_OXFORD_CORTICAL_FILENAME",
    "HARVARD_OXFORD_SUBCORTICAL_FILENAME",
    "MODULE_ATLAS_LABELS",
    "MODULE_NAMES",
    "OPENNEURO_GRAPHQL_URL",
    "Ds003059EmpiricalRecord",
    "Ds003059RestManifest",
    "Ds003059RunRecord",
    "NiftiLabelsMasker",
    "_build_macro_module_labels_image",
    "_download_url_to_path",
    "_file_sha256",
    "_manifest_core_payload",
    "_run_graphql_query",
    "_stable_json_hash",
    "_to_plain_python",
    "atlas_label_overlap_rows",
    "atlas_label_overlaps",
    "atlas_module_label_rows",
    "build_atlas_mapping_audit",
    "build_empirical_cache_metadata",
    "build_empirical_data_quality_payload",
    "build_empirical_target_payloads",
    "build_preprocessing_qc_summary",
    "build_rest_manifest_from_listing",
    "download_ds003059_rest_runs",
    "extract_empirical_run_records",
    "extract_module_time_series",
    "fetch_ds003059_rest_manifest",
    "generate_empirical_targets",
    "normalize_ds003059_runs",
    "nib",
    "query_snapshot_files",
    "sanitize_rest_manifest_for_cache",
    "validate_empirical_cache_metadata",
]
