from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.data.ds006072 import build_ds006072_func_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a repo-local ds006072 functional-file manifest for psilocybin ingestion planning."
    )
    parser.add_argument("--target-dir", type=Path, default=REPO_ROOT / "data" / "ds006072")
    parser.add_argument("--tag", default=None, help="Optional OpenNeuro snapshot tag. Defaults to latest.")
    args = parser.parse_args()

    manifest = build_ds006072_func_manifest(args.target_dir, tag=args.tag)
    print(
        json.dumps(
            {
                "source_path": manifest["source_path"],
                "csv_path": manifest["csv_path"],
                "subject_count": manifest["subject_count"],
                "rest_bold_nifti_count": manifest["rest_bold_nifti_count"],
                "rest_bold_total_size_bytes": manifest["rest_bold_total_size_bytes"],
                "processed_cifti_count": manifest["processed_cifti_count"],
                "processed_rest_cifti_count": manifest["processed_rest_cifti_count"],
                "processed_cifti_total_size_bytes": manifest["processed_cifti_total_size_bytes"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
