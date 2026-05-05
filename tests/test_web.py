import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config
from lsd_thesis.web.app import (
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


def test_resolve_artifact_path_rejects_paths_outside_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    inside_path = repo_root / "docs" / "stage_2.md"
    inside_path.parent.mkdir()
    inside_path.write_text("# stage 2\n", encoding="utf-8")

    assert _resolve_artifact_path("docs/stage_2.md", repo_root=repo_root) == inside_path.resolve()
    assert _resolve_artifact_path("../outside.md", repo_root=repo_root) is None


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
                "conditions": {},
                "gallery": [
                    {
                        "label": "Empirical metrics",
                        "path": "results/stage_2/figures/example.html",
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
    assert len(payload["empirical_viewer"]["gallery"]) == 1
    assert payload["empirical_viewer"]["gallery"][0]["href"] == "/artifacts/results/stage_2/figures/example.html"
