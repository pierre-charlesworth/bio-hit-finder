# Bio-Hit-Finder Implementation Plan

## Phase 1: Project Setup & Core Infrastructure (Day 1)
**Agent: python-backend-engineer**
- Create project structure with proper Python package organization
- Set up dependencies with `uv` package manager
- Configure pyproject.toml, requirements.txt
- Create config.yaml with default parameters
- Set up logging infrastructure

## Phase 2: Core Data Processing Module (Day 1-2)
**Agent: python-backend-engineer + data-scientist**
- Implement `core/calculations.py`:
  - Reporter ratio calculations (BG/BT)
  - OD normalization functions
  - Robust Z-score computation with MAD
  - Viability gating logic
- Create `core/plate_processor.py`:
  - Plate data ingestion and validation
  - Column auto-detection and mapping
  - Multi-plate aggregation
- Build `core/statistics.py`:
  - Median and MAD calculations
  - NaN-safe operations
  - Edge case handling (zero MAD)

## Phase 3: Advanced Analytics (Day 2)
**Agent: data-scientist + performance-engineer**
- Implement `analytics/bscore.py`:
  - Median-polish algorithm for row/column bias
  - B-score calculation with convergence criteria
  - Caching strategy for performance
- Create `analytics/edge_effects.py`:
  - Edge vs interior diagnostics
  - Row/column trend detection (Spearman correlation)
  - Corner hot/cold spot analysis
  - Warning level system (INFO/WARN/CRITICAL)

## Phase 4: Streamlit UI Development (Day 2-3)
**Agent: frontend-developer + ui-ux-designer**
- Build `app.py` main Streamlit application
- Implement tab structure:
  - Summary tab with metrics and edge diagnostics
  - Hits tab with ranking and filtering
  - Visualizations tab with charts
  - Heatmaps tab with metric selector
  - QC Report tab with export options
- Add file upload with column mapping UI
- Implement session state management
- Create sidebar controls for parameters

## Phase 5: Visualization Components (Day 3)
**Agent: frontend-developer**
- Create `visualizations/charts.py`:
  - Plotly histograms with box overlays
  - Scatter plots (ratio comparisons)
  - Bar charts (viability counts)
- Build `visualizations/heatmaps.py`:
  - 96/384 well plate layouts
  - Raw Z vs B-score side-by-side
  - Color scale management (diverging/sequential)
  - Missing well handling

## Phase 6: Export & Reporting (Day 3-4)
**Agent: backend-architect**
- Implement `export/csv_export.py`:
  - Per-plate CSV export
  - Combined dataset export
  - Top-N hits export
- Create `export/pdf_generator.py`:
  - Jinja2 template system
  - Formula rendering with KaTeX
  - WeasyPrint HTML-to-PDF conversion
- Build `export/bundle.py`:
  - ZIP archive creation
  - Manifest.json generation
  - Plot export (PNG/SVG)

## Phase 7: Testing & Validation (Day 4)
**Agent: test-automator**
- Create `tests/test_calculations.py`:
  - Unit tests for all core calculations
  - Edge case testing (NaN, zero MAD, empty data)
- Build `tests/test_golden.py`:
  - Golden reference data fixtures
  - Numerical tolerance validation (1e-9)
- Add `tests/test_integration.py`:
  - End-to-end workflow tests
  - Multi-plate processing validation

## Phase 8: Performance & Optimization (Day 4)
**Agent: performance-engineer**
- Profile critical paths
- Implement caching with @st.cache_data
- Optimize pandas operations
- Add polars backend option for large datasets
- Ensure < 200ms for single plate, < 2s for 10 plates

## Phase 9: Sample Data & Documentation (Day 4)
**Agent: docs-architect**
- Generate synthetic plate data for demo
- Create user documentation
- Add inline help in UI
- Prepare deployment instructions

## Directory Structure:
```
bio-hit-finder/
├── app.py                 # Main Streamlit application
├── config.yaml           # Default configuration
├── pyproject.toml        # Project dependencies
├── requirements.txt      # Python dependencies
├── core/                 # Core processing logic
│   ├── __init__.py
│   ├── calculations.py   # Basic calculations
│   ├── plate_processor.py # Data ingestion
│   └── statistics.py     # Statistical functions
├── analytics/            # Advanced analytics
│   ├── __init__.py
│   ├── bscore.py        # B-scoring implementation
│   └── edge_effects.py   # Edge effect detection
├── visualizations/       # Plotting modules
│   ├── __init__.py
│   ├── charts.py        # Basic charts
│   └── heatmaps.py      # Plate heatmaps
├── export/              # Export functionality
│   ├── __init__.py
│   ├── csv_export.py    # CSV exports
│   ├── pdf_generator.py # PDF reports
│   └── bundle.py        # ZIP bundles
├── templates/           # Jinja2 templates
│   └── report.html      # PDF report template
├── assets/              # Static assets
│   └── styles.css       # Custom CSS
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_calculations.py
│   ├── test_golden.py
│   └── fixtures/        # Test data
└── data/                # Sample data
    └── sample_plate.csv

```

## Key Implementation Notes:
- Start with MVP features, add advanced features progressively
- Use Streamlit for rapid UI development
- Ensure all calculations are numerically stable and reproducible
- Cache expensive operations aggressively
- Follow the PRD's formulas exactly for validation
- Test with edge cases from the beginning

## Completion Checklist:
- [ ] Phase 1: Project Setup & Core Infrastructure
- [ ] Phase 2: Core Data Processing Module
- [ ] Phase 3: Advanced Analytics
- [ ] Phase 4: Streamlit UI Development
- [ ] Phase 5: Visualization Components
- [ ] Phase 6: Export & Reporting
- [ ] Phase 7: Testing & Validation
- [ ] Phase 8: Performance & Optimization
- [ ] Phase 9: Sample Data & Documentation