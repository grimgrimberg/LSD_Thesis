from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from lsd_thesis.publication import PublicationEvidence
from lsd_thesis.publication_figures import PublicationFigure

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
MARKDOWN_ENVIRONMENT = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def _require_stage1_panel(stage1: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline = stage1.get("baseline")
    perturbed = stage1.get("perturbed")
    if not isinstance(baseline, dict) or not isinstance(perturbed, dict):
        raise ValueError("stage1 evidence must include baseline and perturbed metric mappings")
    return baseline, perturbed


def _portable_figure_path(figure: PublicationFigure) -> str:
    return Path("figures", Path(figure.path).name).as_posix()


def _stage2_objective_sentence(initial_score: float, best_score: float) -> str:
    delta = best_score - initial_score
    if delta < 0:
        direction = "decreased"
    elif delta > 0:
        direction = "increased"
    else:
        direction = "stayed the same"
    return (
        f"Stage 2 objective changed from {initial_score:.3f} to {best_score:.3f} ({direction}); "
        "lower scores are better. The selected score comes from the optimization step."
    )


def _figure_markdown(figure: PublicationFigure) -> str:
    return "\n".join(
        [
            f"![{figure.caption}]({_portable_figure_path(figure)})",
            "",
            f"*Figure: {figure.caption}*",
            "",
            f"*Limitation: {figure.limitations}*",
        ]
    )


def _render_markdown_template(template_name: str, **context: Any) -> str:
    template = MARKDOWN_ENVIRONMENT.get_template(template_name)
    rendered = template.render(**context)
    return rendered.strip() + "\n"


def _small_cardinal(value: int) -> str:
    small_numbers = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
        11: "eleven",
        12: "twelve",
        13: "thirteen",
        14: "fourteen",
        15: "fifteen",
        16: "sixteen",
        17: "seventeen",
        18: "eighteen",
        19: "nineteen",
        20: "twenty",
        30: "thirty",
        40: "forty",
        50: "fifty",
        60: "sixty",
        70: "seventy",
        80: "eighty",
        90: "ninety",
    }
    if value in small_numbers:
        return small_numbers[value]
    if 20 < value < 100:
        tens, ones = divmod(value, 10)
        tens_value = tens * 10
        tens_word = small_numbers[tens_value]
        return f"{tens_word}-{small_numbers[ones]}" if ones else tens_word
    return str(value)


def _best_model_name(models: list[dict[str, Any]], score_keys: tuple[str, ...]) -> str:
    if not models:
        return "not reported"
    for score_key in score_keys:
        scored_models = [model for model in models if _nested_score(model, score_key) is not None]
        if scored_models:
            best_model = max(scored_models, key=lambda model: float(_nested_score(model, score_key) or 0.0))
            return str(best_model.get("name", "unnamed_model"))
    return str(models[0].get("name", "unnamed_model"))


def _nested_score(model: dict[str, Any], score_key: str) -> float | None:
    current: Any = model
    for part in score_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    try:
        return float(current)
    except (TypeError, ValueError):
        return None


def _stage4_pairwise_sentence(stage4: Any) -> str:
    delta = stage4.best_pair_score - stage4.best_single_score
    if delta < 0:
        comparison = "outperformed"
    elif delta > 0:
        comparison = "did not outperform"
    else:
        comparison = "matched"
    return (
        f"The best single mechanism is `{stage4.best_single_mechanism}` "
        f"(score {stage4.best_single_score:.4f}). The best pair is `{stage4.best_pair_name}` "
        f"(score {stage4.best_pair_score:.4f}), which {comparison} the best single mechanism "
        "under the current objective; lower scores are better."
    )


def _provenance_statement(stage2_raw: Any) -> str:
    version_stamp = getattr(stage2_raw, "version_stamp", None)
    if isinstance(version_stamp, dict):
        git = version_stamp.get("git", {})
        if isinstance(git, dict) and git.get("commit_hash"):
            return (
                f"Stage 2 provenance records git commit `{git['commit_hash']}` "
                f"with worktree status `{git.get('worktree_status', 'unknown')}`."
            )
    return (
        "The generated report intentionally avoids claiming a fixed commit state unless "
        "a machine-readable version stamp is present."
    )


def _metric_summary_text(summary: dict[str, Any], *, precision: int = 4) -> str:
    if not isinstance(summary, dict) or not isinstance(summary.get("mean"), int | float):
        return "not recorded"
    text = f"{float(summary['mean']):.{precision}f}"
    if isinstance(summary.get("std"), int | float):
        text += f" (fold SD {float(summary['std']):.{precision}f})"
    return text


def _metric_range_text(values: list[float], *, precision: int = 4) -> str:
    if not values:
        return "not recorded"
    return f"{min(values):.{precision}f} to {max(values):.{precision}f}"


def _cv5_metric_table(cv5_validation: dict[str, Any]) -> str:
    aggregate_metrics = cv5_validation.get("aggregate_metrics", {})
    score_summary = aggregate_metrics.get("score_mean", {})
    sign_summary = aggregate_metrics.get("sign_agreement_fraction", {})
    mechanism_counts = aggregate_metrics.get("selected_mechanism_counts", {})
    strength_counts = aggregate_metrics.get("selected_strength_counts", {})
    per_fold_metrics = cv5_validation.get("per_fold_metrics", [])
    fold_scores = [
        float(item["score_mean"])
        for item in per_fold_metrics
        if isinstance(item, dict) and isinstance(item.get("score_mean"), int | float)
    ]
    sign_scores = [
        float(item["sign_agreement_fraction"])
        for item in per_fold_metrics
        if isinstance(item, dict) and isinstance(item.get("sign_agreement_fraction"), int | float)
    ]
    selected_mechanism = (
        ", ".join(f"`{key}`={value}" for key, value in sorted(mechanism_counts.items()))
        if isinstance(mechanism_counts, dict) and mechanism_counts
        else "not recorded"
    )
    selected_strength = (
        ", ".join(f"`{key}`={value}" for key, value in sorted(strength_counts.items()))
        if isinstance(strength_counts, dict) and strength_counts
        else "not recorded"
    )
    source_manifest = cv5_validation.get("source_manifest_path") or cv5_validation.get("approved_manifest_path")
    run_parameters = cv5_validation.get("run_parameters", {})
    aggregate_path = cv5_validation.get("aggregate_path") or (
        run_parameters.get("aggregate_path") if isinstance(run_parameters, dict) else None
    )
    run_command = run_parameters.get("run_command") if isinstance(run_parameters, dict) else None
    rows = [
        ("Approved manifest", f"`{source_manifest}`" if source_manifest else "not recorded"),
        ("Aggregate artifact", f"`{aggregate_path}`" if aggregate_path else "not recorded"),
        ("Fold-averaged delta mismatch score", _metric_summary_text(score_summary)),
        ("Held-out score range", _metric_range_text(fold_scores)),
        ("Fold-averaged target-sign agreement", _metric_summary_text(sign_summary)),
        ("Target-sign agreement range", _metric_range_text(sign_scores)),
        ("Selected perturbation family counts", selected_mechanism),
        ("Selected strength counts", selected_strength),
        ("Reproduction command", f"`{run_command}`" if run_command else "not recorded"),
    ]
    table_lines = [
        "",
        "",
        "| CV5 descriptive item | Value |",
        "| --- | --- |",
    ]
    table_lines.extend(f"| {label} | {value} |" for label, value in rows)
    table_lines.extend(
        [
            "",
            (
                "These values are descriptive fold summaries. The fold standard deviation is not a "
                "confidence interval, and the result should not be interpreted as external predictive validity."
            ),
        ]
    )
    return "\n".join(table_lines)


def _validation_boundary_statement(stage2_raw: Any, cv5_validation: dict[str, Any] | None = None) -> str:
    if cv5_validation:
        completed_folds = int(cv5_validation.get("completed_folds") or 0)
        total_folds = int(cv5_validation.get("total_folds") or 0)
        total_subjects = int(cv5_validation.get("total_subjects") or 0)
        scope = str(cv5_validation.get("validation_claim_scope") or "internal_subject_disjoint_cv5")
        if cv5_validation.get("held_out_validation_completed") is True:
            return (
                "Approved preliminary five-fold subject-disjoint internal validation completed across "
                f"{completed_folds}/{total_folds} folds under `{scope}`, covering "
                f"{total_subjects} complete paired subjects exactly once as held-out targets. "
                "This is internal validation, not external or clinical validation, and the "
                "n=3 held-out subjects per fold require cautious interpretation. No subject-level "
                "motion/FD/DVARS/confound/censoring stratification was available for the split. "
                "The approved manifest is the split-configuration record; the aggregate artifact is "
                "the authoritative completion record."
                f"{_cv5_metric_table(cv5_validation)}"
            )
        return (
            "Approved five-fold subject-disjoint internal validation is configured but not fully completed: "
            f"{completed_folds}/{total_folds} folds currently have completed held-out results. "
            "No completed CV5 validation claim should be made until all folds complete."
        )

    boundary = getattr(stage2_raw, "validation_boundary", None)
    if boundary is None or not getattr(boundary, "configured", False):
        return (
            "Subject-disjoint held-out validation has not yet been configured or performed for Stage 2/3; "
            "the current evidence remains calibration plus stochastic diagnostics."
        )
    selection_count = getattr(boundary, "selection_subject_count", None)
    validation_count = getattr(boundary, "validation_subject_count", 0)
    if getattr(boundary, "completed", False):
        return (
            "An approved internal subject-disjoint held-out validation completed under "
            f"`{boundary.split_strategy}` with {selection_count} selection subjects and "
            f"{validation_count} held-out validation subjects. This is not external validation."
        )
    if getattr(boundary, "approval_status", "none") == "candidate":
        return (
            "A candidate subject-disjoint split is prepared under "
            f"`{boundary.split_strategy}` with {selection_count} selection subjects and "
            f"{validation_count} held-out validation subjects, but it is not approved and "
            "held-out validation has not yet been completed."
        )
    return (
        "A subject-disjoint split is configured under "
        f"`{boundary.split_strategy}` with {selection_count} selection subjects and "
        f"{validation_count} held-out validation subjects, but held-out validation has not yet been completed."
    )


def _sign_mismatch_sentence(sign_mismatches: list[str]) -> str:
    if not sign_mismatches:
        return ""
    if len(sign_mismatches) == 1:
        return f"sign mismatches remain for: `{sign_mismatches[0]}`."
    mismatch_list = ", ".join(f"`{name}`" for name in sign_mismatches[:-1])
    return f"sign mismatches remain for: {mismatch_list}, and `{sign_mismatches[-1]}`."


def build_thesis_report_markdown(
    evidence: PublicationEvidence,
    figure_bundle: Mapping[str, PublicationFigure],
) -> str:
    stage1 = evidence.stage1
    stage2 = evidence.stage2
    stage3 = evidence.stage3
    stage4 = evidence.stage4

    stage1_baseline, stage1_perturbed = _require_stage1_panel(stage1)
    return _render_markdown_template(
        "thesis_report.md.jinja",
        dataset_anchor=stage2.dataset_anchor,
        subject_count_words=_small_cardinal(stage2.subject_count),
        run_count_words=_small_cardinal(stage2.run_count),
        stage2_objective_sentence=_stage2_objective_sentence(stage2.initial_score, stage2.best_score),
        validation_boundary_statement=_validation_boundary_statement(stage2, evidence.cv5_validation),
        stage1_figure_markdown=_figure_markdown(figure_bundle["stage1_metric_shift"]),
        stage2_figure_markdown=_figure_markdown(figure_bundle["stage2_fit_robustness"]),
        stage1_baseline_entropy=f"{float(stage1_baseline['state_entropy']):.3f}",
        stage1_perturbed_entropy=f"{float(stage1_perturbed['state_entropy']):.3f}",
        stage1_baseline_switching=f"{float(stage1_baseline['switching_rate']):.3f}",
        stage1_perturbed_switching=f"{float(stage1_perturbed['switching_rate']):.3f}",
        best_mechanism=stage3.best_mechanism,
        best_strength=f"{stage3.best_strength:.2f}",
        robust_best_mechanism=stage3.robust_best_mechanism,
        robust_best_strength=(
            f"{stage3.robust_best_strength:.2f}" if stage3.robust_best_strength is not None else None
        ),
        best_pair_name=stage4.best_pair_name,
        best_single_name=stage4.best_single_mechanism,
        best_single_score=f"{stage4.best_single_score:.4f}",
        best_pair_score=f"{stage4.best_pair_score:.4f}",
        stage4_pairwise_sentence=_stage4_pairwise_sentence(stage4),
        provenance_statement=_provenance_statement(stage2),
        sign_mismatch_sentence=_sign_mismatch_sentence(evidence.sign_mismatches),
        best_condition_model=_best_model_name(
            evidence.condition_models,
            ("aggregate.balanced_accuracy_mean", "balanced_accuracy", "aggregate.roc_auc_mean", "roc_auc"),
        ),
        best_multitask_model=_best_model_name(
            evidence.multitask_models,
            ("aggregate.balanced_accuracy_mean", "balanced_accuracy", "aggregate.eigen_r2_mean", "eigen_r2"),
        ),
        rocket_benchmark=evidence.rocket_benchmark,
    )


def build_defense_outline_markdown(evidence: PublicationEvidence) -> str:
    stage2 = evidence.stage2
    stage3 = evidence.stage3
    stage4 = evidence.stage4

    outline_lines = [
        "# Defense Outline",
        "",
        "## Slide 1: Framing",
        "- Talking points:",
        "  - This is a surrogate model of altered-state-inspired macro-dynamics.",
        "  - The goal is to explain proxy shifts, not receptor mechanisms or subjective reports.",
        "  - The repository is strongest when it makes narrow, testable macro-dynamics claims.",
        "",
        "## Slide 2: Stage 1 shift",
        "- Talking points:",
        "  - Baseline and perturbed conditions differ in the proxy values.",
        "  - The stage 1 figure highlights changes in entropy and switching rate.",
        "",
        "## Slide 3: Stage 2 robustness",
        "- Talking points:",
        f"  - {_stage2_objective_sentence(stage2.initial_score, stage2.best_score)}",
        f"  - Benchmark anchor: {stage2.dataset_anchor}.",
        f"  - The comparison uses {stage2.subject_count} subjects and {stage2.run_count} runs.",
        "  - Multi-seed summaries offer limited evidence about run-to-run consistency.",
        "",
        "## Slide 4: Mechanism ranking",
        "- Talking points:",
        f"  - Best single mechanism: `{stage3.best_mechanism}` at strength {stage3.best_strength:.2f}.",
        f"  - Best pair: `{stage4.best_pair_name}`.",
        f"  - Sign mismatches: {', '.join(evidence.sign_mismatches) if evidence.sign_mismatches else 'none reported'}.",
        "",
        "## Slide 5: Limits",
        "- Talking points:",
        "  - The work is explicit about proxy metrics, cached evidence, and limited generalization claims.",
        "  - Any biological interpretation should stay at the macro-dynamics level.",
        "",
        "## Likely challenge",
        "- Likely challenge: Why should anyone trust these proxies if they do not model receptors or subjective experience?",
        "- Answer: The value is in transparent, testable macro-level structure, not in pretending to be a direct mechanistic model.",
        "",
    ]
    return "\n".join(outline_lines)
