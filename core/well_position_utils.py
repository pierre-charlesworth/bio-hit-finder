"""Well position format utilities for handling different plate data formats.

This module provides utilities to handle different well position formats:
1. Well column format: "A01", "B02", "H12", etc.
2. Row/Col format: separate Row ("A", "B") and Col (1, 2, 3) columns

The utilities ensure consistent data format regardless of input format.
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import Tuple, Optional, List
import string

logger = logging.getLogger(__name__)


class WellPositionError(Exception):
    """Exception raised for well position format errors."""
    pass


def detect_well_position_format(df: pd.DataFrame) -> str:
    """Detect the well position format present in the DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Format type: "well_only", "row_col_only", "both", or "none"
    """
    has_well = 'Well' in df.columns
    has_row = 'Row' in df.columns  
    has_col = 'Col' in df.columns
    
    if has_well and has_row and has_col:
        return "both"
    elif has_well and not (has_row and has_col):
        return "well_only"
    elif not has_well and has_row and has_col:
        return "row_col_only"
    else:
        return "none"


def validate_well_format(well_values: pd.Series) -> bool:
    """Validate that well values follow expected format.
    
    Args:
        well_values: Series containing well identifiers
        
    Returns:
        True if all values are valid well formats
        
    Raises:
        WellPositionError: If invalid formats are found
    """
    # Remove NaN values for validation
    valid_wells = well_values.dropna()
    
    if len(valid_wells) == 0:
        raise WellPositionError("No valid well values found")
    
    # Pattern for well format: Letter(s) followed by digits
    # Supports: A1, A01, AA1, AA01, etc.
    well_pattern = re.compile(r'^[A-Z]+\d+$', re.IGNORECASE)
    
    invalid_wells = []
    for well in valid_wells:
        if not isinstance(well, str) or not well_pattern.match(well):
            invalid_wells.append(well)
    
    if invalid_wells:
        raise WellPositionError(f"Invalid well formats found: {invalid_wells[:5]}")
    
    return True


def validate_row_col_format(row_values: pd.Series, col_values: pd.Series) -> bool:
    """Validate that row and column values are in expected format.
    
    Args:
        row_values: Series containing row identifiers
        col_values: Series containing column identifiers
        
    Returns:
        True if all values are valid
        
    Raises:
        WellPositionError: If invalid formats are found
    """
    # Validate rows - should be letters
    valid_rows = row_values.dropna()
    if len(valid_rows) == 0:
        raise WellPositionError("No valid row values found")
    
    invalid_rows = []
    for row in valid_rows:
        if not isinstance(row, str) or not re.match(r'^[A-Z]+$', row, re.IGNORECASE):
            invalid_rows.append(row)
    
    if invalid_rows:
        raise WellPositionError(f"Invalid row formats found: {invalid_rows[:5]}")
    
    # Validate columns - should be positive integers
    valid_cols = col_values.dropna()
    if len(valid_cols) == 0:
        raise WellPositionError("No valid column values found")
    
    invalid_cols = []
    for col in valid_cols:
        try:
            col_int = int(col)
            if col_int <= 0:
                invalid_cols.append(col)
        except (ValueError, TypeError):
            invalid_cols.append(col)
    
    if invalid_cols:
        raise WellPositionError(f"Invalid column formats found: {invalid_cols[:5]}")
    
    return True


def generate_well_from_row_col(df: pd.DataFrame, 
                              row_col: str = 'Row', 
                              col_col: str = 'Col',
                              zero_pad: bool = True) -> pd.DataFrame:
    """Generate Well column from Row and Col columns.
    
    Args:
        df: DataFrame containing Row and Col columns
        row_col: Name of the row column (default: 'Row')
        col_col: Name of the column column (default: 'Col')
        zero_pad: Whether to zero-pad column numbers (default: True)
        
    Returns:
        DataFrame with added Well column
        
    Raises:
        WellPositionError: If Row or Col columns are missing or invalid
    """
    if row_col not in df.columns or col_col not in df.columns:
        raise WellPositionError(f"Missing required columns: {row_col}, {col_col}")
    
    df_copy = df.copy()
    
    # Validate input format
    validate_row_col_format(df_copy[row_col], df_copy[col_col])
    
    # Generate Well column
    if zero_pad:
        # Determine padding width based on max column number
        max_col = df_copy[col_col].max()
        pad_width = len(str(max_col))
        df_copy['Well'] = (
            df_copy[row_col].astype(str).str.upper() + 
            df_copy[col_col].astype(str).str.zfill(pad_width)
        )
    else:
        df_copy['Well'] = (
            df_copy[row_col].astype(str).str.upper() + 
            df_copy[col_col].astype(str)
        )
    
    logger.debug(f"Generated {len(df_copy)} well positions from Row/Col")
    return df_copy


def generate_row_col_from_well(df: pd.DataFrame, well_col: str = 'Well') -> pd.DataFrame:
    """Generate Row and Col columns from Well column.
    
    Args:
        df: DataFrame containing Well column
        well_col: Name of the well column (default: 'Well')
        
    Returns:
        DataFrame with added Row and Col columns
        
    Raises:
        WellPositionError: If Well column is missing or invalid
    """
    if well_col not in df.columns:
        raise WellPositionError(f"Missing required column: {well_col}")
    
    df_copy = df.copy()
    
    # Validate well format
    validate_well_format(df_copy[well_col])
    
    # Extract row and column from well position
    well_pattern = re.compile(r'^([A-Z]+)(\d+)$', re.IGNORECASE)
    
    rows = []
    cols = []
    
    for well in df_copy[well_col]:
        if pd.isna(well):
            rows.append(np.nan)
            cols.append(np.nan)
            continue
            
        match = well_pattern.match(str(well))
        if match:
            row_part, col_part = match.groups()
            rows.append(row_part.upper())
            cols.append(int(col_part))
        else:
            rows.append(np.nan)
            cols.append(np.nan)
    
    df_copy['Row'] = rows
    df_copy['Col'] = cols
    
    logger.debug(f"Generated Row/Col from {len(df_copy)} well positions")
    return df_copy


def auto_generate_plate_id(df: pd.DataFrame, 
                          default_id: Optional[str] = None,
                          plate_id_col: str = 'PlateID') -> pd.DataFrame:
    """Generate PlateID if missing from DataFrame.
    
    Args:
        df: DataFrame that may be missing PlateID
        default_id: Default plate ID to use (if None, generates from context)
        plate_id_col: Name of the plate ID column (default: 'PlateID')
        
    Returns:
        DataFrame with PlateID column
    """
    df_copy = df.copy()
    
    if plate_id_col not in df_copy.columns:
        if default_id is None:
            # Generate intelligent default based on common patterns
            default_id = "Plate001"
        
        df_copy[plate_id_col] = default_id
        logger.info(f"Generated PlateID: {default_id}")
    
    return df_copy


def detect_plate_layout(df: pd.DataFrame) -> Tuple[int, int]:
    """Detect the plate layout (rows x columns) from the data.
    
    Args:
        df: DataFrame with well position data
        
    Returns:
        Tuple of (num_rows, num_cols)
    """
    format_type = detect_well_position_format(df)
    
    if format_type in ["row_col_only", "both"]:
        # Use Row and Col columns
        unique_rows = df['Row'].nunique()
        unique_cols = df['Col'].nunique()
        return unique_rows, unique_cols
    
    elif format_type == "well_only":
        # Parse Well column to extract layout
        df_with_rowcol = generate_row_col_from_well(df)
        unique_rows = df_with_rowcol['Row'].nunique()
        unique_cols = df_with_rowcol['Col'].nunique()
        return unique_rows, unique_cols
    
    else:
        # Default assumption for common plate formats
        logger.warning("Could not detect plate layout, assuming 96-well (8x12)")
        return 8, 12


def standardize_well_position_columns(df: pd.DataFrame, 
                                    plate_id: Optional[str] = None,
                                    auto_detect_layout: bool = True) -> pd.DataFrame:
    """Ensure DataFrame has all required well position columns.
    
    This is the main function that standardizes well position format
    regardless of input format. It ensures the DataFrame has Well, Row, Col,
    and PlateID columns.
    
    Args:
        df: Input DataFrame with well position data
        plate_id: Optional plate ID to assign
        auto_detect_layout: Whether to auto-detect plate layout
        
    Returns:
        DataFrame with standardized well position columns
        
    Raises:
        WellPositionError: If data cannot be standardized
    """
    try:
        format_type = detect_well_position_format(df)
        logger.debug(f"Detected well position format: {format_type}")
        
        df_standardized = df.copy()
        
        # Handle each format type
        if format_type == "none":
            raise WellPositionError(
                "No well position data found. Data must contain either 'Well' column "
                "or both 'Row' and 'Col' columns."
            )
        
        elif format_type == "row_col_only":
            # Generate Well from Row/Col
            df_standardized = generate_well_from_row_col(df_standardized)
            logger.info("Generated Well column from Row/Col")
        
        elif format_type == "well_only":
            # Generate Row/Col from Well
            df_standardized = generate_row_col_from_well(df_standardized)
            logger.info("Generated Row/Col columns from Well")
        
        elif format_type == "both":
            # Validate consistency between Well and Row/Col
            # Generate temporary columns to compare
            temp_df = generate_well_from_row_col(df_standardized.drop('Well', axis=1))
            
            # Check for mismatches (allowing for some format differences)
            mismatches = df_standardized['Well'].str.upper() != temp_df['Well'].str.upper()
            
            if mismatches.sum() > 0:
                logger.warning(f"Found {mismatches.sum()} mismatches between Well and Row/Col columns")
                # Use Row/Col as source of truth and regenerate Well
                df_standardized = df_standardized.drop('Well', axis=1)
                df_standardized = generate_well_from_row_col(df_standardized)
                logger.info("Regenerated Well column from Row/Col due to inconsistencies")
            
        # Ensure PlateID is present
        df_standardized = auto_generate_plate_id(df_standardized, plate_id)
        
        # Detect and log plate layout
        if auto_detect_layout:
            num_rows, num_cols = detect_plate_layout(df_standardized)
            logger.info(f"Detected plate layout: {num_rows} rows x {num_cols} columns")
        
        # Final validation
        required_cols = ['Well', 'Row', 'Col', 'PlateID']
        missing_cols = [col for col in required_cols if col not in df_standardized.columns]
        
        if missing_cols:
            raise WellPositionError(f"Failed to generate required columns: {missing_cols}")
        
        logger.info(f"Successfully standardized {len(df_standardized)} well positions")
        return df_standardized
        
    except Exception as e:
        if isinstance(e, WellPositionError):
            raise
        else:
            raise WellPositionError(f"Failed to standardize well positions: {e}") from e


def get_well_position_summary(df: pd.DataFrame) -> dict:
    """Get a summary of well position data in the DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary with summary information
    """
    format_type = detect_well_position_format(df)
    
    summary = {
        'format_type': format_type,
        'total_wells': len(df),
        'has_well_column': 'Well' in df.columns,
        'has_row_column': 'Row' in df.columns,
        'has_col_column': 'Col' in df.columns,
        'has_plate_id': 'PlateID' in df.columns,
    }
    
    if format_type != "none":
        try:
            num_rows, num_cols = detect_plate_layout(df)
            summary.update({
                'detected_rows': num_rows,
                'detected_cols': num_cols,
                'detected_layout': f"{num_rows}x{num_cols}",
            })
        except Exception as e:
            summary['layout_detection_error'] = str(e)
    
    return summary