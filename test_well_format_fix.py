"""Quick test to verify the well format fix works with both data formats."""

import pandas as pd
import numpy as np
from core.plate_processor import PlateProcessor
from core.well_position_utils import standardize_well_position_columns, detect_well_position_format

# Create test data in Row/Col format (like user's data)
def create_row_col_test_data():
    """Create test data with Row/Col columns (like user's format)."""
    np.random.seed(42)  # For reproducible results
    
    rows = ['A', 'B', 'C', 'D'] * 6  # 24 wells
    cols = [1, 2, 3, 4, 5, 6] * 4
    
    data = {
        'Row': rows,
        'Col': cols,
        'BG_lptA': np.random.randint(30000000, 60000000, 24),
        'BT_lptA': np.random.randint(8000, 25000, 24),
        'BG_ldtD': np.random.randint(30000000, 60000000, 24),
        'BT_ldtD': np.random.randint(8000, 25000, 24),
        'OD_WT': np.random.uniform(0.8, 1.5, 24),
        'OD_tolC': np.random.uniform(0.4, 1.3, 24),
        'OD_SA': np.random.uniform(0.05, 1.2, 24)
    }
    
    return pd.DataFrame(data)

# Create test data with Well column (existing format)
def create_well_test_data():
    """Create test data with Well column (existing format)."""
    np.random.seed(42)
    
    rows = ['A', 'B', 'C', 'D']
    cols = [1, 2, 3, 4, 5, 6]
    wells = []
    
    for row in rows:
        for col in cols:
            wells.append(f"{row}{col:02d}")
    
    data = {
        'Well': wells,
        'BG_lptA': np.random.randint(30000000, 60000000, 24),
        'BT_lptA': np.random.randint(8000, 25000, 24),
        'BG_ldtD': np.random.randint(30000000, 60000000, 24),
        'BT_ldtD': np.random.randint(8000, 25000, 24),
        'OD_WT': np.random.uniform(0.8, 1.5, 24),
        'OD_tolC': np.random.uniform(0.4, 1.3, 24),
        'OD_SA': np.random.uniform(0.05, 1.2, 24)
    }
    
    return pd.DataFrame(data)

def test_well_position_utilities():
    """Test the well position utilities directly."""
    print("=== Testing Well Position Utilities ===\n")
    
    # Test with Row/Col format
    print("1. Testing Row/Col format detection and conversion:")
    row_col_data = create_row_col_test_data()
    print(f"   - Original format: {detect_well_position_format(row_col_data)}")
    print(f"   - Original columns: {list(row_col_data.columns)}")
    
    standardized_data = standardize_well_position_columns(row_col_data, "TestPlate001")
    print(f"   - After standardization: {detect_well_position_format(standardized_data)}")
    print(f"   - New columns: {list(standardized_data.columns)}")
    print(f"   - Sample wells: {standardized_data['Well'].head().tolist()}")
    print()
    
    # Test with Well format
    print("2. Testing Well format detection and conversion:")
    well_data = create_well_test_data()
    print(f"   - Original format: {detect_well_position_format(well_data)}")
    print(f"   - Original columns: {list(well_data.columns)}")
    
    standardized_data = standardize_well_position_columns(well_data, "TestPlate002") 
    print(f"   - After standardization: {detect_well_position_format(standardized_data)}")
    print(f"   - New columns: {list(standardized_data.columns)}")
    print(f"   - Sample wells: {standardized_data['Well'].head().tolist()}")
    print()

def test_plate_processor_integration():
    """Test the full plate processor integration."""
    print("=== Testing Plate Processor Integration ===\n")
    
    processor = PlateProcessor()
    
    # Test with Row/Col format
    print("1. Processing Row/Col format data:")
    row_col_data = create_row_col_test_data()
    print(f"   - Input shape: {row_col_data.shape}")
    print(f"   - Input columns: {list(row_col_data.columns)}")
    
    try:
        processed_data = processor.process_single_plate(row_col_data, "RowColPlate")
        print(f"   - SUCCESS: Processing successful!")
        print(f"   - Output shape: {processed_data.shape}")
        print(f"   - Output columns: {list(processed_data.columns)}")
        print(f"   - Has Well column: {'Well' in processed_data.columns}")
        print(f"   - Has PlateID column: {'PlateID' in processed_data.columns}")
        print(f"   - Sample processed wells: {processed_data[['Well', 'Row', 'Col', 'Ratio_lptA', 'Z_lptA']].head()}")
    except Exception as e:
        print(f"   - ERROR: Processing failed: {e}")
    print()
    
    # Test with Well format
    print("2. Processing Well format data:")
    well_data = create_well_test_data()
    print(f"   - Input shape: {well_data.shape}")
    print(f"   - Input columns: {list(well_data.columns)}")
    
    try:
        processed_data = processor.process_single_plate(well_data, "WellPlate")
        print(f"   - SUCCESS: Processing successful!")
        print(f"   - Output shape: {processed_data.shape}")
        print(f"   - Output columns: {list(processed_data.columns)}")
        print(f"   - Has Well column: {'Well' in processed_data.columns}")
        print(f"   - Has PlateID column: {'PlateID' in processed_data.columns}")
        print(f"   - Sample processed wells: {processed_data[['Well', 'Row', 'Col', 'Ratio_lptA', 'Z_lptA']].head()}")
    except Exception as e:
        print(f"   - ERROR: Processing failed: {e}")
    print()

if __name__ == "__main__":
    print("Testing Well Format Fix Implementation\n")
    print("="*50)
    
    test_well_position_utilities()
    test_plate_processor_integration()
    
    print("="*50)
    print("SUCCESS: Test completed! The fix should now support both data formats.")
    print("\nTo test with your data:")
    print("1. Save your data as a CSV file")
    print("2. Run the Streamlit app: python -m streamlit run app.py")
    print("3. Upload your CSV file using the sidebar")
    print("4. The app should now process your Row/Col format correctly!")