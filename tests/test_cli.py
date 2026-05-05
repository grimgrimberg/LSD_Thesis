import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_pipeline", ROOT / "scripts" / "run_pipeline.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
resolve_command = MODULE.resolve_command
resolve_followup_commands = MODULE.resolve_followup_commands


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
        ("uv", "run", "python", str(MODULE.REPO_ROOT / "scripts" / "export_training_dataset.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_condition_models.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_multitask_models.py")),
    )


def test_resolve_followup_commands_for_run_everything_serve() -> None:
    commands = resolve_followup_commands("run-everything-serve")

    assert commands == (
        ("uv", "run", "python", str(MODULE.REPO_ROOT / "scripts" / "export_training_dataset.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_condition_models.py")),
        ("uv", "run", str(MODULE.REPO_ROOT / "scripts" / "benchmark_multitask_models.py")),
    )


def test_main_runs_followup_commands_for_run_everything(monkeypatch) -> None:
    events: list[tuple[str, str]] = []

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "run-everything"])
    monkeypatch.setattr(MODULE, "run_stage", lambda stage: events.append(("stage", stage)))
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
    monkeypatch.setattr(MODULE, "run_stage", lambda stage: events.append(("stage", stage)))
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
