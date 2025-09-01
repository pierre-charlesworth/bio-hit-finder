"""
Export-ready static plot generation for bio-hit-finder platform.

This module provides high-quality static plots suitable for publications,
reports, and presentations. Uses both Plotly (with kaleido) and matplotlib/seaborn
for different export requirements.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import warnings

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn("Matplotlib/Seaborn not available. Some export functions will be limited.")

from .styling import (
    PlotlyTheme,
    color_manager,
    get_figure_export_config,
    format_number_for_display,
    COLORBLIND_FRIENDLY_PALETTE
)
from .charts import (
    create_histogram_with_overlay,
    create_scatter_plot,
    create_viability_bar_chart,
    create_zscore_comparison_chart
)
from .heatmaps import create_plate_heatmap


class PlotExporter:
    """High-level interface for exporting publication-ready plots."""
    
    def __init__(self, output_dir: Union[str, Path], dpi: int = 300):
        """
        Initialize PlotExporter.
        
        Args:
            output_dir: Directory to save exported plots
            dpi: Resolution for static image exports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        
        # Configure plotly for exports
        self.export_config = get_figure_export_config()
        self.export_config.update({'scale': dpi/150})  # Adjust scale for DPI
    
    def export_figure(
        self,
        fig: go.Figure,
        filename: str,
        formats: List[str] = ['png', 'svg', 'html'],
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> List[Path]:
        """
        Export a Plotly figure in multiple formats.
        
        Args:
            fig: Plotly figure to export
            filename: Base filename (without extension)
            formats: List of formats to export ('png', 'svg', 'html', 'pdf')
            width: Custom width in pixels
            height: Custom height in pixels
        
        Returns:
            List of paths to exported files
        """
        exported_files = []
        
        # Update export config if custom dimensions provided
        export_config = self.export_config.copy()
        if width:
            export_config['width'] = width
        if height:
            export_config['height'] = height
        
        for fmt in formats:
            output_file = self.output_dir / f"{filename}.{fmt}"
            
            try:
                if fmt == 'html':
                    fig.write_html(str(output_file), include_plotlyjs='cdn')
                elif fmt == 'pdf':
                    fig.write_image(str(output_file), **export_config, format='pdf')
                else:
                    fig.write_image(str(output_file), **export_config, format=fmt)
                
                exported_files.append(output_file)
            except Exception as e:
                warnings.warn(f"Failed to export {fmt}: {e}")
        
        return exported_files
    
    def create_publication_charts(self, df: pd.DataFrame) -> Dict[str, List[Path]]:
        """
        Create all publication-ready charts specified in PRD.
        
        Args:
            df: DataFrame containing processed plate data
        
        Returns:
            Dictionary mapping chart type to list of exported file paths
        """
        exported_charts = {}
        
        # Required columns check
        required_cols = ['Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            warnings.warn(f"Missing required columns: {missing_cols}")
            return exported_charts
        
        # 1. Histograms of Ratio_lptA and Ratio_ldtD
        for ratio_col in ['Ratio_lptA', 'Ratio_ldtD']:
            if ratio_col in df.columns:
                fig = create_histogram_with_overlay(
                    df, ratio_col, 
                    title=f'Distribution of {ratio_col.replace("_", " ")}',
                    show_box=True
                )
                files = self.export_figure(fig, f'histogram_{ratio_col.lower()}')
                exported_charts[f'histogram_{ratio_col}'] = files
        
        # 2. Histograms/boxplots of Z_lptA and Z_ldtD
        for z_col in ['Z_lptA', 'Z_ldtD']:
            if z_col in df.columns:
                fig = create_histogram_with_overlay(
                    df, z_col,
                    title=f'Distribution of {z_col.replace("_", " ")} Z-scores',
                    show_box=True
                )
                files = self.export_figure(fig, f'zscore_{z_col.lower()}')
                exported_charts[f'zscore_{z_col}'] = files
        
        # 3. Scatter plot: Ratio_lptA vs Ratio_ldtD
        if 'Ratio_lptA' in df.columns and 'Ratio_ldtD' in df.columns:
            fig = create_scatter_plot(
                df, 'Ratio_lptA', 'Ratio_ldtD',
                color_col='PlateID' if 'PlateID' in df.columns else None,
                title='Ratio_lptA vs Ratio_ldtD',
                hover_data=['Well'] if 'Well' in df.columns else None
            )
            files = self.export_figure(fig, 'scatter_ratios')
            exported_charts['scatter_ratios'] = files
        
        # 4. Viability bar chart
        if 'Viable' in df.columns:
            fig = create_viability_bar_chart(df, title='Viability Gate Counts')
            files = self.export_figure(fig, 'viability_bars')
            exported_charts['viability_bars'] = files
        
        # 5. Z-score comparison (if B-scores available)
        bscore_cols = [col for col in df.columns if col.startswith('B_')]
        if bscore_cols:
            for zscore_col in ['Z_lptA', 'Z_ldtD']:
                bscore_col = zscore_col.replace('Z_', 'B_')
                if zscore_col in df.columns and bscore_col in df.columns:
                    fig = create_zscore_comparison_chart(
                        df, zscore_col, bscore_col,
                        title=f'{zscore_col} Raw Z-score vs B-score Comparison'
                    )
                    files = self.export_figure(fig, f'comparison_{zscore_col.lower()}')
                    exported_charts[f'comparison_{zscore_col}'] = files
        
        # 6. Plate heatmaps
        if 'Well' in df.columns:
            # Get unique plates
            plates = df.get('PlateID', pd.Series(['Plate1'])).unique()[:4]  # Max 4 plates
            
            for plate in plates:
                for metric in ['Z_lptA', 'Z_ldtD']:
                    if metric in df.columns:
                        fig = create_plate_heatmap(
                            df, metric, 
                            title=f'{metric} Heatmap - {plate}',
                            plate_id=plate if 'PlateID' in df.columns else None
                        )
                        files = self.export_figure(fig, f'heatmap_{metric.lower()}_{plate}')
                        exported_charts[f'heatmap_{metric}_{plate}'] = files
        
        return exported_charts


def create_pdf_compatible_plots(df: pd.DataFrame, output_dir: Union[str, Path]) -> List[Path]:
    """
    Create matplotlib-based static plots specifically for PDF reports.
    
    Args:
        df: DataFrame containing processed plate data
        output_dir: Directory to save plots
    
    Returns:
        List of paths to saved plot files
    """
    if not MATPLOTLIB_AVAILABLE:
        warnings.warn("Matplotlib not available, cannot create PDF-compatible plots")
        return []
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exported_files = []
    
    # Set matplotlib style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Ratio histograms
    for ratio_col in ['Ratio_lptA', 'Ratio_ldtD']:
        if ratio_col in df.columns:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), 
                                          gridspec_kw={'height_ratios': [3, 1]},
                                          sharex=True)
            
            # Histogram
            clean_data = df[ratio_col].dropna()
            ax1.hist(clean_data, bins=30, alpha=0.7, color=COLORBLIND_FRIENDLY_PALETTE[0],
                    edgecolor='black', linewidth=0.5)
            ax1.set_ylabel('Frequency')
            ax1.set_title(f'Distribution of {ratio_col.replace("_", " ")}')
            ax1.grid(True, alpha=0.3)
            
            # Box plot
            ax2.boxplot(clean_data, vert=False, patch_artist=True,
                       boxprops=dict(facecolor=COLORBLIND_FRIENDLY_PALETTE[0], alpha=0.7))
            ax2.set_xlabel(ratio_col.replace('_', ' '))
            ax2.set_yticks([])
            
            # Add statistics
            stats_text = (f'n = {len(clean_data):,}\n'
                         f'μ = {clean_data.mean():.3f}\n'
                         f'σ = {clean_data.std():.3f}')
            ax1.text(0.98, 0.98, stats_text, transform=ax1.transAxes,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            output_file = output_dir / f'pdf_histogram_{ratio_col.lower()}.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            exported_files.append(output_file)
    
    # 2. Scatter plot
    if 'Ratio_lptA' in df.columns and 'Ratio_ldtD' in df.columns:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        if 'PlateID' in df.columns and df['PlateID'].nunique() <= 10:
            # Color by plate
            plates = df['PlateID'].unique()
            colors = COLORBLIND_FRIENDLY_PALETTE[:len(plates)]
            
            for i, plate in enumerate(plates):
                plate_data = df[df['PlateID'] == plate]
                ax.scatter(plate_data['Ratio_lptA'], plate_data['Ratio_ldtD'],
                          alpha=0.6, s=30, c=colors[i], label=f'Plate {plate}',
                          edgecolor='black', linewidth=0.5)
            
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            ax.scatter(df['Ratio_lptA'], df['Ratio_ldtD'],
                      alpha=0.6, s=30, c=COLORBLIND_FRIENDLY_PALETTE[0],
                      edgecolor='black', linewidth=0.5)
        
        # Add diagonal line
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        line_min = max(x_min, y_min)
        line_max = min(x_max, y_max)
        ax.plot([line_min, line_max], [line_min, line_max], 
               'k--', alpha=0.5, label='y = x')
        
        ax.set_xlabel('Ratio_lptA')
        ax.set_ylabel('Ratio_ldtD')
        ax.set_title('Ratio_lptA vs Ratio_ldtD')
        ax.grid(True, alpha=0.3)
        
        # Add correlation
        correlation = df[['Ratio_lptA', 'Ratio_ldtD']].corr().iloc[0, 1]
        ax.text(0.02, 0.98, f'r = {correlation:.3f}', transform=ax.transAxes,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        output_file = output_dir / 'pdf_scatter_ratios.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        exported_files.append(output_file)
    
    # 3. Viability bar chart
    if 'Viable' in df.columns and 'PlateID' in df.columns:
        viability_counts = df.groupby(['PlateID', 'Viable']).size().unstack(fill_value=0)
        
        if True not in viability_counts.columns:
            viability_counts[True] = 0
        if False not in viability_counts.columns:
            viability_counts[False] = 0
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(viability_counts))
        width = 0.35
        
        ax.bar(x, viability_counts[False], width, label='Non-viable',
              color='#d62728', alpha=0.8)
        ax.bar(x, viability_counts[True], width, bottom=viability_counts[False],
              label='Viable', color='#2ca02c', alpha=0.8)
        
        ax.set_xlabel('Plate ID')
        ax.set_ylabel('Number of Wells')
        ax.set_title('Viability Counts by Plate')
        ax.set_xticks(x)
        ax.set_xticklabels(viability_counts.index, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add percentage labels
        for i, plate_id in enumerate(viability_counts.index):
            total = viability_counts.loc[plate_id].sum()
            viable = viability_counts.loc[plate_id, True]
            pct = (viable / total * 100) if total > 0 else 0
            ax.text(i, total + total * 0.02, f'{pct:.1f}%',
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        output_file = output_dir / 'pdf_viability_bars.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        exported_files.append(output_file)
    
    return exported_files


def create_summary_figure(
    df: pd.DataFrame,
    title: str = 'Plate Analysis Summary',
    figsize: Tuple[int, int] = (16, 12)
) -> go.Figure:
    """
    Create a comprehensive summary figure with multiple panels.
    
    Args:
        df: DataFrame containing processed plate data
        title: Overall figure title
        figsize: Figure size (width, height) in pixels
    
    Returns:
        Plotly Figure with multiple subplots
    """
    # Create 2x3 subplot layout
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[
            'Ratio_lptA Distribution',
            'Ratio_ldtD Distribution', 
            'Ratio Correlation',
            'Z_lptA Distribution',
            'Z_ldtD Distribution',
            'Viability by Plate'
        ],
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # 1. Ratio_lptA histogram
    if 'Ratio_lptA' in df.columns:
        data = df['Ratio_lptA'].dropna()
        fig.add_trace(
            go.Histogram(x=data, nbinsx=25, name='Ratio_lptA',
                        marker_color=COLORBLIND_FRIENDLY_PALETTE[0],
                        opacity=0.7, showlegend=False),
            row=1, col=1
        )
    
    # 2. Ratio_ldtD histogram
    if 'Ratio_ldtD' in df.columns:
        data = df['Ratio_ldtD'].dropna()
        fig.add_trace(
            go.Histogram(x=data, nbinsx=25, name='Ratio_ldtD',
                        marker_color=COLORBLIND_FRIENDLY_PALETTE[1],
                        opacity=0.7, showlegend=False),
            row=1, col=2
        )
    
    # 3. Ratio correlation scatter
    if 'Ratio_lptA' in df.columns and 'Ratio_ldtD' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['Ratio_lptA'], y=df['Ratio_ldtD'],
                      mode='markers', name='Ratios',
                      marker=dict(size=4, opacity=0.6, 
                                color=COLORBLIND_FRIENDLY_PALETTE[2]),
                      showlegend=False),
            row=1, col=3
        )
    
    # 4. Z_lptA histogram
    if 'Z_lptA' in df.columns:
        data = df['Z_lptA'].dropna()
        fig.add_trace(
            go.Histogram(x=data, nbinsx=25, name='Z_lptA',
                        marker_color=COLORBLIND_FRIENDLY_PALETTE[3],
                        opacity=0.7, showlegend=False),
            row=2, col=1
        )
        fig.add_vline(x=0, line_dash="dash", line_color="gray", 
                     opacity=0.7, row=2, col=1)
    
    # 5. Z_ldtD histogram  
    if 'Z_ldtD' in df.columns:
        data = df['Z_ldtD'].dropna()
        fig.add_trace(
            go.Histogram(x=data, nbinsx=25, name='Z_ldtD',
                        marker_color=COLORBLIND_FRIENDLY_PALETTE[4],
                        opacity=0.7, showlegend=False),
            row=2, col=2
        )
        fig.add_vline(x=0, line_dash="dash", line_color="gray",
                     opacity=0.7, row=2, col=2)
    
    # 6. Viability bar chart
    if 'Viable' in df.columns and 'PlateID' in df.columns:
        viability_counts = df.groupby(['PlateID', 'Viable']).size().unstack(fill_value=0)
        
        if True in viability_counts.columns:
            fig.add_trace(
                go.Bar(x=viability_counts.index, y=viability_counts[True],
                      name='Viable', marker_color='#2ca02c',
                      opacity=0.8, showlegend=False),
                row=2, col=3
            )
        
        if False in viability_counts.columns:
            fig.add_trace(
                go.Bar(x=viability_counts.index, y=viability_counts[False],
                      name='Non-viable', marker_color='#d62728',
                      opacity=0.8, showlegend=False),
                row=2, col=3
            )
    
    # Apply theme and update layout
    fig = PlotlyTheme.apply_theme(fig, title)
    fig.update_layout(width=figsize[0], height=figsize[1])
    
    # Update axes labels
    fig.update_xaxes(title_text="Ratio_lptA", row=1, col=1)
    fig.update_xaxes(title_text="Ratio_ldtD", row=1, col=2)
    fig.update_xaxes(title_text="Ratio_lptA", row=1, col=3)
    fig.update_xaxes(title_text="Z_lptA", row=2, col=1)
    fig.update_xaxes(title_text="Z_ldtD", row=2, col=2)
    fig.update_xaxes(title_text="Plate ID", row=2, col=3)
    
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    fig.update_yaxes(title_text="Frequency", row=1, col=2)
    fig.update_yaxes(title_text="Ratio_ldtD", row=1, col=3)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)
    fig.update_yaxes(title_text="Well Count", row=2, col=3)
    
    return fig


# Export main functions and classes
__all__ = [
    'PlotExporter',
    'create_pdf_compatible_plots',
    'create_summary_figure'
]