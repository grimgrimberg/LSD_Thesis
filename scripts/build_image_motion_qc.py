from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.image_motion_qc import DEFAULT_STRIDE, REPO_ROOT, write_image_motion_qc_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Build raw-BOLD image-derived motion/QC control artifacts.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--stride", type=int, default=DEFAULT_STRIDE, help="Spatial downsampling stride for raw BOLD QC summaries.")
    parser.add_argument("--force", action="store_true", help="Recompute even when a ready artifact already exists.")
    args = parser.parse_args()

    status = write_image_motion_qc_status(args.repo_root, args.output_dir, stride=args.stride, force=args.force)
    print(f"Wrote {Path(status['source_path']).as_posix()}")
    print(f"Wrote {Path(status['report_path']).as_posix()}")
    print(f"Wrote {Path(status['association_csv_path']).as_posix()}")
    print(f"status={status['analysis_status']} ready={status['image_motion_qc_ready']}")


if __name__ == "__main__":
    main()
