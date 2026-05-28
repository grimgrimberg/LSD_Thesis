from __future__ import annotations

from pathlib import Path

from lsd_thesis.neuromaps_spatial_nulls import REPO_ROOT, write_neuromaps_spatial_null_status


def main() -> None:
    status = write_neuromaps_spatial_null_status(REPO_ROOT)
    print(f"Wrote {Path(status['source_path']).as_posix()}")
    print(f"Wrote {Path(status['report_path']).as_posix()}")


if __name__ == "__main__":
    main()
