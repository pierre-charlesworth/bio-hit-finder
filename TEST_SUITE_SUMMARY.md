# Bio-Hit-Finder Comprehensive Test Suite

## Overview

Complete test suite implementation for the bio-hit-finder platform following PRD validation requirements. The test suite provides comprehensive coverage of all platform functionality with strict adherence to specified performance and numerical precision requirements.

## Test Suite Structure

### 📁 Core Test Files

| File | Purpose | Test Count | Coverage |
|------|---------|------------|----------|
| **test_integration.py** | End-to-end workflow validation | 25+ tests | Multi-plate processing, performance benchmarks |
| **test_golden.py** | Reference data validation (≤1e-9 precision) | 30+ tests | Exact formula validation, numerical precision |
| **test_visualizations.py** | Chart generation and export validation | 20+ tests | Plotly integration, format validation |
| **test_export.py** | CSV/PDF/ZIP export functionality | 25+ tests | File I/O, format integrity, error handling |
| **test_performance.py** | Benchmark validation against PRD targets | 15+ tests | Speed, memory, scalability limits |

### 📁 Supporting Test Files

- `test_calculations.py` - Unit tests for core calculation functions
- `test_statistics.py` - Statistical function validation
- `test_plate_processor.py` - Plate processing pipeline tests
- `test_bscore.py` - B-scoring algorithm validation  
- `test_edge_effects.py` - Edge effect detection validation

### 📁 Test Infrastructure

- **`fixtures/`** - Comprehensive test data and reference calculations
  - `sample_plates.py` - Sample plate data generators (12 fixture types)
  - `conftest.py` - Shared pytest fixtures and configuration
  - Generated CSV fixtures and JSON reference data

## Key Testing Requirements Implemented

### ✅ PRD Validation Requirements

1. **Numerical Tolerance**: All calculations tested to ≤ 1e-9 precision
2. **Performance Targets**:
   - Single plate (2000 rows): < 200ms ✓
   - 10 plates: < 2s end-to-end ✓
   - Memory usage: < 1GB for 10 plates ✓
3. **Formula Validation**: Exact implementation of PRD formulas
4. **Edge Case Handling**: Missing values, MAD=0, empty datasets
5. **Reproducibility**: Identical results across multiple runs

### ✅ Core Calculation Testing

**Reporter Ratios**: `Ratio_lptA = BG_lptA / BT_lptA`
- Golden reference validation
- Division by zero handling
- NaN propagation testing

**OD Normalization**: `OD_norm = OD / median(OD)`
- Median calculation validation
- Zero median handling
- Multi-column normalization

**Robust Z-scores**: `Z = (value - median) / (1.4826 * MAD)`
- MAD calculation accuracy
- Robust scaling factor (1.4826)
- Zero MAD edge cases

**Viability Gates**: `viable = BT >= f * median(BT)`
- Threshold calculations
- Multiple threshold testing
- Boolean flag validation

### ✅ Advanced Feature Testing

**B-scoring (Row/Column Bias Correction)**
- Median polish algorithm
- Bias removal validation
- Missing value handling

**Edge Effect Detection**
- Spatial artifact detection
- Statistical significance testing
- Warning level classification

**Multi-plate Aggregation**
- Cross-plate consistency
- PlateID tracking
- Statistical aggregation

## Test Categories and Execution

### 🚀 Quick Test Runs

```bash
# Smoke test (30 seconds)
python run_tests.py smoke

# Unit tests only (1 minute)  
python run_tests.py unit

# Quick validation (2-3 minutes)
python run_tests.py quick
```

### 🔬 Comprehensive Testing

```bash
# Golden reference tests
python run_tests.py golden

# Performance benchmarks
python run_tests.py performance

# Complete test suite
python run_tests.py all
```

### 📊 Coverage Analysis

```bash
# Generate coverage report
python run_tests.py coverage

# View results
# - Terminal summary: Immediate feedback
# - HTML report: htmlcov/index.html  
# - XML report: coverage.xml (CI/CD)
```

## Test Data and Fixtures

### 📋 Sample Plate Types

1. **Normal Plates**: Typical biological variation patterns
2. **Edge Effect Plates**: Evaporation/temperature gradients
3. **Plates with Hits**: Planted extreme outliers for validation
4. **Missing Data Plates**: Random missing values for robustness
5. **Empty Plates**: Template structures for edge cases
6. **Constant Value Plates**: MAD=0 scenarios
7. **Multi-plate Datasets**: Aggregation and batch processing
8. **Large Format Plates**: 384-well and 1536-well support

### 🎯 Golden Reference Data

- Hand-calculated reference values for all formulas
- Known statistical properties (median, MAD, Z-scores)
- B-scoring matrices with artificial bias patterns
- Edge effect detection test cases
- Numerical precision validation datasets

## Performance Validation

### ⚡ Speed Benchmarks

| Test Scenario | PRD Target | Test Validation |
|--------------|------------|----------------|
| Single plate (~2000 rows) | < 200ms | ✅ Automated benchmark |
| 10 plates with visualizations | < 2s | ✅ End-to-end timing |
| Large format (1536 wells) | < 5s | ✅ Scalability test |

### 💾 Memory Benchmarks

| Test Scenario | PRD Target | Test Validation |
|--------------|------------|----------------|
| Single large plate | < 200MB | ✅ Memory monitoring |
| 10 plates (~20,000 rows) | < 1GB | ✅ Peak memory tracking |
| Memory cleanup | No leaks | ✅ Garbage collection validation |

## Error Handling Coverage

### 🛡️ Input Validation

- Missing required columns
- Invalid data types
- Malformed plate layouts
- Empty and all-NaN datasets

### 🔧 System Error Handling

- File I/O permissions and disk space
- Memory limit scenarios  
- Network connectivity (if applicable)
- Concurrent processing simulation

### ⚠️ Edge Case Robustness

- Division by zero scenarios
- Constant value datasets (MAD=0)
- Extreme outlier handling
- Missing well positions

## Continuous Integration Ready

### 📋 CI/CD Integration Features

- **Parallel execution**: pytest-xdist support
- **JUnit XML output**: Standard CI reporting format
- **Coverage XML**: SonarQube/CodeClimate integration  
- **Configurable test selection**: Fast vs. comprehensive runs
- **Docker compatibility**: Containerized testing support

### 🎛️ Test Configuration

```ini
# pytest.ini - Comprehensive configuration
[tool:pytest]
testpaths = tests
markers = unit, integration, golden, performance, slow, visualization, export
addopts = --cov --strict-markers --tb=short
filterwarnings = ignore::UserWarning
```

## Quality Metrics

### 📈 Coverage Targets

- **Core modules**: 95% line coverage
- **Analytics**: 90% line coverage  
- **Visualizations**: 85% line coverage
- **Export**: 90% line coverage
- **Overall minimum**: 80% coverage

### 🧪 Test Quality Standards

- **Golden tests**: ≤ 1e-9 numerical precision
- **Performance tests**: PRD compliance validation
- **Integration tests**: End-to-end workflow coverage
- **Error scenarios**: Comprehensive failure mode testing
- **Reproducibility**: Fixed seeds, deterministic results

## Usage Examples

### Development Testing

```bash
# During development - quick feedback
python run_tests.py unit

# Before commit - comprehensive validation  
python run_tests.py quick

# Performance regression testing
python run_tests.py performance
```

### Release Validation

```bash
# Complete validation suite
python run_tests.py all

# Generate release report
python run_tests.py --report

# Validate specific functionality
pytest tests/test_golden.py -v
```

### Debugging

```bash
# Verbose debugging with full traces
pytest tests/test_calculations.py::test_specific_function -v --tb=long

# Stop on first failure for investigation
pytest -x --pdb

# Run single test with debugging
pytest tests/test_golden.py::TestGoldenEndToEnd::test_complete_pipeline_golden -s -v
```

## Extension Guidelines

### Adding New Tests

1. **Choose appropriate test file** based on functionality category
2. **Use existing fixtures** from `fixtures/conftest.py` 
3. **Follow naming conventions** (`test_*` functions, descriptive names)
4. **Add pytest markers** for proper categorization
5. **Include error cases** alongside success scenarios
6. **Validate numerical precision** for calculation tests

### Performance Test Guidelines

1. **Include warm-up runs** to exclude JIT compilation effects
2. **Use high-resolution timing** with `time.perf_counter()`
3. **Monitor memory usage** with `psutil` process monitoring
4. **Test realistic data sizes** matching PRD specifications
5. **Validate constraints** for both time and memory usage

## Summary

This comprehensive test suite provides:

✅ **Complete PRD compliance validation**  
✅ **Numerical precision testing (≤1e-9)**  
✅ **Performance benchmarking against targets**  
✅ **Robust error handling validation**  
✅ **CI/CD integration ready**  
✅ **Extensive fixture library**  
✅ **Multiple test execution strategies**  
✅ **Detailed coverage reporting**  

The test suite ensures platform reliability, performance, and correctness through systematic validation of all functionality described in the PRD specification.