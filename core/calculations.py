"""Core calculation functions implementing exact PRD specification formulas.

This module contains all the mathematical transformations specified in the 
PRD document, including reporter ratios, OD normalization, robust Z-scores,
and viability gating.

All calculations are designed to be numerically reproducible with tolerance ≤ 1e-9
and handle missing values gracefully.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

import numpy as np
import pandas as pd

from .statistics import calculate_robust_zscore, nan_safe_median

logger = logging.getLogger(__name__)

# Type aliases
ArrayLike = Union[np.ndarray, pd.Series, list[float]]
DataFrameLike = Union[pd.DataFrame]


def calculate_reporter_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate reporter ratios as specified in PRD Section 4.1.
    
    Formulas:
    - Ratio_lptA = BG_lptA / BT_lptA
    - Ratio_ldtD = BG_ldtD / BT_ldtD
    
    Args:
        df: DataFrame containing required columns: BG_lptA, BT_lptA, BG_ldtD, BT_ldtD
        
    Returns:
        DataFrame with original columns plus new ratio columns: Ratio_lptA, Ratio_ldtD
        
    Raises:
        ValueError: If required columns are missing
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'BG_lptA': [100, 200, np.nan],
        ...     'BT_lptA': [50, 100, 50],
        ...     'BG_ldtD': [150, 300, 200],
        ...     'BT_ldtD': [75, 150, np.nan]
        ... })
        >>> result = calculate_reporter_ratios(df)
        >>> result['Ratio_lptA'].tolist()
        [2.0, 2.0, nan]
        >>> result['Ratio_ldtD'].tolist()
        [2.0, 2.0, nan]
    """
    logger.debug("Calculating reporter ratios")
    
    # Validate required columns
    required_columns = ['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for reporter ratios: {missing_columns}")
    
    # Create a copy to avoid modifying original DataFrame
    result_df = df.copy()
    
    # Calculate reporter ratios with proper NaN handling
    # Division by zero or NaN automatically produces NaN in pandas/numpy
    with np.errstate(divide='ignore', invalid='ignore'):
        result_df['Ratio_lptA'] = result_df['BG_lptA'] / result_df['BT_lptA']
        result_df['Ratio_ldtD'] = result_df['BG_ldtD'] / result_df['BT_ldtD']
    
    # Log summary statistics
    ratio_lptA_valid = result_df['Ratio_lptA'].count()
    ratio_ldtD_valid = result_df['Ratio_ldtD'].count()
    total_rows = len(result_df)
    
    logger.info(f"Reporter ratios calculated: Ratio_lptA {ratio_lptA_valid}/{total_rows} valid, "
                f"Ratio_ldtD {ratio_ldtD_valid}/{total_rows} valid")
    
    return result_df


def calculate_od_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate OD normalization as specified in PRD Section 4.2.
    
    Formulas:
    - OD_WT_norm = OD_WT / median(OD_WT)
    - OD_tolC_norm = OD_tolC / median(OD_tolC)  
    - OD_SA_norm = OD_SA / median(OD_SA)
    
    Args:
        df: DataFrame containing required columns: OD_WT, OD_tolC, OD_SA
        
    Returns:
        DataFrame with original columns plus normalized OD columns
        
    Raises:
        ValueError: If required columns are missing
        
    Notes:
        - If median is NaN or zero for any OD column, the normalized column will contain all NaN
        - Each OD column is normalized by its own median independently
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'OD_WT': [0.5, 1.0, 1.5, 2.0],
        ...     'OD_tolC': [0.3, 0.6, 0.9, 1.2], 
        ...     'OD_SA': [0.4, 0.8, 1.2, 1.6]
        ... })
        >>> result = calculate_od_normalization(df)
        >>> result['OD_WT_norm'].tolist()  # median(OD_WT) = 1.25
        [0.4, 0.8, 1.2, 1.6]
    """
    logger.debug("Calculating OD normalization")
    
    # Validate required columns
    required_columns = ['OD_WT', 'OD_tolC', 'OD_SA']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for OD normalization: {missing_columns}")
    
    # Create a copy to avoid modifying original DataFrame
    result_df = df.copy()
    
    # Calculate normalization for each OD column
    od_columns = ['OD_WT', 'OD_tolC', 'OD_SA']
    
    for col in od_columns:
        norm_col = f"{col}_norm"
        
        # Calculate median for this column
        col_median = nan_safe_median(result_df[col])
        
        if np.isnan(col_median) or col_median == 0:
            logger.warning(f"Cannot normalize {col}: median is {col_median}")
            result_df[norm_col] = np.nan
        else:
            # Normalize by median
            with np.errstate(divide='ignore', invalid='ignore'):
                result_df[norm_col] = result_df[col] / col_median
            
            logger.debug(f"Normalized {col} by median {col_median:.6f}")
    
    # Log summary statistics
    total_rows = len(result_df)
    for col in od_columns:
        norm_col = f"{col}_norm"
        valid_count = result_df[norm_col].count()
        logger.info(f"OD normalization: {norm_col} {valid_count}/{total_rows} valid")
    
    return result_df


def calculate_robust_zscore_columns(df: pd.DataFrame, 
                                   columns: Optional[list[str]] = None) -> pd.DataFrame:
    """Calculate robust Z-scores for specified columns using PRD Section 4.3 formula.
    
    Formula: Z = (value - median(values)) / (1.4826 * MAD(values))
    where MAD = median(|X - median(X)|)
    
    Args:
        df: DataFrame containing columns to calculate Z-scores for
        columns: List of column names to calculate Z-scores for.
                If None, defaults to ['Ratio_lptA', 'Ratio_ldtD']
        
    Returns:
        DataFrame with original columns plus Z-score columns (prefixed with 'Z_')
        
    Raises:
        ValueError: If any specified columns are missing
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'Ratio_lptA': [1.0, 2.0, 3.0, 4.0, 5.0],
        ...     'Ratio_ldtD': [0.5, 1.0, 1.5, 2.0, 2.5]
        ... })
        >>> result = calculate_robust_zscore_columns(df)
        >>> 'Z_lptA' in result.columns
        True
        >>> 'Z_ldtD' in result.columns  
        True
    """
    logger.debug("Calculating robust Z-scores for columns")
    
    # Default columns if not specified
    if columns is None:
        columns = ['Ratio_lptA', 'Ratio_ldtD']
    
    # Validate columns exist
    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns for Z-score calculation: {missing_columns}")
    
    # Create a copy to avoid modifying original DataFrame
    result_df = df.copy()
    
    # Calculate Z-scores for each specified column
    for col in columns:
        z_col = f"Z_{col.replace('Ratio_', '')}"  # Z_lptA, Z_ldtD
        
        # Calculate robust Z-scores
        z_scores = calculate_robust_zscore(result_df[col])
        result_df[z_col] = z_scores
        
        # Log statistics
        valid_count = np.sum(~np.isnan(z_scores))
        total_count = len(z_scores)
        logger.info(f"Calculated {z_col}: {valid_count}/{total_count} valid Z-scores")
    
    return result_df


def apply_viability_gate(df: pd.DataFrame, f: float = 0.3) -> pd.DataFrame:
    """Apply viability gating as specified in PRD Section 4.4.
    
    Formulas:
    - viability_ok_lptA = BT_lptA >= f * median(BT_lptA)
    - viability_fail_lptA = BT_lptA < f * median(BT_lptA)  
    - viability_ok_ldtD = BT_ldtD >= f * median(BT_ldtD)
    - viability_fail_ldtD = BT_ldtD < f * median(BT_ldtD)
    
    Args:
        df: DataFrame containing BT_lptA and BT_ldtD columns
        f: Viability threshold fraction (default 0.3)
        
    Returns:
        DataFrame with original columns plus viability flag columns
        
    Raises:
        ValueError: If required BT columns are missing
        ValueError: If f is not between 0 and 1
        
    Notes:
        - Wells with NaN BT values are marked as viability_fail
        - If median BT is NaN or zero, all wells are marked as viability_fail
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'BT_lptA': [100, 50, 25, 10, np.nan],
        ...     'BT_ldtD': [200, 100, 50, 25, 150]
        ... })
        >>> result = apply_viability_gate(df, f=0.3)
        >>> result['viability_ok_lptA'].tolist()  # median(BT_lptA)=50, threshold=15
        [True, True, True, False, False]
    """
    logger.debug(f"Applying viability gate with threshold f={f}")
    
    # Validate threshold parameter
    if not 0 <= f <= 1:
        raise ValueError(f"Viability threshold f must be between 0 and 1, got {f}")
    
    # Validate required columns
    required_columns = ['BT_lptA', 'BT_ldtD']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for viability gating: {missing_columns}")
    
    # Create a copy to avoid modifying original DataFrame
    result_df = df.copy()
    
    # Process each BT column
    bt_columns = ['BT_lptA', 'BT_ldtD']
    
    for bt_col in bt_columns:
        reporter = bt_col.replace('BT_', '')  # lptA or ldtD
        ok_col = f"viability_ok_{reporter}"
        fail_col = f"viability_fail_{reporter}"
        
        # Calculate median threshold
        bt_median = nan_safe_median(result_df[bt_col])
        threshold = f * bt_median if not np.isnan(bt_median) else np.nan
        
        if np.isnan(threshold) or threshold <= 0:
            logger.warning(f"Cannot calculate viability gate for {bt_col}: "
                         f"median={bt_median}, threshold={threshold}")
            # Mark all wells as failing viability
            result_df[ok_col] = False
            result_df[fail_col] = True
        else:
            # Apply viability gating
            # NaN values automatically become False in comparison
            with np.errstate(invalid='ignore'):
                result_df[ok_col] = result_df[bt_col] >= threshold
                result_df[fail_col] = result_df[bt_col] < threshold
            
            # Explicitly handle NaN cases - they should fail viability
            nan_mask = result_df[bt_col].isna()
            result_df.loc[nan_mask, ok_col] = False
            result_df.loc[nan_mask, fail_col] = True
            
            logger.info(f"Viability gate {bt_col}: median={bt_median:.3f}, "
                       f"threshold={threshold:.3f}, "
                       f"pass={result_df[ok_col].sum()}/{len(result_df)}")
    
    return result_df


def process_plate_calculations(df: pd.DataFrame, 
                              viability_threshold: float = 0.3) -> pd.DataFrame:
    """Apply all core calculations to a single plate dataset.
    
    This function applies the complete calculation pipeline:
    1. Reporter ratios (Section 4.1)
    2. OD normalization (Section 4.2) 
    3. Robust Z-scores (Section 4.3)
    4. Viability gating (Section 4.4)
    
    Args:
        df: DataFrame with required raw measurement columns
        viability_threshold: Threshold for viability gating (default 0.3)
        
    Returns:
        DataFrame with all original columns plus calculated metrics
        
    Raises:
        ValueError: If required columns are missing
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'BG_lptA': [100, 200], 'BT_lptA': [50, 100],
        ...     'BG_ldtD': [150, 300], 'BT_ldtD': [75, 150],
        ...     'OD_WT': [1.0, 2.0], 'OD_tolC': [0.8, 1.6], 'OD_SA': [1.2, 2.4]
        ... })
        >>> result = process_plate_calculations(df)
        >>> expected_columns = ['Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD',
        ...                    'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm',
        ...                    'viability_ok_lptA', 'viability_ok_ldtD']
        >>> all(col in result.columns for col in expected_columns)
        True
    """
    logger.info(f"Processing plate calculations for {len(df)} wells")
    
    # Start with a copy of input data
    processed_df = df.copy()
    
    # Step 1: Calculate reporter ratios
    processed_df = calculate_reporter_ratios(processed_df)
    
    # Step 2: Calculate OD normalization  
    processed_df = calculate_od_normalization(processed_df)
    
    # Step 3: Calculate robust Z-scores for ratios
    processed_df = calculate_robust_zscore_columns(processed_df, ['Ratio_lptA', 'Ratio_ldtD'])
    
    # Step 4: Apply viability gating
    processed_df = apply_viability_gate(processed_df, f=viability_threshold)
    
    logger.info(f"Completed plate calculations: {len(processed_df)} wells, "
                f"{len(processed_df.columns)} total columns")
    
    return processed_df


def validate_plate_columns(df: pd.DataFrame, required_columns: Optional[list[str]] = None) -> bool:
    """Validate that DataFrame contains required columns for calculations.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names. If None, uses standard set.
        
    Returns:
        True if all required columns are present
        
    Raises:
        ValueError: If any required columns are missing (with detailed message)
    """
    if required_columns is None:
        required_columns = [
            'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD',
            'OD_WT', 'OD_tolC', 'OD_SA'
        ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        available_columns = list(df.columns)
        raise ValueError(
            f"Missing required columns: {missing_columns}\n"
            f"Available columns: {available_columns}"
        )
    
    return True


def calculate_plate_summary(df: pd.DataFrame) -> dict[str, Union[int, float]]:
    """Calculate summary statistics for a processed plate.
    
    Args:
        df: Processed DataFrame with calculated metrics
        
    Returns:
        Dictionary with summary statistics including:
        - total_wells: Total number of wells
        - valid_ratios_lptA/ldtD: Number of valid ratio calculations  
        - viable_wells_lptA/ldtD: Number passing viability gate
        - median_z_lptA/ldtD: Median Z-scores (should be ~0 for robust calculation)
        
    Examples:
        >>> # Assume df is a processed plate DataFrame
        >>> summary = calculate_plate_summary(df)
        >>> summary['total_wells']
        384
        >>> summary['viable_wells_lptA'] 
        312
    """
    summary = {
        'total_wells': len(df),
        'valid_ratios_lptA': df['Ratio_lptA'].count() if 'Ratio_lptA' in df else 0,
        'valid_ratios_ldtD': df['Ratio_ldtD'].count() if 'Ratio_ldtD' in df else 0,
        'viable_wells_lptA': df['viability_ok_lptA'].sum() if 'viability_ok_lptA' in df else 0,
        'viable_wells_ldtD': df['viability_ok_ldtD'].sum() if 'viability_ok_ldtD' in df else 0,
    }
    
    # Add Z-score medians if available (should be ~0 for robust calculation)
    if 'Z_lptA' in df.columns:
        summary['median_z_lptA'] = nan_safe_median(df['Z_lptA'])
    if 'Z_ldtD' in df.columns:
        summary['median_z_ldtD'] = nan_safe_median(df['Z_ldtD'])
    
    # Add ratio medians
    if 'Ratio_lptA' in df.columns:
        summary['median_ratio_lptA'] = nan_safe_median(df['Ratio_lptA'])
    if 'Ratio_ldtD' in df.columns:
        summary['median_ratio_ldtD'] = nan_safe_median(df['Ratio_ldtD'])
    
    return summary


# Multi-stage hit calling functions

def calculate_od_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate OD percentages using plate-wide medians.
    
    Formulas:
    - WT% = OD_WT / median(OD_WT)
    - tolC% = OD_tolC / median(OD_tolC) 
    - SA% = OD_SA / median(OD_SA)
    
    Args:
        df: DataFrame with OD columns
        
    Returns:
        DataFrame with added percentage columns
        
    Note:
        Reuses medians from existing normalization if available,
        otherwise calculates fresh medians from experimental data.
    """
    logger.debug("Calculating OD percentages for vitality analysis")
    
    result_df = df.copy()
    od_columns = ['OD_WT', 'OD_tolC', 'OD_SA']
    
    for od_col in od_columns:
        if od_col not in df.columns:
            logger.warning(f"Missing OD column: {od_col}")
            continue
            
        # Determine percentage column name: OD_WT -> WT%, OD_tolC -> tolC%, OD_SA -> SA%
        strain_name = od_col.split('_')[1]
        pct_col = f"{strain_name}%"
        
        # Check if we can reuse median from existing normalization
        norm_col = f"{od_col}_norm"
        median_val = None
        
        if norm_col in df.columns and not df[norm_col].isna().all():
            # Try to extract median from normalized data: norm = original/median
            # So median = original/norm (for non-zero norm values)
            non_zero_norm = df[df[norm_col] > 0]
            if len(non_zero_norm) > 0:
                # Take median of original/norm to get consistent median estimate
                calculated_medians = non_zero_norm[od_col] / non_zero_norm[norm_col]
                median_val = nan_safe_median(calculated_medians)
        
        # If we couldn't reuse, calculate fresh median
        if median_val is None or np.isnan(median_val) or median_val <= 0:
            median_val = nan_safe_median(df[od_col])
        
        # Apply percentage calculation with error handling
        if np.isnan(median_val) or median_val <= 0:
            logger.warning(f"Cannot calculate {pct_col}: median is {median_val}")
            result_df[pct_col] = np.nan
        else:
            result_df[pct_col] = result_df[od_col] / median_val
            logger.debug(f"Calculated {pct_col} using median {median_val:.6f}")
    
    return result_df


def apply_reporter_hit_gate(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Apply Stage 1 reporter hit calling.
    
    Formula: LumHit = OR(AND(Z_lptA ≥ threshold, viability_ok_lptA), 
                         AND(Z_ldtD ≥ threshold, viability_ok_ldtD))
    
    Args:
        df: DataFrame with Z-scores and viability columns
        config: Configuration with reporter thresholds
        
    Returns:
        DataFrame with added LumHit column
    """
    logger.debug("Applying Stage 1 reporter hit gate")
    
    result_df = df.copy()
    hit_config = config.get('hit_calling', {}).get('reporter', {})
    
    # Get thresholds
    z_threshold_lptA = hit_config.get('z_threshold_lptA', 2.0)
    z_threshold_ldtD = hit_config.get('z_threshold_ldtD', 2.0)
    
    # Check required columns
    required_cols = ['Z_lptA', 'Z_ldtD', 'viability_ok_lptA', 'viability_ok_ldtD']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing columns for reporter hit calling: {missing_cols}")
        result_df['LumHit'] = False
        return result_df
    
    # Apply reporter hit logic
    lptA_hit = (df['Z_lptA'] >= z_threshold_lptA) & df['viability_ok_lptA']
    ldtD_hit = (df['Z_ldtD'] >= z_threshold_ldtD) & df['viability_ok_ldtD']
    
    # OR logic: either reporter can trigger a hit
    result_df['LumHit'] = lptA_hit | ldtD_hit
    
    hit_count = result_df['LumHit'].sum()
    logger.info(f"Stage 1 Reporter hits: {hit_count} / {len(result_df)} wells "
               f"(Z≥{z_threshold_lptA:.1f} lptA or Z≥{z_threshold_ldtD:.1f} ldtD + viable)")
    
    return result_df


def apply_vitality_hit_gate(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Apply Stage 2 vitality hit calling.
    
    Formula: OMpatternOK = AND(tolC% ≤ max_thresh, WT% > min_thresh, SA% > min_thresh)
    
    Logic:
    - tolC% ≤ 0.8: ΔtolC strain inhibited (compound penetrates)
    - WT% > 0.8: Wild type survives (not generally toxic)
    - SA% > 0.8: SA strain survives (compound specificity)
    
    Args:
        df: DataFrame with OD percentage columns
        config: Configuration with vitality thresholds
        
    Returns:
        DataFrame with added OMpatternOK column
    """
    logger.debug("Applying Stage 2 vitality hit gate")
    
    result_df = df.copy()
    vitality_config = config.get('hit_calling', {}).get('vitality', {})
    
    # Get thresholds
    tolC_max = vitality_config.get('tolC_max_percent', 0.8)
    WT_min = vitality_config.get('WT_min_percent', 0.8)
    SA_min = vitality_config.get('SA_min_percent', 0.8)
    
    # Check required columns
    required_cols = ['tolC%', 'WT%', 'SA%']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing columns for vitality hit calling: {missing_cols}")
        result_df['OMpatternOK'] = False
        return result_df
    
    # Apply vitality hit logic with NaN handling
    tolC_inhibited = (df['tolC%'] <= tolC_max) & ~df['tolC%'].isna()
    WT_survives = (df['WT%'] > WT_min) & ~df['WT%'].isna()
    SA_survives = (df['SA%'] > SA_min) & ~df['SA%'].isna()
    
    # AND logic: all three conditions must be met
    result_df['OMpatternOK'] = tolC_inhibited & WT_survives & SA_survives
    
    hit_count = result_df['OMpatternOK'].sum()
    logger.info(f"Stage 2 Vitality hits: {hit_count} / {len(result_df)} wells "
               f"(tolC%≤{tolC_max}, WT%>{WT_min}, SA%>{SA_min})")
    
    return result_df


def apply_platform_hit_gate(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Stage 3 platform hit calling.
    
    Formula: PlatformHit = AND(LumHit, OMpatternOK)
    
    Args:
        df: DataFrame with LumHit and OMpatternOK columns
        
    Returns:
        DataFrame with added PlatformHit column
    """
    logger.debug("Applying Stage 3 platform hit gate")
    
    result_df = df.copy()
    
    # Check required columns
    required_cols = ['LumHit', 'OMpatternOK']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing columns for platform hit calling: {missing_cols}")
        result_df['PlatformHit'] = False
        return result_df
    
    # AND logic: must pass both reporter and vitality
    result_df['PlatformHit'] = df['LumHit'] & df['OMpatternOK']
    
    hit_count = result_df['PlatformHit'].sum()
    reporter_hits = df['LumHit'].sum()
    vitality_hits = df['OMpatternOK'].sum()
    
    logger.info(f"Stage 3 Platform hits: {hit_count} / {len(result_df)} wells "
               f"(Reporter: {reporter_hits}, Vitality: {vitality_hits}, Both: {hit_count})")
    
    return result_df


def process_multi_stage_hit_calling(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Apply complete multi-stage hit calling pipeline.
    
    Pipeline:
    1. Calculate OD percentages (WT%, tolC%, SA%)
    2. Apply Stage 1: Reporter hits (LumHit)
    3. Apply Stage 2: Vitality hits (OMpatternOK)
    4. Apply Stage 3: Platform hits (PlatformHit)
    
    Args:
        df: Processed plate DataFrame (from process_single_plate)
        config: Configuration dictionary with hit calling parameters
        
    Returns:
        DataFrame with all hit calling columns added
    """
    logger.info("Starting multi-stage hit calling pipeline")
    
    try:
        # Stage 0: Calculate OD percentages for vitality analysis
        result_df = calculate_od_percentages(df)
        
        # Stage 1: Reporter hit calling
        result_df = apply_reporter_hit_gate(result_df, config)
        
        # Stage 2: Vitality hit calling  
        result_df = apply_vitality_hit_gate(result_df, config)
        
        # Stage 3: Platform hit calling
        result_df = apply_platform_hit_gate(result_df)
        
        # Log final summary
        total_wells = len(result_df)
        reporter_hits = result_df['LumHit'].sum()
        vitality_hits = result_df['OMpatternOK'].sum()
        platform_hits = result_df['PlatformHit'].sum()
        
        logger.info(f"Multi-stage hit calling complete: {total_wells} wells total, "
                   f"{reporter_hits} reporter hits, {vitality_hits} vitality hits, "
                   f"{platform_hits} platform hits")
        
        return result_df
        
    except Exception as e:
        logger.error(f"Multi-stage hit calling failed: {e}")
        raise