"""Tests for core.plate_processor module.

Tests the PlateProcessor class and related functions for data ingestion,
column mapping, validation, and processing workflow.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.plate_processor import (
    ColumnMappingError,
    PlateProcessor,
    PlateProcessingError,
    get_available_excel_sheets,
    process_plate_file,
)


class TestPlateProcessor:
    """Test the PlateProcessor class."""
    
    def test_initialization(self):
        """Test PlateProcessor initialization."""
        processor = PlateProcessor(viability_threshold=0.4)
        
        assert processor.viability_threshold == 0.4
        assert processor.column_mapping == {}
        assert processor.processed_plates == {}
    
    def test_auto_detect_columns_exact_match(self):
        """Test column auto-detection with exact matches."""
        df = pd.DataFrame({
            'BG_lptA': [1], 'BT_lptA': [1], 'BG_ldtD': [1], 'BT_ldtD': [1],
            'OD_WT': [1], 'OD_tolC': [1], 'OD_SA': [1],
        })
        
        processor = PlateProcessor()
        mapping = processor.auto_detect_columns(df)
        
        # Should map all columns directly
        expected = {
            'BG_lptA': 'BG_lptA', 'BT_lptA': 'BT_lptA',
            'BG_ldtD': 'BG_ldtD', 'BT_ldtD': 'BT_ldtD', 
            'OD_WT': 'OD_WT', 'OD_tolC': 'OD_tolC', 'OD_SA': 'OD_SA',
        }
        assert mapping == expected
    
    def test_auto_detect_columns_aliases(self):
        """Test column auto-detection with alias matching."""
        df = pd.DataFrame({
            'BetaGlo_lptA': [1], 'BacTiter_lptA': [1],
            'betaglo_ldtD': [1], 'bactiter_ldtD': [1],
            'OD_wt': [1], 'od_tolC': [1], 'OD_sa': [1],
        })
        
        processor = PlateProcessor()
        mapping = processor.auto_detect_columns(df)
        
        # Should map aliases to standard names
        expected = {
            'BG_lptA': 'BetaGlo_lptA', 'BT_lptA': 'BacTiter_lptA',
            'BG_ldtD': 'betaglo_ldtD', 'BT_ldtD': 'bactiter_ldtD',
            'OD_WT': 'OD_wt', 'OD_tolC': 'od_tolC', 'OD_SA': 'OD_sa',
        }
        assert mapping == expected
    
    def test_auto_detect_columns_missing(self):
        """Test error when columns cannot be detected."""
        df = pd.DataFrame({
            'Unknown_A': [1], 'Unknown_B': [1], 'Unknown_C': [1],
        })
        
        processor = PlateProcessor()
        
        with pytest.raises(ColumnMappingError, match="Could not auto-detect columns"):
            processor.auto_detect_columns(df)
    
    def test_set_column_mapping(self):
        """Test manual column mapping."""
        processor = PlateProcessor()
        
        mapping = {
            'BG_lptA': 'Custom_BG_lptA', 'BT_lptA': 'Custom_BT_lptA',
            'BG_ldtD': 'Custom_BG_ldtD', 'BT_ldtD': 'Custom_BT_ldtD',
            'OD_WT': 'Custom_OD_WT', 'OD_tolC': 'Custom_OD_tolC', 'OD_SA': 'Custom_OD_SA',
        }
        
        processor.set_column_mapping(mapping)
        assert processor.column_mapping == mapping
    
    def test_set_column_mapping_incomplete(self):
        """Test error with incomplete column mapping."""
        processor = PlateProcessor()
        
        mapping = {
            'BG_lptA': 'Custom_BG_lptA',
            # Missing other required columns
        }
        
        with pytest.raises(ColumnMappingError, match="Missing mappings for columns"):
            processor.set_column_mapping(mapping)
    
    def test_apply_column_mapping(self):
        """Test applying column mapping to DataFrame."""
        df = pd.DataFrame({
            'Custom_BG_lptA': [1], 'Custom_BT_lptA': [1],
            'Custom_BG_ldtD': [1], 'Custom_BT_ldtD': [1],
            'Custom_OD_WT': [1], 'Custom_OD_tolC': [1], 'Custom_OD_SA': [1],
            'Other_Column': ['keep'],
        })
        
        processor = PlateProcessor()
        processor.set_column_mapping({
            'BG_lptA': 'Custom_BG_lptA', 'BT_lptA': 'Custom_BT_lptA',
            'BG_ldtD': 'Custom_BG_ldtD', 'BT_ldtD': 'Custom_BT_ldtD',
            'OD_WT': 'Custom_OD_WT', 'OD_tolC': 'Custom_OD_tolC', 'OD_SA': 'Custom_OD_SA',
        })
        
        result = processor.apply_column_mapping(df)
        
        # Check that columns are renamed
        assert 'BG_lptA' in result.columns
        assert 'BT_lptA' in result.columns
        assert 'Custom_BG_lptA' not in result.columns
        
        # Check that other columns are preserved
        assert 'Other_Column' in result.columns
        assert result['Other_Column'].iloc[0] == 'keep'
    
    def test_apply_column_mapping_missing_column(self):
        """Test error when mapped column doesn't exist."""
        df = pd.DataFrame({
            'Existing_Column': [1],
        })
        
        processor = PlateProcessor()
        processor.set_column_mapping({
            'BG_lptA': 'Missing_Column', 'BT_lptA': 'Custom_BT_lptA',
            'BG_ldtD': 'Custom_BG_ldtD', 'BT_ldtD': 'Custom_BT_ldtD',
            'OD_WT': 'Custom_OD_WT', 'OD_tolC': 'Custom_OD_tolC', 'OD_SA': 'Custom_OD_SA',
        })
        
        with pytest.raises(ColumnMappingError, match="Mapped columns not found"):
            processor.apply_column_mapping(df)
    
    def test_validate_plate_data_valid(self):
        """Test validation with valid data."""
        df = pd.DataFrame({
            'BG_lptA': [1.0, 2.0], 'BT_lptA': [1.0, 2.0],
            'BG_ldtD': [1.0, 2.0], 'BT_ldtD': [1.0, 2.0],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [1.0, 2.0], 'OD_SA': [1.0, 2.0],
        })
        
        processor = PlateProcessor()
        result = processor.validate_plate_data(df)
        assert result == True
    
    def test_validate_plate_data_empty(self):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame({
            'BG_lptA': [], 'BT_lptA': [], 'BG_ldtD': [], 'BT_ldtD': [],
            'OD_WT': [], 'OD_tolC': [], 'OD_SA': [],
        })
        
        processor = PlateProcessor()
        
        with pytest.raises(PlateProcessingError, match="DataFrame is empty"):
            processor.validate_plate_data(df)
    
    def test_validate_plate_data_non_numeric(self):
        """Test validation with non-numeric data."""
        df = pd.DataFrame({
            'BG_lptA': ['text', 'data'], 'BT_lptA': [1.0, 2.0],
            'BG_ldtD': [1.0, 2.0], 'BT_ldtD': [1.0, 2.0],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [1.0, 2.0], 'OD_SA': [1.0, 2.0],
        })
        
        processor = PlateProcessor()
        
        with pytest.raises(PlateProcessingError, match="Non-numeric data in columns"):
            processor.validate_plate_data(df)
    
    def test_process_single_plate(self):
        """Test processing a single plate."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200], 'BT_lptA': [50, 100],
            'BG_ldtD': [150, 300], 'BT_ldtD': [75, 150],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [0.8, 1.6], 'OD_SA': [1.2, 2.4],
        })
        
        processor = PlateProcessor()
        result = processor.process_single_plate(df, 'TestPlate')
        
        # Check that PlateID is added
        assert 'PlateID' in result.columns
        assert (result['PlateID'] == 'TestPlate').all()
        
        # Check that calculations were applied
        assert 'Ratio_lptA' in result.columns
        assert 'Z_lptA' in result.columns
        assert 'viability_ok_lptA' in result.columns
        
        # Check that plate is stored
        assert 'TestPlate' in processor.processed_plates
    
    def test_get_processing_summary(self):
        """Test getting processing summary."""
        df = pd.DataFrame({
            'BG_lptA': [100, 200], 'BT_lptA': [50, 100],
            'BG_ldtD': [150, 300], 'BT_ldtD': [75, 150],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [0.8, 1.6], 'OD_SA': [1.2, 2.4],
        })
        
        processor = PlateProcessor(viability_threshold=0.3)
        processor.process_single_plate(df, 'TestPlate')
        
        summary = processor.get_processing_summary()
        
        assert summary['plate_count'] == 1
        assert summary['total_wells'] == 2
        assert summary['viability_threshold'] == 0.3
        assert 'TestPlate' in summary['plate_summaries']
    
    def test_reset(self):
        """Test resetting processor state."""
        df = pd.DataFrame({
            'BG_lptA': [100], 'BT_lptA': [50], 'BG_ldtD': [150], 'BT_ldtD': [75],
            'OD_WT': [1.0], 'OD_tolC': [0.8], 'OD_SA': [1.2],
        })
        
        processor = PlateProcessor()
        processor.set_column_mapping({
            'BG_lptA': 'BG_lptA', 'BT_lptA': 'BT_lptA',
            'BG_ldtD': 'BG_ldtD', 'BT_ldtD': 'BT_ldtD',
            'OD_WT': 'OD_WT', 'OD_tolC': 'OD_tolC', 'OD_SA': 'OD_SA',
        })
        processor.process_single_plate(df, 'TestPlate')
        
        # Check state before reset
        assert len(processor.column_mapping) > 0
        assert len(processor.processed_plates) > 0
        
        # Reset and check state
        processor.reset()
        assert len(processor.column_mapping) == 0
        assert len(processor.processed_plates) == 0


class TestFileIOFunctions:
    """Test file I/O related functions."""
    
    def test_load_csv_file(self):
        """Test loading CSV file."""
        # Create temporary CSV file
        data = {
            'BG_lptA': [100, 200], 'BT_lptA': [50, 100],
            'BG_ldtD': [150, 300], 'BT_ldtD': [75, 150],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [0.8, 1.6], 'OD_SA': [1.2, 2.4],
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            processor = PlateProcessor()
            result = processor.load_plate_data(temp_path)
            
            assert len(result) == 2
            assert 'BG_lptA' in result.columns
            assert result['BG_lptA'].iloc[0] == 100
        finally:
            Path(temp_path).unlink()  # Clean up
    
    def test_load_excel_file(self):
        """Test loading Excel file."""
        # Create temporary Excel file
        data = {
            'BG_lptA': [100, 200], 'BT_lptA': [50, 100],
            'BG_ldtD': [150, 300], 'BT_ldtD': [75, 150],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [0.8, 1.6], 'OD_SA': [1.2, 2.4],
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False, sheet_name='Data')
            temp_path = f.name
        
        try:
            processor = PlateProcessor()
            result = processor.load_plate_data(temp_path, sheet_name='Data')
            
            assert len(result) == 2
            assert 'BG_lptA' in result.columns
        finally:
            Path(temp_path).unlink()  # Clean up
    
    def test_load_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        processor = PlateProcessor()
        
        with pytest.raises(PlateProcessingError, match="File not found"):
            processor.load_plate_data('nonexistent_file.csv')
    
    def test_load_unsupported_format(self):
        """Test error handling for unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'some text data')
            temp_path = f.name
        
        try:
            processor = PlateProcessor()
            
            with pytest.raises(PlateProcessingError, match="Unsupported file format"):
                processor.load_plate_data(temp_path)
        finally:
            Path(temp_path).unlink()  # Clean up


class TestProcessPlateFile:
    """Test the convenience function process_plate_file."""
    
    def test_process_csv_file(self):
        """Test processing a complete CSV file."""
        # Create temporary CSV file with complete data
        data = {
            'BG_lptA': [100, 200, 300], 'BT_lptA': [50, 100, 150],
            'BG_ldtD': [150, 300, 450], 'BT_ldtD': [75, 150, 225],
            'OD_WT': [1.0, 2.0, 3.0], 'OD_tolC': [0.8, 1.6, 2.4], 'OD_SA': [1.2, 2.4, 3.6],
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            result = process_plate_file(temp_path, plate_id='Test001')
            
            # Check that full processing was completed
            assert 'PlateID' in result.columns
            assert (result['PlateID'] == 'Test001').all()
            assert 'Ratio_lptA' in result.columns
            assert 'Z_lptA' in result.columns
            assert 'viability_ok_lptA' in result.columns
            assert len(result) == 3
            
        finally:
            Path(temp_path).unlink()  # Clean up
    
    def test_process_file_with_aliases(self):
        """Test processing file with column aliases."""
        # Create CSV with alias column names
        data = {
            'BetaGlo_lptA': [100, 200], 'BacTiter_lptA': [50, 100],
            'betaglo_ldtD': [150, 300], 'bactiter_ldtD': [75, 150],
            'OD_wt': [1.0, 2.0], 'od_tolC': [0.8, 1.6], 'OD_sa': [1.2, 2.4],
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            result = process_plate_file(temp_path)
            
            # Should auto-detect aliases and process successfully
            assert 'Ratio_lptA' in result.columns
            assert len(result) == 2
            
        finally:
            Path(temp_path).unlink()  # Clean up
    
    def test_process_file_with_custom_mapping(self):
        """Test processing file with custom column mapping."""
        # Create CSV with non-standard column names
        data = {
            'Custom_BG_lptA': [100, 200], 'Custom_BT_lptA': [50, 100],
            'Custom_BG_ldtD': [150, 300], 'Custom_BT_ldtD': [75, 150],
            'Custom_OD_WT': [1.0, 2.0], 'Custom_OD_tolC': [0.8, 1.6], 'Custom_OD_SA': [1.2, 2.4],
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            mapping = {
                'BG_lptA': 'Custom_BG_lptA', 'BT_lptA': 'Custom_BT_lptA',
                'BG_ldtD': 'Custom_BG_ldtD', 'BT_ldtD': 'Custom_BT_ldtD',
                'OD_WT': 'Custom_OD_WT', 'OD_tolC': 'Custom_OD_tolC', 'OD_SA': 'Custom_OD_SA',
            }
            
            result = process_plate_file(temp_path, column_mapping=mapping)
            
            assert 'Ratio_lptA' in result.columns
            assert len(result) == 2
            
        finally:
            Path(temp_path).unlink()  # Clean up


class TestExcelSheetFunctions:
    """Test Excel sheet handling functions."""
    
    def test_get_available_excel_sheets(self):
        """Test getting available sheet names from Excel file."""
        # Create temporary Excel file with multiple sheets
        data1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        data2 = pd.DataFrame({'C': [5, 6], 'D': [7, 8]})
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
            
        # Write the Excel file separately to ensure it's properly closed
        with pd.ExcelWriter(temp_path) as writer:
            data1.to_excel(writer, sheet_name='Sheet1', index=False)
            data2.to_excel(writer, sheet_name='Sheet2', index=False)
        
        try:
            sheets = get_available_excel_sheets(temp_path)
            
            assert isinstance(sheets, list)
            assert 'Sheet1' in sheets
            assert 'Sheet2' in sheets
            
        finally:
            # Robust cleanup for Windows file locking
            import time
            for attempt in range(3):
                try:
                    Path(temp_path).unlink()
                    break
                except PermissionError:
                    if attempt < 2:
                        time.sleep(0.1)
                    else:
                        # Last resort: just pass if we can't clean up
                        pass
    
    def test_get_sheets_non_excel_file(self):
        """Test error when trying to get sheets from non-Excel file."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            f.write(b'col1,col2\n1,2\n')
            temp_path = f.name
        
        try:
            with pytest.raises(PlateProcessingError, match="File is not Excel format"):
                get_available_excel_sheets(temp_path)
        finally:
            Path(temp_path).unlink()  # Clean up


class TestIntegrationWorkflow:
    """Test complete integration workflows."""
    
    def test_multi_plate_processing_workflow(self):
        """Test processing multiple plates through complete workflow."""
        # Create two temporary CSV files
        data1 = {
            'BG_lptA': [100, 200], 'BT_lptA': [50, 100],
            'BG_ldtD': [150, 300], 'BT_ldtD': [75, 150],
            'OD_WT': [1.0, 2.0], 'OD_tolC': [0.8, 1.6], 'OD_SA': [1.2, 2.4],
        }
        data2 = {
            'BG_lptA': [120, 240], 'BT_lptA': [60, 120],
            'BG_ldtD': [180, 360], 'BT_ldtD': [90, 180],
            'OD_WT': [1.1, 2.2], 'OD_tolC': [0.9, 1.8], 'OD_SA': [1.3, 2.6],
        }
        
        temp_files = {}
        
        try:
            # Create temporary files
            for i, data in enumerate([data1, data2], 1):
                df = pd.DataFrame(data)
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    df.to_csv(f.name, index=False)
                    temp_files[f'Plate{i:03d}'] = f.name
            
            # Process multiple plates
            processor = PlateProcessor(viability_threshold=0.25)
            combined_result = processor.process_multiple_plates(temp_files)
            
            # Check combined results
            assert 'PlateID' in combined_result.columns
            assert len(combined_result) == 4  # 2 wells per plate × 2 plates
            assert 'Plate001' in combined_result['PlateID'].values
            assert 'Plate002' in combined_result['PlateID'].values
            
            # Check that all calculations are present
            assert 'Ratio_lptA' in combined_result.columns
            assert 'Z_lptA' in combined_result.columns
            assert 'viability_ok_lptA' in combined_result.columns
            
            # Check processing summary
            summary = processor.get_processing_summary()
            assert summary['plate_count'] == 2
            assert summary['total_wells'] == 4
            
        finally:
            # Clean up temporary files
            for temp_path in temp_files.values():
                Path(temp_path).unlink()