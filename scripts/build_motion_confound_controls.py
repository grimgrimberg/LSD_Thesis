from __future__ import annotations

from pathlib import Path

from lsd_thesis.confound_controls import REPO_ROOT, write_motion_confound_control_status


def main() -> None:
    status = write_motion_confound_control_status(REPO_ROOT)
    print(f"Wrote {Path(status['source_path']).as_posix()}")
    print(f"Wrote {Path(status['report_path']).as_posix()}")
    print(f"Wrote {Path(status['association_csv_path']).as_posix()}")


if __name__ == "__main__":
    main()
