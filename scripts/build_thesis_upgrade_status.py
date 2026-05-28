from __future__ import annotations

from pathlib import Path

from lsd_thesis.thesis_upgrade import REPO_ROOT, write_thesis_upgrade_status


def main() -> None:
    status = write_thesis_upgrade_status(REPO_ROOT)
    source_path = status.get("source_path", "results/thesis_upgrade/thesis_upgrade_status.json")
    report_path = status.get("report_path", "results/thesis_upgrade/thesis_upgrade_status.md")
    print(f"Wrote {Path(source_path).as_posix()}")
    print(f"Wrote {Path(report_path).as_posix()}")


if __name__ == "__main__":
    main()
