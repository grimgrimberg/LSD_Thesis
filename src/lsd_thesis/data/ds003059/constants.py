from __future__ import annotations

from lsd_thesis.core import MODULE_NAMES as MODULE_NAMES

OPENNEURO_GRAPHQL_URL = "https://openneuro.org/crn/graphql"
DS003059_DATASET_ID = "ds003059"
DS003059_VERSION = "1.0.0"
DS003059_SESSIONS: tuple[str, ...] = ("ses-LSD", "ses-PLCB")
DS003059_DEFAULT_RUNS: tuple[str, ...] = ("run-01", "run-03")
DS003059_MUSIC_RUN = "run-02"
DS003059_MUSIC_RUNS: tuple[str, ...] = ("run-01", "run-02", "run-03")
DS003059_ALLOWED_RUNS: tuple[str, ...] = DS003059_MUSIC_RUNS
EMPIRICAL_CACHE_SCHEMA_VERSION = 1
EMPIRICAL_CACHE_METADATA_FILENAME = "empirical_cache_metadata.json"
HARVARD_OXFORD_CORTICAL_FILENAME = "HarvardOxford-cort-maxprob-thr25-2mm.nii.gz"
HARVARD_OXFORD_SUBCORTICAL_FILENAME = "HarvardOxford-sub-maxprob-thr25-2mm.nii.gz"
MODULE_ATLAS_LABELS: dict[str, dict[str, tuple[int, ...]]] = {
    "visual": {"cortical": (22, 23, 24, 31, 32, 36, 39, 40, 47, 48), "subcortical": ()},
    "auditory": {"cortical": (9, 10, 42, 44, 45, 46), "subcortical": ()},
    "salience": {"cortical": (2, 28, 29, 41), "subcortical": ()},
    "default_mode": {"cortical": (21, 25, 30, 31), "subcortical": ()},
    "executive_frontoparietal": {"cortical": (3, 4, 5, 6, 18, 19, 20), "subcortical": ()},
    "limbic_affective": {"cortical": (8, 27, 33, 34, 35), "subcortical": (9, 10, 11, 19, 20, 21)},
    "thalamic_gateway": {"cortical": (), "subcortical": (4, 15)},
    "sensorimotor": {"cortical": (7, 17, 26, 42, 43), "subcortical": ()},
}
