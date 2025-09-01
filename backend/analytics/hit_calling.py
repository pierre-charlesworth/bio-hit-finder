"""Hit calling analytics for dual-readout compound screening.

This module provides high-level analytics functions for multi-stage hit calling
workflows, including reporter hit analysis, vitality pattern assessment, and
platform hit identification. It builds on the core calculation functions to
provide aggregated metrics and visualization support.

Functions for the Streamlit UI and analysis workflows.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from core.calculations import (
    process_multi_stage_hit_calling,
    calculate_od_percentages,
    apply_reporter_hit_gate,
    apply_vitality_hit_gate,
    apply_platform_hit_gate,
)

logger = logging.getLogger(__name__)

# Type aliases
ArrayLike = Union[np.ndarray, pd.Series, List[float]]


class HitCallingError(Exception):
    """Custom exception for hit calling analysis errors."""
    pass


class HitCallingAnalyzer:
    """Advanced analytics for multi-stage hit calling workflows.
    
    This class provides comprehensive analysis of dual-readout screening data,
    including stage-wise hit identification, pattern analysis, and quality metrics.
    
    Attributes:
        config: Hit calling configuration parameters
        stage_results: Dictionary containing results from each hit calling stage
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize HitCallingAnalyzer.
        
        Args:
            config: Hit calling configuration dictionary
        """
        self.config = config or {}
        self.stage_results: Dict[str, pd.DataFrame] = {}
        
        logger.info("Initialized HitCallingAnalyzer")
    
    def analyze_plate_hits(self, df: pd.DataFrame) -> dict:
        """Comprehensive hit calling analysis for a single plate.
        
        Args:
            df: Processed plate DataFrame with all calculated metrics
            
        Returns:
            Dictionary containing hit calling summary and stage-wise results
            
        Raises:
            HitCallingError: If required columns are missing or analysis fails
        """
        logger.info("Starting comprehensive hit calling analysis")
        
        # Validate required columns for hit calling
        required_cols = ['Z_lptA', 'Z_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA', 'viability_ok_lptA', 'viability_ok_ldtD']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HitCallingError(f"Missing required columns for hit calling: {missing_cols}")
        
        # Apply multi-stage hit calling if enabled
        if self.config.get('hit_calling', {}).get('multi_stage_enabled', False):
            analyzed_df = process_multi_stage_hit_calling(df.copy(), self.config)
        else:
            # Apply each stage individually for analysis
            analyzed_df = df.copy()
            analyzed_df = calculate_od_percentages(analyzed_df)
            analyzed_df = apply_reporter_hit_gate(analyzed_df, self.config)
            analyzed_df = apply_vitality_hit_gate(analyzed_df, self.config)
            analyzed_df = apply_platform_hit_gate(analyzed_df)
        
        # Store stage results
        self.stage_results['full'] = analyzed_df
        
        # Calculate summary statistics
        summary = self._calculate_hit_summary(analyzed_df)
        
        # Analyze hit patterns
        patterns = self._analyze_hit_patterns(analyzed_df)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(analyzed_df)
        
        result = {
            'summary': summary,
            'patterns': patterns,
            'quality_metrics': quality_metrics,
            'analyzed_data': analyzed_df,
        }
        
        logger.info(f"Hit calling analysis complete: {summary['total_wells']} wells analyzed")
        
        return result
    
    def _calculate_hit_summary(self, df: pd.DataFrame) -> dict:
        """Calculate hit calling summary statistics.
        
        Args:
            df: DataFrame with hit calling results
            
        Returns:
            Dictionary with hit counts and percentages
        """
        total_wells = len(df)
        
        summary = {
            'total_wells': total_wells,
            'viable_wells': df['viability_ok_lptA'].sum() + df['viability_ok_ldtD'].sum(),
        }
        
        # Reporter hits
        if 'reporter_hit' in df.columns:
            reporter_hits = df['reporter_hit'].sum()
            summary.update({
                'reporter_hits': int(reporter_hits),
                'reporter_hit_rate': float(reporter_hits / total_wells) if total_wells > 0 else 0.0,
            })
        
        # Vitality hits
        if 'vitality_hit' in df.columns:
            vitality_hits = df['vitality_hit'].sum()
            summary.update({
                'vitality_hits': int(vitality_hits),
                'vitality_hit_rate': float(vitality_hits / total_wells) if total_wells > 0 else 0.0,
            })
        
        # Platform hits
        if 'platform_hit' in df.columns:
            platform_hits = df['platform_hit'].sum()
            summary.update({
                'platform_hits': int(platform_hits),
                'platform_hit_rate': float(platform_hits / total_wells) if total_wells > 0 else 0.0,
            })
        
        # OD percentages summary
        if all(col in df.columns for col in ['WT%', 'tolC%', 'SA%']):
            summary.update({
                'mean_wt_percent': float(df['WT%'].mean()),
                'mean_tolc_percent': float(df['tolC%'].mean()),
                'mean_sa_percent': float(df['SA%'].mean()),
            })
        
        return summary
    
    def _analyze_hit_patterns(self, df: pd.DataFrame) -> dict:
        """Analyze patterns in hit calling results.
        
        Args:
            df: DataFrame with hit calling results
            
        Returns:
            Dictionary with pattern analysis results
        """
        patterns = {}
        
        # Check if we have hit calling columns
        hit_cols = ['reporter_hit', 'vitality_hit', 'platform_hit']
        available_hit_cols = [col for col in hit_cols if col in df.columns]
        
        if not available_hit_cols:
            return patterns
        
        # Stage overlap analysis
        if 'reporter_hit' in df.columns and 'vitality_hit' in df.columns:
            reporter_only = df['reporter_hit'] & ~df['vitality_hit']
            vitality_only = df['vitality_hit'] & ~df['reporter_hit']
            both_stages = df['reporter_hit'] & df['vitality_hit']
            
            patterns.update({
                'reporter_only': int(reporter_only.sum()),
                'vitality_only': int(vitality_only.sum()),
                'both_reporter_vitality': int(both_stages.sum()),
                'overlap_rate': float(both_stages.sum() / max(df['reporter_hit'].sum(), 1)),
            })
        
        # Z-score distribution analysis for hits
        if 'reporter_hit' in df.columns:
            hit_wells = df[df['reporter_hit']]
            if len(hit_wells) > 0:
                patterns.update({
                    'hit_z_lptA_median': float(hit_wells['Z_lptA'].median()),
                    'hit_z_ldtD_median': float(hit_wells['Z_ldtD'].median()),
                    'hit_z_lptA_max': float(hit_wells['Z_lptA'].max()),
                    'hit_z_ldtD_max': float(hit_wells['Z_ldtD'].max()),
                })
        
        # Vitality pattern analysis
        if 'vitality_hit' in df.columns and all(col in df.columns for col in ['WT%', 'tolC%', 'SA%']):
            vitality_wells = df[df['vitality_hit']]
            if len(vitality_wells) > 0:
                patterns.update({
                    'vitality_wt_median': float(vitality_wells['WT%'].median()),
                    'vitality_tolc_median': float(vitality_wells['tolC%'].median()),
                    'vitality_sa_median': float(vitality_wells['SA%'].median()),
                })
        
        return patterns
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> dict:
        """Calculate quality metrics for hit calling performance.
        
        Args:
            df: DataFrame with hit calling results
            
        Returns:
            Dictionary with quality metrics
        """
        quality = {}
        
        # Viability assessment
        total_wells = len(df)
        if total_wells > 0:
            viable_lptA = df['viability_ok_lptA'].sum() if 'viability_ok_lptA' in df.columns else 0
            viable_ldtD = df['viability_ok_ldtD'].sum() if 'viability_ok_ldtD' in df.columns else 0
            
            quality.update({
                'viability_rate_lptA': float(viable_lptA / total_wells),
                'viability_rate_ldtD': float(viable_ldtD / total_wells),
                'overall_viability': float((viable_lptA + viable_ldtD) / (2 * total_wells)),
            })
        
        # Hit calling consistency
        if all(col in df.columns for col in ['reporter_hit', 'vitality_hit', 'platform_hit']):
            # Check logical consistency (platform hits should be subset of both reporter and vitality)
            reporter_hits = df['reporter_hit'].sum()
            vitality_hits = df['vitality_hit'].sum()
            platform_hits = df['platform_hit'].sum()
            
            expected_platform = df['reporter_hit'] & df['vitality_hit']
            actual_platform = df['platform_hit']
            consistency = (expected_platform == actual_platform).sum() / total_wells
            
            quality.update({
                'hit_consistency': float(consistency),
                'platform_reporter_ratio': float(platform_hits / max(reporter_hits, 1)),
                'platform_vitality_ratio': float(platform_hits / max(vitality_hits, 1)),
            })
        
        # Z-score quality assessment
        z_cols = ['Z_lptA', 'Z_ldtD']
        available_z_cols = [col for col in z_cols if col in df.columns]
        
        for z_col in available_z_cols:
            z_values = df[z_col].dropna()
            if len(z_values) > 0:
                quality.update({
                    f'{z_col.lower()}_range': float(z_values.max() - z_values.min()),
                    f'{z_col.lower()}_std': float(z_values.std()),
                    f'{z_col.lower()}_dynamic_range': float(abs(z_values.quantile(0.95) - z_values.quantile(0.05))),
                })
        
        return quality
    
    def get_hit_summary_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate a summary table of hit calling results by stage.
        
        Args:
            df: DataFrame with hit calling results
            
        Returns:
            Summary DataFrame with hit counts by stage
        """
        stages = []
        
        # Basic statistics
        total_wells = len(df)
        viable_wells = 0
        if 'viability_ok_lptA' in df.columns and 'viability_ok_ldtD' in df.columns:
            viable_wells = (df['viability_ok_lptA'] | df['viability_ok_ldtD']).sum()
        
        stages.append({
            'Stage': 'Total',
            'Description': 'All wells in plate',
            'Hit_Count': total_wells,
            'Hit_Rate': 1.0,
            'Notes': 'Baseline'
        })
        
        stages.append({
            'Stage': 'Viable',
            'Description': 'Wells passing viability gate',
            'Hit_Count': int(viable_wells),
            'Hit_Rate': float(viable_wells / max(total_wells, 1)),
            'Notes': 'ATP-based viability filter'
        })
        
        # Reporter hits
        if 'reporter_hit' in df.columns:
            reporter_hits = df['reporter_hit'].sum()
            stages.append({
                'Stage': 'Reporter',
                'Description': 'Z-score ≥ 2.0 AND viable',
                'Hit_Count': int(reporter_hits),
                'Hit_Rate': float(reporter_hits / max(total_wells, 1)),
                'Notes': 'lptA OR ldtD activity'
            })
        
        # Vitality hits
        if 'vitality_hit' in df.columns:
            vitality_hits = df['vitality_hit'].sum()
            stages.append({
                'Stage': 'Vitality',
                'Description': 'Growth pattern analysis',
                'Hit_Count': int(vitality_hits),
                'Hit_Rate': float(vitality_hits / max(total_wells, 1)),
                'Notes': 'tolC≤80%, WT>80%, SA>80%'
            })
        
        # Platform hits
        if 'platform_hit' in df.columns:
            platform_hits = df['platform_hit'].sum()
            stages.append({
                'Stage': 'Platform',
                'Description': 'Reporter AND Vitality',
                'Hit_Count': int(platform_hits),
                'Hit_Rate': float(platform_hits / max(total_wells, 1)),
                'Notes': 'Final compound hits'
            })
        
        return pd.DataFrame(stages)


def analyze_multi_plate_hits(plate_data: dict[str, pd.DataFrame], 
                           config: Optional[dict] = None) -> dict:
    """Analyze hit calling results across multiple plates.
    
    Args:
        plate_data: Dictionary mapping plate IDs to processed DataFrames
        config: Hit calling configuration
        
    Returns:
        Dictionary with cross-plate hit calling analysis
        
    Examples:
        >>> plates = {'P1': df1, 'P2': df2}
        >>> results = analyze_multi_plate_hits(plates)
        >>> results['total_platform_hits']
        42
    """
    logger.info(f"Analyzing hit calling across {len(plate_data)} plates")
    
    analyzer = HitCallingAnalyzer(config)
    
    plate_analyses = {}
    combined_summaries = []
    
    # Analyze each plate individually
    for plate_id, df in plate_data.items():
        try:
            analysis = analyzer.analyze_plate_hits(df)
            plate_analyses[plate_id] = analysis
            
            # Add plate ID to summary for aggregation
            summary = analysis['summary'].copy()
            summary['plate_id'] = plate_id
            combined_summaries.append(summary)
            
        except Exception as e:
            logger.error(f"Failed to analyze plate {plate_id}: {e}")
            continue
    
    # Aggregate cross-plate statistics
    if combined_summaries:
        summary_df = pd.DataFrame(combined_summaries)
        
        cross_plate_summary = {
            'total_plates': len(plate_analyses),
            'total_wells': summary_df['total_wells'].sum(),
            'total_reporter_hits': summary_df.get('reporter_hits', pd.Series([0])).sum(),
            'total_vitality_hits': summary_df.get('vitality_hits', pd.Series([0])).sum(),
            'total_platform_hits': summary_df.get('platform_hits', pd.Series([0])).sum(),
            'mean_reporter_hit_rate': summary_df.get('reporter_hit_rate', pd.Series([0])).mean(),
            'mean_vitality_hit_rate': summary_df.get('vitality_hit_rate', pd.Series([0])).mean(),
            'mean_platform_hit_rate': summary_df.get('platform_hit_rate', pd.Series([0])).mean(),
        }
    else:
        cross_plate_summary = {}
    
    result = {
        'cross_plate_summary': cross_plate_summary,
        'plate_analyses': plate_analyses,
        'summary_table': pd.DataFrame(combined_summaries) if combined_summaries else pd.DataFrame(),
    }
    
    logger.info(f"Multi-plate analysis complete: {len(plate_analyses)} plates processed")
    
    return result


def format_hit_calling_report(analysis_results: dict) -> str:
    """Format hit calling analysis results into a text report.
    
    Args:
        analysis_results: Results from analyze_plate_hits or analyze_multi_plate_hits
        
    Returns:
        Formatted text report string
    """
    lines = []
    lines.append("=== Hit Calling Analysis Report ===\n")
    
    # Handle single plate or multi-plate results
    if 'cross_plate_summary' in analysis_results:
        # Multi-plate report
        summary = analysis_results['cross_plate_summary']
        lines.append(f"Multi-Plate Analysis ({summary.get('total_plates', 0)} plates)")
        lines.append(f"Total Wells: {summary.get('total_wells', 0):,}")
        lines.append(f"Platform Hits: {summary.get('total_platform_hits', 0):,} "
                    f"({summary.get('mean_platform_hit_rate', 0):.1%} average rate)")
        lines.append(f"Reporter Hits: {summary.get('total_reporter_hits', 0):,} "
                    f"({summary.get('mean_reporter_hit_rate', 0):.1%} average rate)")
        lines.append(f"Vitality Hits: {summary.get('total_vitality_hits', 0):,} "
                    f"({summary.get('mean_vitality_hit_rate', 0):.1%} average rate)")
        
    else:
        # Single plate report
        summary = analysis_results.get('summary', {})
        lines.append(f"Single Plate Analysis")
        lines.append(f"Total Wells: {summary.get('total_wells', 0):,}")
        
        if 'platform_hits' in summary:
            lines.append(f"Platform Hits: {summary['platform_hits']:,} "
                        f"({summary.get('platform_hit_rate', 0):.1%})")
        
        if 'reporter_hits' in summary:
            lines.append(f"Reporter Hits: {summary['reporter_hits']:,} "
                        f"({summary.get('reporter_hit_rate', 0):.1%})")
                        
        if 'vitality_hits' in summary:
            lines.append(f"Vitality Hits: {summary['vitality_hits']:,} "
                        f"({summary.get('vitality_hit_rate', 0):.1%})")
    
    # Quality metrics
    if 'quality_metrics' in analysis_results:
        quality = analysis_results['quality_metrics']
        lines.append(f"\nQuality Metrics:")
        
        if 'overall_viability' in quality:
            lines.append(f"Overall Viability: {quality['overall_viability']:.1%}")
            
        if 'hit_consistency' in quality:
            lines.append(f"Hit Consistency: {quality['hit_consistency']:.1%}")
    
    # Pattern analysis
    if 'patterns' in analysis_results:
        patterns = analysis_results['patterns']
        lines.append(f"\nHit Patterns:")
        
        if 'overlap_rate' in patterns:
            lines.append(f"Reporter/Vitality Overlap: {patterns['overlap_rate']:.1%}")
            
        if 'both_reporter_vitality' in patterns:
            lines.append(f"Wells hitting both stages: {patterns['both_reporter_vitality']:,}")
    
    return '\n'.join(lines)