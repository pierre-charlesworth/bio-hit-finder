"""Multi-stage hit calling for dual-readout screening platform.

This module implements a three-stage hit calling pipeline:
- Stage 1: Reporter hits (Z≥threshold AND PassViab)
- Stage 2: Vitality hits (growth pattern analysis)  
- Stage 3: Platform hits (Stage1 AND Stage2)

Classes:
    MultiStageHitCaller: Main class for multi-stage hit analysis
    MultiStageConfig: Configuration for hit calling parameters
    MultiStageError: Custom exception for multi-stage analysis errors
    
Functions:
    stage1_reporter_hits: Identify reporter-based hits
    stage2_vitality_hits: Identify vitality-based hits
    stage3_platform_hits: Identify combined platform hits
"""

from typing import Dict, Any, Optional, List, Tuple, Union
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging

from .vitality_analysis import VitalityAnalyzer, VitalityConfig, VitalityError

logger = logging.getLogger(__name__)


class MultiStageError(Exception):
    """Custom exception for multi-stage hit calling errors."""
    pass


@dataclass
class MultiStageConfig:
    """Configuration for multi-stage hit calling parameters."""
    
    # Stage 1: Reporter hit parameters
    z_threshold: float = 2.0          # Z-score threshold for reporter hits
    viability_column: str = 'PassViab' # Column name for viability flags
    reporter_columns: List[str] = None  # Reporter Z-score columns (auto-detect if None)
    
    # Stage 2: Vitality hit parameters  
    vitality_config: VitalityConfig = None
    
    # Stage 3: Platform hit parameters
    require_both_stages: bool = True   # True: AND logic, False: OR logic
    
    # Analysis options
    include_partial_hits: bool = True  # Include partial reporter/vitality hits in output
    min_wells_for_analysis: int = 10   # Minimum wells required for analysis
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.reporter_columns is None:
            self.reporter_columns = ['Z_lptA', 'Z_ldtD']  # Default reporter columns
        if self.vitality_config is None:
            self.vitality_config = VitalityConfig()


class MultiStageHitCaller:
    """Multi-stage hit calling for dual-readout screening.
    
    Implements a three-stage pipeline for comprehensive hit identification:
    1. Reporter hits: Z-score based detection with viability gating
    2. Vitality hits: Growth pattern analysis across bacterial strains
    3. Platform hits: Combined analysis requiring both reporter and vitality signals
    
    Attributes:
        config: MultiStageConfig with analysis parameters
        vitality_analyzer: VitalityAnalyzer instance for Stage 2 analysis
    """
    
    def __init__(self, config: Optional[MultiStageConfig] = None):
        """Initialize MultiStageHitCaller.
        
        Args:
            config: MultiStageConfig object, uses defaults if None
        """
        self.config = config or MultiStageConfig()
        self.vitality_analyzer = VitalityAnalyzer(self.config.vitality_config)
        
    def stage1_reporter_hits(self, df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> pd.DataFrame:
        """Identify Stage 1 reporter hits based on Z-scores and viability.
        
        Reporter hits are defined as wells with:
        - Z-score ≥ threshold for any reporter gene AND
        - PassViab = True (viable)
        
        Args:
            df: DataFrame with Z-score columns and viability flags
            config: Optional MultiStageConfig, uses instance config if None
            
        Returns:
            DataFrame with added Stage1_ReporterHit and related columns
            
        Raises:
            MultiStageError: If required columns are missing
        """
        config = config or self.config
        df_result = df.copy()
        
        # Validate required columns
        missing_cols = []
        for col in config.reporter_columns:
            if col not in df_result.columns:
                missing_cols.append(col)
        if config.viability_column not in df_result.columns:
            missing_cols.append(config.viability_column)
            
        if missing_cols:
            raise MultiStageError(f"Missing required columns for Stage 1: {missing_cols}")
            
        # Calculate reporter hits for each gene
        reporter_hits = pd.DataFrame(index=df_result.index)
        
        for col in config.reporter_columns:
            gene_name = col.replace('Z_', '')  # Extract gene name (lptA, ldtD, etc.)
            hit_col = f'{gene_name}_ReporterHit'
            
            # Z-score threshold AND viability requirement
            reporter_hits[hit_col] = (
                (df_result[col] >= config.z_threshold) & 
                (df_result[config.viability_column] == True)
            )
            
            # Add Z-score information for hits
            df_result[f'{gene_name}_ZScore'] = df_result[col]
            df_result[hit_col] = reporter_hits[hit_col]
        
        # Stage 1 overall hit: any reporter hit
        df_result['Stage1_ReporterHit'] = reporter_hits.any(axis=1)
        
        # Add summary columns
        df_result['Stage1_HitCount'] = reporter_hits.sum(axis=1)
        df_result['Stage1_MaxZ'] = df_result[config.reporter_columns].max(axis=1)
        
        hit_count = df_result['Stage1_ReporterHit'].sum()
        total_wells = len(df_result)
        logger.info(f"Stage 1: {hit_count} reporter hits out of {total_wells} wells ({hit_count/total_wells:.1%})")
        
        return df_result
        
    def stage2_vitality_hits(self, df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> pd.DataFrame:
        """Identify Stage 2 vitality hits based on growth patterns.
        
        Uses VitalityAnalyzer to detect hits based on bacterial strain growth patterns:
        tolC% ≤ threshold AND WT% > threshold AND SA% > threshold
        
        Args:
            df: DataFrame with OD measurements for WT, tolC, SA strains
            config: Optional MultiStageConfig, uses instance config if None
            
        Returns:
            DataFrame with added Stage2_VitalityHit and related columns
            
        Raises:
            MultiStageError: If vitality analysis fails
        """
        config = config or self.config
        df_result = df.copy()
        
        try:
            # Perform vitality analysis
            df_result = self.vitality_analyzer.detect_vitality_hits(df_result, config.vitality_config)
            
            # Map vitality results to Stage 2 columns
            df_result['Stage2_VitalityHit'] = df_result['VitalityHit']
            df_result['Stage2_Pattern'] = df_result['VitalityPattern']
            
            # Add OD percentage summary for hits
            if all(col in df_result.columns for col in ['WT%', 'tolC%', 'SA%']):
                df_result['Stage2_tolC_pct'] = df_result['tolC%']
                df_result['Stage2_WT_pct'] = df_result['WT%']
                df_result['Stage2_SA_pct'] = df_result['SA%']
            
            hit_count = df_result['Stage2_VitalityHit'].sum()
            total_wells = len(df_result)
            logger.info(f"Stage 2: {hit_count} vitality hits out of {total_wells} wells ({hit_count/total_wells:.1%})")
            
        except VitalityError as e:
            raise MultiStageError(f"Stage 2 vitality analysis failed: {str(e)}")
            
        return df_result
        
    def stage3_platform_hits(self, df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> pd.DataFrame:
        """Identify Stage 3 platform hits combining reporter and vitality signals.
        
        Platform hits are defined as wells meeting both Stage 1 and Stage 2 criteria
        (when require_both_stages=True) or either criteria (when False).
        
        Args:
            df: DataFrame with Stage 1 and Stage 2 results
            config: Optional MultiStageConfig, uses instance config if None
            
        Returns:
            DataFrame with added Stage3_PlatformHit and related columns
            
        Raises:
            MultiStageError: If required stage columns are missing
        """
        config = config or self.config
        df_result = df.copy()
        
        # Validate required columns from previous stages
        required_cols = ['Stage1_ReporterHit', 'Stage2_VitalityHit']
        missing_cols = [col for col in required_cols if col not in df_result.columns]
        
        if missing_cols:
            raise MultiStageError(f"Missing required columns for Stage 3: {missing_cols}. Run Stage 1 and 2 first.")
        
        # Calculate platform hits based on logic
        if config.require_both_stages:
            # AND logic: both reporter AND vitality hits required
            df_result['Stage3_PlatformHit'] = (
                df_result['Stage1_ReporterHit'] & 
                df_result['Stage2_VitalityHit']
            )
            logic_description = "Stage1 AND Stage2"
        else:
            # OR logic: either reporter OR vitality hits sufficient
            df_result['Stage3_PlatformHit'] = (
                df_result['Stage1_ReporterHit'] | 
                df_result['Stage2_VitalityHit']
            )
            logic_description = "Stage1 OR Stage2"
        
        # Add hit classification
        df_result['Stage3_HitType'] = df_result.apply(
            lambda row: self._classify_platform_hit(row), axis=1
        )
        
        # Add confidence scoring
        df_result['Stage3_Confidence'] = df_result.apply(
            lambda row: self._calculate_hit_confidence(row), axis=1
        )
        
        hit_count = df_result['Stage3_PlatformHit'].sum()
        total_wells = len(df_result)
        logger.info(f"Stage 3: {hit_count} platform hits out of {total_wells} wells ({hit_count/total_wells:.1%}) using {logic_description} logic")
        
        return df_result
    
    def _classify_platform_hit(self, row: pd.Series) -> str:
        """Classify the type of platform hit based on stage results."""
        stage1 = row.get('Stage1_ReporterHit', False)
        stage2 = row.get('Stage2_VitalityHit', False) 
        stage3 = row.get('Stage3_PlatformHit', False)
        
        if stage3 and stage1 and stage2:
            return 'PlatformHit_Both'
        elif stage3 and stage1:
            return 'PlatformHit_ReporterOnly'
        elif stage3 and stage2:
            return 'PlatformHit_VitalityOnly'
        elif stage1:
            return 'ReporterHit_NoVitality'
        elif stage2:
            return 'VitalityHit_NoReporter'
        else:
            return 'NoHit'
    
    def _calculate_hit_confidence(self, row: pd.Series) -> float:
        """Calculate confidence score for platform hits based on signal strength."""
        confidence = 0.0
        
        # Reporter signal contribution (0-0.5)
        if row.get('Stage1_ReporterHit', False):
            max_z = row.get('Stage1_MaxZ', 0)
            # Normalize Z-score contribution (cap at Z=10 for 0.5 confidence)
            confidence += min(max_z / 20.0, 0.5)
        
        # Vitality signal contribution (0-0.5)
        if row.get('Stage2_VitalityHit', False):
            # Use tolC suppression strength as vitality confidence
            tolc_pct = row.get('Stage2_tolC_pct', 1.0)
            vitality_strength = max(0, (0.8 - tolc_pct) / 0.8)  # Stronger suppression = higher confidence
            confidence += vitality_strength * 0.5
        
        return min(confidence, 1.0)  # Cap at 1.0
        
    def generate_hit_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive hit summary statistics.
        
        Args:
            df: DataFrame with multi-stage analysis results
            
        Returns:
            Dict with summary statistics for all stages
        """
        total_wells = len(df)
        
        summary = {
            'total_wells': total_wells,
            'stage1_reporter_hits': int(df.get('Stage1_ReporterHit', pd.Series([False])).sum()),
            'stage2_vitality_hits': int(df.get('Stage2_VitalityHit', pd.Series([False])).sum()),
            'stage3_platform_hits': int(df.get('Stage3_PlatformHit', pd.Series([False])).sum()),
        }
        
        # Calculate hit rates
        for stage in ['stage1_reporter_hits', 'stage2_vitality_hits', 'stage3_platform_hits']:
            rate_key = stage.replace('hits', 'hit_rate')
            summary[rate_key] = summary[stage] / total_wells if total_wells > 0 else 0
        
        # Hit type distribution
        if 'Stage3_HitType' in df.columns:
            summary['hit_type_distribution'] = df['Stage3_HitType'].value_counts().to_dict()
        
        # Confidence statistics
        if 'Stage3_Confidence' in df.columns:
            confidence_values = df[df['Stage3_PlatformHit'] == True]['Stage3_Confidence']
            if len(confidence_values) > 0:
                summary['confidence_stats'] = {
                    'mean': confidence_values.mean(),
                    'median': confidence_values.median(),
                    'min': confidence_values.min(),
                    'max': confidence_values.max(),
                    'high_confidence_count': (confidence_values >= 0.8).sum()
                }
        
        # Stage overlap analysis
        if all(col in df.columns for col in ['Stage1_ReporterHit', 'Stage2_VitalityHit']):
            summary['stage_overlap'] = {
                'both_stages': int((df['Stage1_ReporterHit'] & df['Stage2_VitalityHit']).sum()),
                'reporter_only': int((df['Stage1_ReporterHit'] & ~df['Stage2_VitalityHit']).sum()),
                'vitality_only': int((~df['Stage1_ReporterHit'] & df['Stage2_VitalityHit']).sum()),
                'neither_stage': int((~df['Stage1_ReporterHit'] & ~df['Stage2_VitalityHit']).sum())
            }
        
        # Configuration used
        summary['config_used'] = {
            'z_threshold': self.config.z_threshold,
            'vitality_thresholds': {
                'tolc': self.config.vitality_config.tolc_threshold,
                'wt': self.config.vitality_config.wt_threshold,
                'sa': self.config.vitality_config.sa_threshold
            },
            'require_both_stages': self.config.require_both_stages
        }
        
        return summary
        
    def run_full_analysis(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Run complete three-stage hit calling analysis.
        
        Args:
            df: DataFrame with raw plate data
            
        Returns:
            Tuple of (results_dataframe, summary_dict)
            
        Raises:
            MultiStageError: If analysis fails at any stage
        """
        if len(df) < self.config.min_wells_for_analysis:
            raise MultiStageError(f"Insufficient wells for analysis: {len(df)} < {self.config.min_wells_for_analysis}")
        
        logger.info(f"Starting multi-stage analysis on {len(df)} wells")
        
        try:
            # Stage 1: Reporter hits
            df_result = self.stage1_reporter_hits(df)
            
            # Stage 2: Vitality hits  
            df_result = self.stage2_vitality_hits(df_result)
            
            # Stage 3: Platform hits
            df_result = self.stage3_platform_hits(df_result)
            
            # Generate summary
            summary = self.generate_hit_summary(df_result)
            
            logger.info("Multi-stage analysis completed successfully")
            return df_result, summary
            
        except Exception as e:
            raise MultiStageError(f"Multi-stage analysis failed: {str(e)}")


# Convenience functions for standalone use
def stage1_reporter_hits(df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> pd.DataFrame:
    """Identify Stage 1 reporter hits using default MultiStageHitCaller."""
    caller = MultiStageHitCaller(config)
    return caller.stage1_reporter_hits(df)


def stage2_vitality_hits(df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> pd.DataFrame:
    """Identify Stage 2 vitality hits using default MultiStageHitCaller."""
    caller = MultiStageHitCaller(config)
    return caller.stage2_vitality_hits(df)


def stage3_platform_hits(df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> pd.DataFrame:
    """Identify Stage 3 platform hits using default MultiStageHitCaller."""
    caller = MultiStageHitCaller(config)
    return caller.stage3_platform_hits(df)


def run_multi_stage_analysis(df: pd.DataFrame, config: Optional[MultiStageConfig] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run complete multi-stage analysis using default MultiStageHitCaller."""
    caller = MultiStageHitCaller(config)
    return caller.run_full_analysis(df)