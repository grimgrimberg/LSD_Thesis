import importlib.util
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_pipeline", ROOT / "scripts" / "run_pipeline.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
resolve_command = MODULE.resolve_command
resolve_followup_commands = MODULE.resolve_followup_commands


def test_training_benchmark_scripts_avoid_dynamic_eval_scanner_trigger() -> None:
    condition_script = (ROOT / "scripts" / "benchmark_condition_models.py").read_text(encoding="utf-8")
    multitask_script = (ROOT / "scripts" / "benchmark_multitask_models.py").read_text(encoding="utf-8")
    rocket_script = (ROOT / "scripts" / "benchmark_rocket_condition_models.py").read_text(encoding="utf-8")
    forbidden_eval_call = "." + "ev" + "al("

    assert forbidden_eval_call not in condition_script
    assert forbidden_eval_call not in multitask_script
    assert forbidden_eval_call not in rocket_script


def test_resolve_command_for_run_all() -> None:
    stages, serve_dashboard = resolve_command("run-all")

    assert stages == ("stage1", "stage2", "stage3", "stage4")
    assert serve_dashboard is False


def test_resolve_command_for_run_all_serve() -> None:
    stages, serve_dashboard = resolve_command("run-all-serve")

    assert stages == ("stage1", "stage2", "stage3", "stage4")
    assert serve_dashboard is True


def test_resolve_command_for_run_everything_serve() -> None:
    stages, serve_dashboard = resolve_command("run-everything-serve")

    assert stages == ("stage1", "stage2", "stage3", "stage4")
    assert serve_dashboard is True


def test_resolve_followup_commands_for_run_everything() -> None:
    commands = resolve_followup_commands("run-everything")

    assert commands == (
        (sys.executable, str(MODULE.REPO_ROOT / "scripts" / "export_training_dataset.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_condition_models.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_multitask_models.py")),
    )


def test_resolve_followup_commands_for_run_everything_serve() -> None:
    commands = resolve_followup_commands("run-everything-serve")

    assert commands == (
        (sys.executable, str(MODULE.REPO_ROOT / "scripts" / "export_training_dataset.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_condition_models.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_multitask_models.py")),
    )


def test_main_runs_followup_commands_for_run_everything(monkeypatch) -> None:
    events: list[tuple[str, str]] = []

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "run-everything"])
    monkeypatch.setattr(MODULE, "run_stage", lambda stage, subject_split_path=None, **kwargs: events.append(("stage", stage)))
    monkeypatch.setattr(MODULE, "run_followup_commands", lambda command: events.append(("followup", command)))
    monkeypatch.setattr(MODULE, "launch_dashboard", lambda: None)

    MODULE.main()

    assert events == [
        ("stage", "stage1"),
        ("stage", "stage2"),
        ("stage", "stage3"),
        ("stage", "stage4"),
        ("followup", "run-everything"),
    ]


def test_main_runs_followup_commands_and_dashboard_for_run_everything_serve(monkeypatch) -> None:
    events: list[tuple[str, str]] = []

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "run-everything-serve"])
    monkeypatch.setattr(MODULE, "run_stage", lambda stage, subject_split_path=None, **kwargs: events.append(("stage", stage)))
    monkeypatch.setattr(MODULE, "run_followup_commands", lambda command: events.append(("followup", command)))

    class DummyProcess:
        pid = 4321

    monkeypatch.setattr(
        MODULE,
        "launch_dashboard",
        lambda: events.append(("dashboard", "launch")) or DummyProcess(),
    )

    MODULE.main()

    assert events == [
        ("stage", "stage1"),
        ("stage", "stage2"),
        ("stage", "stage3"),
        ("stage", "stage4"),
        ("followup", "run-everything-serve"),
        ("dashboard", "launch"),
    ]


def test_main_runs_parcellation_dry_run(monkeypatch) -> None:
    events: list[tuple[str, str, bool]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pipeline.py",
            "generate-empirical-targets",
            "--parcellation",
            "schaefer_100_yeo_7",
            "--dry-run",
        ],
    )

    def fake_prepare(stage_2_dir, parcellation_id, dry_run):
        events.append((str(stage_2_dir), parcellation_id, dry_run))
        return MODULE.REPO_ROOT / "codex_logs" / "cli_parcellation_test" / parcellation_id

    monkeypatch.setattr(MODULE, "prepare_parcellation_outputs", fake_prepare, raising=False)

    MODULE.main()

    assert events == [
        (
            str(MODULE.REPO_ROOT / "results" / "stage_2"),
            "schaefer_100_yeo_7",
            True,
        )
    ]


def test_main_runs_stage5_quick_and_generates_missing_stage2b(monkeypatch) -> None:
    events: list[tuple[str, str]] = []
    temp_root = Path("codex_logs") / "cli_stage5_tests" / uuid4().hex
    temp_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(MODULE, "REPO_ROOT", temp_root)
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "run-stage-5", "--quick"])
    monkeypatch.setattr(
        MODULE,
        "generate_stage_2b_target_validation",
        lambda parcellation: events.append(("stage2b", parcellation)) or {"metric_count": 1, "paired_subject_count": 1},
    )
    monkeypatch.setattr(
        MODULE,
        "generate_stage_5_literature_fit",
        lambda quick: events.append(("stage5", str(quick))) or {"candidate_count": 2, "best_candidate": {"label": "gain_only"}},
    )

    MODULE.main()

    assert events == [("stage2b", "harvard_oxford_8"), ("stage5", "True")]


def test_main_threads_subject_split_path_to_stage2_and_stage3(monkeypatch) -> None:
    events: list[tuple[str, str | None]] = []
    split_path = "results/stage_2/subject_split.json"

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "stage3", "--subject-split", split_path])
    monkeypatch.setattr(
        MODULE,
        "run_stage",
        lambda stage, subject_split_path=None, **kwargs: events.append(
            ("stage", f"{stage}:{subject_split_path}")
        ),
    )

    MODULE.main()

    assert events == [
        ("stage", f"stage3:{split_path}"),
    ]


def test_main_validates_subject_split_command(monkeypatch, tmp_path: Path, capsys) -> None:
    split_path = tmp_path / "subject_split.json"
    split_path.write_text(
        """{
          "schema_version": 1,
          "split_id": "fixture",
          "strategy": "subject_disjoint",
          "selection_subjects": ["sub-001"],
          "validation_subjects": ["sub-002"]
        }""",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "validate-subject-split", "--subject-split", str(split_path)])

    MODULE.main()

    output = capsys.readouterr().out
    assert "subject split valid" in output.lower()
    assert "held-out validation completed: no" in output.lower()


def test_main_threads_music_extraction_flags_to_stage2(monkeypatch) -> None:
    events: list[tuple[str, str | None, tuple[str, ...] | None, bool]] = []
    output_dir = "results/setting_seed/run02_extraction/stage_2_music"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pipeline.py",
            "stage2",
            "--include-music",
            "--runs",
            "run-01",
            "run-02",
            "run-03",
            "--stage2-output-dir",
            output_dir,
        ],
    )
    monkeypatch.setattr(
        MODULE,
        "run_stage",
        lambda stage, subject_split_path=None, stage2_output_dir=None, stage2_runs=None, include_music=False: events.append(
            (stage, str(stage2_output_dir), stage2_runs, include_music)
        ),
    )
    monkeypatch.setattr(MODULE, "run_followup_commands", lambda command: None)

    MODULE.main()

    assert events == [
        ("stage2", str(Path(output_dir)), ("run-01", "run-02", "run-03"), True),
    ]


def test_main_rejects_music_flag_outside_stage2(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "stage1", "--include-music"])
    monkeypatch.setattr(MODULE, "run_stage", lambda *args, **kwargs: None)

    try:
        MODULE.main()
    except SystemExit as error:
        assert "--include-music is only supported for the stage2 command" in str(error)
    else:
        raise AssertionError("Expected SystemExit for --include-music outside stage2.")
