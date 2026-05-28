import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.web.app import (
    _augment_empirical_viewer_with_run02,
    _load_dashboard_empirical_detail,
    _resolve_artifact_path,
    build_dashboard_payload,
    build_simulation_payload,
    load_empirical_viewer_detail,
    load_empirical_viewer_overview,
)

ROOT = Path(__file__).resolve().parents[1]


def test_simulation_payload_contains_timeseries_fc_and_metrics() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    payload = build_simulation_payload(graph, regime)

    assert "time" in payload
    assert "modules" in payload
    assert "time_series" in payload
    assert "fc_matrix" in payload
    assert "metrics" in payload
    assert len(payload["modules"]) == 8


def test_empirical_viewer_loaders_read_overview_and_subject_detail(tmp_path: Path) -> None:
    viewer_root = tmp_path / "empirical_viewer"
    subject_views = viewer_root / "subject_views"
    subject_views.mkdir(parents=True)
    group_overview = {
        "subjects": ["sub-001"],
        "runs": ["run-01"],
        "default_subject": "sub-001",
        "conditions": {
            "ses-PLCB": {"metrics": {"within_network_stability": 0.2}},
            "ses-LSD": {"metrics": {"within_network_stability": 0.3}},
        },
        "gallery": [{"label": "Empirical metrics", "path": "results/stage_2/figures/example.html"}],
    }
    subject_detail = {
        "subject": "sub-001",
        "run": "run-01",
        "conditions": {
            "ses-PLCB": {"windows": [{"index": 0}]},
            "ses-LSD": {"windows": [{"index": 0}]},
        },
        "window_deltas": [{"index": 0, "metrics": {"within_network_stability": 0.1}}],
    }
    (viewer_root / "group_overview.json").write_text(json.dumps(group_overview), encoding="utf-8")
    (viewer_root / "subject_index.json").write_text(
        json.dumps({"sub-001": ["run-01"]}),
        encoding="utf-8",
    )
    (subject_views / "sub-001_run-01.json").write_text(json.dumps(subject_detail), encoding="utf-8")

    overview = load_empirical_viewer_overview(viewer_root)
    detail = load_empirical_viewer_detail(viewer_root, subject="sub-001", run="run-01")

    assert overview is not None
    assert overview["default_subject"] == "sub-001"
    assert overview["gallery"][0]["label"] == "Empirical metrics"
    assert detail is not None
    assert detail["subject"] == "sub-001"
    assert len(detail["window_deltas"]) == 1


def test_empirical_viewer_overview_filters_to_paired_detail_runs(tmp_path: Path) -> None:
    viewer_root = tmp_path / "empirical_viewer"
    subject_views = viewer_root / "subject_views"
    subject_views.mkdir(parents=True)
    (viewer_root / "group_overview.json").write_text(
        json.dumps(
            {
                "subjects": ["sub-001", "sub-002"],
                "runs": ["run-01", "run-03"],
                "default_subject": "sub-002",
                "conditions": {},
                "gallery": [],
            }
        ),
        encoding="utf-8",
    )
    (viewer_root / "subject_index.json").write_text(
        json.dumps({"sub-001": ["run-01", "run-03"], "sub-002": ["run-01"]}),
        encoding="utf-8",
    )
    (subject_views / "sub-001_run-03.json").write_text(json.dumps({"ok": True}), encoding="utf-8")

    overview = load_empirical_viewer_overview(viewer_root)

    assert overview is not None
    assert overview["subjects"] == ["sub-001"]
    assert overview["runs"] == ["run-03"]
    assert overview["default_subject"] == "sub-001"
    assert overview["subject_index"] == {"sub-001": ["run-03"]}
    assert overview["paired_run_index"] == {"sub-001": ["run-03"]}
    assert overview["display_metadata"]["preview_kind"] == "window_averaged_downsampled_slice_preview"
    assert "not diagnostic images" in overview["display_metadata"]["claim_guardrail"]


def test_empirical_viewer_adds_guarded_run02_music_detail(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run02_viewer = (
        repo_root
        / "results"
        / "setting_seed"
        / "run02_extraction"
        / "stage_2_music"
        / "empirical_viewer"
    )
    subject_views = run02_viewer / "subject_views"
    subject_views.mkdir(parents=True)
    (run02_viewer / "group_overview.json").write_text(
        json.dumps(
            {
                "subjects": ["sub-001"],
                "runs": ["run-01", "run-02", "run-03"],
                "default_subject": "sub-001",
                "subject_index": {"sub-001": ["run-01", "run-02", "run-03"]},
                "module_names": ["visual"],
                "conditions": {},
                "gallery": [],
            }
        ),
        encoding="utf-8",
    )
    (subject_views / "sub-001_run-02.json").write_text(
        json.dumps({"subject": "sub-001", "run": "run-02", "conditions": {}, "window_deltas": []}),
        encoding="utf-8",
    )
    data_audit_path = repo_root / "results" / "setting_seed" / "run02_extraction" / "data_audit"
    data_audit_path.mkdir(parents=True)
    (data_audit_path / "data_audit.json").write_text(
        json.dumps(
            {
                "record_count": 90,
                "subject_count": 15,
                "run_labels": {"run-01": "Rest1", "run-02": "Music", "run-03": "Rest3"},
                "run_02_analysis_ready": True,
                "run_02_files_present": True,
                "run_02_valid_file_count": 24,
                "run_02_expected_file_count": 24,
                "motion_summaries_available": False,
                "motion_analysis_ready": False,
                "analysis_status": {"music_control": "blocked_missing_motion_review"},
                "claim_guardrail": "Data audit is an implemented cache inventory.",
            }
        ),
        encoding="utf-8",
    )
    primary_overview = {
        "subjects": ["sub-001"],
        "runs": ["run-01", "run-03"],
        "default_subject": "sub-001",
        "subject_index": {"sub-001": ["run-01", "run-03"]},
        "module_names": ["visual"],
        "conditions": {},
        "gallery": [],
    }

    overview = _augment_empirical_viewer_with_run02(primary_overview, repo_root)
    detail = _load_dashboard_empirical_detail(repo_root, subject="sub-001", run="run-02")

    assert overview is not None
    assert overview["runs"] == ["run-01", "run-02", "run-03"]
    assert overview["default_run"] == "run-02"
    assert overview["subject_index"] == {"sub-001": ["run-01", "run-02", "run-03"]}
    assert overview["run_labels"]["run-02"] == "Music (exploratory)"
    assert "motion-sensitive claims" in overview["run_caveats"]["run-02"]
    assert overview["run_02_status"]["analysis_ready"] is True
    assert overview["run_02_status"]["music_control"] == "blocked_missing_motion_review"
    assert detail is not None
    assert detail["run_label"] == "Music (exploratory)"
    assert detail["viewer_source"] == "results/setting_seed/run02_extraction/stage_2_music/empirical_viewer"
    assert "exploratory inspection only" in detail["run_caveat"]


def test_resolve_artifact_path_rejects_paths_outside_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    inside_path = repo_root / "docs" / "stage_reports" / "stage_2.md"
    inside_path.parent.mkdir(parents=True)
    inside_path.write_text("# stage 2\n", encoding="utf-8")

    assert _resolve_artifact_path("docs/stage_reports/stage_2.md", repo_root=repo_root) == inside_path.resolve()
    assert _resolve_artifact_path("../outside.md", repo_root=repo_root) is None


def test_resolve_artifact_path_rejects_private_and_non_artifact_roots(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    assert _resolve_artifact_path("configs/regimes/baseline.yaml", repo_root=repo_root) is None
    assert _resolve_artifact_path("tmp/local_debug.json", repo_root=repo_root) is None
    assert _resolve_artifact_path("codex_logs/dashboard.log", repo_root=repo_root) is None
    assert _resolve_artifact_path("data/ds003059/dataset_description.json", repo_root=repo_root) is None
    assert _resolve_artifact_path("output/doc/~$thesis_report_revised.docx", repo_root=repo_root) is None


def test_resolve_artifact_path_allows_report_and_figure_outputs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    assert _resolve_artifact_path("docs/stage_reports/stage_2.md", repo_root=repo_root) is not None
    assert _resolve_artifact_path("output/doc/defense_presentation.pptx", repo_root=repo_root) is not None
    assert _resolve_artifact_path("output/doc/figures/stage1_metric_shift.png", repo_root=repo_root) is not None
    assert _resolve_artifact_path("results/stage_2/figures/group_metrics.html", repo_root=repo_root) is not None
    assert _resolve_artifact_path("results/dynamic_mechanism_ranking/figures/dmdc_fold_rmse.html", repo_root=repo_root) is not None


def test_resolve_artifact_path_rejects_codex_archive(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    archived_file = repo_root / ".codex-archive" / "20260507_120000" / "dashboard_launch.log"
    archived_file.parent.mkdir(parents=True)
    archived_file.write_text("archived local log\n", encoding="utf-8")

    assert _resolve_artifact_path(".codex-archive/20260507_120000/dashboard_launch.log", repo_root=repo_root) is None


def test_dashboard_payload_includes_provenance_block(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "results" / "stage_2").mkdir(parents=True)
    (repo_root / "results" / "stage_3").mkdir(parents=True)
    (repo_root / "configs" / "targets").mkdir(parents=True)
    (repo_root / "docs" / "stage_reports").mkdir(parents=True)
    (repo_root / "docs" / "stage_reports" / "stage_2.md").write_text("# report\n", encoding="utf-8")
    (repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  source_strategy: test",
                "target_deltas:",
                "  within_network_stability: 0.1",
                "  cross_network_communication: 0.2",
                "confidence: {}",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml").write_text(
        "\n".join(
            [
                "metadata:",
                "  source_strategy: test",
                "target_deltas:",
                "  within_network_stability: -0.3",
                "  cross_network_communication: 0.25",
                "confidence: {}",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "results" / "stage_2" / "stage_2_summary.json").write_text(
        json.dumps(
            {
                "best_score": 0.9,
                "selection_score_std": 0.03,
                "selected_iteration": 2,
                "fit_seed_plan": {
                    "proposal_seed": 11,
                    "selection_seeds": [111, 112, 113],
                    "validation_seeds": [1011, 1012],
                    "selection_mode": "multi_seed_mean",
                    "validation_mode": "disjoint_seed_panel",
                },
                "multi_seed_summary": {
                    "role": "validation_seed_panel",
                    "seeds": [1011, 1012],
                    "seed_count": 2,
                    "mean_metrics": {"within_network_stability": 0.2},
                    "std_metrics": {"within_network_stability": 0.01},
                    "score_mean": 0.95,
                    "score_std": 0.05,
                },
                "empirical_validation_boundary": {
                    "held_out": False,
                    "held_out_validation_configured": True,
                    "held_out_validation_completed": False,
                    "split_file_path": "results/stage_2/subject_split.json",
                    "split_schema_version": 1,
                    "split_id": "fixture_candidate_split",
                    "split_strategy": "none_all_available_targets_used_for_selection",
                    "split_seed": 123,
                    "approval_status": "candidate",
                    "selection_data_source": "Empirical anchor",
                    "validation_data_source": None,
                    "selection_subjects": ["sub-001", "sub-002"],
                    "validation_subjects": ["sub-003"],
                    "selection_subject_count": 2,
                    "validation_subject_count": 1,
                    "overlap_count": 0,
                    "claim_guardrail": "Subject-disjoint split is configured, but held-out validation has not yet been completed.",
                },
                "empirical_provenance": {
                    "dataset_id": "ds003059",
                    "dataset_version": "1.0.0",
                    "dataset_anchor": "Empirical anchor",
                    "subjects": ["sub-001", "sub-002"],
                    "subject_count": 2,
                    "sessions": ["ses-LSD", "ses-PLCB"],
                    "runs": ["a", "b", "c", "d"],
                    "run_count": 4,
                    "target_paths": {
                        "sober": str(repo_root / "results" / "stage_2" / "empirical_sober_targets.yaml"),
                        "perturbation": str(repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml"),
                    },
                    "viewer_cache_paths": {},
                    "cache_fingerprint": "abc123",
                    "cache_schema_version": 1,
                    "preprocessing_qc": {"output_record_count": 4},
                    "notes": ["test note"],
                },
                "version_stamp": {
                    "timestamp": "2026-04-13T00:00:00+00:00",
                    "git": {
                        "repo_present": True,
                        "branch": "main",
                        "head_present": False,
                        "commit_hash": None,
                        "worktree_status": "unborn",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (repo_root / "results" / "stage_2" / "atlas_mapping_audit.json").write_text(
        json.dumps(
            {
                "overlaps": [{"atlas": "cortical", "label": 31, "modules": ["visual", "default_mode"]}],
                "module_voxel_counts": {"visual": 10},
                "assigned_voxels": 10,
            }
        ),
        encoding="utf-8",
    )
    (repo_root / "results" / "stage_2" / "empirical_data_quality.json").write_text(
        json.dumps(
            {
                "record_count": 4,
                "paired_subject_count": 2,
                "complete_subject_count": 1,
                "timepoints": {"min": 190, "max": 200, "mean": 195.0},
                "sign_conflicts": [],
            }
        ),
        encoding="utf-8",
    )
    cv5_results_dir = repo_root / "output" / "validation" / "cv5_subject_disjoint" / "results"
    cv5_results_dir.mkdir(parents=True)
    (cv5_results_dir / "cv5_aggregate_validation.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "split_set_id": "cv5_fixture_approved",
                "approval_status": "approved",
                "validation_claim_scope": "preliminary_internal_subject_disjoint_cv5",
                "completed_folds": 5,
                "total_folds": 5,
                "all_folds_completed": True,
                "all_subjects_held_out_once": True,
                "total_subjects": 15,
                "held_out_validation_completed": True,
                "aggregate_path": "output/validation/cv5_subject_disjoint/results/cv5_aggregate_validation.json",
                "run_parameters": {
                    "run_command": (
                        "uv run python scripts/run_cv5_validation.py --manifest "
                        "output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json "
                        "--output-dir output/validation/cv5_subject_disjoint/results --fit-iterations 64 --seed 11"
                    )
                },
                "aggregate_metrics": {
                    "score_mean": {"mean": 0.42, "std": 0.03},
                    "sign_agreement_fraction": {"mean": 0.675, "std": 0.19},
                },
                "limitations": [
                    "Internal validation only; not external validation",
                    "No subject-level motion/FD/DVARS/confound/censoring stratification available",
                ],
            }
        ),
        encoding="utf-8",
    )
    (repo_root / "results" / "stage_3" / "stage_3_summary.json").write_text(
        json.dumps(
            {
                "best_mechanism": "less_hierarchical_constraint",
                "best_score": 1.2,
                "robust_best_mechanism": "more_cross_talk",
                "robust_best_score_mean": 0.8,
                "robust_best_score_std": 0.1,
                "robust_best_sign_agreement_fraction": 0.75,
            }
        ),
        encoding="utf-8",
    )

    graph = SimpleNamespace(modules=("visual", "auditory"), adjacency=np.zeros((2, 2), dtype=float))
    regime = SimpleNamespace(
        global_parameters=SimpleNamespace(within_group_scale=1.0, cross_group_scale=1.0, constraint_scale=1.0),
        module_defaults=SimpleNamespace(rigidity=0.3, barrier=0.8, temperature=0.1, tau=0.9),
    )
    monkeypatch.setattr("lsd_thesis.web.app.load_graph_config", lambda path: graph)
    monkeypatch.setattr("lsd_thesis.web.app.load_regime_config", lambda path: regime)
    monkeypatch.setattr(
        "lsd_thesis.web.app.build_simulation_payload",
        lambda graph, regime: {
            "time": [0.0],
            "modules": list(graph.modules),
            "time_series": [[0.0, 0.0]],
            "fc_matrix": [[1.0, 0.0], [0.0, 1.0]],
            "metrics": {"within_network_stability": 0.2},
        },
    )

    payload = build_dashboard_payload(repo_root)

    assert payload["provenance"]["dataset_anchor"] == "Empirical anchor"
    assert payload["provenance"]["subject_count"] == 2
    assert payload["provenance"]["run_count"] == 4
    assert payload["provenance"]["sessions"] == ["ses-LSD", "ses-PLCB"]
    assert payload["provenance"]["target_filenames"]["sober"] == "empirical_sober_targets.yaml"
    assert payload["provenance"]["git"]["worktree_status"] == "unborn"
    assert payload["audit_status"]["sign_mismatches"][0]["metric"] == "within_network_stability"
    assert payload["audit_status"]["provenance_warning"].startswith("No git HEAD")
    assert payload["audit_status"]["stage3_best_mechanism"] == "more_cross_talk"
    assert payload["audit_status"]["stage3_score"] == 0.8
    assert payload["audit_status"]["stage3_score_std"] == 0.1
    assert payload["audit_status"]["atlas_assigned_voxels"] == 10
    assert payload["audit_status"]["empirical_record_count"] == 4
    assert payload["audit_status"]["empirical_complete_subject_count"] == 1
    assert payload["model_selection"]["selection_mode"] == "multi_seed_mean"
    assert payload["model_selection"]["selection_seed_count"] == 3
    assert payload["model_selection"]["validation_score_mean"] == 0.95
    assert payload["empirical_validation"]["held_out"] is False
    assert payload["empirical_validation"]["held_out_validation_configured"] is True
    assert payload["empirical_validation"]["held_out_validation_completed"] is False
    assert payload["empirical_validation"]["split_file_path"] == "results/stage_2/subject_split.json"
    assert payload["empirical_validation"]["split_schema_version"] == 1
    assert payload["empirical_validation"]["split_id"] == "fixture_candidate_split"
    assert payload["empirical_validation"]["approval_status"] == "candidate"
    assert payload["empirical_validation"]["selection_subject_count"] == 2
    assert payload["empirical_validation"]["validation_subject_count"] == 1
    assert payload["empirical_validation"]["overlap_count"] == 0
    assert payload["cv5_validation"]["held_out_validation_completed"] is True
    assert payload["cv5_validation"]["completed_folds"] == 5
    assert payload["cv5_validation"]["validation_claim_scope"] == "preliminary_internal_subject_disjoint_cv5"
    assert payload["cv5_validation"]["run_parameters"]["run_command"].startswith("uv run python scripts/run_cv5_validation.py")
    assert payload["audit_status"]["cv5_validation"]["all_subjects_held_out_once"] is True
    assert payload["audit_status"]["cache_status"]["status"] == "fingerprinted"
    assert payload["provenance"]["preprocessing_qc"]["output_record_count"] == 4
    assert payload["dynamic_mechanism"]["analysis_status"] == "missing"
    assert payload["dynamic_mechanism"]["source_path"] == "results/dynamic_mechanism_ranking/summary.json"
    assert payload["structural_dti"]["analysis_status"] == "missing_structural_connectome_matrix"


def test_dashboard_payload_includes_publication_outputs_in_report_links(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "results" / "stage_2").mkdir(parents=True)
    (repo_root / "docs" / "stage_reports").mkdir(parents=True)
    (repo_root / "docs" / "stage_reports" / "stage_2.md").write_text("# stage 2\n", encoding="utf-8")
    (repo_root / "output" / "doc").mkdir(parents=True)
    (repo_root / "output" / "doc" / "thesis_report_revised.md").write_text("# thesis\n", encoding="utf-8")
    (repo_root / "output" / "doc" / "thesis_report_revised.docx").write_bytes(b"docx")
    (repo_root / "output" / "doc" / "defense_outline.md").write_text("# defense\n", encoding="utf-8")
    (repo_root / "output" / "doc" / "defense_outline.docx").write_bytes(b"docx")
    (repo_root / "output" / "doc" / "thesis_microsite.html").write_text("<html></html>", encoding="utf-8")
    (repo_root / "output" / "doc" / "defense_presentation.html").write_text("<html></html>", encoding="utf-8")
    (repo_root / "output" / "doc" / "defense_presentation.pptx").write_bytes(b"pptx")
    (repo_root / "output" / "doc" / "figures").mkdir(parents=True)
    (repo_root / "output" / "doc" / "figures" / "stage1_metric_shift.png").write_bytes(b"png")
    (repo_root / "output" / "doc" / "figures" / "stage2_fit_robustness.png").write_bytes(b"png")
    dynamic_figures = repo_root / "results" / "dynamic_mechanism_ranking" / "figures"
    dynamic_figures.mkdir(parents=True)
    (dynamic_figures / "dmdc_fold_rmse.html").write_text("<html></html>", encoding="utf-8")
    (repo_root / "results" / "stage_2" / "stage_2_summary.json").write_text(
        json.dumps(
            {
                "best_score": 0.9,
                "empirical_provenance": {
                    "dataset_anchor": "Empirical anchor",
                    "subject_count": 2,
                    "run_count": 4,
                    "sessions": ["ses-LSD", "ses-PLCB"],
                    "target_paths": {},
                },
                "version_stamp": {
                    "timestamp": "2026-04-13T00:00:00+00:00",
                    "git": {
                        "repo_present": True,
                        "branch": "main",
                        "head_present": False,
                        "commit_hash": None,
                        "worktree_status": "unborn",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    graph = SimpleNamespace(modules=("visual", "auditory"), adjacency=np.zeros((2, 2), dtype=float))
    regime = SimpleNamespace(
        global_parameters=SimpleNamespace(within_group_scale=1.0, cross_group_scale=1.0, constraint_scale=1.0),
        module_defaults=SimpleNamespace(rigidity=0.3, barrier=0.8, temperature=0.1, tau=0.9),
    )
    monkeypatch.setattr("lsd_thesis.web.app.load_graph_config", lambda path: graph)
    monkeypatch.setattr("lsd_thesis.web.app.load_regime_config", lambda path: regime)
    monkeypatch.setattr(
        "lsd_thesis.web.app.build_simulation_payload",
        lambda graph, regime: {
            "time": [0.0],
            "modules": list(graph.modules),
            "time_series": [[0.0, 0.0]],
            "fc_matrix": [[1.0, 0.0], [0.0, 1.0]],
            "metrics": {"within_network_stability": 0.2},
        },
    )

    payload = build_dashboard_payload(repo_root)
    report_links = payload["artifact_links"]["reports"]
    report_hrefs = {item["href"] for item in report_links}
    figure_links = payload["artifact_links"]["figures"]
    figure_hrefs = {item["href"] for item in figure_links}

    assert "/artifacts/docs/stage_reports/stage_2.md" in report_hrefs
    assert "/artifacts/output/doc/thesis_report_revised.md" in report_hrefs
    assert "/artifacts/output/doc/thesis_report_revised.docx" in report_hrefs
    assert "/artifacts/output/doc/defense_outline.md" in report_hrefs
    assert "/artifacts/output/doc/defense_outline.docx" in report_hrefs
    assert "/artifacts/output/doc/thesis_microsite.html" in report_hrefs
    assert "/artifacts/output/doc/defense_presentation.html" in report_hrefs
    assert "/artifacts/output/doc/defense_presentation.pptx" in report_hrefs
    assert "/artifacts/output/doc/figures/stage1_metric_shift.png" in figure_hrefs
    assert "/artifacts/output/doc/figures/stage2_fit_robustness.png" in figure_hrefs
    assert "/artifacts/results/dynamic_mechanism_ranking/figures/dmdc_fold_rmse.html" in figure_hrefs


def test_dashboard_payload_rewrites_gallery_paths_relative_to_repo_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    outside_root = tmp_path / "outside"
    outside_root.mkdir(parents=True)

    (repo_root / "results" / "stage_2" / "empirical_viewer").mkdir(parents=True)
    (repo_root / "results" / "stage_2" / "figures").mkdir(parents=True)
    (repo_root / "results" / "stage_2" / "figures" / "example.html").write_text(
        "<html></html>",
        encoding="utf-8",
    )
    (repo_root / "results" / "stage_2" / "stage_2_summary.json").write_text(
        json.dumps(
            {
                "best_score": 0.9,
                "empirical_provenance": {
                    "dataset_anchor": "Empirical anchor",
                    "subject_count": 2,
                    "run_count": 4,
                    "sessions": ["ses-LSD", "ses-PLCB"],
                    "target_paths": {},
                },
                "version_stamp": {
                    "timestamp": "2026-04-13T00:00:00+00:00",
                    "git": {
                        "repo_present": True,
                        "branch": "main",
                        "head_present": False,
                        "commit_hash": None,
                        "worktree_status": "unborn",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (repo_root / "results" / "stage_2" / "empirical_viewer" / "group_overview.json").write_text(
        json.dumps(
            {
                "subjects": ["sub-001"],
                "runs": ["run-01"],
                "default_subject": "sub-001",
                "subject_index": {"sub-001": ["run-01"]},
                "module_names": ["visual", "auditory"],
                "conditions": {},
                "gallery": [
                    {
                        "label": "Empirical metrics",
                        "path": "results/stage_2/figures/example.html",
                    },
                    {
                        "label": "Windows absolute empirical metrics",
                        "path": "D:\\LSD_Thesis\\results\\stage_2\\figures\\example.html",
                    },
                    {
                        "label": "Outside",
                        "path": "../outside/outside.html",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    graph = SimpleNamespace(modules=("visual", "auditory"), adjacency=np.zeros((2, 2), dtype=float))
    regime = SimpleNamespace(
        global_parameters=SimpleNamespace(within_group_scale=1.0, cross_group_scale=1.0, constraint_scale=1.0),
        module_defaults=SimpleNamespace(rigidity=0.3, barrier=0.8, temperature=0.1, tau=0.9),
    )
    monkeypatch.setattr("lsd_thesis.web.app.load_graph_config", lambda path: graph)
    monkeypatch.setattr("lsd_thesis.web.app.load_regime_config", lambda path: regime)
    monkeypatch.setattr(
        "lsd_thesis.web.app.build_simulation_payload",
        lambda graph, regime: {
            "time": [0.0],
            "modules": list(graph.modules),
            "time_series": [[0.0, 0.0]],
            "fc_matrix": [[1.0, 0.0], [0.0, 1.0]],
            "metrics": {"within_network_stability": 0.2},
        },
    )
    monkeypatch.chdir(outside_root)

    payload = build_dashboard_payload(repo_root)

    assert payload["empirical_viewer"] is not None
    assert len(payload["empirical_viewer"]["gallery"]) == 2
    assert payload["empirical_viewer"]["gallery"][0]["href"] == "/artifacts/results/stage_2/figures/example.html"
    assert payload["empirical_viewer"]["gallery"][1]["href"] == "/artifacts/results/stage_2/figures/example.html"


def test_dashboard_template_contains_scholarly_sections_and_figure_links() -> None:
    html = (ROOT / "src" / "lsd_thesis" / "templates" / "dashboard.html").read_text(encoding="utf-8")

    for heading in (
        "Thesis Snapshot",
        "AI/ML Mechanism Ranking",
        "Scientific Story",
        "How to Read This Dashboard",
        "Data and Input Summary",
        "Methods and Pipeline Overview",
        "Model Assumptions",
        "Validation Summary",
        "Empirical Validation Boundary",
        "CV5 Fold Results",
        "Metrics and Diagnostics",
        "Figures and Captions",
        "Limitations and Reviewer Notes",
        "Methods Appendix / Details",
        "Empirical/fMRI Explorer",
        "Group-Level Empirical Evidence",
        "Reproducibility and Provenance",
        "Reproduce This Dashboard Snapshot",
        "Artifact Browser",
        "Pipeline Status",
    ):
        assert heading in html
    assert "Hiring-Readiness Claim Evidence Matrix" in html
    assert "CSV/XLSX export" in html
    assert "Plot Review: Core Evidence vs Appendix" in html
    assert 'data-plot-role="core"' in html
    assert 'id="model_explorer_appendix"' in html
    assert 'id="empirical_preview_appendix"' in html
    assert "Support score (unitless)" in html
    assert "Pearson r (unitless)" in html
    assert "Delta Pearson r (unitless)" in html
    assert "z-scored BOLD proxy" in html
    assert "/assets/plotly.min.js" in html
    assert "artifactLinks.figures" in html

    for container_id in (
        "audit_status",
        "validation_status",
        "model_selection_status",
        "provenance_status",
        "preview_status",
        "stage_status",
        "hero_metrics",
        "cv5_summary_cards",
        "cv5_fold_plot",
        "cv5_fold_table",
        "empirical_viewer_notice",
        "empirical_viewer_badges",
        "empirical_run_quick_select",
        "graph_plot",
        "dynamic_mechanism_status",
        "claim_evidence_matrix_table",
        "claim_evidence_links",
        "dynamic_mechanism_cards",
        "dynamic_mechanism_table",
        "dynamic_mechanism_inference_gating",
        "dynamic_mechanism_inference_table",
        "dynamic_figure_links",
        "dynamic_transition_plot",
        "dynamic_dmdc_plot",
        "dynamic_condition_vector_plot",
        "dynamic_hierarchy_plot",
        "dynamic_repertoire_plot",
        "dynamic_control_plot",
        "time_plot",
        "fc_plot",
        "perturbed_fc_plot",
        "delta_plot",
        "ablation_plot",
        "empirical_group_traces",
        "empirical_group_metric_delta",
        "empirical_group_fc_delta",
        "empirical_raw_plcb",
        "empirical_raw_lsd",
        "empirical_interpretation",
    ):
        assert f'id="{container_id}"' in html

    assert "Uncertainty here is seed-sampling spread, not an external confidence interval." in html
    assert "Current QC exposure is aggregate-only" in html
    assert "Aggregate preprocessing QC records" in html
    assert "CV5 uncertainty: fold SD is descriptive across folds" in html
    assert "Dual-axis descriptive plot" in html
    assert "five-fold subject-disjoint internal validation" in html
    assert "Downsampled exploratory preview; not a diagnostic anatomical image." in html
    assert "Within-dataset ds003059 summary" in html
    assert "not evidence of subjective-state realism" in html
    assert "empiricalRunLabel" in html
    assert "Run caveat:" in html
    assert "run-02 exploratory" in html
    assert "overview.default_run" in html
    assert "selected perturbation family in proxy-objective space" in html
    assert "Proxy interpretation" in html
    assert "summary.json" in html
    assert "Minimum q-value" in html
    assert "FDR-significant metrics" in html
    assert "CI overlaps zero" in html
    assert "renderDynamicInferenceGating(dynamicMechanism, inferenceTable);" in html
    assert "This static method board mirrors" not in html
    assert "renderDynamicMechanism(dashboardState.dynamic_mechanism);" in html
    assert "CV5 rerun command" in html
    assert "uv run python scripts/run_dashboard.py" in html
    assert 'class="skip-link"' in html
    assert 'id="main_content"' in html
    assert 'aria-pressed="false"' in html
    assert 'aria-live="polite"' in html
    assert 'id="empirical_summary" role="status" aria-live="polite" aria-atomic="true"' in html
    assert "section[id], main[id] { scroll-margin-top: 96px; }" in html
    assert "#cv5_fold_results { overflow-x: auto; }" in html
    assert "repeat(auto-fit, minmax(150px, 1fr))" in html
    assert "const isFocused = module === focusedModule;" in html
    assert "renderSubjectSignals(subjectDetail, currentWindow);" in html
    assert "@media print" in html
    assert "zmid: 0" in html


def test_dashboard_inline_javascript_passes_node_syntax_check(tmp_path: Path) -> None:
    html = (ROOT / "src" / "lsd_thesis" / "templates" / "dashboard.html").read_text(encoding="utf-8")
    script_start = html.index("<script>") + len("<script>")
    script_end = html.rindex("</script>")
    script_path = tmp_path / "dashboard.js"
    script_path.write_text(html[script_start:script_end], encoding="utf-8")

    result = subprocess.run(
        ["node", "--check", str(script_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
