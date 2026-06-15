from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_pipeline import build_parser

REPO_ROOT = Path(__file__).resolve().parents[1]

SAFE_HELP_SCRIPTS = (
    "scripts/benchmark_rocket_condition_models.py",
    "scripts/build_fmriprep_motion_proof_plan.py",
    "scripts/build_motion_confound_controls.py",
    "scripts/build_reproducible_archive.py",
    "scripts/build_thesis_upgrade_status.py",
    "scripts/check_ds003059_motion_sources.py",
    "scripts/export_dynamic_mechanism_tables.py",
    "scripts/export_thesis_loop_tables.py",
    "scripts/export_training_dataset.py",
    "scripts/run_setting_seed_motion_summary.py",
    "scripts/run_thesis_evidence_loop.py",
)

EXPECTED_PIPELINE_COMMANDS = (
    "stage1",
    "stage2",
    "stage3",
    "stage4",
    "run-all",
    "run-all-serve",
    "run-everything",
    "run-everything-serve",
    "generate-empirical-targets",
    "stage-2b-target-validation",
    "validate-subject-split",
    "run-stage-5",
    "run-rgg-fit",
    "run-literature-fit",
)


def _script_help(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / script), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("script", SAFE_HELP_SCRIPTS)
def test_safe_script_help_commands_return_zero(script: str) -> None:
    result = _script_help(script)
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0, output
    assert "usage:" in output.lower()


def test_preview_dashboard_help_is_safe() -> None:
    result = _script_help("scripts/preview_dashboard.py")
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0, output
    assert "usage:" in output.lower()


def test_run_pipeline_parser_exposes_expected_commands_without_running_pipeline() -> None:
    parser = build_parser()

    for command in EXPECTED_PIPELINE_COMMANDS:
        assert parser.parse_args([command]).command == command
