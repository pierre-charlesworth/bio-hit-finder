"""Tests for core.statistics module.

Tests the robust statistical functions used throughout the bio-hit-finder platform,
with emphasis on edge cases and numerical accuracy.
"""

import numpy as np
import pytest

from core.statistics import (
    calculate_robust_zscore,
    count_valid_values,
    is_constant_array,
    mad,
    nan_safe_median,
    robust_zscore,
    summary_statistics,
)


class TestNanSafeMedian:
    """Test nan_safe_median function."""
    
    def test_normal_values(self):
        """Test with normal numeric values."""
        values = [1, 2, 3, 4, 5]
        result = nan_safe_median(values)
        assert result == 3.0
    
    def test_with_nans(self):
        """Test with NaN values mixed in."""
        values = [1, 2, np.nan, 4, 5]
        result = nan_safe_median(values)
        assert result == 3.0  # median of [1, 2, 4, 5]
    
    def test_all_nans(self):
        """Test with all NaN values."""
        values = [np.nan, np.nan, np.nan]
        result = nan_safe_median(values)
        assert np.isnan(result)
    
    def test_empty_array(self):
        """Test with empty array."""
        result = nan_safe_median([])
        assert np.isnan(result)
    
    def test_single_value(self):
        """Test with single value."""
        result = nan_safe_median([42])
        assert result == 42.0
    
    def test_even_length(self):
        """Test with even number of values."""
        values = [1, 2, 3, 4]
        result = nan_safe_median(values)
        assert result == 2.5


class TestMAD:
    """Test Median Absolute Deviation function."""
    
    def test_normal_values(self):
        """Test MAD with normal values."""
        values = [1, 2, 3, 4, 5]  # median = 3
        result = mad(values)
        # MAD = median([2, 1, 0, 1, 2]) = 1
        assert result == 1.0
    
    def test_constant_values(self):
        """Test MAD with constant values (should return 0)."""
        values = [5, 5, 5, 5, 5]
        result = mad(values)
        assert result == 0.0
    
    def test_with_nans(self):
        """Test MAD with NaN values."""
        values = [1, 2, np.nan, 4, 5]
        result = mad(values)
        # median = 2.5, MAD of [1, 2, 4, 5] relative to 2.5
        expected = np.median([1.5, 0.5, 1.5, 2.5])  # = 1.5
        assert abs(result - expected) < 1e-10
    
    def test_all_nans(self):
        """Test MAD with all NaN values."""
        values = [np.nan, np.nan, np.nan]
        result = mad(values)
        assert np.isnan(result)
    
    def test_empty_array(self):
        """Test MAD with empty array.""" 
        result = mad([])
        assert np.isnan(result)


class TestRobustZScore:
    """Test robust Z-score calculation."""
    
    def test_normal_distribution_like(self):
        """Test with normal distribution-like values."""
        # Use symmetric distribution around zero
        values = [-2, -1, 0, 1, 2]
        result = robust_zscore(values)
        
        # Check that median Z-score is approximately 0
        median_z = np.median(result)
        assert abs(median_z) < 1e-10
        
        # Check scaling factor (MAD * 1.4826 should approximate std for normal data)
        assert len(result) == len(values)
        assert np.all(~np.isnan(result))  # No NaN values
    
    def test_constant_values(self):
        """Test with constant values (MAD = 0 case)."""
        values = [5, 5, 5, 5, 5]
        result = robust_zscore(values)
        
        # Should return all NaN when MAD = 0
        assert np.all(np.isnan(result))
        assert len(result) == len(values)
    
    def test_with_nans(self):
        """Test with NaN values in input."""
        values = [1, 2, np.nan, 4, 5]
        result = robust_zscore(values)
        
        # NaN positions should remain NaN
        assert np.isnan(result[2])
        
        # Other positions should have valid Z-scores
        assert not np.isnan(result[0])
        assert not np.isnan(result[1])
        assert not np.isnan(result[3])
        assert not np.isnan(result[4])
    
    def test_all_nans(self):
        """Test with all NaN values."""
        values = [np.nan, np.nan, np.nan]
        result = robust_zscore(values)
        assert np.all(np.isnan(result))
    
    def test_empty_array(self):
        """Test with empty array."""
        result = robust_zscore([])
        assert len(result) == 0
        assert result.dtype == float
    
    def test_single_value(self):
        """Test with single value."""
        values = [42]
        result = robust_zscore(values)
        assert np.all(np.isnan(result))  # MAD = 0 for single value
    
    def test_numerical_accuracy(self):
        """Test numerical accuracy of calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = robust_zscore(values)
        
        # Manual calculation
        median_val = 3.0
        mad_val = 1.0  # median([2,1,0,1,2]) = 1
        scaling_factor = 1.4826 * mad_val
        expected = (np.array(values) - median_val) / scaling_factor
        
        np.testing.assert_allclose(result, expected, rtol=1e-10)


class TestCalculateRobustZScore:
    """Test the alias function calculate_robust_zscore."""
    
    def test_alias_functionality(self):
        """Test that alias works identically to robust_zscore."""
        values = [1, 2, 3, 4, 5]
        result1 = robust_zscore(values)
        result2 = calculate_robust_zscore(values)
        
        np.testing.assert_array_equal(result1, result2)


class TestSummaryStatistics:
    """Test comprehensive summary statistics."""
    
    def test_normal_data(self):
        """Test with normal data."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = summary_statistics(values)
        
        assert result['count'] == 10
        assert result['median'] == 5.5
        assert result['min'] == 1.0
        assert result['max'] == 10.0
        assert result['q25'] == 3.25
        assert result['q75'] == 7.75
        assert result['nan_count'] == 0
        assert result['mad'] == mad(values)
    
    def test_with_nans(self):
        """Test with NaN values."""
        values = [1, 2, np.nan, 4, 5, np.nan]
        result = summary_statistics(values)
        
        assert result['count'] == 4  # Valid values
        assert result['nan_count'] == 2
        assert result['median'] == 3.0  # median of [1, 2, 4, 5]
        assert result['min'] == 1.0
        assert result['max'] == 5.0
    
    def test_empty_data(self):
        """Test with empty data."""
        result = summary_statistics([])
        
        assert result['count'] == 0
        assert result['nan_count'] == 0
        assert np.isnan(result['median'])
        assert np.isnan(result['min'])
        assert np.isnan(result['max'])
    
    def test_all_nans(self):
        """Test with all NaN data."""
        values = [np.nan, np.nan, np.nan]
        result = summary_statistics(values)
        
        assert result['count'] == 0
        assert result['nan_count'] == 3
        assert np.isnan(result['median'])


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_is_constant_array(self):
        """Test constant array detection."""
        assert is_constant_array([5, 5, 5, 5]) == True
        assert is_constant_array([1, 2, 3, 4]) == False
        assert is_constant_array([1, 1, np.nan, 1]) == True  # NaNs ignored
        assert is_constant_array([np.nan, np.nan]) == True  # All NaN
        assert is_constant_array([]) == True  # Empty
        assert is_constant_array([42]) == True  # Single value
    
    def test_is_constant_array_with_tolerance(self):
        """Test constant array detection with tolerance.""" 
        assert is_constant_array([1.0, 1.0000001, 1.0000002], tolerance=1e-5) == True
        assert is_constant_array([1.0, 1.1, 1.2], tolerance=1e-5) == False
    
    def test_count_valid_values(self):
        """Test counting valid values."""
        assert count_valid_values([1, 2, 3, 4, 5]) == 5
        assert count_valid_values([1, np.nan, 3, np.nan, 5]) == 3
        assert count_valid_values([np.nan, np.nan, np.nan]) == 0
        assert count_valid_values([]) == 0
        assert count_valid_values([42]) == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_large_values(self):
        """Test with very large values."""
        values = [1e10, 2e10, 3e10, 4e10, 5e10]
        result = robust_zscore(values)
        
        # Should handle large values without overflow
        assert np.all(np.isfinite(result))
        assert abs(np.median(result)) < 1e-10  # Median Z should be ~0
    
    def test_very_small_values(self):
        """Test with very small values."""
        values = [1e-10, 2e-10, 3e-10, 4e-10, 5e-10]
        result = robust_zscore(values)
        
        # Should handle small values without underflow
        assert np.all(np.isfinite(result))
        assert abs(np.median(result)) < 1e-10
    
    def test_mixed_types(self):
        """Test with mixed numeric types."""
        values = [1, 2.0, np.int32(3), np.float64(4.0)]
        result = robust_zscore(values)
        
        # Should convert to float and work correctly
        assert result.dtype == float
        assert len(result) == 4
        assert np.all(np.isfinite(result))
    
    def test_infinite_values(self):
        """Test with infinite values."""
        values = [1, 2, np.inf, 4, 5]
        result = robust_zscore(values)
        
        # Infinite values should be handled (likely as NaN in result)
        # Implementation should not crash
        assert len(result) == len(values)