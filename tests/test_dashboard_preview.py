from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "preview_dashboard.py"


def _load_preview_module():
    spec = importlib.util.spec_from_file_location("preview_dashboard", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_preview_report_lists_dashboard_command_routes_and_data_state() -> None:
    module = _load_preview_module()

    report = module.build_preview_report(ROOT, host="127.0.0.1", port=8765)

    assert report.local_url == "http://127.0.0.1:8765/"
    assert report.launch_command == (
        "uv",
        "run",
        "uvicorn",
        "lsd_thesis.web.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8765",
    )
    assert "/" in report.routes
    assert "/api/dashboard-data" in report.routes
    assert "/artifacts/{artifact_path:path}" in report.routes
    assert "configs/graphs/macro_modules.yaml" in report.required_paths
    assert "results/stage_2/stage_2_summary.json" in report.optional_data_paths
    assert report.held_out_validation_status in {
        "not configured",
        "configured but not completed",
        "candidate split prepared but not approved or completed",
        "approved split configured but not completed",
        "completed",
        "completed CV5 internal validation (5/5 folds; not external validation)",
    }


def test_preview_dashboard_check_only_prints_viewing_contract(monkeypatch, capsys) -> None:
    module = _load_preview_module()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "preview_dashboard.py",
            "--check-only",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
    )

    module.main()

    output = capsys.readouterr().out
    assert "uv run uvicorn lsd_thesis.web.app:app --host 127.0.0.1 --port 8765" in output
    assert "http://127.0.0.1:8765/" in output
    assert "/api/dashboard-data" in output
    assert "Subject-disjoint held-out validation:" in output
    assert "Held-out empirical validation is not implied by this preview check." in output
