"""PDF report generation for bio-hit-finder platform.

This module creates comprehensive QC reports with embedded formulas,
visualizations, and statistical summaries using Jinja2 templates
and WeasyPrint rendering.
"""

import base64
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from jinja2 import Environment, FileSystemLoader, Template
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generates comprehensive PDF reports with formulas and visualizations."""
    
    def __init__(self, templates_dir: Optional[Path] = None, config: Optional[Dict] = None):
        """Initialize PDF report generator.
        
        Args:
            templates_dir: Directory containing Jinja2 templates
            config: Configuration dictionary
        """
        self.config = config or {}
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        # Add custom filters
        self.jinja_env.filters['format_number'] = self._format_number
        self.jinja_env.filters['format_pvalue'] = self._format_pvalue
        self.jinja_env.filters['format_percent'] = self._format_percent
        
        # Font configuration for better PDF rendering
        self.font_config = FontConfiguration()
        
        logger.info(f"Initialized PDF generator with templates from {self.templates_dir}")
    
    def _format_number(self, value: float, precision: int = 3) -> str:
        """Format number for display in reports."""
        if pd.isna(value):
            return "N/A"
        if abs(value) < 0.001 and value != 0:
            return f"{value:.2e}"
        return f"{value:.{precision}f}"
    
    def _format_pvalue(self, value: float) -> str:
        """Format p-value for display."""
        if pd.isna(value):
            return "N/A"
        if value < 0.001:
            return f"{value:.2e}"
        return f"{value:.3f}"
    
    def _format_percent(self, value: float) -> str:
        """Format percentage for display."""
        if pd.isna(value):
            return "N/A"
        return f"{value*100:.1f}%"
    
    def _create_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary statistics for report.
        
        Args:
            df: Processed DataFrame
            
        Returns:
            Dictionary of summary statistics
        """
        stats = {
            'total_wells': len(df),
            'processing_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Plate information
        if 'PlateID' in df.columns:
            stats['total_plates'] = df['PlateID'].nunique()
            stats['plates'] = df['PlateID'].unique().tolist()
        else:
            stats['total_plates'] = 1
            stats['plates'] = ['Unknown']
        
        # Viability assessment
        if 'Viability_Flag' in df.columns:
            viable_count = (~df['Viability_Flag']).sum()
            stats['viable_wells'] = viable_count
            stats['viability_rate'] = viable_count / len(df) if len(df) > 0 else 0
        
        # Quality flags
        if 'Edge_Flag' in df.columns:
            stats['edge_flagged'] = df['Edge_Flag'].sum()
        
        # Z-score distribution
        z_cols = [col for col in df.columns if col.startswith('Z_') and not col.endswith('_rank')]
        if z_cols:
            z_values = df[z_cols].values.flatten()
            z_values = z_values[~pd.isna(z_values)]
            
            if len(z_values) > 0:
                stats['z_score_stats'] = {
                    'count': len(z_values),
                    'mean': np.mean(z_values),
                    'std': np.std(z_values),
                    'min': np.min(z_values),
                    'max': np.max(z_values),
                    'hits_z2': np.sum(np.abs(z_values) >= 2.0),
                    'hits_z3': np.sum(np.abs(z_values) >= 3.0)
                }
        
        return stats
    
    def _create_plate_summaries(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create per-plate summary information.
        
        Args:
            df: Processed DataFrame
            
        Returns:
            List of plate summary dictionaries
        """
        summaries = []
        
        # Ensure PlateID column
        if 'PlateID' not in df.columns:
            df = df.copy()
            df['PlateID'] = 'Unknown'
        
        for plate_id in df['PlateID'].unique():
            plate_df = df[df['PlateID'] == plate_id]
            
            summary = {
                'plate_id': plate_id,
                'well_count': len(plate_df)
            }
            
            # Key metrics
            ratio_cols = ['Ratio_lptA', 'Ratio_ldtD']
            for col in ratio_cols:
                if col in plate_df.columns:
                    values = plate_df[col].dropna()
                    if len(values) > 0:
                        summary[f'{col.lower()}_median'] = values.median()
                        summary[f'{col.lower()}_mad'] = np.median(np.abs(values - values.median()))
            
            # Z-score summaries
            z_cols = [col for col in plate_df.columns if col.startswith('Z_')]
            if z_cols:
                z_values = plate_df[z_cols].values.flatten()
                z_values = z_values[~pd.isna(z_values)]
                
                if len(z_values) > 0:
                    summary['z_range'] = np.max(z_values) - np.min(z_values)
                    summary['strong_hits'] = np.sum(np.abs(z_values) >= 3.0)
            
            # Quality assessment
            if 'Viability_Flag' in plate_df.columns:
                viable = (~plate_df['Viability_Flag']).sum()
                summary['viable_wells'] = viable
                summary['viability_rate'] = viable / len(plate_df) if len(plate_df) > 0 else 0
            
            summaries.append(summary)
        
        return summaries
    
    def _plot_to_base64(self, fig: go.Figure, width: int = 800, height: int = 600) -> str:
        """Convert Plotly figure to base64 string for embedding.
        
        Args:
            fig: Plotly figure
            width: Figure width in pixels
            height: Figure height in pixels
            
        Returns:
            Base64 encoded image string
        """
        # Update layout for PDF rendering
        fig.update_layout(
            width=width,
            height=height,
            font_size=12,
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        # Convert to PNG bytes
        img_bytes = pio.to_image(fig, format='png', width=width, height=height, scale=2)
        
        # Encode to base64
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/png;base64,{img_b64}"
    
    def _create_distribution_plot(self, df: pd.DataFrame, metric: str) -> Optional[str]:
        """Create distribution plot for a given metric.
        
        Args:
            df: DataFrame containing the metric
            metric: Column name to plot
            
        Returns:
            Base64 encoded plot or None if column not found
        """
        if metric not in df.columns:
            return None
        
        values = df[metric].dropna()
        if len(values) == 0:
            return None
        
        fig = go.Figure()
        
        # Histogram
        fig.add_trace(go.Histogram(
            x=values,
            nbinsx=30,
            name=metric,
            opacity=0.7
        ))
        
        # Add median line
        median_val = values.median()
        fig.add_vline(
            x=median_val,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Median: {median_val:.3f}"
        )
        
        fig.update_layout(
            title=f"Distribution of {metric}",
            xaxis_title=metric,
            yaxis_title="Count",
            showlegend=False
        )
        
        return self._plot_to_base64(fig, width=600, height=400)
    
    def _create_zscore_overview(self, df: pd.DataFrame) -> Optional[str]:
        """Create Z-score overview plot.
        
        Args:
            df: DataFrame with Z-score columns
            
        Returns:
            Base64 encoded plot or None if no Z-scores found
        """
        z_cols = [col for col in df.columns if col.startswith('Z_') and not col.endswith('_rank')]
        
        if not z_cols:
            return None
        
        fig = go.Figure()
        
        for i, col in enumerate(z_cols):
            values = df[col].dropna()
            if len(values) > 0:
                fig.add_trace(go.Box(
                    y=values,
                    name=col.replace('Z_', ''),
                    boxpoints='outliers'
                ))
        
        # Add significance thresholds
        for threshold in [2.0, 3.0]:
            fig.add_hline(y=threshold, line_dash="dash", line_color="red", opacity=0.5)
            fig.add_hline(y=-threshold, line_dash="dash", line_color="red", opacity=0.5)
        
        fig.update_layout(
            title="Z-Score Distribution by Metric",
            yaxis_title="Z-Score",
            showlegend=True
        )
        
        return self._plot_to_base64(fig, width=800, height=500)
    
    def generate_report(
        self, 
        df: pd.DataFrame, 
        output_path: Union[str, Path],
        config: Optional[Dict] = None,
        include_plots: bool = True
    ) -> Path:
        """Generate complete PDF QC report.
        
        Args:
            df: Processed DataFrame
            output_path: Output path for PDF file
            config: Configuration dictionary (overrides instance config)
            include_plots: Whether to include visualization plots
            
        Returns:
            Path to generated PDF file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = config or self.config
        
        logger.info(f"Generating PDF report to {output_path}")
        
        # Create report data
        report_data = {
            'title': 'Bio-Hit-Finder QC Report',
            'summary': self._create_summary_stats(df),
            'plate_summaries': self._create_plate_summaries(df),
            'config': config,
            'formulas': self._get_formula_definitions(),
            'methodology': self._get_methodology_text()
        }
        
        # Add plots if requested
        if include_plots:
            report_data['plots'] = {}
            
            # Z-score overview
            zscore_plot = self._create_zscore_overview(df)
            if zscore_plot:
                report_data['plots']['zscore_overview'] = zscore_plot
            
            # Distribution plots for key metrics
            for metric in ['Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD']:
                plot = self._create_distribution_plot(df, metric)
                if plot:
                    report_data['plots'][f'{metric.lower()}_dist'] = plot
        
        # Load and render template
        try:
            template = self.jinja_env.get_template('report.html')
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            raise
        
        html_content = template.render(**report_data)
        
        # Generate PDF using WeasyPrint
        try:
            # Custom CSS for better PDF rendering
            css_content = """
            @page {
                size: A4;
                margin: 20mm 15mm 20mm 15mm;
            }
            body {
                font-family: 'DejaVu Sans', Arial, sans-serif;
                line-height: 1.4;
                color: #333;
            }
            .page-break {
                page-break-before: always;
            }
            .formula {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
                font-family: 'DejaVu Sans Mono', monospace;
            }
            .summary-table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            .summary-table th, .summary-table td {
                border: 1px solid #dee2e6;
                padding: 8px;
                text-align: left;
            }
            .summary-table th {
                background-color: #f8f9fa;
            }
            .plot-container {
                text-align: center;
                margin: 20px 0;
            }
            .plot-container img {
                max-width: 100%;
                height: auto;
            }
            """
            
            HTML(string=html_content).write_pdf(
                output_path,
                stylesheets=[CSS(string=css_content)],
                font_config=self.font_config
            )
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise
        
        logger.info(f"Successfully generated PDF report: {output_path}")
        return output_path
    
    def _get_formula_definitions(self) -> Dict[str, str]:
        """Get mathematical formula definitions for the report.
        
        Returns:
            Dictionary of formula definitions
        """
        return {
            'reporter_ratio_lpta': 'Ratio_lptA = BG_lptA / BT_lptA',
            'reporter_ratio_ldtd': 'Ratio_ldtD = BG_ldtD / BT_ldtD',
            'od_normalization': 'OD_WT_norm = OD_WT / median(OD_WT)',
            'robust_zscore': 'Z = (value - median) / (1.4826 × MAD)',
            'viability_gate': 'Viability_Flag = ATP < f × median(ATP)',
            'mad_calculation': 'MAD = median(|value - median(value)|)',
            'bscore_formula': 'B-score = median-polish residual / (1.4826 × MAD)'
        }
    
    def _get_methodology_text(self) -> Dict[str, str]:
        """Get methodology descriptions for the report.
        
        Returns:
            Dictionary of methodology text sections
        """
        return {
            'overview': '''This report presents the results of automated plate data processing using the Bio-Hit-Finder platform. The analysis pipeline includes data normalization, robust statistical scoring, quality control assessment, and candidate hit identification.''',
            
            'normalization': '''Raw measurement data is normalized using robust statistical methods. Reporter ratios are calculated as the ratio of beta-galactosidase (BG) to BacTiter (BT) signals. Optical density measurements are normalized relative to the plate-wide median to account for systematic variations.''',
            
            'zscore_calculation': '''Robust Z-scores are calculated using the median and median absolute deviation (MAD) instead of mean and standard deviation. This approach is less sensitive to outliers and provides more reliable statistical assessment of potential hits. The MAD is scaled by 1.4826 to make it comparable to the standard deviation for normally distributed data.''',
            
            'viability_gating': '''Wells with low ATP levels (BacTiter signal) are flagged as potentially non-viable. The viability threshold is set as a fraction of the plate median ATP level (default: 0.3). These wells are excluded from hit calling but retained for visualization.''',
            
            'quality_control': '''Multiple quality control metrics are calculated including edge-effect detection, spatial artifact identification, and statistical distribution assessment. Plates showing significant systematic biases or unusual distributions are flagged for manual review.'''
        }


def generate_quick_summary(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    config: Optional[Dict] = None
) -> Path:
    """Generate a quick summary report without full visualizations.
    
    Args:
        df: Processed DataFrame
        output_path: Output path for PDF
        config: Optional configuration
        
    Returns:
        Path to generated summary PDF
    """
    generator = PDFReportGenerator(config=config)
    return generator.generate_report(df, output_path, config=config, include_plots=False)