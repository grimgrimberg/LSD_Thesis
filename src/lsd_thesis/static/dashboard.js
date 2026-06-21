const pageId = document.body.dataset.page || "overview";
const dashboardDataUrl = document.body.dataset.dashboardDataUrl || "/api/dashboard-data";
const priorArtDataUrl = document.body.dataset.priorArtDataUrl || "/api/prior-art-data";
const artifactPrefix = document.body.dataset.artifactPrefix || "/artifacts/";
const deploymentMode = document.body.dataset.deploymentMode || "local";
const isStaticDeployment = deploymentMode === "static";

const COLORS = {
  bg: "#0b1014",
  panel: "#101820",
  grid: "rgba(172, 190, 186, 0.18)",
  text: "#eef4f1",
  muted: "#98aaa5",
  teal: "#49d6c8",
  amber: "#e3ba4f",
  moss: "#93c66d",
  rose: "#e47d93",
  violet: "#9a8fd3",
  gray: "#3b444b",
};

const layerColor = {
  A: COLORS.violet,
  B: COLORS.rose,
  C: COLORS.teal,
  D: COLORS.moss,
  E: COLORS.amber,
};

const JARGON_GLOSSARY = {
  "finite-horizon discrete network-control energy": "Model-level control effort needed to move between coarse proxy states.",
  "dmdc condition interaction": "Linear baseline: how much a condition term accounts for module-level activity.",
  "dynamic repertoire": "How much module-level network patterns vary over time.",
  "hierarchy routing": "How proxy module activity follows the hierarchy or constraint structure.",
  "transition proxy": "How often coarse module-state labels change and how long they persist.",
  "transition state proxy": "How often coarse module-state labels change and how long they persist."
};

const chartLayout = {
  autosize: true,
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: COLORS.text, family: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" },
  margin: { t: 28, r: 22, b: 54, l: 72 },
  hoverlabel: { bgcolor: "#111a20", bordercolor: "rgba(255,255,255,0.18)", font: { color: COLORS.text } },
  legend: { orientation: "h", y: -0.18, x: 0, font: { color: COLORS.muted } },
  xaxis: { gridcolor: COLORS.grid, zerolinecolor: "rgba(255,255,255,0.28)", automargin: true },
  yaxis: { gridcolor: COLORS.grid, zerolinecolor: "rgba(255,255,255,0.28)", automargin: true },
};

const chartConfig = {
  displayModeBar: true,
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"],
  toImageButtonOptions: {
    format: "png",
    filename: `lsd-thesis-${pageId}`,
    scale: 2,
  },
};

let dashboardPayload = null;
let priorArtPayload = null;
let empiricalDetailState = {
  detail: null,
  windows: [],
  rawRecord: null,
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

function titleText(value) {
  return text(value, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function asRecords(items) {
  return Array.isArray(items) ? items.filter((item) => item && typeof item === "object") : [];
}

function asStringList(items) {
  return Array.isArray(items) ? items.map((item) => text(item, "")).filter(Boolean) : [];
}

function finiteNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatNumber(value, digits = 3) {
  const number = finiteNumber(value);
  if (number === null) {
    return "N/A";
  }
  if (Math.abs(number) >= 100) {
    return number.toFixed(1);
  }
  if (Math.abs(number) >= 10) {
    return number.toFixed(2);
  }
  return number.toFixed(digits);
}

function sanitizeSeries(values) {
  let invalidCount = 0;
  const clean = (Array.isArray(values) ? values : []).map((value) => {
    const number = finiteNumber(value);
    if (number === null) {
      invalidCount += 1;
      return null;
    }
    return number;
  });
  return { values: clean, invalidCount };
}

function sanitizeMatrix(matrix) {
  let invalidCount = 0;
  const clean = (Array.isArray(matrix) ? matrix : []).map((row) => (
    (Array.isArray(row) ? row : []).map((value) => {
      const number = finiteNumber(value);
      if (number === null) {
        invalidCount += 1;
        return null;
      }
      return number;
    })
  ));
  return { values: clean, invalidCount };
}

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = text(options.text, "");
  if (options.href) node.href = options.href;
  if (options.title) node.title = options.title;
  if (options.type) node.type = options.type;
  if (options.role) node.setAttribute("role", options.role);
  if (options.ariaSelected !== undefined) node.setAttribute("aria-selected", String(options.ariaSelected));
  if (options.disabled) node.disabled = true;
  for (const child of children) node.append(child);
  return node;
}

function setText(id, value, fallback) {
  const node = byId(id);
  if (node) node.textContent = text(value, fallback);
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

function setLoading(targetId, message = "Loading...") {
  const target = byId(targetId);
  if (!target) return;
  target.textContent = message;
  const frame = target.closest(".chart-frame");
  const panel = target.closest(".panel");
  frame?.classList.add("is-loading");
  panel?.setAttribute("aria-busy", "true");
}

function clearLoading(target) {
  const frame = target.closest(".chart-frame");
  const panel = target.closest(".panel");
  frame?.classList.remove("is-loading");
  panel?.removeAttribute("aria-busy");
}

function invalidAnnotation(count) {
  if (!count) return [];
  return [{
    x: 1,
    y: 1.12,
    xref: "paper",
    yref: "paper",
    xanchor: "right",
    showarrow: false,
    text: `${count} invalid values shown as N/A`,
    font: { color: COLORS.amber, size: 11 },
  }];
}

function compactLayoutForTarget(target, layout) {
  const targetWidth = target.clientWidth || target.getBoundingClientRect().width || 0;
  if (targetWidth >= 480) {
    return {};
  }
  const baseMargin = layout.margin || chartLayout.margin;
  const labelMargin = Math.min(
    Math.max(baseMargin.l ?? chartLayout.margin.l, 104),
    Math.floor(targetWidth * 0.42),
  );
  return {
    margin: {
      t: Math.min(baseMargin.t ?? chartLayout.margin.t, 20),
      r: Math.min(baseMargin.r ?? chartLayout.margin.r, 12),
      b: Math.max(baseMargin.b ?? chartLayout.margin.b, 58),
      l: labelMargin,
    },
    legend: {
      ...chartLayout.legend,
      ...(layout.legend || {}),
      y: Math.min((layout.legend || chartLayout.legend).y ?? chartLayout.legend.y, -0.28),
    },
  };
}

function plot(targetId, traces, layout = {}, options = {}) {
  const target = byId(targetId);
  if (!target) return;
  if (!window.Plotly) {
    target.textContent = "Plotly asset was not loaded. Use the linked source artifact or table.";
    return;
  }
  const annotations = [
    ...(layout.annotations || []),
    ...invalidAnnotation(layout.invalidCount || 0),
  ];
  const nextLayout = {
    ...chartLayout,
    ...layout,
    ...compactLayoutForTarget(target, layout),
    annotations,
  };
  delete nextLayout.invalidCount;
  target.classList.remove("chart-empty");
  clearLoading(target);
  target.textContent = "";
  target.dataset.plotlyRendered = "true";
  const nextConfig = { ...chartConfig, ...(options.config || {}) };
  if ((target.clientWidth || target.getBoundingClientRect().width || 0) < 480 && options.config?.displayModeBar === undefined) {
    nextConfig.displayModeBar = false;
  }
  window.Plotly.react(target, traces, nextLayout, nextConfig);
  window.requestAnimationFrame(() => window.Plotly.Plots?.resize?.(target));
}

function emptyPlot(targetId, message) {
  const target = byId(targetId);
  if (!target) return;
  clearLoading(target);
  target.classList.add("chart-empty");
  target.textContent = message;
}

function purgeCharts(container) {
  if (!container || !window.Plotly) return;
  container.querySelectorAll(".chart").forEach((node) => {
    if (node.dataset.plotlyRendered === "true") {
      window.Plotly.purge(node);
      delete node.dataset.plotlyRendered;
    }
  });
}

function statusClass(status) {
  const value = text(status, "").toLowerCase();
  if (value.includes("implement") || value.includes("support") || value.includes("aligned") || value.includes("complete")) {
    return "status-token--teal";
  }
  if (value.includes("mixed") || value.includes("proxy") || value.includes("future") || value.includes("missing")) {
    return "status-token--amber";
  }
  if (value.includes("block") || value.includes("reject") || value.includes("unsupported") || value.includes("not_")) {
    return "status-token--rose";
  }
  return "status-token--moss";
}

function localPageHref(href) {
  const value = text(href, "");
  if (!value || !isStaticDeployment || !value.startsWith("/")) {
    return value;
  }
  const staticMap = {
    "/": "index.html",
    "/overview": "index.html",
    "/ranking": "ranking.html",
    "/robustness": "robustness.html",
    "/prior-art": "prior-art.html",
    "/empirical": "empirical.html",
    "/simulator": "simulator.html",
    "/submission": "submission.html",
    "/thesis": "thesis.html",
    "/figures": "figures.html",
  };
  return staticMap[value] || value.replace(/^\//, "");
}

function figureExplainer(payload, plotId) {
  return payload?.figure_explainers?.[plotId] || null;
}

function artifactNode(item) {
  const label = text(item.label || item.path, "source artifact");
  const path = text(item.path, "");
  const href = text(item.href, "");
  const children = [
    href
      ? el("a", { text: label, href: displayHref(href) })
      : el("span", { text: label }),
  ];
  if (path) {
    children.push(el("code", { text: path }));
  }
  if (item.public === false) {
    children.push(el("small", { text: "not public-linked" }));
  }
  return el("li", {}, children);
}

function explainerField(label, value) {
  return el("div", { className: "figure-explainer-field" }, [
    el("span", { text: label }),
    el("p", { text: value }),
  ]);
}

function renderFigureExplainer(containerId, plotId, payload) {
  const container = byId(containerId);
  if (!container) return;
  const explainer = figureExplainer(payload, plotId);
  if (!explainer) {
    container.replaceChildren();
    return;
  }
  const artifacts = asRecords(explainer.input_artifacts);
  const details = el("details", { className: "figure-explainer" }, [
    el("summary", {}, [
      el("span", { text: "How this plot was calculated" }),
      el("strong", { className: `mini-status ${statusClass(explainer.claim_status)}`, text: explainer.claim_status }),
    ]),
    el("div", { className: "figure-explainer-grid" }, [
      explainerField("Source", explainer.subtitle),
      explainerField("Metric", explainer.metric_definition),
      explainerField("Aggregation", explainer.aggregation_level),
      explainerField("Formula / rule", explainer.calculation || explainer.formula_summary),
      explainerField("Caveat", explainer.caveat),
    ]),
    el("ul", { className: "source-list" }, artifacts.map(artifactNode)),
  ]);
  container.replaceChildren(details);
}

function renderEvidenceFlow(payload) {
  const container = byId("evidence_flow");
  if (!container) return;
  const flow = payload.evidence_flow || {};
  const nodes = asRecords(flow.nodes);
  if (!nodes.length) {
    container.replaceChildren(el("p", { className: "microcopy", text: "Evidence flow metadata is not available." }));
    return;
  }
  const cards = [];
  nodes.forEach((node, index) => {
    const source = asRecords(node.artifacts)[0];
    cards.push(el("article", { className: "evidence-node" }, [
      el("span", { className: "evidence-node__step", text: String(index + 1) }),
      el("strong", { text: node.label || node.title }),
      el("small", { className: `mini-status ${statusClass(node.claim_status)}`, text: node.claim_status }),
      el("p", { text: node.detail || node.status }),
      source?.href
        ? el("a", { className: "evidence-node__source", text: source.label || "source", href: displayHref(source.href) })
        : el("code", { text: source?.path || "source path pending" }),
    ]));
    if (index < nodes.length - 1) {
      cards.push(el("span", { className: "evidence-edge", text: "->" }));
    }
  });
  container.replaceChildren(
    el("p", { className: "evidence-flow-title", text: flow.title || "Evidence pipeline" }),
    el("div", { className: "evidence-flow-track" }, cards),
    el("p", { className: "microcopy", text: flow.guardrail }),
  );
}

function renderFigureDeck(payload) {
  const deck = payload.figure_deck || {};
  const figures = asRecords(deck.figures);
  setText("figure_deck_subtitle", deck.subtitle || "Figure metadata is generated from dashboard-data.json.");
  setText("figures_status", `${figures.length} figures`);
  renderUnitGuide("figure_unit_cards");
  renderPitchLinks("figure_atlas_links");
  byId("figure_deck_status_cards")?.replaceChildren(
    ...asRecords(deck.status_cards).map((item) => dataRecord(item.label, item.value, "production gate", item.claim_status)),
  );
  byId("figure_deck_cards")?.replaceChildren(...figures.map((figure, index) => {
    const artifacts = asRecords(figure.input_artifacts);
    const exportHref = text(figure.export_href || figure.export_target?.href, "");
    const pageHref = localPageHref(figure.page_href || "/figures");
    const actions = [
      pageHref ? el("a", { text: "Open page", href: pageHref }) : null,
      exportHref ? el("a", { text: "Open export", href: displayHref(exportHref) }) : null,
    ].filter(Boolean);
    return el("article", { className: "figure-card" }, [
      el("div", { className: "figure-card__index", text: `F${index + 1}` }),
      el("div", { className: "figure-card__body" }, [
        el("div", { className: "panel-heading figure-card__heading" }, [
          el("h3", { text: figure.title }),
          el("span", { className: `status-token ${statusClass(figure.claim_status)}`, text: figure.claim_status }),
        ]),
        el("p", { text: figure.subtitle }),
        el("div", { className: "figure-explainer-grid" }, [
          explainerField("Metric", figure.metric_definition),
          explainerField("Aggregation", figure.aggregation_level),
          explainerField("Formula / rule", figure.calculation || figure.formula_summary),
          explainerField("Caveat", figure.caveat),
        ]),
        el("ul", { className: "source-list" }, artifacts.map(artifactNode)),
        el("div", { className: "button-row" }, actions),
      ]),
    ]);
  }));
}

function getJargonSubtitle(textContent) {
  const t = text(textContent, "").toLowerCase();
  for (const [key, explainer] of Object.entries(JARGON_GLOSSARY)) {
    if (t.includes(key)) return explainer;
  }
  return null;
}

function dataRecord(label, value, detail, status) {
  const children = [
    el("span", { text: label }),
    el("strong", { text: value }),
  ];

  const subtitle = getJargonSubtitle(label) || getJargonSubtitle(value);
  if (subtitle) {
    children.push(el("span", { className: "explainer-subtitle", text: subtitle }));
  }

  if (detail) children.push(el("p", { text: detail }));
  if (status) children.push(el("span", { className: `mini-status ${statusClass(status)}`, text: status }));

  return el("div", { className: "data-record" }, children);
}

function tdText(value) {
  return el("td", { text: value });
}

function tdNumber(value) {
  return el("td", { text: formatNumber(value) });
}

function tdCode(value) {
  const td = document.createElement("td");
  td.append(el("code", { text: value }));
  return td;
}

function tdLink(label, href) {
  const td = document.createElement("td");
  const normalized = displayHref(href);
  if (!normalized) {
    td.textContent = "N/A";
    return td;
  }
  td.append(el("a", { text: label, href: normalized }));
  return td;
}

function fillTable(tableId, rows, builders, emptyMessage = "No rows available.") {
  const body = byId(tableId);
  if (!body) return;
  const cleanRows = Array.isArray(rows) ? rows : [];
  if (!cleanRows.length) {
    const tr = document.createElement("tr");
    const td = el("td", { text: emptyMessage });
    td.colSpan = builders.length || 1;
    tr.append(td);
    body.replaceChildren(tr);
    return;
  }
  body.replaceChildren(...cleanRows.map((row) => {
    const tr = document.createElement("tr");
    builders.forEach((builder) => tr.append(builder(row)));
    return tr;
  }));
}

function artifactRows(payload, filter = "") {
  const lowered = filter.toLowerCase();
  const rows = [];
  for (const [kind, bucket] of Object.entries(payload.artifact_links || {})) {
    for (const item of asRecords(bucket)) {
      const label = text(item.label || item.href);
      const href = text(item.href);
      const haystack = `${kind} ${label} ${href}`.toLowerCase();
      if (!lowered || haystack.includes(lowered)) rows.push([label, kind, href]);
    }
  }
  return rows.slice(0, 80);
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

function benchmarkRows(payload) {
  return asRecords(payload.dynamic_mechanism?.literature_benchmark?.rows);
}

function renderMetricStrip(payload) {
  const summary = payload.thesis_upgrade?.readiness_summary || {};
  const audit = payload.audit_status || {};
  const dynamic = payload.dynamic_mechanism || {};
  const literature = dynamic.literature_benchmark || {};
  const items = [
    ["Strict gates", `${text(summary.strict_complete_gates, "0")}/${text(summary.strict_total_gates, "0")}`, summary.thesis_status],
    ["Best layer", text(audit.stage3_best_mechanism || dynamic.mechanism_ranking?.[0]?.layer), "current proxy ranking"],
    ["Benchmark match", `${text(literature.aligned_count, "0")}/${text(literature.measurable_count, "0")}`, "directional literature rows"],
    ["Subjects", text(dynamic.subject_count || payload.empirical_viewer?.paired_subject_count), "paired cached records"],
  ];
  return items.map(([label, value, detail]) => dataRecord(label, value, detail));
}

function renderOverviewMetricStrip(payload) {
  byId("overview_metric_strip")?.replaceChildren(...renderMetricStrip(payload));
}

function staticRootPrefix() {
  if (!isStaticDeployment) return "";
  return dashboardDataUrl === "dashboard-data.json" ? "../" : "";
}

function piReviewHref(path = "") {
  if (!isStaticDeployment) return "/thesis";
  return `${staticRootPrefix()}pi-review/${path}`;
}

function unitGuideItems() {
  return [
    ["Support score", "unitless", "Weighted proxy-support score from current artifacts; higher means stronger current alignment for a layer, not biological proof."],
    ["Rank-1 fraction", "0-1 proportion", "Subject-bootstrap fraction where the layer ranked first; 0.844 means 84.4% of resamples ranked it first."],
    ["LSD - placebo delta", "metric-native difference", "Paired condition difference. Most macro-dynamic metrics are unitless proxy summaries unless the artifact defines a physical unit."],
    ["FC delta", "correlation-unit difference", "Signed change in functional connectivity. It is unitless and should not be read as activation magnitude."],
    ["Energy reduction", "percent", "Relative network-control proxy reduction. Keep this separate from receptor-specific placement claims."],
    ["TR / horizon", "TR count / model steps", "Window size is counted in TRs; finite horizon is counted in model steps. Neither is a biological time constant."],
  ];
}

function renderUnitGuide(containerId) {
  byId(containerId)?.replaceChildren(
    ...unitGuideItems().map(([label, value, detail]) => dataRecord(label, value, detail, "proxy-supported")),
  );
}

function pitchCardItems(payload = {}) {
  const dynamic = payload.dynamic_mechanism || {};
  const topLayer = dynamic.mechanism_ranking?.[0]?.layer || "C";
  const summary = payload.thesis_upgrade?.readiness_summary || {};
  const strict = `${text(summary.strict_complete_gates, "4")}/${text(summary.strict_total_gates, "6")}`;
  return [
    ["Interdisciplinary fit", "AI + control theory + fMRI", "The project connects subject-disjoint ML, graph/control priors, and psychedelic macro-dynamics in one inspectable workbench."],
    ["Research judgment", "claim-gated", "Implemented, proxy-supported, mixed, unsupported, blocked, and future claims stay visibly separated."],
    ["Engineering proof", "tested dashboard + artifacts", "FastAPI/Jinja/Plotly surfaces consume typed Python payloads, allowlisted artifacts, and regression-tested public JSON contracts."],
    ["Current result", `top layer ${topLayer}`, "The current A-E ranking is shown as model-level proxy evidence, with B retained as a negative baseline."],
    ["Falsification posture", `${strict} strict gates`, "The pitch shows what would weaken the claim instead of hiding blockers such as motion/confound proof."],
    ["Supervisor ask", "next threshold", "The package asks for the next blocker and the evidence threshold for promoting proxy support into a thesis-level claim."],
  ];
}

function renderPitchCards(containerId, payload) {
  byId(containerId)?.replaceChildren(
    ...pitchCardItems(payload).map(([label, value, detail]) => dataRecord(label, value, detail, "implemented")),
  );
}

function renderPitchLinks(containerId) {
  const links = [
    ["Submission brief", isStaticDeployment ? `${staticRootPrefix()}submission.html` : "/submission"],
    ["Open hosted PI package", piReviewHref()],
    ["Pitch slides", piReviewHref("pages/pitch-slides.html")],
    ["Figure atlas", piReviewHref("pages/figure-atlas.html")],
    ["All figure metadata", isStaticDeployment ? `${staticRootPrefix()}figures.html` : "/figures"],
  ];
  byId(containerId)?.replaceChildren(...links.map(([label, href]) => el("a", { className: "secondary-link", text: label, href })));
}

function statusBalanceRows(payload) {
  const counts = new Map();
  const add = (value) => {
    const key = text(value, "").toLowerCase().replace(/\s+/g, "_") || "unknown";
    counts.set(key, (counts.get(key) || 0) + 1);
  };
  asRecords(payload.dynamic_mechanism?.claim_verdicts).forEach((row) => add(row.verdict));
  asRecords(payload.thesis_upgrade?.strict_completion_requirements).forEach((row) => add(row.complete ? "complete" : row.status || "blocked"));
  return [...counts.entries()].map(([status, count]) => ({ status, count }));
}

function renderStatusBalance(payload, targetId = "thesis_status_balance_chart") {
  const rows = statusBalanceRows(payload);
  if (!rows.length) {
    emptyPlot(targetId, "No claim or gate status rows are available.");
    return;
  }
  plot(targetId, [{
    type: "bar",
    x: rows.map((row) => titleText(row.status)),
    y: rows.map((row) => row.count),
    marker: { color: rows.map((row) => row.status.includes("block") || row.status.includes("unsupported") ? COLORS.rose : row.status.includes("mixed") ? COLORS.amber : COLORS.teal) },
    text: rows.map((row) => String(row.count)),
    textposition: "auto",
    hovertemplate: "%{x}<br>%{y} items<extra></extra>",
  }], {
    margin: { t: 12, r: 18, b: 72, l: 58 },
    xaxis: { ...chartLayout.xaxis, title: "Status label" },
    yaxis: { ...chartLayout.yaxis, title: "Count of claims/gates" },
  });
}

function mechanismRankingRows(payload) {
  return asRecords(payload.dynamic_mechanism?.mechanism_ranking)
    .sort((left, right) => Number(left.rank ?? 999) - Number(right.rank ?? 999));
}

function bootstrapLayerSummary(payload, layer) {
  return asRecords(payload.dynamic_mechanism?.robustness?.subject_bootstrap?.layer_summary)
    .find((row) => text(row.layer, "") === layer) || {};
}

function layerRankingRecord(payload, layer) {
  return mechanismRankingRows(payload).find((row) => text(row.layer, "") === layer) || {};
}

function scoreWithUnit(row) {
  return `unitless support score ${formatNumber(row.score)}`;
}

function rankOneFraction(payload, layer) {
  const summary = bootstrapLayerSummary(payload, layer);
  const fraction = finiteNumber(summary.rank_1_fraction);
  return fraction === null ? "rank-1 fraction not reported" : `bootstrap rank-1 fraction ${formatNumber(fraction)}`;
}

function renderSubmissionInsights(payload) {
  const top = mechanismRankingRows(payload)[0] || {};
  const layerB = layerRankingRecord(payload, "B");
  const layerE = layerRankingRecord(payload, "E");
  const cv5 = payload.cv5_validation || {};
  const readiness = payload.thesis_upgrade?.readiness_summary || {};
  const strictLabel = `${text(readiness.strict_complete_gates, "0")}/${text(readiness.strict_total_gates, "0")} strict gates`;
  const cards = [
    [
      "Top current proxy",
      `${text(top.layer, "C")} ${titleText(top.mechanism)}`,
      `${scoreWithUnit(top)}; ${rankOneFraction(payload, text(top.layer, "C"))}. This is macro-dynamics proxy evidence, not biological mechanism proof.`,
      text(top.status, "implemented"),
    ],
    [
      "E layer interpretation",
      scoreWithUnit(layerE),
      "Current E evidence supports a lower transition/control-energy proxy. Receptor-specific placement remains separated from that proxy claim.",
      text(layerE.status, "proxy-supported"),
    ],
    [
      "Negative baseline",
      scoreWithUnit(layerB),
      `${rankOneFraction(payload, "B")}. B is retained as a predictive/control baseline instead of a control-energy mechanism claim.`,
      text(layerB.status, "implemented"),
    ],
    [
      "Internal validation",
      `${text(cv5.completed_folds, "0")}/${text(cv5.total_folds, "0")} CV5 folds`,
      text(cv5.claim_guardrail, "Subject-disjoint CV5 is internal validation only, not external or clinical validation."),
      text(cv5.status, "complete"),
    ],
    [
      "Remaining blockers",
      strictLabel,
      text(readiness.remaining_hard_requirements?.join?.(", "), "Motion/confound proof and final thesis/package thresholds remain explicit blockers."),
      "blocked",
    ],
  ];
  byId("submission_insight_cards")?.replaceChildren(
    ...cards.map(([label, value, detail, status]) => dataRecord(label, value, detail, status)),
  );
}

function renderSubmissionMechanismChart(payload) {
  const rows = mechanismRankingRows(payload);
  if (!rows.length) {
    emptyPlot("submission_mechanism_chart", "No mechanism ranking rows are available.");
    return;
  }
  const scores = sanitizeSeries(rows.map((row) => row.score));
  plot("submission_mechanism_chart", [{
    type: "bar",
    orientation: "h",
    x: scores.values,
    y: rows.map((row) => `${text(row.layer)}: ${titleText(row.mechanism)}`),
    marker: { color: rows.map((row) => layerColor[text(row.layer, "")] || COLORS.teal) },
    text: scores.values.map((value) => formatNumber(value)),
    textposition: "auto",
    customdata: rows.map((row) => [text(row.status), text(row.evidence)]),
    hovertemplate: "%{y}<br>unitless support score %{x:.3f}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
  }], {
    invalidCount: scores.invalidCount,
    margin: { t: 10, r: 20, b: 46, l: 190 },
    xaxis: { ...chartLayout.xaxis, title: "Proxy Support Score (unitless)" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Mechanism Layer" },
  });
}

function renderSubmissionDecisionMatrix(payload) {
  const top = mechanismRankingRows(payload)[0] || {};
  const rows = [
    [
      "Ready to show",
      "Working evidence dashboard",
      "Static Pages, local FastAPI dashboard, artifact links, figure deck, and claim gates are inspectable.",
      "implemented",
    ],
    [
      "Ready as proxy evidence",
      `${text(top.layer, "C")} mechanism ranking`,
      "Use as model-level macro-dynamic ranking evidence with explicit units and status labels.",
      "proxy-supported",
    ],
    [
      "Needs supervisor threshold",
      "Motion/confound and thesis gate priorities",
      "The next research decision is which blocker must be closed first before stronger thesis language is acceptable.",
      "blocked",
    ],
    [
      "Do not claim",
      "Subjective, receptor-level, or clinical validity",
      "The dashboard deliberately keeps these as unsupported, blocked, or future work unless new approved evidence changes the gate.",
      "unsupported",
    ],
  ];
  byId("submission_decision_matrix")?.replaceChildren(
    ...rows.map(([label, value, detail, status]) => dataRecord(label, value, detail, status)),
  );
}

function renderSubmissionTour() {
  const steps = [
    ["Overview", "/", "Start with strict gates, claim cards, and the dashboard evidence path."],
    ["Mechanism Ranking", "/ranking", "Read unitless proxy support scores and the A-E layer order."],
    ["Robustness", "/robustness", "Check bootstrap, run, horizon, and window sensitivity before interpreting C or E."],
    ["Empirical Viewer", "/empirical", "Inspect paired LSD/placebo module summaries and metric-native deltas."],
    ["Prior Art", "/prior-art", "Keep literature wrappers separate from original local analysis."],
    ["Figure Deck", "/figures", "Use figure-level metadata, calculation notes, caveats, and source artifacts."],
  ];
  byId("submission_dashboard_tour")?.replaceChildren(...steps.map(([title, href, detail], index) => el("section", { className: "story-step" }, [
    el("span", { text: String(index + 1) }),
    el("div", {}, [
      el("strong", { text: title }),
      el("p", { text: detail }),
      el("a", { text: "Open", href: localPageHref(href) }),
    ]),
  ])));
}

function renderSubmissionArtifactLinks(payload) {
  const reportRows = artifactRows(payload).filter((row) => row[1] === "reports");
  const links = [
    ["Hosted dashboard overview", isStaticDeployment ? `${staticRootPrefix()}dashboard/` : "/"],
    ["Submission brief", isStaticDeployment ? `${staticRootPrefix()}submission.html` : "/submission"],
    ["PI review package", piReviewHref()],
    ["Pitch slides", piReviewHref("pages/pitch-slides.html")],
    ["Figure atlas", piReviewHref("pages/figure-atlas.html")],
    ["Evidence and calculations", piReviewHref("pages/evidence-and-calculations.html")],
    ["A-E math metadata", piReviewHref("pages/ae-math-metadata.html")],
    ...reportRows.slice(0, 5).map((row) => [row[0], row[2]]),
  ];
  byId("submission_artifact_links")?.replaceChildren(
    ...links.map(([label, href]) => el("a", { text: label, href: displayHref(href) })),
  );
}

function renderSubmissionQuestions() {
  const rows = [
    ["Primary threshold", "Which evidence gate must close before the C-layer result can be thesis-central?", "blocked"],
    ["Mechanism boundary", "Should E remain only a transition/control-energy proxy until PET or spatial-null evidence improves?", "mixed"],
    ["Next work package", "Should the next iteration prioritize motion proof, external validation, or manuscript-grade archive publication?", "future"],
  ];
  byId("submission_supervisor_questions")?.replaceChildren(
    ...rows.map(([label, detail, status]) => dataRecord(label, "decision needed", detail, status)),
  );
}

function renderSubmission(payload) {
  byId("submission_status_cards")?.replaceChildren(...renderMetricStrip(payload));
  renderPitchLinks("submission_pitch_links");
  renderSubmissionInsights(payload);
  renderSubmissionMechanismChart(payload);
  renderSubmissionDecisionMatrix(payload);
  renderUnitGuide("submission_unit_cards");
  renderStatusBalance(payload, "submission_status_balance_chart");
  renderSubmissionTour();
  renderSubmissionArtifactLinks(payload);
  renderSubmissionQuestions();
  renderFigureExplainer("submission_mechanism_chart_explainer", "ranking_chart", payload);
}

function renderGateChart(payload) {
  const requirements = asRecords(payload.thesis_upgrade?.strict_completion_requirements);
  const complete = requirements.filter((item) => item.complete).length;
  setText("strict_gate_status", `${complete}/${requirements.length} complete`);
  if (!requirements.length) {
    emptyPlot("strict_gate_chart", "No strict completion requirements are present.");
    return;
  }
  const labels = requirements.map((item) => text(item.label || item.requirement_id));
  plot("strict_gate_chart", [{
    type: "bar",
    orientation: "h",
    x: requirements.map((item) => (item.complete ? 1 : 0)),
    y: labels,
    marker: { color: requirements.map((item) => (item.complete ? COLORS.moss : COLORS.rose)) },
    text: requirements.map((item) => (item.complete ? "complete" : text(item.status, "blocked"))),
    textposition: "auto",
    hovertemplate: "%{y}<br>%{text}<extra></extra>",
  }], {
    margin: { t: 12, r: 18, b: 34, l: 180 },
    xaxis: { ...chartLayout.xaxis, range: [0, 1.05], tickvals: [0, 1], ticktext: ["blocked", "complete"] },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Evidence gate" },
  });
}

function renderReadPath() {
  const steps = [
    ["Open strict gates", "Read requirement status before interpreting any mechanism panel."],
    ["Check ranking", "Treat mechanism order as macro-dynamics proxy evidence."],
    ["Inspect robustness", "Use seed, subject, run, E-horizon, and D-window spread as uncertainty."],
    ["Audit prior art", "Keep literature wrappers separate from original local analysis."],
    ["Use local-only tools carefully", "Subject-level fMRI previews and simulations require FastAPI."],
  ];
  byId("read_path_list")?.replaceChildren(...steps.map(([title, detail]) => el("li", {}, [
    el("strong", { text: title }),
    document.createTextNode(` - ${detail}`),
  ])));
}

function renderOverviewLiterature(payload) {
  const rows = benchmarkRows(payload);
  setText("overview_literature_status", `${rows.filter((row) => row.status === "aligned").length}/${rows.length} aligned`);
  if (!rows.length) {
    emptyPlot("overview_literature_chart", "No literature benchmark rows are available.");
    return;
  }
  const series = sanitizeSeries(rows.map((row) => row.observed_signed_effect_size));
  plot("overview_literature_chart", [{
    type: "bar",
    orientation: "h",
    x: series.values,
    y: rows.map((row) => text(row.benchmark)),
    marker: { color: rows.map((row) => row.status === "aligned" ? COLORS.teal : row.status === "missing_required_region" ? COLORS.gray : COLORS.rose) },
    text: rows.map((row) => text(row.status)),
    textposition: "auto",
    customdata: rows.map((row) => [text(row.status), text(row.source)]),
    hovertemplate: "%{y}<br>%{customdata[0]}<br>%{customdata[1]}<br>signed effect %{x:.3f}<extra></extra>",
  }], {
    invalidCount: series.invalidCount,
    showlegend: true,
    margin: { t: 8, r: 22, b: 42, l: 210 },
    xaxis: { ...chartLayout.xaxis, title: "Signed Proxy Effect (unitless)" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Benchmark" },
  });
}

function renderOverviewClaimCards(payload) {
  const verdicts = asRecords(payload.dynamic_mechanism?.claim_verdicts);
  const cards = verdicts.slice(0, 6).map((row) => dataRecord(row.claim, row.verdict, row.evidence, row.verdict));
  byId("overview_claim_cards")?.replaceChildren(...cards);
}

function renderOverview(payload) {
  renderOverviewMetricStrip(payload);
  renderPitchCards("overview_pitch_cards", payload);
  renderGateChart(payload);
  renderEvidenceFlow(payload);
  renderReadPath();
  renderOverviewLiterature(payload);
  renderOverviewClaimCards(payload);
  renderArtifacts(payload);
  renderFigureExplainer("strict_gate_chart_explainer", "strict_gate_chart", payload);
  renderFigureExplainer("overview_literature_chart_explainer", "overview_literature_chart", payload);
}

function renderRanking(payload) {
  const dynamic = payload.dynamic_mechanism || {};
  const rows = asRecords(dynamic.mechanism_ranking).sort((left, right) => Number(left.rank ?? 999) - Number(right.rank ?? 999));
  setText("ranking_status", dynamic.analysis_status || dynamic.status || "loaded");
  if (!rows.length) {
    emptyPlot("ranking_chart", "No mechanism ranking rows are available in dashboard-data.json.");
    return;
  }
  const labels = rows.map((row) => `${text(row.layer)}: ${titleText(row.mechanism)}`);
  const scores = sanitizeSeries(rows.map((row) => row.score));
  plot("ranking_chart", [{
    type: "bar",
    orientation: "h",
    x: scores.values,
    y: labels,
    marker: { color: rows.map((row) => layerColor[text(row.layer, "")] || COLORS.teal) },
    text: scores.values.map((value) => formatNumber(value)),
    textposition: "auto",
    customdata: rows.map((row) => [text(row.status), text(row.evidence)]),
    hovertemplate: "%{y}<br>unitless support score %{x:.3f}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
  }], {
    invalidCount: scores.invalidCount,
    margin: { t: 12, r: 24, b: 46, l: 190 },
    xaxis: { ...chartLayout.xaxis, title: "Proxy Support Score (unitless)" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Mechanism layer" },
  });
  plot("ranking_distribution_chart", [{
    type: "scatter",
    mode: "lines+markers+text",
    x: rows.map((row) => text(row.layer)),
    y: scores.values,
    text: rows.map((row) => `#${text(row.rank)}`),
    textposition: "top center",
    marker: { color: rows.map((row) => layerColor[text(row.layer, "")] || COLORS.teal), size: 12 },
    line: { color: COLORS.grid },
    hovertemplate: "Layer %{x}<br>unitless support score %{y:.3f}<extra></extra>",
  }], {
    invalidCount: scores.invalidCount,
    yaxis: { ...chartLayout.yaxis, title: "Support score (unitless)" },
  });
  renderUnitGuide("ranking_unit_cards");
  renderBenchmarkChart(payload, "benchmark_chart", "benchmark_status");
  fillTable("claim_verdict_table", asRecords(dynamic.claim_verdicts), [
    (row) => tdText(row.claim),
    (row) => tdText(row.verdict),
    (row) => tdText(row.evidence),
    (row) => tdText(row.next_action),
  ]);
  fillTable("ranking_gate_table", rows, [
    (row) => tdText(row.layer),
    (row) => tdText(row.status),
    (row) => tdText(row.evidence),
  ]);
  const figures = asRecords(payload.artifact_links?.figures).filter((item) => text(item.href).includes("dynamic_mechanism"));
  byId("dynamic_figure_links")?.replaceChildren(...figures.slice(0, 12).map((item) => el("a", { text: item.label || item.href, href: displayHref(item.href) })));
  renderFigureExplainer("ranking_chart_explainer", "ranking_chart", payload);
  renderFigureExplainer("ranking_distribution_chart_explainer", "ranking_distribution_chart", payload);
  renderFigureExplainer("benchmark_chart_explainer", "benchmark_chart", payload);
}

function renderBenchmarkChart(payload, targetId, statusId) {
  const rows = benchmarkRows(payload);
  if (statusId) {
    setText(statusId, `${rows.filter((row) => row.status === "aligned").length}/${rows.length} aligned`);
  }
  if (!rows.length) {
    emptyPlot(targetId, "No literature benchmark rows are available.");
    return;
  }
  const values = sanitizeSeries(rows.map((row) => row.observed_signed_effect_size));
  plot(targetId, [{
    type: "bar",
    orientation: "h",
    x: values.values,
    y: rows.map((row) => text(row.benchmark)),
    marker: { color: rows.map((row) => row.status === "aligned" ? COLORS.teal : row.status === "missing_required_region" ? COLORS.gray : COLORS.rose) },
    text: rows.map((row) => text(row.status)),
    textposition: "auto",
    customdata: rows.map((row) => [text(row.layer), text(row.status), text(row.caveat)]),
    hovertemplate: "%{y}<br>layer %{customdata[0]}<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>",
  }], {
    invalidCount: values.invalidCount,
    margin: { t: 12, r: 24, b: 48, l: 240 },
    xaxis: { ...chartLayout.xaxis, title: "Signed Effect Size (unitless)" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Module" },
  });
}

function renderRobustness(payload) {
  const robustness = payload.dynamic_mechanism?.robustness || {};
  const layerSummary = asRecords(robustness.subject_bootstrap?.layer_summary);
  setText("robustness_status", robustness.analysis_status || payload.dynamic_mechanism?.analysis_status || "loaded");
  const topLayer = robustness.subject_bootstrap?.top_layer_by_rank_1_fraction || layerSummary.slice().sort((a, b) => Number(b.rank_1_fraction || 0) - Number(a.rank_1_fraction || 0))[0]?.layer;
  byId("robustness_cards")?.replaceChildren(
    dataRecord("Top layer", topLayer, "rank-1 bootstrap fraction"),
    dataRecord("Bootstrap rows", layerSummary.length, "subject-level resamples"),
    dataRecord("Run rows", asRecords(robustness.run_sensitivity?.run_rows).length, "run sensitivity records"),
    dataRecord("Claim guardrail", robustness.claim_guardrail || "proxy evidence only", "interpret before charts"),
  );
  if (!layerSummary.length) {
    emptyPlot("robustness_chart", "No bootstrap layer summary is available in robustness_summary.json.");
  } else {
    const means = sanitizeSeries(layerSummary.map((row) => row.score_mean));
    plot("robustness_chart", [{
      type: "bar",
      x: layerSummary.map((row) => text(row.layer)),
      y: means.values,
      error_y: {
        type: "data",
        array: layerSummary.map((row) => Math.abs(Number(row.score_ci_high ?? row.score_mean) - Number(row.score_mean ?? 0))),
        arrayminus: layerSummary.map((row) => Math.abs(Number(row.score_mean ?? 0) - Number(row.score_ci_low ?? row.score_mean))),
        color: "rgba(255,255,255,0.55)",
      },
      marker: { color: layerSummary.map((row) => layerColor[text(row.layer, "")] || COLORS.teal) },
      text: layerSummary.map((row) => `rank-1 ${formatNumber(row.rank_1_fraction)}`),
      textposition: "auto",
      customdata: layerSummary.map((row) => [formatNumber(row.rank_1_fraction), formatNumber(row.median_rank)]),
      hovertemplate: "Layer %{x}<br>mean support score %{y:.3f} unitless<br>rank-1 fraction %{customdata[0]}<br>median rank %{customdata[1]}<extra></extra>",
    }], {
      invalidCount: means.invalidCount,
      yaxis: { ...chartLayout.yaxis, title: "Bootstrap score mean (unitless)" },
    });
  }
  renderRunSensitivity(robustness);
  renderEHorizon(robustness);
  renderDWindow(robustness);
  renderRobustnessExports();
  fillTable("requirements_table", asRecords(payload.thesis_upgrade?.strict_completion_requirements), [
    (row) => tdText(row.label),
    (row) => tdText(row.status),
    (row) => tdText(row.complete ? "complete" : row.missing || row.next_action),
  ]);
  renderFigureExplainer("robustness_chart_explainer", "robustness_chart", payload);
  renderFigureExplainer("run_sensitivity_chart_explainer", "run_sensitivity_chart", payload);
  renderFigureExplainer("e_horizon_chart_explainer", "e_horizon_chart", payload);
  renderFigureExplainer("d_window_chart_explainer", "d_window_chart", payload);
}

function renderRunSensitivity(robustness) {
  const rows = asRecords(robustness.run_sensitivity?.run_rows);
  if (!rows.length) {
    emptyPlot("run_sensitivity_chart", "No run sensitivity rows are available.");
    return;
  }
  const layers = [...new Set(rows.map((row) => text(row.layer)))];
  const runs = [...new Set(rows.map((row) => text(row.run)))];
  const traces = runs.map((run) => {
    const values = sanitizeSeries(layers.map((layer) => rows.find((row) => row.layer === layer && row.run === run)?.support_score));
    return {
      type: "bar",
      name: run,
      x: layers,
      y: values.values,
      marker: { color: run === "run-01" ? COLORS.teal : COLORS.amber },
      text: values.values.map((value) => formatNumber(value)),
      textposition: "auto",
      hovertemplate: `${run}<br>Layer %{x}<br>unitless support %{y:.3f}<extra></extra>`,
    };
  });
  plot("run_sensitivity_chart", traces, {
    barmode: "group",
    yaxis: { ...chartLayout.yaxis, title: "Support score (unitless)" },
  });
}

function renderEHorizon(robustness) {
  const rows = asRecords(robustness.e_horizon_sensitivity?.rows);
  if (!rows.length) {
    emptyPlot("e_horizon_chart", "No E horizon sensitivity rows are available.");
    return;
  }
  const support = sanitizeSeries(rows.map((row) => row.support_score));
  const energy = sanitizeSeries(rows.map((row) => row.receptor_vs_random_energy_reduction_pct));
  plot("e_horizon_chart", [
    { type: "scatter", mode: "lines+markers", name: "support score", x: rows.map((row) => row.horizon), y: support.values, line: { color: COLORS.amber } },
    { type: "scatter", mode: "lines+markers", name: "receptor vs random energy", x: rows.map((row) => row.horizon), y: energy.values, line: { color: COLORS.rose }, yaxis: "y2" },
  ], {
    invalidCount: support.invalidCount + energy.invalidCount,
    xaxis: { ...chartLayout.xaxis, title: "Finite horizon (model steps)" },
    yaxis: { ...chartLayout.yaxis, title: "Support score (unitless)" },
    yaxis2: { overlaying: "y", side: "right", title: "Energy reduction (%)", gridcolor: "rgba(0,0,0,0)" },
  });
}

function renderDWindow(robustness) {
  const rows = asRecords(robustness.d_window_sensitivity?.rows);
  if (!rows.length) {
    emptyPlot("d_window_chart", "No D window sensitivity rows are available.");
    return;
  }
  const support = sanitizeSeries(rows.map((row) => row.support_score));
  plot("d_window_chart", [{
    type: "scatter",
    mode: "lines+markers",
    x: rows.map((row) => row.window_size),
    y: support.values,
    line: { color: COLORS.moss },
    hovertemplate: "Window %{x} TRs<br>unitless support %{y:.3f}<extra></extra>",
  }], {
    invalidCount: support.invalidCount,
    xaxis: { ...chartLayout.xaxis, title: "Window size (TRs)" },
    yaxis: { ...chartLayout.yaxis, title: "Support score (unitless)" },
  });
}

function renderRobustnessExports() {
  const links = [
    ["Mechanism ranking CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/mechanism_ranking.csv"],
    ["Claim verdicts CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/claim_verdicts.csv"],
    ["Literature benchmark CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/literature_benchmark.csv"],
    ["Robust bootstrap CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/robust_bootstrap_summary.csv"],
    ["Robust run sensitivity CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/robust_run_sensitivity.csv"],
    ["Robust E horizon CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/robust_e_horizon.csv"],
    ["Robust D windows CSV", "/artifacts/results/dynamic_mechanism_ranking/exports/robust_d_windows.csv"],
    ["Dynamic results workbook", "/artifacts/results/dynamic_mechanism_ranking/exports/dynamic_mechanism_results.xlsx"],
  ];
  byId("robustness_export_links")?.replaceChildren(...links.map(([label, href]) => el("a", { text: label, href: displayHref(href) })));
}

function renderEmpirical(payload) {
  const overview = payload.empirical_viewer || {};
  const subjects = Array.isArray(overview.subjects) ? overview.subjects : [];
  const subjectIndex = overview.paired_run_index || overview.subject_index || {};
  const subjectSelect = byId("empirical_subject");
  const runSelect = byId("empirical_run");
  setText("empirical_status", subjects.length ? "viewer cache ready" : "viewer cache missing");
  subjectSelect?.replaceChildren(...subjects.map((subject) => el("option", { text: subject })));
  function setRunOptions(subject) {
    const runs = Array.isArray(subjectIndex[subject]) ? subjectIndex[subject] : (Array.isArray(overview.runs) ? overview.runs : []);
    runSelect?.replaceChildren(...runs.map((run) => el("option", { text: run })));
  }
  if (overview.default_subject && subjectSelect) subjectSelect.value = overview.default_subject;
  setRunOptions(subjectSelect?.value || overview.default_subject || subjects[0]);
  if (overview.default_run && runSelect) runSelect.value = overview.default_run;
  subjectSelect?.addEventListener("change", () => setRunOptions(subjectSelect.value));
  const deltas = overview.delta_metrics || payload.empirical?.target_deltas || {};
  const labels = Object.keys(deltas);
  const values = sanitizeSeries(Object.values(deltas));
  if (!labels.length) {
    emptyPlot("empirical_delta_chart", "No group delta metrics are available.");
  } else {
    plot("empirical_delta_chart", [{
      type: "bar",
      x: labels.map(titleText),
      y: values.values,
      marker: { color: values.values.map((value) => (Number(value) >= 0 ? COLORS.teal : COLORS.rose)) },
      text: values.values.map((value) => formatNumber(value)),
      textposition: "auto",
      hovertemplate: "%{x}<br>LSD - placebo delta %{y:.3f}<br>metric-native proxy units<extra></extra>",
    }], {
      invalidCount: values.invalidCount,
      margin: { t: 12, r: 18, b: 92, l: 64 },
      yaxis: { ...chartLayout.yaxis, title: "LSD - placebo delta (metric-native proxy units)" },
    });
  }
  byId("load_empirical")?.addEventListener("click", loadEmpiricalDetail);
  byId("empirical_window")?.addEventListener("input", (event) => renderEmpiricalWindow(Number(event.target.value || 0)));
  byId("copy_empirical_json")?.addEventListener("click", copyEmpiricalJson);
  if (!isStaticDeployment && subjects.length) {
    loadEmpiricalDetail();
  } else if (isStaticDeployment) {
    setText("empirical_notice", "Static GitHub Pages shows group summaries only; subject-level cache records require the local FastAPI dashboard.");
  }
  renderFigureExplainer("empirical_delta_chart_explainer", "empirical_delta_chart", payload);
  renderFigureExplainer("empirical_fc_heatmap_explainer", "empirical_fc_heatmap", payload);
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
  const button = byId("load_empirical");
  button && (button.disabled = true);
  setLoading("empirical_fc_heatmap", `Loading ${subject} ${run}...`);
  setText("empirical_notice", `loading ${subject}/${run}`);
  setText("empirical_detail_status", "loading");
  try {
    const detail = await fetchJson(`/api/empirical-view?subject=${encodeURIComponent(subject)}&run=${encodeURIComponent(run)}`);
    empiricalDetailState.detail = detail;
    empiricalDetailState.windows = asRecords(detail.window_deltas);
    const slider = byId("empirical_window");
    if (slider) {
      slider.min = 0;
      slider.max = Math.max(empiricalDetailState.windows.length - 1, 0);
      slider.value = 0;
      slider.disabled = !empiricalDetailState.windows.length;
    }
    setText("empirical_notice", detail.run_caveat || detail.viewer_source || `${subject}/${run} loaded`);
    renderEmpiricalWindow(0);
  } catch (error) {
    emptyPlot("empirical_fc_heatmap", error.message);
    setText("empirical_notice", error.message);
    setText("empirical_detail_status", "error");
  } finally {
    button && (button.disabled = false);
  }
}

function renderEmpiricalWindow(index) {
  const detail = empiricalDetailState.detail;
  const windows = empiricalDetailState.windows;
  const selected = windows[index];
  if (!detail || !selected) {
    emptyPlot("empirical_fc_heatmap", "No selected empirical window is available.");
    return;
  }
  const modules = dashboardPayload?.empirical_viewer?.module_names || dashboardPayload?.graph?.modules?.map((module) => module.name) || [];
  const matrix = sanitizeMatrix(selected.fc_matrix);
  setText("empirical_window_label", `Window ${Number(selected.index ?? index) + 1} of ${windows.length}`);
  setText("empirical_matrix_status", `${matrix.invalidCount} invalid`);
  const axisLabels = modules.length === matrix.values.length ? modules.map(titleText) : matrix.values.map((_, rowIndex) => `Module ${rowIndex + 1}`);
  plot("empirical_fc_heatmap", [{
    type: "heatmap",
    x: axisLabels,
    y: axisLabels,
    z: matrix.values,
    colorscale: [[0, COLORS.rose], [0.5, COLORS.gray], [1, COLORS.teal]],
    zmid: 0,
    hovertemplate: "%{y} -> %{x}<br>FC delta %{z:.3f}<br>correlation-unit difference<extra></extra>",
    colorbar: { title: "FC delta (r)" },
  }], {
    invalidCount: matrix.invalidCount,
    margin: { t: 16, r: 18, b: 88, l: 120 },
    plot_bgcolor: "#2b3339",
    xaxis: { ...chartLayout.xaxis, side: "top" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Module" },
  });
  const metricRows = Object.entries(selected.metrics || {}).map(([metric, value]) => ({ metric, value }));
  fillTable("empirical_detail_table", metricRows, [
    (row) => tdText(titleText(row.metric)),
    (row) => tdNumber(row.value),
  ]);
  setText("empirical_detail_status", `${metricRows.length} metrics`);
  empiricalDetailState.rawRecord = {
    subject: detail.subject,
    run: detail.run,
    window_index: selected.index ?? index,
    metrics: selected.metrics || {},
    fc_matrix: selected.fc_matrix || [],
  };
  const raw = byId("empirical_raw_json");
  if (raw) raw.textContent = JSON.stringify(empiricalDetailState.rawRecord, null, 2);
  const copyButton = byId("copy_empirical_json");
  if (copyButton) copyButton.disabled = false;
  const sourceLink = byId("open_empirical_source");
  if (sourceLink) {
    sourceLink.textContent = "Source gated";
    sourceLink.removeAttribute("href");
    sourceLink.setAttribute("aria-disabled", "true");
  }
}

async function copyEmpiricalJson() {
  if (!empiricalDetailState.rawRecord) return;
  const serialized = JSON.stringify(empiricalDetailState.rawRecord, null, 2);
  await navigator.clipboard?.writeText(serialized);
  setText("empirical_notice", "selected cache record copied");
}

function priorArtRows(payload, filter = "") {
  const lowered = filter.toLowerCase();
  return asRecords(payload.sources).filter((row) => {
    const haystack = `${row.family} ${row.name} ${row.status} ${row.role}`.toLowerCase();
    return !lowered || haystack.includes(lowered);
  });
}

function priorArtComparisonRows(payload, filter = "") {
  const lowered = filter.toLowerCase();
  return asRecords(payload.comparison_plan).filter((row) => {
    const haystack = [
      row.family,
      row.label,
      row.readiness,
      row.dry_run_command,
      row.comparison_target,
      row.extract_target_summary,
      asStringList(row.missing_inputs).join(" "),
      row.claim_status,
    ].join(" ").toLowerCase();
    return !lowered || haystack.includes(lowered);
  });
}

function renderPriorArt(payload, dashboard) {
  setText("prior_art_status", `${payload.summary?.family_count || 0} families`);
  byId("prior_art_cards")?.replaceChildren(...asRecords(payload.families).map((item) => dataRecord(item.family, item.claim_status, item.connection, item.claim_status)));
  const input = byId("prior_art_filter");
  const draw = () => fillTable("prior_art_table", priorArtRows(payload, input?.value || ""), [
    (row) => tdText(row.family),
    (row) => tdText(row.name),
    (row) => tdText(row.status),
    (row) => tdText(row.commit_or_policy),
  ]);
  input?.addEventListener("input", draw);
  draw();
  byId("prior_art_input_cards")?.replaceChildren(...asRecords(payload.input_status).map((item) => dataRecord(item.label, item.status, item.relative_path, item.status)));
  const comparisonRows = asRecords(payload.comparison_plan);
  const readyCount = comparisonRows.filter((row) => row.readiness === "ready_to_test").length;
  setText("prior_art_test_status", `${readyCount}/${comparisonRows.length} ready`);
  const comparisonInput = byId("prior_art_comparison_filter");
  const drawComparison = () => fillTable("prior_art_comparison_table", priorArtComparisonRows(payload, comparisonInput?.value || ""), [
    (row) => tdText(row.label || row.family),
    (row) => tdText(`${row.readiness} / ${row.claim_status}`),
    (row) => tdCode(row.dry_run_command),
    (row) => tdText(row.comparison_target),
    (row) => tdText(row.extract_target_summary),
    (row) => tdText(asStringList(row.missing_inputs).join(", ") || "none"),
  ]);
  comparisonInput?.addEventListener("input", drawComparison);
  drawComparison();
  renderPriorArtPaperBoard(payload, dashboard);
}

function paperTargets() {
  return [
    { id: "preller", label: "Preller 2018 Fig 1", status: "proxy-supported", title: "Global brain connectivity proxy", kind: "empirical" },
    { id: "girn_fc", label: "Girn 2026 Figs 1-2", status: "mixed", title: "Network integration benchmarks", kind: "benchmark" },
    { id: "girn_posterior", label: "Girn 2026 Fig 3", status: "future", title: "Bayesian posteriors not recreated", kind: "blocked" },
    { id: "singleton_energy", label: "Singleton 2022 Figs 1,4-5", status: "mixed", title: "Network-control energy proxy", kind: "energy" },
    { id: "singleton_entropy", label: "Singleton 2022 Fig 6", status: "proxy-supported", title: "Transition entropy and repertoire", kind: "entropy" },
  ];
}

function renderPriorArtPaperBoard(priorPayload, dashboard) {
  const tabs = byId("prior_art_paper_tabs");
  const targets = paperTargets();
  tabs?.replaceChildren(...targets.map((target, index) => {
    const button = el("button", { text: target.label, type: "button", role: "tab", ariaSelected: index === 0 });
    button.dataset.paperTarget = target.id;
    button.addEventListener("click", () => {
      tabs.querySelectorAll("button").forEach((item) => item.setAttribute("aria-selected", String(item === button)));
      renderPaperTarget(target, priorPayload, dashboard);
    });
    return button;
  }));
  if (targets[0]) renderPaperTarget(targets[0], priorPayload, dashboard);
}

function renderPaperTarget(target, priorPayload, dashboard) {
  const board = byId("prior_art_paper_board");
  if (!board) return;
  setText("prior_art_paper_status", target.status);
  purgeCharts(board);
  board.replaceChildren(
    el("div", { className: "paper-target-summary" }, [
      dataRecord(target.title, target.status, "Local recreation is constrained to current derived artifacts.", target.status),
      dataRecord("Claim boundary", "proxy only", "Paper layout is inspiration; external analysis code is not copied.", "proxy-supported"),
    ]),
    el("div", { className: "chart-frame" }, [
      el("div", { className: "chart chart-sm", text: "Loading..." }),
    ]),
  );
  const chartNode = board.querySelector(".chart");
  const chartId = `paper_target_${target.id}_chart`;
  chartNode.id = chartId;
  if (target.kind === "empirical") {
    const deltas = dashboard.empirical_viewer?.delta_metrics || {};
    const values = sanitizeSeries(Object.values(deltas));
    plot(chartId, [{
      type: "bar",
      x: Object.keys(deltas).map(titleText),
      y: values.values,
      marker: { color: values.values.map((value) => Number(value) >= 0 ? COLORS.teal : COLORS.rose) },
      hovertemplate: "%{x}<br>proxy delta %{y:.3f}<extra></extra>",
    }], { invalidCount: values.invalidCount, margin: { t: 12, r: 16, b: 92, l: 58 } });
  } else if (target.kind === "benchmark") {
    renderBenchmarkChart(dashboard, chartId);
  } else if (target.kind === "energy") {
    const rows = asRecords(dashboard.dynamic_mechanism?.network_control_energy?.metric_deltas).filter((row) => text(row.metric).includes("energy"));
    const values = sanitizeSeries(rows.map((row) => row.mean_delta));
    plot(chartId, [{
      type: "bar",
      orientation: "h",
      y: rows.map((row) => titleText(row.metric)),
      x: values.values,
      marker: { color: values.values.map((value) => Number(value) >= 0 ? COLORS.teal : COLORS.rose) },
      hovertemplate: "%{y}<br>mean delta %{x:.3f}<extra></extra>",
    }], { invalidCount: values.invalidCount, margin: { t: 12, r: 24, b: 46, l: 230 } });
  } else if (target.kind === "entropy") {
    const rows = asRecords(dashboard.dynamic_mechanism?.transition_proxy?.metric_deltas).slice(0, 8);
    const values = sanitizeSeries(rows.map((row) => row.signed_effect_size));
    plot(chartId, [{
      type: "bar",
      orientation: "h",
      y: rows.map((row) => titleText(row.metric)),
      x: values.values,
      marker: { color: values.values.map((value) => Number(value) >= 0 ? COLORS.teal : COLORS.rose) },
      hovertemplate: "%{y}<br>signed effect %{x:.3f}<extra></extra>",
    }], { invalidCount: values.invalidCount, margin: { t: 12, r: 22, b: 46, l: 190 } });
  } else {
    emptyPlot(chartId, "Not recreated in the first pass. Current payload has directional proxy rows, not the Bayesian posterior model required for this figure.");
  }
}

function renderSimulationPayload(payload) {
  const modules = payload.modules || [];
  const time = payload.time || [];
  const traces = modules.map((module, index) => {
    const values = sanitizeSeries((payload.time_series || []).map((row) => Array.isArray(row) ? row[index] : null));
    return {
      type: "scatter",
      mode: "lines",
      name: module,
      x: time,
      y: values.values,
    };
  });
  plot("sim_time_chart", traces, {
    margin: { t: 14, r: 20, b: 46, l: 60 },
    yaxis: { ...chartLayout.yaxis, title: "z-scored model activity" },
  });
  const matrix = sanitizeMatrix(payload.fc_matrix || []);
  plot("sim_fc_chart", [{
    type: "heatmap",
    x: modules,
    y: modules,
    z: matrix.values,
    colorscale: [[0, COLORS.rose], [0.5, COLORS.gray], [1, COLORS.teal]],
    zmid: 0,
    hovertemplate: "%{y} -> %{x}<br>FC %{z:.3f}<extra></extra>",
  }], {
    invalidCount: matrix.invalidCount,
    margin: { t: 16, r: 18, b: 82, l: 120 },
    plot_bgcolor: "#2b3339",
    xaxis: { ...chartLayout.xaxis, side: "top" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Mechanism" },
  });
}

async function runSimulation(dashboard = {}) {
  const body = {
    regime: byId("sim_regime")?.value || "baseline",
    within_group_scale: Number(byId("sim_within")?.value || 1),
    cross_group_scale: Number(byId("sim_cross")?.value || 1),
    constraint_scale: Number(byId("sim_constraint")?.value || 1),
    temperature: Number(byId("sim_temperature")?.value || 0.1),
  };
  const button = byId("run_simulation");
  button && (button.disabled = true);
  setText("simulator_status", "running");
  setLoading("sim_time_chart", "Running simulator...");
  setLoading("sim_fc_chart", "Running simulator...");
  try {
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
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`/api/simulate returned ${response.status}`);
    const payload = await response.json();
    renderSimulationPayload(payload);
    setText("simulator_status", "rendered");
  } catch (error) {
    emptyPlot("sim_time_chart", error.message);
    emptyPlot("sim_fc_chart", error.message);
    setText("simulator_status", "error");
  } finally {
    button && (button.disabled = false);
  }
}

function renderThesis(payload, priorPayloadForPage) {
  byId("thesis_status_cards")?.replaceChildren(...renderMetricStrip(payload));
  renderPitchLinks("thesis_pitch_links");
  renderPitchCards("thesis_pitch_cards", payload);
  renderStatusBalance(payload);
  const rows = asRecords(payload.dynamic_mechanism?.mechanism_ranking);
  const scores = sanitizeSeries(rows.map((row) => row.score));
  plot("thesis_mechanism_chart", [{
    type: "bar",
    orientation: "h",
    y: rows.map((row) => `${row.layer}: ${titleText(row.mechanism)}`),
    x: scores.values,
    marker: { color: rows.map((row) => layerColor[text(row.layer, "")] || COLORS.teal) },
    hovertemplate: "%{y}<br>unitless support score %{x:.3f}<extra></extra>",
  }], {
    invalidCount: scores.invalidCount,
    margin: { t: 10, r: 20, b: 44, l: 190 },
    xaxis: { ...chartLayout.xaxis, title: "Proxy support score (unitless)" },
    yaxis: { ...chartLayout.yaxis, autorange: "reversed", title: "Mechanism" },
  });
  const verdicts = asRecords(payload.dynamic_mechanism?.claim_verdicts);
  byId("thesis_claim_ladder")?.replaceChildren(...verdicts.slice(0, 6).map((row) => dataRecord(row.claim, row.verdict, row.evidence, row.verdict)));
  const loopSteps = asRecords(payload.thesis_expansion?.loop_steps);
  const fallbackSteps = [
    { label: "Dataset anchor", status: "implemented", implementation_evidence: "Use ds003059-derived paired LSD/placebo summaries as the empirical anchor." },
    { label: "Transparent surrogate", status: "proxy-supported", implementation_evidence: "Rank macro-dynamic layers A-E rather than claiming receptor-level realism." },
    { label: "Mechanism ranking", status: "implemented", implementation_evidence: "C is strongest in the current proxy score; E is split into landscape proxy and receptor-placement gates." },
    { label: "Limitations", status: "blocked", implementation_evidence: "Motion and music/run-02 remain explicit gates; striatal evidence is limited to a bilateral proxy row, PET receptor promotion is blocked by spatial nulls, and external validation is negative/partial." },
  ];
  const steps = loopSteps.length ? loopSteps : fallbackSteps;
  byId("thesis_evidence_sequence")?.replaceChildren(...steps.map((row, index) => el("section", { className: "story-step" }, [
    el("span", { text: text(row.step, String(index + 1)) }),
    el("div", {}, [
      el("strong", { text: text(row.label, "Evidence step") }),
      el("small", { className: statusClass(row.status), text: text(row.status, "status") }),
      el("p", { text: text(row.implementation_evidence || row.scientific_question || row.dashboard_output, "Evidence pending.") }),
      row.implementation_blocker ? el("p", { className: "muted", text: text(row.implementation_blocker) }) : "",
    ]),
  ])));
  byId("thesis_prior_art_summary")?.replaceChildren(...asRecords(priorPayloadForPage?.families).slice(0, 6).map((row) => dataRecord(row.family, row.claim_status, row.connection, row.claim_status)));
  const links = [
    ["Dashboard", isStaticDeployment ? "dashboard/" : "/"],
    ["Supervisor pitch package", piReviewHref()],
    ["Pitch slides", piReviewHref("pages/pitch-slides.html")],
    ["Figure atlas", piReviewHref("pages/figure-atlas.html")],
    ["Claim matrix", "/artifacts/results/thesis_evidence_loop/claim_evidence_matrix.csv"],
    ["Thesis microsite artifact", "/artifacts/output/doc/thesis_microsite.html"],
    ["Defense presentation artifact", "/artifacts/output/doc/defense_presentation.html"],
  ];
  byId("thesis_artifact_links")?.replaceChildren(...links.map(([label, href]) => el("a", { text: label, href: displayHref(href) })));
  renderFigureExplainer("thesis_mechanism_chart_explainer", "thesis_mechanism_chart", payload);
}

async function main() {
  document.querySelectorAll(".chart").forEach((node) => {
    if (!node.textContent.trim()) node.textContent = "Loading...";
  });
  if (pageId === "prior_art") {
    const [prior, dashboard] = await Promise.all([fetchJson(priorArtDataUrl), fetchJson(dashboardDataUrl)]);
    priorArtPayload = prior;
    dashboardPayload = dashboard;
    renderPriorArt(prior, dashboard);
    return;
  }
  if (pageId === "thesis") {
    const [dashboard, prior] = await Promise.all([fetchJson(dashboardDataUrl), fetchJson(priorArtDataUrl)]);
    dashboardPayload = dashboard;
    priorArtPayload = prior;
    renderThesis(dashboard, prior);
    return;
  }
  const dashboard = await fetchJson(dashboardDataUrl);
  dashboardPayload = dashboard;
  if (pageId === "overview") {
    renderOverview(dashboard);
  } else if (pageId === "mechanism_ranking") {
    renderRanking(dashboard);
  } else if (pageId === "submission") {
    renderSubmission(dashboard);
  } else if (pageId === "robustness") {
    renderRobustness(dashboard);
  } else if (pageId === "empirical") {
    renderEmpirical(dashboard);
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
      if (button) button.textContent = "Render Cached Regime";
    }
    await runSimulation(dashboard);
    byId("run_simulation")?.addEventListener("click", () => runSimulation(dashboard));
  } else if (pageId === "figures") {
    renderFigureDeck(dashboard);
  }
}

main().catch((error) => {
  const target = byId(`${pageId}_status`) || byId("strict_gate_status") || byId("simulator_status");
  if (target) target.textContent = error.message;
  document.querySelectorAll(".chart").forEach((node) => {
    if (node.textContent.trim() === "Loading...") {
      emptyPlot(node.id, error.message);
    }
  });
});
