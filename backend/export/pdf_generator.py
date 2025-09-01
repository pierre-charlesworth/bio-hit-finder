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
            'platform_overview': '''The BREAKthrough Platform represents a next-generation approach to antimicrobial discovery, specifically designed to identify compounds that disrupt the Gram-negative outer membrane (OM). Developed as part of the European Union's Horizon Europe Programme, this platform addresses the critical need for novel antibiotics against multi-drug resistant pathogens by targeting the OM permeability barrier that protects Gram-negative bacteria. The platform integrates dual-reporter stress response monitoring with three-strain selectivity profiling to provide mechanistically informed hit identification with reduced false positive rates.''',
            
            'biological_foundation': '''The outer membrane of Gram-negative bacteria serves as the primary permeability barrier limiting antibiotic efficacy and conferring resistance. LPS (lipopolysaccharide) transport via the Lpt machinery and peptidoglycan remodeling through L,D-transpeptidases represent critical envelope biogenesis pathways. The σE and Cpx envelope stress response systems evolved to detect and respond to perturbations in these essential processes. By monitoring lptA (σE-regulated, LPS transport-specific) and ldtD (Cpx-regulated, structural compensation) as sentinel reporters, the platform detects OM disruption through two orthogonal stress pathways. This dual-reporter design increases mechanistic specificity while reducing artifacts from non-specific stress responses.''',
            
            'normalization_methodology': '''Reporter ratio calculation (BG/BT) provides internal normalization critical for robust screening data. β-galactosidase (BG) signals reflect transcriptional stress responses, while ATP (BT) measurements via BacTiter-Glo quantify viable cell mass. This ratiometric approach corrects for: (1) Well-to-well variations in inoculum density; (2) Compound effects on bacterial growth; (3) Pipetting and dispensing errors; (4) Plate-to-plate systematic variations. Unlike raw fluorescence measurements, BG/BT ratios enable direct comparison across conditions by normalizing stress response intensity to cellular biomass. OD normalizations relative to plate medians account for batch effects in media preparation, inoculum standardization, and incubation conditions, ensuring consistent interpretation of growth inhibition patterns.''',
            
            'robust_statistical_foundations': '''Classical statistical methods (mean/standard deviation) fail in screening contexts due to heavy-tailed distributions where 1-5% of wells contain genuine bioactive compounds that appear as extreme outliers. Robust statistics using median and median absolute deviation (MAD) provide outlier-resistant parameter estimation, tolerating up to 50% contamination versus 0% for mean-based methods. The robust Z-score formula Z = (value - median) / (1.4826 × MAD) maintains interpretability equivalent to standard Z-scores for normal distributions while remaining stable in the presence of outliers. This approach ensures that genuine hits enhance rather than distort statistical thresholds, improving both sensitivity and specificity for hit detection. B-scoring via median-polish algorithms removes systematic row/column biases when spatial artifacts are detected, further improving statistical power.''',
            
            'viability_gating_rationale': '''ATP-based viability gating represents a critical quality control step that distinguishes genuine stress responses from cytotoxicity artifacts. ATP levels directly reflect cellular energy status and drop rapidly upon cell death or severe metabolic compromise. The default threshold (f = 0.3) requires wells to maintain at least 30% of the plate median ATP level, ensuring sufficient viable biomass for reliable reporter measurements. This approach: (1) Excludes wells where reporter signals may reflect dying cell artifacts; (2) Focuses analysis on viable stress responses indicative of cellular adaptation; (3) Reduces false positives from cytotoxic compounds; (4) Maintains sensitivity for detecting bacteriostatic effects that may preserve viability while activating stress responses. Threshold optimization may be required for specific compound libraries or assay conditions.''',
            
            'quality_control_framework': '''Multi-dimensional quality control encompasses statistical, spatial, and biological validation criteria. Edge-effect detection uses spatial correlation analysis to identify systematic elevation of signals at plate periphery, common due to evaporation, temperature gradients, or handling artifacts. Row/column bias detection identifies systematic patterns suggesting pipetting errors, gradient effects, or dispensing problems. Statistical distribution assessment flags plates with unusual Z-score distributions, excessive hit rates, or poor separation between positive and negative controls. Z' factor calculations quantify assay window and reproducibility. Plates failing quality criteria are flagged for manual review and potential exclusion from analysis. This comprehensive approach ensures data integrity and reliability of biological conclusions.''',
            
            'hit_classification_system': '''The hierarchical hit calling system integrates biological and phenotypic evidence across three stages: Stage 1 (Reporter Hits) identifies wells with statistically significant stress response activation (Z ≥ 2.0, corresponding to >95% confidence); Stage 2 (Vitality Hits) confirms appropriate selectivity patterns (E. coli WT resistant, ΔtolC sensitive, S. aureus resistant) indicating OM-specific targeting; Stage 3 (Platform Hits) combines both criteria for high-confidence candidates. This multi-stage approach reduces false discovery rates while maintaining sensitivity for genuine OM disruptors. Expected hit rates (~1% of library) and validation success rates (10-30% confirmation) reflect the stringent criteria applied. Priority ranking considers statistical significance, selectivity specificity, and quality control metrics to guide follow-up studies.''',
            
            'technical_implementation': '''The platform implements several technical innovations: (1) Automated column mapping accommodates diverse data formats while maintaining standardized processing; (2) Multi-sheet processing enables batch analysis of large datasets; (3) Configurable parameters allow optimization for different libraries and assay conditions; (4) Interactive visualizations support real-time data exploration; (5) Comprehensive export formats facilitate integration with downstream analysis tools. Quality control algorithms automatically detect and flag potential artifacts, while robust statistical methods ensure reproducible results across experiments. The web-based interface enables access by distributed research teams while maintaining data security and processing consistency.'''
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