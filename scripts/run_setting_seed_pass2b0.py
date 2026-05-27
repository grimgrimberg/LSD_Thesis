from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.control_input import write_control_outputs
from lsd_thesis.setting_seed.dashboard_payload import write_dashboard_outputs
from lsd_thesis.setting_seed.data import write_data_audit
from lsd_thesis.setting_seed.motion import write_motion_outputs
from lsd_thesis.setting_seed.reliability import write_reliability_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run safe PASS 2B-0 readiness artifacts without downloads or extraction.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--seed", type=int, default=20260512, help="Deterministic seed for reliability bootstrap.")
    args = parser.parse_args()

    stage_2_dir = Path(args.stage_2_dir)
    motion = write_motion_outputs(stage_2_dir=stage_2_dir)
    audit = write_data_audit(stage_2_dir=stage_2_dir)
    write_reliability_outputs(stage_2_dir=stage_2_dir, seed=args.seed)
    write_control_outputs(
        stage_2_dir=stage_2_dir,
        run_02_available=bool(audit["run_02_files_present"]),
        run_02_analysis_ready=bool(audit["run_02_analysis_ready"]),
        motion_analysis_ready=bool(audit["motion_analysis_ready"]),
    )
    write_dashboard_outputs()
    print("PASS 2B-0 readiness artifacts written under results/setting_seed and output/doc/set_setting_seed_microsite.html")
    print(
        "run_02_files_present="
        f"{audit['run_02_files_present']} run_02_analysis_ready={audit['run_02_analysis_ready']} "
        f"motion_status={motion['status']}"
    )


if __name__ == "__main__":
    main()
