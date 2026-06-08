#!/usr/bin/env python3
"""Verify cloned prior-art repositories.

The verifier reads ``prior_art/repository_sources.json`` and checks the local
clone for each expected repository. It does not modify cloned repositories.

Usage:
    uv run python prior_art/scripts/verify_repos.py
    uv run python prior_art/scripts/verify_repos.py --strict
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PRIOR_ART_ROOT = SCRIPT_DIR.parent
REPOSITORIES_ROOT = PRIOR_ART_ROOT / "repositories"
SOURCE_PATH = PRIOR_ART_ROOT / "repository_sources.json"


@dataclass(frozen=True)
class CheckResult:
    directory: str
    expected_url: str
    present: bool
    is_git: bool
    head: str | None
    branch: str | None
    readme: str | None
    license_file: str | None
    remote: str | None
    warning: str | None = None


def run_git(directory: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else None


def first_matching_file(directory: Path, prefixes: tuple[str, ...]) -> str | None:
    try:
        for child in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_file():
                continue
            name_lower = child.name.lower()
            if any(name_lower.startswith(prefix.lower()) for prefix in prefixes):
                return child.name
    except OSError:
        return None
    return None


def load_sources() -> list[dict[str, str]]:
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Missing repository source list: {SOURCE_PATH}")
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8-sig"))
    return list(payload.get("repositories", []))


def check_repository(source: dict[str, str]) -> CheckResult:
    directory_name = source["directory"]
    expected_url = source["url"]
    directory = REPOSITORIES_ROOT / directory_name

    if not directory.exists():
        return CheckResult(
            directory=directory_name,
            expected_url=expected_url,
            present=False,
            is_git=False,
            head=None,
            branch=None,
            readme=None,
            license_file=None,
            remote=None,
            warning="missing clone",
        )

    is_git = run_git(directory, "rev-parse", "--is-inside-work-tree") == "true"
    head = run_git(directory, "rev-parse", "HEAD") if is_git else None
    branch = run_git(directory, "branch", "--show-current") if is_git else None
    remote = run_git(directory, "remote", "get-url", "origin") if is_git else None
    readme = first_matching_file(directory, ("readme",))
    license_file = first_matching_file(directory, ("license", "licence", "copying"))

    warning = None
    if not is_git:
        warning = "not a git repository"
    elif remote and remote.rstrip("/").removesuffix(".git") != expected_url.rstrip("/").removesuffix(".git"):
        warning = "remote URL differs"
    elif not readme:
        warning = "missing README"

    return CheckResult(
        directory=directory_name,
        expected_url=expected_url,
        present=True,
        is_git=is_git,
        head=head,
        branch=branch,
        readme=readme,
        license_file=license_file,
        remote=remote,
        warning=warning,
    )


def print_table(results: list[CheckResult]) -> None:
    name_width = max([len("Repository"), *(len(item.directory) for item in results)])
    header = (
        f"{'Repository':<{name_width}}  Present  Git  Branch       Commit        "
        "README   License  Warning"
    )
    sep = "-" * len(header)

    print()
    print(sep)
    print("Prior-Art Repository Verification")
    print(f"Directory: {REPOSITORIES_ROOT}")
    print(sep)
    print(header)
    print(sep)

    for result in results:
        present = "yes" if result.present else "NO"
        is_git = "yes" if result.is_git else "NO"
        branch = (result.branch or "-")[:12]
        commit = (result.head or "-")[:12]
        readme = "yes" if result.readme else "NO"
        license_file = "yes" if result.license_file else "NO"
        warning = result.warning or "-"
        print(
            f"{result.directory:<{name_width}}  "
            f"{present:<7}  {is_git:<3}  {branch:<12}  {commit:<12}  "
            f"{readme:<7}  {license_file:<7}  {warning}"
        )

    print(sep)
    missing = sum(1 for item in results if not item.present or not item.is_git)
    warn = sum(1 for item in results if item.warning)
    print(f"Total: {len(results)} | Missing/not-git: {missing} | Warnings: {warn}")
    print(sep)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when a repository is missing, not git, or warning is present.",
    )
    args = parser.parse_args()

    sources = load_sources()
    results = [check_repository(source) for source in sources]
    print_table(results)

    if args.strict and any((not item.present or not item.is_git or item.warning) for item in results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
