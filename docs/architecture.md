# Architecture

## Overview

The MVP is organized around a small number of explicit layers:

1. Config layer
2. Simulator layer
3. Metrics / feature extraction layer
4. Fitting and perturbation-search layer
5. Reporting and dashboard layer

```mermaid
flowchart LR
    A["YAML Configs"] --> B["Graph Builder"]
    A --> C["Regime Parameters"]
    L["OpenNeuro ds003059"] --> M["Exact Rest-Run Downloader"]
    M --> N["8-Module Time-Series Extraction"]
    B --> D["Stochastic Surrogate Simulator"]
    C --> D
    D --> E["Synthetic Time Series"]
    E --> F["Shared Observables"]
    N --> F
    F --> G["Sober Fitting"]
    F --> H["Perturbation Search"]
    H --> I["Ablation Engine"]
    F --> J["Plotting and Reports"]
    G --> J
    H --> J
    I --> J
    J --> K["Plotly Dashboard Payloads"]
    N --> O["Windowed Training Export"]
    O --> P["Cloud DNN Scaffolds"]
```

## Package Boundaries

- `core.py`: typed configuration models and shared constants
- `graph.py`: module names, graph assembly, hierarchy helpers
- `simulator.py`: state integration and regime execution
- `metrics.py`: FC, dynamic FC, entropy, switching, metastability proxies
- `fit.py`: sober fitting objective and search routine
- `perturbation.py`: mechanism operators and ranking
- `ablation.py`: one-at-a-time and pairwise analyses
- `reporting.py`: figures, markdown snippets, JSON outputs
- `web/`: lightweight dashboard server and template assets
- `data/`: OpenNeuro ingestion, ds003059 extraction, target generation, and fallback interfaces
- `training.py`: windowed export helpers for later cloud experiments

## Dashboard And Reporting Map

The local FastAPI dashboard is intentionally split into small modules so route handling, payload assembly, artifact policy, and empirical-viewer policy can evolve independently.

```mermaid
flowchart TD
    APP["web/app.py\nFastAPI routes and dashboard payload orchestration"]
    SIM["web/simulation_payload.py\nsimulation and graph payload adapters"]
    STATUS["web/status_payload.py\nprovenance, model-selection, validation, and audit-status payloads"]
    EMP["web/empirical_viewer.py\npaired empirical viewer and guarded run-02 policy"]
    DTI["web/structural_dti.py\nstructural-connectome dashboard graph payload"]
    THESIS["web/thesis_payload.py\nPI-pitch, claim-status, and thesis-loop payloads"]
    ART["web/artifacts.py\nallowlisted artifact links and artifact-path policy"]
    TEMPLATE["templates/base.html + templates/pages/*\nmultipage dashboard shell"]
    REPORTS["reporting.py and publication modules\nmarkdown, figures, document artifacts"]

    APP --> SIM
    APP --> STATUS
    APP --> EMP
    APP --> DTI
    APP --> THESIS
    APP --> ART
    APP --> TEMPLATE
    REPORTS --> ART
```

Keep `web/app.py` as the route module. New dashboard payload concerns should move behind a focused `web/*_payload.py` or policy module when they would otherwise add another large helper block to `web/app.py`.

## Dynamic Mechanism Map

The dynamic-mechanism ranking code is being split around stable helper interfaces so mechanism summaries can be tested without adding more private helper imports across research modules.

```mermaid
flowchart TD
    DYN["dynamic_mechanism.py\nsummary orchestration, DMDc, and control-energy ranking"]
    CONN["dynamic_mechanism_connectivity.py\nFC graph, network, and vector-correlation helpers"]
    HIER["dynamic_mechanism_hierarchy.py\nhierarchy/routing proxy summary"]
    PRIORS["dynamic_mechanism_priors.py\nmodule masks, prior vectors, and control-weight normalization"]
    REP["dynamic_mechanism_repertoire.py\ndynamic-FC and integration/segregation proxy summary"]
    STATS["dynamic_mechanism_stats.py\npaired metric rows, bootstrap/FDR helpers, labels, and trajectory statistics"]
    TRANS["dynamic_mechanism_transitions.py\ntransition-state proxy summary"]
    ROBUST["dynamic_robustness.py\nsensitivity checks using public dynamic-mechanism helpers"]

    DYN --> CONN
    DYN --> HIER
    DYN --> PRIORS
    DYN --> REP
    DYN --> STATS
    DYN --> TRANS
    HIER --> CONN
    HIER --> PRIORS
    HIER --> STATS
    REP --> CONN
    REP --> PRIORS
    REP --> STATS
    ROBUST --> DYN
    ROBUST --> STATS
```

Keep new mechanism-specific summaries behind focused public helper modules when they can be extracted without changing the summary schema. `dynamic_mechanism.py` should stay the orchestration layer for the combined ranking artifact.

## Rationale

The design favors explicit state variables, visible configuration, and inspectable intermediate outputs. Most of the scientific uncertainty sits in the perturbation interpretation, so the implementation intentionally keeps the mathematics simple and the claims narrow.
