"""Debug Z-score calculation for specific well."""

import pandas as pd
import numpy as np
from core.plate_processor import PlateProcessor
from core.statistics import nan_safe_median, mad

# Load and process the data
processor = PlateProcessor(viability_threshold=0.3)

# Update this path to your actual file
file_path = r"C:\Users\Pierre\Documents\GitHub\bio-hit-finder\backend\test_data\Plate_1.xlsx"

try:
    # Load and process
    raw_df = processor.load_plate_data(file_path)
    processor.auto_detect_columns(raw_df)
    mapped_df = processor.apply_column_mapping(raw_df)
    processed_df = processor.process_single_plate(mapped_df, 'Plate_1')

    # Find well E02
    e02_data = processed_df[processed_df['Well'] == 'E02']

    if len(e02_data) == 0:
        print("Well E02 not found. Available wells:")
        print(processed_df['Well'].unique()[:20])
    else:
        print("\n=== WELL E02 DATA ===")
        print(f"BG_lptA: {e02_data['BG_lptA'].values[0]}")
        print(f"BT_lptA: {e02_data['BT_lptA'].values[0]}")
        print(f"Ratio_lptA: {e02_data['Ratio_lptA'].values[0]}")
        print(f"Z_lptA: {e02_data['Z_lptA'].values[0]}")

        print("\n=== PLATE-WIDE STATISTICS ===")
        ratio_values = processed_df['Ratio_lptA'].dropna()

        median_val = nan_safe_median(ratio_values)
        mad_val = mad(ratio_values)

        print(f"Number of wells: {len(ratio_values)}")
        print(f"Median(Ratio_lptA): {median_val}")
        print(f"MAD(Ratio_lptA): {mad_val}")
        print(f"1.4826 × MAD: {1.4826 * mad_val}")

        # Manual calculation
        ratio_e02 = e02_data['Ratio_lptA'].values[0]
        manual_z = (ratio_e02 - median_val) / (1.4826 * mad_val)
        print(f"\n=== MANUAL Z-SCORE CALCULATION ===")
        print(f"Z = ({ratio_e02} - {median_val}) / ({1.4826} × {mad_val})")
        print(f"Z = {ratio_e02 - median_val} / {1.4826 * mad_val}")
        print(f"Z = {manual_z}")

        # Show distribution around E02
        print("\n=== RATIO DISTRIBUTION (sorted, showing position of E02) ===")
        sorted_ratios = sorted(ratio_values)
        e02_ratio = ratio_e02

        # Find position of E02 in sorted list
        position = sum(1 for r in sorted_ratios if r < e02_ratio)

        # Show values around E02
        start = max(0, position - 5)
        end = min(len(sorted_ratios), position + 6)

        for i, val in enumerate(sorted_ratios[start:end], start=start):
            marker = " <-- E02" if abs(val - e02_ratio) < 0.001 else ""
            print(f"{i+1:3d}. {val:.6f}{marker}")

        print(f"\nE02 Ratio position: {position+1}/{len(sorted_ratios)}")

        # Compare with Excel expected values
        print("\n=== COMPARISON WITH EXCEL ===")
        excel_z_lpta = 1.3060  # Your Excel value
        excel_z_ldtd = 0.2115  # Your Excel value
        print(f"Platform Z_lptA: {e02_data['Z_lptA'].values[0]:.4f}")
        print(f"Excel Z_lptA:    {excel_z_lpta:.4f}")
        print(f"Difference:      {e02_data['Z_lptA'].values[0] - excel_z_lpta:.4f}")

        # Check if Excel might be using different median/MAD
        print("\n=== POSSIBLE EXCEL CALCULATION ===")
        # Work backwards from Excel Z-score to find what median/MAD Excel used
        excel_denominator = (ratio_e02 - median_val) / excel_z_lpta if excel_z_lpta != 0 else 0
        excel_mad = excel_denominator / 1.4826 if excel_denominator != 0 else 0
        print(f"If Excel median = {median_val:.6f}, then Excel MAD = {excel_mad:.6f}")
        print(f"Platform MAD = {mad_val:.6f}")

        # Or different median
        excel_median = ratio_e02 - (excel_z_lpta * 1.4826 * mad_val)
        print(f"If Excel MAD = {mad_val:.6f}, then Excel median = {excel_median:.6f}")
        print(f"Platform median = {median_val:.6f}")

except FileNotFoundError:
    print(f"File not found: {file_path}")
    print("\nPlease update the file_path variable in this script to point to your actual data file.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
