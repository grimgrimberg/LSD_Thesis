from __future__ import annotations

import argparse
import json

from lsd_thesis.ds006072_cifti_extraction import REPO_ROOT, write_ds006072_cifti_extraction_status


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build ds006072 CIFTI empirical viewer records for unchanged external scoring, "
            "including the stronger Schaefer100/Yeo7 cortex parcel layer when --execute is used."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Extract local selected CIFTIs into structure-family and Schaefer100 empirical-viewer records.",
    )
    args = parser.parse_args()

    status = write_ds006072_cifti_extraction_status(REPO_ROOT, execute=args.execute)
    print(
        json.dumps(
            {
                "source_path": status["source_path"],
                "report_path": status["report_path"],
                "analysis_status": status["analysis_status"],
                "subject_view_count": status["subject_view_count"],
                "cifti_empirical_viewer_ready": status["cifti_empirical_viewer_ready"],
                "schaefer100_subject_view_count": status["schaefer100_subject_view_count"],
                "schaefer100_empirical_viewer_ready": status["schaefer100_empirical_viewer_ready"],
                "stronger_external_validation_ready": status["stronger_external_validation_ready"],
                "claim_status": status["claim_status"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
