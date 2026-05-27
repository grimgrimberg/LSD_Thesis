from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _python_command(script: str, *args: str) -> tuple[str, ...]:
    return (sys.executable, str(REPO_ROOT / "scripts" / script), *args)


def build_live_commands(*, with_legacy_pipeline: bool, skip_preflight: bool) -> tuple[tuple[str, ...], ...]:
    commands: list[tuple[str, ...]] = []
    if with_legacy_pipeline:
        commands.append(_python_command("run_pipeline.py", "run-everything"))
    commands.append(_python_command("run_setting_seed_pass2b0.py"))
    if not skip_preflight:
        commands.append(_python_command("preview_dashboard.py", "--check-only", "--strict"))
    return tuple(commands)


def _run_step(label: str, command: tuple[str, ...]) -> None:
    print(f"[live] {label}: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=str(REPO_ROOT), check=True)


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) != 0


def _choose_port(host: str, requested_port: int) -> int:
    for port in range(requested_port, requested_port + 20):
        if _port_is_available(host, port):
            return port
    raise RuntimeError(f"No available local dashboard port found from {requested_port} to {requested_port + 19}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build current project artifacts and launch the live dashboard from one safe command.",
    )
    parser.add_argument("--with-legacy-pipeline", action="store_true", help="Run the existing full legacy pipeline before setting-seed artifacts.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip dashboard preflight checks before serving.")
    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host.")
    parser.add_argument(
        "--port",
        type=int,
        default=8020,
        help="Preferred dashboard port. Defaults to 8020 to avoid common local port-8000 conflicts.",
    )
    parser.add_argument("--open-browser", action="store_true", help="Open the dashboard URL in the system browser.")
    args = parser.parse_args()

    commands = build_live_commands(
        with_legacy_pipeline=bool(args.with_legacy_pipeline),
        skip_preflight=bool(args.skip_preflight),
    )
    for index, command in enumerate(commands, start=1):
        _run_step(f"step {index}/{len(commands)}", command)

    port = _choose_port(str(args.host), int(args.port))
    dashboard_url = f"http://{args.host}:{port}/"
    microsite_url = f"{dashboard_url}artifacts/output/doc/set_setting_seed_microsite.html"
    print("", flush=True)
    print("[live] dashboard ready", flush=True)
    print(f"[live] main dashboard: {dashboard_url}", flush=True)
    print(f"[live] Set / Setting / Seed microsite: {microsite_url}", flush=True)
    print("[live] stop with Ctrl+C", flush=True)
    if args.open_browser:
        webbrowser.open(dashboard_url)

    from lsd_thesis.web.app import app

    uvicorn.run(app, host=str(args.host), port=port)


if __name__ == "__main__":
    main()
