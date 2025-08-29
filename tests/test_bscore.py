"""Unit tests for B-score calculation module.

Tests cover median-polish algorithm, B-score computation, and the BScoreProcessor class.
All tests ensure numerical reproducibility and proper handling of edge cases.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from analytics.bscore import (
    median_polish, 
    calculate_bscore, 
    BScoreProcessor,
    BScoreError,
    ConvergenceError,
    apply_bscoring_to_dataframe,
    validate_bscore_matrix,
)


class TestMedianPolish:
    """Test cases for the median-polish algorithm."""
    
    def test_median_polish_simple_matrix(self):
        """Test median-polish on a simple additive matrix."""
        # Create a matrix with known additive structure
        # True row effects: [1, 2, 3]
        # True col effects: [0.5, 1.0, 1.5, 2.0]
        # Grand median: 2.0
        
        row_effects = np.array([1, 2, 3])
        col_effects = np.array([0.5, 1.0, 1.5, 2.0])
        grand_median = 2.0
        
        matrix = np.zeros((3, 4))
        for i in range(3):
            for j in range(4):
                matrix[i, j] = grand_median + row_effects[i] + col_effects[j]
        
        # Apply median-polish
        residuals = median_polish(matrix, max_iter=10, tol=1e-6)
        
        # Residuals should be close to zero for perfect additive matrix
        assert np.allclose(residuals, 0, atol=1e-6), f"Residuals not close to zero: {residuals}"
    
    def test_median_polish_with_noise(self):
        """Test median-polish with random noise added."""
        np.random.seed(42)  # For reproducibility
        
        # Create base matrix with additive structure  
        n_rows, n_cols = 6, 8
        row_effects = np.random.randn(n_rows) * 2
        col_effects = np.random.randn(n_cols) * 2
        grand_median = 5.0
        
        matrix = np.zeros((n_rows, n_cols))
        for i in range(n_rows):
            for j in range(n_cols):
                matrix[i, j] = grand_median + row_effects[i] + col_effects[j]
        
        # Add small amount of noise
        noise = np.random.randn(n_rows, n_cols) * 0.1
        noisy_matrix = matrix + noise
        
        # Apply median-polish
        residuals = median_polish(noisy_matrix, max_iter=20, tol=1e-8)
        
        # Residuals should be close to the noise we added
        assert np.std(residuals) < 0.5, f"Residuals std too large: {np.std(residuals)}"
        assert np.abs(np.mean(residuals)) < 0.1, f"Residuals mean not close to zero: {np.mean(residuals)}"
    
    def test_median_polish_with_missing_values(self):
        """Test median-polish handles NaN values correctly."""
        matrix = np.array([
            [1.0, 2.0, np.nan, 4.0],
            [2.0, np.nan, 4.0, 5.0],
            [np.nan, 4.0, 5.0, 6.0]
        ])
        
        residuals = median_polish(matrix, max_iter=10, tol=1e-6)
        
        # Check that NaN positions are preserved
        assert np.isnan(residuals[0, 2])
        assert np.isnan(residuals[1, 1])
        assert np.isnan(residuals[2, 0])
        
        # Check that valid positions have reasonable residuals
        valid_residuals = residuals[~np.isnan(residuals)]
        assert len(valid_residuals) == 6  # 9 - 3 NaN values
        assert np.abs(np.mean(valid_residuals)) < 1.0
    
    def test_median_polish_return_components(self):
        """Test that return_components=True works correctly."""
        matrix = np.array([
            [1.0, 2.0, 3.0],
            [2.0, 3.0, 4.0],
            [3.0, 4.0, 5.0]
        ])
        
        residuals, row_effects, col_effects = median_polish(
            matrix, max_iter=10, tol=1e-6, return_components=True
        )
        
        # Check shapes
        assert residuals.shape == matrix.shape
        assert row_effects.shape == (3,)
        assert col_effects.shape == (3,)
        
        # Check that reconstruction is close to original
        reconstructed = np.zeros_like(matrix)
        for i in range(3):
            for j in range(3):
                reconstructed[i, j] = residuals[i, j] + row_effects[i] + col_effects[j]
        
        assert np.allclose(reconstructed, matrix, atol=1e-6)
    
    def test_median_polish_convergence(self):
        """Test convergence behavior."""
        # Create a matrix that should converge quickly
        matrix = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0],
            [3.0, 4.0, 5.0, 6.0]
        ])
        
        # Test with very tight tolerance - should converge
        residuals = median_polish(matrix, max_iter=50, tol=1e-9)
        assert residuals.shape == matrix.shape
        
        # Test with impossible tolerance - should still return result
        residuals = median_polish(matrix, max_iter=2, tol=1e-12)
        assert residuals.shape == matrix.shape
    
    def test_median_polish_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with 1D array
        with pytest.raises(ValueError, match="Expected 2D matrix"):
            median_polish(np.array([1, 2, 3]))
        
        # Test with empty matrix
        with pytest.raises(ValueError, match="cannot have zero rows"):
            median_polish(np.array([]).reshape(0, 3))
        
        # Test with single element matrix
        single = np.array([[5.0]])
        residuals = median_polish(single)
        assert residuals.shape == (1, 1)
        
        # Test with all NaN matrix
        nan_matrix = np.full((3, 3), np.nan)
        residuals = median_polish(nan_matrix)
        assert np.all(np.isnan(residuals))


class TestCalculateBScore:
    """Test cases for B-score calculation."""
    
    def test_calculate_bscore_basic(self):
        """Test basic B-score calculation."""
        np.random.seed(123)
        
        # Create a matrix with some structure plus noise
        n_rows, n_cols = 8, 12  # 96-well plate
        matrix = np.random.randn(n_rows, n_cols) * 2 + 5  # Mean around 5, std around 2
        
        # Add systematic row and column effects
        for i in range(n_rows):
            matrix[i, :] += (i - n_rows/2) * 0.5  # Row gradient
        for j in range(n_cols):
            matrix[:, j] += (j - n_cols/2) * 0.3  # Column gradient
        
        # Calculate B-scores
        bscores = calculate_bscore(matrix, max_iter=10, tol=1e-6)
        
        # Check basic properties
        assert bscores.shape == matrix.shape
        
        # B-scores should be approximately standardized (mean~0, std~1)
        valid_bscores = bscores[~np.isnan(bscores)]
        assert len(valid_bscores) == bscores.size  # No NaN in this case
        
        assert abs(np.mean(valid_bscores)) < 0.2, f"Mean not close to 0: {np.mean(valid_bscores)}"
        assert abs(np.std(valid_bscores) - 1.0) < 0.3, f"Std not close to 1: {np.std(valid_bscores)}"
    
    def test_calculate_bscore_with_missing_values(self):
        """Test B-score calculation with missing values."""
        matrix = np.array([
            [1.0, 2.0, 3.0, np.nan],
            [2.0, 3.0, np.nan, 5.0],
            [3.0, np.nan, 5.0, 6.0],
            [np.nan, 5.0, 6.0, 7.0]
        ])
        
        bscores = calculate_bscore(matrix)
        
        # Check that NaN positions are preserved
        assert np.isnan(bscores[0, 3])
        assert np.isnan(bscores[1, 2])
        assert np.isnan(bscores[2, 1])
        assert np.isnan(bscores[3, 0])
        
        # Check that valid positions have B-scores
        valid_bscores = bscores[~np.isnan(bscores)]
        assert len(valid_bscores) == 12  # 16 - 4 NaN
        assert np.abs(np.mean(valid_bscores)) < 0.5
    
    def test_calculate_bscore_constant_matrix(self):
        """Test B-score calculation with constant values (zero MAD case)."""
        # All values are the same
        constant_matrix = np.full((4, 6), 5.0)
        
        bscores = calculate_bscore(constant_matrix)
        
        # Should return all NaN when MAD = 0
        assert np.all(np.isnan(bscores))
    
    def test_calculate_bscore_numerical_precision(self):
        """Test numerical precision of B-score calculation."""
        # Use known matrix for reproducibility testing
        np.random.seed(42)
        matrix = np.random.randn(6, 8) * 3 + 10
        
        # Calculate B-scores multiple times
        bscores1 = calculate_bscore(matrix, max_iter=20, tol=1e-9)
        bscores2 = calculate_bscore(matrix, max_iter=20, tol=1e-9)
        
        # Results should be identical (within floating point precision)
        assert np.allclose(bscores1, bscores2, atol=1e-9, equal_nan=True)
        
        # Test with different but reasonable tolerances
        bscores3 = calculate_bscore(matrix, max_iter=20, tol=1e-6)
        assert np.allclose(bscores1, bscores3, atol=1e-6, equal_nan=True)


class TestBScoreProcessor:
    """Test cases for BScoreProcessor class."""
    
    @pytest.fixture
    def sample_plate_data(self):
        """Create sample plate DataFrame for testing."""
        np.random.seed(456)
        
        # Create 96-well plate data
        rows = []
        for i in range(8):  # A-H
            for j in range(1, 13):  # 1-12
                row_letter = chr(ord('A') + i)
                rows.append({
                    'Row': row_letter,
                    'Col': j,
                    'Z_lptA': np.random.randn() * 2 + 1,
                    'Z_ldtD': np.random.randn() * 1.5 + 0.5,
                    'Ratio_lptA': np.random.lognormal(0, 0.5),
                    'Ratio_ldtD': np.random.lognormal(-0.2, 0.6),
                    'PlateID': 'TestPlate1'
                })
        
        return pd.DataFrame(rows)
    
    def test_bscore_processor_initialization(self):
        """Test BScoreProcessor initialization."""
        processor = BScoreProcessor(max_iter=15, tol=1e-7, cache_enabled=False)
        
        assert processor.max_iter == 15
        assert processor.tol == 1e-7
        assert processor.cache_enabled == False
        assert processor.enabled_metrics == ['Z_lptA', 'Z_ldtD', 'Ratio_lptA', 'Ratio_ldtD']
    
    def test_set_enabled_metrics(self):
        """Test setting enabled metrics."""
        processor = BScoreProcessor()
        
        new_metrics = ['Z_lptA', 'Ratio_lptA']
        processor.set_enabled_metrics(new_metrics)
        
        assert processor.enabled_metrics == new_metrics
    
    def test_matrix_conversion_methods(self, sample_plate_data):
        """Test matrix conversion methods."""
        processor = BScoreProcessor()
        
        # Test DataFrame to matrix conversion
        matrix = processor._matrix_from_plate_data(sample_plate_data, 'Z_lptA', (8, 12))
        
        assert matrix.shape == (8, 12)
        
        # Check that well A1 maps to position [0, 0]
        a1_value = sample_plate_data[
            (sample_plate_data['Row'] == 'A') & (sample_plate_data['Col'] == 1)
        ]['Z_lptA'].iloc[0]
        assert matrix[0, 0] == a1_value
        
        # Check that well H12 maps to position [7, 11]
        h12_value = sample_plate_data[
            (sample_plate_data['Row'] == 'H') & (sample_plate_data['Col'] == 12)
        ]['Z_lptA'].iloc[0]
        assert matrix[7, 11] == h12_value
        
        # Test matrix to DataFrame conversion
        bscore_series = processor._matrix_to_plate_data(matrix, sample_plate_data, 'B_Z_lptA', (8, 12))
        
        assert len(bscore_series) == len(sample_plate_data)
        assert bscore_series.iloc[0] == a1_value  # First row should be A1
        assert bscore_series.iloc[-1] == h12_value  # Last row should be H12
    
    def test_calculate_bscores_for_plate(self, sample_plate_data):
        """Test B-score calculation for a complete plate."""
        processor = BScoreProcessor()
        
        result_df = processor.calculate_bscores_for_plate(sample_plate_data)
        
        # Check that B-score columns were added
        expected_columns = ['B_Z_lptA', 'B_Z_ldtD', 'B_Ratio_lptA', 'B_Ratio_ldtD']
        for col in expected_columns:
            assert col in result_df.columns
        
        # Check that original columns are preserved
        original_columns = ['Row', 'Col', 'Z_lptA', 'Z_ldtD', 'Ratio_lptA', 'Ratio_ldtD']
        for col in original_columns:
            assert col in result_df.columns
        
        # Check data integrity
        assert len(result_df) == len(sample_plate_data)
        
        # B-scores should be approximately standardized
        for col in expected_columns:
            valid_values = result_df[col].dropna()
            if len(valid_values) > 10:  # Only check if sufficient data
                assert abs(valid_values.mean()) < 0.5, f"Mean of {col} not close to 0: {valid_values.mean()}"
                assert 0.5 < valid_values.std() < 2.0, f"Std of {col} not reasonable: {valid_values.std()}"
    
    def test_calculate_bscores_missing_columns(self, sample_plate_data):
        """Test error handling for missing columns."""
        processor = BScoreProcessor()
        
        # Remove required column
        incomplete_df = sample_plate_data.drop(columns=['Row'])
        
        with pytest.raises(ValueError, match="Missing required columns"):
            processor.calculate_bscores_for_plate(incomplete_df)
    
    def test_caching_functionality(self, sample_plate_data):
        """Test result caching."""
        processor = BScoreProcessor(cache_enabled=True)
        
        # First calculation
        result1 = processor.calculate_bscores_for_plate(sample_plate_data, metrics=['Z_lptA'])
        cache_size_after_first = len(processor.cache)
        
        # Second calculation with same data - should use cache
        result2 = processor.calculate_bscores_for_plate(sample_plate_data, metrics=['Z_lptA'])
        cache_size_after_second = len(processor.cache)
        
        # Cache size shouldn't increase
        assert cache_size_after_first == cache_size_after_second
        
        # Results should be identical
        pd.testing.assert_series_equal(result1['B_Z_lptA'], result2['B_Z_lptA'])
        
        # Clear cache
        processor.clear_cache()
        assert len(processor.cache) == 0
    
    def test_custom_plate_layout(self, sample_plate_data):
        """Test with custom plate layout (384-well)."""
        processor = BScoreProcessor()
        
        # Create 384-well data (16x24)
        rows_384 = []
        for i in range(16):  # A-P
            for j in range(1, 25):  # 1-24
                row_letter = chr(ord('A') + i)
                rows_384.append({
                    'Row': row_letter,
                    'Col': j,
                    'Z_lptA': np.random.randn() * 2
                })
        
        df_384 = pd.DataFrame(rows_384)
        
        result_df = processor.calculate_bscores_for_plate(
            df_384, metrics=['Z_lptA'], plate_layout=(16, 24)
        )
        
        assert 'B_Z_lptA' in result_df.columns
        assert len(result_df) == 384
    
    def test_processing_summary(self):
        """Test get_processing_summary method."""
        processor = BScoreProcessor(max_iter=15, tol=1e-7)
        processor.set_enabled_metrics(['Z_lptA'])
        
        summary = processor.get_processing_summary()
        
        assert summary['enabled_metrics'] == ['Z_lptA']
        assert summary['max_iter'] == 15
        assert summary['tolerance'] == 1e-7
        assert 'cached_results' in summary


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def sample_plate_data(self):
        """Create sample plate DataFrame for testing."""
        np.random.seed(789)
        
        rows = []
        for i in range(8):
            for j in range(1, 13):
                row_letter = chr(ord('A') + i)
                rows.append({
                    'Row': row_letter,
                    'Col': j,
                    'Z_lptA': np.random.randn() * 1.5,
                    'Z_ldtD': np.random.randn() * 1.2,
                })
        
        return pd.DataFrame(rows)
    
    def test_apply_bscoring_to_dataframe(self, sample_plate_data):
        """Test apply_bscoring_to_dataframe function."""
        result_df = apply_bscoring_to_dataframe(
            sample_plate_data, 
            metrics=['Z_lptA'], 
            max_iter=5, 
            tol=1e-5
        )
        
        assert 'B_Z_lptA' in result_df.columns
        assert len(result_df) == len(sample_plate_data)
        
        # Check that B-scores are reasonable
        b_scores = result_df['B_Z_lptA'].dropna()
        assert abs(b_scores.mean()) < 0.3
        assert 0.5 < b_scores.std() < 2.0
    
    def test_validate_bscore_matrix(self):
        """Test matrix validation function."""
        # Valid matrix
        valid_matrix = np.random.randn(8, 12)
        assert validate_bscore_matrix(valid_matrix) == True
        
        # Matrix with some NaN values (acceptable)
        matrix_with_nan = valid_matrix.copy()
        matrix_with_nan[0:2, 0:2] = np.nan  # 4/96 = 4.2% NaN
        assert validate_bscore_matrix(matrix_with_nan) == True
        
        # Matrix with too many NaN values
        matrix_mostly_nan = np.full((8, 12), np.nan)
        matrix_mostly_nan[0:3, 0:3] = 1.0  # Only 9 valid values
        with pytest.raises(ValueError, match="Too many NaN values"):
            validate_bscore_matrix(matrix_mostly_nan, max_nan_fraction=0.1)
        
        # Invalid dimensions
        with pytest.raises(ValueError, match="Expected 2D matrix"):
            validate_bscore_matrix(np.array([1, 2, 3]))
        
        # Empty matrix
        with pytest.raises(ValueError, match="Matrix is empty"):
            validate_bscore_matrix(np.array([]).reshape(0, 0))
        
        # Insufficient valid data
        tiny_matrix = np.array([[1.0, np.nan], [np.nan, np.nan]])
        with pytest.raises(ValueError, match="Insufficient valid data"):
            validate_bscore_matrix(tiny_matrix)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_bscore_error_handling(self):
        """Test BScoreError handling."""
        # Test with invalid input to trigger BScoreError
        with pytest.raises(BScoreError):
            calculate_bscore("not a matrix")
    
    def test_median_polish_with_problematic_data(self):
        """Test median-polish with problematic data."""
        # Matrix with extreme values
        extreme_matrix = np.array([
            [1e10, 1e-10, 1.0],
            [1e-10, 1e10, 1.0],
            [1.0, 1.0, 1e10]
        ])
        
        # Should handle extreme values gracefully
        residuals = median_polish(extreme_matrix, max_iter=10)
        assert residuals.shape == extreme_matrix.shape
        
        # Matrix with very small differences (near machine precision)
        epsilon = 1e-15
        precision_matrix = np.array([
            [1.0, 1.0 + epsilon, 1.0 + 2*epsilon],
            [1.0 + epsilon, 1.0 + 2*epsilon, 1.0 + 3*epsilon]
        ])
        
        residuals = median_polish(precision_matrix, max_iter=10, tol=1e-12)
        assert residuals.shape == precision_matrix.shape


class TestNumericalReproducibility:
    """Test numerical reproducibility as required by PRD."""
    
    def test_reproducible_bscores(self):
        """Test that B-scores are reproducible within tolerance."""
        np.random.seed(999)
        
        # Create test matrix
        matrix = np.random.randn(8, 12) * 2 + 5
        
        # Calculate B-scores multiple times
        bscores1 = calculate_bscore(matrix, max_iter=20, tol=1e-9)
        bscores2 = calculate_bscore(matrix, max_iter=20, tol=1e-9)
        bscores3 = calculate_bscore(matrix, max_iter=20, tol=1e-9)
        
        # All results should be identical within 1e-9 tolerance
        assert np.allclose(bscores1, bscores2, atol=1e-9, equal_nan=True)
        assert np.allclose(bscores2, bscores3, atol=1e-9, equal_nan=True)
    
    def test_processor_reproducibility(self):
        """Test that BScoreProcessor gives reproducible results."""
        np.random.seed(111)
        
        # Create test data
        rows = []
        for i in range(8):
            for j in range(1, 13):
                rows.append({
                    'Row': chr(ord('A') + i),
                    'Col': j,
                    'Z_lptA': np.random.randn()
                })
        
        df = pd.DataFrame(rows)
        
        # Process multiple times
        processor1 = BScoreProcessor(max_iter=15, tol=1e-8, cache_enabled=False)
        processor2 = BScoreProcessor(max_iter=15, tol=1e-8, cache_enabled=False)
        
        result1 = processor1.calculate_bscores_for_plate(df, metrics=['Z_lptA'])
        result2 = processor2.calculate_bscores_for_plate(df, metrics=['Z_lptA'])
        
        # Results should be identical
        pd.testing.assert_series_equal(result1['B_Z_lptA'], result2['B_Z_lptA'])


if __name__ == "__main__":
    pytest.main([__file__])