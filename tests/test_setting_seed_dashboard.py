import json
import uuid
from pathlib import Path

from lsd_thesis.setting_seed.dashboard_payload import build_setting_seed_dashboard_payload, render_dashboard_html


def _fixture_root(name: str) -> Path:
    root = Path("results") / "setting_seed" / "test_fixtures" / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _write_minimal_artifacts(root: Path) -> None:
    data_dir = root / "results" / "setting_seed" / "data_audit"
    reliability_dir = root / "results" / "setting_seed" / "reliability"
    latent_dir = root / "results" / "setting_seed" / "latent"
    control_dir = root / "results" / "setting_seed" / "control"
    for directory in [data_dir, reliability_dir, latent_dir, control_dir]:
        directory.mkdir(parents=True)
    (data_dir / "data_audit.json").write_text(
        json.dumps(
            {
                "schema_version": "setting_seed_data_audit.v1",
                "subjects": ["sub-001"],
                "runs": ["run-01", "run-03"],
                "sessions": ["ses-LSD", "ses-PLCB"],
                "modules": ["visual"],
                "run_02_available": False,
                "run_02_extraction_support_available": True,
                "run_02_files_present": False,
                "run_02_analysis_ready": False,
                "motion_summaries_available": False,
                "motion_summary_support_available": True,
                "motion_files_present": False,
                "motion_analysis_ready": False,
                "music_excluded_subjects": ["sub-003", "sub-012", "sub-015"],
                "analysis_availability": {
                    "music_control": "blocked_missing_run_02",
                    "motion_sensitivity": "unavailable_missing_motion_summaries",
                },
                "next_commands": {
                    "run_02_extraction_after_approval": (
                        "uv run python scripts/run_pipeline.py stage2 --include-music --runs run-01 run-02 run-03 "
                        "--stage2-output-dir results/setting_seed/run02_extraction/stage_2_music"
                    ),
                    "motion_summary": "uv run python scripts/run_setting_seed_motion_summary.py",
                },
                "blockers": ["run-02 module time series are missing; music-control empirical analysis is scaffolded only."],
            }
        ),
        encoding="utf-8",
    )
    (reliability_dir / "reliability_table.json").write_text(
        json.dumps(
            [
                {
                    "metric": "cross_network_communication",
                    "tier": "Tier A",
                    "mean_delta": 0.1,
                    "ci_low": 0.05,
                    "ci_high": 0.15,
                    "sign_consistency": 1.0,
                    "theory_sign_conflict": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    (latent_dir / "trajectory_metrics.csv").write_text(
        "subject,session,run,trajectory_length,trajectory_dispersion,latent_velocity\nsub-001,ses-LSD,run-01,1.0,0.2,0.5\n",
        encoding="utf-8",
    )
    (control_dir / "control_scaffold.json").write_text(
        json.dumps({"status": "blocked_missing_run_02", "claim_guardrail": "No music-control empirical claim is made yet."}),
        encoding="utf-8",
    )


def test_dashboard_payload_surfaces_guardrails_and_missing_music() -> None:
    root = _fixture_root("dashboard_payload")
    _write_minimal_artifacts(root)

    payload = build_setting_seed_dashboard_payload(root)

    assert payload["title"] == "Set, Setting, and Seed"
    assert payload["data_audit"]["run_02_available"] is False
    assert "Not clinical" in payload["guardrail_badges"]
    assert payload["music_control"]["status"] == "blocked_missing_run_02"


def test_render_dashboard_html_contains_required_sections() -> None:
    root = _fixture_root("dashboard_html")
    _write_minimal_artifacts(root)
    payload = build_setting_seed_dashboard_payload(root)

    html = render_dashboard_html(payload)

    assert "Set / Setting / Seed" in html
    assert "Run-02 extraction support" in html
    assert "Data present: false" in html
    assert "Diffusion analogy only" in html
    assert "Previous proxy-ranking artifacts" in html
