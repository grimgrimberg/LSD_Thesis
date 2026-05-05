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
        scored_models = [model for model in models if score_key in model]
        if scored_models:
            best_model = max(scored_models, key=lambda model: float(model[score_key]))
            return str(best_model.get("name", "unnamed_model"))
    return str(models[0].get("name", "unnamed_model"))


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
        stage1_figure_markdown=_figure_markdown(figure_bundle["stage1_metric_shift"]),
        stage2_figure_markdown=_figure_markdown(figure_bundle["stage2_fit_robustness"]),
        stage1_baseline_entropy=f"{float(stage1_baseline['state_entropy']):.3f}",
        stage1_perturbed_entropy=f"{float(stage1_perturbed['state_entropy']):.3f}",
        stage1_baseline_switching=f"{float(stage1_baseline['switching_rate']):.3f}",
        stage1_perturbed_switching=f"{float(stage1_perturbed['switching_rate']):.3f}",
        best_mechanism=stage3.best_mechanism,
        best_strength=f"{stage3.best_strength:.2f}",
        best_pair_name=stage4.best_pair_name,
        sign_mismatch_sentence=_sign_mismatch_sentence(evidence.sign_mismatches),
        best_condition_model=_best_model_name(evidence.condition_models, ("balanced_accuracy", "roc_auc")),
        best_multitask_model=_best_model_name(evidence.multitask_models, ("balanced_accuracy", "eigen_r2")),
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
