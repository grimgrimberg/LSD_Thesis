import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from lsd_thesis.data.ds003059 import (
    DS003059_DEFAULT_RUNS,
    EMPIRICAL_CACHE_METADATA_FILENAME,
    Ds003059EmpiricalRecord,
    Ds003059RestManifest,
    Ds003059RunRecord,
    atlas_label_overlap_rows,
    atlas_label_overlaps,
    atlas_module_label_rows,
    build_atlas_mapping_audit,
    build_empirical_cache_metadata,
    build_empirical_data_quality_payload,
    build_empirical_target_payloads,
    build_preprocessing_qc_summary,
    build_rest_manifest_from_listing,
    generate_empirical_targets,
    normalize_ds003059_runs,
    query_snapshot_files,
    validate_empirical_cache_metadata,
)


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
        "sub-001-lsd": [
            {"filename": "func", "key": "sub-001-lsd-func", "directory": True},
        ],
        "sub-001-plcb": [
            {"filename": "func", "key": "sub-001-plcb-func", "directory": True},
        ],
        "sub-001-lsd-func": [
            {
                "filename": "._sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                "key": "bad-appledouble",
                "directory": False,
                "urls": ["https://example.com/bad"],
                "size": 4096,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_bold.json",
                "key": "json-1",
                "directory": False,
                "urls": ["https://example.com/json-1"],
                "size": 80,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                "key": "run-01",
                "directory": False,
                "urls": ["https://example.com/run-01"],
                "size": 101,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_run-02_bold.nii.gz",
                "key": "run-02",
                "directory": False,
                "urls": ["https://example.com/run-02"],
                "size": 102,
            },
            {
                "filename": "sub-001_ses-LSD_task-rest_run-03_bold.nii.gz",
                "key": "run-03",
                "directory": False,
                "urls": ["https://example.com/run-03"],
                "size": 103,
            },
        ],
        "sub-001-plcb-func": [
            {
                "filename": "sub-001_ses-PLCB_task-rest_bold.json",
                "key": "json-2",
                "directory": False,
                "urls": ["https://example.com/json-2"],
                "size": 80,
            },
            {
                "filename": "sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                "key": "plcb-run-01",
                "directory": False,
                "urls": ["https://example.com/plcb-run-01"],
                "size": 201,
            },
            {
                "filename": "sub-001_ses-PLCB_task-rest_run-02_bold.nii.gz",
                "key": "plcb-run-02",
                "directory": False,
                "urls": ["https://example.com/plcb-run-02"],
                "size": 202,
            },
            {
                "filename": "sub-001_ses-PLCB_task-rest_run-03_bold.nii.gz",
                "key": "plcb-run-03",
                "directory": False,
                "urls": ["https://example.com/plcb-run-03"],
                "size": 203,
            },
        ],
        "subject-002": [],
    }

    manifest = build_rest_manifest_from_listing(
        root_listing=root_listing,
        tree_lookup=tree_lookup,
    )

    assert manifest.subjects == ("sub-001",)
    assert len(manifest.runs) == 4
    assert {run.run for run in manifest.runs} == {"run-01", "run-03"}
    assert not any("run-02" in run.filename for run in manifest.runs)
    assert not any(run.filename.startswith("._") for run in manifest.runs)
    assert set(manifest.sidecars) == {
        "sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_bold.json",
        "sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_bold.json",
    }


def test_run_selector_defaults_to_rest_and_requires_explicit_music_flag() -> None:
    assert normalize_ds003059_runs() == DS003059_DEFAULT_RUNS
    assert normalize_ds003059_runs(include_music=True) == ("run-01", "run-02", "run-03")
    assert normalize_ds003059_runs(("run-03", "run-01")) == ("run-01", "run-03")

    with pytest.raises(ValueError, match="requires include_music=True"):
        normalize_ds003059_runs(("run-01", "run-02", "run-03"))


def test_build_rest_manifest_can_include_music_only_when_flagged() -> None:
    root_listing = [{"filename": "sub-001", "key": "subject-001", "directory": True}]
    tree_lookup = {
        "subject-001": [
            {"filename": "ses-LSD", "key": "sub-001-lsd", "directory": True},
        ],
        "sub-001-lsd": [{"filename": "func", "key": "sub-001-lsd-func", "directory": True}],
        "sub-001-lsd-func": [
            {
                "filename": f"sub-001_ses-LSD_task-rest_{run}_bold.nii.gz",
                "key": run,
                "directory": False,
                "urls": [f"https://example.com/{run}"],
                "size": 100,
            }
            for run in ["run-01", "run-02", "run-03"]
        ],
    }

    manifest = build_rest_manifest_from_listing(root_listing, tree_lookup, include_music=True)

    assert tuple(run.run for run in manifest.runs) == ("run-01", "run-02", "run-03")


def test_query_snapshot_files_uses_current_openneuro_schema_and_aliases_tree_key(monkeypatch) -> None:
    captured_queries: list[str] = []

    def fake_graphql_query(query: str) -> dict[str, object]:
        captured_queries.append(query)
        return {
            "data": {
                "snapshot": {
                    "files": [
                        {
                            "filename": "sub-001",
                            "id": "tree-object-id",
                            "directory": True,
                            "size": 0,
                            "annexed": False,
                            "urls": [],
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr("lsd_thesis.data.ds003059._run_graphql_query", fake_graphql_query)

    files = query_snapshot_files("ds003059", "1.0.0", tree="parent-tree-id")

    assert " key" not in captured_queries[0]
    assert 'files(tree: "parent-tree-id")' in captured_queries[0]
    assert files[0]["id"] == "tree-object-id"
    assert files[0]["key"] == "tree-object-id"


def test_atlas_audit_helpers_expose_known_overlapping_proxy_labels() -> None:
    label_rows = atlas_module_label_rows()
    overlaps = atlas_label_overlaps()
    overlap_rows = atlas_label_overlap_rows()

    assert {"module": "visual", "atlas": "cortical", "label": 31} in label_rows
    assert overlaps["cortical"][31] == ("visual", "default_mode")
    assert overlaps["cortical"][42] == ("auditory", "sensorimotor")
    assert {"atlas": "cortical", "label": 31, "modules": ["visual", "default_mode"]} in overlap_rows


def test_build_atlas_mapping_audit_counts_assigned_module_voxels() -> None:
    label_volume = np.asarray(
        [
            [[0, 1], [2, 2]],
            [[3, 0], [8, 8]],
        ],
        dtype=np.int16,
    )
    labels_img = nib.Nifti1Image(label_volume, affine=np.eye(4))

    audit = build_atlas_mapping_audit(labels_img)

    assert audit["assigned_voxels"] == 6
    assert audit["unassigned_voxels"] == 2
    assert audit["module_voxel_counts"]["visual"] == 1
    assert audit["module_voxel_counts"]["auditory"] == 2
    assert audit["module_voxel_counts"]["sensorimotor"] == 2


def test_build_atlas_mapping_audit_loads_cached_harvard_oxford_files(tmp_path: Path) -> None:
    atlas_root = tmp_path / "nilearn_data" / "fsl" / "data" / "atlases" / "HarvardOxford"
    atlas_root.mkdir(parents=True)
    cortical = np.asarray(
        [
            [[0, 22], [31, 42]],
            [[7, 0], [0, 0]],
        ],
        dtype=np.int16,
    )
    subcortical = np.asarray(
        [
            [[0, 0], [0, 0]],
            [[0, 4], [0, 0]],
        ],
        dtype=np.int16,
    )
    nib.Nifti1Image(cortical, affine=np.eye(4)).to_filename(
        atlas_root / "HarvardOxford-cort-maxprob-thr25-2mm.nii.gz"
    )
    nib.Nifti1Image(subcortical, affine=np.eye(4)).to_filename(
        atlas_root / "HarvardOxford-sub-maxprob-thr25-2mm.nii.gz"
    )

    audit = build_atlas_mapping_audit(include_voxel_counts=True, nilearn_data_dir=tmp_path / "nilearn_data")

    assert audit["assigned_voxels"] == 5
    assert audit["module_voxel_counts"]["visual"] == 1
    assert audit["module_voxel_counts"]["default_mode"] == 1
    assert audit["module_voxel_counts"]["sensorimotor"] == 2
    assert audit["module_voxel_counts"]["thalamic_gateway"] == 1


def test_build_empirical_target_payloads_uses_paired_subject_deltas() -> None:
    records = [
        {
            "subject": "sub-001",
            "session": "ses-PLCB",
            "run": "run-01",
            "metrics": {
                "within_network_stability": 0.40,
                "cross_network_communication": 0.10,
                "thalamic_coupling": 0.05,
                "hierarchical_compression": 0.20,
                "entropy_diversity": 0.70,
                "switching_rate": 0.10,
                "metastability_proxy": 1.20,
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
                "thalamic_coupling": 0.16,
                "hierarchical_compression": 0.28,
                "entropy_diversity": 0.82,
                "switching_rate": 0.18,
                "metastability_proxy": 1.35,
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
                "thalamic_coupling": 0.04,
                "hierarchical_compression": 0.18,
                "entropy_diversity": 0.68,
                "switching_rate": 0.09,
                "metastability_proxy": 1.15,
                "effective_barrier_proxy": 14.0,
            },
            "fc_matrix": np.full((8, 8), 0.08),
        },
        {
            "subject": "sub-002",
            "session": "ses-LSD",
            "run": "run-03",
            "metrics": {
                "within_network_stability": 0.20,
                "cross_network_communication": 0.18,
                "thalamic_coupling": 0.12,
                "hierarchical_compression": 0.24,
                "entropy_diversity": 0.78,
                "switching_rate": 0.16,
                "metastability_proxy": 1.30,
                "effective_barrier_proxy": 10.0,
            },
            "fc_matrix": np.full((8, 8), 0.18),
        },
    ]

    sober_payload, perturbation_payload = build_empirical_target_payloads(
        records=records,
        module_names=(
            "visual",
            "auditory",
            "salience",
            "default_mode",
            "executive_frontoparietal",
            "limbic_affective",
            "thalamic_gateway",
            "sensorimotor",
        ),
    )

    assert sober_payload["dataset_anchor"].startswith("OpenNeuro ds003059")
    assert sober_payload["metrics"]["within_network_stability"]["target"] == 0.375
    assert sober_payload["metrics"]["cross_network_communication"]["target"] == 0.09
    assert sober_payload["fc_matrix"][0][0] == 0.09
    assert perturbation_payload["target_deltas"]["within_network_stability"] == -0.15
    assert perturbation_payload["target_deltas"]["cross_network_communication"] == pytest.approx(0.11)
    assert perturbation_payload["target_deltas"]["effective_barrier_proxy"] == pytest.approx(-3.5)


def test_build_empirical_data_quality_payload_reports_completeness_and_sign_conflicts() -> None:
    records = [
        {
            "subject": "sub-001",
            "session": "ses-PLCB",
            "run": "run-01",
            "timepoints": 200,
            "metrics": {"within_network_stability": 0.2},
        },
        {
            "subject": "sub-001",
            "session": "ses-LSD",
            "run": "run-01",
            "timepoints": 198,
            "metrics": {"within_network_stability": 0.3},
        },
        {
            "subject": "sub-002",
            "session": "ses-PLCB",
            "run": "run-03",
            "timepoints": 190,
            "metrics": {"within_network_stability": 0.2},
        },
    ]

    quality = build_empirical_data_quality_payload(
        records=records,
        empirical_deltas={"within_network_stability": 0.1},
        literature_deltas={"within_network_stability": -0.3},
    )

    assert quality["record_count"] == 3
    assert quality["subject_count"] == 2
    assert quality["paired_subject_count"] == 1
    assert quality["complete_subject_count"] == 0
    assert quality["timepoints"]["min"] == 190
    assert quality["sign_conflicts"][0]["metric"] == "within_network_stability"
    assert quality["preprocessing_qc"]["output_record_count"] == 3


def test_preprocessing_qc_summary_reports_transform_and_proxy_limitations() -> None:
    records = [
        {
            "subject": "sub-001",
            "session": "ses-PLCB",
            "run": "run-01",
            "timepoints": 12,
            "metrics": {"within_network_stability": 0.2},
            "fc_matrix": np.eye(2).tolist(),
            "time_series_path": "module_time_series/example.npy",
        }
    ]

    summary = build_preprocessing_qc_summary(records)

    assert summary["input_run_count"] == 1
    assert summary["output_record_count"] == 1
    assert summary["missing_values"] == 0
    assert summary["parcellation"]["parcellation_id"] == "harvard_oxford_8_module_proxy"
    assert "run_02_music" in summary["exclusion_policy"]["excluded_reasons"]
    assert any("does not rerun full scanner-level preprocessing" in item for item in summary["limitations"])


def test_empirical_cache_metadata_validates_and_detects_stale_or_wrong_subject_cache(tmp_path: Path) -> None:
    manifest = Ds003059RestManifest(
        subjects=("sub-001",),
        runs=(
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-PLCB",
                run="run-01",
                filename="sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                url="",
                size=10,
            ),
        ),
        sidecars=(),
    )
    record = {
        "subject": "sub-001",
        "session": "ses-PLCB",
        "run": "run-01",
        "relative_path": manifest.runs[0].relative_path,
        "timepoints": 12,
        "metrics": {"within_network_stability": 0.2},
        "fc_matrix": np.eye(8).tolist(),
        "time_series_path": "module_time_series/sub-001.npy",
    }
    output_path = tmp_path / "stage_2"
    output_path.mkdir()
    (output_path / "empirical_sober_targets.yaml").write_text("dataset_anchor: test\n", encoding="utf-8")
    (output_path / "empirical_perturbation_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (output_path / "ds003059_rest_manifest.json").write_text(
        manifest.model_dump_json(),
        encoding="utf-8",
    )
    (output_path / "empirical_run_summaries.json").write_text(
        json.dumps([record]),
        encoding="utf-8",
    )
    metadata = build_empirical_cache_metadata(
        output_path=output_path,
        manifest=manifest,
        records=[record],
        requested_subjects=("sub-001",),
    )
    metadata_path = output_path / EMPIRICAL_CACHE_METADATA_FILENAME
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    validated = validate_empirical_cache_metadata(output_path, requested_subjects=("sub-001",))

    assert validated["cache_fingerprint"] == metadata["cache_fingerprint"]
    with pytest.raises(ValueError, match="requested-subject mismatch"):
        validate_empirical_cache_metadata(output_path, requested_subjects=("sub-002",))

    metadata_path.write_text(json.dumps({**metadata, "schema_version": -1}), encoding="utf-8")
    with pytest.raises(ValueError, match="schema mismatch"):
        validate_empirical_cache_metadata(output_path, requested_subjects=("sub-001",))

    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    (output_path / "empirical_sober_targets.yaml").write_text("dataset_anchor: changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        validate_empirical_cache_metadata(output_path, requested_subjects=("sub-001",))


def test_empirical_cache_metadata_validates_raw_run_file_provenance_changes(tmp_path: Path) -> None:
    manifest = Ds003059RestManifest(
        subjects=("sub-001",),
        runs=(
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-PLCB",
                run="run-01",
                filename="sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                url="",
                size=16,
            ),
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-LSD",
                run="run-01",
                filename="sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                url="",
                size=16,
            ),
        ),
        sidecars=(),
    )
    record = {
        "subject": "sub-001",
        "session": "ses-PLCB",
        "run": "run-01",
        "relative_path": manifest.runs[0].relative_path,
        "timepoints": 12,
        "metrics": {"within_network_stability": 0.2},
        "fc_matrix": np.eye(8).tolist(),
        "time_series_path": "module_time_series/sub-001.npy",
    }

    output_path = tmp_path / "stage_2"
    dataset_root = tmp_path / "dataset"
    run_01_path = dataset_root / manifest.runs[0].relative_path
    run_02_path = dataset_root / manifest.runs[1].relative_path
    output_path.mkdir(parents=True)
    run_01_path.parent.mkdir(parents=True, exist_ok=True)
    run_02_path.parent.mkdir(parents=True, exist_ok=True)
    run_01_path.write_bytes(b"initial-run-01")
    run_02_path.write_bytes(b"initial-run-02")

    (output_path / "empirical_sober_targets.yaml").write_text("dataset_anchor: test\n", encoding="utf-8")
    (output_path / "empirical_perturbation_targets.yaml").write_text("target_deltas: {}\n", encoding="utf-8")
    (output_path / "ds003059_rest_manifest.json").write_text(
        manifest.model_dump_json(),
        encoding="utf-8",
    )
    (output_path / "empirical_run_summaries.json").write_text(
        json.dumps([record]),
        encoding="utf-8",
    )

    metadata = build_empirical_cache_metadata(
        output_path=output_path,
        manifest=manifest,
        records=[record],
        requested_subjects=("sub-001",),
        dataset_dir=dataset_root,
    )
    metadata_path = output_path / EMPIRICAL_CACHE_METADATA_FILENAME
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    validate_empirical_cache_metadata(
        output_path,
        requested_subjects=("sub-001",),
        dataset_dir=dataset_root,
    )

    run_01_path.write_bytes(b"tampered-run-01")

    with pytest.raises(ValueError, match="raw run-file fingerprints changed"):
        validate_empirical_cache_metadata(
            output_path,
            requested_subjects=("sub-001",),
            dataset_dir=dataset_root,
        )


def test_generate_empirical_targets_regenerates_when_cache_metadata_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-PLCB",
                run="run-01",
                filename="sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                url="",
                size=10,
            ),
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-LSD",
                run="run-01",
                filename="sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                url="",
                size=10,
            ),
        ),
        sidecars=(),
    )
    metrics = {
        "within_network_stability": 0.2,
        "cross_network_communication": 0.1,
    }
    records = (
        Ds003059EmpiricalRecord(
            subject="sub-001",
            session="ses-PLCB",
            run="run-01",
            relative_path=manifest.runs[0].relative_path,
            timepoints=12,
            metrics=metrics,
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

    monkeypatch.setattr(
        "lsd_thesis.data.ds003059.fetch_ds003059_rest_manifest",
        lambda subjects=None, runs=None, include_music=False: manifest,
    )
    monkeypatch.setattr("lsd_thesis.data.ds003059.download_ds003059_rest_runs", lambda manifest, target_dir: ())
    monkeypatch.setattr("lsd_thesis.data.ds003059.extract_empirical_run_records", lambda **kwargs: records)

    result = generate_empirical_targets(
        dataset_dir=tmp_path / "dataset",
        output_dir=output_path,
        subjects=("sub-001",),
    )

    assert result["manifest"].subjects == ("sub-001",)
    assert (output_path / EMPIRICAL_CACHE_METADATA_FILENAME).exists()
    assert "stale" not in (output_path / "empirical_sober_targets.yaml").read_text(encoding="utf-8")
    assert result["cache_metadata"]["requested_subjects"] == ["sub-001"]
