"""Integration tests for the bio-hit-finder platform.

Tests end-to-end workflows, multi-plate processing, UI component integration,
export functionality validation, and performance benchmarks as specified in PRD.
"""

import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import pytest

from core.plate_processor import PlateProcessor
from core.calculations import process_plate_calculations
from export.bundle import create_export_bundle
from export.csv_export import export_processed_data
from export.pdf_generator import generate_qc_report


class TestEndToEndWorkflow:
    """Test complete end-to-end processing workflows."""

    @pytest.fixture
    def sample_plate_data(self) -> pd.DataFrame:
        """Create sample plate data for testing."""
        np.random.seed(42)  # For reproducible tests
        
        # Generate 96-well plate data (8 rows x 12 columns)
        n_wells = 96
        
        data = {
            'Well': [f"{chr(65 + i // 12)}{(i % 12) + 1:02d}" for i in range(n_wells)],
            'Row': [chr(65 + i // 12) for i in range(n_wells)],
            'Col': [(i % 12) + 1 for i in range(n_wells)],
            'BG_lptA': np.random.normal(1000, 200, n_wells),
            'BT_lptA': np.random.normal(500, 100, n_wells),
            'BG_ldtD': np.random.normal(1200, 250, n_wells),
            'BT_ldtD': np.random.normal(600, 120, n_wells),
            'OD_WT': np.random.normal(1.5, 0.3, n_wells),
            'OD_tolC': np.random.normal(1.2, 0.25, n_wells),
            'OD_SA': np.random.normal(1.0, 0.2, n_wells),
        }
        
        # Add some hits (extreme values)
        hit_indices = [10, 25, 50, 75]
        for idx in hit_indices:
            data['BG_lptA'][idx] *= 3  # Make it a hit
            data['BG_ldtD'][idx] *= 2.5
        
        # Add some low viability wells
        low_viability_indices = [5, 15, 35, 55]
        for idx in low_viability_indices:
            data['BT_lptA'][idx] *= 0.1
            data['BT_ldtD'][idx] *= 0.1
        
        return pd.DataFrame(data)

    @pytest.fixture
    def multi_plate_data(self, sample_plate_data: pd.DataFrame) -> List[pd.DataFrame]:
        """Create multiple plate datasets for testing."""
        plates = []
        
        for plate_id in range(3):
            plate_data = sample_plate_data.copy()
            # Add plate identifier
            plate_data['PlateID'] = f"Plate_{plate_id + 1}"
            
            # Add some variation between plates
            noise_factor = 0.1 * plate_id
            for col in ['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD']:
                plate_data[col] *= (1 + noise_factor * np.random.normal(0, 0.1, len(plate_data)))
            
            plates.append(plate_data)
        
        return plates

    def test_single_plate_processing(self, sample_plate_data: pd.DataFrame):
        """Test processing a single plate through the complete pipeline."""
        # Process the plate
        result = process_plate_calculations(sample_plate_data, viability_threshold=0.3)
        
        # Verify all expected columns are present
        expected_columns = {
            # Original columns
            'Well', 'Row', 'Col', 'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD',
            'OD_WT', 'OD_tolC', 'OD_SA',
            # Calculated columns
            'Ratio_lptA', 'Ratio_ldtD',
            'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm',
            'Z_lptA', 'Z_ldtD',
            'viability_ok_lptA', 'viability_fail_lptA',
            'viability_ok_ldtD', 'viability_fail_ldtD'
        }
        
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Verify data integrity
        assert len(result) == len(sample_plate_data)
        assert result.isna().sum().sum() < len(result) * 0.1  # < 10% NaN values
        
        # Verify ratios are calculated correctly
        expected_ratio_lptA = sample_plate_data['BG_lptA'] / sample_plate_data['BT_lptA']
        np.testing.assert_allclose(
            result['Ratio_lptA'], 
            expected_ratio_lptA, 
            rtol=1e-9
        )
        
        # Verify viability gates work
        bt_lptA_median = sample_plate_data['BT_lptA'].median()
        threshold = 0.3 * bt_lptA_median
        expected_viable = sample_plate_data['BT_lptA'] >= threshold
        pd.testing.assert_series_equal(
            result['viability_ok_lptA'],
            expected_viable,
            check_names=False
        )

    def test_multi_plate_processing(self, multi_plate_data: List[pd.DataFrame]):
        """Test processing multiple plates and aggregation."""
        processor = PlateProcessor()
        
        # Process each plate
        processed_plates = []
        for plate_data in multi_plate_data:
            processed = processor.process_plate(plate_data, viability_threshold=0.3)
            processed_plates.append(processed)
        
        # Aggregate results
        combined_data = pd.concat(processed_plates, ignore_index=True)
        
        # Verify aggregation
        assert len(combined_data) == sum(len(p) for p in multi_plate_data)
        assert 'PlateID' in combined_data.columns
        assert len(combined_data['PlateID'].unique()) == len(multi_plate_data)
        
        # Verify calculations are consistent across plates
        for plate_id in combined_data['PlateID'].unique():
            plate_subset = combined_data[combined_data['PlateID'] == plate_id]
            
            # Z-scores should have median ~0 for each plate
            assert abs(plate_subset['Z_lptA'].median()) < 0.1
            assert abs(plate_subset['Z_ldtD'].median()) < 0.1
            
            # Viability percentages should be reasonable
            viability_rate = plate_subset['viability_ok_lptA'].mean()
            assert 0.5 < viability_rate < 1.0  # 50-100% viable wells

    def test_hit_identification(self, sample_plate_data: pd.DataFrame):
        """Test hit identification and ranking."""
        processed = process_plate_calculations(sample_plate_data, viability_threshold=0.3)
        
        # Get top hits by Z-score
        viable_wells = processed[processed['viability_ok_lptA'] & processed['viability_ok_ldtD']]
        viable_wells['max_abs_z'] = np.maximum(
            np.abs(viable_wells['Z_lptA']),
            np.abs(viable_wells['Z_ldtD'])
        )
        
        top_hits = viable_wells.nlargest(10, 'max_abs_z')
        
        # Verify hits are identified
        assert len(top_hits) > 0
        assert all(top_hits['max_abs_z'] >= 0)  # Sanity check
        
        # Verify hits are sorted correctly
        z_scores = top_hits['max_abs_z'].values
        assert np.all(z_scores[:-1] >= z_scores[1:])  # Descending order

    @pytest.mark.slow
    def test_performance_single_plate(self, sample_plate_data: pd.DataFrame):
        """Test single plate processing performance (PRD requirement: <200ms)."""
        # Warm-up run
        process_plate_calculations(sample_plate_data, viability_threshold=0.3)
        
        # Timed run
        start_time = time.time()
        result = process_plate_calculations(sample_plate_data, viability_threshold=0.3)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # PRD requirement: < 200ms for ~2000 rows (96 wells is smaller)
        assert processing_time < 0.2, f"Processing took {processing_time:.3f}s, expected < 0.2s"
        
        # Verify result integrity
        assert len(result) == len(sample_plate_data)

    @pytest.mark.slow
    def test_performance_multi_plate(self, multi_plate_data: List[pd.DataFrame]):
        """Test multi-plate processing performance (PRD requirement: <2s for 10 plates)."""
        # Create 10 plates for testing
        plates = []
        for i in range(10):
            plate_idx = i % len(multi_plate_data)
            plate = multi_plate_data[plate_idx].copy()
            plate['PlateID'] = f"Plate_{i + 1}"
            plates.append(plate)
        
        processor = PlateProcessor()
        
        # Warm-up
        processor.process_plate(plates[0], viability_threshold=0.3)
        
        # Timed run
        start_time = time.time()
        
        processed_plates = []
        for plate in plates:
            processed = processor.process_plate(plate, viability_threshold=0.3)
            processed_plates.append(processed)
        
        # Aggregate
        combined = pd.concat(processed_plates, ignore_index=True)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # PRD requirement: < 2s for 10 plates
        assert processing_time < 2.0, f"Processing took {processing_time:.3f}s, expected < 2.0s"
        
        # Verify result integrity
        assert len(combined) == sum(len(p) for p in plates)

    def test_memory_usage_multi_plate(self, multi_plate_data: List[pd.DataFrame]):
        """Test memory usage for multi-plate processing."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create 10 plates (~20,000 rows total)
        plates = []
        for i in range(10):
            plate_idx = i % len(multi_plate_data)
            plate = multi_plate_data[plate_idx].copy()
            
            # Expand to ~2000 rows per plate to match PRD
            expanded_data = []
            for _ in range(21):  # 96 * 21 ≈ 2000 rows
                expanded_plate = plate.copy()
                expanded_plate['Well'] = expanded_plate['Well'] + f"_rep{len(expanded_data)}"
                expanded_data.append(expanded_plate)
            
            large_plate = pd.concat(expanded_data, ignore_index=True)
            large_plate['PlateID'] = f"Plate_{i + 1}"
            plates.append(large_plate)
        
        # Process plates
        processor = PlateProcessor()
        processed_plates = []
        
        for plate in plates:
            processed = processor.process_plate(plate, viability_threshold=0.3)
            processed_plates.append(processed)
        
        combined = pd.concat(processed_plates, ignore_index=True)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        
        # PRD requirement: < 1GB for 10 plates
        assert memory_used < 1024, f"Memory usage {memory_used:.1f}MB, expected < 1024MB"
        
        # Verify processing worked
        assert len(combined) > 10000  # Should have substantial data
        assert 'Z_lptA' in combined.columns


class TestExportIntegration:
    """Test export functionality integration."""

    @pytest.fixture
    def processed_data(self) -> pd.DataFrame:
        """Create processed plate data for export testing."""
        np.random.seed(42)
        n_wells = 96
        
        data = {
            'Well': [f"A{i+1:02d}" for i in range(n_wells)],
            'PlateID': ['Test_Plate'] * n_wells,
            'BG_lptA': np.random.normal(1000, 200, n_wells),
            'BT_lptA': np.random.normal(500, 100, n_wells),
            'BG_ldtD': np.random.normal(1200, 250, n_wells),
            'BT_ldtD': np.random.normal(600, 120, n_wells),
            'OD_WT': np.random.normal(1.5, 0.3, n_wells),
            'OD_tolC': np.random.normal(1.2, 0.25, n_wells),
            'OD_SA': np.random.normal(1.0, 0.2, n_wells),
            'Ratio_lptA': np.random.normal(2.0, 0.5, n_wells),
            'Ratio_ldtD': np.random.normal(2.2, 0.6, n_wells),
            'Z_lptA': np.random.normal(0, 1, n_wells),
            'Z_ldtD': np.random.normal(0, 1, n_wells),
            'viability_ok_lptA': np.random.choice([True, False], n_wells, p=[0.85, 0.15]),
            'viability_ok_ldtD': np.random.choice([True, False], n_wells, p=[0.85, 0.15]),
        }
        
        return pd.DataFrame(data)

    def test_csv_export_integration(self, processed_data: pd.DataFrame, tmp_path: Path):
        """Test CSV export integration."""
        output_file = tmp_path / "test_export.csv"
        
        # Export data
        export_processed_data(processed_data, str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify content
        reimported = pd.read_csv(output_file)
        assert len(reimported) == len(processed_data)
        assert set(reimported.columns) == set(processed_data.columns)
        
        # Check numerical precision
        for col in ['Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD']:
            np.testing.assert_allclose(
                reimported[col], 
                processed_data[col], 
                rtol=1e-9
            )

    def test_bundle_export_integration(self, processed_data: pd.DataFrame, tmp_path: Path):
        """Test ZIP bundle export integration."""
        bundle_path = tmp_path / "test_bundle.zip"
        
        # Create export bundle
        config = {
            'viability_threshold': 0.3,
            'z_score_threshold': 2.0,
            'top_n_hits': 20
        }
        
        bundle_info = create_export_bundle(
            processed_data=processed_data,
            output_path=str(bundle_path),
            config=config
        )
        
        # Verify bundle was created
        assert bundle_path.exists()
        assert bundle_info['status'] == 'success'
        assert 'manifest' in bundle_info
        
        # Verify bundle contents
        import zipfile
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            file_list = zf.namelist()
            
            # Check for expected files
            assert any('processed_data.csv' in f for f in file_list)
            assert any('manifest.json' in f for f in file_list)
            assert len(file_list) > 2  # Should contain multiple files

    def test_pdf_report_integration(self, processed_data: pd.DataFrame, tmp_path: Path):
        """Test PDF report generation integration."""
        pdf_path = tmp_path / "test_report.pdf"
        
        # Generate report
        report_info = generate_qc_report(
            processed_data=processed_data,
            output_path=str(pdf_path),
            config={'viability_threshold': 0.3}
        )
        
        # Verify report was generated
        assert pdf_path.exists()
        assert report_info['status'] == 'success'
        assert pdf_path.stat().st_size > 1000  # Should be substantial size


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_input_data(self):
        """Test handling of invalid input data."""
        # Missing required columns
        invalid_data = pd.DataFrame({
            'Well': ['A01', 'A02'],
            'BG_lptA': [100, 200],  # Missing other required columns
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            process_plate_calculations(invalid_data)

    def test_empty_data(self):
        """Test handling of empty datasets."""
        empty_data = pd.DataFrame()
        
        # Should handle gracefully
        result = process_plate_calculations(empty_data, validate_columns=False)
        assert len(result) == 0

    def test_all_nan_data(self):
        """Test handling of all-NaN data."""
        nan_data = pd.DataFrame({
            'BG_lptA': [np.nan] * 10,
            'BT_lptA': [np.nan] * 10,
            'BG_ldtD': [np.nan] * 10,
            'BT_ldtD': [np.nan] * 10,
            'OD_WT': [np.nan] * 10,
            'OD_tolC': [np.nan] * 10,
            'OD_SA': [np.nan] * 10,
        })
        
        result = process_plate_calculations(nan_data, validate_columns=False)
        
        # Should complete without error
        assert len(result) == 10
        assert result['Ratio_lptA'].isna().all()
        assert result['Z_lptA'].isna().all()

    def test_constant_values(self):
        """Test handling of constant values (MAD = 0 case)."""
        constant_data = pd.DataFrame({
            'BG_lptA': [100] * 10,  # All same value
            'BT_lptA': [50] * 10,   # All same value
            'BG_ldtD': [150] * 10,
            'BT_ldtD': [75] * 10,
            'OD_WT': [1.0] * 10,
            'OD_tolC': [0.8] * 10,
            'OD_SA': [1.2] * 10,
        })
        
        result = process_plate_calculations(constant_data, validate_columns=False)
        
        # Ratios should be calculated correctly
        assert np.allclose(result['Ratio_lptA'], 2.0)
        
        # Z-scores should be NaN (MAD = 0 case)
        assert result['Z_lptA'].isna().all()


class TestConfigurationHandling:
    """Test configuration and parameter handling."""

    @pytest.fixture
    def base_data(self) -> pd.DataFrame:
        """Create base test data."""
        return pd.DataFrame({
            'BG_lptA': [100, 200, 300, 400],
            'BT_lptA': [50, 100, 150, 200],
            'BG_ldtD': [150, 300, 450, 600],
            'BT_ldtD': [75, 150, 225, 300],
            'OD_WT': [1.0, 2.0, 3.0, 4.0],
            'OD_tolC': [0.8, 1.6, 2.4, 3.2],
            'OD_SA': [1.2, 2.4, 3.6, 4.8],
        })

    def test_viability_threshold_variations(self, base_data: pd.DataFrame):
        """Test different viability threshold values."""
        thresholds = [0.1, 0.3, 0.5, 0.8]
        
        for threshold in thresholds:
            result = process_plate_calculations(base_data, viability_threshold=threshold)
            
            # Verify threshold was applied
            bt_median = base_data['BT_lptA'].median()
            expected_threshold = threshold * bt_median
            
            viable_wells = result[result['viability_ok_lptA']]
            failing_wells = result[result['viability_fail_lptA']]
            
            # All viable wells should meet threshold
            assert (viable_wells['BT_lptA'] >= expected_threshold).all()
            
            # All failing wells should be below threshold
            if len(failing_wells) > 0:
                assert (failing_wells['BT_lptA'] < expected_threshold).all()

    def test_extreme_threshold_values(self, base_data: pd.DataFrame):
        """Test edge cases for threshold values."""
        # Very low threshold - should make all wells viable
        result_low = process_plate_calculations(base_data, viability_threshold=0.01)
        assert result_low['viability_ok_lptA'].all()
        
        # Very high threshold - should make most wells non-viable
        result_high = process_plate_calculations(base_data, viability_threshold=0.99)
        assert not result_high['viability_ok_lptA'].all()