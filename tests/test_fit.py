import json
from pathlib import Path

import numpy as np
import pytest

from lsd_thesis.data.ds003059 import Ds003059RestManifest, Ds003059RunRecord
from lsd_thesis.data.openneuro import ds003059_subset_spec
from lsd_thesis.data.targets import load_sober_target_set
from lsd_thesis.fit import FitResult, build_fit_seed_plan, fit_sober_regime, generate_stage_2_outputs
from lsd_thesis.graph import load_graph_config
from lsd_thesis.simulator import load_regime_config

ROOT = Path(__file__).resolve().parents[1]


def test_ds003059_subset_spec_targets_rest_runs_only() -> None:
    spec = ds003059_subset_spec(subject="sub-001")

    assert spec.dataset_id == "ds003059"
    assert spec.version == "1.0.0"
    assert any("run-01_bold.nii.gz" in item for item in spec.include_paths)
    assert any("run-03_bold.nii.gz" in item for item in spec.include_paths)
    assert not any("run-02_bold.nii.gz" in item for item in spec.include_paths)


def test_sober_target_config_loads_expected_metric_names() -> None:
    target_set = load_sober_target_set(ROOT / "configs" / "targets" / "sober_summary_targets.yaml")

    assert "within_network_stability" in target_set.metrics
    assert "cross_network_communication" in target_set.metrics
    assert target_set.fc_matrix.shape == (8, 8)


def test_sober_fit_returns_an_improving_candidate() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_sober_target_set(ROOT / "configs" / "targets" / "sober_summary_targets.yaml")

    result = fit_sober_regime(
        graph=graph,
        initial_regime=regime,
        target_set=target_set,
        iterations=6,
        seed=5,
    )

    assert result.best_score <= result.initial_score
    assert "within_network_stability" in result.best_metrics
    assert "cross_network_communication" in result.best_metrics


def test_sober_fit_multi_seed_selection_uses_mean_score_not_lucky_single_seed(monkeypatch) -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_sober_target_set(ROOT / "configs" / "targets" / "sober_summary_targets.yaml")

    def fake_candidate(initial_regime, rng, seed: int, iteration: int = 0):
        candidate = initial_regime.model_copy(deep=True)
        candidate.simulation.seed = seed + iteration
        candidate.global_parameters.within_group_scale = float(iteration)
        return candidate

    score_by_candidate_and_seed = {
        0: {101: 9.0, 102: 9.0, 103: 9.0, 201: 9.0, 202: 9.0},
        1: {101: 0.1, 102: 10.0, 103: 10.0, 201: 10.0, 202: 10.0},
        2: {101: 2.0, 102: 2.0, 103: 2.0, 201: 2.0, 202: 2.0},
    }

    def fake_summarize(_graph, candidate):
        candidate_id = int(candidate.global_parameters.within_group_scale)
        score_proxy = score_by_candidate_and_seed[candidate_id][int(candidate.simulation.seed)]
        return (
            {
                "score_proxy": score_proxy,
                "within_network_stability": float(candidate_id),
                "cross_network_communication": 0.0,
                "thalamic_coupling": 0.0,
                "hierarchical_compression": 0.0,
                "entropy_diversity": 0.0,
                "switching_rate": 0.0,
                "metastability_proxy": 0.0,
                "effective_barrier_proxy": 0.0,
            },
            np.eye(8),
        )

    monkeypatch.setattr("lsd_thesis.fit._candidate_from_initial", fake_candidate)
    monkeypatch.setattr("lsd_thesis.fit.summarize_regime", fake_summarize)
    monkeypatch.setattr(
        "lsd_thesis.fit._score_against_targets",
        lambda metrics, fc_matrix, target_set: float(metrics["score_proxy"]),
    )

    result = fit_sober_regime(
        graph=graph,
        initial_regime=regime,
        target_set=target_set,
        iterations=2,
        seed=11,
        selection_seeds=(101, 102, 103),
        validation_seeds=(201, 202),
    )

    assert result.selected_iteration == 2
    assert result.best_score == 2.0
    assert result.seed_plan["selection_mode"] == "multi_seed_mean"
    assert result.seed_plan["selection_seeds"] == (101, 102, 103)
    assert result.validation_score_mean == 2.0
    assert result.seed_plan["validation_seeds"] == (201, 202)


def test_fit_seed_plan_rejects_selection_validation_seed_overlap() -> None:
    with pytest.raises(ValueError, match="disjoint"):
        build_fit_seed_plan(11, selection_seeds=(1, 2), validation_seeds=(2, 3))


def test_stage_2_summary_uses_empirical_provenance_and_writes_mvp_sidecar(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target_path = tmp_path / "empirical_sober_targets.yaml"
    target_path.write_text(
        "\n".join(
            [
                "dataset_anchor: Test anchor",
                "module_names:",
                "  - visual",
                "  - auditory",
                "metrics:",
                "  within_network_stability:",
                "    target: 0.2",
                "    weight: 1.0",
                "    confidence: moderate",
                "    note: test",
                "  cross_network_communication:",
                "    target: 0.1",
                "    weight: 1.0",
                "    confidence: moderate",
                "    note: test",
                "fc_matrix:",
                "  - [1.0, 0.0]",
                "  - [0.0, 1.0]",
                "notes:",
                "  - test note",
            ]
        ),
        encoding="utf-8",
    )
    perturbation_target_path = tmp_path / "empirical_perturbation_targets.yaml"
    perturbation_target_path.write_text(
        "\n".join(
            [
                "metadata: {source_strategy: test, paired_subject_count: 2, notes: [test]}",
                "target_deltas: {within_network_stability: 0.1}",
                "confidence: {within_network_stability: moderate}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = Ds003059RestManifest(
        subjects=("sub-001", "sub-002"),
        runs=(
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-PLCB",
                run="run-01",
                filename="sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                url="",
                size=1,
            ),
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-LSD",
                run="run-01",
                filename="sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_run-01_bold.nii.gz",
                url="",
                size=1,
            ),
            Ds003059RunRecord(
                subject="sub-002",
                session="ses-PLCB",
                run="run-03",
                filename="sub-002_ses-PLCB_task-rest_run-03_bold.nii.gz",
                relative_path="sub-002/ses-PLCB/func/sub-002_ses-PLCB_task-rest_run-03_bold.nii.gz",
                url="",
                size=1,
            ),
            Ds003059RunRecord(
                subject="sub-002",
                session="ses-LSD",
                run="run-03",
                filename="sub-002_ses-LSD_task-rest_run-03_bold.nii.gz",
                relative_path="sub-002/ses-LSD/func/sub-002_ses-LSD_task-rest_run-03_bold.nii.gz",
                url="",
                size=1,
            ),
        ),
        sidecars=(),
    )
    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    metrics = {
        "within_network_stability": 0.22,
        "cross_network_communication": 0.11,
        "thalamic_coupling": 0.05,
        "hierarchical_compression": 0.12,
        "entropy_diversity": 0.95,
        "switching_rate": 0.2,
        "metastability_proxy": 1.0,
        "effective_barrier_proxy": 3.0,
        "within_group_fc": 0.22,
        "cross_group_fc": 0.11,
        "state_entropy": 0.95,
        "dynamic_fc_change": 1.0,
    }

    monkeypatch.setattr(
        "lsd_thesis.fit.generate_empirical_targets",
        lambda dataset_dir, output_dir, subjects=None, runs=None, include_music=False: {
            "manifest": manifest,
            "run_records": (),
            "sober_target_path": str(target_path),
            "perturbation_target_path": str(perturbation_target_path),
        },
    )
    monkeypatch.setattr(
        "lsd_thesis.fit.fit_sober_regime",
        lambda graph, initial_regime, target_set, iterations=24, seed=0, **kwargs: FitResult(
            initial_score=2.0,
            best_score=0.5,
            selection_score_std=0.05,
            selected_iteration=1,
            best_regime=regime,
            best_metrics=metrics,
            best_metrics_std={"within_network_stability": 0.01},
            best_fc_matrix=np.eye(2),
            history=[{"iteration": 0, "score": 2.0}, {"iteration": 1, "score": 0.5}],
            seed_plan={
                "proposal_seed": seed,
                "selection_seeds": kwargs["selection_seeds"],
                "validation_seeds": kwargs["validation_seeds"],
                "selection_mode": "multi_seed_mean",
                "validation_mode": "disjoint_seed_panel",
            },
            validation_score_mean=0.55,
            validation_score_std=0.03,
            validation_metrics_mean={"within_network_stability": 0.2},
            validation_metrics_std={"within_network_stability": 0.01},
        ),
    )
    monkeypatch.setattr(
        "lsd_thesis.fit.multi_seed_summary",
        lambda graph, best_regime, n_seeds=5, base_seed=0: (
            {"within_network_stability": 0.2},
            {"within_network_stability": 0.01},
        ),
    )
    monkeypatch.setattr("lsd_thesis.fit.build_empirical_run_views_from_records", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        "lsd_thesis.fit.build_empirical_viewer_payloads",
        lambda run_views, modules: {"group_overview": {"gallery": []}},
    )
    monkeypatch.setattr(
        "lsd_thesis.fit.generate_empirical_gallery",
        lambda group_overview, figures_dir: [{"label": "Gallery", "path": str(figures_dir / "gallery.html")}],
    )
    monkeypatch.setattr(
        "lsd_thesis.fit.write_empirical_viewer_cache",
        lambda viewer_payloads, output_dir: {
            "group_overview_path": str(output_dir / "group_overview.json"),
            "subject_index_path": str(output_dir / "subject_index.json"),
            "subject_views_dir": str(output_dir / "subject_views"),
        },
    )
    monkeypatch.setattr(
        "lsd_thesis.fit.get_version_stamp",
        lambda repo_root=None: {
            "timestamp": "2026-04-13T00:00:00+00:00",
            "git": {
                "repo_present": True,
                "branch": "main",
                "head_present": True,
                "commit_hash": "abc123",
                "worktree_status": "clean",
            },
        },
    )
    monkeypatch.setattr(
        "lsd_thesis.fit.build_atlas_mapping_audit",
        lambda *args, **kwargs: {
            "mapping": [],
            "overlaps": [{"atlas": "cortical", "label": 31, "modules": ["visual", "default_mode"]}],
            "module_voxel_counts": {"visual": 10, "auditory": 12},
            "assigned_voxels": 22,
            "unassigned_voxels": 3,
            "notes": ["test"],
        },
    )

    output_dir = tmp_path / "stage_2"
    report_path = tmp_path / "stage_2.md"
    generate_stage_2_outputs(
        graph_path=ROOT / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=ROOT / "configs" / "regimes" / "baseline.yaml",
        target_path=ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
        output_dir=output_dir,
        report_path=report_path,
        dataset_dir=tmp_path / "dataset",
    )

    summary = json.loads((output_dir / "stage_2_summary.json").read_text(encoding="utf-8"))
    assert "empirical_provenance" in summary
    assert "subset_spec" not in summary
    assert "download_command" not in summary
    assert summary["empirical_provenance"]["subject_count"] == 2
    assert summary["empirical_provenance"]["run_count"] == 4
    assert len(summary["empirical_provenance"]["runs"]) == 4
    assert summary["empirical_provenance"]["target_paths"]["sober"] == str(target_path)
    assert summary["empirical_provenance"]["viewer_cache_paths"]["group_overview_path"].endswith("group_overview.json")
    assert summary["fit_seed_plan"]["selection_mode"] == "multi_seed_mean"
    assert summary["multi_seed_summary"]["role"] == "validation_seed_panel"
    assert summary["multi_seed_summary"]["selection_validation_seed_overlap"] is False
    assert summary["empirical_validation_boundary"]["held_out"] is False
    assert "independent validation" in summary["empirical_validation_boundary"]["claim_guardrail"]
    assert summary["atlas_mapping_audit_path"].endswith("atlas_mapping_audit.json")
    atlas_audit = json.loads((output_dir / "atlas_mapping_audit.json").read_text(encoding="utf-8"))
    assert atlas_audit["assigned_voxels"] == 22

    mvp_sidecar = json.loads((output_dir / "ds003059_mvp_subset_plan.json").read_text(encoding="utf-8"))
    assert "subset_spec" in mvp_sidecar
    assert "download_command" in mvp_sidecar

    report_text = report_path.read_text(encoding="utf-8")
    assert "full empirical cohort" in report_text
    assert "convenience bootstrap artifact" in report_text


def test_stage_2_summary_records_subject_disjoint_split_without_claiming_completion(
    tmp_path: Path,
    monkeypatch,
) -> None:
    split_path = tmp_path / "subject_split.json"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "split_id": "fixture_subject_split",
                "strategy": "subject_disjoint",
                "selection_subjects": ["sub-001", "sub-002"],
                "validation_subjects": ["sub-003"],
                "split_seed": 123,
                "created_by": "pytest",
                "created_at": "2026-05-10T00:00:00Z",
                "approval_status": "approved",
                "approved_by": "pytest-reviewer",
                "approved_at": "2026-05-10T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    target_path = tmp_path / "empirical_sober_targets.yaml"
    target_path.write_text(
        "\n".join(
            [
                "dataset_anchor: Selection-only test anchor",
                "module_names:",
                "  - visual",
                "  - auditory",
                "metrics:",
                "  within_network_stability: {target: 0.2, weight: 1.0, confidence: moderate, note: test}",
                "  cross_network_communication: {target: 0.1, weight: 1.0, confidence: moderate, note: test}",
                "fc_matrix:",
                "  - [1.0, 0.0]",
                "  - [0.0, 1.0]",
                "notes:",
                "  - test note",
            ]
        ),
        encoding="utf-8",
    )
    perturbation_target_path = tmp_path / "empirical_perturbation_targets.yaml"
    perturbation_target_path.write_text(
        "metadata: {source_strategy: test, paired_subject_count: 2, notes: [test]}\n"
        "target_deltas: {within_network_stability: 0.1}\n"
        "confidence: {within_network_stability: moderate}\n",
        encoding="utf-8",
    )
    manifest = Ds003059RestManifest(
        subjects=("sub-001", "sub-002"),
        runs=(
            Ds003059RunRecord(
                subject="sub-001",
                session="ses-PLCB",
                run="run-01",
                filename="sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                relative_path="sub-001/ses-PLCB/func/sub-001_ses-PLCB_task-rest_run-01_bold.nii.gz",
                url="",
                size=1,
            ),
        ),
        sidecars=(),
    )
    requested_subjects: list[tuple[str, ...] | None] = []

    def fake_generate_empirical_targets(dataset_dir, output_dir, subjects=None, runs=None, include_music=False):
        requested_subjects.append(subjects)
        resolved_subjects = tuple(subjects or ())
        return {
            "manifest": manifest.model_copy(update={"subjects": resolved_subjects}),
            "run_records": (),
            "sober_target_path": str(target_path),
            "perturbation_target_path": str(perturbation_target_path),
        }

    regime = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    metrics = {
        "within_network_stability": 0.22,
        "cross_network_communication": 0.11,
        "thalamic_coupling": 0.05,
        "hierarchical_compression": 0.12,
        "entropy_diversity": 0.95,
        "switching_rate": 0.2,
        "metastability_proxy": 1.0,
        "effective_barrier_proxy": 3.0,
    }

    monkeypatch.setattr("lsd_thesis.fit.generate_empirical_targets", fake_generate_empirical_targets)
    monkeypatch.setattr(
        "lsd_thesis.fit.fit_sober_regime",
        lambda graph, initial_regime, target_set, iterations=24, seed=0, **kwargs: FitResult(
            initial_score=2.0,
            best_score=0.5,
            selection_score_std=0.05,
            selected_iteration=1,
            best_regime=regime,
            best_metrics={**metrics, "within_group_fc": 0.22, "cross_group_fc": 0.11, "state_entropy": 0.95, "dynamic_fc_change": 1.0},
            best_metrics_std={"within_network_stability": 0.01},
            best_fc_matrix=np.eye(2),
            history=[{"iteration": 0, "score": 2.0}, {"iteration": 1, "score": 0.5}],
            seed_plan={
                "proposal_seed": seed,
                "selection_seeds": kwargs["selection_seeds"],
                "validation_seeds": kwargs["validation_seeds"],
                "selection_mode": "multi_seed_mean",
                "validation_mode": "disjoint_seed_panel",
            },
            validation_score_mean=0.55,
            validation_score_std=0.03,
            validation_metrics_mean={"within_network_stability": 0.2},
            validation_metrics_std={"within_network_stability": 0.01},
        ),
    )
    monkeypatch.setattr("lsd_thesis.fit.build_empirical_run_views_from_records", lambda *args, **kwargs: [])
    monkeypatch.setattr("lsd_thesis.fit.build_empirical_viewer_payloads", lambda run_views, modules: {"group_overview": {"gallery": []}})
    monkeypatch.setattr("lsd_thesis.fit.generate_empirical_gallery", lambda group_overview, figures_dir: [])
    monkeypatch.setattr("lsd_thesis.fit.write_empirical_viewer_cache", lambda viewer_payloads, output_dir: {})
    monkeypatch.setattr(
        "lsd_thesis.fit.build_atlas_mapping_audit",
        lambda *args, **kwargs: {
            "mapping": [],
            "overlaps": [],
            "module_voxel_counts": {},
            "assigned_voxels": 0,
            "unassigned_voxels": 0,
            "notes": ["test"],
        },
    )

    output_dir = tmp_path / "stage_2"
    generate_stage_2_outputs(
        graph_path=ROOT / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=ROOT / "configs" / "regimes" / "baseline.yaml",
        target_path=ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
        output_dir=output_dir,
        report_path=tmp_path / "stage_2.md",
        dataset_dir=tmp_path / "dataset",
        subject_split_path=split_path,
    )

    summary = json.loads((output_dir / "stage_2_summary.json").read_text(encoding="utf-8"))
    boundary = summary["empirical_validation_boundary"]
    assert requested_subjects == [("sub-001", "sub-002"), ("sub-003",)]
    assert boundary["split_file_path"] == str(split_path)
    assert boundary["split_schema_version"] == 1
    assert boundary["split_id"] == "fixture_subject_split"
    assert boundary["approval_status"] == "approved"
    assert boundary["boundary_type"] == "subject_disjoint_approved_configured_not_completed"
    assert boundary["selection_subjects"] == ["sub-001", "sub-002"]
    assert boundary["validation_subjects"] == ["sub-003"]
    assert boundary["held_out_validation_configured"] is True
    assert boundary["held_out_validation_completed"] is False
    assert boundary["held_out"] is False
    assert boundary["selection_subject_count"] == 2
    assert boundary["validation_subject_count"] == 1
    assert boundary["overlap_count"] == 0
    assert "not yet been completed" in boundary["claim_guardrail"]
    assert summary["heldout_validation_target_paths"]["status"] == "prepared_for_stage3_not_completed"
    assert summary["heldout_validation_target_paths"]["subject_count"] == 1
