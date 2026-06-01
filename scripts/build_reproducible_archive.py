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
    parser.add_argument(
        "--release-url",
        help="Citable GitHub release URL for this exact thesis snapshot, e.g. https://github.com/owner/repo/releases/tag/v1.0.0.",
    )
    parser.add_argument(
        "--doi",
        help="Zenodo DOI minted from the release, e.g. 10.5281/zenodo.1234567 or https://doi.org/10.5281/zenodo.1234567.",
    )
    args = parser.parse_args()
    manifest = write_archive_manifest(
        args.repo_root,
        args.output_dir,
        release_url=args.release_url,
        doi=args.doi,
    )
    print(
        json.dumps(
            {
                "manifest_path": manifest["manifest_path"],
                "artifact_csv_path": manifest["artifact_csv_path"],
                "checksum_path": manifest["checksum_path"],
                "artifact_count": manifest["artifact_count"],
                "archive_publication_ready": manifest["archive_publication_ready"],
                "release_url": manifest["release_url"],
                "doi": manifest["doi"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
