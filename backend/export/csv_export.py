"""CSV export functionality for processed plate data.

This module provides comprehensive CSV export capabilities including:
- Single plate exports with all calculated columns
- Combined multi-plate datasets
- Top hits rankings
- Summary statistics per plate

All exports include complete provenance information and proper Excel formatting.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import warnings

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class CSVExporter:
    """Handles CSV export of processed plate data with full provenance."""
    
    # Standard column ordering for export consistency
    STANDARD_COLUMNS = [
        # Identifiers
        'PlateID', 'Well', 'Row', 'Col',
        
        # Raw measurements
        'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD',
        'OD_WT', 'OD_tolC', 'OD_SA',
        
        # Calculated ratios
        'Ratio_lptA', 'Ratio_ldtD',
        
        # Normalized OD values
        'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm',
        
        # Z-scores (robust)
        'Z_lptA', 'Z_ldtD', 'Z_Ratio_lptA', 'Z_Ratio_ldtD',
        'Z_OD_WT_norm', 'Z_OD_tolC_norm', 'Z_OD_SA_norm',
        
        # B-scores (if calculated)
        'B_lptA', 'B_ldtD', 'B_Ratio_lptA', 'B_Ratio_ldtD',
        
        # Quality flags
        'Viability_Flag', 'Edge_Flag', 'Control_Type'
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize CSV exporter with configuration.
        
        Args:
            config: Configuration dictionary with export settings
        """
        self.config = config or {}
        self.processing_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _add_metadata_header(self, filepath: Path, metadata: Dict[str, str]) -> None:
        """Add metadata header to CSV file.
        
        Args:
            filepath: Path to CSV file
            metadata: Metadata dictionary to include
        """
        # Read existing content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prepare header
        header_lines = [
            "# Bio-Hit-Finder Export",
            f"# Generated: {self.processing_timestamp}",
            f"# Software Version: {metadata.get('version', 'unknown')}",
        ]
        
        # Add processing parameters
        if 'processing_params' in metadata:
            params = metadata['processing_params']
            header_lines.append("# Processing Parameters:")
            for key, value in params.items():
                header_lines.append(f"#   {key}: {value}")
        
        # Add plate information
        if 'plate_info' in metadata:
            info = metadata['plate_info']
            header_lines.append("# Plate Information:")
            for key, value in info.items():
                header_lines.append(f"#   {key}: {value}")
        
        header_lines.append("")  # Empty line before data
        
        # Write header + content
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(header_lines) + '\n')
            f.write(content)
    
    def _order_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Order columns according to standard layout.
        
        Args:
            df: DataFrame to reorder
            
        Returns:
            DataFrame with properly ordered columns
        """
        # Get available columns in standard order
        available_cols = [col for col in self.STANDARD_COLUMNS if col in df.columns]
        
        # Add any additional columns not in standard list
        extra_cols = [col for col in df.columns if col not in available_cols]
        final_cols = available_cols + sorted(extra_cols)
        
        return df[final_cols]
    
    def export_processed_plate(
        self, 
        df: pd.DataFrame, 
        filename: Union[str, Path],
        metadata: Optional[Dict] = None
    ) -> Path:
        """Export single processed plate with all calculated columns.
        
        Args:
            df: Processed plate DataFrame
            filename: Output filename or path
            metadata: Optional metadata to include in header
            
        Returns:
            Path to exported file
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting processed plate to {filepath}")
        
        # Order columns and handle missing ones
        df_export = self._order_columns(df.copy())
        
        # Export to CSV
        df_export.to_csv(filepath, index=False, float_format='%.6f')
        
        # Add metadata header if provided
        if metadata:
            self._add_metadata_header(filepath, metadata)
        
        logger.info(f"Successfully exported {len(df_export)} wells to {filepath}")
        return filepath
    
    def export_combined_dataset(
        self, 
        df: pd.DataFrame, 
        filename: Union[str, Path],
        metadata: Optional[Dict] = None
    ) -> Path:
        """Export combined multi-plate dataset with PlateID column.
        
        Args:
            df: Combined DataFrame from multiple plates
            filename: Output filename or path
            metadata: Optional metadata to include in header
            
        Returns:
            Path to exported file
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting combined dataset to {filepath}")
        
        # Ensure PlateID is present
        if 'PlateID' not in df.columns:
            logger.warning("PlateID column not found - adding default values")
            df = df.copy()
            df['PlateID'] = 'Unknown'
        
        # Order columns and export
        df_export = self._order_columns(df.copy())
        df_export.to_csv(filepath, index=False, float_format='%.6f')
        
        # Add metadata header
        if metadata:
            # Add plate count to metadata
            plate_count = df_export['PlateID'].nunique()
            metadata = metadata.copy()
            metadata.setdefault('plate_info', {})['total_plates'] = plate_count
            metadata['plate_info']['total_wells'] = len(df_export)
            
            self._add_metadata_header(filepath, metadata)
        
        logger.info(f"Successfully exported {len(df_export)} wells from {df_export['PlateID'].nunique()} plates to {filepath}")
        return filepath
    
    def export_top_hits(
        self, 
        df: pd.DataFrame, 
        top_n: int, 
        filename: Union[str, Path],
        score_column: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Path:
        """Export top hits ranked by maximum absolute Z-scores.
        
        Args:
            df: Processed DataFrame
            top_n: Number of top hits to export
            filename: Output filename or path
            score_column: Column to rank by (default: max absolute Z-score)
            metadata: Optional metadata to include in header
            
        Returns:
            Path to exported file
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting top {top_n} hits to {filepath}")
        
        df_work = df.copy()
        
        # Calculate ranking score
        if score_column is None:
            # Use maximum absolute Z-score across all Z-score columns
            z_cols = [col for col in df_work.columns if col.startswith('Z_') and not col.endswith('_rank')]
            
            if not z_cols:
                raise ValueError("No Z-score columns found for ranking")
            
            # Calculate max absolute Z-score
            df_work['Max_Abs_Z'] = df_work[z_cols].abs().max(axis=1)
            score_column = 'Max_Abs_Z'
        
        # Rank and select top hits
        df_hits = df_work.nlargest(top_n, score_column)
        
        # Add ranking column
        df_hits = df_hits.reset_index(drop=True)
        df_hits.insert(0, 'Hit_Rank', range(1, len(df_hits) + 1))
        
        # Order columns and export
        df_export = self._order_columns(df_hits)
        df_export.to_csv(filepath, index=False, float_format='%.6f')
        
        # Add metadata header
        if metadata:
            metadata = metadata.copy()
            metadata.setdefault('export_info', {})['hit_selection'] = {
                'top_n': top_n,
                'ranking_column': score_column,
                'total_candidates': len(df_work)
            }
            self._add_metadata_header(filepath, metadata)
        
        logger.info(f"Successfully exported top {len(df_export)} hits to {filepath}")
        return filepath
    
    def export_summary_stats(
        self, 
        df: pd.DataFrame, 
        filename: Union[str, Path],
        metadata: Optional[Dict] = None
    ) -> Path:
        """Export per-plate summary statistics.
        
        Args:
            df: Processed DataFrame (can be multi-plate)
            filename: Output filename or path
            metadata: Optional metadata to include in header
            
        Returns:
            Path to exported file
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting summary statistics to {filepath}")
        
        # Ensure PlateID column exists
        if 'PlateID' not in df.columns:
            df = df.copy()
            df['PlateID'] = 'Unknown'
        
        # Calculate summary statistics per plate
        summary_stats = []
        
        for plate_id in df['PlateID'].unique():
            plate_df = df[df['PlateID'] == plate_id]
            
            stats = {'PlateID': plate_id, 'Well_Count': len(plate_df)}
            
            # Statistical summaries for key metrics
            numeric_cols = [
                'Ratio_lptA', 'Ratio_ldtD',
                'Z_lptA', 'Z_ldtD', 'Z_Ratio_lptA', 'Z_Ratio_ldtD',
                'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm'
            ]
            
            for col in numeric_cols:
                if col in plate_df.columns:
                    values = plate_df[col].dropna()
                    if len(values) > 0:
                        stats.update({
                            f'{col}_Mean': values.mean(),
                            f'{col}_Median': values.median(),
                            f'{col}_Std': values.std(),
                            f'{col}_MAD': np.median(np.abs(values - values.median())),
                            f'{col}_Min': values.min(),
                            f'{col}_Max': values.max()
                        })
            
            # Quality flags summary
            if 'Viability_Flag' in plate_df.columns:
                stats['Viable_Wells'] = (~plate_df['Viability_Flag']).sum()
                stats['Flagged_Wells'] = plate_df['Viability_Flag'].sum()
            
            if 'Edge_Flag' in plate_df.columns:
                stats['Edge_Wells'] = plate_df['Edge_Flag'].sum()
            
            # Hit calling summary (using common thresholds)
            z_cols = ['Z_lptA', 'Z_ldtD', 'Z_Ratio_lptA', 'Z_Ratio_ldtD']
            available_z_cols = [col for col in z_cols if col in plate_df.columns]
            
            if available_z_cols:
                for threshold in [2.0, 2.5, 3.0]:
                    hits = 0
                    for z_col in available_z_cols:
                        hits += (plate_df[z_col].abs() >= threshold).sum()
                    stats[f'Hits_Z_{threshold}'] = hits
            
            summary_stats.append(stats)
        
        # Convert to DataFrame and export
        summary_df = pd.DataFrame(summary_stats)
        summary_df.to_csv(filepath, index=False, float_format='%.6f')
        
        # Add metadata header
        if metadata:
            metadata = metadata.copy()
            metadata.setdefault('export_info', {})['summary_type'] = 'per_plate_statistics'
            self._add_metadata_header(filepath, metadata)
        
        logger.info(f"Successfully exported summary statistics for {len(summary_df)} plates to {filepath}")
        return filepath
    
    def export_quality_report(
        self, 
        df: pd.DataFrame, 
        filename: Union[str, Path],
        metadata: Optional[Dict] = None
    ) -> Path:
        """Export quality control report with key metrics.
        
        Args:
            df: Processed DataFrame
            filename: Output filename or path
            metadata: Optional metadata to include in header
            
        Returns:
            Path to exported file
        """
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting QC report to {filepath}")
        
        # Build QC report
        qc_data = []
        
        # Per-plate QC metrics
        if 'PlateID' in df.columns:
            plate_ids = df['PlateID'].unique()
        else:
            plate_ids = ['Unknown']
            df = df.copy()
            df['PlateID'] = 'Unknown'
        
        for plate_id in plate_ids:
            plate_df = df[df['PlateID'] == plate_id]
            
            # Basic metrics
            qc_row = {
                'PlateID': plate_id,
                'Total_Wells': len(plate_df),
                'Processing_Timestamp': self.processing_timestamp
            }
            
            # Viability assessment
            if 'Viability_Flag' in plate_df.columns:
                viable_count = (~plate_df['Viability_Flag']).sum()
                qc_row.update({
                    'Viable_Wells': viable_count,
                    'Viability_Rate': viable_count / len(plate_df) if len(plate_df) > 0 else 0
                })
            
            # Z-score distribution quality
            z_cols = [col for col in plate_df.columns if col.startswith('Z_')]
            if z_cols:
                z_values = plate_df[z_cols].values.flatten()
                z_values = z_values[~pd.isna(z_values)]
                
                if len(z_values) > 0:
                    qc_row.update({
                        'Z_Score_Range': z_values.max() - z_values.min(),
                        'Z_Score_IQR': np.percentile(z_values, 75) - np.percentile(z_values, 25),
                        'Extreme_Z_Count': np.sum(np.abs(z_values) > 5),
                        'Strong_Hits_Z3': np.sum(np.abs(z_values) >= 3.0)
                    })
            
            # Edge effect indicators
            if 'Edge_Flag' in plate_df.columns:
                qc_row['Edge_Flagged_Wells'] = plate_df['Edge_Flag'].sum()
            
            qc_data.append(qc_row)
        
        # Export QC report
        qc_df = pd.DataFrame(qc_data)
        qc_df.to_csv(filepath, index=False, float_format='%.6f')
        
        # Add metadata header
        if metadata:
            metadata = metadata.copy()
            metadata.setdefault('export_info', {})['report_type'] = 'quality_control'
            self._add_metadata_header(filepath, metadata)
        
        logger.info(f"Successfully exported QC report for {len(qc_df)} plates to {filepath}")
        return filepath


def create_export_metadata(
    config: Dict,
    processing_info: Optional[Dict] = None,
    software_version: str = "1.0.0"
) -> Dict[str, str]:
    """Create standardized metadata for export files.
    
    Args:
        config: Configuration dictionary
        processing_info: Optional processing information
        software_version: Software version string
        
    Returns:
        Metadata dictionary for export headers
    """
    metadata = {
        'version': software_version,
        'processing_params': {
            'viability_threshold': config.get('processing', {}).get('viability_threshold', 0.3),
            'z_score_cutoff': config.get('processing', {}).get('z_score_cutoff', 2.0),
            'bscore_enabled': config.get('bscore', {}).get('enabled', False)
        }
    }
    
    if processing_info:
        metadata['plate_info'] = processing_info
    
    return metadata