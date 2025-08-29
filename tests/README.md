# Bio-Hit-Finder Test Suite

Comprehensive test suite for the bio-hit-finder platform, implementing thorough validation of all core functionality according to PRD specifications.

## Test Structure

### Core Test Files

- **`test_calculations.py`** - Unit tests for core calculation functions
- **`test_integration.py`** - End-to-end workflow and multi-plate processing tests  
- **`test_golden.py`** - Golden reference tests with exact numerical validation (≤1e-9)
- **`test_performance.py`** - Performance benchmarks against PRD targets
- **`test_visualizations.py`** - Chart generation and export format validation
- **`test_export.py`** - CSV/PDF/ZIP export functionality validation

### Specialized Test Files  

- **`test_statistics.py`** - Statistical calculation validation
- **`test_plate_processor.py`** - Plate processing pipeline tests
- **`test_bscore.py`** - B-scoring algorithm validation
- **`test_edge_effects.py`** - Edge effect detection validation

### Test Fixtures

- **`fixtures/sample_plates.py`** - Sample plate data generators
- **`fixtures/conftest.py`** - Shared pytest fixtures and configuration

## Test Categories

### Unit Tests (`pytest -m unit`)
Fast, isolated tests for individual functions and classes:
- Reporter ratio calculations: `Ratio_lptA = BG_lptA / BT_lptA`
- OD normalization: `OD_norm = OD / median(OD)`  
- Robust Z-scores: `Z = (value - median) / (1.4826 * MAD)`
- Viability gating: `viable = BT >= f * median(BT)`
- Statistical functions (median, MAD, robust scaling)

### Integration Tests (`pytest -m integration`)
End-to-end workflow validation:
- Complete plate processing pipelines
- Multi-plate aggregation and analysis
- Export functionality integration
- Performance benchmarks (< 200ms single plate, < 2s for 10 plates)
- Memory usage validation (< 1GB for 10 plates)

### Golden Tests (`pytest -m golden`)
Reference data validation with exact numerical precision:
- Hand-calculated reference values for all formulas
- Numerical tolerance validation (≤ 1e-9 as specified in PRD)
- Edge case handling (NaN, zero MAD, constant values)
- B-scoring validation against reference calculations
- Reproducibility testing (identical results across runs)

### Performance Tests (`pytest -m performance`)
Benchmark validation against PRD targets:
- **Single plate**: < 200ms for ~2000 rows
- **10 plates**: < 2s end-to-end including visualizations  
- **Memory usage**: < 1GB for 10 plates (~20,000 rows total)
- Large dataset handling and scalability limits
- Caching effectiveness and memory cleanup

### Visualization Tests (`pytest -m visualization`)
Chart and plot generation validation:
- Histogram, scatter plot, box plot generation
- 96-well and 384-well heatmap layouts
- Color mapping (diverging for Z-scores, sequential for ratios)
- Missing data handling in plots
- Export formats (PNG, SVG, HTML) with high DPI support

### Export Tests (`pytest -m export`)
Data export functionality validation:
- CSV format validation with numerical precision
- PDF report generation with mathematical formulas
- ZIP bundle integrity and manifest validation
- File I/O error handling
- Large dataset export performance

## Running Tests

### Using the Test Runner Script

```bash
# Quick overview of test categories
python run_tests.py --list

# Run specific test categories
python run_tests.py unit           # Fast unit tests
python run_tests.py integration    # End-to-end tests
python run_tests.py golden         # Reference validation
python run_tests.py performance    # Benchmark tests
python run_tests.py quick          # Unit + integration (skip slow)
python run_tests.py all            # Complete suite

# Generate coverage report
python run_tests.py coverage
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit -v                  # Unit tests only
pytest -m integration -v           # Integration tests only  
pytest -m golden -v                # Golden reference tests
pytest -m "not slow" -v            # Skip slow tests

# Run specific test files
pytest tests/test_golden.py -v
pytest tests/test_performance.py::TestCoreCalculationPerformance -v

# Run with coverage
pytest --cov=core --cov=analytics --cov-report=html
```

## Test Data and Fixtures

### Sample Plate Types

The test suite includes comprehensive sample data:

- **Normal plates**: Typical biological variation
- **Edge effect plates**: Evaporation and temperature gradients  
- **Plates with hits**: Planted extreme outliers for hit detection
- **Missing data plates**: Random missing values for robustness
- **Empty plates**: Template structures with no measurements
- **Constant value plates**: Testing MAD=0 edge cases
- **Multi-plate datasets**: For aggregation and batch processing

### Reference Calculations

Golden test fixtures include hand-calculated reference values:
- Simple datasets with known statistical properties
- Expected outputs for all core formulas
- B-scoring reference matrices with artificial row/column bias
- Edge effect detection test cases

## Performance Requirements (PRD Validation)

The test suite validates these PRD performance targets:

1. **Single plate processing**: < 200ms for ~2000 rows
2. **Multi-plate processing**: < 2s for 10 plates with visualizations  
3. **Memory usage**: < 1GB for 10 plates (~20,000 rows total)
4. **Numerical precision**: ≤ 1e-9 difference from reference calculations
5. **Reproducibility**: Identical results across multiple runs

## Test Configuration

### pytest.ini
- Comprehensive markers for test categorization
- Coverage configuration (80% minimum)
- Warning filters and logging setup  
- Timeout configuration (5 minutes max per test)

### Continuous Integration
Ready for CI/CD integration with:
- Parallel test execution support
- JUnit XML output for CI reporting
- Coverage XML for external tools
- Configurable test selection for fast/full runs

## Error Handling Tests

Comprehensive validation of error scenarios:
- Missing or invalid input columns
- Empty datasets and all-NaN values
- File I/O errors and permission issues
- Memory limits and disk space errors
- Malformed plate layouts and data corruption

## Extending the Test Suite

### Adding New Tests

1. Choose appropriate test file based on functionality
2. Use existing fixtures from `fixtures/conftest.py`
3. Follow naming conventions (`test_*` functions)
4. Add appropriate pytest markers
5. Include both success and error cases
6. Validate numerical precision for calculations

### Creating New Fixtures

1. Add sample data generators to `fixtures/sample_plates.py`
2. Register fixtures in `fixtures/conftest.py`
3. Ensure reproducible data with fixed random seeds
4. Document fixture characteristics and intended use

### Performance Test Guidelines

1. Include warm-up runs to exclude JIT/caching effects
2. Use `time.perf_counter()` for high-resolution timing
3. Monitor memory usage with `psutil` 
4. Test with realistic data sizes per PRD specifications
5. Validate both time and memory constraints

## Dependencies

Core testing dependencies:
- `pytest` (≥7.4.0) - Test framework
- `pytest-cov` (≥4.1.0) - Coverage reporting
- `pytest-benchmark` (≥4.0.0) - Performance benchmarking
- `hypothesis` (≥6.82.0) - Property-based testing
- `psutil` - Memory monitoring for performance tests

Optional for specific test categories:
- `playwright` - UI testing (if implemented)
- `selenium` - Browser automation (if needed)

## Coverage Goals

Target coverage levels by module:
- **core/**: 95% line coverage
- **analytics/**: 90% line coverage  
- **visualizations/**: 85% line coverage
- **export/**: 90% line coverage
- **Overall**: 80% minimum

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies installed and PYTHONPATH set
2. **Performance test failures**: May vary by hardware; adjust tolerances if needed
3. **Visualization test failures**: May require display/GUI support
4. **Export test failures**: Check file permissions and disk space

### Debug Options

```bash
# Verbose output with full tracebacks
pytest -v --tb=long

# Stop on first failure
pytest -x

# Run specific failing test
pytest tests/test_golden.py::TestGoldenReporterRatios::test_exact_ratio_calculations -v

# Debug with pdb
pytest --pdb tests/test_calculations.py::test_specific_function
```