"""Golden reference tests for bio-hit-finder platform.

Tests exact formulas from PRD with golden reference data fixtures and validates
numerical tolerance (≤ 1e-9 as specified). Includes reference calculations for:
- Reporter ratios: Ratio_lptA = BG_lptA / BT_lptA  
- OD normalization: OD_WT_norm = OD_WT / median(OD_WT)
- Robust Z-scores: Z = (value - median) / (1.4826 * MAD)
- Viability gates: flags based on f * median thresholds
- B-scoring validation against reference calculations
- Edge effect detection validation
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from typing import Dict, Any

from core.calculations import (
    calculate_reporter_ratios,
    calculate_od_normalization, 
    calculate_robust_zscore_columns,
    apply_viability_gate,
    process_plate_calculations
)
from core.statistics import calculate_robust_zscore, calculate_mad
from analytics.bscore import calculate_bscore_matrix
from analytics.edge_effects import detect_edge_effects


class TestGoldenReporterRatios:
    """Golden tests for reporter ratio calculations (PRD Section 4.1)."""
    
    @pytest.fixture
    def golden_ratio_data(self) -> Dict[str, Any]:
        """Golden reference data for reporter ratio testing."""
        return {
            'input': pd.DataFrame({
                'BG_lptA': [1000.0, 2000.0, 1500.0, 800.0, 1200.0],
                'BT_lptA': [500.0, 1000.0, 750.0, 400.0, 600.0],
                'BG_ldtD': [1200.0, 2400.0, 1800.0, 960.0, 1440.0],
                'BT_ldtD': [400.0, 800.0, 600.0, 320.0, 480.0],
            }),
            'expected': {
                'Ratio_lptA': [2.0, 2.0, 2.0, 2.0, 2.0],
                'Ratio_ldtD': [3.0, 3.0, 3.0, 3.0, 3.0],
            }
        }
    
    def test_exact_ratio_calculations(self, golden_ratio_data: Dict[str, Any]):
        """Test exact reporter ratio calculations with golden data."""
        result = calculate_reporter_ratios(golden_ratio_data['input'])
        
        # PRD Formula: Ratio_lptA = BG_lptA / BT_lptA
        expected_lptA = golden_ratio_data['expected']['Ratio_lptA']
        expected_ldtD = golden_ratio_data['expected']['Ratio_ldtD']
        
        # Numerical tolerance: ≤ 1e-9
        np.testing.assert_allclose(
            result['Ratio_lptA'], 
            expected_lptA,
            rtol=1e-9, 
            atol=1e-12,
            err_msg="Reporter ratio lptA calculation failed golden test"
        )
        
        np.testing.assert_allclose(
            result['Ratio_ldtD'],
            expected_ldtD, 
            rtol=1e-9,
            atol=1e-12,
            err_msg="Reporter ratio ldtD calculation failed golden test"
        )
    
    def test_edge_cases_division(self):
        """Test edge cases for division operations."""
        edge_data = pd.DataFrame({
            'BG_lptA': [100.0, 200.0, 0.0, 100.0],
            'BT_lptA': [50.0, 0.0, 50.0, 50.0],
            'BG_ldtD': [150.0, 300.0, 0.0, 150.0],
            'BT_ldtD': [75.0, 0.0, 0.0, 75.0],
        })
        
        result = calculate_reporter_ratios(edge_data)
        
        # Normal division
        assert abs(result['Ratio_lptA'].iloc[0] - 2.0) < 1e-9
        
        # Division by zero should produce inf
        assert np.isinf(result['Ratio_lptA'].iloc[1])
        
        # Zero numerator should produce 0.0
        assert abs(result['Ratio_lptA'].iloc[2] - 0.0) < 1e-9
        
        # Zero/Zero case should produce NaN
        assert np.isnan(result['Ratio_ldtD'].iloc[2])


class TestGoldenODNormalization:
    """Golden tests for OD normalization (PRD Section 4.2)."""
    
    @pytest.fixture
    def golden_od_data(self) -> Dict[str, Any]:
        """Golden reference data for OD normalization testing."""
        return {
            'input': pd.DataFrame({
                'OD_WT': [0.5, 1.0, 1.5, 2.0, 2.5],    # median = 1.5
                'OD_tolC': [0.3, 0.6, 0.9, 1.2, 1.5],  # median = 0.9
                'OD_SA': [0.4, 0.8, 1.2, 1.6, 2.0],    # median = 1.2
            }),
            'expected': {
                'OD_WT_norm': [1/3, 2/3, 1.0, 4/3, 5/3],      # / 1.5
                'OD_tolC_norm': [1/3, 2/3, 1.0, 4/3, 5/3],    # / 0.9
                'OD_SA_norm': [1/3, 2/3, 1.0, 4/3, 5/3],      # / 1.2
            }
        }
    
    def test_exact_normalization_calculations(self, golden_od_data: Dict[str, Any]):
        """Test exact OD normalization calculations with golden data."""
        result = calculate_od_normalization(golden_od_data['input'])
        
        # PRD Formula: OD_norm = OD / median(OD)
        input_data = golden_od_data['input']
        
        # Calculate expected values manually
        expected_wt = input_data['OD_WT'] / input_data['OD_WT'].median()
        expected_tolc = input_data['OD_tolC'] / input_data['OD_tolC'].median() 
        expected_sa = input_data['OD_SA'] / input_data['OD_SA'].median()
        
        # Numerical tolerance: ≤ 1e-9
        np.testing.assert_allclose(
            result['OD_WT_norm'],
            expected_wt,
            rtol=1e-9,
            atol=1e-12,
            err_msg="OD WT normalization failed golden test"
        )
        
        np.testing.assert_allclose(
            result['OD_tolC_norm'],
            expected_tolc,
            rtol=1e-9, 
            atol=1e-12,
            err_msg="OD tolC normalization failed golden test"
        )
        
        np.testing.assert_allclose(
            result['OD_SA_norm'],
            expected_sa,
            rtol=1e-9,
            atol=1e-12,
            err_msg="OD SA normalization failed golden test"
        )


class TestGoldenRobustZScores:
    """Golden tests for robust Z-score calculations (PRD Section 4.3)."""
    
    @pytest.fixture
    def golden_zscore_data(self) -> Dict[str, Any]:
        """Golden reference data for Z-score testing."""
        # Carefully chosen values with known median and MAD
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        # median = 5.5, MAD = median([4.5, 3.5, 2.5, 1.5, 0.5, 0.5, 1.5, 2.5, 3.5, 4.5]) = 2.5
        
        return {
            'input': pd.DataFrame({
                'Values': values,
                'Ratio_lptA': values,
                'Ratio_ldtD': [x * 2 for x in values]  # Scale by 2
            }),
            'expected_stats': {
                'median': 5.5,
                'mad': 2.5,
                'robust_scale': 1.4826 * 2.5  # = 3.7065
            }
        }
    
    def test_exact_zscore_calculations(self, golden_zscore_data: Dict[str, Any]):
        """Test exact robust Z-score calculations with golden data."""
        input_data = golden_zscore_data['input']
        expected_stats = golden_zscore_data['expected_stats']
        
        # Test individual function first
        values = input_data['Values'].values
        median = np.median(values)
        mad = calculate_mad(values)
        
        # Verify statistics match expected
        assert abs(median - expected_stats['median']) < 1e-9
        assert abs(mad - expected_stats['mad']) < 1e-9
        
        # Calculate Z-scores manually
        expected_z = (values - median) / (1.4826 * mad)
        
        # Test via function
        calculated_z = calculate_robust_zscore(values)
        
        # PRD Formula: Z = (value - median) / (1.4826 * MAD)
        np.testing.assert_allclose(
            calculated_z,
            expected_z,
            rtol=1e-9,
            atol=1e-12,
            err_msg="Robust Z-score calculation failed golden test"
        )
        
        # Test via column function
        result = calculate_robust_zscore_columns(input_data)
        
        np.testing.assert_allclose(
            result['Z_Ratio_lptA'],
            expected_z,
            rtol=1e-9,
            atol=1e-12,
            err_msg="Column Z-score calculation failed golden test"
        )
    
    def test_mad_calculation_golden(self):
        """Test MAD calculation with golden reference."""
        # Known values with exact MAD
        values = np.array([1, 2, 3, 4, 5])  # median = 3
        # Deviations: [2, 1, 0, 1, 2], median = 1
        expected_mad = 1.0
        
        calculated_mad = calculate_mad(values)
        assert abs(calculated_mad - expected_mad) < 1e-9
        
        # Test with even number of values
        values_even = np.array([1, 2, 4, 5])  # median = 3
        # Deviations: [2, 1, 1, 2], median = 1.5
        expected_mad_even = 1.5
        
        calculated_mad_even = calculate_mad(values_even)
        assert abs(calculated_mad_even - expected_mad_even) < 1e-9
    
    def test_zero_mad_handling(self):
        """Test handling when MAD = 0 (constant values)."""
        constant_values = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        
        mad = calculate_mad(constant_values)
        assert mad == 0.0
        
        # Z-scores should be NaN when MAD = 0
        z_scores = calculate_robust_zscore(constant_values)
        assert np.isnan(z_scores).all()


class TestGoldenViabilityGates:
    """Golden tests for viability gating (PRD Section 4.4)."""
    
    @pytest.fixture
    def golden_viability_data(self) -> Dict[str, Any]:
        """Golden reference data for viability gating."""
        return {
            'input': pd.DataFrame({
                'BT_lptA': [100.0, 80.0, 60.0, 40.0, 20.0, 10.0],  # median = 50.0
                'BT_ldtD': [200.0, 160.0, 120.0, 80.0, 40.0, 20.0], # median = 100.0
            }),
            'thresholds': {
                'f': 0.3,
                'bt_lptA_threshold': 0.3 * 50.0,  # = 15.0
                'bt_ldtD_threshold': 0.3 * 100.0,  # = 30.0
            },
            'expected': {
                'viability_ok_lptA': [True, True, True, True, True, False],
                'viability_fail_lptA': [False, False, False, False, False, True],
                'viability_ok_ldtD': [True, True, True, True, True, False],
                'viability_fail_ldtD': [False, False, False, False, False, True],
            }
        }
    
    def test_exact_viability_calculations(self, golden_viability_data: Dict[str, Any]):
        """Test exact viability gate calculations with golden data."""
        input_data = golden_viability_data['input']
        expected = golden_viability_data['expected']
        f = golden_viability_data['thresholds']['f']
        
        result = apply_viability_gate(input_data, f=f)
        
        # PRD Formula: viability_ok = BT >= f * median(BT)
        pd.testing.assert_series_equal(
            result['viability_ok_lptA'],
            pd.Series(expected['viability_ok_lptA'], name='viability_ok_lptA'),
            check_exact=True,
            err_msg="Viability lptA calculation failed golden test"
        )
        
        pd.testing.assert_series_equal(
            result['viability_fail_lptA'],
            pd.Series(expected['viability_fail_lptA'], name='viability_fail_lptA'),
            check_exact=True,
            err_msg="Viability fail lptA calculation failed golden test"
        )
        
        pd.testing.assert_series_equal(
            result['viability_ok_ldtD'],
            pd.Series(expected['viability_ok_ldtD'], name='viability_ok_ldtD'),
            check_exact=True,
            err_msg="Viability ldtD calculation failed golden test"
        )
    
    def test_threshold_variations(self):
        """Test viability calculations with different thresholds."""
        data = pd.DataFrame({
            'BT_lptA': [100, 50, 30, 20, 10],  # median = 30
            'BT_ldtD': [200, 100, 60, 40, 20], # median = 60
        })
        
        test_cases = [
            {'f': 0.1, 'expected_lptA_fails': 0},  # threshold = 3, all pass
            {'f': 0.5, 'expected_lptA_fails': 2},  # threshold = 15, 2 fail
            {'f': 0.8, 'expected_lptA_fails': 4},  # threshold = 24, 4 fail
        ]
        
        for case in test_cases:
            result = apply_viability_gate(data, f=case['f'])
            actual_fails = result['viability_fail_lptA'].sum()
            
            assert actual_fails == case['expected_lptA_fails'], \
                f"f={case['f']}: expected {case['expected_lptA_fails']} fails, got {actual_fails}"


class TestGoldenBScoring:
    """Golden tests for B-scoring (median polish + robust scaling)."""
    
    @pytest.fixture
    def golden_bscore_data(self) -> Dict[str, Any]:
        """Golden reference data for B-scoring validation."""
        # 3x3 matrix with known row/column effects
        np.random.seed(42)  # Reproducible
        
        # Create plate with artificial row/column bias
        rows, cols = 8, 12  # 96-well plate
        base_values = np.random.normal(0, 1, (rows, cols))
        
        # Add row effect (increasing by row)
        row_effect = np.arange(rows).reshape(-1, 1) * 0.5
        
        # Add column effect (sinusoidal)
        col_effect = np.sin(np.arange(cols) * np.pi / 6).reshape(1, -1) * 0.3
        
        # Combine effects
        matrix_with_bias = base_values + row_effect + col_effect
        
        return {
            'input_matrix': matrix_with_bias,
            'base_values': base_values,
            'row_effect': row_effect,
            'col_effect': col_effect
        }
    
    def test_bscore_bias_removal(self, golden_bscore_data: Dict[str, Any]):
        """Test that B-scoring removes row/column bias."""
        input_matrix = golden_bscore_data['input_matrix']
        
        # Calculate B-scores
        b_scores = calculate_bscore_matrix(input_matrix)
        
        # B-scores should have mean ~0 and std ~1 (robust scaling)
        assert abs(np.nanmean(b_scores)) < 0.1
        assert abs(np.nanstd(b_scores, ddof=1) - 1.0) < 0.2  # Some tolerance due to robustness
        
        # B-scores should have reduced row/column correlation
        row_means_original = np.nanmean(input_matrix, axis=1)
        row_means_bscore = np.nanmean(b_scores, axis=1)
        
        # Original should have strong row trend, B-scores should not
        from scipy.stats import pearsonr
        
        row_indices = np.arange(len(row_means_original))
        original_corr, _ = pearsonr(row_indices, row_means_original)
        bscore_corr, _ = pearsonr(row_indices, row_means_bscore)
        
        # B-scores should have much lower correlation with position
        assert abs(bscore_corr) < abs(original_corr) * 0.5
    
    def test_bscore_with_missing_values(self):
        """Test B-scoring with missing values (NaN handling)."""
        matrix = np.array([
            [1.0, 2.0, np.nan],
            [4.0, np.nan, 6.0],
            [7.0, 8.0, 9.0]
        ])
        
        b_scores = calculate_bscore_matrix(matrix)
        
        # Should complete without error
        assert b_scores.shape == matrix.shape
        
        # NaN positions should remain NaN
        assert np.isnan(b_scores[0, 2])
        assert np.isnan(b_scores[1, 1])
        
        # Non-NaN values should be computed
        assert not np.isnan(b_scores[0, 0])
        assert not np.isnan(b_scores[2, 2])


class TestGoldenEdgeEffects:
    """Golden tests for edge effect detection."""
    
    @pytest.fixture
    def plates_with_known_effects(self) -> Dict[str, Any]:
        """Create plates with known edge effects for testing."""
        rows, cols = 8, 12
        
        # Plate 1: No edge effect
        normal_plate = np.random.normal(0, 1, (rows, cols))
        
        # Plate 2: Strong edge effect
        edge_plate = np.random.normal(0, 1, (rows, cols))
        # Add edge lift
        edge_plate[0, :] += 2.0  # Top row
        edge_plate[-1, :] += 2.0  # Bottom row
        edge_plate[:, 0] += 2.0  # Left column
        edge_plate[:, -1] += 2.0  # Right column
        
        # Plate 3: Row trend
        trend_plate = np.random.normal(0, 1, (rows, cols))
        for i in range(rows):
            trend_plate[i, :] += i * 0.5  # Increasing by row
        
        return {
            'normal_plate': normal_plate,
            'edge_plate': edge_plate, 
            'trend_plate': trend_plate,
            'expected': {
                'normal_has_edge': False,
                'edge_has_edge': True,
                'trend_has_trend': True
            }
        }
    
    def test_edge_effect_detection(self, plates_with_known_effects: Dict[str, Any]):
        """Test edge effect detection with known patterns."""
        normal_plate = plates_with_known_effects['normal_plate']
        edge_plate = plates_with_known_effects['edge_plate']
        trend_plate = plates_with_known_effects['trend_plate']
        expected = plates_with_known_effects['expected']
        
        # Test normal plate (no edge effect)
        normal_results = detect_edge_effects(normal_plate)
        assert normal_results['severity'] in ['none', 'info'], \
            f"Normal plate incorrectly flagged: {normal_results['severity']}"
        
        # Test edge plate (should detect edge effect)
        edge_results = detect_edge_effects(edge_plate)
        assert edge_results['severity'] in ['warn', 'critical'], \
            f"Edge plate not detected: {edge_results['severity']}"
        assert edge_results['edge_effect_detected'] == True
        
        # Test trend plate (should detect trend)
        trend_results = detect_edge_effects(trend_plate)
        assert 'row_trend' in trend_results and trend_results['row_trend']['significant']
    
    def test_edge_effect_metrics(self):
        """Test specific edge effect metric calculations."""
        # Create minimal plate with known edge pattern
        plate = np.zeros((8, 12))
        
        # Add edge values
        plate[0, :] = 2.0  # Top edge
        plate[-1, :] = 2.0  # Bottom edge
        plate[:, 0] = 2.0  # Left edge
        plate[:, -1] = 2.0  # Right edge
        
        results = detect_edge_effects(plate)
        
        # Should detect significant edge-interior difference
        assert results['edge_interior_diff']['effect_size'] > 1.0
        assert results['edge_effect_detected'] == True


class TestGoldenEndToEnd:
    """Golden tests for complete end-to-end pipeline."""
    
    @pytest.fixture
    def comprehensive_golden_data(self) -> Dict[str, Any]:
        """Comprehensive golden dataset with known expected outputs."""
        return {
            'input': pd.DataFrame({
                'Well': ['A01', 'A02', 'A03', 'A04'],
                'BG_lptA': [1000.0, 2000.0, 1500.0, 800.0],
                'BT_lptA': [500.0, 1000.0, 750.0, 200.0],  # Last one low for viability
                'BG_ldtD': [1200.0, 2400.0, 1800.0, 960.0],
                'BT_ldtD': [600.0, 1200.0, 900.0, 240.0],
                'OD_WT': [1.0, 2.0, 1.5, 0.8],
                'OD_tolC': [0.8, 1.6, 1.2, 0.6],
                'OD_SA': [1.2, 2.4, 1.8, 0.9],
            }),
            'expected_ratios': {
                'Ratio_lptA': [2.0, 2.0, 2.0, 4.0],
                'Ratio_ldtD': [2.0, 2.0, 2.0, 4.0],
            }
        }
    
    def test_complete_pipeline_golden(self, comprehensive_golden_data: Dict[str, Any]):
        """Test complete processing pipeline with golden reference."""
        input_data = comprehensive_golden_data['input']
        expected = comprehensive_golden_data['expected_ratios']
        
        # Process through complete pipeline
        result = process_plate_calculations(input_data, viability_threshold=0.3)
        
        # Test reporter ratios match exactly
        np.testing.assert_allclose(
            result['Ratio_lptA'],
            expected['Ratio_lptA'],
            rtol=1e-9,
            atol=1e-12,
            err_msg="End-to-end ratio calculation failed"
        )
        
        # Test OD normalizations
        expected_od_wt = input_data['OD_WT'] / input_data['OD_WT'].median()
        np.testing.assert_allclose(
            result['OD_WT_norm'],
            expected_od_wt,
            rtol=1e-9,
            atol=1e-12,
            err_msg="End-to-end OD normalization failed"
        )
        
        # Test viability gating
        bt_lptA_median = input_data['BT_lptA'].median()  # 625.0
        threshold = 0.3 * bt_lptA_median  # 187.5
        expected_viable = input_data['BT_lptA'] >= threshold
        
        pd.testing.assert_series_equal(
            result['viability_ok_lptA'],
            expected_viable,
            check_names=False,
            err_msg="End-to-end viability calculation failed"
        )
        
        # Test that all expected columns exist
        required_columns = [
            'Ratio_lptA', 'Ratio_ldtD',
            'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm', 
            'Z_lptA', 'Z_ldtD',
            'viability_ok_lptA', 'viability_ok_ldtD'
        ]
        
        for col in required_columns:
            assert col in result.columns, f"Missing required column: {col}"
    
    def test_numerical_precision_requirements(self):
        """Test that all calculations meet PRD numerical precision requirements."""
        # High precision test data
        precision_data = pd.DataFrame({
            'BG_lptA': [1000.123456789, 2000.987654321],
            'BT_lptA': [500.111111111, 1000.222222222],
            'BG_ldtD': [1200.333333333, 2400.444444444],
            'BT_ldtD': [600.555555555, 1200.666666666],
            'OD_WT': [1.777777777, 2.888888888],
            'OD_tolC': [0.999999999, 1.111111111],
            'OD_SA': [1.222222222, 2.333333333],
        })
        
        result = process_plate_calculations(precision_data, viability_threshold=0.3)
        
        # Manual calculation for verification
        expected_ratio_lptA = precision_data['BG_lptA'] / precision_data['BT_lptA']
        
        # Test meets PRD requirement: differences ≤ 1e-9
        differences = np.abs(result['Ratio_lptA'] - expected_ratio_lptA)
        assert np.all(differences <= 1e-9), \
            f"Precision requirement violated: max difference = {differences.max()}"
    
    def test_reproducibility(self, comprehensive_golden_data: Dict[str, Any]):
        """Test that calculations are completely reproducible."""
        input_data = comprehensive_golden_data['input']
        
        # Run same calculation multiple times
        results = []
        for _ in range(5):
            result = process_plate_calculations(input_data, viability_threshold=0.3)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            pd.testing.assert_frame_equal(
                results[0],
                results[i],
                check_exact=True,
                err_msg=f"Reproducibility failed on run {i+1}"
            )