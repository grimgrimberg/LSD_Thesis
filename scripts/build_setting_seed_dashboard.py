from __future__ import annotations

import argparse

from lsd_thesis.setting_seed.dashboard_payload import write_dashboard_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Set / Setting / Seed dashboard payload and static microsite.")
    parser.parse_args()

    payload = write_dashboard_outputs()
    print("wrote results/setting_seed/dashboard/dashboard_payload.json")
    print("wrote results/setting_seed/dashboard/index.html")
    print("wrote output/doc/set_setting_seed_microsite.html")
    print(f"status={payload['status']}")


if __name__ == "__main__":
    main()

