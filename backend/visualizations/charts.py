"""
Standard chart components for bio-hit-finder platform.

This module provides interactive Plotly-based chart components including
histograms, scatter plots, bar charts, and comparison visualizations.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union, Tuple
import warnings

from .styling import (
    PlotlyTheme, 
    color_manager, 
    COLORBLIND_FRIENDLY_PALETTE,
    format_number_for_display
)


def create_histogram_with_overlay(
    data: pd.DataFrame,
    column: str,
    title: str,
    show_box: bool = True,
    bins: Optional[int] = None,
    show_kde: bool = False,
    color: Optional[str] = None
) -> go.Figure:
    """
    Create a histogram with optional box plot overlay.
    
    Args:
        data: DataFrame containing the data
        column: Column name to plot
        title: Plot title
        show_box: Whether to show box plot overlay
        bins: Number of histogram bins (auto if None)
        show_kde: Whether to show kernel density estimate
        color: Custom color for the histogram
    
    Returns:
        Plotly Figure object
    
    Example:
        >>> df = pd.DataFrame({'Ratio_lptA': np.random.normal(1.0, 0.3, 1000)})
        >>> fig = create_histogram_with_overlay(df, 'Ratio_lptA', 'Distribution of Ratio_lptA')
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Remove NaN values
    clean_data = data[column].dropna()
    
    if len(clean_data) == 0:
        raise ValueError(f"No valid data found in column '{column}'")
    
    # Create subplot with secondary y-axis if showing box plot
    if show_box:
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.8, 0.2],
            shared_xaxis=True,
            vertical_spacing=0.02,
            subplot_titles=(title, "")
        )
    else:
        fig = go.Figure()
    
    # Determine bins if not specified
    if bins is None:
        bins = min(50, max(10, int(np.sqrt(len(clean_data)))))
    
    # Color selection
    hist_color = color or COLORBLIND_FRIENDLY_PALETTE[0]
    
    # Create histogram
    if show_box:
        fig.add_trace(
            go.Histogram(
                x=clean_data,
                nbinsx=bins,
                name='Distribution',
                marker_color=hist_color,
                opacity=0.7,
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Add box plot
        fig.add_trace(
            go.Box(
                x=clean_data,
                name='',
                marker_color=hist_color,
                showlegend=False,
                boxpoints='outliers'
            ),
            row=2, col=1
        )
    else:
        fig.add_trace(
            go.Histogram(
                x=clean_data,
                nbinsx=bins,
                name='Distribution',
                marker_color=hist_color,
                opacity=0.7
            )
        )
    
    # Add KDE if requested
    if show_kde and not show_box:
        # Simple KDE approximation using numpy
        hist, bin_edges = np.histogram(clean_data, bins=bins, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Smooth the histogram for KDE-like appearance
        from scipy import ndimage
        try:
            smoothed = ndimage.gaussian_filter1d(hist, sigma=1)
            fig.add_trace(
                go.Scatter(
                    x=bin_centers,
                    y=smoothed,
                    mode='lines',
                    name='KDE',
                    line=dict(color='red', width=2),
                    yaxis='y2'
                )
            )
        except ImportError:
            warnings.warn("SciPy not available, skipping KDE overlay")
    
    # Update layout
    if not show_box:
        fig = PlotlyTheme.apply_theme(fig, title)
        fig.update_xaxes(title_text=column)
        fig.update_yaxes(title_text='Frequency')
    else:
        fig = PlotlyTheme.apply_theme(fig)
        fig.update_xaxes(title_text=column, row=2, col=1)
        fig.update_yaxes(title_text='Frequency', row=1, col=1)
        fig.update_yaxes(showticklabels=False, row=2, col=1)
    
    # Add summary statistics as annotation
    stats_text = (
        f"n = {len(clean_data):,}<br>"
        f"Mean = {format_number_for_display(clean_data.mean())}<br>"
        f"Median = {format_number_for_display(clean_data.median())}<br>"
        f"Std = {format_number_for_display(clean_data.std())}"
    )
    
    fig.add_annotation(
        x=0.98, y=0.98,
        xref='paper', yref='paper',
        text=stats_text,
        showarrow=False,
        align='left',
        bgcolor='rgba(255, 255, 255, 0.8)',
        bordercolor='gray',
        borderwidth=1,
        font=dict(size=10)
    )
    
    return fig


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = 'PlateID',
    title: str = '',
    hover_data: Optional[List[str]] = None,
    size_col: Optional[str] = None
) -> go.Figure:
    """
    Create interactive scatter plot with plate coloring.
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis  
        color_col: Column name for color grouping (default: PlateID)
        title: Plot title
        hover_data: Additional columns to show in hover
        size_col: Column name for marker size
    
    Returns:
        Plotly Figure object
    
    Example:
        >>> fig = create_scatter_plot(df, 'Ratio_lptA', 'Ratio_ldtD', 
        ...                          title='Ratio_lptA vs Ratio_ldtD')
    """
    # Validate columns
    required_cols = [x_col, y_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Handle color column
    if color_col not in df.columns:
        # Create a dummy color column if not present
        df = df.copy()
        df[color_col] = 'All Data'
    
    # Prepare hover data
    hover_cols = hover_data or []
    available_hover_cols = [col for col in hover_cols if col in df.columns]
    
    # Create scatter plot
    if df[color_col].nunique() <= 20:  # Use discrete colors for small number of groups
        colors = color_manager.get_plate_colors(df[color_col].nunique())
        color_discrete_map = dict(zip(df[color_col].unique(), colors))
        
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col,
            color=color_col,
            size=size_col,
            hover_data=available_hover_cols,
            color_discrete_map=color_discrete_map,
            opacity=0.7
        )
    else:  # Use continuous color scale for many groups
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col,
            color=color_col,
            size=size_col,
            hover_data=available_hover_cols,
            color_continuous_scale=color_manager.get_sequential_colormap(),
            opacity=0.7
        )
    
    # Add diagonal reference line if both axes represent similar metrics
    if ('Ratio' in x_col and 'Ratio' in y_col) or ('Z_' in x_col and 'Z_' in y_col):
        # Find plot range
        x_range = [df[x_col].quantile(0.01), df[x_col].quantile(0.99)]
        y_range = [df[y_col].quantile(0.01), df[y_col].quantile(0.99)]
        
        # Diagonal line range
        line_min = max(x_range[0], y_range[0])
        line_max = min(x_range[1], y_range[1])
        
        fig.add_trace(
            go.Scatter(
                x=[line_min, line_max],
                y=[line_min, line_max],
                mode='lines',
                name='y = x',
                line=dict(color='gray', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            )
        )
    
    # Apply theme and update layout
    fig = PlotlyTheme.apply_theme(fig, title)
    fig.update_xaxes(title_text=x_col.replace('_', ' '))
    fig.update_yaxes(title_text=y_col.replace('_', ' '))
    
    # Add correlation annotation if both columns are numeric
    try:
        correlation = df[[x_col, y_col]].corr().iloc[0, 1]
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"r = {correlation:.3f}",
            showarrow=False,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1,
            font=dict(size=12)
        )
    except:
        pass  # Skip correlation if calculation fails
    
    return fig


def create_viability_bar_chart(
    df: pd.DataFrame,
    plate_col: str = 'PlateID',
    viability_col: str = 'Viable',
    title: str = 'Viability Counts by Plate'
) -> go.Figure:
    """
    Create bar chart showing viability counts per plate.
    
    Args:
        df: DataFrame with viability data
        plate_col: Column name for plate identification
        viability_col: Column name for viability flag (True/False)
        title: Plot title
    
    Returns:
        Plotly Figure object
    
    Example:
        >>> fig = create_viability_bar_chart(df, 'PlateID', 'Viable')
    """
    # Validate columns
    if plate_col not in df.columns:
        raise ValueError(f"Column '{plate_col}' not found in data")
    if viability_col not in df.columns:
        raise ValueError(f"Column '{viability_col}' not found in data")
    
    # Calculate viability counts
    viability_counts = df.groupby([plate_col, viability_col]).size().unstack(fill_value=0)
    
    # Handle case where only one viability state is present
    if True not in viability_counts.columns:
        viability_counts[True] = 0
    if False not in viability_counts.columns:
        viability_counts[False] = 0
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            name='Non-viable',
            x=viability_counts.index,
            y=viability_counts[False],
            marker_color='#d62728',  # Red
            opacity=0.8
        )
    )
    
    fig.add_trace(
        go.Bar(
            name='Viable',
            x=viability_counts.index,
            y=viability_counts[True],
            marker_color='#2ca02c',  # Green
            opacity=0.8
        )
    )
    
    # Apply theme and update layout
    fig = PlotlyTheme.apply_theme(fig, title)
    fig.update_xaxes(title_text='Plate ID')
    fig.update_yaxes(title_text='Number of Wells')
    fig.update_layout(barmode='stack')
    
    # Add percentage annotations
    for i, plate_id in enumerate(viability_counts.index):
        total_wells = viability_counts.loc[plate_id].sum()
        viable_wells = viability_counts.loc[plate_id, True]
        viable_pct = (viable_wells / total_wells * 100) if total_wells > 0 else 0
        
        fig.add_annotation(
            x=i,
            y=total_wells + total_wells * 0.02,
            text=f"{viable_pct:.1f}%",
            showarrow=False,
            font=dict(size=10),
            xanchor='center'
        )
    
    return fig


def create_zscore_comparison_chart(
    df: pd.DataFrame,
    raw_col: str,
    bscore_col: str,
    title: str = 'Raw Z-score vs B-score Comparison'
) -> go.Figure:
    """
    Create side-by-side comparison of Raw Z vs B-score distributions.
    
    Args:
        df: DataFrame containing both score types
        raw_col: Column name for raw Z-scores
        bscore_col: Column name for B-scores
        title: Plot title
    
    Returns:
        Plotly Figure object with subplots
    
    Example:
        >>> fig = create_zscore_comparison_chart(df, 'Z_lptA', 'B_lptA')
    """
    # Validate columns
    missing_cols = [col for col in [raw_col, bscore_col] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(f'Raw Z-scores ({raw_col})', f'B-scores ({bscore_col})'),
        shared_yaxis=True
    )
    
    # Clean data
    raw_data = df[raw_col].dropna()
    bscore_data = df[bscore_col].dropna()
    
    # Determine common bin range for comparison
    all_data = pd.concat([raw_data, bscore_data])
    data_range = [all_data.quantile(0.001), all_data.quantile(0.999)]
    bins = np.linspace(data_range[0], data_range[1], 40)
    
    # Add raw Z-score histogram
    fig.add_trace(
        go.Histogram(
            x=raw_data,
            xbins=dict(start=data_range[0], end=data_range[1], size=(data_range[1]-data_range[0])/40),
            name='Raw Z',
            marker_color=COLORBLIND_FRIENDLY_PALETTE[0],
            opacity=0.7,
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add B-score histogram
    fig.add_trace(
        go.Histogram(
            x=bscore_data,
            xbins=dict(start=data_range[0], end=data_range[1], size=(data_range[1]-data_range[0])/40),
            name='B-score',
            marker_color=COLORBLIND_FRIENDLY_PALETTE[1],
            opacity=0.7,
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Add reference lines at 0
    for col in [1, 2]:
        fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.7, row=1, col=col)
    
    # Apply theme
    fig = PlotlyTheme.apply_theme(fig, title)
    fig.update_xaxes(title_text='Z-score', row=1, col=1)
    fig.update_xaxes(title_text='B-score', row=1, col=2)
    fig.update_yaxes(title_text='Frequency', row=1, col=1)
    
    # Add summary statistics
    raw_stats = f"μ={raw_data.mean():.2f}, σ={raw_data.std():.2f}"
    bscore_stats = f"μ={bscore_data.mean():.2f}, σ={bscore_data.std():.2f}"
    
    fig.add_annotation(x=0.24, y=1.02, xref='paper', yref='paper',
                      text=raw_stats, showarrow=False, font=dict(size=10))
    fig.add_annotation(x=0.74, y=1.02, xref='paper', yref='paper',
                      text=bscore_stats, showarrow=False, font=dict(size=10))
    
    return fig


def create_multi_metric_histogram(
    df: pd.DataFrame,
    columns: List[str],
    title: str = 'Multi-Metric Distribution',
    overlay: bool = True
) -> go.Figure:
    """
    Create histogram comparing multiple metrics on the same plot.
    
    Args:
        df: DataFrame containing the metrics
        columns: List of column names to plot
        title: Plot title
        overlay: If True, overlay histograms; if False, create subplots
    
    Returns:
        Plotly Figure object
    
    Example:
        >>> fig = create_multi_metric_histogram(df, ['Ratio_lptA', 'Ratio_ldtD'])
    """
    # Validate columns
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    if overlay:
        fig = go.Figure()
        colors = color_manager.get_plate_colors(len(columns))
        
        for i, col in enumerate(columns):
            clean_data = df[col].dropna()
            fig.add_trace(
                go.Histogram(
                    x=clean_data,
                    name=col.replace('_', ' '),
                    marker_color=colors[i],
                    opacity=0.6,
                    nbinsx=30
                )
            )
        
        fig.update_layout(barmode='overlay')
        fig = PlotlyTheme.apply_theme(fig, title)
        fig.update_xaxes(title_text='Value')
        fig.update_yaxes(title_text='Frequency')
        
    else:
        # Create subplots
        n_cols = min(2, len(columns))
        n_rows = (len(columns) + n_cols - 1) // n_cols
        
        fig = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=[col.replace('_', ' ') for col in columns]
        )
        
        colors = color_manager.get_plate_colors(len(columns))
        
        for i, col in enumerate(columns):
            row = i // n_cols + 1
            col_idx = i % n_cols + 1
            
            clean_data = df[col].dropna()
            fig.add_trace(
                go.Histogram(
                    x=clean_data,
                    name=col.replace('_', ' '),
                    marker_color=colors[i],
                    opacity=0.7,
                    nbinsx=30,
                    showlegend=False
                ),
                row=row, col=col_idx
            )
        
        fig = PlotlyTheme.apply_theme(fig, title)
    
    return fig


# Export main functions
__all__ = [
    'create_histogram_with_overlay',
    'create_scatter_plot',
    'create_viability_bar_chart',
    'create_zscore_comparison_chart',
    'create_multi_metric_histogram'
]