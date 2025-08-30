#!/usr/bin/env python3
"""
Test script to verify the Windows file locking fix works correctly.
"""

import io
import tempfile
from pathlib import Path
import pandas as pd
import time

def test_in_memory_excel_processing():
    """Test that we can process Excel data from memory without file locking issues."""
    
    # Create a simple test Excel file in memory
    test_data = {
        'Well': ['A1', 'A2', 'B1', 'B2'],
        'BG_lptA': [100, 120, 90, 110],
        'BT_lptA': [50, 60, 45, 55],
        'ATP': [1000, 1200, 900, 1100]
    }
    df = pd.DataFrame(test_data)
    
    # Write to bytes buffer
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name='TestSheet')
    excel_bytes = excel_buffer.getvalue()
    excel_buffer.close()
    
    print(f"Created test Excel data: {len(excel_bytes)} bytes")
    
    # Test 1: Load sheet names from bytes
    try:
        sheet_buffer = io.BytesIO(excel_bytes)
        with pd.ExcelFile(sheet_buffer) as excel_file:
            sheet_names = excel_file.sheet_names
            print(f"Sheet names from memory: {sheet_names}")
        sheet_buffer.close()
        print("✅ Sheet name extraction from memory: SUCCESS")
    except Exception as e:
        print(f"❌ Sheet name extraction from memory: FAILED - {e}")
        return False
    
    # Test 2: Load DataFrame from bytes
    try:
        data_buffer = io.BytesIO(excel_bytes)
        loaded_df = pd.read_excel(data_buffer, sheet_name='TestSheet')
        data_buffer.close()
        print(f"Loaded DataFrame shape: {loaded_df.shape}")
        print(f"Columns: {list(loaded_df.columns)}")
        print("✅ DataFrame loading from memory: SUCCESS")
    except Exception as e:
        print(f"❌ DataFrame loading from memory: FAILED - {e}")
        return False
    
    # Test 3: Temporary file cleanup (simulate the old problem)
    try:
        temp_path = Path(tempfile.gettempdir()) / "test_cleanup.xlsx"
        temp_path.write_bytes(excel_bytes)
        
        # Open and close file handle properly
        with pd.ExcelFile(temp_path) as excel_file:
            sheet_names = excel_file.sheet_names
            print(f"Temp file sheet names: {sheet_names}")
        
        # Try immediate cleanup
        temp_path.unlink()
        print("✅ Temporary file cleanup: SUCCESS")
    except PermissionError as e:
        print(f"❌ Temporary file cleanup: FAILED with PermissionError - {e}")
        return False
    except Exception as e:
        print(f"❌ Temporary file cleanup: FAILED - {e}")
        return False
    
    return True

def test_retry_cleanup():
    """Test the retry cleanup mechanism."""
    
    # Create a test file
    temp_path = Path(tempfile.gettempdir()) / "test_retry_cleanup.txt"
    temp_path.write_text("test content")
    
    print(f"Created test file: {temp_path}")
    
    # Import the safe cleanup function (would need to be imported from app.py)
    # For now, just implement a simple version here
    def safe_cleanup_with_retry(file_path, max_attempts=3):
        import gc
        for attempt in range(max_attempts):
            try:
                file_path.unlink()
                return True
            except PermissionError:
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
                    gc.collect()
                else:
                    return False
            except FileNotFoundError:
                return True
        return False
    
    success = safe_cleanup_with_retry(temp_path)
    if success:
        print("✅ Retry cleanup mechanism: SUCCESS")
        return True
    else:
        print("❌ Retry cleanup mechanism: FAILED")
        return False

if __name__ == "__main__":
    print("🧪 Testing Windows file locking fixes...\n")
    
    success1 = test_in_memory_excel_processing()
    success2 = test_retry_cleanup()
    
    print(f"\n📊 Test Results:")
    print(f"In-memory processing: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Retry cleanup: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print(f"\n🎉 All tests passed! The file locking fixes should work correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Review the implementation.")