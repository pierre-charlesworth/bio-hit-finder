"""Pytest configuration and shared fixtures for bio-hit-finder tests."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import shutil

from .sample_plates import (
    create_normal_96_well_plate,
    create_384_well_plate,
    create_plate_with_edge_effects,
    create_plate_with_hits,
    create_plate_with_missing_data,
    create_empty_plate,
    create_constant_value_plate,
    create_multi_plate_dataset,
    create_reference_calculations,
    create_bscore_reference_data
)


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for test outputs."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def normal_96_well_plate() -> pd.DataFrame:
    """Fixture providing normal 96-well plate data."""
    return create_normal_96_well_plate()


@pytest.fixture
def normal_384_well_plate() -> pd.DataFrame:
    """Fixture providing normal 384-well plate data."""
    return create_384_well_plate()


@pytest.fixture
def edge_effect_plate() -> pd.DataFrame:
    """Fixture providing plate with edge effects."""
    return create_plate_with_edge_effects()


@pytest.fixture
def plate_with_hits() -> pd.DataFrame:
    """Fixture providing plate with planted hits."""
    return create_plate_with_hits()


@pytest.fixture
def plate_with_missing() -> pd.DataFrame:
    """Fixture providing plate with missing data."""
    return create_plate_with_missing_data()


@pytest.fixture
def empty_plate() -> pd.DataFrame:
    """Fixture providing empty plate template."""
    return create_empty_plate()


@pytest.fixture
def constant_value_plate() -> pd.DataFrame:
    """Fixture providing plate with constant values."""
    return create_constant_value_plate()


@pytest.fixture
def multi_plate_dataset() -> List[pd.DataFrame]:
    """Fixture providing multiple plates for aggregation testing."""
    return create_multi_plate_dataset()


@pytest.fixture
def reference_calculations() -> Dict[str, Any]:
    """Fixture providing reference calculation results."""
    return create_reference_calculations()


@pytest.fixture
def bscore_reference_data() -> Dict[str, Any]:
    """Fixture providing B-score reference data."""
    return create_bscore_reference_data()


@pytest.fixture
def sample_processed_data() -> pd.DataFrame:
    """Fixture providing sample processed data with all calculated columns."""
    base_data = create_normal_96_well_plate()
    
    # Add calculated columns that would be present after processing
    base_data['Ratio_lptA'] = base_data['BG_lptA'] / base_data['BT_lptA']
    base_data['Ratio_ldtD'] = base_data['BG_ldtD'] / base_data['BT_ldtD']
    
    # Add normalized OD values
    base_data['OD_WT_norm'] = base_data['OD_WT'] / base_data['OD_WT'].median()
    base_data['OD_tolC_norm'] = base_data['OD_tolC'] / base_data['OD_tolC'].median()
    base_data['OD_SA_norm'] = base_data['OD_SA'] / base_data['OD_SA'].median()
    
    # Add Z-scores (simplified calculation)
    for ratio_col in ['Ratio_lptA', 'Ratio_ldtD']:
        values = base_data[ratio_col]
        median = values.median()
        mad = np.median(np.abs(values - median))
        if mad > 0:
            base_data[f'Z_{ratio_col.split("_")[1]}'] = (values - median) / (1.4826 * mad)
        else:
            base_data[f'Z_{ratio_col.split("_")[1]}'] = np.nan
    
    # Add viability flags
    for bt_col in ['BT_lptA', 'BT_ldtD']:
        reporter = bt_col.split('_')[1]
        threshold = 0.3 * base_data[bt_col].median()
        base_data[f'viability_ok_{reporter}'] = base_data[bt_col] >= threshold
        base_data[f'viability_fail_{reporter}'] = base_data[bt_col] < threshold
    
    return base_data


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Fixture providing sample configuration."""
    return {
        'viability_threshold': 0.3,
        'z_score_threshold': 2.0,
        'bscore_enabled': True,
        'bscore_max_iter': 10,
        'bscore_tolerance': 1e-6,
        'edge_detection_enabled': True,
        'edge_effect_threshold': 0.8,
        'export_formats': ['csv', 'pdf'],
        'plate_type': '96-well',
        'include_plots': True
    }


@pytest.fixture
def large_dataset() -> pd.DataFrame:
    """Fixture providing large dataset for performance testing."""
    # Create dataset with ~2000 rows (simulating large plate or multiple plates)
    base_plate = create_normal_96_well_plate()
    
    # Replicate and modify to create larger dataset
    large_data_frames = []
    
    for i in range(21):  # 96 * 21 ≈ 2016 rows
        plate_copy = base_plate.copy()
        plate_copy['Well'] = plate_copy['Well'] + f'_rep{i}'
        plate_copy['PlateID'] = f'Large_Plate_{i // 7 + 1}'  # Group into ~3 plates
        
        # Add slight variation between replicates
        noise_factor = 1.0 + np.random.normal(0, 0.05)
        measurement_cols = ['BG_lptA', 'BG_ldtD', 'BT_lptA', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']
        for col in measurement_cols:
            plate_copy[col] *= noise_factor
        
        large_data_frames.append(plate_copy)
    
    return pd.concat(large_data_frames, ignore_index=True)


@pytest.fixture
def performance_test_data() -> Dict[str, pd.DataFrame]:
    """Fixture providing datasets of various sizes for performance testing."""
    datasets = {}
    
    # Small dataset (96 wells)
    datasets['small'] = create_normal_96_well_plate()
    
    # Medium dataset (384 wells)
    datasets['medium'] = create_384_well_plate()
    
    # Large dataset (multiple 96-well plates)
    large_plates = create_multi_plate_dataset(n_plates=10)
    datasets['large'] = pd.concat(large_plates, ignore_index=True)
    
    # Extra large dataset (simulating 10 plates with ~2000 rows each)
    xl_plates = []
    for i in range(10):
        base_plate = create_normal_96_well_plate(seed=100 + i)
        
        # Expand each plate to ~2000 rows
        expanded_frames = []
        for j in range(21):
            plate_copy = base_plate.copy()
            plate_copy['Well'] = plate_copy['Well'] + f'_sub{j}'
            plate_copy['PlateID'] = f'XL_Plate_{i+1:02d}'
            expanded_frames.append(plate_copy)
        
        expanded_plate = pd.concat(expanded_frames, ignore_index=True)
        xl_plates.append(expanded_plate)
    
    datasets['extra_large'] = pd.concat(xl_plates, ignore_index=True)
    
    return datasets


@pytest.fixture(autouse=True)
def reset_random_state():
    """Reset random state before each test for reproducibility."""
    np.random.seed(42)


@pytest.fixture(scope="session")
def save_test_fixtures(fixtures_dir):
    """Save test fixtures to files at session start."""
    from .sample_plates import save_fixtures_to_files
    
    try:
        file_paths = save_fixtures_to_files(str(fixtures_dir))
        yield file_paths
    except Exception as e:
        pytest.skip(f"Could not save fixtures: {e}")


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "golden: Golden reference tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "visualization: Visualization tests")
    config.addinivalue_line("markers", "export: Export functionality tests")


# Custom pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on file names
        if "test_golden" in str(item.fspath):
            item.add_marker(pytest.mark.golden)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "test_visualizations" in str(item.fspath):
            item.add_marker(pytest.mark.visualization)
        elif "test_export" in str(item.fspath):
            item.add_marker(pytest.mark.export)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Auto-mark slow tests
        if "slow" in item.name.lower() or any("slow" in marker.name for marker in item.iter_markers()):
            item.add_marker(pytest.mark.slow)