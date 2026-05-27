from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from lsd_thesis.setting_seed.data import _default_repo_root


def _load_json(path: Path, fallback: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def _load_csv_records(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    return cast(list[dict[str, Any]], frame.head(limit).to_dict(orient="records"))


def build_setting_seed_dashboard_payload(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    base = root / "results" / "setting_seed"
    data_audit = _load_json(base / "data_audit" / "data_audit.json", {"status": "missing"})
    reliability = _load_json(base / "reliability" / "reliability_table.json", [])
    latent_metrics = _load_csv_records(base / "latent" / "trajectory_metrics.csv")
    latent_coordinates = _load_csv_records(base / "latent" / "latent_coordinates.csv", limit=400)
    subject_displacements = _load_csv_records(base / "latent" / "subject_displacements.csv")
    control = _load_json(base / "control" / "control_scaffold.json", {"status": "missing"})
    motion_summary_raw = _load_json(base / "motion" / "motion_summary.json", {"status": "missing"})
    motion_summary = (
        {key: value for key, value in motion_summary_raw.items() if key != "summaries"}
        if isinstance(motion_summary_raw, dict)
        else {"status": "missing"}
    )
    setting_status = "music run analysis ready" if data_audit.get("run_02_analysis_ready") else "music run not analysis-ready"
    return {
        "title": "Set, Setting, and Seed",
        "subtitle": "Guided Latent Brain Dynamics Under LSD",
        "status": "partial_rest_only_foundation",
        "claim_guardrail": "Exploratory macro-dynamics proxy summaries, not subjective-experience simulation or biological proof.",
        "guardrail_badges": ["Not clinical", "Not subjective decoding", "Not receptor proof", "Diffusion analogy only"],
        "concept_map": [
            {"concept": "Set", "meaning": "subject baseline geometry and placebo reference", "status": "rest cache available"},
            {"concept": "Setting", "meaning": "run context and music/control input", "status": setting_status},
            {"concept": "Seed", "meaning": "initial condition and subject-specific latent state", "status": "descriptive rest geometry available"},
            {"concept": "Substance", "meaning": "LSD-minus-placebo perturbation", "status": "rest deltas available"},
            {"concept": "Guidance", "meaning": "routing, hierarchy, precision, context sensitivity", "status": "proxy targets only"},
        ],
        "data_audit": data_audit,
        "reliability": reliability,
        "latent": {
            "analysis_label": "visualization-only descriptive PCA; not subject-disjoint ML evidence",
            "trajectory_metrics": latent_metrics,
            "coordinates": latent_coordinates,
            "subject_displacements": subject_displacements,
        },
        "music_control": control,
        "motion": motion_summary,
        "mechanism_context": {
            "stage_5_non_quick_best": "thalamic_routing_only",
            "stage_5_loss": 0.762443,
            "cv5_selected": "more_cross_talk @ 0.1",
            "label": "Previous proxy-ranking artifacts, not biological proof.",
        },
        "artifact_paths": {
            "data_audit": "results/setting_seed/data_audit/data_audit.md",
            "reliability_report": "results/setting_seed/reliability/reliability_report.md",
            "latent_report": "results/setting_seed/latent/latent_report.md",
            "music_control_report": "results/setting_seed/control/music_control_report.md",
            "microsite": "output/doc/set_setting_seed_microsite.html",
        },
    }


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _metric_rows(reliability: list[dict[str, Any]]) -> str:
    if not reliability:
        return "<tr><td colspan='6'>Reliability table not generated.</td></tr>"
    rows = []
    for item in reliability:
        rows.append(
            "<tr>"
            f"<td>{_esc(item.get('metric'))}</td>"
            f"<td>{_esc(item.get('tier'))}</td>"
            f"<td>{float(item.get('mean_delta', 0.0)):.4f}</td>"
            f"<td>[{float(item.get('ci_low', 0.0)):.4f}, {float(item.get('ci_high', 0.0)):.4f}]</td>"
            f"<td>{float(item.get('sign_consistency', 0.0)):.2f}</td>"
            f"<td>{_esc(item.get('motion_sensitivity', 'unavailable'))}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_dashboard_html(payload: dict[str, Any]) -> str:
    data = cast(dict[str, Any], payload.get("data_audit", {}))
    control = cast(dict[str, Any], payload.get("music_control", {}))
    reliability = cast(list[dict[str, Any]], payload.get("reliability", []))
    control_guardrail = _esc(control.get("claim_guardrail", "No music-control empirical claim is made yet."))
    reliability_rows = _metric_rows(reliability)
    concepts = "".join(
        f"<li><strong>{_esc(item['concept'])}</strong>: {_esc(item['meaning'])} <span>{_esc(item['status'])}</span></li>"
        for item in cast(list[dict[str, Any]], payload.get("concept_map", []))
    )
    badges = "".join(f"<span class='badge'>{_esc(badge)}</span>" for badge in cast(list[str], payload.get("guardrail_badges", [])))
    run_02_command = _esc(cast(dict[str, Any], data.get("next_commands", {})).get("run_02_extraction_after_approval", "pending"))
    motion_command = _esc(cast(dict[str, Any], data.get("next_commands", {})).get("motion_summary", "pending"))
    run_02_notice = (
        "Run-02 music module time series are analysis-ready for descriptive follow-up."
        if data.get("run_02_analysis_ready")
        else "Run-02 music module time series are not analysis-ready in the current cache."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Set / Setting / Seed</title>
  <style>
    :root {{ color-scheme: light; --ink:#132019; --muted:#5b665e; --line:#d9e0da; --accent:#1f7a5a; --warn:#945b00; --bg:#f7faf7; }}
    body {{ margin:0; font-family: Inter, Segoe UI, Arial, sans-serif; color:var(--ink); background:var(--bg); line-height:1.5; }}
    header {{ padding:42px min(6vw,72px) 24px; background:#eaf2ec; border-bottom:1px solid var(--line); }}
    main {{ padding:28px min(6vw,72px) 56px; display:grid; gap:24px; }}
    section {{ border-top:1px solid var(--line); padding-top:20px; }}
    h1 {{ margin:0; font-size:clamp(2rem,4vw,4rem); letter-spacing:0; }}
    h2 {{ margin:0 0 10px; font-size:1.25rem; }}
    p {{ max-width:84ch; }}
    .badges {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
    .badge {{ border:1px solid var(--line); border-radius:999px; padding:6px 10px; background:white; font-size:.9rem; }}
    .warning {{ color:var(--warn); font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:16px; }}
    .panel {{ background:white; border:1px solid var(--line); border-radius:8px; padding:16px; }}
    table {{ width:100%; border-collapse:collapse; background:white; }}
    th, td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; font-size:.92rem; vertical-align:top; }}
    th {{ color:var(--muted); font-weight:700; }}
    code {{ background:#eef4ef; padding:2px 4px; border-radius:4px; }}
  </style>
</head>
<body>
  <header>
    <h1>Set / Setting / Seed</h1>
    <p>{_esc(payload.get('subtitle'))}</p>
    <p>{_esc(payload.get('claim_guardrail'))}</p>
    <div class="badges">{badges}</div>
  </header>
  <main>
    <section>
      <h2>Overview</h2>
      <ul>{concepts}</ul>
      <p class="warning">{_esc(run_02_notice)} Music-control analysis remains scaffolded until coverage and motion review pass.</p>
    </section>
    <section class="grid">
      <div class="panel"><h2>Data</h2><p>Subjects: {_esc(data.get('subject_count', 'unknown'))}</p><p>Runs: {_esc(', '.join(data.get('runs', [])))}</p></div>
      <div class="panel">
        <h2>Run-02 extraction support</h2>
        <p>Support: {_esc(str(data.get('run_02_extraction_support_available', False)).lower())}</p>
        <p>Data present: {_esc(str(data.get('run_02_files_present', False)).lower())}</p>
        <p>Analysis ready: {_esc(str(data.get('run_02_analysis_ready', False)).lower())}</p>
        <p><code>{run_02_command}</code></p>
      </div>
      <div class="panel">
        <h2>Motion</h2>
        <p>Support: {_esc(str(data.get('motion_summary_support_available', False)).lower())}</p>
        <p>Data present: {_esc(str(data.get('motion_files_present', False)).lower())}</p>
        <p>{_esc(data.get('analysis_availability', {}).get('motion_sensitivity', 'unavailable'))}</p>
        <p><code>{motion_command}</code></p>
      </div>
      <div class="panel"><h2>Music as Control</h2><p>{_esc(control.get('status', 'missing'))}</p><p>{control_guardrail}</p></div>
    </section>
    <section>
      <h2>Reliability Gate</h2>
      <table>
        <thead><tr><th>Metric</th><th>Tier</th><th>Delta</th><th>CI</th><th>Sign</th><th>Motion</th></tr></thead>
        <tbody>{reliability_rows}</tbody>
      </table>
    </section>
    <section>
      <h2>Latent State Space</h2>
      <p>Descriptive PCA outputs are labeled visualization-only. Full-data PCA is not used for ML claims.</p>
    </section>
    <section>
      <h2>Previous proxy-ranking artifacts</h2>
      <p>Stage 5 non-quick best: <code>thalamic_routing_only</code>. CV5 selected:
      <code>more_cross_talk @ 0.1</code>. These are proxy-ranking artifacts, not proof.</p>
    </section>
  </main>
</body>
</html>
"""


def write_dashboard_outputs(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    payload = build_setting_seed_dashboard_payload(root)
    dashboard_dir = root / "results" / "setting_seed" / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    (dashboard_dir / "dashboard_payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    html_text = render_dashboard_html(payload)
    (dashboard_dir / "index.html").write_text(html_text, encoding="utf-8")
    output_doc = root / "output" / "doc"
    output_doc.mkdir(parents=True, exist_ok=True)
    (output_doc / "set_setting_seed_microsite.html").write_text(html_text, encoding="utf-8")
    return payload
