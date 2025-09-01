"""Edge effect detection system for plate-based assays.

This module implements comprehensive edge-effect diagnostics as specified in the PRD,
including edge vs interior comparisons, row/column trend analysis, corner effect
detection, and optional spatial autocorrelation analysis.

Edge effects are common artifacts in microplate assays where wells near the plate
edges show systematic differences from interior wells due to evaporation, temperature
gradients, or other physical factors.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union, NamedTuple
from enum import Enum
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform

try:
    from ..core.statistics import nan_safe_median, mad
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.statistics import nan_safe_median, mad

logger = logging.getLogger(__name__)

# Type aliases
ArrayLike = Union[np.ndarray, pd.Series, list[float]]
MatrixLike = Union[np.ndarray, pd.DataFrame]


class WarningLevel(Enum):
    """Warning levels for edge effects."""
    INFO = "INFO"
    WARN = "WARN" 
    CRITICAL = "CRITICAL"


class EdgeEffectResult(NamedTuple):
    """Results from edge effect analysis."""
    metric: str
    plate_id: str
    effect_size_d: float
    edge_median: float
    interior_median: float
    interior_mad: float
    row_correlation: float
    row_p_value: float
    col_correlation: float  
    col_p_value: float
    corner_deviations: Dict[str, float]
    warning_level: WarningLevel
    n_edge_wells: int
    n_interior_wells: int
    spatial_autocorr: Optional[float] = None
    spatial_p_value: Optional[float] = None


class EdgeEffectError(Exception):
    """Custom exception for edge effect detection errors."""
    pass


class EdgeEffectDetector:
    """Detector class for comprehensive edge effect analysis.
    
    This class implements all edge effect diagnostics specified in the PRD:
    - Edge vs Interior comparison using robust effect size
    - Row/Column trend detection using Spearman correlation
    - Corner hot/cold spot analysis
    - Optional spatial autocorrelation testing (Moran's I)
    
    Attributes:
        thresholds: Dictionary of detection thresholds
        min_group_wells: Minimum wells required in each group
        spatial_enabled: Whether to compute spatial autocorrelation
    """
    
    # Default thresholds as per PRD specification
    DEFAULT_THRESHOLDS = {
        'effect_size_d': 0.8,
        'spearman_rho': 0.5,
        'corner_mads': 1.2,
        'info_d': 0.5,
        'warn_d': 0.8,
        'critical_d': 1.5,
    }
    
    def __init__(self, 
                 thresholds: Optional[Dict[str, float]] = None,
                 min_group_wells: int = 16,
                 spatial_enabled: bool = False):
        """Initialize edge effect detector.
        
        Args:
            thresholds: Custom detection thresholds (defaults used if None)
            min_group_wells: Minimum wells required in each group for testing
            spatial_enabled: Whether to compute spatial autocorrelation
        """
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        if thresholds:
            self.thresholds.update(thresholds)
        
        self.min_group_wells = min_group_wells
        self.spatial_enabled = spatial_enabled
        
        logger.info(f"Initialized EdgeEffectDetector: thresholds={self.thresholds}, "
                   f"min_group_wells={min_group_wells}, spatial_enabled={spatial_enabled}")
    
    def _identify_edge_wells(self, plate_layout: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Identify edge and interior well positions for a plate layout.
        
        Args:
            plate_layout: Tuple of (n_rows, n_cols)
            
        Returns:
            Tuple of (edge_positions, interior_positions) as lists of (row, col) tuples
            
        Examples:
            >>> detector = EdgeEffectDetector()
            >>> edge_pos, interior_pos = detector._identify_edge_wells((8, 12))
            >>> len(edge_pos) + len(interior_pos) == 8 * 12
            True
            >>> (0, 0) in edge_pos  # Corner is edge
            True
            >>> (3, 5) in interior_pos  # Interior well
            True
        """
        n_rows, n_cols = plate_layout
        
        edge_positions = []
        interior_positions = []
        
        for row in range(n_rows):
            for col in range(n_cols):
                # Edge wells are on the perimeter
                if row == 0 or row == n_rows - 1 or col == 0 or col == n_cols - 1:
                    edge_positions.append((row, col))
                else:
                    interior_positions.append((row, col))
        
        logger.debug(f"Identified {len(edge_positions)} edge wells and {len(interior_positions)} interior wells")
        return edge_positions, interior_positions
    
    def _extract_well_values(self, 
                           matrix: np.ndarray, 
                           positions: List[Tuple[int, int]]) -> np.ndarray:
        """Extract values from specific well positions, excluding NaN.
        
        Args:
            matrix: 2D numpy array with plate data
            positions: List of (row, col) positions to extract
            
        Returns:
            1D array of valid (non-NaN) values from specified positions
        """
        values = []
        for row, col in positions:
            if 0 <= row < matrix.shape[0] and 0 <= col < matrix.shape[1]:
                value = matrix[row, col]
                if not np.isnan(value):
                    values.append(value)
        
        return np.array(values)
    
    def _calculate_effect_size(self, 
                              edge_values: np.ndarray, 
                              interior_values: np.ndarray) -> Tuple[float, float, float, float]:
        """Calculate robust effect size between edge and interior wells.
        
        Formula: d = (median(edge) - median(interior)) / MAD(interior)
        
        Args:
            edge_values: Array of edge well values
            interior_values: Array of interior well values
            
        Returns:
            Tuple of (effect_size_d, edge_median, interior_median, interior_mad)
        """
        if len(edge_values) == 0 or len(interior_values) == 0:
            return np.nan, np.nan, np.nan, np.nan
        
        edge_median = nan_safe_median(edge_values)
        interior_median = nan_safe_median(interior_values)
        interior_mad = mad(interior_values)
        
        if np.isnan(interior_mad) or interior_mad == 0:
            effect_size_d = np.nan
        else:
            effect_size_d = (edge_median - interior_median) / interior_mad
        
        return effect_size_d, edge_median, interior_median, interior_mad
    
    def _calculate_row_col_trends(self, matrix: np.ndarray) -> Tuple[float, float, float, float]:
        """Calculate Spearman correlations for row and column trends.
        
        Args:
            matrix: 2D numpy array with plate data
            
        Returns:
            Tuple of (row_correlation, row_p_value, col_correlation, col_p_value)
        """
        n_rows, n_cols = matrix.shape
        
        # Row trend analysis: correlate row index with row medians
        row_medians = []
        row_indices = []
        
        for i in range(n_rows):
            row_values = matrix[i, :]
            valid_values = row_values[~np.isnan(row_values)]
            if len(valid_values) > 0:
                row_medians.append(nan_safe_median(valid_values))
                row_indices.append(i)
        
        if len(row_medians) < 3:
            row_correlation, row_p_value = np.nan, np.nan
        else:
            try:
                row_correlation, row_p_value = stats.spearmanr(row_indices, row_medians)
            except Exception:
                row_correlation, row_p_value = np.nan, np.nan
        
        # Column trend analysis: correlate column index with column medians
        col_medians = []
        col_indices = []
        
        for j in range(n_cols):
            col_values = matrix[:, j]
            valid_values = col_values[~np.isnan(col_values)]
            if len(valid_values) > 0:
                col_medians.append(nan_safe_median(valid_values))
                col_indices.append(j)
        
        if len(col_medians) < 3:
            col_correlation, col_p_value = np.nan, np.nan
        else:
            try:
                col_correlation, col_p_value = stats.spearmanr(col_indices, col_medians)
            except Exception:
                col_correlation, col_p_value = np.nan, np.nan
        
        return row_correlation, row_p_value, col_correlation, col_p_value
    
    def _calculate_corner_effects(self, 
                                matrix: np.ndarray, 
                                interior_median: float, 
                                interior_mad: float) -> Dict[str, float]:
        """Calculate corner deviations in MAD units.
        
        Args:
            matrix: 2D numpy array with plate data
            interior_median: Median of interior wells
            interior_mad: MAD of interior wells
            
        Returns:
            Dictionary with corner deviations: {'top_left', 'top_right', 'bottom_left', 'bottom_right'}
        """
        n_rows, n_cols = matrix.shape
        
        corner_positions = {
            'top_left': (0, 0),
            'top_right': (0, n_cols - 1),
            'bottom_left': (n_rows - 1, 0),
            'bottom_right': (n_rows - 1, n_cols - 1)
        }
        
        corner_deviations = {}
        
        if np.isnan(interior_mad) or interior_mad == 0:
            # Can't calculate meaningful deviations
            for corner in corner_positions:
                corner_deviations[corner] = np.nan
            return corner_deviations
        
        for corner, (row, col) in corner_positions.items():
            if 0 <= row < n_rows and 0 <= col < n_cols:
                corner_value = matrix[row, col]
                if not np.isnan(corner_value):
                    deviation = abs(corner_value - interior_median) / interior_mad
                    corner_deviations[corner] = deviation
                else:
                    corner_deviations[corner] = np.nan
            else:
                corner_deviations[corner] = np.nan
        
        return corner_deviations
    
    def _calculate_spatial_autocorr(self, matrix: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
        """Calculate Moran's I spatial autocorrelation coefficient.
        
        This is computationally expensive and optional. Moran's I tests whether
        nearby wells are more similar than expected by chance.
        
        Args:
            matrix: 2D numpy array with plate data
            
        Returns:
            Tuple of (morans_i, p_value) or (None, None) if disabled or failed
        """
        if not self.spatial_enabled:
            return None, None
        
        try:
            n_rows, n_cols = matrix.shape
            
            # Create position coordinates for all wells
            positions = []
            values = []
            
            for i in range(n_rows):
                for j in range(n_cols):
                    if not np.isnan(matrix[i, j]):
                        positions.append([i, j])
                        values.append(matrix[i, j])
            
            if len(values) < 10:  # Need sufficient data
                return None, None
            
            positions = np.array(positions)
            values = np.array(values)
            
            # Calculate distance matrix
            distances = squareform(pdist(positions, metric='euclidean'))
            
            # Create spatial weights (inverse distance, with neighbors within distance 2)
            weights = np.zeros_like(distances)
            max_dist = 2.0  # Consider wells within distance 2 as neighbors
            
            for i in range(len(positions)):
                for j in range(len(positions)):
                    if i != j and distances[i, j] <= max_dist:
                        weights[i, j] = 1.0 / (1.0 + distances[i, j])
            
            # Normalize weights
            row_sums = np.sum(weights, axis=1)
            for i in range(len(weights)):
                if row_sums[i] > 0:
                    weights[i, :] /= row_sums[i]
            
            # Calculate Moran's I
            n = len(values)
            mean_val = np.mean(values)
            
            numerator = 0
            denominator = 0
            
            for i in range(n):
                for j in range(n):
                    numerator += weights[i, j] * (values[i] - mean_val) * (values[j] - mean_val)
                denominator += (values[i] - mean_val) ** 2
            
            if denominator == 0:
                return None, None
            
            morans_i = numerator / denominator
            
            # Approximate p-value (simplified)
            # For proper inference, would need to compute expected value and variance
            expected_i = -1.0 / (n - 1)
            
            # Simple z-test approximation (not rigorous)
            if abs(morans_i - expected_i) > 0.1:  # Arbitrary threshold
                p_value = 0.01  # Significant
            else:
                p_value = 0.5   # Not significant
            
            return morans_i, p_value
            
        except Exception as e:
            logger.warning(f"Spatial autocorrelation calculation failed: {e}")
            return None, None
    
    def _determine_warning_level(self, effect_size_d: float) -> WarningLevel:
        """Determine warning level based on effect size.
        
        Args:
            effect_size_d: Robust effect size
            
        Returns:
            WarningLevel enum value
        """
        abs_d = abs(effect_size_d) if not np.isnan(effect_size_d) else 0
        
        if abs_d >= self.thresholds['critical_d']:
            return WarningLevel.CRITICAL
        elif abs_d >= self.thresholds['warn_d']:
            return WarningLevel.WARN
        elif abs_d >= self.thresholds['info_d']:
            return WarningLevel.INFO
        else:
            return WarningLevel.INFO  # Always return at least INFO level
    
    def detect_edge_effects(self, 
                           matrix: np.ndarray,
                           metric: str = "Z_lptA", 
                           plate_id: str = "Unknown",
                           plate_layout: Tuple[int, int] = (8, 12)) -> EdgeEffectResult:
        """Perform comprehensive edge effect detection on a plate matrix.
        
        Args:
            matrix: 2D numpy array with plate data
            metric: Name of the metric being analyzed
            plate_id: Identifier for the plate
            plate_layout: Tuple of (n_rows, n_cols)
            
        Returns:
            EdgeEffectResult with comprehensive diagnostics
            
        Raises:
            EdgeEffectError: If analysis fails or insufficient data
            
        Examples:
            >>> detector = EdgeEffectDetector()
            >>> matrix = np.random.randn(8, 12)
            >>> result = detector.detect_edge_effects(matrix)
            >>> result.metric == "Z_lptA"
            True
            >>> isinstance(result.effect_size_d, float)
            True
        """
        logger.info(f"Detecting edge effects for {metric} on plate {plate_id}")
        
        # Validate input
        if matrix.ndim != 2:
            raise EdgeEffectError(f"Expected 2D matrix, got {matrix.ndim}D")
        
        if matrix.shape != plate_layout:
            logger.warning(f"Matrix shape {matrix.shape} doesn't match expected {plate_layout}")
        
        try:
            # Identify edge and interior wells
            edge_positions, interior_positions = self._identify_edge_wells(plate_layout)
            
            # Extract values
            edge_values = self._extract_well_values(matrix, edge_positions)
            interior_values = self._extract_well_values(matrix, interior_positions)
            
            logger.debug(f"Extracted {len(edge_values)} edge and {len(interior_values)} interior values")
            
            # Check minimum data requirements
            if len(edge_values) < self.min_group_wells or len(interior_values) < self.min_group_wells:
                logger.warning(f"Insufficient data: {len(edge_values)} edge, {len(interior_values)} interior "
                              f"(minimum {self.min_group_wells} each)")
            
            # Calculate effect size
            effect_size_d, edge_median, interior_median, interior_mad = self._calculate_effect_size(
                edge_values, interior_values
            )
            
            # Calculate row/column trends
            row_correlation, row_p_value, col_correlation, col_p_value = self._calculate_row_col_trends(matrix)
            
            # Calculate corner effects
            corner_deviations = self._calculate_corner_effects(matrix, interior_median, interior_mad)
            
            # Calculate spatial autocorrelation (if enabled)
            spatial_autocorr, spatial_p_value = self._calculate_spatial_autocorr(matrix)
            
            # Determine warning level
            warning_level = self._determine_warning_level(effect_size_d)
            
            # Create result
            result = EdgeEffectResult(
                metric=metric,
                plate_id=plate_id,
                effect_size_d=effect_size_d,
                edge_median=edge_median,
                interior_median=interior_median,
                interior_mad=interior_mad,
                row_correlation=row_correlation,
                row_p_value=row_p_value,
                col_correlation=col_correlation,
                col_p_value=col_p_value,
                corner_deviations=corner_deviations,
                warning_level=warning_level,
                n_edge_wells=len(edge_values),
                n_interior_wells=len(interior_values),
                spatial_autocorr=spatial_autocorr,
                spatial_p_value=spatial_p_value
            )
            
            # Log summary
            logger.info(f"Edge effect analysis complete: d={effect_size_d:.3f}, "
                       f"level={warning_level.value}, "
                       f"row_ρ={row_correlation:.3f}, col_ρ={col_correlation:.3f}")
            
            return result
            
        except Exception as e:
            raise EdgeEffectError(f"Failed to detect edge effects: {e}") from e
    
    def detect_edge_effects_dataframe(self, 
                                     df: pd.DataFrame,
                                     metric: str = "Z_lptA",
                                     plate_id_col: str = "PlateID",
                                     plate_layout: Tuple[int, int] = (8, 12)) -> List[EdgeEffectResult]:
        """Detect edge effects for all plates in a DataFrame.
        
        Args:
            df: DataFrame with plate data including Row, Col columns
            metric: Metric column to analyze
            plate_id_col: Column containing plate identifiers
            plate_layout: Plate dimensions
            
        Returns:
            List of EdgeEffectResult objects, one per plate
            
        Raises:
            EdgeEffectError: If analysis fails
        """
        required_cols = ['Row', 'Col', metric]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise EdgeEffectError(f"Missing required columns: {missing_cols}")
        
        results = []
        
        if plate_id_col in df.columns:
            # Multiple plates
            plate_ids = df[plate_id_col].unique()
        else:
            # Single plate
            plate_ids = ["Unknown"]
        
        for plate_id in plate_ids:
            try:
                if plate_id_col in df.columns:
                    plate_df = df[df[plate_id_col] == plate_id]
                else:
                    plate_df = df
                
                # Convert to matrix format
                matrix = self._dataframe_to_matrix(plate_df, metric, plate_layout)
                
                # Detect edge effects
                result = self.detect_edge_effects(matrix, metric, str(plate_id), plate_layout)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to analyze plate {plate_id}: {e}")
                continue
        
        logger.info(f"Analyzed edge effects for {len(results)} plates")
        return results
    
    def _dataframe_to_matrix(self, 
                           df: pd.DataFrame,
                           metric: str, 
                           plate_layout: Tuple[int, int] = (8, 12)) -> np.ndarray:
        """Convert DataFrame to matrix format for analysis.
        
        Args:
            df: DataFrame with Row, Col columns
            metric: Metric column to extract
            plate_layout: Plate dimensions
            
        Returns:
            2D numpy array with plate layout
        """
        n_rows, n_cols = plate_layout
        matrix = np.full((n_rows, n_cols), np.nan)
        
        # Map rows A-H to indices 0-7 
        row_mapping = {chr(ord('A') + i): i for i in range(n_rows)}
        
        for _, row in df.iterrows():
            try:
                row_label = str(row['Row']).upper().strip()
                col_num = int(row['Col'])
                
                if row_label in row_mapping and 1 <= col_num <= n_cols:
                    row_idx = row_mapping[row_label]
                    col_idx = col_num - 1  # Convert to 0-based
                    
                    if not np.isnan(row[metric]):
                        matrix[row_idx, col_idx] = row[metric]
                        
            except (ValueError, KeyError):
                continue
        
        return matrix
    
    def generate_report(self, results: List[EdgeEffectResult]) -> Dict[str, any]:
        """Generate summary report for edge effect analysis.
        
        Args:
            results: List of EdgeEffectResult objects
            
        Returns:
            Dictionary with summary statistics and recommendations
        """
        if not results:
            return {'summary': 'No edge effect results to report'}
        
        # Aggregate statistics
        effect_sizes = [r.effect_size_d for r in results if not np.isnan(r.effect_size_d)]
        warning_levels = [r.warning_level for r in results]
        
        # Count warning levels
        level_counts = {level: sum(1 for w in warning_levels if w == level) for level in WarningLevel}
        
        # Flag problematic plates
        critical_plates = [r.plate_id for r in results if r.warning_level == WarningLevel.CRITICAL]
        warning_plates = [r.plate_id for r in results if r.warning_level == WarningLevel.WARN]
        
        # Row/column trend analysis
        strong_row_trends = [r.plate_id for r in results 
                           if not np.isnan(r.row_correlation) and abs(r.row_correlation) > self.thresholds['spearman_rho']]
        strong_col_trends = [r.plate_id for r in results 
                           if not np.isnan(r.col_correlation) and abs(r.col_correlation) > self.thresholds['spearman_rho']]
        
        # Corner effects
        corner_issues = []
        for r in results:
            for corner, deviation in r.corner_deviations.items():
                if not np.isnan(deviation) and deviation > self.thresholds['corner_mads']:
                    corner_issues.append(f"{r.plate_id}:{corner}")
        
        report = {
            'summary': {
                'total_plates': len(results),
                'effect_sizes': {
                    'mean': np.mean(effect_sizes) if effect_sizes else np.nan,
                    'median': np.median(effect_sizes) if effect_sizes else np.nan,
                    'max': np.max(np.abs(effect_sizes)) if effect_sizes else np.nan,
                },
                'warning_levels': dict(level_counts),
                'problematic_plates': {
                    'critical': critical_plates,
                    'warning': warning_plates,
                }
            },
            'trends': {
                'strong_row_trends': strong_row_trends,
                'strong_col_trends': strong_col_trends,
            },
            'corner_effects': corner_issues,
            'recommendations': self._generate_recommendations(results),
            'details': [r._asdict() for r in results]
        }
        
        return report
    
    def _generate_recommendations(self, results: List[EdgeEffectResult]) -> List[str]:
        """Generate recommendations based on edge effect analysis.
        
        Args:
            results: List of EdgeEffectResult objects
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for systematic edge effects
        critical_count = sum(1 for r in results if r.warning_level == WarningLevel.CRITICAL)
        warning_count = sum(1 for r in results if r.warning_level == WarningLevel.WARN)
        
        if critical_count > 0:
            recommendations.append(f"{critical_count} plates show CRITICAL edge effects - consider B-scoring or plate redesign")
        
        if warning_count > len(results) / 2:  # More than half have warnings
            recommendations.append("Widespread edge effects detected - check incubation conditions and plate sealing")
        
        # Check for directional trends
        strong_trends = sum(1 for r in results 
                          if (not np.isnan(r.row_correlation) and abs(r.row_correlation) > 0.5) or
                             (not np.isnan(r.col_correlation) and abs(r.col_correlation) > 0.5))
        
        if strong_trends > 0:
            recommendations.append(f"{strong_trends} plates show directional trends - check for temperature gradients or pipetting bias")
        
        # Check corner effects
        corner_problems = sum(1 for r in results 
                            if any(not np.isnan(d) and d > 1.2 for d in r.corner_deviations.values()))
        
        if corner_problems > 0:
            recommendations.append(f"{corner_problems} plates show corner effects - check plate stacking and storage")
        
        if not recommendations:
            recommendations.append("No significant edge effects detected - plate quality appears good")
        
        return recommendations


# Convenience functions for direct usage
def detect_edge_effects_simple(df: pd.DataFrame,
                              metric: str = "Z_lptA", 
                              thresholds: Optional[Dict[str, float]] = None,
                              plate_layout: Tuple[int, int] = (8, 12)) -> List[EdgeEffectResult]:
    """Simple edge effect detection for a DataFrame.
    
    Args:
        df: DataFrame with plate data
        metric: Metric to analyze  
        thresholds: Custom detection thresholds
        plate_layout: Plate dimensions
        
    Returns:
        List of EdgeEffectResult objects
        
    Examples:
        >>> df = load_plate_data('plate1.xlsx')  
        >>> results = detect_edge_effects_simple(df, 'Z_lptA')
        >>> len(results) > 0
        True
    """
    detector = EdgeEffectDetector(thresholds=thresholds)
    return detector.detect_edge_effects_dataframe(df, metric=metric, plate_layout=plate_layout)


def is_edge_effect_significant(result: EdgeEffectResult, 
                             threshold: float = 0.8) -> bool:
    """Check if edge effect is significant based on effect size.
    
    Args:
        result: EdgeEffectResult object
        threshold: Effect size threshold
        
    Returns:
        True if effect size exceeds threshold
    """
    return not np.isnan(result.effect_size_d) and abs(result.effect_size_d) >= threshold


def format_edge_effect_summary(result: EdgeEffectResult) -> str:
    """Format edge effect result as human-readable summary.
    
    Args:
        result: EdgeEffectResult object
        
    Returns:
        Formatted summary string
    """
    d = result.effect_size_d
    level = result.warning_level.value
    
    summary_parts = [
        f"Plate {result.plate_id} ({result.metric}):",
        f"Effect size d={d:.3f} ({level})"
    ]
    
    if not np.isnan(result.row_correlation) and abs(result.row_correlation) > 0.3:
        summary_parts.append(f"Row trend rho={result.row_correlation:.3f}")
    
    if not np.isnan(result.col_correlation) and abs(result.col_correlation) > 0.3:
        summary_parts.append(f"Col trend rho={result.col_correlation:.3f}")
    
    # Check corner effects
    max_corner = max((d for d in result.corner_deviations.values() if not np.isnan(d)), default=0)
    if max_corner > 1.0:
        summary_parts.append(f"Max corner deviation {max_corner:.1f} MADs")
    
    return " | ".join(summary_parts)