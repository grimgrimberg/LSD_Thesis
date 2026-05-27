from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.data.ds006072 import download_ds006072_metadata

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the ds006072 metadata/provenance slice into the repo-local data directory."
    )
    parser.add_argument("--target-dir", type=Path, default=REPO_ROOT / "data" / "ds006072")
    parser.add_argument("--tag", default=None, help="Optional OpenNeuro snapshot tag. Defaults to latest.")
    args = parser.parse_args()

    manifest = download_ds006072_metadata(args.target_dir, tag=args.tag)
    print(json.dumps({"source_path": manifest["source_path"], "snapshot_tag": manifest["snapshot_tag"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
