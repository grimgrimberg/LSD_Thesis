import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

class SurrogatePipeline:
    def __init__(self, model_family: str = "bistable"):
        self.model_family = model_family
        self.dataset_dir = REPO_ROOT / "data" / "ds003059"

        self.targets_dir = REPO_ROOT / "results" / "stage_2"
        self.stage_2_sober_target = self.targets_dir / "empirical_sober_targets.yaml"
        self.stage_2_perturbation_target = self.targets_dir / "empirical_perturbation_targets.yaml"

        self.heldout_dir = self.targets_dir / "heldout_validation"
        self.stage_2_heldout_sober_target = self.heldout_dir / "empirical_sober_targets.yaml"
        self.stage_2_heldout_perturbation_target = self.heldout_dir / "empirical_perturbation_targets.yaml"

        self.stages = ("stage1", "stage2", "stage3", "stage4")

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

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the surrogate-model pipeline via OOP interface.")
    parser.add_argument("command", choices=[
        "stage1", "stage2", "stage3", "stage4", "run-all", "run-all-serve"
    ], help="Pipeline stage to execute.")
    parser.add_argument("--model", default="bistable")
    parser.add_argument("--subject-split", default=None)
    parser.add_argument("--include-music", action="store_true")
    parser.add_argument("--runs", nargs="+", default=None, choices=["run-01", "run-02", "run-03"])
    parser.add_argument("--stage2-output-dir", default=None)

    args = parser.parse_args()

    pipeline = SurrogatePipeline(model_family=args.model)
    stages = pipeline.stages if args.command in ("run-all", "run-all-serve") else (args.command,)
    serve = args.command == "run-all-serve"

    for stage in stages:
        pipeline.run_stage(
            stage,
            subject_split_path=args.subject_split,
            stage2_output_dir=args.stage2_output_dir,
            stage2_runs=tuple(args.runs) if args.runs else None,
            include_music=args.include_music
        )

    if serve:
        process = DashboardRunner.launch()
        print(f"[pipeline] dashboard started on http://127.0.0.1:8000/ (pid={process.pid})", flush=True)

if __name__ == "__main__":
    main()
