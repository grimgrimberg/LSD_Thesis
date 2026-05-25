from __future__ import annotations

import argparse
import json
from pathlib import Path

from lsd_thesis.thesis_loop import build_thesis_evidence_loop


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build thesis evidence-loop status artifacts for LSD robustness, psilocybin, structural graph, "
            "receptor priors, parcellation, and literature checks."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root.")
    args = parser.parse_args()

    payload = build_thesis_evidence_loop(args.repo_root.resolve())
    print(json.dumps({"analysis_status": payload["analysis_status"], "source_path": payload["source_path"]}, indent=2))
    for row in payload["status_rows"]:
        print(f"{row['step']}. {row['label']}: {row['status']} - {row['evidence']}")


if __name__ == "__main__":
    main()
