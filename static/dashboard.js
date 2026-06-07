const pageId = document.body.dataset.page || "overview";
const dashboardDataUrl = document.body.dataset.dashboardDataUrl || "/api/dashboard-data";
const priorArtDataUrl = document.body.dataset.priorArtDataUrl || "/api/prior-art-data";
const artifactPrefix = document.body.dataset.artifactPrefix || "/artifacts/";
const deploymentMode = document.body.dataset.deploymentMode || "local";
const isStaticDeployment = deploymentMode === "static";

const chartLayout = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#edf4f1", family: "Inter, system-ui, sans-serif" },
  margin: { t: 24, r: 18, b: 46, l: 54 },
  xaxis: { gridcolor: "rgba(160,188,186,0.14)", zerolinecolor: "rgba(160,188,186,0.24)" },
  yaxis: { gridcolor: "rgba(160,188,186,0.14)", zerolinecolor: "rgba(160,188,186,0.24)" },
};

function byId(id) {
  return document.getElementById(id);
}

function text(value, fallback = "not reported") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) {
    node.className = options.className;
  }
  if (options.text !== undefined) {
    node.textContent = text(options.text, "");
  }
  if (options.href) {
    node.href = options.href;
  }
  if (options.title) {
    node.title = options.title;
  }
  for (const child of children) {
    node.append(child);
  }
  return node;
}

function setText(id, value, fallback) {
  const node = byId(id);
  if (node) {
    node.textContent = text(value, fallback);
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

function displayHref(href) {
  const value = text(href, "");
  if (value.startsWith("/artifacts/")) {
    return `${artifactPrefix}${value.slice("/artifacts/".length)}`;
  }
  return value;
}

function plot(targetId, traces, layout = {}) {
  const target = byId(targetId);
  if (!target) {
    return;
  }
  if (!window.Plotly) {
    target.textContent = "Plotly asset was not loaded.";
    return;
  }
  window.Plotly.newPlot(target, traces, { ...chartLayout, ...layout }, { displayModeBar: false, responsive: true });
}

function emptyPlot(targetId, message) {
  const target = byId(targetId);
  if (target) {
    target.textContent = message;
  }
}

function records(items) {
  return Array.isArray(items) ? items.filter((item) => item && typeof item === "object") : [];
}

function renderMetricStrip(payload) {
  const summary = payload.thesis_upgrade?.readiness_summary || {};
  const audit = payload.audit_status || {};
  const cv5 = payload.cv5_validation || {};
  const items = [
    ["Strict gates", `${text(summary.strict_complete_gates, "0")}/${text(summary.strict_total_gates, "0")}`, summary.thesis_status],
    ["Best mechanism", text(audit.stage3_best_mechanism), "current proxy ranking"],
    ["CV5 folds", `${text(cv5.completed_folds, "0")}/${text(cv5.total_folds, "0")}`, cv5.validation_claim_scope],
    ["Artifacts", text((payload.artifact_links?.reports || []).length + (payload.artifact_links?.figures || []).length), "linked derived outputs"],
  ];
  const nodes = items.map(([label, value, detail]) => el("div", { className: "data-record" }, [
    el("span", { text: label }),
    el("strong", { text: value }),
    el("p", { text: detail }),
  ]));
  byId("overview_metric_strip")?.replaceChildren(...nodes);
}

function renderGateChart(payload) {
  const requirements = records(payload.thesis_upgrade?.strict_completion_requirements);
  const complete = requirements.filter((item) => item.complete).length;
  setText("strict_gate_status", `${complete}/${requirements.length} complete`);
  plot("strict_gate_chart", [{
    type: "bar",
    x: requirements.map((item) => text(item.label)),
    y: requirements.map((item) => item.complete ? 1 : 0),
    marker: { color: requirements.map((item) => item.complete ? "#91c46c" : "#d88094") },
    hovertemplate: "%{x}<br>%{y}<extra></extra>",
  }], { yaxis: { ...chartLayout.yaxis, range: [0, 1.1], tickvals: [0, 1], ticktext: ["blocked", "complete"] } });
}

function renderReadPath() {
  const steps = [
    ["Open strict gates", "Read requirement status before interpreting any mechanism panel."],
    ["Check ranking", "Treat mechanism order as macro-dynamics proxy evidence."],
    ["Inspect robustness", "Use seed and fold spread as descriptive uncertainty."],
    ["Audit prior art", "Keep literature wrappers separate from original local analysis."],
    ["Run simulator locally", "Interactive controls are local FastAPI features, not static publication evidence."],
  ];
  byId("read_path_list")?.replaceChildren(...steps.map(([title, detail]) => el("li", {}, [
    el("strong", { text: title }),
    document.createTextNode(` - ${detail}`),
  ])));
}

function artifactRows(payload, filter = "") {
  const lowered = filter.toLowerCase();
  const rows = [];
  for (const [kind, bucket] of Object.entries(payload.artifact_links || {})) {
    for (const item of records(bucket)) {
      const label = text(item.label || item.href);
      const href = text(item.href);
      const haystack = `${kind} ${label} ${href}`.toLowerCase();
      if (!lowered || haystack.includes(lowered)) {
        rows.push([label, kind, href]);
      }
    }
  }
  return rows.slice(0, 40);
}

function fillTable(tableId, rows, builders) {
  const body = byId(tableId);
  if (!body) {
    return;
  }
  body.replaceChildren(...rows.map((row) => {
    const tr = document.createElement("tr");
    builders.forEach((builder) => tr.append(builder(row)));
    return tr;
  }));
}

function tdText(value) {
  return el("td", { text: value });
}

function tdLink(label, href) {
  const td = document.createElement("td");
  td.append(el("a", { text: label, href: displayHref(href) }));
  return td;
}

function renderArtifacts(payload) {
  const input = byId("artifact_filter");
  const draw = () => fillTable("artifact_table", artifactRows(payload, input?.value || ""), [
    (row) => tdText(row[0]),
    (row) => tdText(row[1]),
    (row) => tdLink("open", row[2]),
  ]);
  input?.addEventListener("input", draw);
  draw();
}

function renderRanking(payload) {
  const dynamic = payload.dynamic_mechanism || {};
  setText("ranking_status", dynamic.analysis_status || dynamic.status || "loaded");
  const rows = records(dynamic.mechanism_ranking || dynamic.ranking_rows || dynamic.mechanism_rows || dynamic.families);
  if (!rows.length) {
    emptyPlot("ranking_chart", "No mechanism ranking rows are available in dashboard-data.json.");
    return;
  }
  const sortedRows = [...rows].sort((left, right) => Number(left.rank ?? 999) - Number(right.rank ?? 999));
  const labels = sortedRows.map((row) => {
    const mechanism = text(row.mechanism || row.family || row.label);
    return row.layer ? `${row.layer}: ${mechanism}` : mechanism;
  });
  const scores = sortedRows.map((row) => Number(row.score ?? row.support_score ?? row.rank_score ?? 0));
  plot("ranking_chart", [{
    type: "bar",
    orientation: "h",
    x: scores,
    y: labels,
    marker: { color: ["#56d5c2", "#91c46c", "#e8bd6a", "#d88094", "#9a7be0"] },
    hovertemplate: "%{y}<br>support %{x:.3f}<extra></extra>",
  }], {
    xaxis: { ...chartLayout.xaxis, title: "proxy support score" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed" },
  });

  const gateRows = [
    ["Macro-dynamics", dynamic.analysis_status || "implemented", "Use for mechanism ranking only."],
    ["Receptor priors", payload.external_cortical_maps?.analysis_status || "exploratory", "Do not promote to receptor-level realism."],
    ["Motion controls", payload.thesis_upgrade?.components?.motion_confound?.gate?.status || "fail closed", "Downgrade if confounds remain incomplete."],
  ];
  fillTable("ranking_gate_table", gateRows, [(row) => tdText(row[0]), (row) => tdText(row[1]), (row) => tdText(row[2])]);

  const figures = records(payload.artifact_links?.figures).filter((item) => text(item.href).includes("dynamic_mechanism"));
  byId("dynamic_figure_links")?.replaceChildren(...figures.slice(0, 8).map((item) => el("a", { text: item.label || item.href, href: displayHref(item.href) })));
}

function renderRobustness(payload) {
  const summary = payload.dynamic_mechanism?.robustness || payload.stage_summaries?.stage_3 || payload.audit_status || {};
  setText("robustness_status", summary.analysis_status || "loaded");
  const layerSummary = records(payload.dynamic_mechanism?.robustness?.subject_bootstrap?.layer_summary);
  const cardItems = [
    ["Top layer", payload.dynamic_mechanism?.robustness?.subject_bootstrap?.top_layer_by_rank_1_fraction || payload.audit_status?.stage3_best_mechanism],
    ["Bootstrap rows", layerSummary.length],
    ["Run rows", records(payload.dynamic_mechanism?.robustness?.run_sensitivity?.run_rows).length],
    ["CV5 status", payload.cv5_validation?.analysis_status || payload.cv5_validation?.status],
  ];
  byId("robustness_cards")?.replaceChildren(...cardItems.map(([label, value]) => el("div", { className: "data-record" }, [
    el("span", { text: label }),
    el("strong", { text: text(value) }),
  ])));
  if (!layerSummary.length) {
    emptyPlot("robustness_chart", "No bootstrap layer summary is available in robustness_summary.json.");
    return;
  }
  plot("robustness_chart", [{
    type: "bar",
    name: "rank-1 fraction",
    x: layerSummary.map((row) => text(row.layer)),
    y: layerSummary.map((row) => Number(row.rank_1_fraction ?? 0)),
    customdata: layerSummary.map((row) => [Number(row.score_mean ?? 0), Number(row.score_std ?? 0)]),
    marker: { color: ["#56d5c2", "#d88094", "#91c46c", "#e8bd6a", "#9a7be0"] },
    hovertemplate: "Layer %{x}<br>rank-1 %{y:.3f}<br>score mean %{customdata[0]:.3f}<br>score sd %{customdata[1]:.3f}<extra></extra>",
  }], { yaxis: { ...chartLayout.yaxis, title: "bootstrap rank-1 fraction", range: [0, 1] } });

  const requirements = records(payload.thesis_upgrade?.strict_completion_requirements);
  fillTable("requirements_table", requirements, [
    (row) => tdText(row.label),
    (row) => tdText(row.status),
    (row) => tdText(row.complete ? "complete" : row.missing || row.next_action),
  ]);
}

function priorArtRows(payload, filter = "") {
  const lowered = filter.toLowerCase();
  return records(payload.sources).filter((row) => {
    const haystack = `${row.family} ${row.name} ${row.status} ${row.role}`.toLowerCase();
    return !lowered || haystack.includes(lowered);
  });
}

function renderPriorArt(payload) {
  setText("prior_art_status", `${payload.summary?.family_count || 0} families`);
  const cards = records(payload.families).map((item) => el("div", { className: "data-record" }, [
    el("span", { text: item.family }),
    el("strong", { text: item.claim_status }),
    el("p", { text: item.connection }),
  ]));
  byId("prior_art_cards")?.replaceChildren(...cards);
  const input = byId("prior_art_filter");
  const draw = () => fillTable("prior_art_table", priorArtRows(payload, input?.value || ""), [
    (row) => tdText(row.family),
    (row) => tdText(row.name),
    (row) => tdText(row.status),
    (row) => tdText(row.commit_or_policy),
  ]);
  input?.addEventListener("input", draw);
  draw();
}

function renderEmpirical(payload) {
  const overview = payload.empirical_viewer || {};
  const subjects = Array.isArray(overview.subjects) ? overview.subjects : [];
  const runs = Array.isArray(overview.runs) ? overview.runs : [];
  setText("empirical_status", subjects.length ? "viewer cache ready" : "viewer cache missing");
  byId("empirical_subject")?.replaceChildren(...subjects.map((subject) => el("option", { text: subject })));
  byId("empirical_run")?.replaceChildren(...runs.map((run) => el("option", { text: run })));
  if (overview.default_subject && byId("empirical_subject")) {
    byId("empirical_subject").value = overview.default_subject;
  }
  if (overview.default_run && byId("empirical_run")) {
    byId("empirical_run").value = overview.default_run;
  }
  const deltas = payload.empirical?.target_deltas || {};
  plot("empirical_delta_chart", [{
    type: "bar",
    x: Object.keys(deltas),
    y: Object.values(deltas),
    marker: { color: Object.values(deltas).map((value) => Number(value) >= 0 ? "#56d5c2" : "#d88094") },
    hovertemplate: "%{x}<br>delta %{y:.3f}<extra></extra>",
  }], { yaxis: { ...chartLayout.yaxis, title: "LSD minus placebo proxy delta" } });
}

async function loadEmpiricalDetail() {
  if (isStaticDeployment) {
    setText("empirical_notice", "Static GitHub Pages shows the group delta plot; subject-level detail requires the local FastAPI dashboard.");
    return;
  }
  const subject = byId("empirical_subject")?.value;
  const run = byId("empirical_run")?.value;
  if (!subject || !run) {
    setText("empirical_notice", "No empirical selector is available.");
    return;
  }
  try {
    const detail = await fetchJson(`/api/empirical-view?subject=${encodeURIComponent(subject)}&run=${encodeURIComponent(run)}`);
    setText("empirical_notice", detail.run_caveat || detail.viewer_source || "Subject detail loaded.");
    const windows = records(detail.window_deltas);
    const first = windows[0]?.metrics || {};
    const rows = Object.entries(first).map(([metric, value]) => [metric, "window", "window", Number(value).toFixed(4)]);
    fillTable("empirical_detail_table", rows, [(row) => tdText(row[0]), (row) => tdText(row[1]), (row) => tdText(row[2]), (row) => tdText(row[3])]);
  } catch (error) {
    setText("empirical_notice", error.message);
  }
}

function renderSimulationPayload(payload) {
  const modules = payload.modules || [];
  const time = payload.time || [];
  const traces = modules.map((module, index) => ({
    type: "scatter",
    mode: "lines",
    name: module,
    x: time,
    y: (payload.time_series || []).map((row) => row[index]),
  }));
  plot("sim_time_chart", traces, { yaxis: { ...chartLayout.yaxis, title: "z-scored model activity" } });
  plot("sim_fc_chart", [{
    type: "heatmap",
    x: modules,
    y: modules,
    z: payload.fc_matrix || [],
    colorscale: [[0, "#d88094"], [0.5, "#151d22"], [1, "#56d5c2"]],
    zmid: 0,
  }], { xaxis: { ...chartLayout.xaxis, side: "top" } });
}

async function runSimulation(dashboard = {}) {
  const body = {
    regime: byId("sim_regime")?.value || "baseline",
    within_group_scale: Number(byId("sim_within")?.value || 1),
    cross_group_scale: Number(byId("sim_cross")?.value || 1),
    constraint_scale: Number(byId("sim_constraint")?.value || 1),
    temperature: Number(byId("sim_temperature")?.value || 0.1),
  };
  if (isStaticDeployment) {
    const payload = body.regime === "perturbed" ? dashboard.perturbed : dashboard.baseline;
    if (!payload) {
      setText("simulator_status", "static snapshot missing");
      return;
    }
    renderSimulationPayload(payload);
    setText("simulator_status", `static ${body.regime} snapshot`);
    return;
  }
  setText("simulator_status", "running");
  const response = await fetch("/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    setText("simulator_status", `error ${response.status}`);
    return;
  }
  const payload = await response.json();
  setText("simulator_status", "rendered");
  renderSimulationPayload(payload);
}

async function main() {
  const dashboard = await fetchJson(dashboardDataUrl);
  if (pageId === "overview") {
    renderMetricStrip(dashboard);
    renderGateChart(dashboard);
    renderReadPath();
    renderArtifacts(dashboard);
  } else if (pageId === "mechanism_ranking") {
    renderRanking(dashboard);
  } else if (pageId === "robustness") {
    renderRobustness(dashboard);
  } else if (pageId === "prior_art") {
    renderPriorArt(await fetchJson(priorArtDataUrl));
  } else if (pageId === "empirical") {
    renderEmpirical(dashboard);
    byId("load_empirical")?.addEventListener("click", loadEmpiricalDetail);
  } else if (pageId === "simulator") {
    if (isStaticDeployment) {
      ["sim_within", "sim_cross", "sim_constraint", "sim_temperature"].forEach((id) => {
        const input = byId(id);
        if (input) {
          input.disabled = true;
          input.title = "Static GitHub Pages uses cached baseline/perturbed snapshots; parameter sweeps require the local FastAPI dashboard.";
        }
      });
      const button = byId("run_simulation");
      if (button) {
        button.textContent = "Render Cached Regime";
      }
    }
    await runSimulation(dashboard);
    byId("run_simulation")?.addEventListener("click", () => runSimulation(dashboard));
  }
}

main().catch((error) => {
  const target = byId(`${pageId}_status`) || byId("strict_gate_status") || byId("simulator_status");
  if (target) {
    target.textContent = error.message;
  }
});
