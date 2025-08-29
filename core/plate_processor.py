"""Plate data processing and ingestion module.

This module provides the PlateProcessor class for loading, validating, and processing
plate data files. It handles Excel/CSV file loading, column detection and mapping,
data validation, and applies the complete calculation pipeline.

The processor supports both single plate and multi-plate workflows as specified
in the PRD document.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

from .calculations import (
    calculate_plate_summary,
    process_plate_calculations,
    validate_plate_columns,
    process_multi_stage_hit_calling,
)
from .well_position_utils import standardize_well_position_columns, WellPositionError

logger = logging.getLogger(__name__)

# Type aliases
PathLike = Union[str, Path]
DataFrameLike = pd.DataFrame


class PlateProcessingError(Exception):
    """Custom exception for plate processing errors."""
    pass


class ColumnMappingError(PlateProcessingError):
    """Exception raised when column mapping fails."""
    pass


class PlateProcessor:
    """Processes plate data files and applies calculation pipeline.
    
    This class handles the complete workflow from raw data files to processed
    plate metrics, including:
    - File loading (Excel/CSV)
    - Column detection and mapping
    - Data validation
    - Calculation pipeline application
    - Multi-plate aggregation
    
    Attributes:
        required_columns: Standard column names required for processing
        column_mapping: Current mapping from file columns to standard names
        processed_plates: Dictionary of processed plate DataFrames
    """
    
    # Standard required columns as per PRD specification
    REQUIRED_COLUMNS = [
        'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD',
        'OD_WT', 'OD_tolC', 'OD_SA'
    ]
    
    # Common alternative column names for auto-detection
    COLUMN_ALIASES = {
        'BG_lptA': ['BG_lptA', 'BetaGlo_lptA', 'betaglo_lptA', 'bg_lptA'],
        'BT_lptA': ['BT_lptA', 'BacTiter_lptA', 'bactiter_lptA', 'bt_lptA'],
        'BG_ldtD': ['BG_ldtD', 'BetaGlo_ldtD', 'betaglo_ldtD', 'bg_ldtD'],
        'BT_ldtD': ['BT_ldtD', 'BacTiter_ldtD', 'bactiter_ldtD', 'bt_ldtD'],
        'OD_WT': ['OD_WT', 'OD_wt', 'od_WT', 'od_wt', 'OD_wildtype'],
        'OD_tolC': ['OD_tolC', 'OD_tolc', 'od_tolC', 'od_tolc'],
        'OD_SA': ['OD_SA', 'OD_sa', 'od_SA', 'od_sa'],
    }
    
    def __init__(self, viability_threshold: float = 0.3):
        """Initialize PlateProcessor.
        
        Args:
            viability_threshold: Threshold for viability gating (default 0.3)
        """
        self.viability_threshold = viability_threshold
        self.column_mapping: dict[str, str] = {}
        self.processed_plates: dict[str, pd.DataFrame] = {}
        
        logger.info(f"Initialized PlateProcessor with viability_threshold={viability_threshold}")
    
    def load_plate_data(self, 
                       file_path: PathLike, 
                       sheet_name: Optional[str] = None,
                       **kwargs) -> pd.DataFrame:
        """Load plate data from Excel or CSV file.
        
        Args:
            file_path: Path to the data file
            sheet_name: Excel sheet name (None for CSV or first sheet)
            **kwargs: Additional arguments passed to pandas read functions
            
        Returns:
            DataFrame with loaded plate data
            
        Raises:
            PlateProcessingError: If file cannot be loaded or is empty
            
        Examples:
            >>> processor = PlateProcessor()
            >>> df = processor.load_plate_data('plate1.xlsx', sheet_name='Data')
            >>> len(df) > 0
            True
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise PlateProcessingError(f"File not found: {file_path}")
        
        logger.info(f"Loading plate data from {file_path}")
        
        try:
            # Determine file type and load accordingly
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Excel file
                if sheet_name is None:
                    # Load first sheet
                    df = pd.read_excel(file_path, **kwargs)
                    logger.debug(f"Loaded first sheet from Excel file")
                else:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
                    logger.debug(f"Loaded sheet '{sheet_name}' from Excel file")
                    
            elif file_path.suffix.lower() == '.csv':
                # CSV file
                df = pd.read_csv(file_path, **kwargs)
                logger.debug(f"Loaded CSV file")
                
            else:
                raise PlateProcessingError(f"Unsupported file format: {file_path.suffix}")
            
            # Validate loaded data
            if df.empty:
                raise PlateProcessingError(f"Loaded file is empty: {file_path}")
            
            # Clean column names (remove leading/trailing whitespace)
            df.columns = df.columns.str.strip()
            
            logger.info(f"Successfully loaded {len(df)} rows, {len(df.columns)} columns")
            logger.debug(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            if isinstance(e, PlateProcessingError):
                raise
            raise PlateProcessingError(f"Failed to load {file_path}: {e}") from e
    
    def auto_detect_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """Automatically detect and map required columns.
        
        Args:
            df: DataFrame with raw column names
            
        Returns:
            Dictionary mapping standard names to detected column names
            
        Raises:
            ColumnMappingError: If required columns cannot be detected
            
        Examples:
            >>> df = pd.DataFrame({'BetaGlo_lptA': [1], 'BacTiter_lptA': [1]})
            >>> processor = PlateProcessor()
            >>> mapping = processor.auto_detect_columns(df)
            >>> mapping['BG_lptA']
            'BetaGlo_lptA'
        """
        logger.debug("Auto-detecting column mapping")
        
        available_columns = list(df.columns)
        detected_mapping = {}
        
        # Try to match each required column to available columns
        for std_name in self.REQUIRED_COLUMNS:
            possible_names = self.COLUMN_ALIASES.get(std_name, [std_name])
            
            # Look for exact matches first
            for possible_name in possible_names:
                if possible_name in available_columns:
                    detected_mapping[std_name] = possible_name
                    logger.debug(f"Mapped {std_name} -> {possible_name}")
                    break
            else:
                # Try case-insensitive matching
                for possible_name in possible_names:
                    for col in available_columns:
                        if col.lower() == possible_name.lower():
                            detected_mapping[std_name] = col
                            logger.debug(f"Mapped {std_name} -> {col} (case-insensitive)")
                            break
                    if std_name in detected_mapping:
                        break
        
        # Check if all required columns were detected
        missing_columns = set(self.REQUIRED_COLUMNS) - set(detected_mapping.keys())
        if missing_columns:
            raise ColumnMappingError(
                f"Could not auto-detect columns: {missing_columns}\n"
                f"Available columns: {available_columns}\n"
                f"Please provide manual column mapping"
            )
        
        logger.info(f"Auto-detected all required columns: {detected_mapping}")
        self.column_mapping = detected_mapping
        return detected_mapping
    
    def set_column_mapping(self, mapping: dict[str, str]) -> None:
        """Set manual column mapping.
        
        Args:
            mapping: Dictionary mapping standard column names to actual column names
            
        Raises:
            ColumnMappingError: If mapping is incomplete or invalid
        """
        # Validate that all required columns are mapped
        missing_columns = set(self.REQUIRED_COLUMNS) - set(mapping.keys())
        if missing_columns:
            raise ColumnMappingError(f"Missing mappings for columns: {missing_columns}")
        
        self.column_mapping = mapping.copy()
        logger.info(f"Set manual column mapping: {self.column_mapping}")
    
    def apply_column_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply column mapping to rename columns to standard names.
        
        Args:
            df: DataFrame with original column names
            
        Returns:
            DataFrame with renamed columns
            
        Raises:
            ColumnMappingError: If mapping columns don't exist in DataFrame
        """
        if not self.column_mapping:
            raise ColumnMappingError("No column mapping set. Call auto_detect_columns() first.")
        
        # Check that all mapped columns exist
        missing_columns = []
        for std_name, actual_name in self.column_mapping.items():
            if actual_name not in df.columns:
                missing_columns.append(actual_name)
        
        if missing_columns:
            raise ColumnMappingError(f"Mapped columns not found in DataFrame: {missing_columns}")
        
        # Create reverse mapping for renaming
        rename_mapping = {actual: std for std, actual in self.column_mapping.items()}
        
        # Apply mapping - only rename the mapped columns, keep others as-is
        mapped_df = df.rename(columns=rename_mapping)
        
        logger.debug(f"Applied column mapping: {len(rename_mapping)} columns renamed")
        return mapped_df
    
    def validate_plate_data(self, df: pd.DataFrame) -> bool:
        """Validate that DataFrame contains required columns and data.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if validation passes
            
        Raises:
            PlateProcessingError: If validation fails
        """
        logger.debug("Validating plate data")
        
        # Check for required columns
        try:
            validate_plate_columns(df, self.REQUIRED_COLUMNS)
        except ValueError as e:
            raise PlateProcessingError(f"Column validation failed: {e}") from e
        
        # Check for data presence
        if len(df) == 0:
            raise PlateProcessingError("DataFrame is empty")
        
        # Check for at least some valid data in each required column
        all_nan_columns = []
        for col in self.REQUIRED_COLUMNS:
            if df[col].isna().all():
                all_nan_columns.append(col)
        
        if all_nan_columns:
            logger.warning(f"Columns with all NaN values: {all_nan_columns}")
        
        # Check data types (should be numeric)
        non_numeric_columns = []
        for col in self.REQUIRED_COLUMNS:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    # Try to convert to numeric
                    pd.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    non_numeric_columns.append(col)
        
        if non_numeric_columns:
            raise PlateProcessingError(f"Non-numeric data in columns: {non_numeric_columns}")
        
        logger.info(f"Validation passed for {len(df)} rows")
        return True
    
    def _clean_precalculated_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove any pre-calculated columns that might conflict with our calculations.
        
        Args:
            df: Input DataFrame that may contain pre-calculated columns
            
        Returns:
            DataFrame with only raw data columns needed for processing
        """
        # List of columns that we calculate - remove them if they exist
        calculated_columns = [
            'Ratio_lptA', 'Ratio_ldtD',
            'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm', 
            'Z_lptA', 'Z_ldtD',
            'B_Z_lptA', 'B_Z_ldtD',
            'viability_ok_lptA', 'viability_fail_lptA',
            'viability_ok_ldtD', 'viability_fail_ldtD',
            'viable_lptA', 'viable_ldtD',  # Alternative names
            'PassViab_lptA', 'PassViab_ldtD',  # Your Excel file's names
            'Hit_lptA', 'Hit_ldtD',  # Hit calling columns
            'rawScore', 'Score', 'LumHit?', 'OMpatternOK?', 'PlatformHit?'  # Other analysis columns
        ]
        
        # Also remove percentage columns that might conflict
        percentage_columns = ['WT%', 'tolC%', 'SA%']
        calculated_columns.extend(percentage_columns)
        
        # Keep only the columns we need + well position columns
        columns_to_drop = [col for col in calculated_columns if col in df.columns]
        
        if columns_to_drop:
            logger.info(f"Removing {len(columns_to_drop)} pre-calculated columns: {columns_to_drop}")
            cleaned_df = df.drop(columns=columns_to_drop)
        else:
            cleaned_df = df.copy()
        
        # Filter out summary/statistics rows - keep only actual well data
        if 'Row' in cleaned_df.columns:
            # Keep only rows where Row matches standard well row format (A-Z letters)
            original_rows = len(cleaned_df)
            cleaned_df = cleaned_df[cleaned_df['Row'].str.match('^[A-Z]+$', na=False)]
            filtered_rows = original_rows - len(cleaned_df)
            
            if filtered_rows > 0:
                logger.info(f"Filtered out {filtered_rows} non-well rows (summary/statistics data)")
        
        # Remove any completely empty rows
        cleaned_df = cleaned_df.dropna(how='all')
            
        logger.debug(f"Cleaned DataFrame has {len(cleaned_df)} rows, {len(cleaned_df.columns)} columns")
        return cleaned_df
    
    def process_single_plate(self, 
                           df: pd.DataFrame, 
                           plate_id: str) -> pd.DataFrame:
        """Process a single plate through the complete calculation pipeline.
        
        Args:
            df: DataFrame with raw plate data (must have standard column names)
            plate_id: Identifier for this plate
            
        Returns:
            DataFrame with all calculated metrics
            
        Raises:
            PlateProcessingError: If processing fails
        """
        logger.info(f"Processing single plate: {plate_id}")
        
        try:
            # Clean input data - remove any pre-calculated columns to avoid conflicts
            cleaned_df = self._clean_precalculated_columns(df)
            
            # Validate input data
            self.validate_plate_data(cleaned_df)
            
            # Standardize well position columns (supports both Well and Row/Col formats)
            standardized_df = standardize_well_position_columns(cleaned_df, plate_id)
            
            # Apply calculation pipeline
            processed_df = process_plate_calculations(standardized_df, self.viability_threshold)
            
            # Ensure plate identifier is set (may have been added by standardization)
            if 'PlateID' not in processed_df.columns:
                processed_df['PlateID'] = plate_id
            
            # Calculate and log summary
            summary = calculate_plate_summary(processed_df)
            logger.info(f"Plate {plate_id} processed: {summary['total_wells']} wells, "
                       f"{summary['viable_wells_lptA']} viable lptA, "
                       f"{summary['viable_wells_ldtD']} viable ldtD")
            
            # Store processed plate
            self.processed_plates[plate_id] = processed_df
            
            return processed_df
            
        except Exception as e:
            if isinstance(e, (PlateProcessingError, WellPositionError)):
                raise
            raise PlateProcessingError(f"Failed to process plate {plate_id}: {e}") from e
    
    def process_dual_readout_plate(self, 
                                 df: pd.DataFrame, 
                                 plate_id: str,
                                 hit_calling_config: Optional[dict] = None) -> pd.DataFrame:
        """Process a single plate with dual-readout multi-stage hit calling.
        
        This method extends the standard single-plate processing with multi-stage
        hit calling that identifies reporter hits, vitality hits, and platform hits
        according to the compound screening workflow.
        
        Args:
            df: DataFrame with raw plate data (must have standard column names)
            plate_id: Identifier for this plate
            hit_calling_config: Configuration for hit calling parameters
            
        Returns:
            DataFrame with all calculated metrics plus hit calling results
            
        Raises:
            PlateProcessingError: If processing fails
            
        Examples:
            >>> processor = PlateProcessor()
            >>> config = {'hit_calling': {'multi_stage_enabled': True}}
            >>> df = processor.process_dual_readout_plate(raw_df, 'Plate001', config)
            >>> 'reporter_hit' in df.columns
            True
            >>> 'platform_hit' in df.columns
            True
        """
        logger.info(f"Processing dual-readout plate: {plate_id}")
        
        # Start with existing single-stage processing
        processed_df = self.process_single_plate(df, plate_id)
        
        # Add multi-stage hit calling if requested and configuration provided
        if (hit_calling_config and 
            hit_calling_config.get('hit_calling', {}).get('multi_stage_enabled', False)):
            
            logger.info(f"Applying multi-stage hit calling to plate {plate_id}")
            processed_df = process_multi_stage_hit_calling(processed_df, hit_calling_config)
            
            # Log hit calling summary
            if 'reporter_hit' in processed_df.columns:
                reporter_hits = processed_df['reporter_hit'].sum()
                logger.info(f"Plate {plate_id}: {reporter_hits} reporter hits")
            
            if 'vitality_hit' in processed_df.columns:
                vitality_hits = processed_df['vitality_hit'].sum()
                logger.info(f"Plate {plate_id}: {vitality_hits} vitality hits")
                
            if 'platform_hit' in processed_df.columns:
                platform_hits = processed_df['platform_hit'].sum()
                logger.info(f"Plate {plate_id}: {platform_hits} platform hits")
        
        # Update stored processed plate
        self.processed_plates[plate_id] = processed_df
        
        return processed_df
    
    def process_multiple_plates(self, 
                               plate_files: dict[str, PathLike],
                               sheet_names: Optional[dict[str, str]] = None) -> pd.DataFrame:
        """Process multiple plates and combine results.
        
        Args:
            plate_files: Dictionary mapping plate IDs to file paths
            sheet_names: Optional dictionary mapping plate IDs to Excel sheet names
            
        Returns:
            Combined DataFrame with PlateID column
            
        Raises:
            PlateProcessingError: If any plate processing fails
        """
        logger.info(f"Processing {len(plate_files)} plates")
        
        if sheet_names is None:
            sheet_names = {}
        
        processed_plates = []
        
        for plate_id, file_path in plate_files.items():
            try:
                # Load plate data
                sheet_name = sheet_names.get(plate_id)
                raw_df = self.load_plate_data(file_path, sheet_name=sheet_name)
                
                # Auto-detect columns for first plate, reuse mapping for subsequent plates
                if not self.column_mapping:
                    self.auto_detect_columns(raw_df)
                
                # Apply column mapping
                mapped_df = self.apply_column_mapping(raw_df)
                
                # Process plate
                processed_df = self.process_single_plate(mapped_df, plate_id)
                processed_plates.append(processed_df)
                
                logger.info(f"Successfully processed plate {plate_id}")
                
            except Exception as e:
                logger.error(f"Failed to process plate {plate_id}: {e}")
                raise PlateProcessingError(f"Multi-plate processing failed at {plate_id}: {e}") from e
        
        # Combine all plates
        if not processed_plates:
            raise PlateProcessingError("No plates were successfully processed")
        
        combined_df = pd.concat(processed_plates, ignore_index=True)
        
        logger.info(f"Combined {len(plate_files)} plates into dataset with {len(combined_df)} wells")
        
        return combined_df
    
    def get_processing_summary(self) -> dict[str, Any]:
        """Get summary of all processed plates.
        
        Returns:
            Dictionary with processing summary statistics
        """
        if not self.processed_plates:
            return {'plate_count': 0, 'total_wells': 0}
        
        plate_summaries = {}
        total_wells = 0
        total_viable_lptA = 0
        total_viable_ldtD = 0
        
        for plate_id, df in self.processed_plates.items():
            summary = calculate_plate_summary(df)
            plate_summaries[plate_id] = summary
            total_wells += summary['total_wells']
            total_viable_lptA += summary['viable_wells_lptA']
            total_viable_ldtD += summary['viable_wells_ldtD']
        
        return {
            'plate_count': len(self.processed_plates),
            'total_wells': total_wells,
            'total_viable_lptA': total_viable_lptA,
            'total_viable_ldtD': total_viable_ldtD,
            'viability_rate_lptA': total_viable_lptA / total_wells if total_wells > 0 else 0,
            'viability_rate_ldtD': total_viable_ldtD / total_wells if total_wells > 0 else 0,
            'plate_summaries': plate_summaries,
            'column_mapping': self.column_mapping,
            'viability_threshold': self.viability_threshold,
        }
    
    def reset(self) -> None:
        """Reset processor state (clear processed plates and column mapping)."""
        self.processed_plates.clear()
        self.column_mapping.clear()
        logger.info("Processor state reset")


# Convenience functions for single-file processing
def process_plate_file(file_path: PathLike, 
                      plate_id: Optional[str] = None,
                      sheet_name: Optional[str] = None,
                      viability_threshold: float = 0.3,
                      column_mapping: Optional[dict[str, str]] = None,
                      hit_calling_config: Optional[dict] = None) -> pd.DataFrame:
    """Process a single plate file with automatic setup.
    
    Args:
        file_path: Path to plate data file
        plate_id: Identifier for the plate (defaults to filename)
        sheet_name: Excel sheet name (if applicable)
        viability_threshold: Threshold for viability gating
        column_mapping: Manual column mapping (if auto-detection fails)
        hit_calling_config: Configuration for multi-stage hit calling
        
    Returns:
        Processed DataFrame with all calculated metrics
        
    Examples:
        >>> df = process_plate_file('plate1.xlsx', plate_id='Plate001')
        >>> 'PlateID' in df.columns
        True
        >>> 'Ratio_lptA' in df.columns
        True
        
        >>> # With dual-readout hit calling
        >>> config = {'hit_calling': {'multi_stage_enabled': True}}
        >>> df = process_plate_file('plate1.xlsx', hit_calling_config=config)
        >>> 'platform_hit' in df.columns
        True
    """
    if plate_id is None:
        plate_id = Path(file_path).stem
    
    processor = PlateProcessor(viability_threshold=viability_threshold)
    
    # Load data
    raw_df = processor.load_plate_data(file_path, sheet_name=sheet_name)
    
    # Set up column mapping
    if column_mapping:
        processor.set_column_mapping(column_mapping)
    else:
        processor.auto_detect_columns(raw_df)
    
    # Apply mapping and process
    mapped_df = processor.apply_column_mapping(raw_df)
    
    # Choose processing method based on hit calling configuration
    if hit_calling_config and hit_calling_config.get('hit_calling', {}).get('multi_stage_enabled', False):
        processed_df = processor.process_dual_readout_plate(mapped_df, plate_id, hit_calling_config)
    else:
        processed_df = processor.process_single_plate(mapped_df, plate_id)
    
    return processed_df


def get_available_excel_sheets(file_path: PathLike) -> list[str]:
    """Get list of available sheet names in an Excel file.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        List of sheet names
        
    Raises:
        PlateProcessingError: If file cannot be read or is not Excel format
    """
    file_path = Path(file_path)
    
    if file_path.suffix.lower() not in ['.xlsx', '.xls']:
        raise PlateProcessingError(f"File is not Excel format: {file_path}")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        return excel_file.sheet_names
    except Exception as e:
        raise PlateProcessingError(f"Could not read Excel file {file_path}: {e}") from e