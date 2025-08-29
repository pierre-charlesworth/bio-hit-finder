"""Integration module connecting core processing with advanced analytics.

This module provides enhanced plate processing capabilities that integrate
B-scoring and edge effect detection with the standard calculation pipeline.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union
import warnings

import pandas as pd
import numpy as np

from .plate_processor import PlateProcessor, PlateProcessingError
try:
    from ..analytics import (
        BScoreProcessor, 
        EdgeEffectDetector,
        EdgeEffectResult,
        WarningLevel,
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from analytics import (
        BScoreProcessor, 
        EdgeEffectDetector,
        EdgeEffectResult,
        WarningLevel,
    )

logger = logging.getLogger(__name__)


class AdvancedPlateProcessor(PlateProcessor):
    """Enhanced PlateProcessor with B-scoring and edge effect detection.
    
    This class extends the standard PlateProcessor to include:
    - Automatic B-score calculation for bias correction
    - Edge effect detection and warnings
    - Quality control diagnostics
    - Configurable analytics parameters
    
    Attributes:
        bscore_enabled: Whether to calculate B-scores
        edge_detection_enabled: Whether to detect edge effects
        bscore_processor: BScoreProcessor instance
        edge_detector: EdgeEffectDetector instance
        analytics_results: Dictionary storing analytics results
    """
    
    def __init__(self, 
                 viability_threshold: float = 0.3,
                 bscore_enabled: bool = False,
                 edge_detection_enabled: bool = True,
                 bscore_config: Optional[Dict] = None,
                 edge_config: Optional[Dict] = None):
        """Initialize AdvancedPlateProcessor.
        
        Args:
            viability_threshold: Threshold for viability gating
            bscore_enabled: Whether to calculate B-scores
            edge_detection_enabled: Whether to detect edge effects
            bscore_config: Configuration for B-score processor
            edge_config: Configuration for edge effect detector
        """
        super().__init__(viability_threshold=viability_threshold)
        
        self.bscore_enabled = bscore_enabled
        self.edge_detection_enabled = edge_detection_enabled
        
        # Initialize analytics processors
        bscore_config = bscore_config or {}
        self.bscore_processor = BScoreProcessor(**bscore_config)
        
        edge_config = edge_config or {}
        self.edge_detector = EdgeEffectDetector(**edge_config)
        
        # Storage for analytics results
        self.analytics_results = {
            'edge_effects': {},
            'bscore_summaries': {},
        }
        
        logger.info(f"Initialized AdvancedPlateProcessor: "
                   f"bscore_enabled={bscore_enabled}, "
                   f"edge_detection_enabled={edge_detection_enabled}")
    
    def process_single_plate(self, 
                           df: pd.DataFrame, 
                           plate_id: str,
                           plate_layout: Tuple[int, int] = (8, 12)) -> pd.DataFrame:
        """Process a single plate with advanced analytics.
        
        Args:
            df: DataFrame with raw plate data
            plate_id: Identifier for this plate
            plate_layout: Plate dimensions (rows, cols)
            
        Returns:
            DataFrame with all calculated metrics including B-scores
            
        Raises:
            PlateProcessingError: If processing fails
        """
        logger.info(f"Processing plate {plate_id} with advanced analytics")
        
        try:
            # Standard processing pipeline
            processed_df = super().process_single_plate(df, plate_id)
            
            # Add required position columns if missing
            processed_df = self._ensure_position_columns(processed_df, plate_layout)
            
            # Apply B-scoring if enabled
            if self.bscore_enabled:
                processed_df = self._apply_bscoring(processed_df, plate_id, plate_layout)
            
            # Detect edge effects if enabled
            if self.edge_detection_enabled:
                self._detect_edge_effects(processed_df, plate_id, plate_layout)
            
            logger.info(f"Advanced processing complete for plate {plate_id}")
            return processed_df
            
        except Exception as e:
            if isinstance(e, PlateProcessingError):
                raise
            raise PlateProcessingError(f"Failed advanced processing for plate {plate_id}: {e}") from e
    
    def _ensure_position_columns(self, 
                                df: pd.DataFrame, 
                                plate_layout: Tuple[int, int]) -> pd.DataFrame:
        """Ensure Row and Col columns exist in DataFrame.
        
        Args:
            df: DataFrame to check
            plate_layout: Plate dimensions
            
        Returns:
            DataFrame with Row and Col columns
        """
        if 'Row' in df.columns and 'Col' in df.columns:
            return df
        
        # Generate Row and Col columns based on index
        n_rows, n_cols = plate_layout
        result_df = df.copy()
        
        if len(df) != n_rows * n_cols:
            logger.warning(f"DataFrame length {len(df)} doesn't match expected "
                          f"plate layout {n_rows}x{n_cols}={n_rows*n_cols}")
        
        # Generate positions assuming row-major order (A1, A2, ..., A12, B1, B2, ...)
        rows = []
        cols = []
        
        for i in range(len(df)):
            row_idx = i // n_cols
            col_idx = i % n_cols
            
            # Convert to plate notation
            if row_idx < n_rows:
                row_letter = chr(ord('A') + row_idx)
                col_number = col_idx + 1
            else:
                # Fallback for excess rows
                row_letter = 'Z'
                col_number = 1
            
            rows.append(row_letter)
            cols.append(col_number)
        
        result_df['Row'] = rows
        result_df['Col'] = cols
        
        logger.debug(f"Generated Row/Col columns for {len(df)} wells")
        return result_df
    
    def _apply_bscoring(self, 
                       df: pd.DataFrame, 
                       plate_id: str,
                       plate_layout: Tuple[int, int]) -> pd.DataFrame:
        """Apply B-scoring to the processed DataFrame.
        
        Args:
            df: DataFrame with processed plate data
            plate_id: Plate identifier
            plate_layout: Plate dimensions
            
        Returns:
            DataFrame with B-score columns added
        """
        logger.debug(f"Applying B-scoring to plate {plate_id}")
        
        try:
            result_df = self.bscore_processor.calculate_bscores_for_plate(
                df, plate_layout=plate_layout
            )
            
            # Store summary for reporting
            summary = self.bscore_processor.get_processing_summary()
            self.analytics_results['bscore_summaries'][plate_id] = summary
            
            logger.info(f"B-scores calculated for plate {plate_id}: "
                       f"{len(summary['enabled_metrics'])} metrics processed")
            
            return result_df
            
        except Exception as e:
            logger.error(f"B-scoring failed for plate {plate_id}: {e}")
            # Continue processing without B-scores
            return df
    
    def _detect_edge_effects(self, 
                           df: pd.DataFrame, 
                           plate_id: str,
                           plate_layout: Tuple[int, int]) -> None:
        """Detect edge effects for the plate.
        
        Args:
            df: DataFrame with processed plate data
            plate_id: Plate identifier
            plate_layout: Plate dimensions
        """
        logger.debug(f"Detecting edge effects for plate {plate_id}")
        
        try:
            # Determine which metric to use for edge detection
            edge_metric = self._select_edge_detection_metric(df)
            
            if edge_metric is None:
                logger.warning(f"No suitable metric found for edge detection on plate {plate_id}")
                return
            
            # Perform edge effect detection
            results = self.edge_detector.detect_edge_effects_dataframe(
                df, 
                metric=edge_metric, 
                plate_id_col='PlateID',
                plate_layout=plate_layout
            )
            
            if results:
                result = results[0]  # Single plate result
                self.analytics_results['edge_effects'][plate_id] = result
                
                # Log warnings based on severity
                if result.warning_level == WarningLevel.CRITICAL:
                    logger.warning(f"CRITICAL edge effects detected on plate {plate_id}: "
                                 f"d={result.effect_size_d:.3f}")
                elif result.warning_level == WarningLevel.WARN:
                    logger.warning(f"Significant edge effects detected on plate {plate_id}: "
                                 f"d={result.effect_size_d:.3f}")
                else:
                    logger.info(f"Edge effects analysis complete for plate {plate_id}: "
                              f"d={result.effect_size_d:.3f} (no significant effects)")
            
        except Exception as e:
            logger.error(f"Edge effect detection failed for plate {plate_id}: {e}")
            # Continue processing without edge detection
    
    def _select_edge_detection_metric(self, df: pd.DataFrame) -> Optional[str]:
        """Select the best metric for edge effect detection.
        
        Args:
            df: DataFrame with plate data
            
        Returns:
            Name of metric column to use, or None if no suitable metric found
        """
        # Priority order for edge detection metrics
        preferred_metrics = ['Z_lptA', 'Z_ldtD', 'Ratio_lptA', 'Ratio_ldtD']
        
        for metric in preferred_metrics:
            if metric in df.columns and df[metric].count() > 50:  # Sufficient valid data
                return metric
        
        # Fallback: any numeric column with sufficient data
        for col in df.columns:
            if (df[col].dtype in [np.float64, np.int64] and 
                df[col].count() > 50 and 
                col not in ['PlateID', 'Row', 'Col']):
                logger.debug(f"Using fallback metric {col} for edge detection")
                return col
        
        return None
    
    def configure_bscoring(self, 
                          enabled: bool = True,
                          metrics: Optional[List[str]] = None,
                          **kwargs) -> None:
        """Configure B-scoring parameters.
        
        Args:
            enabled: Whether to enable B-scoring
            metrics: List of metrics to apply B-scoring to
            **kwargs: Additional parameters for BScoreProcessor
        """
        self.bscore_enabled = enabled
        
        if metrics:
            self.bscore_processor.set_enabled_metrics(metrics)
        
        # Update processor parameters if provided
        for param, value in kwargs.items():
            if hasattr(self.bscore_processor, param):
                setattr(self.bscore_processor, param, value)
        
        logger.info(f"B-scoring configuration updated: enabled={enabled}, "
                   f"metrics={self.bscore_processor.enabled_metrics}")
    
    def configure_edge_detection(self, 
                               enabled: bool = True,
                               **kwargs) -> None:
        """Configure edge effect detection parameters.
        
        Args:
            enabled: Whether to enable edge detection
            **kwargs: Additional parameters for EdgeEffectDetector
        """
        self.edge_detection_enabled = enabled
        
        # Update detector parameters if provided
        for param, value in kwargs.items():
            if hasattr(self.edge_detector, param):
                setattr(self.edge_detector, param, value)
        
        logger.info(f"Edge detection configuration updated: enabled={enabled}")
    
    def get_edge_effect_summary(self) -> Dict:
        """Get summary of edge effects across all processed plates.
        
        Returns:
            Dictionary with edge effect summary and recommendations
        """
        edge_results = list(self.analytics_results['edge_effects'].values())
        
        if not edge_results:
            return {'summary': 'No edge effect analysis performed'}
        
        return self.edge_detector.generate_report(edge_results)
    
    def get_analytics_summary(self) -> Dict:
        """Get comprehensive analytics summary.
        
        Returns:
            Dictionary with all analytics results and summaries
        """
        summary = super().get_processing_summary()
        
        # Add analytics information
        summary.update({
            'analytics_enabled': {
                'bscore': self.bscore_enabled,
                'edge_detection': self.edge_detection_enabled,
            },
            'edge_effects': {
                'analyzed_plates': len(self.analytics_results['edge_effects']),
                'warnings': self._count_edge_warnings(),
                'summary': self.get_edge_effect_summary(),
            },
            'bscoring': {
                'processed_plates': len(self.analytics_results['bscore_summaries']),
                'enabled_metrics': self.bscore_processor.enabled_metrics if self.bscore_enabled else [],
            }
        })
        
        return summary
    
    def _count_edge_warnings(self) -> Dict[str, int]:
        """Count edge effect warnings by severity level.
        
        Returns:
            Dictionary with warning counts by level
        """
        counts = {level.value: 0 for level in WarningLevel}
        
        for result in self.analytics_results['edge_effects'].values():
            counts[result.warning_level.value] += 1
        
        return counts
    
    def reset(self) -> None:
        """Reset processor state including analytics results."""
        super().reset()
        self.analytics_results = {'edge_effects': {}, 'bscore_summaries': {}}
        self.bscore_processor.clear_cache()
        logger.info("Advanced processor state reset")


def create_advanced_processor_from_config(config: Dict) -> AdvancedPlateProcessor:
    """Create AdvancedPlateProcessor from configuration dictionary.
    
    Args:
        config: Configuration dictionary with processing parameters
        
    Returns:
        Configured AdvancedPlateProcessor instance
        
    Examples:
        >>> config = {
        ...     'viability_threshold': 0.3,
        ...     'bscore_enabled': True,
        ...     'bscore_config': {'max_iter': 15, 'tol': 1e-7},
        ...     'edge_config': {'spatial_enabled': False}
        ... }
        >>> processor = create_advanced_processor_from_config(config)
    """
    return AdvancedPlateProcessor(
        viability_threshold=config.get('viability_threshold', 0.3),
        bscore_enabled=config.get('bscore_enabled', False),
        edge_detection_enabled=config.get('edge_detection_enabled', True),
        bscore_config=config.get('bscore_config', {}),
        edge_config=config.get('edge_config', {}),
    )


def apply_analytics_to_existing_data(df: pd.DataFrame,
                                   bscore_enabled: bool = False,
                                   edge_detection_enabled: bool = True,
                                   plate_layout: Tuple[int, int] = (8, 12),
                                   **kwargs) -> Tuple[pd.DataFrame, Dict]:
    """Apply analytics to already-processed plate data.
    
    Args:
        df: DataFrame with processed plate data
        bscore_enabled: Whether to calculate B-scores
        edge_detection_enabled: Whether to detect edge effects
        plate_layout: Plate dimensions
        **kwargs: Additional configuration parameters
        
    Returns:
        Tuple of (enhanced_dataframe, analytics_results)
        
    Examples:
        >>> processed_df = load_processed_plate_data()
        >>> enhanced_df, results = apply_analytics_to_existing_data(
        ...     processed_df, bscore_enabled=True
        ... )
    """
    processor = AdvancedPlateProcessor(
        bscore_enabled=bscore_enabled,
        edge_detection_enabled=edge_detection_enabled,
        **kwargs
    )
    
    # Ensure position columns exist
    if 'Row' not in df.columns or 'Col' not in df.columns:
        df = processor._ensure_position_columns(df, plate_layout)
    
    # Determine plate ID
    plate_id = df.get('PlateID', 'Unknown').iloc[0] if 'PlateID' in df.columns else 'Unknown'
    
    enhanced_df = df.copy()
    
    # Apply B-scoring
    if bscore_enabled:
        enhanced_df = processor._apply_bscoring(enhanced_df, plate_id, plate_layout)
    
    # Detect edge effects
    if edge_detection_enabled:
        processor._detect_edge_effects(enhanced_df, plate_id, plate_layout)
    
    # Get analytics results
    analytics_results = {
        'edge_effects': processor.analytics_results['edge_effects'],
        'bscore_summaries': processor.analytics_results['bscore_summaries'],
    }
    
    return enhanced_df, analytics_results