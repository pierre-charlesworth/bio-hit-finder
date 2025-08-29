# Contributing to Bio Hit Finder

Thank you for your interest in contributing to Bio Hit Finder! This guide will help you get started with development setup, coding standards, and the contribution process.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Issue Guidelines](#issue-guidelines)
7. [Documentation](#documentation)
8. [Release Process](#release-process)

## Development Setup

### Prerequisites

- **Python 3.11+** (required)
- **Git** for version control
- **IDE/Editor** (VS Code recommended with Python extension)
- **Modern web browser** for testing Streamlit interface

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bio-hit-finder/bio-hit-finder.git
   cd bio-hit-finder
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Verify setup**:
   ```bash
   pytest --version
   ruff --version
   mypy --version
   streamlit --version
   ```

### Configuration

Create a `.env` file for development settings:
```bash
# .env
DEBUG=True
LOG_LEVEL=DEBUG
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### IDE Setup (VS Code)

Recommended extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Python Docstring Generator
- GitLens
- Black Formatter
- Ruff

VS Code settings (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".mypy_cache": true
    }
}
```

## Project Structure

### Directory Organization

```
bio-hit-finder/
├── .github/                 # GitHub workflows and templates
│   ├── workflows/
│   │   ├── ci.yml          # Continuous integration
│   │   └── release.yml     # Release automation
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── src/bio_hit_finder/     # Main source code (future structure)
├── core/                   # Core processing modules
├── analytics/              # Advanced analytics
├── visualizations/         # Plotting components
├── export/                 # Output generation
├── templates/              # Report templates
├── assets/                 # Static resources
├── data/                   # Sample data
├── tests/                  # Test suite
├── docs/                   # Documentation
│
├── app.py                  # Main Streamlit app
├── demo_mode.py           # Interactive demo
├── config.yaml            # Configuration
├── pyproject.toml         # Project metadata
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Development dependencies
└── README.md
```

### Module Guidelines

#### Core Modules (`core/`)
- **Purpose**: Fundamental data processing functionality
- **Dependencies**: Minimal external dependencies
- **Testing**: High test coverage (>90%)
- **Documentation**: Comprehensive docstrings

#### Analytics Modules (`analytics/`)
- **Purpose**: Specialized statistical and biological analysis
- **Dependencies**: Scientific libraries (scipy, scikit-learn)
- **Testing**: Mathematical correctness validation
- **Documentation**: Algorithm explanations and references

#### Visualization Modules (`visualizations/`)
- **Purpose**: Interactive plotting and visualization
- **Dependencies**: Plotly, matplotlib
- **Testing**: Visual regression testing where possible
- **Documentation**: Usage examples and customization options

## Coding Standards

### Python Code Style

We use **Ruff** for linting and **Black** for formatting:

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Configuration Files

#### `pyproject.toml` - Ruff Configuration
```toml
[tool.ruff]
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"tests/**/*" = ["S101"]  # allow assert statements in tests

[tool.black]
line-length = 88
target-version = ['py311']
```

### Type Hints

Use type hints for all public functions and methods:

```python
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np

def calculate_robust_zscore(
    values: np.ndarray,
    center: str = 'median',
    scale: str = 'mad'
) -> np.ndarray:
    """
    Calculate robust Z-scores using median and MAD.
    
    Args:
        values: Array of numeric values
        center: Centering method ('median' or 'mean')
        scale: Scaling method ('mad' or 'std')
        
    Returns:
        Array of Z-scores with same shape as input
        
    Raises:
        ValueError: If center or scale method is invalid
    """
```

### Docstring Standards

Use **Google-style docstrings**:

```python
def process_plate_data(
    df: pd.DataFrame,
    viability_threshold: float = 0.3,
    z_threshold: float = 2.0
) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
    """Process biological plate screening data.
    
    This function performs comprehensive analysis of plate-based screening data,
    including ratio calculations, statistical normalization, and hit identification.
    
    Args:
        df: Input DataFrame with required measurement columns
        viability_threshold: Minimum relative viability (0.0-1.0)
        z_threshold: Z-score threshold for hit calling (>0.0)
        
    Returns:
        Dictionary containing:
            - 'results': Processed DataFrame with calculated metrics
            - 'summary': Dictionary of summary statistics
            - 'hits': DataFrame of identified hits
            
    Raises:
        ValueError: If required columns are missing
        RuntimeError: If calculation fails due to insufficient data
        
    Example:
        >>> raw_data = pd.read_csv('plate_data.csv')
        >>> results = process_plate_data(raw_data, z_threshold=2.5)
        >>> print(f"Found {len(results['hits'])} hits")
        Found 15 hits
    """
```

### Error Handling

Use custom exception classes for domain-specific errors:

```python
class PlateProcessingError(Exception):
    """Base exception for plate processing errors."""
    pass

class DataValidationError(PlateProcessingError):
    """Raised when input data validation fails."""
    pass

class CalculationError(PlateProcessingError):
    """Raised when statistical calculations fail."""
    pass

# Usage
def validate_required_columns(df: pd.DataFrame, required: List[str]) -> None:
    """Validate that required columns are present."""
    missing = set(required) - set(df.columns)
    if missing:
        raise DataValidationError(
            f"Missing required columns: {sorted(missing)}. "
            f"Available columns: {sorted(df.columns)}"
        )
```

### Logging

Use structured logging throughout the application:

```python
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def log_execution_time(func):
    """Decorator to log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f}s: {e}")
            raise
    
    return wrapper
```

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration
├── fixtures/                # Test data
│   ├── __init__.py
│   ├── sample_plates.py    # Test data generation
│   └── *.csv               # Sample CSV files
├── unit/                   # Unit tests
│   ├── test_calculations.py
│   ├── test_statistics.py
│   └── test_plate_processor.py
├── integration/            # Integration tests
│   ├── test_full_pipeline.py
│   └── test_export_workflow.py
└── performance/            # Performance tests
    └── test_large_datasets.py
```

### Unit Testing

Use **pytest** with comprehensive fixtures:

```python
# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def sample_96well_data():
    """Generate standard 96-well plate data."""
    np.random.seed(42)  # Reproducible results
    
    n_wells = 96
    data = {
        'Well': [f"{chr(65 + i//12)}{(i%12)+1:02d}" for i in range(n_wells)],
        'BG_lptA': np.random.normal(1000, 200, n_wells),
        'BT_lptA': np.random.normal(2000, 300, n_wells),
        'BG_ldtD': np.random.normal(800, 150, n_wells),
        'BT_ldtD': np.random.normal(1500, 250, n_wells),
        'OD_WT': np.random.normal(0.5, 0.1, n_wells),
        'OD_tolC': np.random.normal(0.4, 0.08, n_wells),
        'OD_SA': np.random.normal(0.45, 0.09, n_wells),
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def mock_hits_data(sample_96well_data):
    """Generate data with known hits."""
    df = sample_96well_data.copy()
    
    # Add strong hits (low ratios)
    hit_indices = [10, 25, 47, 63, 81]  # Known hit positions
    for idx in hit_indices:
        df.iloc[idx, df.columns.get_loc('BG_lptA')] *= 0.3  # 70% reduction
        df.iloc[idx, df.columns.get_loc('BG_ldtD')] *= 0.3
    
    return df, hit_indices
```

### Test Examples

```python
# tests/unit/test_calculations.py
import pytest
import numpy as np
import pandas as pd
from core.calculations import calculate_robust_zscore, calculate_reporter_ratios

class TestRobustZScore:
    """Test robust Z-score calculations."""
    
    def test_robust_zscore_normal_distribution(self):
        """Test Z-score calculation on normal distribution."""
        np.random.seed(42)
        data = np.random.normal(100, 15, 1000)
        
        z_scores = calculate_robust_zscore(data)
        
        # Z-scores should have median ≈ 0 and MAD ≈ 1
        assert abs(np.median(z_scores)) < 0.1
        assert abs(np.median(np.abs(z_scores - np.median(z_scores))) - 1.0) < 0.1
    
    def test_robust_zscore_with_outliers(self):
        """Test that robust Z-scores handle outliers correctly."""
        # Data with extreme outliers
        data = np.concatenate([
            np.random.normal(100, 10, 95),  # Normal data
            [500, -500, 1000, -1000, 2000]  # Extreme outliers
        ])
        
        z_scores = calculate_robust_zscore(data)
        
        # Outliers should have extreme Z-scores
        outlier_z_scores = z_scores[-5:]
        assert all(abs(z) > 5 for z in outlier_z_scores)
        
        # Normal data should have reasonable Z-scores
        normal_z_scores = z_scores[:-5]
        assert np.mean(abs(normal_z_scores)) < 2.0
    
    def test_robust_zscore_edge_cases(self):
        """Test edge cases for Z-score calculation."""
        # Constant values
        constant_data = np.array([5.0] * 100)
        z_scores = calculate_robust_zscore(constant_data)
        assert np.allclose(z_scores, 0.0)
        
        # Single value
        single_value = np.array([42.0])
        z_scores = calculate_robust_zscore(single_value)
        assert z_scores[0] == 0.0
        
        # Two values
        two_values = np.array([10.0, 20.0])
        z_scores = calculate_robust_zscore(two_values)
        assert len(z_scores) == 2

class TestReporterRatios:
    """Test reporter ratio calculations."""
    
    def test_reporter_ratio_calculation(self, sample_96well_data):
        """Test basic ratio calculation."""
        df_with_ratios = calculate_reporter_ratios(sample_96well_data)
        
        # Check that ratio columns were added
        assert 'Ratio_lptA' in df_with_ratios.columns
        assert 'Ratio_ldtD' in df_with_ratios.columns
        
        # Verify calculations
        expected_lptA = sample_96well_data['BG_lptA'] / sample_96well_data['BT_lptA']
        expected_ldtD = sample_96well_data['BG_ldtD'] / sample_96well_data['BT_ldtD']
        
        pd.testing.assert_series_equal(df_with_ratios['Ratio_lptA'], expected_lptA)
        pd.testing.assert_series_equal(df_with_ratios['Ratio_ldtD'], expected_ldtD)
    
    def test_reporter_ratio_with_zeros(self):
        """Test ratio calculation with zero denominators."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200, 300],
            'BT_lptA': [50, 0, 100],  # Zero denominator
            'BG_ldtD': [80, 160, 240],
            'BT_ldtD': [40, 80, 120]
        })
        
        df_with_ratios = calculate_reporter_ratios(df)
        
        # Check that infinite values are handled appropriately
        assert pd.isna(df_with_ratios.iloc[1]['Ratio_lptA']) or \
               np.isinf(df_with_ratios.iloc[1]['Ratio_lptA'])
```

### Integration Testing

```python
# tests/integration/test_full_pipeline.py
import pytest
import pandas as pd
from core.plate_processor import PlateProcessor

class TestFullPipeline:
    """Test complete data processing pipeline."""
    
    def test_end_to_end_processing(self, sample_96well_data):
        """Test complete processing workflow."""
        processor = PlateProcessor(
            viability_threshold=0.3,
            z_threshold=2.0
        )
        
        results = processor.process_dataframe(sample_96well_data)
        
        # Verify all expected columns are present
        expected_columns = [
            'Ratio_lptA', 'Ratio_ldtD',
            'Z_lptA', 'Z_ldtD',
            'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm',
            'Viability_Gate_lptA', 'Viability_Gate_ldtD'
        ]
        
        for col in expected_columns:
            assert col in results.columns
        
        # Verify data integrity
        assert len(results) == len(sample_96well_data)
        assert results.isnull().sum().sum() == 0  # No unexpected NaN values
    
    def test_hit_identification_workflow(self, mock_hits_data):
        """Test hit identification in complete workflow."""
        df, expected_hit_indices = mock_hits_data
        
        processor = PlateProcessor(z_threshold=2.0)
        results = processor.process_dataframe(df)
        
        # Identify hits
        hits = results[
            (results['Z_lptA'].abs() > 2.0) | 
            (results['Z_ldtD'].abs() > 2.0)
        ]
        
        # Should identify some hits (exact number depends on data and thresholds)
        assert len(hits) > 0
        assert len(hits) <= len(expected_hit_indices)
```

### Performance Testing

```python
# tests/performance/test_large_datasets.py
import pytest
import pandas as pd
import numpy as np
import time
from core.plate_processor import PlateProcessor

class TestPerformance:
    """Test performance with large datasets."""
    
    @pytest.mark.slow
    def test_large_dataset_processing(self):
        """Test processing speed with large dataset."""
        # Generate large dataset (10 plates × 384 wells = 3,840 wells)
        n_wells = 10 * 384
        
        large_dataset = pd.DataFrame({
            'PlateID': [f"PLATE_{i//384 + 1:03d}" for i in range(n_wells)],
            'Well': [f"{chr(65 + (i%384)//24)}{((i%384)%24)+1:02d}" for i in range(n_wells)],
            'BG_lptA': np.random.normal(1000, 200, n_wells),
            'BT_lptA': np.random.normal(2000, 300, n_wells),
            'BG_ldtD': np.random.normal(800, 150, n_wells),
            'BT_ldtD': np.random.normal(1500, 250, n_wells),
            'OD_WT': np.random.normal(0.5, 0.1, n_wells),
            'OD_tolC': np.random.normal(0.4, 0.08, n_wells),
            'OD_SA': np.random.normal(0.45, 0.09, n_wells),
        })
        
        processor = PlateProcessor()
        
        start_time = time.time()
        results = processor.process_dataframe(large_dataset)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 10.0  # Should complete in <10 seconds
        assert len(results) == n_wells
        
        print(f"Processed {n_wells} wells in {processing_time:.2f} seconds")
        print(f"Processing rate: {n_wells/processing_time:.0f} wells/second")
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=analytics --cov=visualizations

# Run specific test file
pytest tests/unit/test_calculations.py

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m "integration"  # Run only integration tests

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_calculations.py::TestRobustZScore::test_robust_zscore_normal_distribution
```

## Pull Request Process

### Before Creating a PR

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following coding standards

3. **Add/update tests** for new functionality

4. **Run test suite**:
   ```bash
   pytest
   ```

5. **Check code quality**:
   ```bash
   ruff check .
   ruff format .
   mypy .
   ```

6. **Update documentation** if needed

### PR Checklist

- [ ] **Tests added/updated** for new functionality
- [ ] **All tests pass** locally
- [ ] **Code follows style guidelines** (ruff, black)
- [ ] **Type hints added** for new functions
- [ ] **Documentation updated** (docstrings, README, etc.)
- [ ] **No breaking changes** without version bump
- [ ] **PR description** explains changes and rationale

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing functionality)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)
Include screenshots for UI changes.

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
- [ ] New and existing unit tests pass locally
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Address feedback** and update PR as needed
4. **Final approval** from maintainer
5. **Merge** using "Squash and merge" strategy

## Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Windows 10, macOS 12]
 - Python version: [e.g. 3.11.2]
 - Bio Hit Finder version: [e.g. 2.1.0]
 - Browser (if applicable): [e.g. Chrome 96]

**Additional Context**
Any other context about the problem.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the requested feature.

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other solutions you've considered.

**Additional Context**
Any other context, mockups, or examples.
```

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information requested
- `wontfix`: Issue will not be addressed

## Documentation

### User Documentation

Located in `docs/user_guide/`:
- Written in Markdown
- Focus on practical usage
- Include examples and screenshots
- Test all code examples

### API Documentation

Generated from docstrings:
```bash
# Generate API docs
pdoc --html --output-dir docs/api bio_hit_finder
```

### Development Documentation

Located in `docs/development/`:
- Architecture decisions
- Development setup
- Contributing guidelines
- Deployment instructions

### Documentation Standards

1. **Use clear, concise language**
2. **Include practical examples**
3. **Keep examples up-to-date**
4. **Use screenshots for UI features**
5. **Link to related sections**

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite**
4. **Update documentation** if needed
5. **Create release tag**:
   ```bash
   git tag -a v2.1.0 -m "Release version 2.1.0"
   git push origin v2.1.0
   ```
6. **Build and publish** (automated via GitHub Actions)

### Release Notes Format

```markdown
## [2.1.0] - 2024-01-15

### Added
- New demo mode with interactive tutorials
- Support for 384-well plate format
- Enhanced sample data generation

### Changed
- Improved B-score calculation performance
- Updated default viability threshold to 0.3

### Fixed
- Edge effect detection for small plates
- Memory leak in large dataset processing

### Deprecated
- Legacy CSV export format (will be removed in v3.0)
```

## Getting Help

### Development Questions

- **GitHub Discussions**: General development questions
- **GitHub Issues**: Specific bugs or feature requests
- **Email**: maintainers@bio-hit-finder.com

### Resources

- **Documentation**: https://bio-hit-finder.readthedocs.io
- **Examples**: https://github.com/bio-hit-finder/examples
- **Community**: https://github.com/bio-hit-finder/community

---

Thank you for contributing to Bio Hit Finder! Your efforts help make biological data analysis more accessible and reliable for researchers worldwide.