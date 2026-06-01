from __future__ import annotations

import argparse
import json

from lsd_thesis.ds006072_payload_plan import REPO_ROOT, write_ds006072_payload_plan_status
from lsd_thesis.ds006072_validation import MIN_COMPARABLE_SUBJECTS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or execute the minimum ds006072 processed-CIFTI payload plan for true external validation."
    )
    parser.add_argument("--minimum-subjects", type=int, default=MIN_COMPARABLE_SUBJECTS)
    parser.add_argument("--execute", action="store_true", help="Download the selected payloads into data/ds006072.")
    args = parser.parse_args()

    status = write_ds006072_payload_plan_status(
        REPO_ROOT,
        minimum_subjects=args.minimum_subjects,
        execute=args.execute,
    )
    print(
        json.dumps(
            {
                "source_path": status["source_path"],
                "report_path": status["report_path"],
                "analysis_status": status["analysis_status"],
                "selected_subject_count": status["selected_subject_count"],
                "selected_file_count": status["selected_file_count"],
                "selected_total_size_bytes": status["selected_total_size_bytes"],
                "minimum_payloads_local_ready": status["minimum_payloads_local_ready"],
                "downloaded_file_count": len(status["downloaded_files"]),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
