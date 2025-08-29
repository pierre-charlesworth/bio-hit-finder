# Bio Hit Finder

> 🧬 Plate data processing and analysis platform for biological research

A comprehensive platform that ingests raw plate measurement data and produces normalized ratios, robust statistical scores (Z-scores and B-scores), viability flags, and quality control metrics to help researchers identify candidate hits and assess plate performance.

## Features

- **Data Processing Pipeline**: Handles tabular plate data with BG/BT ratios for lptA/ldtD and OD measurements for WT/tolC/SA strains
- **Robust Statistics**: Implements robust Z-scores using median and MAD, plus optional B-scoring for row/column bias correction  
- **Quality Control**: Viability gating based on ATP levels, edge-effect detection, and spatial artifact warnings
- **Interactive Visualizations**: Histograms, scatter plots, heatmaps, and quality control reports
- **Export Capabilities**: CSV, PDF reports, and ZIP bundles with processing artifacts

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip or uv for package management

### Installation

```bash
# Clone the repository
git clone https://github.com/bio-hit-finder/bio-hit-finder.git
cd bio-hit-finder

# Install dependencies
pip install -r requirements.txt

# Or install with optional dependencies
pip install -e ".[dev,polars]"
```

### Running the Application

```bash
# Start the Streamlit web interface
streamlit run app.py
```

The application will open in your web browser at `http://localhost:8501`.

## Core Calculations

### Reporter Ratios
```
Ratio_lptA = BG_lptA / BT_lptA
Ratio_ldtD = BG_ldtD / BT_ldtD
```

### OD Normalization
```
OD_WT_norm = OD_WT / median(OD_WT)
OD_tolC_norm = OD_tolC / median(OD_tolC)
OD_SA_norm = OD_SA / median(OD_SA)
```

### Robust Z-scores
```
Z = (value - median(values)) / (1.4826 * MAD(values))
where MAD = median(|X - median(X)|)
```

### Viability Gating
```
viability_ok = BT >= f * median(BT)  # default f = 0.3
```

## Input Data Format

The platform expects tabular data with the following required columns:

- `BG_lptA` - BetaGlo (reporter) for lptA
- `BT_lptA` - BacTiter (ATP/viability) for lptA  
- `BG_ldtD` - BetaGlo for ldtD
- `BT_ldtD` - BacTiter for ldtD
- `OD_WT` - optical density for wild-type strain
- `OD_tolC` - optical density for ΔtolC strain
- `OD_SA` - optical density for SA strain

Optional columns include plate identifier, well position, treatment ID, and control types.

## Project Structure

```
bio-hit-finder/
├── core/                 # Core data processing logic
├── analytics/           # B-scoring, edge effects analysis  
├── visualizations/      # Charts, heatmaps, plots
├── export/             # CSV, PDF, ZIP exports
├── templates/          # Jinja2 templates for reports
├── assets/             # CSS, static files
├── tests/              # Test suite
├── data/               # Sample data and fixtures
├── app.py              # Main Streamlit application
├── config.yaml         # Configuration defaults
├── pyproject.toml      # Project metadata and dependencies
└── requirements.txt    # Pip-compatible requirements
```

## Development

### Setting up Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .

# Format code  
ruff format .

# Type checking
mypy .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=analytics --cov=visualizations --cov=export

# Run specific test types
pytest -m "not slow"  # Skip slow tests
pytest -m golden      # Run golden tests only
```

## Configuration

The platform uses a hierarchical configuration system:

1. **Built-in defaults** for all parameters
2. **config.yaml** for deployment-specific overrides  
3. **UI controls** for session-specific adjustments

Key configurable parameters:
- Viability gate threshold (default: 0.3)
- Z-score cutoffs for hit calling
- Edge-effect warning thresholds
- B-scoring iteration limits and tolerance

## Performance

- Single plate (~2,000 rows): < 200ms processing
- 10 plates with visualizations: < 2s end-to-end
- Memory usage: < 1GB for 10 plates

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite and ensure all tests pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Support

For questions, issues, or feature requests, please:

1. Check the [documentation](https://bio-hit-finder.readthedocs.io)
2. Search [existing issues](https://github.com/bio-hit-finder/bio-hit-finder/issues)
3. Create a new issue with detailed information

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Uses [Plotly](https://plotly.com/python/) for interactive visualizations
- Statistical calculations powered by [NumPy](https://numpy.org/) and [SciPy](https://scipy.org/)
- Data processing with [Pandas](https://pandas.pydata.org/) and optional [Polars](https://pola.rs/) backend