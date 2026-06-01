import json
from pathlib import Path

import pandas as pd

from lsd_thesis.confound_controls import build_motion_confound_control_status, write_motion_confound_control_status
from lsd_thesis.setting_seed.motion import write_motion_outputs


def test_motion_confound_control_fails_closed_without_motion_summary(tmp_path: Path) -> None:
    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "unavailable_not_found"
    assert status["motion_confound_control_ready"] is False
    assert status["claim_status"] == "not_proven_motion_confound_control_missing"
    assert status["input_contract"]["minimum_overlap"] == 4
    assert status["next_action"]


def test_motion_confound_control_includes_negative_source_availability(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "confound_controls"
    output_dir.mkdir(parents=True)
    (output_dir / "ds003059_motion_source_availability.json").write_text(
        json.dumps(
            {
                "analysis_status": "no_authorized_subject_level_motion_confounds_found",
                "motion_source_availability_ready": True,
                "source_confounds_available": False,
                "local_search": {"motion_file_count": 0},
                "openneuro_raw_snapshot": {"confound_like_file_count": 0},
                "public_derivative_repositories": {"available_count": 0},
                "conclusion": "No checked source exposes subject-level motion confounds.",
                "next_action": "Run fMRIPrep or supply authorized confounds.",
            }
        ),
        encoding="utf-8",
    )

    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "blocked_absent_authorized_subject_level_motion_confounds"
    assert status["source_availability"]["source_confounds_available"] is False
    assert "No checked source" in status["blocker"]


def test_motion_confound_control_computes_subject_run_associations(tmp_path: Path) -> None:
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    views_dir = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    motion_dir.mkdir(parents=True)
    views_dir.mkdir(parents=True)
    summaries = []
    for index in range(6):
        subject = f"sub-{index + 1:03d}"
        run = "run-01"
        summaries.append(
            {
                "subject": subject,
                "session": "ses-PLCB",
                "run": run,
                "framewise_displacement_mean": 0.05,
                "framewise_displacement_max": 0.10,
                "std_dvars_mean": 0.20,
                "motion_outlier_fraction": 0.10,
            }
        )
        summaries.append(
            {
                "subject": subject,
                "session": "ses-LSD",
                "run": run,
                "framewise_displacement_mean": 0.05 + index * 0.02,
                "framewise_displacement_max": 0.10 + index * 0.03,
                "std_dvars_mean": 0.20 + index * 0.01,
                "motion_outlier_fraction": 0.10 + index * 0.015,
            }
        )
        (views_dir / f"{subject}_{run}.json").write_text(
            json.dumps(
                {
                    "subject": subject,
                    "run": run,
                    "delta_metrics": {
                        "cross_network_communication": 0.3 - index * 0.01,
                        "within_network_stability": 0.1 + index * 0.04,
                    },
                }
            ),
            encoding="utf-8",
        )
    (motion_dir / "motion_summary.json").write_text(
        json.dumps(
            {
                "status": "available_parsed",
                "motion_analysis_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 6,
                "minimum_paired_subject_run_count": 4,
                "motion_files_present": True,
                "summaries": summaries,
            }
        ),
        encoding="utf-8",
    )

    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "implemented_dedicated_motion_confound_control_result"
    assert status["motion_confound_control_ready"] is True
    assert status["merged_subject_run_count"] == 6
    assert status["motion_pairing_ready"] is True
    assert status["paired_subject_run_count"] == 6
    assert status["strict_fmriprep_motion_control_ready"] is True
    assert status["missing_motion_feature_families"] == []
    assert status["input_contract"]["required_motion_features"]
    assert status["association_rows"]
    assert any(row["motion_feature"] == "fd_mean_delta_lsd_minus_placebo" for row in status["association_rows"])


def test_motion_confound_control_fails_closed_without_all_motion_feature_families(tmp_path: Path) -> None:
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    confound_dir = tmp_path / "results" / "confound_controls"
    views_dir = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    motion_dir.mkdir(parents=True)
    confound_dir.mkdir(parents=True)
    views_dir.mkdir(parents=True)
    summaries = []
    for index in range(6):
        subject = f"sub-{index + 1:03d}"
        run = "run-01"
        summaries.append(
            {
                "subject": subject,
                "session": "ses-PLCB",
                "run": run,
                "mean_fd": 0.05,
                "mean_dvars": 0.20,
            }
        )
        summaries.append(
            {
                "subject": subject,
                "session": "ses-LSD",
                "run": run,
                "mean_fd": 0.05 + index * 0.02,
                "mean_dvars": 0.20 + index * 0.01,
            }
        )
        (views_dir / f"{subject}_{run}.json").write_text(
            json.dumps(
                {
                    "subject": subject,
                    "run": run,
                    "delta_metrics": {"transition_entropy_delta": index * 0.05},
                }
            ),
            encoding="utf-8",
        )
    (motion_dir / "motion_summary.json").write_text(
        json.dumps(
            {
                "status": "available_parsed",
                "motion_analysis_ready": True,
                "motion_pairing_ready": True,
                "paired_subject_run_count": 6,
                "minimum_paired_subject_run_count": 4,
                "motion_files_present": True,
                "summaries": summaries,
            }
        ),
        encoding="utf-8",
    )
    (confound_dir / "ds003059_motion_source_availability.json").write_text(
        json.dumps(
            {
                "analysis_status": "no_authorized_subject_level_motion_confounds_found",
                "motion_source_availability_ready": True,
                "source_confounds_available": False,
                "conclusion": "No checked public source exposes subject-level motion confounds.",
            }
        ),
        encoding="utf-8",
    )

    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "blocked_incomplete_fd_dvars_censoring_family_coverage"
    assert status["motion_confound_control_ready"] is False
    assert status["strict_fmriprep_motion_control_ready"] is False
    assert status["motion_feature_family_coverage"] == {
        "fd": True,
        "dvars": True,
        "censoring": False,
    }
    assert status["missing_motion_feature_families"] == ["censoring"]
    assert status["association_rows"]


def test_motion_confound_control_uses_parsed_fmriprep_scrub_and_fd_spike_features(tmp_path: Path) -> None:
    confounds_root = tmp_path / "author_confounds"
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    views_dir = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    views_dir.mkdir(parents=True)
    for index in range(6):
        subject = f"sub-{index + 1:03d}"
        run = "run-01"
        for condition, dvars_offset, outlier_count in (
            ("ses-PLCB", 0.0, 1),
            ("ses-LSD", index * 0.04, 1 + min(index, 3)),
        ):
            path = confounds_root / f"author_table_{index + 1}_{condition}_desc-confounds_timeseries.tsv"
            path.parent.mkdir(parents=True, exist_ok=True)
            outlier_columns = {
                f"motion_outlier{column_index:02d}": [1 if row_index == column_index else 0 for row_index in range(4)]
                for column_index in range(outlier_count)
            }
            fd_values = (
                [0.0, 0.1, 0.2, 0.3]
                if condition == "ses-PLCB"
                else [0.0, 0.2 + index * 0.08, 0.45 + index * 0.08, 0.65 + index * 0.08]
            )
            pd.DataFrame(
                {
                    "participant_id": [str(index + 1)] * 4,
                    "condition": [condition.replace("ses-", "")] * 4,
                    "run": ["1"] * 4,
                    "framewise_displacement": fd_values,
                    "std_dvars": [1.0, 1.2 + dvars_offset, 1.5 + dvars_offset, 2.0 + dvars_offset],
                    **outlier_columns,
                }
            ).to_csv(path, sep="\t", index=False)
        (views_dir / f"{subject}_{run}.json").write_text(
            json.dumps(
                {
                    "subject": subject,
                    "run": run,
                    "delta_metrics": {
                        "transition_entropy_delta": index * 0.07,
                        "integration_delta": 0.5 - index * 0.03,
                    },
                }
            ),
            encoding="utf-8",
        )

    write_motion_outputs(output_dir=motion_dir, repo_root=tmp_path, roots=(confounds_root,))
    status = build_motion_confound_control_status(tmp_path)

    features = {row["motion_feature"] for row in status["association_rows"]}
    assert status["analysis_status"] == "implemented_dedicated_motion_confound_control_result"
    assert status["strict_fmriprep_motion_control_ready"] is True
    assert "fd_spike_fraction_delta_lsd_minus_placebo" in features
    assert "motion_outlier_fraction_delta_lsd_minus_placebo" in features


def test_motion_confound_control_rejects_unpaired_observed_motion_features(tmp_path: Path) -> None:
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    views_dir = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    motion_dir.mkdir(parents=True)
    views_dir.mkdir(parents=True)
    summaries = []
    for index in range(6):
        subject = f"sub-{index + 1:03d}"
        run = "run-01"
        summaries.append(
            {
                "subject": subject,
                "session": "unknown",
                "run": run,
                "mean_fd": 0.05 + index * 0.02,
                "mean_dvars": 0.20 + index * 0.01,
            }
        )
        (views_dir / f"{subject}_{run}.json").write_text(
            json.dumps(
                {
                    "subject": subject,
                    "run": run,
                    "delta_metrics": {"within_network_stability": 0.1 + index * 0.04},
                }
            ),
            encoding="utf-8",
        )
    (motion_dir / "motion_summary.json").write_text(
        json.dumps(
            {
                "status": "available_parsed",
                "motion_analysis_ready": True,
                "motion_pairing_ready": False,
                "paired_subject_run_count": 0,
                "minimum_paired_subject_run_count": 4,
                "motion_files_present": True,
                "summaries": summaries,
            }
        ),
        encoding="utf-8",
    )

    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "blocked_insufficient_paired_motion_coverage"
    assert status["motion_confound_control_ready"] is False
    assert status["paired_subject_run_count"] == 0


def test_write_motion_confound_control_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_motion_confound_control_status(tmp_path)

    assert status["source_path"] == "results/confound_controls/motion_confound_control_status.json"
    assert (tmp_path / status["source_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()
    assert (tmp_path / status["association_csv_path"]).exists()
