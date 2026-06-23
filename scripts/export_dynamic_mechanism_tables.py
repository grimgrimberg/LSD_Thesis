from __future__ import annotations

import argparse
import csv
import json
import math
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

DEFAULT_SUMMARY_PATH = Path("results/dynamic_mechanism_ranking/summary.json")
DEFAULT_OUTPUT_DIR = Path("results/dynamic_mechanism_ranking/exports")


def _clean_sheet_name(name: str) -> str:
    invalid_chars = set("[]:*?/\\")
    cleaned = "".join("_" if char in invalid_chars else char for char in name)
    return cleaned[:31] or "Sheet"


def _column_name(index: int) -> str:
    index += 1
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _cell_xml(row_index: int, col_index: int, value: Any) -> str:
    ref = f"{_column_name(col_index)}{row_index}"
    if value is None:
        return f'<c r="{ref}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, int):
        return f'<c r="{ref}"><v>{value}</v></c>'
    if isinstance(value, float):
        if math.isfinite(value):
            return f'<c r="{ref}"><v>{value:.15g}</v></c>'
        return f'<c r="{ref}"/>'
    text = escape(str(value))
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def _worksheet_xml(headers: list[str], rows: list[dict[str, Any]]) -> str:
    all_rows: list[list[Any]] = [headers]
    all_rows.extend([[row.get(header) for header in headers] for row in rows])
    sheet_rows = []
    for row_index, row in enumerate(all_rows, start=1):
        cells = "".join(_cell_xml(row_index, col_index, value) for col_index, value in enumerate(row))
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        + "".join(sheet_rows)
        + "</sheetData></worksheet>"
    )


def _write_xlsx(path: Path, sheets: dict[str, tuple[list[str], list[dict[str, Any]]]]) -> None:
    sheet_items = list(sheets.items())
    workbook_sheets = []
    workbook_rels = []
    content_overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for index, (name, _) in enumerate(sheet_items, start=1):
        sheet_name = escape(_clean_sheet_name(name))
        workbook_sheets.append(f'<sheet name="{sheet_name}" sheetId="{index}" r:id="rId{index}"/>')
        workbook_rels.append(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
        content_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets>"
        + "".join(workbook_sheets)
        + "</sheets></workbook>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(workbook_rels)
        + "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + "".join(content_overrides)
        + "</Types>"
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        "</styleSheet>"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", content_types_xml)
        workbook.writestr("_rels/.rels", rels_xml)
        workbook.writestr("xl/workbook.xml", workbook_xml)
        workbook.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        workbook.writestr("xl/styles.xml", styles_xml)
        for index, (_, (headers, rows)) in enumerate(sheet_items, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", _worksheet_xml(headers, rows))


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _expected_sign(metric: str) -> int:
    return -1 if metric == "mean_dwell_time" else 1


def _metric_support(row: dict[str, Any]) -> str:
    value = row.get("mean_delta")
    if not isinstance(value, int | float):
        return "unknown"
    sign = row.get("expected_sign")
    expected_sign = int(sign) if isinstance(sign, int | float) and int(sign) in {-1, 1} else _expected_sign(str(row.get("metric")))
    if abs(float(value)) <= 1e-12:
        return "neutral"
    return "supports_expected_direction" if float(value) * expected_sign > 0 else "opposes_expected_direction"


def _build_tables(summary: dict[str, Any]) -> dict[str, tuple[list[str], list[dict[str, Any]]]]:
    ranking_headers = ["rank", "layer", "mechanism", "status", "raw_status", "score", "evidence"]
    ranking_rows = [
        {
            "rank": row.get("rank") if row.get("rank") is not None else "not_ranked",
            "layer": row.get("layer"),
            "mechanism": row.get("mechanism"),
            "status": row.get("public_status", row.get("status")),
            "raw_status": row.get("status"),
            "score": row.get("score"),
            "evidence": row.get("evidence"),
        }
        for row in summary.get("mechanism_ranking", [])
    ]

    metric_headers = [
        "metric",
        "mean_delta",
        "std_delta",
        "effect_size",
        "signed_effect_size",
        "expected_sign",
        "sign_consistency",
        "sign_flip_p_value",
        "expected_direction",
        "support_direction",
    ]
    metric_tables: dict[str, list[dict[str, Any]]] = {}
    pair_tables: dict[str, tuple[list[str], list[dict[str, Any]]]] = {}
    for section_key in ("transition_proxy", "hierarchy_routing", "dynamic_repertoire"):
        metric_rows = [
            {**row, "support_direction": _metric_support(row)}
            for row in summary.get(section_key, {}).get("metric_deltas", [])
        ]
        metric_tables[section_key] = metric_rows
        metrics = [str(row.get("metric")) for row in metric_rows]
        pair_headers = ["subject", "run"]
        pair_rows: list[dict[str, Any]] = []
        for metric in metrics:
            pair_headers.extend([f"placebo_{metric}", f"lsd_{metric}", f"delta_{metric}"])
        for row in summary.get(section_key, {}).get("pair_rows", []):
            flat: dict[str, Any] = {"subject": row.get("subject"), "run": row.get("run")}
            for metric in metrics:
                flat[f"placebo_{metric}"] = row.get("placebo", {}).get(metric)
                flat[f"lsd_{metric}"] = row.get("lsd", {}).get(metric)
                flat[f"delta_{metric}"] = row.get("delta", {}).get(metric)
            pair_rows.append(flat)
        pair_tables[section_key] = (pair_headers, pair_rows)

    control_metric_rows = [
        {**row, "support_direction": _metric_support(row)}
        for row in summary.get("network_control_energy", {}).get("metric_deltas", [])
    ]
    control_metrics = [str(row.get("metric")) for row in control_metric_rows]
    control_pair_headers = ["subject", "run", "matched_state_count", *control_metrics]
    control_pair_rows = []
    for row in summary.get("network_control_energy", {}).get("pair_rows", []):
        flat = {
            "subject": row.get("subject"),
            "run": row.get("run"),
            "matched_state_count": row.get("matched_state_count"),
        }
        for metric in control_metrics:
            flat[metric] = row.get("metrics", {}).get(metric)
        control_pair_rows.append(flat)

    control_energy_headers = ["subject", "run", "profile", "mean_control_energy", "matched_state_count"]
    control_energy_rows = summary.get("network_control_energy", {}).get("energy_rows", [])
    control_profile_headers = ["profile", "module", "normalized_weight"]
    control_profile_rows = []
    for profile in summary.get("network_control_energy", {}).get("control_profiles", []):
        for module, weight in profile.get("module_weights", {}).items():
            control_profile_rows.append(
                {
                    "profile": profile.get("profile"),
                    "module": module,
                    "normalized_weight": weight,
                }
            )

    dmdc_headers = [
        "held_out_subject",
        "sample_count",
        "rmse_no_input",
        "rmse_condition_input",
        "rmse_condition_interaction",
        "rmse_improvement",
        "relative_improvement_pct",
        "condition_bias_rmse_improvement",
        "condition_bias_relative_improvement_pct",
        "condition_interaction_rmse_improvement",
        "condition_interaction_relative_improvement_pct",
        "condition_input_helped",
        "condition_interaction_helped",
    ]
    dmdc_rows = []
    for row in summary.get("dmdc", {}).get("fold_rows", []):
        relative = row.get("relative_improvement_pct")
        interaction_relative = row.get("condition_interaction_relative_improvement_pct")
        dmdc_rows.append(
            {
                **row,
                "condition_input_helped": bool(isinstance(relative, int | float) and float(relative) > 0),
                "condition_interaction_helped": bool(
                    isinstance(interaction_relative, int | float) and float(interaction_relative) > 0
                ),
            }
        )

    vector_headers = ["module", "coefficient", "absolute_coefficient", "direction"]
    vector_tables: dict[str, list[dict[str, Any]]] = {}
    for vector_key in ("condition_input_vector", "condition_interaction_vector"):
        vector_rows = []
        for row in summary.get("dmdc", {}).get(vector_key, []):
            coefficient = row.get("coefficient")
            value = float(coefficient) if isinstance(coefficient, int | float) else 0.0
            vector_rows.append(
                {
                    "module": row.get("module"),
                    "coefficient": coefficient,
                    "absolute_coefficient": abs(value),
                    "direction": "positive" if value > 0 else "negative" if value < 0 else "zero",
                }
            )
        vector_tables[vector_key] = vector_rows

    readme_headers = ["field", "value"]
    dmdc = summary.get("dmdc", {})
    readme_rows = [
        {"field": "export_generated_at_utc", "value": datetime.now(UTC).isoformat()},
        {"field": "summary_generated_at_utc", "value": summary.get("generated_at_utc")},
        {"field": "source_summary_path", "value": summary.get("source_path", DEFAULT_SUMMARY_PATH.as_posix())},
        {"field": "dataset_scope", "value": summary.get("dataset_scope")},
        {"field": "source_viewer_root", "value": summary.get("source_viewer_root")},
        {"field": "paired_subject_run_records", "value": summary.get("pair_count")},
        {"field": "subject_count", "value": summary.get("subject_count")},
        {"field": "runs_used_for_ai_ml", "value": ", ".join(summary.get("runs", []))},
        {"field": "transition_proxy_support_score", "value": summary.get("transition_proxy", {}).get("support_score")},
        {"field": "hierarchy_routing_support_score", "value": summary.get("hierarchy_routing", {}).get("support_score")},
        {"field": "dynamic_repertoire_support_score", "value": summary.get("dynamic_repertoire", {}).get("support_score")},
        {"field": "network_control_energy_support_score", "value": summary.get("network_control_energy", {}).get("support_score")},
        {"field": "network_control_graph_source", "value": summary.get("network_control_energy", {}).get("graph_source")},
        {
            "field": "network_control_receptor_prior_source",
            "value": summary.get("network_control_energy", {}).get("receptor_prior_source"),
        },
        {"field": "dmdc_relative_improvement_pct_mean", "value": dmdc.get("relative_improvement_pct_mean")},
        {
            "field": "dmdc_condition_interaction_relative_improvement_pct_mean",
            "value": dmdc.get("condition_interaction_relative_improvement_pct_mean"),
        },
        {
            "field": "validation_interpretation",
            "value": (
                "A/B/C/D are exploratory proxy layers; judge claims by held-out RMSE, "
                "signed effect sizes, sign consistency, and network-control null comparisons."
            ),
        },
        {"field": "claim_guardrail", "value": summary.get("claim_guardrail")},
        {
            "field": "limitation_1",
            "value": (
                "Run-02 music is available in the fMRI explorer but is not part of the "
                "current A+B+C+D+E ranking summary."
            ),
        },
        {
            "field": "limitation_2",
            "value": (
                "DMDc is not evidence for controlled dynamics unless the condition-interaction "
                "variant improves held-out prediction."
            ),
        },
        {"field": "limitation_3", "value": "C and D are coarse FC proxy layers, not direct biological mechanism tests."},
        {
            "field": "limitation_4",
            "value": "E uses a proxy graph and proxy receptor priors until structural-connectome and PET receptor-map inputs are added.",
        },
    ]

    def generic_table(rows: list[dict[str, Any]], preferred_headers: list[str]) -> tuple[list[str], list[dict[str, Any]]]:
        keys = sorted({key for row in rows for key in row})
        headers = preferred_headers + [key for key in keys if key not in preferred_headers]
        return headers, rows

    tables = {
        "readme": (readme_headers, readme_rows),
        "mechanism_ranking": (ranking_headers, ranking_rows),
        "transition_metric_deltas": (metric_headers, metric_tables["transition_proxy"]),
        "transition_pair_deltas": pair_tables["transition_proxy"],
        "hierarchy_metric_deltas": (metric_headers, metric_tables["hierarchy_routing"]),
        "hierarchy_pair_deltas": pair_tables["hierarchy_routing"],
        "repertoire_metric_deltas": (metric_headers, metric_tables["dynamic_repertoire"]),
        "repertoire_pair_deltas": pair_tables["dynamic_repertoire"],
        "network_control_metrics": (metric_headers, control_metric_rows),
        "network_control_pair_metrics": (control_pair_headers, control_pair_rows),
        "network_control_energies": (control_energy_headers, control_energy_rows),
        "network_control_profiles": (control_profile_headers, control_profile_rows),
        "dmdc_loso_folds": (dmdc_headers, dmdc_rows),
        "dmdc_condition_vector": (vector_headers, vector_tables["condition_input_vector"]),
        "dmdc_interaction_vector": (vector_headers, vector_tables["condition_interaction_vector"]),
    }
    robustness = summary.get("robustness", {})
    if isinstance(robustness, dict) and robustness:
        tables.update(
            {
                "robust_bootstrap_summary": generic_table(
                    robustness.get("subject_bootstrap", {}).get("layer_summary", []),
                    ["layer", "current_score", "score_mean", "score_ci_low", "score_ci_high", "rank_1_fraction", "median_rank"],
                ),
                "robust_run_sensitivity": generic_table(
                    robustness.get("run_sensitivity", {}).get("run_rows", []),
                    ["layer", "run", "support_score", "metric_count"],
                ),
                "robust_e_horizon": generic_table(
                    robustness.get("e_horizon_sensitivity", {}).get("rows", []),
                    ["layer", "horizon", "support_score", "lsd_receptor_energy_reduction_pct", "receptor_vs_random_energy_reduction_pct"],
                ),
                "robust_state_labels": generic_table(
                    robustness.get("state_label_sensitivity", {}).get("rows", []),
                    ["layer", "state_method", "state_bins", "score_mode", "support_score"],
                ),
                "robust_d_windows": generic_table(
                    robustness.get("d_window_sensitivity", {}).get("rows", []),
                    ["layer", "window_size", "support_score", "dynamic_fc_variance_delta", "global_efficiency_delta"],
                ),
                "literature_benchmark": generic_table(
                    robustness.get("literature_benchmark", {}).get("rows", []),
                    ["benchmark", "layer", "project_metric", "status", "sign_match", "observed_mean_delta", "source", "url"],
                ),
                "claim_verdicts": generic_table(
                    robustness.get("claim_verdicts", []),
                    ["claim", "verdict", "evidence", "next_action"],
                ),
            }
        )
    return tables


def export_tables(summary_path: Path = DEFAULT_SUMMARY_PATH, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, str]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    tables = _build_tables(summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for name, (headers, rows) in tables.items():
        path = output_dir / f"{name}.csv"
        _write_csv(path, headers, rows)
        written[f"{name}_csv"] = path.as_posix()
    workbook_path = output_dir / "dynamic_mechanism_results.xlsx"
    _write_xlsx(workbook_path, tables)
    written["xlsx"] = workbook_path.as_posix()
    manifest_path = output_dir / "export_manifest.json"
    manifest_path.write_text(json.dumps(written, indent=2), encoding="utf-8")
    written["manifest"] = manifest_path.as_posix()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Export dynamic mechanism AI/ML results to CSV and Excel-compatible XLSX files.")
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    written = export_tables(args.summary_path, args.output_dir)
    for label, path in written.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
