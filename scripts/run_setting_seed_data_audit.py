from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.data import write_data_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Set / Setting / Seed cached data audit.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--output-dir", default="results/setting_seed/data_audit", help="Output directory for audit artifacts.")
    args = parser.parse_args()

    audit = write_data_audit(stage_2_dir=Path(args.stage_2_dir), output_dir=Path(args.output_dir))
    print(f"wrote {args.output_dir}/data_audit.json")
    print(f"subjects={audit['subject_count']} runs={','.join(audit['runs'])} run_02_available={audit['run_02_available']}")


if __name__ == "__main__":
    main()

