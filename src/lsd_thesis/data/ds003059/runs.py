from __future__ import annotations

from collections.abc import Sequence

from .constants import DS003059_ALLOWED_RUNS, DS003059_DEFAULT_RUNS, DS003059_MUSIC_RUN, DS003059_MUSIC_RUNS


def normalize_ds003059_runs(
    runs: Sequence[str] | None = None,
    *,
    include_music: bool = False,
) -> tuple[str, ...]:
    """Return a deterministic ds003059 run tuple with run-02 guarded by an explicit flag."""
    selected = DS003059_MUSIC_RUNS if runs is None and include_music else (DS003059_DEFAULT_RUNS if runs is None else tuple(str(run) for run in runs))
    if not selected:
        raise ValueError("At least one ds003059 run must be selected.")
    invalid = sorted(set(selected).difference(DS003059_ALLOWED_RUNS))
    if invalid:
        raise ValueError(f"Unsupported ds003059 runs: {invalid}. Allowed runs: {list(DS003059_ALLOWED_RUNS)}.")
    if DS003059_MUSIC_RUN in selected and not include_music:
        raise ValueError("run-02 music extraction requires include_music=True / --include-music.")
    selected_set = set(selected)
    return tuple(run for run in DS003059_ALLOWED_RUNS if run in selected_set)
