from __future__ import annotations

import argparse
from pathlib import Path

from lsd_thesis.setting_seed.control_input import write_control_outputs
from lsd_thesis.setting_seed.dashboard_payload import write_dashboard_outputs
from lsd_thesis.setting_seed.data import write_data_audit
from lsd_thesis.setting_seed.latent import write_latent_outputs
from lsd_thesis.setting_seed.reliability import write_reliability_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the safe PASS 2A Set / Setting / Seed artifact build.")
    parser.add_argument("--stage-2-dir", default="results/stage_2", help="Cached Stage 2 artifact directory.")
    parser.add_argument("--seed", type=int, default=20260512, help="Deterministic seed.")
    args = parser.parse_args()

    stage_2_dir = Path(args.stage_2_dir)
    audit = write_data_audit(stage_2_dir=stage_2_dir)
    write_reliability_outputs(stage_2_dir=stage_2_dir, seed=args.seed)
    write_latent_outputs(stage_2_dir=stage_2_dir, seed=args.seed)
    write_control_outputs(
        stage_2_dir=stage_2_dir,
        run_02_available=bool(audit["run_02_files_present"]),
        run_02_analysis_ready=bool(audit["run_02_analysis_ready"]),
        motion_analysis_ready=bool(audit["motion_analysis_ready"]),
    )
    write_dashboard_outputs()
    print("PASS 2A artifacts written under results/setting_seed and output/doc/set_setting_seed_microsite.html")
    print(f"run_02_available={audit['run_02_available']} motion_summaries_available={audit['motion_summaries_available']}")


if __name__ == "__main__":
    main()
