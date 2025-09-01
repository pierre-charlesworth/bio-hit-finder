"""Vitality analysis module for dual-readout screening.

This module implements vitality hit detection based on growth pattern analysis
of bacterial strains (WT, tolC, SA) using OD measurements normalized to plate
medians. Vitality hits are identified by the pattern: tolC≤0.8 AND WT>0.8 AND SA>0.8.

Classes:
    VitalityAnalyzer: Main class for vitality analysis and hit detection
    VitalityError: Custom exception for vitality analysis errors

Functions:
    calculate_plate_medians: Calculate medians for strain measurements
    calculate_od_percentages: Convert OD values to percentage of median
    detect_vitality_hits: Identify vitality hits based on growth patterns
"""

from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class VitalityError(Exception):
    """Custom exception for vitality analysis errors."""
    pass


@dataclass
class VitalityConfig:
    """Configuration for vitality analysis parameters."""
    tolc_threshold: float = 0.8  # tolC% threshold (≤ for hits)
    wt_threshold: float = 0.8    # WT% threshold (> for hits) 
    sa_threshold: float = 0.8    # SA% threshold (> for hits)
    min_od_value: float = 0.001  # Minimum OD value to avoid division issues


class VitalityAnalyzer:
    """Vitality analysis for dual-readout screening.
    
    Implements growth pattern analysis based on OD measurements from
    three bacterial strains (WT, tolC, SA). Calculates plate medians,
    normalizes OD values to percentages, and identifies vitality hits.
    
    Attributes:
        config: VitalityConfig with analysis parameters
    """
    
    def __init__(self, config: Optional[VitalityConfig] = None):
        """Initialize VitalityAnalyzer.
        
        Args:
            config: VitalityConfig object, uses defaults if None
        """
        self.config = config or VitalityConfig()
        
    def calculate_plate_medians(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate plate medians from experimental OD data.
        
        Calculates median OD values for each strain (WT, tolC, SA) from
        experimental measurements, excluding any summary/calculated rows.
        
        Args:
            df: DataFrame with OD columns (OD_WT, OD_tolC, OD_SA)
            
        Returns:
            Dict with strain medians: {'WT_med': float, 'tolC_med': float, 'SA_med': float}
            
        Raises:
            VitalityError: If required OD columns are missing or invalid
        """
        required_columns = ['OD_WT', 'OD_tolC', 'OD_SA']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            raise VitalityError(f"Missing required OD columns: {missing_cols}")
            
        # Use only experimental data (exclude summary rows if present)
        if 'Well_Type' in df.columns:
            experimental_data = df[df['Well_Type'] == 'experimental'].copy()
            if experimental_data.empty:
                experimental_data = df.copy()  # Fallback if no experimental data found
        else:
            experimental_data = df.copy()  # No Well_Type column, use all data
            
        # Calculate medians, handling NaN values
        medians = {}
        for strain in ['WT', 'tolC', 'SA']:
            col = f'OD_{strain}'
            values = experimental_data[col].dropna()
            
            if len(values) == 0:
                raise VitalityError(f"No valid OD values found for strain {strain}")
                
            # Apply minimum threshold to avoid zero/negative values
            values = values[values >= self.config.min_od_value]
            
            if len(values) == 0:
                logger.warning(f"All OD values for {strain} below minimum threshold {self.config.min_od_value}")
                medians[f'{strain}_med'] = self.config.min_od_value
            else:
                medians[f'{strain}_med'] = values.median()
                
        logger.info(f"Calculated plate medians: {medians}")
        return medians
        
    def calculate_od_percentages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate OD percentages relative to plate medians.
        
        Converts absolute OD measurements to percentages of plate median
        for each strain: WT% = OD_WT/WT_med, etc.
        
        Args:
            df: DataFrame with OD measurements
            
        Returns:
            DataFrame with added percentage columns (WT%, tolC%, SA%)
            
        Raises:
            VitalityError: If median calculation fails
        """
        df_result = df.copy()
        
        # Calculate plate medians
        medians = self.calculate_plate_medians(df)
        
        # Calculate percentages for each strain
        for strain in ['WT', 'tolC', 'SA']:
            od_col = f'OD_{strain}'
            pct_col = f'{strain}%'
            median_val = medians[f'{strain}_med']
            
            if median_val <= 0:
                raise VitalityError(f"Invalid median for {strain}: {median_val}")
                
            # Calculate percentage, handling NaN values
            df_result[pct_col] = df_result[od_col] / median_val
            
            # Cap extreme values to avoid outlier issues
            df_result[pct_col] = df_result[pct_col].clip(0, 5.0)  # Cap at 500%
            
        logger.info("Calculated OD percentages for all strains")
        return df_result
        
    def detect_vitality_hits(self, df: pd.DataFrame, config: Optional[VitalityConfig] = None) -> pd.DataFrame:
        """Detect vitality hits based on growth patterns.
        
        Identifies vitality hits using the pattern:
        tolC% ≤ threshold AND WT% > threshold AND SA% > threshold
        
        Args:
            df: DataFrame with OD percentage columns
            config: Optional VitalityConfig, uses instance config if None
            
        Returns:
            DataFrame with added VitalityHit boolean column
            
        Raises:
            VitalityError: If required percentage columns are missing
        """
        config = config or self.config
        df_result = df.copy()
        
        # Ensure percentage columns exist
        required_pct_cols = ['WT%', 'tolC%', 'SA%']
        if not all(col in df_result.columns for col in required_pct_cols):
            df_result = self.calculate_od_percentages(df_result)
            
        # Apply vitality hit criteria
        vitality_conditions = (
            (df_result['tolC%'] <= config.tolc_threshold) &
            (df_result['WT%'] > config.wt_threshold) & 
            (df_result['SA%'] > config.sa_threshold)
        )
        
        df_result['VitalityHit'] = vitality_conditions
        
        # Add vitality pattern classification
        df_result['VitalityPattern'] = self._classify_vitality_pattern(df_result, config)
        
        hit_count = df_result['VitalityHit'].sum()
        total_wells = len(df_result)
        logger.info(f"Detected {hit_count} vitality hits out of {total_wells} wells ({hit_count/total_wells:.1%})")
        
        return df_result
        
    def _classify_vitality_pattern(self, df: pd.DataFrame, config: VitalityConfig) -> pd.Series:
        """Classify vitality patterns for each well.
        
        Args:
            df: DataFrame with percentage columns
            config: VitalityConfig with thresholds
            
        Returns:
            Series with pattern classifications
        """
        def classify_pattern(row):
            tolc_low = row['tolC%'] <= config.tolc_threshold
            wt_high = row['WT%'] > config.wt_threshold
            sa_high = row['SA%'] > config.sa_threshold
            
            if tolc_low and wt_high and sa_high:
                return 'VitalityHit'
            elif tolc_low and wt_high:
                return 'PartialVitality_WT'
            elif tolc_low and sa_high:
                return 'PartialVitality_SA'
            elif tolc_low:
                return 'tolC_Sensitive'
            elif wt_high and sa_high:
                return 'HighGrowth_Both'
            else:
                return 'No_Pattern'
                
        return df.apply(classify_pattern, axis=1)
        
    def generate_vitality_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for vitality analysis.
        
        Args:
            df: DataFrame with vitality analysis results
            
        Returns:
            Dict with summary statistics and metrics
        """
        if 'VitalityHit' not in df.columns:
            df = self.detect_vitality_hits(df)
            
        total_wells = len(df)
        vitality_hits = df['VitalityHit'].sum()
        
        # Pattern distribution
        pattern_counts = df['VitalityPattern'].value_counts().to_dict()
        
        # OD percentage statistics
        pct_stats = {}
        for strain in ['WT', 'tolC', 'SA']:
            col = f'{strain}%'
            if col in df.columns:
                pct_stats[f'{strain}_pct'] = {
                    'median': df[col].median(),
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        
        # Threshold compliance
        threshold_stats = {
            'tolC_below_threshold': (df['tolC%'] <= self.config.tolc_threshold).sum(),
            'WT_above_threshold': (df['WT%'] > self.config.wt_threshold).sum(),
            'SA_above_threshold': (df['SA%'] > self.config.sa_threshold).sum()
        }
        
        summary = {
            'total_wells': total_wells,
            'vitality_hits': int(vitality_hits),
            'vitality_hit_rate': vitality_hits / total_wells if total_wells > 0 else 0,
            'pattern_distribution': pattern_counts,
            'percentage_statistics': pct_stats,
            'threshold_compliance': threshold_stats,
            'config_used': {
                'tolc_threshold': self.config.tolc_threshold,
                'wt_threshold': self.config.wt_threshold,
                'sa_threshold': self.config.sa_threshold
            }
        }
        
        return summary


# Convenience functions for standalone use
def calculate_plate_medians(df: pd.DataFrame, min_od_value: float = 0.001) -> Dict[str, float]:
    """Calculate plate medians using default VitalityAnalyzer."""
    analyzer = VitalityAnalyzer(VitalityConfig(min_od_value=min_od_value))
    return analyzer.calculate_plate_medians(df)


def calculate_od_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate OD percentages using default VitalityAnalyzer."""
    analyzer = VitalityAnalyzer()
    return analyzer.calculate_od_percentages(df)


def detect_vitality_hits(df: pd.DataFrame, config: Optional[VitalityConfig] = None) -> pd.DataFrame:
    """Detect vitality hits using default VitalityAnalyzer."""
    analyzer = VitalityAnalyzer(config)
    return analyzer.detect_vitality_hits(df)