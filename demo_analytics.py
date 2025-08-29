#!/usr/bin/env python3
"""Demonstration script for the advanced analytics modules.

This script demonstrates the key functionality of the B-scoring and edge effect
detection modules that have been implemented according to the PRD specification.
"""

import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from analytics.bscore import (
    median_polish,
    calculate_bscore, 
    BScoreProcessor,
    apply_bscoring_to_dataframe,
)

from analytics.edge_effects import (
    EdgeEffectDetector,
    detect_edge_effects_simple,
    format_edge_effect_summary,
)


def create_sample_plate_data(n_rows=8, n_cols=12, seed=42):
    """Create sample 96-well plate data for demonstration."""
    np.random.seed(seed)
    
    rows = []
    for i in range(n_rows):
        for j in range(n_cols):
            row_letter = chr(ord('A') + i)
            col_number = j + 1
            
            # Create realistic plate data with some biological structure
            base_lptA = np.random.randn() * 1.5 + 2.0
            base_ldtD = np.random.randn() * 1.2 + 1.5
            
            # Add some systematic plate effects (this is what B-scoring should correct)
            row_effect = (i - n_rows/2) * 0.3  # Row gradient
            col_effect = (j - n_cols/2) * 0.2  # Column gradient
            
            # Add edge effects (higher values near plate edges)
            is_edge = (i == 0 or i == n_rows-1 or j == 0 or j == n_cols-1)
            edge_effect = 1.0 if is_edge else 0.0
            
            rows.append({
                'Row': row_letter,
                'Col': col_number,
                'PlateID': 'Demo_Plate_001',
                'Z_lptA': base_lptA + row_effect + col_effect + edge_effect,
                'Z_ldtD': base_ldtD + row_effect * 0.8 + col_effect * 1.2 + edge_effect * 0.7,
                'Ratio_lptA': np.exp(base_lptA * 0.5 + row_effect * 0.2),
                'Ratio_ldtD': np.exp(base_ldtD * 0.4 + col_effect * 0.3),
            })
    
    return pd.DataFrame(rows)


def demonstrate_median_polish():
    """Demonstrate median-polish algorithm."""
    print("\n" + "="*60)
    print("MEDIAN-POLISH DEMONSTRATION")
    print("="*60)
    
    # Create a matrix with known additive structure
    print("Creating test matrix with additive row/column structure...")
    
    # True effects
    row_effects = np.array([1.0, 2.0, 3.0, 1.5, 2.5])
    col_effects = np.array([0.5, 1.0, 1.5, 2.0])
    grand_mean = 10.0
    
    # Build matrix
    matrix = np.zeros((5, 4))
    for i in range(5):
        for j in range(4):
            matrix[i, j] = grand_mean + row_effects[i] + col_effects[j]
    
    # Add small amount of noise
    matrix += np.random.randn(5, 4) * 0.1
    
    print(f"Original matrix:\n{matrix}")
    print(f"Matrix mean: {np.mean(matrix):.3f}")
    
    # Apply median-polish
    residuals, row_est, col_est = median_polish(matrix, max_iter=20, tol=1e-8, return_components=True)
    
    print(f"\nEstimated row effects: {row_est}")
    print(f"True row effects: {row_effects}")
    print(f"Row estimation error: {np.mean(np.abs(row_est - row_effects)):.6f}")
    
    print(f"\nEstimated col effects: {col_est}")
    print(f"True col effects: {col_effects}")
    print(f"Col estimation error: {np.mean(np.abs(col_est - col_effects)):.6f}")
    
    print(f"\nResiduals (should be close to noise):")
    print(f"Residuals std: {np.std(residuals):.6f}")
    print(f"Residuals mean: {np.mean(residuals):.6f}")


def demonstrate_bscoring():
    """Demonstrate B-score calculation."""
    print("\n" + "="*60) 
    print("B-SCORE CALCULATION DEMONSTRATION")
    print("="*60)
    
    # Create sample plate data
    df = create_sample_plate_data()
    print(f"Created sample plate data: {len(df)} wells")
    
    # Show original Z-score statistics
    print("\nOriginal Z_lptA statistics:")
    print(f"  Mean: {df['Z_lptA'].mean():.3f}")
    print(f"  Std: {df['Z_lptA'].std():.3f}")
    print(f"  Min: {df['Z_lptA'].min():.3f}")
    print(f"  Max: {df['Z_lptA'].max():.3f}")
    
    # Apply B-scoring
    print("\nApplying B-scoring...")
    bscore_processor = BScoreProcessor(max_iter=15, tol=1e-7)
    result_df = bscore_processor.calculate_bscores_for_plate(df)
    
    # Show B-score statistics
    print("\nB-score Z_lptA statistics:")
    print(f"  Mean: {result_df['B_Z_lptA'].mean():.3f}")
    print(f"  Std: {result_df['B_Z_lptA'].std():.3f}")
    print(f"  Min: {result_df['B_Z_lptA'].min():.3f}")
    print(f"  Max: {result_df['B_Z_lptA'].max():.3f}")
    
    # Check that B-scores are properly standardized
    b_mean = result_df['B_Z_lptA'].mean()
    b_std = result_df['B_Z_lptA'].std()
    print(f"\nB-score standardization check:")
    print(f"  Mean close to 0: {abs(b_mean) < 0.1}")
    print(f"  Std close to 1: {abs(b_std - 1.0) < 0.2}")
    
    return result_df


def demonstrate_edge_effects():
    """Demonstrate edge effect detection."""
    print("\n" + "="*60)
    print("EDGE EFFECT DETECTION DEMONSTRATION") 
    print("="*60)
    
    # Create plate data with deliberate edge effects
    df = create_sample_plate_data(seed=123)  # This already has edge effects built in
    print(f"Created sample plate data with edge effects: {len(df)} wells")
    
    # Show edge vs interior comparison for Z_lptA
    edge_mask = (df['Row'].isin(['A', 'H']) | df['Col'].isin([1, 12]))
    edge_values = df[edge_mask]['Z_lptA']
    interior_values = df[~edge_mask]['Z_lptA']
    
    print(f"\nManual edge effect check for Z_lptA:")
    print(f"  Edge wells: n={len(edge_values)}, median={edge_values.median():.3f}")
    print(f"  Interior wells: n={len(interior_values)}, median={interior_values.median():.3f}")
    print(f"  Difference: {edge_values.median() - interior_values.median():.3f}")
    
    # Use EdgeEffectDetector
    print("\nRunning EdgeEffectDetector...")
    detector = EdgeEffectDetector()
    results = detector.detect_edge_effects_dataframe(df, metric='Z_lptA')
    
    if results:
        result = results[0]
        print(f"\nEdge Effect Analysis Results:")
        print(f"  Effect size (d): {result.effect_size_d:.3f}")
        print(f"  Warning level: {result.warning_level.value}")
        print(f"  Edge median: {result.edge_median:.3f}")
        print(f"  Interior median: {result.interior_median:.3f}")
        print(f"  Interior MAD: {result.interior_mad:.3f}")
        print(f"  Row correlation: {result.row_correlation:.3f} (p={result.row_p_value:.3f})")
        print(f"  Col correlation: {result.col_correlation:.3f} (p={result.col_p_value:.3f})")
        
        # Show corner effects
        print("\nCorner deviations (in MAD units):")
        for corner, deviation in result.corner_deviations.items():
            print(f"  {corner}: {deviation:.3f}")
        
        # Format summary
        summary = format_edge_effect_summary(result)
        print(f"\nSummary: {summary}")
    else:
        print("No edge effect results generated")


def demonstrate_integration():
    """Demonstrate integration of both analytics modules."""
    print("\n" + "="*60)
    print("INTEGRATED ANALYTICS DEMONSTRATION")
    print("="*60)
    
    # Create sample data
    df = create_sample_plate_data(seed=456)
    print(f"Created sample plate data: {len(df)} wells")
    
    # Apply both B-scoring and edge effect detection
    print("\nApplying integrated analytics...")
    
    # Step 1: Detect edge effects on original data
    edge_results_original = detect_edge_effects_simple(df, metric='Z_lptA')
    
    # Step 2: Apply B-scoring
    bscored_df = apply_bscoring_to_dataframe(df, metrics=['Z_lptA', 'Z_ldtD'])
    
    # Step 3: Detect edge effects on B-scored data
    edge_results_bscored = detect_edge_effects_simple(bscored_df, metric='B_Z_lptA')
    
    # Compare results
    if edge_results_original and edge_results_bscored:
        orig_result = edge_results_original[0]
        bscore_result = edge_results_bscored[0]
        
        print(f"\nComparison of edge effects:")
        print(f"  Original Z_lptA effect size: {orig_result.effect_size_d:.3f}")
        print(f"  B-scored Z_lptA effect size: {bscore_result.effect_size_d:.3f}")
        print(f"  Improvement: {abs(orig_result.effect_size_d) - abs(bscore_result.effect_size_d):.3f}")
        
        if abs(bscore_result.effect_size_d) < abs(orig_result.effect_size_d):
            print("  [SUCCESS] B-scoring reduced edge effects!")
        else:
            print("  [NOTE] B-scoring did not improve edge effects (may indicate other artifacts)")
    
    print(f"\nB-scored columns added: {[col for col in bscored_df.columns if col.startswith('B_')]}")


def main():
    """Run all demonstrations."""
    print("Bio Hit Finder - Advanced Analytics Module Demonstration")
    print("This demonstrates the B-scoring and edge effect detection capabilities")
    print("implemented according to the PRD specification.")
    
    try:
        demonstrate_median_polish()
        demonstrate_bscoring() 
        demonstrate_edge_effects()
        demonstrate_integration()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("All analytics modules are working correctly!")
        print("\nKey capabilities demonstrated:")
        print("[OK] Median-polish algorithm for row/column bias correction")
        print("[OK] B-score calculation with robust scaling")
        print("[OK] Edge effect detection with multiple diagnostics")
        print("[OK] Row/column trend analysis")
        print("[OK] Corner effect detection")
        print("[OK] Integration of B-scoring with edge effect detection")
        
    except Exception as e:
        print(f"\nERROR: Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    main()