from __future__ import annotations

from pathlib import Path

from lsd_thesis.published_motion_qc import REPO_ROOT, write_published_motion_qc_status


def main() -> None:
    status = write_published_motion_qc_status(REPO_ROOT)
    print(f"Wrote {Path(status['status_path']).as_posix()}")
    print(f"Wrote {Path(status['report_path']).as_posix()}")


if __name__ == "__main__":
    main()
