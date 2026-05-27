from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lsd_thesis.external_ingestion import (  # noqa: E402
    ingest_receptor_prior,
    ingest_structural_connectome,
    write_external_ingestion_status,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and ingest external structural-connectome and PET receptor-prior CSVs."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--structural-csv", type=Path, default=None)
    parser.add_argument("--receptor-csv", type=Path, default=None)
    parser.add_argument("--structural-provenance", default="user_supplied_structural_connectome_csv")
    parser.add_argument("--receptor-provenance", default="user_supplied_pet_receptor_prior_csv")
    args = parser.parse_args()

    outputs: dict[str, object] = {}
    if args.structural_csv is not None:
        outputs["structural"] = ingest_structural_connectome(
            args.structural_csv,
            repo_root=args.repo_root,
            provenance=args.structural_provenance,
        )
    if args.receptor_csv is not None:
        outputs["receptor"] = ingest_receptor_prior(
            args.receptor_csv,
            repo_root=args.repo_root,
            provenance=args.receptor_provenance,
        )
    outputs["status"] = write_external_ingestion_status(args.repo_root)
    print(json.dumps(outputs, indent=2), flush=True)


if __name__ == "__main__":
    main()
