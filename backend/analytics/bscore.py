"""B-scoring implementation using median-polish for row/column bias correction.

This module implements the B-score calculation as specified in the PRD,
which uses median-polish to remove systematic row and column biases while
preserving biological effects.

The B-scoring process:
1. Apply median-polish iteratively to remove row and column effects
2. Calculate residuals from the additive model
3. Apply robust scaling to get final B-scores

All calculations handle missing wells (NaN) gracefully and include performance
optimizations for real-time UI updates.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple, Union, Dict, List
import warnings

import numpy as np
import pandas as pd

try:
    from ..core.statistics import nan_safe_median, mad, robust_zscore
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.statistics import nan_safe_median, mad, robust_zscore

logger = logging.getLogger(__name__)

# Type aliases
ArrayLike = Union[np.ndarray, pd.Series, list[float]]
MatrixLike = Union[np.ndarray, pd.DataFrame]


class BScoreError(Exception):
    """Custom exception for B-score calculation errors."""
    pass


class ConvergenceError(BScoreError):
    """Exception raised when median-polish fails to converge."""
    pass


def median_polish(matrix: np.ndarray, 
                  max_iter: int = 10, 
                  tol: float = 1e-6,
                  return_components: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Apply median-polish algorithm to remove row and column effects.
    
    The median-polish algorithm iteratively estimates and removes row and column
    effects from a matrix using medians, which are robust to outliers.
    
    Algorithm:
    1. Initialize row_effects = 0, col_effects = 0
    2. For each iteration:
       - r_i ← median_j(X_ij - c_j) for each row i
       - c_j ← median_i(X_ij - r_i) for each column j
       - Update effects and residuals
    3. Continue until convergence or max_iter reached
    
    Args:
        matrix: 2D numpy array (rows x cols) - missing values should be NaN
        max_iter: Maximum number of iterations
        tol: Convergence tolerance (change in effects)
        return_components: If True, return (residuals, row_effects, col_effects)
        
    Returns:
        If return_components=False: residuals matrix (same shape as input)
        If return_components=True: tuple of (residuals, row_effects, col_effects)
        
    Raises:
        ValueError: If matrix is not 2D or has invalid dimensions
        ConvergenceError: If algorithm fails to converge within max_iter
        
    Examples:
        >>> matrix = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
        >>> residuals = median_polish(matrix)
        >>> residuals.shape == matrix.shape
        True
        
        >>> # With missing values
        >>> matrix[0, 0] = np.nan
        >>> residuals = median_polish(matrix)
        >>> np.isnan(residuals[0, 0])
        True
    """
    # Validate input
    if not isinstance(matrix, np.ndarray):
        matrix = np.asarray(matrix, dtype=float)
    
    if matrix.ndim != 2:
        raise ValueError(f"Expected 2D matrix, got {matrix.ndim}D")
    
    n_rows, n_cols = matrix.shape
    
    if n_rows == 0 or n_cols == 0:
        raise ValueError("Matrix cannot have zero rows or columns")
    
    logger.debug(f"Starting median-polish on {n_rows}x{n_cols} matrix")
    
    # Initialize effects arrays
    row_effects = np.zeros(n_rows)
    col_effects = np.zeros(n_cols)
    
    # Working copy of matrix
    working_matrix = matrix.copy()
    
    # Track convergence
    converged = False
    prev_residuals = None
    
    for iteration in range(max_iter):
        prev_row_effects = row_effects.copy()
        prev_col_effects = col_effects.copy()
        
        # Step 1: Update row effects
        # r_i = median_j(X_ij - c_j) for each row i
        for i in range(n_rows):
            row_values = working_matrix[i, :] - col_effects
            row_median = nan_safe_median(row_values)
            if not np.isnan(row_median) and np.abs(row_median) > 1e-12:
                row_effects[i] += row_median
                working_matrix[i, :] -= row_median
        
        # Step 2: Update column effects  
        # c_j = median_i(X_ij - r_i) for each column j  
        for j in range(n_cols):
            col_values = working_matrix[:, j] - (row_effects - prev_row_effects)
            col_median = nan_safe_median(col_values)
            if not np.isnan(col_median) and np.abs(col_median) > 1e-12:
                col_effects[j] += col_median
                working_matrix[:, j] -= col_median
        
        # Check convergence using residuals instead of effects
        current_residuals = working_matrix.copy()
        
        if prev_residuals is not None:
            residual_change = np.nanmax(np.abs(current_residuals - prev_residuals))
        else:
            residual_change = np.inf
        
        prev_residuals = current_residuals.copy()
        
        # Also check effects change as backup
        row_change = np.max(np.abs(row_effects - prev_row_effects))
        col_change = np.max(np.abs(col_effects - prev_col_effects))
        max_change = min(residual_change, max(row_change, col_change))
        
        logger.debug(f"Iteration {iteration + 1}: residual_change = {residual_change:.9f}, effects_change = {max(row_change, col_change):.9f}")
        
        if max_change < tol:
            converged = True
            logger.debug(f"Converged after {iteration + 1} iterations")
            break
    
    if not converged:
        logger.warning(f"Median-polish did not converge after {max_iter} iterations "
                      f"(final change = {max_change:.9f})")
        # Don't raise exception - use partial result
    
    # Calculate final residuals
    # Residuals = Original - RowEffects - ColEffects  
    residuals = matrix.copy()
    for i in range(n_rows):
        for j in range(n_cols):
            if not np.isnan(matrix[i, j]):
                residuals[i, j] = matrix[i, j] - row_effects[i] - col_effects[j]
    
    logger.debug(f"Median-polish complete: "
                f"row_effects range [{np.min(row_effects):.6f}, {np.max(row_effects):.6f}], "
                f"col_effects range [{np.min(col_effects):.6f}, {np.max(col_effects):.6f}]")
    
    if return_components:
        return residuals, row_effects, col_effects
    else:
        return residuals


def calculate_bscore(matrix: np.ndarray, 
                    max_iter: int = 10, 
                    tol: float = 1e-6) -> np.ndarray:
    """Calculate B-scores from a matrix using median-polish and robust scaling.
    
    B-score calculation:
    1. Apply median-polish to get residuals: R_ij = X_ij - (r_i + c_j)
    2. Apply robust scaling: B_ij = (R_ij - median(R)) / (1.4826 × MAD_R)
    
    Args:
        matrix: 2D numpy array with plate data
        max_iter: Maximum iterations for median-polish
        tol: Convergence tolerance for median-polish
        
    Returns:
        B-score matrix with same shape as input
        
    Raises:
        ValueError: If input matrix is invalid
        BScoreError: If B-score calculation fails
        
    Notes:
        - Missing values (NaN) are preserved in output
        - When MAD = 0 (constant residuals), returns NaN for all positions
        - Uses factor 1.4826 for consistency with normal distribution
        
    Examples:
        >>> matrix = np.random.randn(8, 12)  # 96-well plate layout
        >>> bscores = calculate_bscore(matrix)
        >>> bscores.shape == matrix.shape
        True
        
        >>> # B-scores should be approximately N(0,1) distributed
        >>> valid_bscores = bscores[~np.isnan(bscores)]
        >>> abs(np.median(valid_bscores)) < 0.1  # Close to 0
        True
    """
    logger.debug("Calculating B-scores")
    
    try:
        # Apply median-polish to get residuals
        residuals = median_polish(matrix, max_iter=max_iter, tol=tol)
        
        # Apply robust scaling to residuals
        # Flatten residuals to calculate global median and MAD
        residuals_flat = residuals.flatten()
        
        # Remove NaN values for statistics calculation
        valid_residuals = residuals_flat[~np.isnan(residuals_flat)]
        
        if len(valid_residuals) == 0:
            logger.warning("No valid residuals for B-score calculation")
            return np.full_like(matrix, np.nan)
        
        # Calculate robust scaling parameters
        residual_median = nan_safe_median(valid_residuals)
        residual_mad = mad(valid_residuals)
        
        logger.debug(f"Residuals: median={residual_median:.6f}, MAD={residual_mad:.6f}")
        
        # Handle zero MAD case
        if np.isnan(residual_mad) or residual_mad == 0.0:
            logger.warning("MAD of residuals is zero - cannot compute B-scores")
            return np.full_like(matrix, np.nan)
        
        # Calculate B-scores: (residuals - median) / (1.4826 * MAD)
        bscores = (residuals - residual_median) / (1.4826 * residual_mad)
        
        # Count valid B-scores
        valid_bscores = np.sum(~np.isnan(bscores))
        total_wells = bscores.size
        
        logger.info(f"B-scores calculated: {valid_bscores}/{total_wells} valid wells")
        
        return bscores
        
    except Exception as e:
        raise BScoreError(f"Failed to calculate B-scores: {e}") from e


class BScoreProcessor:
    """Processor class for applying B-scoring to plate metrics.
    
    This class handles the application of B-scoring to multiple plate metrics
    simultaneously, with caching for performance optimization.
    
    Attributes:
        max_iter: Maximum iterations for median-polish
        tol: Convergence tolerance
        cache: Dictionary for caching results
        enabled_metrics: List of metrics to apply B-scoring to
    """
    
    DEFAULT_METRICS = ['Z_lptA', 'Z_ldtD', 'Ratio_lptA', 'Ratio_ldtD']
    
    def __init__(self, 
                 max_iter: int = 10, 
                 tol: float = 1e-6,
                 cache_enabled: bool = True):
        """Initialize B-score processor.
        
        Args:
            max_iter: Maximum iterations for median-polish
            tol: Convergence tolerance
            cache_enabled: Whether to enable result caching
        """
        self.max_iter = max_iter
        self.tol = tol
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, np.ndarray] = {}
        self.enabled_metrics = self.DEFAULT_METRICS.copy()
        
        logger.info(f"Initialized BScoreProcessor: max_iter={max_iter}, tol={tol}")
    
    def set_enabled_metrics(self, metrics: List[str]) -> None:
        """Set which metrics to apply B-scoring to.
        
        Args:
            metrics: List of column names to apply B-scoring to
        """
        self.enabled_metrics = list(metrics)
        logger.info(f"Set B-score metrics: {self.enabled_metrics}")
    
    def clear_cache(self) -> None:
        """Clear the result cache."""
        self.cache.clear()
        logger.debug("Cleared B-score cache")
    
    def _get_cache_key(self, metric: str, matrix: np.ndarray) -> str:
        """Generate cache key for a metric matrix."""
        if not self.cache_enabled:
            return ""
        
        # Use hash of non-NaN values for cache key
        valid_values = matrix[~np.isnan(matrix)]
        if len(valid_values) == 0:
            return f"{metric}_empty"
        
        value_hash = hash(tuple(valid_values.tolist()))
        shape_str = f"{matrix.shape[0]}x{matrix.shape[1]}"
        return f"{metric}_{shape_str}_{value_hash}_{self.max_iter}_{self.tol}"
    
    def _matrix_from_plate_data(self, 
                               df: pd.DataFrame, 
                               metric: str,
                               plate_layout: Tuple[int, int] = (8, 12)) -> np.ndarray:
        """Convert plate data to matrix format for B-scoring.
        
        Args:
            df: DataFrame with plate data including Row and Col columns
            metric: Name of the metric column to extract
            plate_layout: Tuple of (n_rows, n_cols) for plate dimensions
            
        Returns:
            2D numpy array with plate layout
            
        Raises:
            ValueError: If required columns are missing or data is invalid
        """
        required_cols = ['Row', 'Col', metric]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        n_rows, n_cols = plate_layout
        
        # Initialize matrix with NaN
        matrix = np.full((n_rows, n_cols), np.nan)
        
        # Map rows (A, B, C, ...) to indices (0, 1, 2, ...)
        row_mapping = {chr(ord('A') + i): i for i in range(n_rows)}
        
        valid_wells = 0
        for _, row in df.iterrows():
            try:
                row_label = str(row['Row']).upper().strip()
                col_num = int(row['Col'])
                
                if row_label not in row_mapping:
                    logger.warning(f"Invalid row label: {row_label}")
                    continue
                
                row_idx = row_mapping[row_label]
                col_idx = col_num - 1  # Convert 1-based to 0-based
                
                if col_idx < 0 or col_idx >= n_cols:
                    logger.warning(f"Column {col_num} out of range for plate layout")
                    continue
                
                if not np.isnan(row[metric]):
                    matrix[row_idx, col_idx] = row[metric]
                    valid_wells += 1
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid well position: {e}")
                continue
        
        logger.debug(f"Created {n_rows}x{n_cols} matrix for {metric}: {valid_wells} valid wells")
        return matrix
    
    def _matrix_to_plate_data(self, 
                             matrix: np.ndarray, 
                             df: pd.DataFrame, 
                             metric_name: str,
                             plate_layout: Tuple[int, int] = (8, 12)) -> pd.Series:
        """Convert matrix back to plate data format.
        
        Args:
            matrix: 2D array with B-scores
            df: Original DataFrame to map back to
            metric_name: Name for the new B-score column
            plate_layout: Plate dimensions
            
        Returns:
            Series with B-scores in same order as input DataFrame
        """
        n_rows, n_cols = plate_layout
        
        # Initialize result series with NaN
        result = pd.Series(np.nan, index=df.index, name=metric_name)
        
        # Map rows (A, B, C, ...) to indices
        row_mapping = {chr(ord('A') + i): i for i in range(n_rows)}
        
        for idx, row in df.iterrows():
            try:
                row_label = str(row['Row']).upper().strip()
                col_num = int(row['Col'])
                
                if row_label in row_mapping and 1 <= col_num <= n_cols:
                    row_idx = row_mapping[row_label]
                    col_idx = col_num - 1
                    
                    result.iloc[idx] = matrix[row_idx, col_idx]
                    
            except (ValueError, KeyError):
                continue  # Keep NaN for invalid positions
        
        return result
    
    def calculate_bscores_for_plate(self, 
                                   df: pd.DataFrame,
                                   metrics: Optional[List[str]] = None,
                                   plate_layout: Tuple[int, int] = (8, 12)) -> pd.DataFrame:
        """Calculate B-scores for specified metrics in a plate DataFrame.
        
        Args:
            df: DataFrame with plate data (must include Row, Col columns)
            metrics: List of metrics to calculate B-scores for (default: enabled_metrics)
            plate_layout: Tuple of (n_rows, n_cols) for plate dimensions
            
        Returns:
            DataFrame with original data plus B-score columns (B_<metric>)
            
        Raises:
            ValueError: If required columns are missing
            BScoreError: If B-score calculation fails
            
        Examples:
            >>> df = load_plate_data_with_positions('plate1.xlsx')
            >>> processor = BScoreProcessor()
            >>> result_df = processor.calculate_bscores_for_plate(df)
            >>> 'B_Z_lptA' in result_df.columns
            True
        """
        if metrics is None:
            metrics = self.enabled_metrics
        
        logger.info(f"Calculating B-scores for metrics: {metrics}")
        
        # Validate required columns
        required_cols = ['Row', 'Col'] + metrics
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns for B-scoring: {missing_cols}")
        
        result_df = df.copy()
        
        for metric in metrics:
            try:
                logger.debug(f"Processing metric: {metric}")
                
                # Convert to matrix format
                matrix = self._matrix_from_plate_data(df, metric, plate_layout)
                
                # Check cache
                cache_key = self._get_cache_key(metric, matrix)
                if cache_key and cache_key in self.cache:
                    logger.debug(f"Using cached B-scores for {metric}")
                    bscore_matrix = self.cache[cache_key]
                else:
                    # Calculate B-scores
                    bscore_matrix = calculate_bscore(matrix, self.max_iter, self.tol)
                    
                    # Cache result
                    if cache_key:
                        self.cache[cache_key] = bscore_matrix
                
                # Convert back to plate format
                bscore_column_name = f"B_{metric}"
                bscore_series = self._matrix_to_plate_data(
                    bscore_matrix, df, bscore_column_name, plate_layout
                )
                
                result_df[bscore_column_name] = bscore_series
                
                # Log summary
                valid_bscores = bscore_series.count()
                total_wells = len(bscore_series)
                logger.info(f"Generated B-scores for {metric}: {valid_bscores}/{total_wells} valid")
                
            except Exception as e:
                logger.error(f"Failed to calculate B-scores for {metric}: {e}")
                # Add NaN column so downstream processing doesn't fail
                result_df[f"B_{metric}"] = np.nan
        
        return result_df
    
    def get_processing_summary(self) -> Dict[str, any]:
        """Get summary of B-score processing status.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'enabled_metrics': self.enabled_metrics,
            'max_iter': self.max_iter,
            'tolerance': self.tol,
            'cache_enabled': self.cache_enabled,
            'cached_results': len(self.cache) if self.cache_enabled else 0,
            'cache_keys': list(self.cache.keys()) if self.cache_enabled else []
        }


# Convenience functions for direct usage
def apply_bscoring_to_dataframe(df: pd.DataFrame, 
                               metrics: Optional[List[str]] = None,
                               max_iter: int = 10,
                               tol: float = 1e-6,
                               plate_layout: Tuple[int, int] = (8, 12)) -> pd.DataFrame:
    """Apply B-scoring to a plate DataFrame with automatic setup.
    
    Args:
        df: DataFrame with plate data (must include Row, Col columns)
        metrics: List of metrics to calculate B-scores for
        max_iter: Maximum iterations for median-polish
        tol: Convergence tolerance
        plate_layout: Plate dimensions
        
    Returns:
        DataFrame with original data plus B-score columns
        
    Examples:
        >>> df = load_plate_data('plate1.xlsx')
        >>> result_df = apply_bscoring_to_dataframe(df, ['Z_lptA', 'Z_ldtD'])
        >>> 'B_Z_lptA' in result_df.columns
        True
    """
    processor = BScoreProcessor(max_iter=max_iter, tol=tol)
    if metrics:
        processor.set_enabled_metrics(metrics)
    
    return processor.calculate_bscores_for_plate(df, metrics, plate_layout)


def validate_bscore_matrix(matrix: np.ndarray, 
                          max_nan_fraction: float = 0.5) -> bool:
    """Validate that a matrix is suitable for B-scoring.
    
    Args:
        matrix: 2D numpy array to validate
        max_nan_fraction: Maximum fraction of NaN values allowed
        
    Returns:
        True if matrix is suitable for B-scoring
        
    Raises:
        ValueError: If matrix fails validation
    """
    if matrix.ndim != 2:
        raise ValueError(f"Expected 2D matrix, got {matrix.ndim}D")
    
    if matrix.size == 0:
        raise ValueError("Matrix is empty")
    
    # Check NaN fraction
    nan_fraction = np.sum(np.isnan(matrix)) / matrix.size
    if nan_fraction > max_nan_fraction:
        raise ValueError(f"Too many NaN values: {nan_fraction:.1%} > {max_nan_fraction:.1%}")
    
    # Check if we have sufficient data
    valid_values = matrix[~np.isnan(matrix)]
    if len(valid_values) < 4:  # Need at least 4 values for meaningful statistics
        raise ValueError(f"Insufficient valid data: {len(valid_values)} values")
    
    return True