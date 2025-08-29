"""Unit tests for edge effect detection module.

Tests cover edge effect detection algorithms, warning level determination,
and the EdgeEffectDetector class functionality.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from analytics.edge_effects import (
    EdgeEffectDetector,
    EdgeEffectResult,
    WarningLevel,
    EdgeEffectError,
    detect_edge_effects_simple,
    is_edge_effect_significant,
    format_edge_effect_summary,
)


class TestEdgeEffectDetector:
    """Test cases for EdgeEffectDetector class."""
    
    def test_initialization(self):
        """Test detector initialization with custom parameters."""
        custom_thresholds = {
            'effect_size_d': 1.0,
            'spearman_rho': 0.6,
            'corner_mads': 1.5,
        }
        
        detector = EdgeEffectDetector(
            thresholds=custom_thresholds,
            min_group_wells=20,
            spatial_enabled=True
        )
        
        assert detector.thresholds['effect_size_d'] == 1.0
        assert detector.thresholds['spearman_rho'] == 0.6
        assert detector.thresholds['corner_mads'] == 1.5
        assert detector.min_group_wells == 20
        assert detector.spatial_enabled == True
        
        # Check that default values are preserved for unspecified thresholds
        assert detector.thresholds['warn_d'] == 0.8  # Default value
    
    def test_identify_edge_wells(self):
        """Test identification of edge and interior wells."""
        detector = EdgeEffectDetector()
        
        # Test standard 96-well plate (8x12)
        edge_pos, interior_pos = detector._identify_edge_wells((8, 12))
        
        # Check total count
        assert len(edge_pos) + len(interior_pos) == 96
        
        # Check specific positions
        assert (0, 0) in edge_pos  # Top-left corner
        assert (0, 11) in edge_pos  # Top-right corner
        assert (7, 0) in edge_pos  # Bottom-left corner
        assert (7, 11) in edge_pos  # Bottom-right corner
        assert (0, 5) in edge_pos  # Top edge
        assert (7, 5) in edge_pos  # Bottom edge
        assert (3, 0) in edge_pos  # Left edge
        assert (3, 11) in edge_pos  # Right edge
        
        # Interior wells
        assert (3, 5) in interior_pos  # Center well
        assert (1, 1) in interior_pos  # Interior corner
        assert (6, 10) in interior_pos  # Interior edge
        
        # Test smaller plate (6x8)
        edge_pos_small, interior_pos_small = detector._identify_edge_wells((6, 8))
        assert len(edge_pos_small) + len(interior_pos_small) == 48
        
        # For 6x8, interior should be 4x6 = 24 wells
        assert len(interior_pos_small) == 24
        assert len(edge_pos_small) == 24
    
    def test_extract_well_values(self):
        """Test extraction of values from well positions."""
        detector = EdgeEffectDetector()
        
        matrix = np.array([
            [1.0, 2.0, np.nan],
            [4.0, 5.0, 6.0],
            [7.0, np.nan, 9.0]
        ])
        
        # Extract specific positions
        positions = [(0, 0), (1, 1), (0, 2), (2, 1), (1, 2)]
        values = detector._extract_well_values(matrix, positions)
        
        # Should get [1.0, 5.0, 6.0] (excluding NaN values and positions)
        expected = np.array([1.0, 5.0, 6.0])
        np.testing.assert_array_equal(values, expected)
        
        # Test with out-of-bounds positions
        invalid_positions = [(10, 10), (-1, 0), (0, -1)]
        values_invalid = detector._extract_well_values(matrix, invalid_positions)
        assert len(values_invalid) == 0
    
    def test_calculate_effect_size(self):
        """Test robust effect size calculation."""
        detector = EdgeEffectDetector()
        
        # Test case where edge wells are higher than interior
        edge_values = np.array([5.0, 6.0, 7.0, 5.5, 6.5])  # Median = 6.0
        interior_values = np.array([2.0, 3.0, 4.0, 2.5, 3.5, 3.0, 2.8])  # Median = 3.0, MAD = 0.5
        
        d, edge_med, interior_med, interior_mad = detector._calculate_effect_size(edge_values, interior_values)
        
        assert edge_med == 6.0
        assert interior_med == 3.0
        assert interior_mad == 0.5
        assert d == (6.0 - 3.0) / 0.5  # = 6.0
        
        # Test with empty arrays
        d_empty, _, _, _ = detector._calculate_effect_size(np.array([]), interior_values)
        assert np.isnan(d_empty)
    
    def test_calculate_row_col_trends(self):
        """Test row and column trend detection."""
        detector = EdgeEffectDetector()
        
        # Create matrix with row trend (values increase with row index)
        matrix = np.zeros((6, 8))
        for i in range(6):
            for j in range(8):
                matrix[i, j] = i * 2 + np.random.randn() * 0.1  # Strong row trend with small noise
        
        row_corr, row_p, col_corr, col_p = detector._calculate_row_col_trends(matrix)
        
        # Should detect strong positive row correlation
        assert row_corr > 0.8, f"Expected strong row correlation, got {row_corr}"
        assert row_p < 0.05, f"Expected significant row p-value, got {row_p}"
        
        # Column correlation should be weak/random
        assert abs(col_corr) < 0.5, f"Expected weak column correlation, got {col_corr}"
        
        # Test with column trend
        matrix_col = np.zeros((6, 8))
        for i in range(6):
            for j in range(8):
                matrix_col[i, j] = j * 1.5 + np.random.randn() * 0.1
        
        row_corr2, row_p2, col_corr2, col_p2 = detector._calculate_row_col_trends(matrix_col)
        
        assert col_corr2 > 0.8, f"Expected strong column correlation, got {col_corr2}"
        assert col_p2 < 0.05, f"Expected significant column p-value, got {col_p2}"
    
    def test_calculate_corner_effects(self):
        """Test corner effect calculation."""
        detector = EdgeEffectDetector()
        
        # Create matrix where corners deviate from center
        matrix = np.full((8, 12), 5.0)  # Base value 5.0
        
        # Set corner values
        matrix[0, 0] = 10.0    # Top-left: +5 from base
        matrix[0, 11] = 2.0    # Top-right: -3 from base
        matrix[7, 0] = 8.0     # Bottom-left: +3 from base
        matrix[7, 11] = 1.0    # Bottom-right: -4 from base
        
        interior_median = 5.0
        interior_mad = 1.0  # Assumed MAD
        
        corner_deviations = detector._calculate_corner_effects(matrix, interior_median, interior_mad)
        
        expected = {
            'top_left': 5.0,     # |10 - 5| / 1 = 5
            'top_right': 3.0,    # |2 - 5| / 1 = 3
            'bottom_left': 3.0,  # |8 - 5| / 1 = 3
            'bottom_right': 4.0  # |1 - 5| / 1 = 4
        }
        
        for corner, expected_dev in expected.items():
            assert abs(corner_deviations[corner] - expected_dev) < 1e-6, \
                f"Corner {corner}: expected {expected_dev}, got {corner_deviations[corner]}"
    
    def test_determine_warning_level(self):
        """Test warning level determination."""
        detector = EdgeEffectDetector()
        
        # Test different effect sizes
        assert detector._determine_warning_level(0.3) == WarningLevel.INFO
        assert detector._determine_warning_level(0.6) == WarningLevel.INFO
        assert detector._determine_warning_level(0.9) == WarningLevel.WARN
        assert detector._determine_warning_level(1.6) == WarningLevel.CRITICAL
        
        # Test negative values (should use absolute)
        assert detector._determine_warning_level(-1.0) == WarningLevel.WARN
        assert detector._determine_warning_level(-2.0) == WarningLevel.CRITICAL
        
        # Test NaN value
        assert detector._determine_warning_level(np.nan) == WarningLevel.INFO
    
    def test_detect_edge_effects_basic(self):
        """Test basic edge effect detection."""
        detector = EdgeEffectDetector()
        
        # Create matrix with edge effect (edge wells systematically higher)
        np.random.seed(42)
        matrix = np.random.randn(8, 12) * 0.5 + 3.0  # Base: mean=3, std=0.5
        
        # Add edge effect: increase edge wells by 2
        edge_positions, _ = detector._identify_edge_wells((8, 12))
        for row, col in edge_positions:
            matrix[row, col] += 2.0
        
        result = detector.detect_edge_effects(matrix, metric="TestMetric", plate_id="TestPlate")
        
        # Check result structure
        assert isinstance(result, EdgeEffectResult)
        assert result.metric == "TestMetric"
        assert result.plate_id == "TestPlate"
        
        # Should detect significant edge effect
        assert result.effect_size_d > 1.0, f"Expected large effect size, got {result.effect_size_d}"
        assert result.warning_level in [WarningLevel.WARN, WarningLevel.CRITICAL]
        
        # Check that edge median > interior median
        assert result.edge_median > result.interior_median
        
        # Check well counts
        assert result.n_edge_wells > 0
        assert result.n_interior_wells > 0
        assert result.n_edge_wells + result.n_interior_wells <= 96  # Some wells might be excluded
    
    def test_detect_edge_effects_no_effect(self):
        """Test detection when no edge effects are present."""
        detector = EdgeEffectDetector()
        
        # Create homogeneous matrix
        np.random.seed(123)
        matrix = np.random.randn(8, 12) * 1.0 + 5.0  # Uniform random distribution
        
        result = detector.detect_edge_effects(matrix, metric="NoEffect", plate_id="CleanPlate")
        
        # Should detect minimal edge effect
        assert abs(result.effect_size_d) < 1.0, f"Expected small effect size, got {result.effect_size_d}"
        assert result.warning_level == WarningLevel.INFO
    
    def test_detect_edge_effects_with_missing_values(self):
        """Test edge effect detection with missing values."""
        detector = EdgeEffectDetector()
        
        # Create matrix with some missing values
        matrix = np.random.randn(8, 12) * 1.0 + 3.0
        
        # Set some random positions to NaN
        nan_positions = [(1, 2), (3, 5), (6, 8), (7, 11), (0, 0)]
        for row, col in nan_positions:
            matrix[row, col] = np.nan
        
        result = detector.detect_edge_effects(matrix, metric="WithMissing", plate_id="MissingData")
        
        # Should handle missing values gracefully
        assert not np.isnan(result.effect_size_d) or result.n_edge_wells < detector.min_group_wells
        assert result.n_edge_wells + result.n_interior_wells < 96  # Some wells missing
    
    def test_dataframe_processing(self):
        """Test DataFrame-based edge effect detection."""
        detector = EdgeEffectDetector()
        
        # Create sample plate data
        np.random.seed(456)
        rows = []
        for i in range(8):
            for j in range(1, 13):
                row_letter = chr(ord('A') + i)
                value = np.random.randn() * 1.0 + 2.0
                
                # Add edge effect to edge wells
                is_edge = (i == 0 or i == 7 or j == 1 or j == 12)
                if is_edge:
                    value += 1.5  # Edge effect
                
                rows.append({
                    'Row': row_letter,
                    'Col': j,
                    'Z_lptA': value,
                    'PlateID': 'TestPlate1'
                })
        
        df = pd.DataFrame(rows)
        
        results = detector.detect_edge_effects_dataframe(df, metric='Z_lptA')
        
        assert len(results) == 1
        result = results[0]
        assert result.plate_id == 'TestPlate1'
        assert result.effect_size_d > 0.5  # Should detect the added edge effect
    
    def test_multiple_plates_dataframe(self):
        """Test DataFrame processing with multiple plates."""
        detector = EdgeEffectDetector()
        
        # Create data for multiple plates
        np.random.seed(789)
        rows = []
        
        for plate_id in ['Plate1', 'Plate2', 'Plate3']:
            for i in range(8):
                for j in range(1, 13):
                    row_letter = chr(ord('A') + i)
                    
                    # Different edge effects for different plates
                    base_value = np.random.randn() * 0.8 + 1.0
                    is_edge = (i == 0 or i == 7 or j == 1 or j == 12)
                    
                    if plate_id == 'Plate1' and is_edge:
                        base_value += 2.0  # Strong edge effect
                    elif plate_id == 'Plate2' and is_edge:
                        base_value += 0.5  # Weak edge effect
                    # Plate3 has no edge effect
                    
                    rows.append({
                        'Row': row_letter,
                        'Col': j,
                        'Z_lptA': base_value,
                        'PlateID': plate_id
                    })
        
        df = pd.DataFrame(rows)
        results = detector.detect_edge_effects_dataframe(df, metric='Z_lptA')
        
        assert len(results) == 3
        
        # Check that different plates show different effect sizes
        plate1_result = [r for r in results if r.plate_id == 'Plate1'][0]
        plate2_result = [r for r in results if r.plate_id == 'Plate2'][0]
        plate3_result = [r for r in results if r.plate_id == 'Plate3'][0]
        
        assert plate1_result.effect_size_d > plate2_result.effect_size_d > plate3_result.effect_size_d
        assert plate1_result.warning_level != WarningLevel.INFO  # Should have warning
    
    def test_generate_report(self):
        """Test report generation."""
        detector = EdgeEffectDetector()
        
        # Create mock results
        results = [
            EdgeEffectResult(
                metric="Z_lptA",
                plate_id="Plate1",
                effect_size_d=1.8,  # Critical
                edge_median=5.0,
                interior_median=3.0,
                interior_mad=0.5,
                row_correlation=0.7,
                row_p_value=0.01,
                col_correlation=0.2,
                col_p_value=0.5,
                corner_deviations={'top_left': 2.0, 'top_right': 1.0, 'bottom_left': 0.5, 'bottom_right': 0.8},
                warning_level=WarningLevel.CRITICAL,
                n_edge_wells=32,
                n_interior_wells=56
            ),
            EdgeEffectResult(
                metric="Z_lptA",
                plate_id="Plate2",
                effect_size_d=0.3,  # Info
                edge_median=3.2,
                interior_median=3.0,
                interior_mad=0.6,
                row_correlation=0.1,
                row_p_value=0.8,
                col_correlation=-0.05,
                col_p_value=0.9,
                corner_deviations={'top_left': 0.2, 'top_right': 0.3, 'bottom_left': 0.1, 'bottom_right': 0.4},
                warning_level=WarningLevel.INFO,
                n_edge_wells=30,
                n_interior_wells=58
            )
        ]
        
        report = detector.generate_report(results)
        
        # Check report structure
        assert 'summary' in report
        assert 'trends' in report
        assert 'recommendations' in report
        assert 'details' in report
        
        # Check summary statistics
        summary = report['summary']
        assert summary['total_plates'] == 2
        assert summary['problematic_plates']['critical'] == ['Plate1']
        assert summary['problematic_plates']['warning'] == []
        
        # Check recommendations
        recommendations = report['recommendations']
        assert len(recommendations) > 0
        assert any('CRITICAL' in rec for rec in recommendations)


class TestSpatialAutocorrelation:
    """Test spatial autocorrelation functionality."""
    
    def test_spatial_autocorr_disabled(self):
        """Test that spatial autocorrelation is skipped when disabled."""
        detector = EdgeEffectDetector(spatial_enabled=False)
        
        matrix = np.random.randn(8, 12)
        result = detector.detect_edge_effects(matrix)
        
        assert result.spatial_autocorr is None
        assert result.spatial_p_value is None
    
    def test_spatial_autocorr_enabled(self):
        """Test spatial autocorrelation calculation when enabled."""
        detector = EdgeEffectDetector(spatial_enabled=True)
        
        # Create matrix with spatial structure (smooth gradients)
        matrix = np.zeros((8, 12))
        for i in range(8):
            for j in range(12):
                matrix[i, j] = i + j + np.random.randn() * 0.1  # Smooth spatial trend
        
        result = detector.detect_edge_effects(matrix)
        
        # May return None if calculation fails, but should not crash
        assert result.spatial_autocorr is None or isinstance(result.spatial_autocorr, float)
        assert result.spatial_p_value is None or isinstance(result.spatial_p_value, float)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_detect_edge_effects_simple(self):
        """Test simple edge effect detection function."""
        # Create test DataFrame
        np.random.seed(321)
        rows = []
        for i in range(8):
            for j in range(1, 13):
                row_letter = chr(ord('A') + i)
                value = np.random.randn() * 0.8 + 2.0
                
                # Add edge effect
                is_edge = (i == 0 or i == 7 or j == 1 or j == 12)
                if is_edge:
                    value += 1.0
                
                rows.append({
                    'Row': row_letter,
                    'Col': j,
                    'Z_lptA': value
                })
        
        df = pd.DataFrame(rows)
        
        results = detect_edge_effects_simple(df, metric='Z_lptA')
        
        assert len(results) == 1
        assert results[0].effect_size_d > 0.5
    
    def test_is_edge_effect_significant(self):
        """Test significance testing function."""
        # Mock result with significant effect
        significant_result = EdgeEffectResult(
            metric="Z_lptA", plate_id="Test", effect_size_d=1.2,
            edge_median=5.0, interior_median=3.0, interior_mad=1.0,
            row_correlation=0.1, row_p_value=0.5,
            col_correlation=0.1, col_p_value=0.5,
            corner_deviations={}, warning_level=WarningLevel.WARN,
            n_edge_wells=30, n_interior_wells=60
        )
        
        # Mock result with non-significant effect
        nonsignificant_result = EdgeEffectResult(
            metric="Z_lptA", plate_id="Test", effect_size_d=0.3,
            edge_median=3.1, interior_median=3.0, interior_mad=1.0,
            row_correlation=0.1, row_p_value=0.5,
            col_correlation=0.1, col_p_value=0.5,
            corner_deviations={}, warning_level=WarningLevel.INFO,
            n_edge_wells=30, n_interior_wells=60
        )
        
        assert is_edge_effect_significant(significant_result, threshold=0.8) == True
        assert is_edge_effect_significant(nonsignificant_result, threshold=0.8) == False
        
        # Test with NaN effect size
        nan_result = EdgeEffectResult(
            metric="Z_lptA", plate_id="Test", effect_size_d=np.nan,
            edge_median=np.nan, interior_median=np.nan, interior_mad=np.nan,
            row_correlation=np.nan, row_p_value=np.nan,
            col_correlation=np.nan, col_p_value=np.nan,
            corner_deviations={}, warning_level=WarningLevel.INFO,
            n_edge_wells=0, n_interior_wells=0
        )
        
        assert is_edge_effect_significant(nan_result) == False
    
    def test_format_edge_effect_summary(self):
        """Test summary formatting function."""
        result = EdgeEffectResult(
            metric="Z_lptA",
            plate_id="TestPlate123",
            effect_size_d=1.45,
            edge_median=5.2,
            interior_median=3.1,
            interior_mad=0.8,
            row_correlation=0.65,
            row_p_value=0.02,
            col_correlation=0.15,
            col_p_value=0.6,
            corner_deviations={'top_left': 2.5, 'top_right': 0.8, 'bottom_left': 1.1, 'bottom_right': 0.6},
            warning_level=WarningLevel.CRITICAL,
            n_edge_wells=28,
            n_interior_wells=64
        )
        
        summary = format_edge_effect_summary(result)
        
        # Check that key information is included
        assert "TestPlate123" in summary
        assert "Z_lptA" in summary
        assert "1.45" in summary or "1.450" in summary  # Effect size
        assert "CRITICAL" in summary
        assert "0.65" in summary or "0.650" in summary  # Row correlation
        assert "2.5" in summary  # Max corner deviation


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_matrix_dimensions(self):
        """Test error handling for invalid matrix dimensions."""
        detector = EdgeEffectDetector()
        
        # Test with 1D array
        with pytest.raises(EdgeEffectError, match="Expected 2D matrix"):
            detector.detect_edge_effects(np.array([1, 2, 3]))
        
        # Test with 3D array
        with pytest.raises(EdgeEffectError, match="Expected 2D matrix"):
            detector.detect_edge_effects(np.random.randn(2, 3, 4))
    
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        detector = EdgeEffectDetector(min_group_wells=50)  # High threshold
        
        # Small matrix won't have enough wells in each group
        small_matrix = np.random.randn(4, 6)  # 24 total wells
        
        # Should still complete but may have warnings
        result = detector.detect_edge_effects(small_matrix, plate_id="SmallPlate")
        assert result.n_edge_wells < 50
        assert result.n_interior_wells < 50
    
    def test_all_nan_matrix(self):
        """Test handling of all-NaN matrix."""
        detector = EdgeEffectDetector()
        
        nan_matrix = np.full((8, 12), np.nan)
        
        result = detector.detect_edge_effects(nan_matrix, plate_id="AllNaN")
        
        # Should handle gracefully
        assert np.isnan(result.effect_size_d)
        assert result.n_edge_wells == 0
        assert result.n_interior_wells == 0
    
    def test_missing_dataframe_columns(self):
        """Test error handling for missing DataFrame columns."""
        detector = EdgeEffectDetector()
        
        # DataFrame missing required columns
        incomplete_df = pd.DataFrame({
            'Row': ['A', 'B'],
            'Col': [1, 2]
            # Missing Z_lptA column
        })
        
        with pytest.raises(EdgeEffectError, match="Missing required columns"):
            detector.detect_edge_effects_dataframe(incomplete_df, metric='Z_lptA')


class TestNumericalStability:
    """Test numerical stability and edge cases."""
    
    def test_extreme_values(self):
        """Test handling of extreme values."""
        detector = EdgeEffectDetector()
        
        # Matrix with extreme values
        matrix = np.array([
            [1e10, 1e-10, 1.0, 1.0],
            [1e-10, 1e10, 1.0, 1.0],
            [1.0, 1.0, 1e10, 1e-10],
            [1.0, 1.0, 1e-10, 1e10]
        ])
        
        # Should handle extreme values without crashing
        result = detector.detect_edge_effects(matrix, plate_id="ExtremeValues")
        
        # Result should be computed even if not meaningful
        assert isinstance(result, EdgeEffectResult)
        assert not np.isnan(result.effect_size_d) or result.n_edge_wells == 0
    
    def test_constant_values(self):
        """Test handling of constant values."""
        detector = EdgeEffectDetector()
        
        # All values are the same
        constant_matrix = np.full((8, 12), 5.0)
        
        result = detector.detect_edge_effects(constant_matrix, plate_id="Constant")
        
        # Effect size should be 0 (no difference between edge and interior)
        assert abs(result.effect_size_d) < 1e-6 or np.isnan(result.effect_size_d)
        assert result.warning_level == WarningLevel.INFO
    
    def test_reproducibility(self):
        """Test numerical reproducibility."""
        detector1 = EdgeEffectDetector()
        detector2 = EdgeEffectDetector()
        
        # Use fixed seed for reproducible random matrix
        np.random.seed(555)
        matrix1 = np.random.randn(8, 12) * 2 + 3
        
        np.random.seed(555)
        matrix2 = np.random.randn(8, 12) * 2 + 3
        
        result1 = detector1.detect_edge_effects(matrix1, plate_id="Repro1")
        result2 = detector2.detect_edge_effects(matrix2, plate_id="Repro2")
        
        # Results should be identical (within numerical precision)
        assert abs(result1.effect_size_d - result2.effect_size_d) < 1e-9
        assert abs(result1.edge_median - result2.edge_median) < 1e-9
        assert abs(result1.interior_median - result2.interior_median) < 1e-9
        assert abs(result1.interior_mad - result2.interior_mad) < 1e-9


class TestIntegrationWithPlateLayouts:
    """Test integration with different plate layouts."""
    
    def test_384_well_plate(self):
        """Test with 384-well plate layout."""
        detector = EdgeEffectDetector()
        
        # Create 384-well matrix (16x24)
        np.random.seed(888)
        matrix_384 = np.random.randn(16, 24) * 1.5 + 4.0
        
        # Add edge effect
        edge_positions, _ = detector._identify_edge_wells((16, 24))
        for row, col in edge_positions:
            matrix_384[row, col] += 1.0
        
        result = detector.detect_edge_effects(matrix_384, plate_layout=(16, 24), plate_id="384Well")
        
        # Should detect edge effect
        assert result.effect_size_d > 0.3
        assert result.n_edge_wells > 0
        assert result.n_interior_wells > 0
        
        # Check that interior wells are correct for 16x24 layout
        # Interior should be 14x22 = 308 wells
        expected_interior = 14 * 22
        edge_positions_384, interior_positions_384 = detector._identify_edge_wells((16, 24))
        assert len(interior_positions_384) == expected_interior
    
    def test_custom_plate_layout(self):
        """Test with custom plate layout."""
        detector = EdgeEffectDetector()
        
        # Test with 6x10 custom layout
        matrix_custom = np.random.randn(6, 10) * 1.0 + 2.0
        
        result = detector.detect_edge_effects(matrix_custom, plate_layout=(6, 10), plate_id="Custom")
        
        # Should complete without errors
        assert isinstance(result, EdgeEffectResult)
        assert result.n_edge_wells + result.n_interior_wells <= 60


if __name__ == "__main__":
    pytest.main([__file__])