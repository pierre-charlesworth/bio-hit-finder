#!/usr/bin/env python3
"""
Quick test script to process the real data file and see the improved funnel visualization.
"""

import pandas as pd
import sys
import os
sys.path.append(os.getcwd())

from core.plate_processor import PlateProcessor
from analytics.hit_calling import analyze_multi_plate_hits

def main():
    print("Testing real data processing...")
    
    # Load the real data file
    file_path = "RAW DATA (Naicons).xlsx"
    print(f"Loading {file_path}...")
    
    try:
        df = pd.read_excel(file_path)
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        print("Columns:", list(df.columns))
        
        # Process with multi-stage hit calling enabled
        processor = PlateProcessor()
        hit_calling_config = {
            'hit_calling': {
                'multi_stage_enabled': True
            },
            'lptA_threshold': 2.0,
            'ldtD_threshold': 2.0,
            'tolC_max': 0.8,
            'WT_min': 0.8,
            'SA_min': 0.8
        }
        
        print("Processing data...")
        processed_df = processor.process_dual_readout_plate(df, "RAW DATA (Naicons)", hit_calling_config)
        
        if processed_df is not None and len(processed_df) > 0:
            print(f"Processing successful! {len(processed_df)} rows processed")
            
            # Check for hit columns
            hit_cols = ['reporter_hit', 'vitality_hit', 'platform_hit']
            for col in hit_cols:
                if col in processed_df.columns:
                    hit_count = processed_df[col].sum()
                    print(f"{col}: {hit_count} hits")
                else:
                    print(f"Missing column: {col}")
            
            # Test hit calling analysis
            print("\nTesting hit calling analysis...")
            plate_data = {'RAW DATA (Naicons)': processed_df}
            hit_results = analyze_multi_plate_hits(plate_data, hit_calling_config)
            
            if 'cross_plate_summary' in hit_results:
                summary = hit_results['cross_plate_summary']
                print("Hit calling results:")
                print(f"  Total wells: {summary.get('total_wells', 'N/A')}")
                print(f"  Reporter hits: {summary.get('total_reporter_hits', 'N/A')}")
                print(f"  Vitality hits: {summary.get('total_vitality_hits', 'N/A')}")
                print(f"  Platform hits: {summary.get('total_platform_hits', 'N/A')}")
            else:
                print("No cross_plate_summary found")
                print("Available keys:", list(hit_results.keys()))
        else:
            print("Processing failed!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()