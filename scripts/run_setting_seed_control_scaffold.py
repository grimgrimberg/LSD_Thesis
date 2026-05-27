from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.control_input import write_control_outputs
from lsd_thesis.setting_seed.data import audit_stage2_cache


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Set / Setting / Seed music-control scaffold.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--output-dir", default="results/setting_seed/control", help="Output directory for control artifacts.")
    args = parser.parse_args()

    audit = audit_stage2_cache(Path(args.stage_2_dir))
    scaffold = write_control_outputs(
        stage_2_dir=Path(args.stage_2_dir),
        output_dir=Path(args.output_dir),
        run_02_available=bool(audit["run_02_files_present"]),
        run_02_analysis_ready=bool(audit["run_02_analysis_ready"]),
        motion_analysis_ready=bool(audit["motion_analysis_ready"]),
    )
    print(f"wrote {args.output_dir}/control_scaffold.json")
    print(f"status={scaffold['status']}")


if __name__ == "__main__":
    main()
