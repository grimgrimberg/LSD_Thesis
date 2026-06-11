from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

DATASET_DIR = REPO_ROOT / "data" / "ds003059"
PIPELINE_STAGES: tuple[str, ...] = ("stage1", "stage2", "stage3", "stage4")
FOLLOWUP_COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, str(REPO_ROOT / "scripts" / "export_training_dataset.py")),
    ("uv", "run", str(REPO_ROOT / "scripts" / "benchmark_condition_models.py")),
    ("uv", "run", str(REPO_ROOT / "scripts" / "benchmark_multitask_models.py")),
)


def _validate_pipeline_model(model_family: str) -> None:
    from lsd_thesis.models.registry import get_model

    selected_model = get_model(model_family)
    if selected_model.model_name != "bistable":
        raise ValueError("Stage 1-4 pipeline wiring currently supports only the bistable baseline.")


class SurrogatePipeline:
    def __init__(self, model_family: str = "bistable"):
        _validate_pipeline_model(model_family)
        self.model_family = model_family
        self.dataset_dir = DATASET_DIR

        self.targets_dir = REPO_ROOT / "results" / "stage_2"
        self.stage_2_sober_target = self.targets_dir / "empirical_sober_targets.yaml"
        self.stage_2_perturbation_target = self.targets_dir / "empirical_perturbation_targets.yaml"

        self.heldout_dir = self.targets_dir / "heldout_validation"
        self.stage_2_heldout_sober_target = self.heldout_dir / "empirical_sober_targets.yaml"
        self.stage_2_heldout_perturbation_target = self.heldout_dir / "empirical_perturbation_targets.yaml"

        self.stages = PIPELINE_STAGES

    def run_stage(self, stage: str, subject_split_path: str | Path | None = None,
                  stage2_output_dir: str | Path | None = None,
                  stage2_runs: tuple[str, ...] | None = None,
                  include_music: bool = False) -> None:
        print(f"[pipeline] starting {stage}", flush=True)

        if stage == "stage1":
            self._run_stage1()
        elif stage == "stage2":
            self._run_stage2(stage2_output_dir, subject_split_path, stage2_runs, include_music)
        elif stage == "stage3":
            self._run_stage3(subject_split_path)
        elif stage == "stage4":
            self._run_stage4(subject_split_path)
        else:
            raise ValueError(f"Unknown stage: {stage}")

        print(f"[pipeline] finished {stage}", flush=True)

    def _run_stage1(self):
        from lsd_thesis.reporting import generate_stage_1_outputs
        generate_stage_1_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            perturbed_path=REPO_ROOT / "configs" / "regimes" / "perturbed.yaml",
            output_dir=REPO_ROOT / "results" / "stage_1",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_1.md",
        )

    def _run_stage2(self, output_dir, subject_split_path, runs, include_music):
        from lsd_thesis.fit import generate_stage_2_outputs
        resolved_output = REPO_ROOT / "results" / "stage_2" if output_dir is None else Path(output_dir)
        legacy_output = (REPO_ROOT / "results" / "stage_2").resolve()

        if include_music and resolved_output.resolve() == legacy_output:
            raise ValueError("run-02 music extraction must use an explicit non-legacy --stage2-output-dir.")

        report_path = (REPO_ROOT / "docs" / "stage_reports" / "stage_2.md"
                       if resolved_output.resolve() == legacy_output
                       else resolved_output / "stage_2_report.md")

        generate_stage_2_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            target_path=REPO_ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
            output_dir=resolved_output,
            report_path=report_path,
            iterations=64,
            seed=11,
            dataset_dir=self.dataset_dir,
            subject_split_path=subject_split_path,
            runs=runs,
            include_music=include_music,
        )

    def _run_stage3(self, subject_split_path):
        from lsd_thesis.perturbation import generate_stage_3_outputs
        approved_split = self._subject_split_is_approved(subject_split_path)

        if self._stage_3_needs_stage_2(subject_split_path):
            print("[pipeline] stage3 needs stage2 empirical targets; running stage2 first", flush=True)
            self.run_stage("stage2", subject_split_path=subject_split_path)

        generate_stage_3_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            sober_target_path=self.stage_2_sober_target,
            perturbation_target_path=self.stage_2_perturbation_target,
            output_dir=REPO_ROOT / "results" / "stage_3",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_3.md",
            fit_iterations=64,
            strengths=(0.1, 0.25, 0.5, 0.75),
            seed=11,
            subject_split_path=subject_split_path,
            heldout_sober_target_path=self.stage_2_heldout_sober_target if approved_split else None,
            heldout_perturbation_target_path=self.stage_2_heldout_perturbation_target if approved_split else None,
        )

    def _run_stage4(self, subject_split_path):
        from lsd_thesis.ablation import generate_stage_4_outputs
        if not self.stage_2_sober_target.exists() or not self.stage_2_perturbation_target.exists():
            print("[pipeline] stage4 needs stage2 empirical targets; running stage2 first", flush=True)
            self.run_stage("stage2", subject_split_path=subject_split_path)

        generate_stage_4_outputs(
            graph_path=REPO_ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=REPO_ROOT / "configs" / "regimes" / "baseline.yaml",
            sober_target_path=self.stage_2_sober_target,
            perturbation_target_path=self.stage_2_perturbation_target,
            output_dir=REPO_ROOT / "results" / "stage_4",
            report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_4.md",
            fit_iterations=64,
            seed=11,
        )

    def _subject_split_is_approved(self, subject_split_path: str | Path | None) -> bool:
        if subject_split_path is None:
            return False
        from lsd_thesis.subject_split import load_subject_split_file
        return load_subject_split_file(subject_split_path).is_approved

    def _stage_3_needs_stage_2(self, subject_split_path: str | Path | None) -> bool:
        if not self.stage_2_sober_target.exists() or not self.stage_2_perturbation_target.exists():
            return True
        if self._subject_split_is_approved(subject_split_path):
            return (not self.stage_2_heldout_sober_target.exists() or
                    not self.stage_2_heldout_perturbation_target.exists())
        return False

class DashboardRunner:
    @staticmethod
    def launch() -> subprocess.Popen[bytes]:
        dashboard_script = REPO_ROOT / "scripts" / "run_dashboard.py"
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        return subprocess.Popen(
            [sys.executable, str(dashboard_script)],
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

def prepare_parcellation_outputs(stage_2_dir: str | Path, parcellation_id: str, dry_run: bool) -> Path:
    from lsd_thesis.data.parcellations import prepare_parcellation_outputs as _prepare

    return _prepare(stage_2_dir=stage_2_dir, parcellation_id=parcellation_id, dry_run=dry_run)


def extract_parcellation_outputs(
    dataset_dir: str | Path,
    stage_2_dir: str | Path,
    parcellation_id: str,
    runs: tuple[str, ...] | None,
    include_music: bool,
) -> dict[str, object]:
    from lsd_thesis.data.parcellations import extract_schaefer_empirical_viewer

    return extract_schaefer_empirical_viewer(
        dataset_dir=dataset_dir,
        stage_2_dir=stage_2_dir,
        parcellation_id=parcellation_id,
        runs=runs,
        include_music=include_music,
    )


def generate_stage_2b_target_validation(parcellation_id: str) -> dict[str, object]:
    from lsd_thesis.target_validation import generate_stage_2b_from_stage2

    return generate_stage_2b_from_stage2(
        stage_2_dir=REPO_ROOT / "results" / "stage_2",
        output_dir=REPO_ROOT / "results" / "stage_2b",
        report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_2b.md",
        parcellation_id=parcellation_id,
    )


def generate_stage_5_literature_fit(quick: bool) -> dict[str, object]:
    from lsd_thesis.fitting_literature import run_stage_5_literature_fit

    seeds = (11,) if quick else (11, 17, 23)
    config_overrides = {"n_steps": 80, "burn_in": 10, "emit_bold": False} if quick else None
    return run_stage_5_literature_fit(
        target_summary_path=REPO_ROOT / "results" / "stage_2b" / "target_reliability_summary.json",
        output_dir=REPO_ROOT / "results" / "stage_5",
        report_path=REPO_ROOT / "docs" / "stage_reports" / "stage_5.md",
        seeds=seeds,
        model_config_overrides=config_overrides,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the surrogate-model pipeline via OOP interface.")
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
            "generate-empirical-targets",
            "stage-2b-target-validation",
            "validate-subject-split",
            "run-stage-5",
            "run-rgg-fit",
            "run-literature-fit",
        ],
        help="Pipeline stage to execute.",
    )
    parser.add_argument("--model", default="bistable")
    parser.add_argument(
        "--parcellation",
        default="harvard_oxford_8",
        choices=[
            "harvard_oxford_8",
            "schaefer_100_yeo_7",
            "schaefer_200_yeo_7",
            "schaefer_100_yeo_17",
            "schaefer_200_yeo_17",
        ],
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--subject-split", default=None)
    parser.add_argument("--include-music", action="store_true")
    parser.add_argument("--runs", nargs="+", default=None, choices=["run-01", "run-02", "run-03"])
    parser.add_argument("--stage2-output-dir", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "validate-subject-split":
        if not args.subject_split:
            raise SystemExit("--subject-split is required for validate-subject-split.")
        from lsd_thesis.subject_split import format_subject_split_summary, load_subject_split_file

        split = load_subject_split_file(args.subject_split)
        print(format_subject_split_summary(split, held_out_validation_completed=False), flush=True)
        return

    if args.command == "generate-empirical-targets":
        stage2_output_dir = REPO_ROOT / "results" / "stage_2" if args.stage2_output_dir is None else Path(args.stage2_output_dir)
        output_dir = prepare_parcellation_outputs(
            stage_2_dir=stage2_output_dir,
            parcellation_id=args.parcellation,
            dry_run=args.dry_run,
        )
        if not args.dry_run and args.parcellation.startswith("schaefer_"):
            summary = extract_parcellation_outputs(
                dataset_dir=DATASET_DIR,
                stage_2_dir=stage2_output_dir,
                parcellation_id=args.parcellation,
                runs=tuple(args.runs) if args.runs is not None else None,
                include_music=args.include_music,
            )
            print(
                "[pipeline] parcellation extraction complete: "
                f"{summary['subject_count']} subjects, top layer={summary.get('ranking_top_layer')}",
                flush=True,
            )
        print(f"[pipeline] parcellation metadata written to {output_dir}", flush=True)
        return

    if args.command == "stage-2b-target-validation":
        summary = generate_stage_2b_target_validation(args.parcellation)
        print(
            "[pipeline] stage2b target validation complete: "
            f"{summary['metric_count']} metrics, {summary['paired_subject_count']} paired subjects",
            flush=True,
        )
        return

    if args.command in {"run-stage-5", "run-rgg-fit", "run-literature-fit"}:
        if not (REPO_ROOT / "results" / "stage_2b" / "target_reliability_summary.json").exists():
            print("[pipeline] stage5 needs Stage 2b targets; running stage-2b-target-validation first", flush=True)
            generate_stage_2b_target_validation(args.parcellation)
        summary = generate_stage_5_literature_fit(quick=args.quick)
        print(
            "[pipeline] stage5 literature fit complete: "
            f"{summary['candidate_count']} candidates, best={summary['best_candidate']['label']}",
            flush=True,
        )
        return

    pipeline = SurrogatePipeline(model_family=args.model)
    stages, serve = resolve_command(args.command)
    if args.include_music and args.command != "stage2":
        raise SystemExit("--include-music is only supported for the stage2 command.")

    for stage in stages:
        pipeline.run_stage(
            stage,
            subject_split_path=args.subject_split,
            stage2_output_dir=args.stage2_output_dir,
            stage2_runs=tuple(args.runs) if args.runs else None,
            include_music=args.include_music
        )

    run_followup_commands(args.command)

    if serve:
        process = DashboardRunner.launch()
        print(f"[pipeline] dashboard started on http://127.0.0.1:8000/ (pid={process.pid})", flush=True)

if __name__ == "__main__":
    main()
