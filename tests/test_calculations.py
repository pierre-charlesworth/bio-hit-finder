"""Tests for core.calculations module.

Tests the core calculation pipeline functions implementing exact PRD formulas,
including reporter ratios, OD normalization, robust Z-scores, and viability gating.
"""

import numpy as np
import pandas as pd
import pytest

from core.calculations import (
    apply_viability_gate,
    calculate_od_normalization,
    calculate_plate_summary,
    calculate_reporter_ratios,
    calculate_robust_zscore_columns,
    process_plate_calculations,
    validate_plate_columns,
)


class TestCalculateReporterRatios:
    """Test reporter ratio calculations (PRD Section 4.1)."""
    
    def test_basic_calculation(self):
        """Test basic reporter ratio calculation."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200, 300],
            'BT_lptA': [50, 100, 150],
            'BG_ldtD': [150, 300, 450],
            'BT_ldtD': [75, 150, 225],
        })
        
        result = calculate_reporter_ratios(df)
        
        # Check that new columns exist
        assert 'Ratio_lptA' in result.columns
        assert 'Ratio_ldtD' in result.columns
        
        # Check calculations: Ratio_lptA = BG_lptA / BT_lptA
        expected_lptA = [2.0, 2.0, 2.0]
        expected_ldtD = [2.0, 2.0, 2.0]
        
        pd.testing.assert_series_equal(
            result['Ratio_lptA'], 
            pd.Series(expected_lptA, name='Ratio_lptA'),
            check_exact=False,
            rtol=1e-10
        )
        pd.testing.assert_series_equal(
            result['Ratio_ldtD'],
            pd.Series(expected_ldtD, name='Ratio_ldtD'),
            check_exact=False,
            rtol=1e-10
        )
    
    def test_with_nans(self):
        """Test with NaN values in input."""
        df = pd.DataFrame({
            'BG_lptA': [100, np.nan, 300],
            'BT_lptA': [50, 100, np.nan],
            'BG_ldtD': [150, 300, 450],
            'BT_ldtD': [75, np.nan, 225],
        })
        
        result = calculate_reporter_ratios(df)
        
        # Check that NaN inputs produce NaN outputs
        assert result['Ratio_lptA'].iloc[1] is pd.NA or np.isnan(result['Ratio_lptA'].iloc[1])  # np.nan / 100
        assert result['Ratio_lptA'].iloc[2] is pd.NA or np.isnan(result['Ratio_lptA'].iloc[2])  # 300 / np.nan
        assert result['Ratio_ldtD'].iloc[1] is pd.NA or np.isnan(result['Ratio_ldtD'].iloc[1])  # 300 / np.nan
        
        # Check valid calculation
        assert abs(result['Ratio_lptA'].iloc[0] - 2.0) < 1e-10
        assert abs(result['Ratio_ldtD'].iloc[2] - 2.0) < 1e-10
    
    def test_division_by_zero(self):
        """Test division by zero handling."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200],
            'BT_lptA': [0, 100],  # Zero in denominator
            'BG_ldtD': [150, 300],
            'BT_ldtD': [75, 0],   # Zero in denominator
        })
        
        result = calculate_reporter_ratios(df)
        
        # Division by zero should produce inf
        assert np.isinf(result['Ratio_lptA'].iloc[0])
        assert np.isinf(result['Ratio_ldtD'].iloc[1])
        
        # Valid calculations should work
        assert abs(result['Ratio_lptA'].iloc[1] - 2.0) < 1e-10
        assert abs(result['Ratio_ldtD'].iloc[0] - 2.0) < 1e-10
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200],
            'BT_lptA': [50, 100],
            # Missing BG_ldtD and BT_ldtD
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            calculate_reporter_ratios(df)
    
    def test_preserves_other_columns(self):
        """Test that other columns are preserved."""
        df = pd.DataFrame({
            'Well': ['A01', 'A02'],
            'BG_lptA': [100, 200],
            'BT_lptA': [50, 100],
            'BG_ldtD': [150, 300],
            'BT_ldtD': [75, 150],
            'Treatment': ['Control', 'Test'],
        })
        
        result = calculate_reporter_ratios(df)
        
        # Original columns should be preserved
        assert 'Well' in result.columns
        assert 'Treatment' in result.columns
        pd.testing.assert_series_equal(result['Well'], df['Well'])
        pd.testing.assert_series_equal(result['Treatment'], df['Treatment'])


class TestCalculateODNormalization:
    """Test OD normalization calculations (PRD Section 4.2)."""
    
    def test_basic_normalization(self):
        """Test basic OD normalization."""
        df = pd.DataFrame({
            'OD_WT': [0.5, 1.0, 1.5, 2.0],    # median = 1.25
            'OD_tolC': [0.3, 0.6, 0.9, 1.2],  # median = 0.75  
            'OD_SA': [0.4, 0.8, 1.2, 1.6],    # median = 1.0
        })
        
        result = calculate_od_normalization(df)
        
        # Check new columns exist
        assert 'OD_WT_norm' in result.columns
        assert 'OD_tolC_norm' in result.columns  
        assert 'OD_SA_norm' in result.columns
        
        # Check calculations: OD_norm = OD / median(OD)
        expected_wt = [0.4, 0.8, 1.2, 1.6]    # / 1.25
        expected_tolc = [0.4, 0.8, 1.2, 1.6]  # / 0.75
        expected_sa = [0.4, 0.8, 1.2, 1.6]    # / 1.0
        
        np.testing.assert_allclose(result['OD_WT_norm'], expected_wt, rtol=1e-10)
        np.testing.assert_allclose(result['OD_tolC_norm'], expected_tolc, rtol=1e-10)
        np.testing.assert_allclose(result['OD_SA_norm'], expected_sa, rtol=1e-10)
    
    def test_with_nans(self):
        """Test OD normalization with NaN values."""
        df = pd.DataFrame({
            'OD_WT': [0.5, np.nan, 1.5, 2.0],
            'OD_tolC': [0.3, 0.6, 0.9, 1.2], 
            'OD_SA': [np.nan, 0.8, 1.2, 1.6],
        })
        
        result = calculate_od_normalization(df)
        
        # NaN values should propagate
        assert np.isnan(result['OD_WT_norm'].iloc[1])
        assert np.isnan(result['OD_SA_norm'].iloc[0])
        
        # Valid values should be normalized correctly
        assert not np.isnan(result['OD_WT_norm'].iloc[0])
        assert not np.isnan(result['OD_tolC_norm'].iloc[1])
    
    def test_zero_median_handling(self):
        """Test handling when median is zero."""
        df = pd.DataFrame({
            'OD_WT': [0, 0, 0, 1],  # median = 0
            'OD_tolC': [0.3, 0.6, 0.9, 1.2],
            'OD_SA': [0.4, 0.8, 1.2, 1.6],
        })
        
        result = calculate_od_normalization(df)
        
        # Zero median should result in all NaN for that column
        assert result['OD_WT_norm'].isna().all()
        
        # Other columns should work normally
        assert not result['OD_tolC_norm'].isna().all()
        assert not result['OD_SA_norm'].isna().all()
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({
            'OD_WT': [0.5, 1.0, 1.5, 2.0],
            # Missing OD_tolC and OD_SA
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            calculate_od_normalization(df)


class TestCalculateRobustZScoreColumns:
    """Test robust Z-score calculation for columns (PRD Section 4.3)."""
    
    def test_basic_zscore_calculation(self):
        """Test basic Z-score calculation."""
        df = pd.DataFrame({
            'Ratio_lptA': [1, 2, 3, 4, 5],  # median = 3, MAD = 1
            'Ratio_ldtD': [2, 4, 6, 8, 10], # median = 6, MAD = 2
        })
        
        result = calculate_robust_zscore_columns(df)
        
        # Check new columns exist
        assert 'Z_lptA' in result.columns
        assert 'Z_ldtD' in result.columns
        
        # Check that Z-scores have median ~0 (robust property)
        assert abs(np.median(result['Z_lptA'])) < 1e-10
        assert abs(np.median(result['Z_ldtD'])) < 1e-10
    
    def test_custom_columns(self):
        """Test with custom column specification."""
        df = pd.DataFrame({
            'Metric_A': [1, 2, 3, 4, 5],
            'Metric_B': [2, 4, 6, 8, 10],
            'Other': [1, 1, 1, 1, 1],
        })
        
        result = calculate_robust_zscore_columns(df, columns=['Metric_A', 'Metric_B'])
        
        # Check that Z-scores were calculated for specified columns
        assert 'Z_Metric_A' in result.columns
        assert 'Z_Metric_B' in result.columns
        assert 'Z_Other' not in result.columns  # Should not be calculated
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({
            'Ratio_lptA': [1, 2, 3, 4, 5],
            # Missing Ratio_ldtD
        })
        
        with pytest.raises(ValueError, match="Missing columns"):
            calculate_robust_zscore_columns(df)  # Default expects both ratios


class TestApplyViabilityGate:
    """Test viability gating (PRD Section 4.4)."""
    
    def test_basic_viability_gating(self):
        """Test basic viability gate application."""
        df = pd.DataFrame({
            'BT_lptA': [100, 80, 60, 40, 20],  # median = 60, threshold = 18 (f=0.3)
            'BT_ldtD': [200, 160, 120, 80, 40], # median = 120, threshold = 36
        })
        
        result = apply_viability_gate(df, f=0.3)
        
        # Check new columns exist
        assert 'viability_ok_lptA' in result.columns
        assert 'viability_fail_lptA' in result.columns
        assert 'viability_ok_ldtD' in result.columns
        assert 'viability_fail_ldtD' in result.columns
        
        # Check viability calculations
        # BT_lptA: threshold = 0.3 * 60 = 18
        expected_ok_lptA = [True, True, True, True, True]  # All >= 18
        expected_fail_lptA = [False, False, False, False, False]
        
        # BT_ldtD: threshold = 0.3 * 120 = 36  
        expected_ok_ldtD = [True, True, True, True, True]  # All >= 36
        expected_fail_ldtD = [False, False, False, False, False]
        
        pd.testing.assert_series_equal(
            result['viability_ok_lptA'], 
            pd.Series(expected_ok_lptA, name='viability_ok_lptA')
        )
        pd.testing.assert_series_equal(
            result['viability_fail_lptA'],
            pd.Series(expected_fail_lptA, name='viability_fail_lptA')
        )
    
    def test_with_failing_wells(self):
        """Test with wells that fail viability."""
        df = pd.DataFrame({
            'BT_lptA': [100, 50, 20, 10, 5],   # median = 20, threshold = 6
            'BT_ldtD': [200, 100, 40, 20, 10], # median = 40, threshold = 12
        })
        
        result = apply_viability_gate(df, f=0.3)
        
        # BT_lptA: threshold = 0.3 * 20 = 6
        expected_ok_lptA = [True, True, True, True, False]  # Only last fails
        
        # BT_ldtD: threshold = 0.3 * 40 = 12
        expected_ok_ldtD = [True, True, True, True, False]  # Only last fails
        
        pd.testing.assert_series_equal(
            result['viability_ok_lptA'],
            pd.Series(expected_ok_lptA, name='viability_ok_lptA')
        )
        pd.testing.assert_series_equal(
            result['viability_ok_ldtD'], 
            pd.Series(expected_ok_ldtD, name='viability_ok_ldtD')
        )
    
    def test_with_nans(self):
        """Test viability gating with NaN values."""
        df = pd.DataFrame({
            'BT_lptA': [100, np.nan, 60, 40],
            'BT_ldtD': [200, 160, np.nan, 80],
        })
        
        result = apply_viability_gate(df, f=0.3)
        
        # NaN values should fail viability
        assert result['viability_ok_lptA'].iloc[1] == False
        assert result['viability_fail_lptA'].iloc[1] == True
        assert result['viability_ok_ldtD'].iloc[2] == False
        assert result['viability_fail_ldtD'].iloc[2] == True
    
    def test_invalid_threshold(self):
        """Test error handling for invalid threshold."""
        df = pd.DataFrame({
            'BT_lptA': [100, 80, 60],
            'BT_ldtD': [200, 160, 120],
        })
        
        with pytest.raises(ValueError, match="Viability threshold f must be between 0 and 1"):
            apply_viability_gate(df, f=1.5)
        
        with pytest.raises(ValueError, match="Viability threshold f must be between 0 and 1"):
            apply_viability_gate(df, f=-0.1)
    
    def test_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame({
            'BT_lptA': [100, 80, 60],
            # Missing BT_ldtD
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            apply_viability_gate(df)


class TestProcessPlateCalculations:
    """Test the complete calculation pipeline."""
    
    def test_complete_pipeline(self):
        """Test the complete calculation pipeline."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200, 300],
            'BT_lptA': [50, 100, 150],
            'BG_ldtD': [150, 300, 450],
            'BT_ldtD': [75, 150, 225],
            'OD_WT': [1.0, 2.0, 3.0],
            'OD_tolC': [0.8, 1.6, 2.4],
            'OD_SA': [1.2, 2.4, 3.6],
        })
        
        result = process_plate_calculations(df, viability_threshold=0.3)
        
        # Check that all expected columns exist
        expected_columns = [
            # Original columns
            'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA',
            # Calculated columns
            'Ratio_lptA', 'Ratio_ldtD',
            'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm',
            'Z_lptA', 'Z_ldtD',
            'viability_ok_lptA', 'viability_fail_lptA',
            'viability_ok_ldtD', 'viability_fail_ldtD',
        ]
        
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Check that all rows are preserved
        assert len(result) == len(df)
        
        # Spot check some calculations
        assert abs(result['Ratio_lptA'].iloc[0] - 2.0) < 1e-10  # 100/50
        assert abs(result['OD_WT_norm'].iloc[1] - 1.0) < 1e-10  # 2.0/median([1,2,3])


class TestValidatePlateColumns:
    """Test plate column validation."""
    
    def test_valid_columns(self):
        """Test with all required columns present."""
        df = pd.DataFrame({
            'BG_lptA': [1], 'BT_lptA': [1], 'BG_ldtD': [1], 'BT_ldtD': [1],
            'OD_WT': [1], 'OD_tolC': [1], 'OD_SA': [1],
        })
        
        # Should not raise an exception
        result = validate_plate_columns(df)
        assert result == True
    
    def test_missing_columns(self):
        """Test with missing required columns."""
        df = pd.DataFrame({
            'BG_lptA': [1], 'BT_lptA': [1],
            # Missing other required columns
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_plate_columns(df)
    
    def test_custom_required_columns(self):
        """Test with custom required columns."""
        df = pd.DataFrame({
            'Col_A': [1], 'Col_B': [1],
        })
        
        # Should pass with custom requirements
        result = validate_plate_columns(df, required_columns=['Col_A', 'Col_B'])
        assert result == True
        
        # Should fail if custom requirements not met
        with pytest.raises(ValueError):
            validate_plate_columns(df, required_columns=['Col_A', 'Col_C'])


class TestCalculatePlateSummary:
    """Test plate summary statistics calculation."""
    
    def test_basic_summary(self):
        """Test basic summary calculation."""
        df = pd.DataFrame({
            'Ratio_lptA': [1, 2, np.nan, 4],
            'Ratio_ldtD': [1, 2, 3, 4],
            'viability_ok_lptA': [True, True, False, True],
            'viability_ok_ldtD': [True, False, True, True],
            'Z_lptA': [-1, 0, np.nan, 1],
            'Z_ldtD': [-2, -1, 0, 1],
        })
        
        summary = calculate_plate_summary(df)
        
        assert summary['total_wells'] == 4
        assert summary['valid_ratios_lptA'] == 3  # 3 non-NaN values
        assert summary['valid_ratios_ldtD'] == 4  # 4 non-NaN values 
        assert summary['viable_wells_lptA'] == 3  # 3 True values
        assert summary['viable_wells_ldtD'] == 3  # 3 True values
        
        # Check medians
        assert abs(summary['median_z_lptA'] - 0.0) < 1e-10  # median of [-1, 0, 1]
        assert abs(summary['median_z_ldtD'] - (-0.5)) < 1e-10  # median of [-2, -1, 0, 1]
    
    def test_empty_summary(self):
        """Test summary with empty DataFrame."""
        df = pd.DataFrame()
        summary = calculate_plate_summary(df)
        
        assert summary['total_wells'] == 0
        assert summary['valid_ratios_lptA'] == 0
        assert summary['viable_wells_lptA'] == 0