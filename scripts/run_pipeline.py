from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
DATASET_DIR = REPO_ROOT / "data" / "ds003059"
STAGE_2_SOBER_TARGET = REPO_ROOT / "results" / "stage_2" / "empirical_sober_targets.yaml"
STAGE_2_PERTURBATION_TARGET = (
    REPO_ROOT / "results" / "stage_2" / "empirical_perturbation_targets.yaml"
)
PIPELINE_STAGES: tuple[str, ...] = ("stage1", "stage2", "stage3", "stage4")
FOLLOWUP_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("uv", "run", "python", str(REPO_ROOT / "scripts" / "export_training_dataset.py")),
    ("uv", "run", str(REPO_ROOT / "scripts" / "benchmark_condition_models.py")),
    ("uv", "run", str(REPO_ROOT / "scripts" / "benchmark_multitask_models.py")),
)


def resolve_command(command: str) -> tuple[tuple[str, ...], bool]:
    if command in {"run-all", "run-everything"}:
        return PIPELINE_STAGES, False
    if command in {"run-all-serve", "run-everything-serve"}:
        return PIPELINE_STAGES, True
    return (command,), False


def resolve_followup_commands(command: str) -> tuple[tuple[str, ...], ...]:
    if command in {"run-everything", "run-everything-serve"}:
        return FOLLOWUP_COMMANDS
    return ()


def run_followup_commands(command: str) -> None:
    for followup_command in resolve_followup_commands(command):
        print(f"[pipeline] starting {' '.join(followup_command)}", flush=True)
        subprocess.run(followup_command, cwd=str(REPO_ROOT), check=True)
        print(f"[pipeline] finished {' '.join(followup_command)}", flush=True)


def launch_dashboard() -> subprocess.Popen[bytes]:
    dashboard_script = REPO_ROOT / "scripts" / "run_dashboard.py"
    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
    return subprocess.Popen(
        [sys.executable, str(dashboard_script)],
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def run_stage(stage: str) -> None:
    from lsd_thesis.ablation import generate_stage_4_outputs
    from lsd_thesis.fit import generate_stage_2_outputs
    from lsd_thesis.perturbation import generate_stage_3_outputs
    from lsd_thesis.reporting import generate_stage_1_outputs

    print(f"[pipeline] starting {stage}", flush=True)

    if stage == "stage1":
        generate_stage_1_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            perturbed_path=REPO_ROOT / "configs" / "regimes" / "perturbed.yaml",
            output_dir=REPO_ROOT / "results" / "stage_1",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_1.md",
        )
    elif stage == "stage2":
        generate_stage_2_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            target_path=REPO_ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
            output_dir=REPO_ROOT / "results" / "stage_2",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_2.md",
            iterations=64,
            seed=11,
            dataset_dir=DATASET_DIR,
        )
    elif stage == "stage3":
        if not STAGE_2_SOBER_TARGET.exists() or not STAGE_2_PERTURBATION_TARGET.exists():
            print("[pipeline] stage3 needs stage2 empirical targets; running stage2 first", flush=True)
            run_stage("stage2")
        generate_stage_3_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            sober_target_path=STAGE_2_SOBER_TARGET,
            perturbation_target_path=STAGE_2_PERTURBATION_TARGET,
            output_dir=REPO_ROOT / "results" / "stage_3",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_3.md",
            fit_iterations=64,
            strengths=(0.1, 0.25, 0.5, 0.75),
            seed=11,
        )
    elif stage == "stage4":
        if not STAGE_2_SOBER_TARGET.exists() or not STAGE_2_PERTURBATION_TARGET.exists():
            print("[pipeline] stage4 needs stage2 empirical targets; running stage2 first", flush=True)
            run_stage("stage2")
        generate_stage_4_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            sober_target_path=STAGE_2_SOBER_TARGET,
            perturbation_target_path=STAGE_2_PERTURBATION_TARGET,
            output_dir=REPO_ROOT / "results" / "stage_4",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_4.md",
            fit_iterations=64,
            seed=11,
        )
    else:
        raise ValueError(f"Unknown stage: {stage}")

    print(f"[pipeline] finished {stage}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the surrogate-model pipeline.")
    parser.add_argument(
        "command",
        choices=[
            "stage1",
            "stage2",
            "stage3",
            "stage4",
            "run-all",
            "run-all-serve",
            "run-everything",
            "run-everything-serve",
        ],
        help="Pipeline stage to execute.",
    )
    args = parser.parse_args()
    stages, serve_dashboard = resolve_command(args.command)

    for stage in stages:
        run_stage(stage)

    run_followup_commands(args.command)

    if serve_dashboard:
        process = launch_dashboard()
        print(
            f"[pipeline] dashboard started on http://127.0.0.1:8000/ (pid={process.pid})",
            flush=True,
        )
    else:
        print("[pipeline] all requested stages completed", flush=True)
        print(
            "[pipeline] to open the dashboard, run: uv run python scripts/run_dashboard.py",
            flush=True,
        )


if __name__ == "__main__":
    main()
