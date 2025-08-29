"""Robust statistical functions for plate data processing.

This module provides NaN-safe statistical functions used throughout the
bio-hit-finder platform, with emphasis on robust statistics that are 
insensitive to outliers.

All functions follow the exact formulas specified in the PRD specification
and handle edge cases gracefully.
"""

from __future__ import annotations

import logging
import warnings
from typing import Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Type aliases for clarity
ArrayLike = Union[np.ndarray, pd.Series, list[float]]
Float = Union[float, np.floating]


def nan_safe_median(values: ArrayLike) -> Float:
    """Calculate median value while ignoring NaN entries.
    
    Args:
        values: Array-like sequence of numeric values
        
    Returns:
        Median value, or NaN if all values are NaN or array is empty
        
    Examples:
        >>> nan_safe_median([1, 2, 3, np.nan])
        2.0
        >>> nan_safe_median([np.nan, np.nan])
        nan
        >>> nan_safe_median([])
        nan
    """
    if not hasattr(values, '__len__') or len(values) == 0:
        logger.warning("Empty array passed to nan_safe_median")
        return np.nan
    
    values_array = np.asarray(values, dtype=float)
    
    # Handle all-NaN case
    if np.all(np.isnan(values_array)):
        logger.debug("All values are NaN in nan_safe_median")
        return np.nan
    
    # Use numpy's nanmedian for robust calculation
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        result = np.nanmedian(values_array)
    
    return float(result)


def mad(values: ArrayLike) -> Float:
    """Calculate Median Absolute Deviation (MAD).
    
    Formula: MAD(X) = median(|X - median(X)|)
    
    Args:
        values: Array-like sequence of numeric values
        
    Returns:
        MAD value, or NaN if insufficient valid data
        
    Notes:
        - Returns NaN if all values are NaN or array is empty
        - Returns 0.0 if all values are identical (zero variance case)
        
    Examples:
        >>> mad([1, 2, 3, 4, 5])
        1.0
        >>> mad([1, 1, 1, 1])
        0.0
        >>> mad([1, 2, np.nan])
        0.5
    """
    if not hasattr(values, '__len__') or len(values) == 0:
        logger.warning("Empty array passed to mad")
        return np.nan
    
    values_array = np.asarray(values, dtype=float)
    
    # Handle all-NaN case
    if np.all(np.isnan(values_array)):
        logger.debug("All values are NaN in mad calculation")
        return np.nan
    
    # Calculate median
    median_val = nan_safe_median(values_array)
    if np.isnan(median_val):
        return np.nan
    
    # Calculate absolute deviations from median
    abs_deviations = np.abs(values_array - median_val)
    
    # Calculate MAD as median of absolute deviations
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mad_value = np.nanmedian(abs_deviations)
    
    result = float(mad_value) if not np.isnan(mad_value) else np.nan
    
    if result == 0.0:
        logger.debug("MAD is zero - all values are identical")
    
    return result


def robust_zscore(values: ArrayLike) -> np.ndarray:
    """Calculate robust Z-scores using median and MAD.
    
    Formula: Z = (value - median(values)) / (1.4826 * MAD(values))
    
    The factor 1.4826 makes MAD a consistent estimator of the standard
    deviation for normally distributed data.
    
    Args:
        values: Array-like sequence of numeric values
        
    Returns:
        Array of robust Z-scores with same shape as input
        Returns NaN for positions where input is NaN or when MAD=0
        
    Notes:
        - When MAD = 0 (all values identical), returns NaN for all positions
        - Preserves NaN positions from input array
        - Uses factor 1.4826 ≈ 1/Φ⁻¹(3/4) for consistency with normal distribution
        
    Examples:
        >>> robust_zscore([1, 2, 3, 4, 5])
        array([-1.34164079, -0.67082039,  0.        ,  0.67082039,  1.34164079])
        >>> robust_zscore([1, 1, 1, 1])  # Zero MAD case
        array([nan, nan, nan, nan])
    """
    if not hasattr(values, '__len__') or len(values) == 0:
        logger.warning("Empty array passed to robust_zscore")
        return np.array([], dtype=float)
    
    values_array = np.asarray(values, dtype=float)
    
    # Initialize result array with NaNs
    z_scores = np.full_like(values_array, np.nan, dtype=float)
    
    # Check if we have any valid data
    if np.all(np.isnan(values_array)):
        logger.debug("All values are NaN in robust_zscore")
        return z_scores
    
    # Calculate median and MAD
    median_val = nan_safe_median(values_array)
    mad_val = mad(values_array)
    
    if np.isnan(median_val) or np.isnan(mad_val):
        logger.warning("Could not calculate median or MAD for robust_zscore")
        return z_scores
    
    # Handle zero MAD case (all values identical)
    if mad_val == 0.0:
        logger.warning("MAD is zero - cannot compute robust Z-scores (all values identical)")
        return z_scores
    
    # Calculate robust Z-scores
    # Factor 1.4826 makes MAD consistent with standard deviation for normal data
    scaling_factor = 1.4826 * mad_val
    z_scores = (values_array - median_val) / scaling_factor
    
    logger.debug(f"Computed robust Z-scores: median={median_val:.6f}, MAD={mad_val:.6f}")
    
    return z_scores


def calculate_robust_zscore(values: ArrayLike) -> np.ndarray:
    """Alias for robust_zscore to match PRD specification naming.
    
    This function provides the exact interface specified in the PRD document.
    
    Args:
        values: Array-like sequence of numeric values
        
    Returns:
        Array of robust Z-scores with same shape as input
        
    See Also:
        robust_zscore: The underlying implementation
    """
    return robust_zscore(values)


def validate_numeric_array(values: ArrayLike, name: str = "values") -> np.ndarray:
    """Validate and convert input to numeric array.
    
    Args:
        values: Input array-like data
        name: Name of the variable for error messages
        
    Returns:
        Validated numpy array with float dtype
        
    Raises:
        TypeError: If values cannot be converted to numeric array
        ValueError: If array is empty
    """
    try:
        values_array = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as e:
        raise TypeError(f"Cannot convert {name} to numeric array: {e}") from e
    
    if values_array.size == 0:
        raise ValueError(f"{name} cannot be empty")
    
    return values_array


def summary_statistics(values: ArrayLike) -> dict[str, Float]:
    """Calculate comprehensive summary statistics for a dataset.
    
    Args:
        values: Array-like sequence of numeric values
        
    Returns:
        Dictionary containing:
        - count: Number of valid (non-NaN) values
        - median: Robust central tendency
        - mad: Median absolute deviation
        - q25, q75: 25th and 75th percentiles
        - min, max: Extremes of valid data
        - nan_count: Number of NaN values
        
    Examples:
        >>> stats = summary_statistics([1, 2, 3, 4, 5, np.nan])
        >>> stats['median']
        3.0
        >>> stats['mad']
        1.0
        >>> stats['nan_count']
        1
    """
    if not hasattr(values, '__len__') or len(values) == 0:
        return {
            'count': 0,
            'median': np.nan,
            'mad': np.nan,
            'q25': np.nan,
            'q75': np.nan,
            'min': np.nan,
            'max': np.nan,
            'nan_count': 0,
        }
    
    values_array = np.asarray(values, dtype=float)
    
    # Count valid and invalid values
    valid_mask = ~np.isnan(values_array)
    valid_count = np.sum(valid_mask)
    nan_count = len(values_array) - valid_count
    
    if valid_count == 0:
        return {
            'count': 0,
            'median': np.nan,
            'mad': np.nan,
            'q25': np.nan,
            'q75': np.nan,
            'min': np.nan,
            'max': np.nan,
            'nan_count': nan_count,
        }
    
    valid_values = values_array[valid_mask]
    
    # Calculate robust statistics
    median_val = float(np.median(valid_values))
    mad_val = mad(valid_values)
    
    # Calculate percentiles
    q25 = float(np.percentile(valid_values, 25))
    q75 = float(np.percentile(valid_values, 75))
    
    # Calculate extremes
    min_val = float(np.min(valid_values))
    max_val = float(np.max(valid_values))
    
    return {
        'count': valid_count,
        'median': median_val,
        'mad': mad_val,
        'q25': q25,
        'q75': q75,
        'min': min_val,
        'max': max_val,
        'nan_count': nan_count,
    }


# Convenience functions for common patterns
def is_constant_array(values: ArrayLike, tolerance: float = 1e-9) -> bool:
    """Check if array contains essentially constant values.
    
    Args:
        values: Array-like sequence of numeric values  
        tolerance: Tolerance for considering values equal
        
    Returns:
        True if all valid values are within tolerance of each other
    """
    values_array = np.asarray(values, dtype=float)
    
    # Remove NaN values
    valid_values = values_array[~np.isnan(values_array)]
    
    if len(valid_values) <= 1:
        return True
    
    return np.ptp(valid_values) <= tolerance


def count_valid_values(values: ArrayLike) -> int:
    """Count the number of valid (non-NaN) values in array.
    
    Args:
        values: Array-like sequence of numeric values
        
    Returns:
        Number of non-NaN values
    """
    if not hasattr(values, '__len__') or len(values) == 0:
        return 0
    
    values_array = np.asarray(values, dtype=float)
    return int(np.sum(~np.isnan(values_array)))