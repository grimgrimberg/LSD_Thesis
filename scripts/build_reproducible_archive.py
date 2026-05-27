from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.reproducible_archive import write_archive_manifest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a reproducible archive manifest for derived thesis artifacts.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "results" / "reproducible_archive")
    args = parser.parse_args()
    manifest = write_archive_manifest(args.repo_root, args.output_dir)
    print(
        json.dumps(
            {
                "manifest_path": manifest["manifest_path"],
                "artifact_csv_path": manifest["artifact_csv_path"],
                "checksum_path": manifest["checksum_path"],
                "artifact_count": manifest["artifact_count"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
