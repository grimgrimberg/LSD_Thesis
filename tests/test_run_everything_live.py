import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_everything_live", ROOT / "scripts" / "run_everything_live.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_live_commands_defaults_to_setting_seed_and_preflight() -> None:
    commands = MODULE.build_live_commands(with_legacy_pipeline=False, skip_preflight=False)

    assert commands == (
        (sys.executable, str(ROOT / "scripts" / "run_setting_seed_pass2b0.py")),
        (sys.executable, str(ROOT / "scripts" / "preview_dashboard.py"), "--check-only", "--strict"),
    )


def test_build_live_commands_can_include_legacy_pipeline() -> None:
    commands = MODULE.build_live_commands(with_legacy_pipeline=True, skip_preflight=True)

    assert commands == (
        (sys.executable, str(ROOT / "scripts" / "run_pipeline.py"), "run-everything"),
        (sys.executable, str(ROOT / "scripts" / "run_setting_seed_pass2b0.py")),
    )
