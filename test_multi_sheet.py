#!/usr/bin/env python3
"""
Test script for multi-sheet processing functionality.
"""

import pandas as pd
import sys
import os
sys.path.append(os.getcwd())

from app import process_all_sheets_from_files

def main():
    print("Testing multi-sheet processing...")
    
    # Load the Naicons file
    file_path = "RAW DATA (Naicons).xlsx"
    print(f"Loading {file_path}...")
    
    # Read file as bytes (simulating Streamlit file upload)
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    files_data = {file_path: file_data}
    
    # Test parameters
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
    
    try:
        print("Processing all sheets...")
        sheet_results = process_all_sheets_from_files(
            files_data=files_data,
            viability_threshold=0.3,
            apply_bscore=False,
            hit_calling_enabled=True,
            hit_calling_config=hit_calling_config,
            column_mapping=None
        )
        
        print(f"\nProcessing complete! Found {len(sheet_results)} sheets:")
        
        successful_sheets = 0
        failed_sheets = 0
        
        for sheet_key, data in sheet_results.items():
            metadata = data['metadata']
            if data['error']:
                print(f"❌ {sheet_key}: ERROR - {data['error_message']}")
                failed_sheets += 1
            else:
                wells = metadata['total_wells']
                print(f"✅ {sheet_key}: {wells} wells processed")
                successful_sheets += 1
                
                # Show hit calling results if available
                if data['hit_calling_results'] and 'cross_plate_summary' in data['hit_calling_results']:
                    summary = data['hit_calling_results']['cross_plate_summary']
                    reporter_hits = summary.get('total_reporter_hits', 0)
                    vitality_hits = summary.get('total_vitality_hits', 0)
                    platform_hits = summary.get('total_platform_hits', 0)
                    print(f"   📊 Hits: {reporter_hits} reporter, {vitality_hits} vitality, {platform_hits} platform")
        
        print(f"\nSummary: {successful_sheets} successful, {failed_sheets} failed")
        
        if successful_sheets > 0:
            print(f"\nMulti-sheet processing successful! ✅")
            
            # Test accessing a specific sheet
            first_success = next(key for key, data in sheet_results.items() if not data['error'])
            test_data = sheet_results[first_success]
            print(f"Sample data access - {first_success}: {len(test_data['processed_data'])} rows")
        else:
            print("No sheets processed successfully ❌")
            
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()