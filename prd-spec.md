# PRD: Plate Data Processing & Analysis Platform

## 1. Purpose
Build a data processing system that ingests raw plate measurement data and produces normalized ratios, robust statistical scores, and quality control flags. The platform enables researchers to identify candidate hits, assess plate performance, and export results for downstream analysis.

## 2. Users
- Researcher (primary): Uploads raw plate data, inspects processed metrics, flags hits, and exports results.
- Data Scientist (secondary): Integrates processed outputs into statistical pipelines or machine learning models.
- Collaborator (viewer): Receives clean, summarized datasets and figures.

## 3. Inputs
- One or more plate datasets (tabular).
- Each plate dataset includes the following required measurement columns:
  - `BG_lptA` - BetaGlo (reporter) for lptA
  - `BT_lptA` - BacTiter (ATP/viability) for lptA
  - `BG_ldtD` - BetaGlo for ldtD
  - `BT_ldtD` - BacTiter for ldtD
  - `OD_WT`   - optical density for wild-type strain
  - `OD_tolC` - optical density for ΔtolC strain
  - `OD_SA`   - optical density for SA strain
- Optional metadata columns: plate identifier, well position, treatment ID, etc.
- Optional controls: `ControlType` with values `{pos, neg, none}` to enable control-based QC (e.g., Z′-factor) and optional control-anchored thresholds.

Auto-detection & mapping: The system auto-detects required columns; the UI provides a manual column-mapping fallback when headers differ from expected names.

## 4. Core Features & Calculations

### 4.1 Reporter Ratios
Definition:
- `Ratio_lptA = BG_lptA / BT_lptA`
- `Ratio_ldtD = BG_ldtD / BT_ldtD`

Purpose: quantify reporter activity relative to same-well ATP (BacTiter).

### 4.2 OD Normalization
Definition:
- `OD_WT_norm   = OD_WT / median(OD_WT)`
- `OD_tolC_norm = OD_tolC / median(OD_tolC)`
- `OD_SA_norm   = OD_SA / median(OD_SA)`

Purpose: normalize growth values relative to plate-wide medians.

### 4.3 Robust Z-scores
Definition (per reporter ratio):
- `Z = (value - median(values)) / (1.4826 * MAD(values))` where `MAD = median(|X - median(X)|)`
- `Z_lptA = (Ratio_lptA - median(Ratio_lptA)) / (1.4826 * MAD(Ratio_lptA))`
- `Z_ldtD = (Ratio_ldtD - median(Ratio_ldtD)) / (1.4826 * MAD(Ratio_ldtD))`

Purpose: identify outliers/hits with robustness to skew and outliers.

### 4.4 Viability Gate
Definition (per reporter BT column):
- `viability_ok_lptA   = BT_lptA >= f * median(BT_lptA)`
- `viability_fail_lptA = BT_lptA <  f * median(BT_lptA)`
- `viability_ok_ldtD   = BT_ldtD >= f * median(BT_ldtD)`
- `viability_fail_ldtD = BT_ldtD <  f * median(BT_ldtD)`

Configurable parameter: `f` (default `0.3`).

Purpose: gate out low-viability wells (low ATP; unreliable readout). Wells failing the gate remain in outputs but are excluded from default hit-calling and summaries.

### 4.5 Aggregation
- Combine results across multiple plates into a long-format dataset with a `PlateID` column.
- Apply the same calculations (ratios, normalized ODs, Z-scores, viability flags) to each plate independently.
- Support downstream analysis across all plates (e.g., hit ranking, summary statistics).

### 4.6 Optional Controls
If controls are provided (via `ControlType`):
- Compute per-plate QC including Z′-factor (pos vs neg) and control CVs.
- Optionally validate or tune the viability parameter `f` against control behavior.
- Allow control-anchored hit rules (e.g., thresholds relative to negatives) while keeping the default, control-free pipeline unchanged.

## 5. Outputs
- Processed tables:
  - Per-plate processed dataset with calculated columns.
  - Combined dataset across all selected plates.
  - Ranked top-N candidates based on maximum absolute Z-scores (by default includes only `viability_ok_*` wells; toggleable).
- Exports:
  - CSV (per-plate, combined, top-N).
  - ZIP bundle containing all processed results, figures, and manifest metadata.
- Figures (recommended):
  - Histograms of `Ratio_lptA`, `Ratio_ldtD`.
  - Histograms/boxplots of `Z_lptA`, `Z_ldtD`.
  - Scatter `Ratio_lptA` vs `Ratio_ldtD` (colored by plate).
  - Bar plots of viability gate counts.

## 6. Data Flow
1. Ingest: Read one or more plate datasets.
2. Process: For each plate:
   - Compute reporter ratios.
   - Compute OD normalizations.
   - Compute robust Z-scores.
   - Apply viability gating (flag `viability_ok_*` / `viability_fail_*`).
3. Aggregate: Merge results into combined dataset.
4. Export: Provide outputs in CSV and visualization formats.

## 7. Validation
- The system must reproduce expected values for:
  - Reporter ratios.
  - OD normalizations.
  - Robust Z-scores.
  - Viability gate flags.
- Numerical tolerance: differences = 1e-9 when compared to reference calculations.
- Must handle missing values gracefully (output `NaN`).
- Must document cases where MAD = 0 (avoid divide-by-zero errors).

## 8. Non-Functional Requirements
- Accuracy: Reproducible, deterministic outputs.
- Scalability: Handle multiple plates with up to ~2,000 rows each.
- Extensibility: Easy to add new reporters (e.g., other `BG/BT` pairs).
- Transparency: All calculation steps logged or documented.
- Reusability: Core processing logic written as standalone functions for reuse in scripts, pipelines, or UIs.

## 9. Future Extensions
- Plate heatmaps (if well coordinates provided).
- Multi-criteria hit calling (e.g., `(Z > threshold) AND viability_ok == True`).
- Automated QC metrics (plate medians, dispersion, control performance).
- Web or desktop UI for upload/visualization.
- Integration with cloud storage for persistence.

## 10. Implementation Plan & Technology Choices

### 10.1 Preferred UI: Streamlit
Why: fastest path to a usable UI, minimal boilerplate, great for internal tools and rapid iteration.

Key components:
- `st.file_uploader` for plate files (ephemeral; rely on exports).
- Sidebar controls: sheet selection, Z cutoffs, Top-N, viability gate (f), flag toggles.
- Main views: distributions (Plotly histograms/box), ratio scatter, hit table, per-plate tables.
- Export buttons: combined CSV, Top-N CSV, per-plate CSVs, ZIP bundle (includes plots + manifest).

State & performance:
- Use `st.session_state` to avoid recomputation during a session.
- Cache parsing with `@st.cache_data` keyed by file hash; invalidate on parameter change.
- Use pandas by default; switch to polars for larger datasets if needed (feature-parity required).

Limitations / mitigations:
- No built-in persistent storage — export-centric workflow or plug S3/GCS later.
- App reruns on interaction — keep expensive steps cached.
- Multi-user concurrency on shared hosts can be limited — consider container deployment with a process manager.

### 10.2 Alternatives (When to choose them)

| Option | Use When | Pros | Cons |
|---|---|---|---|
| Dash (Plotly Dash) | Need more granular layout/routing, long-lived enterprise apps | Mature, Flask under the hood, fine-grained callbacks | More boilerplate than Streamlit |
| Panel (HoloViz) | Heavy scientific viz (Bokeh/HoloViews/Datashader) | Powerful viz ecosystem, notebook-friendly | Smaller community than Streamlit/Dash |
| Gradio | Quick model demos or very simple UIs | Minimal setup, easy sharing | Limited layout; not ideal for data-heavy apps |
| Voila | Notebook -> App without rewrite | Reuses notebooks, reproducible | Jupyter server overhead, not ideal for complex apps |
| FastAPI + React (Vite/Next.js) | Need robust multi-user, auth, RBAC, APIs, scaling | Full control, best long-term maintainability | Highest initial effort (frontend+backend) |
| Shiny for Python | R/Shiny experience on team | Reactive model, good layouts | Ecosystem less mature on Python |
| Desktop (Tauri/PySide/Qt) | Offline lab PCs, strict environments | True offline, native menus, file access | Packaging complexity; updates harder |

Recommendation: Start with Streamlit for internal alpha/beta. If/when you need multi-user access control, audit logs, or integrations, graduate to FastAPI + React while reusing the same Python processing core.

### 10.3 Packaging & Dependencies
- Python 3.11.
- Core libs: `pandas` (or `polars`), `numpy`, `scipy` (for robust stats if desired), `plotly`, `openpyxl`.
- Optional: `kaleido` for static image export; `boto3`/`google-cloud-storage` for object storage.
- Lock with `uv` or `pip-tools`. Provide `requirements.txt` and `pyproject.toml`.

### 10.4 Storage & Persistence
- Default: no persistence; users download CSV/ZIP artifacts.
- Add-on: object storage (S3/GCS/Azure Blob) with signed URLs for later retrieval.
- Metadata DB (SQLite/Postgres) only if you need auditability, multi-user histories, or sharing.

### 10.5 Security & Privacy
- No PII expected; treat uploads as sensitive lab data.
- If deployed on a server: HTTPS, size limits on uploads, virus scan (optional), signed URL timeouts for downloads.
- Configurable retention policy if persistence is enabled.

### 10.6 Testing Strategy
- Unit tests for calculations: ratios, medians, MAD, Z-scores, viability flags; include edge cases (NaN, zero MAD, zero denominators).
- Golden tests: load canonical plate fixtures and compare outputs to reference CSV with `rtol=1e-9, atol=1e-12`.
- UI smoke tests: script Streamlit interactions with streamlit-testing or Playwright against a dev server.

### 10.7 Performance Targets
- Single plate of up to ~2,000 rows processes in < 200 ms on a typical laptop.
- 10 plates end-to-end including visualizations in < 2 s.
- Memory: < 1 GB for 10 plates; if exceeded, prefer polars/lazy operations.

### 10.8 Observability
- Structured logs for ingest/process/export steps.
- Optional usage telemetry (opt-in): counts of uploads, runtime, errors (no row-level data).

### 10.9 Math Rendering
- Default: pre-render formulas to SVG via KaTeX server-side and embed in HTML/PDF (compatible with WeasyPrint and other non-JS engines).
- Alternative: use a JS-capable HTML→PDF renderer (wkhtmltopdf or headless Chromium) with MathJax to typeset formulas at render time.
- High fidelity: provide a LaTeX→PDF export path (e.g., Tectonic) that compiles the same formulas for publication-quality output.
- Shared source: keep formulas in one module/templates so UI and reports use the same definitions and macros.
- Fonts/encoding: use UTF‑8 throughout and embed fonts in exports to avoid glyph issues.

## 11. Deployment Plan

### 11.1 Environments
- Local Dev: `streamlit run app.py` (+ hot reload).
- Staging/Team: Docker container behind a reverse proxy; per-user session isolation.
- Public/Internal Cloud:
  - Hugging Face Spaces (Docker) — easy deploy, supports `requirements.txt`, persistent repo storage optional.
  - Streamlit Community Cloud — simplest, but ephemeral filesystem and limited resources.
  - VM/Kubernetes — for enterprise setups; autoscale workers; GPU not required here.

### 11.2 CI/CD
- GitHub Actions:
  - Lint & test on PR.
  - Build Docker image on main.
  - Deploy to chosen target (Spaces/VM) on tagged release.

### 11.3 Configuration
- `config.yaml` for default thresholds (e.g., Z cutoff, `viability.min_fraction_of_median: 0.3`), sheet selection patterns, and export toggles.
- Precedence: UI override > YAML > built-in defaults.
- Environment variables for storage credentials and secrets.

## 12. Roadmap (Phased)

1) MVP (2-3 days)
   - CLI + Streamlit minimal UI
   - Ratios, OD norms, Z-scores, viability gate
   - Combined/Top-N CSV, ZIP export (plots + manifest)
   - Golden tests on sample plates

2) Beta (1-2 weeks)
   - Plate heatmaps (if well coordinates available)
   - Configurable hit rules (multi-criteria)
   - Polars backend option
   - Object storage adapter (S3/GCS)

3) v1.0 (3-4 weeks)
   - Authentication (if needed)
   - Run history & shareable links (requires DB + object storage)
   - API endpoints (FastAPI) for headless processing
   - Hardened CI/CD, logging, and monitoring

## 13.7 Formulas Section

### Purpose
Ensure each report clearly documents the exact calculations applied. This allows anyone reading the PDF to understand the processing pipeline without needing to consult external documentation.

### Content
At the end of the report (or in an appendix), include a "Formulas" section that lists all derived metrics with standard mathematical notation.

### Required Formulas

1. Reporter Ratios

$$
\text{Ratio}_{lptA} = \frac{\text{BG}_{lptA}}{\text{BT}_{lptA}}, \quad
\text{Ratio}_{ldtD} = \frac{\text{BG}_{ldtD}}{\text{BT}_{ldtD}}
$$

2. OD Normalization

$$
\text{OD}_{WT}^{norm}   = \frac{\text{OD}_{WT}}{\text{median}(\text{OD}_{WT})}, \quad
\text{OD}_{tolC}^{norm} = \frac{\text{OD}_{tolC}}{\text{median}(\text{OD}_{tolC})}, \quad
\text{OD}_{SA}^{norm}   = \frac{\text{OD}_{SA}}{\text{median}(\text{OD}_{SA})}
$$

3. Robust Z-score

$$
Z_x = \frac{x - \text{median}(X)}{1.4826 \times \text{MAD}(X)}
$$

where

$$
\text{MAD}(X) = \text{median}(|X - \text{median}(X)|)
$$

4. Viability Gate

Let f be the configurable viability parameter (default 0.3).

$$
\text{viability_ok}_{lptA} =
\begin{cases}
1 & \text{if } \text{BT}_{lptA} \ge f \times \text{median}(\text{BT}_{lptA}) \\
0 & \text{otherwise}
\end{cases}
$$

Similarly for ldtD using \text{BT}_{ldtD}.

### Implementation Notes
- Use LaTeX rendering (via matplotlib.mathtext or direct LaTeX compilation) to generate high-quality formula images, then embed them in the PDF.
- For HTML→PDF engines that do not execute JavaScript (e.g., WeasyPrint), pre-render formulas server-side to static SVG via KaTeX and embed them.
- Alternatively, use a JS-capable renderer (e.g., wkhtmltopdf/Chromium headless) with MathJax to typeset at render time.
- Preferred high-fidelity option: provide a LaTeX→PDF export path (e.g., Tectonic) using the same formulas.

## Frontend UI & Visualization Spec

### A. Tech Stack (Phase 1: Streamlit)
- **UI framework:** Streamlit (Python 3.11+)
- **Charts:** Plotly (interactive), Seaborn/Matplotlib (static for PDF)
- **Heatmaps:** Plotly Heatmap/Imshow (96/384 well grids)
- **PDF export:** Jinja2 + WeasyPrint (HTML→PDF; KaTeX pre-render for formulas; see 10.9 Math Rendering) or ReportLab (fallback)
- **State:** `st.session_state`, `@st.cache_data` (cache parsing/compute)
- **Optional (Phase 2):** Dash (for multi-page control), FastAPI+React (multi-user), Tauri/PySide (offline desktop)

### B. Visualization Libraries (approved)
- **Plotly**: histograms, box, scatter, bar, heatmaps; export to PNG/SVG/HTML
- **Seaborn/Matplotlib**: publication-quality static figures (PDF)
- **Colormaps**
  - Diverging (center=0): `"RdBu_r"` or `"Spectral"` for Z/B-score
  - Sequential: `"Viridis"` or `"Inferno"` for ratios/OD

### C. UI Elements (Streamlit)
- **Navigation:** `st.tabs()` — Summary | Hits | Visualizations | Heatmaps | QC Report
- **Layout:** `st.columns()` for side-by-side charts, `st.expander()` for advanced diagnostics
- **Controls:** `st.file_uploader`, `st.selectbox`, `st.radio`, `st.slider`, `st.number_input`, `st.multiselect`
- **Column Mapping:** expander showing detected columns with manual override (bind headers to expected fields)
- **Control Assignment:** expander to mark wells as pos/neg if `ControlType` is missing (upload mapping or select wells on heatmap)
- **Status & KPIs:** `st.metric()` cards for Plates, Rows, Missing%, Edge-Effect status
- **Feedback:** `st.spinner`, `st.progress` for longer runs
- **Exports:** `st.download_button` (CSV, ZIP bundle, PDF)

### D. Styling
- **Theme:** Streamlit theme (light/dark) with single accent color
- **Badges (edge-effect):** INFO (grey), WARN (amber), CRITICAL (red)
- **Typography:** Sans-serif for UI; monospace for manifest/JSON blocks
- **CSS hooks (optional)**
  - Use `st.markdown(..., unsafe_allow_html=True)` to style badges:
    - `.badge { padding:2px 8px; border-radius:8px; font-size:0.8rem }`
    - `.info { background:#f3f4f6 } .warn { background:#fde68a } .crit { background:#fecaca }`

### E. Interactions/Behaviors
- **Metric selector (Heatmaps):** `Raw Z | B-score | Ratio | OD_norm` (radio)
- **B-scoring toggle:** checkbox or radio; when enabled, show Raw vs B-score side-by-side
- **Hit ranking:** rank by `max(|Z_lptA|, |Z_ldtD|)` (abs by default, toggle to signed) or by `max(|B_Z_lptA|, |B_Z_ldtD|)`
- **Edge-effect diagnostics:** small panel with Δ(edge−interior), Spearman ρ (row/col), corner MADs; show badge in tab header
- **Config management:** Reset to defaults; Save/Load config YAML (UI overrides YAML)
- **Persisted outputs:** ZIP bundle includes original upload, processed CSVs, plots (HTML/PNG), PDF, and `manifest.json`
- **Export fidelity:** export static images via Plotly kaleido (2×–3× DPI); include `manifest.json` with app version, config, and file hashes
- **Sample data:** Load sample plate for demo/testing

### F. UI Wireframe (Streamlit)

HEADER: "Plate Data Processing Platform"
SUBHEADER (muted): "Normalization, scoring, B-scoring, and reporting"

[TABS] Summary | Hits | Visualizations | Heatmaps | QC Report

TAB: Summary
  [METRICS ROW]
    - st.metric("Plates", N) | st.metric("Rows", M) | st.metric("Missing %", x%)
    - Edge badge: [INFO/WARN/CRITICAL] (click → expander diagnostics)
  [EXPANDER] "Edge Diagnostics"
    - Δ(edge−interior), d (MADs), ρ_row (p), ρ_col (p), corner MADs
  [BUTTONS]
    - Download combined CSV | Download ZIP Bundle

TAB: Hits
  [ROW]
    - Rank by: ( Raw Z | B-score )
    - Top-N: (number_input)
  [TABLE]
    - Columns: Plate, Well, Ratio_lptA, Ratio_ldtD, Z_lptA, Z_ldtD, B_Z_lptA, B_Z_ldtD, viability_ok_lptA
  [BUTTON] Download Top Hits CSV

TAB: Visualizations
  [COLUMNS]
    - Left: Histogram (Raw Z_lptA) + box overlay
    - Right: Histogram (B_Z_lptA) + box overlay
  [COLUMNS]
    - Left: Scatter (Ratio_lptA vs Ratio_ldtD) color=Plate
    - Right: Bar (viability_ok_lptA counts by plate)

TAB: Heatmaps
  [ROW CONTROLS]
    - Metric: ( Raw Z | B-score | Ratio | OD_norm )
    - Plate: (selectbox)
    - Scale: (diverging center=0 for Z/B-score; sequential for others)
  [COLUMNS]
    - Left: Heatmap (selected metric)
    - Right: Heatmap (comparison: Raw vs B-score when applicable)
  [NOTE]
    - Missing wells rendered with neutral glyph; tooltip shows Row, Col, Value, Flags

TAB: QC Report
  [BUTTON] Generate PDF Report
  [PREVIEW] Inline PDF (optional iframe) or link to download
  [DETAILS] Show manifest (current parameters) in monospace block

### G. Accessibility & Performance
- Keyboard-focusable controls; clear color + numeric labels on heatmaps
- Cache heavy computations (`@st.cache_data`) keyed by file hash + parameters
- Guard rails: NaN-safe calculations; informative warnings; viability-failing wells excluded from hit ranking by default (toggleable)
- Cache keys: compute cache keyed by `(file_hash, sheet, plate_type, f, bscore.apply_to, thresholds, …)`; presentation-only controls (colormap/scale) do not invalidate compute cache
- Spinner & timing: show `st.spinner` and elapsed times for parsing/exports
- Pre-ingest validation: preview table, schema check, friendly errors (missing columns, dtypes, duplicates)

### H. Deliverables (Frontend)
- `ui/streamlit_app.py` implementing the wireframe above
- `assets/` with CSS snippet (badges), logo (optional)
- Configurable defaults in `config.yaml` (Z cutoff, Top-N, thresholds, colormaps)
- Unit/smoke tests for UI actions (basic) and golden-image tests for charts (optional)

## 14. B-Scoring (Row/Column Bias Correction)

### 14.1 Purpose
Reduce plate-position artifacts (evaporation, temperature, handling) by removing row and column effects from well values, yielding more trustworthy hit calls and cleaner heatmaps.

### 14.2 Inputs & Scope
- Works on any plate metric in matrix form per plate (e.g., `Z_lptA`, `Z_ldtD`, `Ratio_*`, `OD_*_norm`).
- Requires well positions (`Row ∈ {A..H}`, `Col ∈ {1..12}` for 96-well; scale to 384-well if used).

### 14.3 Calculation (Median-Polish B-score)
For a plate matrix X_ij (row i, column j):

1) Median polish to estimate row and column biases
   - Iteratively:
     - `r_i ← median_j(X_ij − c_j)`
     - `c_j ← median_i(X_ij − r_i)`
   - After convergence: residuals `R_ij = X_ij − (r_i + c_j)`.

2) Robust scaling by MAD

   `MAD_R = median(|R − median(R)|)`,
   `B_ij = (R_ij − median(R)) / (1.4826 × MAD_R)`

- Output: B-score matrix `B_ij` (mean ~ 0, robustly scaled).
- Handle missing wells with NaN — ignored in medians.

### 14.4 Outputs
- New columns/fields per selected metric, e.g. `B_Z_lptA`, `B_Z_ldtD`.
- Heatmap option to render Raw Z vs B-score (toggle).
- Side-by-side plate visuals (raw vs B-score) in the report.

### 14.5 UI/Config
- Toggle: Heatmap metric: `Raw Z | B-score | Ratio | OD_norm`.
- Config: `bscore.max_iter` (default: 10), `bscore.tol` (default: 1e-6), `bscore.apply_to` (list of metrics).

### 14.6 Validation
- On synthetic plates with injected row/column gradients, B-scores should suppress gradients (R² vs row/col index ~ 0).
- Numerical stability tests with missing wells and constant rows/columns.

---

## 15. Edge-Effect Warning System

### 15.1 Purpose
Automatically detect and warn the user when spatial artifacts are likely distorting results. Provide simple, explainable diagnostics plus thresholds that can be tuned.

### 15.2 Diagnostics (per plate; run on a chosen metric, default Raw Z)
1) Edge vs Interior Test
   - Define edge wells = first/last row and first/last column.
   - Compute difference in medians between edge and interior.
   - Effect size `d = (median(edge) − median(interior)) / MAD(interior)`.
   - Warn if `|d| ≥ threshold` (default 0.8).

2) Row/Column Trend (Monotonic Drift)
   - Regress median per column against index; same for rows.
   - Warn if correlation ≥ threshold (default 0.5) and p < 0.05.

3) Corner Hot/Cold Spots
   - Compare corner wells' median vs plate median.
   - Warn if deviation exceeds threshold MADs (default 1.2).

4) Spatial Autocorrelation (optional)
   - Moran's I test; warn if p < 0.05 (disabled by default).

### 15.3 Warning Levels
- INFO: mild separation (`|d| = 0.5`).
- WARN: moderate (`|d| = 0.8`) or significant row/col trend.
- CRITICAL: large separation (`|d| = 1.5`) or multiple diagnostics triggered.

### 15.4 UI Behavior
- Heatmap header shows badge: `No edge effect | Mild | Warning | Critical`.
- Tooltip links to Edge Diagnostics panel with metrics (`d`, `ρ_row`, `ρ_col`, p-values).
- Action hint: "Consider B-score view" with one-click toggle.

### 15.5 Report Integration
- Executive Summary — QC: add per-plate edge diagnostics summary.
- Visualizations: include Raw Z vs B-score heatmaps side-by-side.
- Notes: state that B-scoring removes row/column biases but not biological effects.

### 15.6 Configuration (defaults)
```yaml
edge_warning:
  metric: "Z_lptA"
  min_group_wells: 16
  thresholds:
    effect_size_d: 0.8
    spearman_rho: 0.5
    corner_mads: 1.2
  levels:
    info_d: 0.5
    warn_d: 0.8
    critical_d: 1.5
  spatial_autocorr:
    enabled: false
```

### 15.7 Testing
- Synthetic plates with known edge lift — expect WARN/CRITICAL.
- Linear row/col drift — expect trend warning.
- No artifact — expect "No edge effect".

---

## 16. Changes to Heatmaps & Top-Hits
- Heatmaps: metric selector includes `B-score`.
- Default color maps: diverging for Z/B-scores (center=0), sequential for ratios/OD.
- Missing wells shown as neutral glyphs.
- Top Hits: allow ranking by B-scores; show Raw Z and B-score side by side.

---

## 17. Developer Notes
- Performance: median-polish on 96/384 wells is trivial; cache per plate.
- Numerics: guard for zero MAD (return NaN, mark in QC).
- Robustness: use NaN-aware medians.
- Extensibility: `bscore.apply_to` can list any reporter metric.

