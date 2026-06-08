from __future__ import annotations

from collections.abc import Sequence

from .models import FitSeedPlan


def _coerce_seed_tuple(seed_values: Sequence[int] | None, *, field_name: str) -> tuple[int, ...]:
    if seed_values is None:
        return ()
    seeds = tuple(int(seed) for seed in seed_values)
    if not seeds:
        raise ValueError(f"{field_name} must contain at least one seed when provided.")
    return seeds

def build_fit_seed_plan(
    proposal_seed: int,
    selection_seeds: Sequence[int] | None = None,
    validation_seeds: Sequence[int] | None = None,
) -> FitSeedPlan:
    selection_tuple = _coerce_seed_tuple(selection_seeds, field_name="selection_seeds")
    validation_tuple = _coerce_seed_tuple(validation_seeds, field_name="validation_seeds")
    overlap = set(selection_tuple).intersection(validation_tuple)
    if overlap:
        raise ValueError(
            "selection_seeds and validation_seeds must be disjoint; "
            f"overlap detected: {sorted(overlap)}."
        )
    if selection_seeds is None:
        selection_mode = "single_candidate_seed"
    elif len(selection_tuple) == 1:
        selection_mode = "single_explicit_seed"
    else:
        selection_mode = "multi_seed_mean"
    validation_mode = "not_run" if not validation_tuple else "disjoint_seed_panel"
    return FitSeedPlan(
        proposal_seed=int(proposal_seed),
        selection_seeds=selection_tuple,
        validation_seeds=validation_tuple,
        selection_mode=selection_mode,
        validation_mode=validation_mode,
    )
