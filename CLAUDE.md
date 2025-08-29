# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a plate data processing and analysis platform for biological research. The system ingests raw plate measurement data and produces normalized ratios, robust statistical scores (Z-scores and B-scores), viability flags, and quality control metrics to help researchers identify candidate hits and assess plate performance.

## Architecture

The platform is designed as a Streamlit-based web application with the following key components:

### Data Processing Pipeline
- **Input Processing**: Handles tabular plate data with required measurement columns (BG/BT ratios for lptA/ldtD, OD measurements for WT/tolC/SA strains)
- **Normalization**: Computes reporter ratios (BG/BT) and OD normalizations relative to plate-wide medians
- **Statistical Scoring**: Implements robust Z-scores using median and MAD, plus optional B-scoring for row/column bias correction
- **Quality Control**: Viability gating based on ATP levels, edge-effect detection, and spatial artifact warnings

### Key Calculations
- Reporter ratios: `Ratio_lptA = BG_lptA / BT_lptA`, `Ratio_ldtD = BG_ldtD / BT_ldtD`
- Robust Z-scores: `Z = (value - median) / (1.4826 * MAD)`
- B-scores: Median-polish row/column bias correction followed by robust scaling
- Viability gates: Wells with ATP < f * median(ATP) are flagged (default f=0.3)

### UI Structure (Streamlit)
- **Summary Tab**: Overview metrics, edge-effect diagnostics
- **Hits Tab**: Ranked candidate hits with configurable thresholds
- **Visualizations Tab**: Histograms, scatter plots, bar charts
- **Heatmaps Tab**: Plate visualizations with Raw Z vs B-score options
- **QC Report Tab**: PDF export with formulas and methodology

## Development Commands

Since this appears to be a new repository with only a PRD specification, the following commands will need to be implemented as the project develops:

### Python Environment
- Use Python 3.11+
- Key dependencies: pandas/polars, numpy, scipy, plotly, streamlit, openpyxl

### Running the Application
```bash
# Local development (once implemented)
streamlit run app.py

# With hot reload for development
streamlit run app.py --server.runOnSave true
```

### Testing
```bash
# Unit tests for calculations (once implemented)
pytest tests/

# Run specific test file
pytest tests/test_calculations.py

# Golden tests with reference data
pytest tests/test_golden.py -v
```

### Code Quality
```bash
# Linting (once configured)
ruff check .

# Type checking (once configured) 
mypy .

# Format code (once configured)
ruff format .
```

## Configuration

The system uses a hierarchical configuration approach:
- Built-in defaults for all parameters
- `config.yaml` for deployment-specific overrides
- UI controls for session-specific adjustments

Key configurable parameters:
- Viability gate threshold (default: 0.3)
- Z-score cutoffs for hit calling
- Edge-effect warning thresholds
- B-scoring iteration limits and tolerance
- Export formats and options

## Performance Targets

- Single plate (~2,000 rows): < 200ms processing
- 10 plates with visualizations: < 2s end-to-end
- Memory usage: < 1GB for 10 plates

## Validation Requirements

All calculations must be numerically reproducible with tolerance ≤ 1e-9 compared to reference implementations. The system must handle missing values gracefully and document edge cases like zero MAD values.