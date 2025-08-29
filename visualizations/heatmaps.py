"""
Plate heatmap visualization components for bio-hit-finder platform.

This module provides specialized heatmap visualizations for microplate data,
supporting 96-well and 384-well plate formats with proper handling of 
missing wells and standardized layouts.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Union
import re
import warnings

from .styling import (
    PlotlyTheme,
    color_manager,
    format_number_for_display
)


# Standard plate layouts
PLATE_LAYOUTS = {
    '96-well': {'rows': 8, 'cols': 12, 'row_labels': 'ABCDEFGH'},
    '384-well': {'rows': 16, 'cols': 24, 'row_labels': 'ABCDEFGHIJKLMNOP'}
}


def detect_plate_format(df: pd.DataFrame, well_col: str = 'Well') -> str:
    """
    Detect plate format (96-well or 384-well) from well positions.
    
    Args:
        df: DataFrame containing well data
        well_col: Column name containing well positions (e.g., 'A01', 'H12')
    
    Returns:
        Plate format string ('96-well' or '384-well')
    
    Example:
        >>> format_type = detect_plate_format(df, 'Well')
        >>> print(format_type)  # '96-well'
    """
    if well_col not in df.columns:
        warnings.warn(f"Well column '{well_col}' not found, defaulting to 96-well")
        return '96-well'
    
    wells = df[well_col].dropna().unique()
    
    # Extract row letters and column numbers
    max_row = 0
    max_col = 0
    
    for well in wells:
        well_str = str(well).upper().strip()
        match = re.match(r'^([A-P])(\d{1,2})$', well_str)
        
        if match:
            row_letter, col_num = match.groups()
            row_idx = ord(row_letter) - ord('A') + 1
            col_idx = int(col_num)
            
            max_row = max(max_row, row_idx)
            max_col = max(max_col, col_idx)
    
    # Determine format based on max dimensions
    if max_row <= 8 and max_col <= 12:
        return '96-well'
    elif max_row <= 16 and max_col <= 24:
        return '384-well'
    else:
        warnings.warn(f"Unusual plate dimensions ({max_row}x{max_col}), defaulting to 96-well")
        return '96-well'


def format_well_positions(df: pd.DataFrame, well_col: str = 'Well') -> pd.DataFrame:
    """
    Convert well positions to standardized row/column indices for matrix layout.
    
    Args:
        df: DataFrame containing well data
        well_col: Column name containing well positions
    
    Returns:
        DataFrame with additional 'Row_Idx' and 'Col_Idx' columns
    
    Example:
        >>> df_formatted = format_well_positions(df, 'Well')
        >>> print(df_formatted[['Well', 'Row_Idx', 'Col_Idx']].head())
    """
    if well_col not in df.columns:
        raise ValueError(f"Well column '{well_col}' not found in DataFrame")
    
    df_copy = df.copy()
    df_copy['Row_Idx'] = np.nan
    df_copy['Col_Idx'] = np.nan
    
    for idx, well in enumerate(df_copy[well_col]):
        well_str = str(well).upper().strip() if pd.notna(well) else ''
        match = re.match(r'^([A-P])(\d{1,2})$', well_str)
        
        if match:
            row_letter, col_num = match.groups()
            df_copy.loc[idx, 'Row_Idx'] = ord(row_letter) - ord('A')  # 0-indexed
            df_copy.loc[idx, 'Col_Idx'] = int(col_num) - 1  # 0-indexed
    
    return df_copy


def handle_missing_wells(matrix: np.ndarray, fill_value: float = np.nan) -> np.ndarray:
    """
    Handle missing wells in plate matrix by filling with specified value.
    
    Args:
        matrix: 2D numpy array representing plate data
        fill_value: Value to use for missing wells
    
    Returns:
        Matrix with missing wells properly handled
    """
    # Replace any existing NaN values with fill_value
    matrix = np.where(np.isnan(matrix), fill_value, matrix)
    return matrix


def create_plate_heatmap(
    df: pd.DataFrame,
    metric_col: str,
    plate_layout: str = 'auto',
    title: str = '',
    well_col: str = 'Well',
    plate_id: Optional[str] = None,
    colormap: Optional[str] = None,
    center_colormap: bool = None
) -> go.Figure:
    """
    Create plate heatmap visualization with proper well layout.
    
    Args:
        df: DataFrame containing plate data
        metric_col: Column name for the metric to visualize
        plate_layout: Plate format ('96-well', '384-well', or 'auto')
        title: Plot title
        well_col: Column name containing well positions
        plate_id: Optional plate ID to filter data
        colormap: Custom colormap name
        center_colormap: Whether to center colormap at 0 (auto-detect if None)
    
    Returns:
        Plotly Figure object
    
    Example:
        >>> fig = create_plate_heatmap(df, 'Z_lptA', title='Z-scores for lptA')
    """
    # Validate inputs
    if metric_col not in df.columns:
        raise ValueError(f"Metric column '{metric_col}' not found in DataFrame")
    if well_col not in df.columns:
        raise ValueError(f"Well column '{well_col}' not found in DataFrame")
    
    # Filter by plate if specified
    if plate_id is not None and 'PlateID' in df.columns:
        df = df[df['PlateID'] == plate_id].copy()
        if len(df) == 0:
            raise ValueError(f"No data found for plate '{plate_id}'")
    
    # Auto-detect plate format if needed
    if plate_layout == 'auto':
        plate_layout = detect_plate_format(df, well_col)
    
    if plate_layout not in PLATE_LAYOUTS:
        raise ValueError(f"Unsupported plate layout: {plate_layout}")
    
    layout_info = PLATE_LAYOUTS[plate_layout]
    n_rows, n_cols = layout_info['rows'], layout_info['cols']
    row_labels = list(layout_info['row_labels'])
    col_labels = [str(i) for i in range(1, n_cols + 1)]
    
    # Format well positions
    df_formatted = format_well_positions(df, well_col)
    
    # Create matrix for heatmap
    matrix = np.full((n_rows, n_cols), np.nan)
    hover_text = np.full((n_rows, n_cols), '', dtype=object)
    
    # Fill matrix with data
    for _, row in df_formatted.iterrows():
        if pd.notna(row['Row_Idx']) and pd.notna(row['Col_Idx']):
            r_idx = int(row['Row_Idx'])
            c_idx = int(row['Col_Idx'])
            
            if 0 <= r_idx < n_rows and 0 <= c_idx < n_cols:
                value = row[metric_col]
                matrix[r_idx, c_idx] = value
                
                # Create hover text
                well_id = row[well_col]
                if pd.notna(value):
                    hover_text[r_idx, c_idx] = (
                        f"Well: {well_id}<br>"
                        f"{metric_col}: {format_number_for_display(value)}"
                    )
                else:
                    hover_text[r_idx, c_idx] = f"Well: {well_id}<br>No data"
    
    # Determine colormap
    if colormap is None:
        # Auto-detect based on metric type
        if center_colormap is None:
            center_colormap = ('Z_' in metric_col or 'B_' in metric_col or 
                             metric_col.lower() in ['zscore', 'bscore'])
        
        if center_colormap:
            colormap = color_manager.get_diverging_colormap()
        else:
            colormap = color_manager.get_sequential_colormap()
    
    # Create heatmap
    fig = go.Figure()
    
    # Handle colorscale centering
    if center_colormap:
        # Center colorscale at 0
        data_range = np.nanmax(np.abs(matrix))
        if data_range > 0:
            zmid = 0
            zmin = -data_range
            zmax = data_range
        else:
            zmid = zmin = zmax = 0
    else:
        # Use data range
        finite_data = matrix[np.isfinite(matrix)]
        if len(finite_data) > 0:
            zmin = np.nanmin(finite_data)
            zmax = np.nanmax(finite_data)
            zmid = None
        else:
            zmin = zmax = zmid = 0
    
    # Add heatmap trace
    heatmap_args = {
        'z': matrix,
        'x': col_labels,
        'y': row_labels,
        'colorscale': colormap,
        'hovertemplate': '%{text}<extra></extra>',
        'text': hover_text,
        'showscale': True,
        'colorbar': {
            'title': metric_col.replace('_', ' '),
            'titleside': 'right'
        }
    }
    
    if center_colormap and zmid is not None:
        heatmap_args.update({'zmid': zmid, 'zmin': zmin, 'zmax': zmax})
    else:
        heatmap_args.update({'zmin': zmin, 'zmax': zmax})
    
    fig.add_trace(go.Heatmap(**heatmap_args))
    
    # Update layout
    fig = PlotlyTheme.apply_theme(fig, title)
    fig.update_xaxes(
        title_text='Column',
        side='top',
        tickmode='array',
        tickvals=list(range(len(col_labels))),
        ticktext=col_labels
    )
    fig.update_yaxes(
        title_text='Row',
        tickmode='array',
        tickvals=list(range(len(row_labels))),
        ticktext=row_labels,
        autorange='reversed'  # A at top
    )
    
    # Ensure square aspect ratio
    fig.update_layout(
        width=max(400, n_cols * 30),
        height=max(300, n_rows * 30 + 100),
        xaxis=dict(constrain='domain'),
        yaxis=dict(scaleanchor='x', scaleratio=1)
    )
    
    return fig


def create_comparison_heatmaps(
    df: pd.DataFrame,
    metric1: str,
    metric2: str,
    plate_id: Optional[str] = None,
    title: str = 'Metric Comparison',
    well_col: str = 'Well',
    plate_layout: str = 'auto'
) -> go.Figure:
    """
    Create side-by-side comparison heatmaps (e.g., Raw Z vs B-score).
    
    Args:
        df: DataFrame containing both metrics
        metric1: First metric column name (e.g., 'Z_lptA')
        metric2: Second metric column name (e.g., 'B_lptA')
        plate_id: Optional plate ID to filter data
        title: Overall plot title
        well_col: Column name containing well positions
        plate_layout: Plate format ('96-well', '384-well', or 'auto')
    
    Returns:
        Plotly Figure with side-by-side heatmaps
    
    Example:
        >>> fig = create_comparison_heatmaps(df, 'Z_lptA', 'B_lptA', 
        ...                                 title='Raw Z vs B-score Comparison')
    """
    # Validate inputs
    missing_cols = [col for col in [metric1, metric2] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Filter by plate if specified
    if plate_id is not None and 'PlateID' in df.columns:
        df = df[df['PlateID'] == plate_id].copy()
        if len(df) == 0:
            raise ValueError(f"No data found for plate '{plate_id}'")
    
    # Auto-detect plate format
    if plate_layout == 'auto':
        plate_layout = detect_plate_format(df, well_col)
    
    layout_info = PLATE_LAYOUTS[plate_layout]
    n_rows, n_cols = layout_info['rows'], layout_info['cols']
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f'{metric1.replace("_", " ")}',
            f'{metric2.replace("_", " ")}'
        ),
        horizontal_spacing=0.15,
        shared_yaxes=True
    )
    
    # Determine common color scale for comparison
    all_data = pd.concat([df[metric1].dropna(), df[metric2].dropna()])
    if len(all_data) > 0:
        data_range = max(abs(all_data.min()), abs(all_data.max()))
        zmin, zmax = -data_range, data_range
        zmid = 0
    else:
        zmin = zmax = zmid = 0
    
    # Get colormap (assuming Z-scores or B-scores)
    colormap = color_manager.get_diverging_colormap()
    
    # Create heatmaps for each metric
    for i, metric in enumerate([metric1, metric2]):
        df_formatted = format_well_positions(df, well_col)
        
        # Create matrix
        matrix = np.full((n_rows, n_cols), np.nan)
        hover_text = np.full((n_rows, n_cols), '', dtype=object)
        
        row_labels = list(layout_info['row_labels'])
        col_labels = [str(j) for j in range(1, n_cols + 1)]
        
        # Fill matrix
        for _, row in df_formatted.iterrows():
            if pd.notna(row['Row_Idx']) and pd.notna(row['Col_Idx']):
                r_idx = int(row['Row_Idx'])
                c_idx = int(row['Col_Idx'])
                
                if 0 <= r_idx < n_rows and 0 <= c_idx < n_cols:
                    value = row[metric]
                    matrix[r_idx, c_idx] = value
                    
                    well_id = row[well_col]
                    if pd.notna(value):
                        hover_text[r_idx, c_idx] = (
                            f"Well: {well_id}<br>"
                            f"{metric}: {format_number_for_display(value)}"
                        )
                    else:
                        hover_text[r_idx, c_idx] = f"Well: {well_id}<br>No data"
        
        # Add heatmap trace
        show_colorbar = (i == 1)  # Only show colorbar for second plot
        fig.add_trace(
            go.Heatmap(
                z=matrix,
                x=col_labels,
                y=row_labels,
                colorscale=colormap,
                zmin=zmin,
                zmax=zmax,
                zmid=zmid,
                hovertemplate='%{text}<extra></extra>',
                text=hover_text,
                showscale=show_colorbar,
                colorbar={'title': 'Score', 'titleside': 'right'} if show_colorbar else None
            ),
            row=1, col=i+1
        )
    
    # Update layout
    fig = PlotlyTheme.apply_theme(fig, title)
    
    # Update axes for both subplots
    for i in range(1, 3):
        fig.update_xaxes(
            title_text='Column',
            side='top',
            row=1, col=i
        )
        if i == 1:  # Only label y-axis for first subplot
            fig.update_yaxes(
                title_text='Row',
                autorange='reversed',
                row=1, col=i
            )
        else:
            fig.update_yaxes(
                autorange='reversed',
                showticklabels=False,
                row=1, col=i
            )
    
    # Ensure consistent sizing
    fig.update_layout(
        width=max(800, n_cols * 60),
        height=max(400, n_rows * 30 + 100)
    )
    
    return fig


def create_multi_plate_heatmap(
    df: pd.DataFrame,
    metric_col: str,
    plate_col: str = 'PlateID',
    max_plates: int = 6,
    title: str = 'Multi-Plate Comparison',
    well_col: str = 'Well',
    plate_layout: str = 'auto'
) -> go.Figure:
    """
    Create multiple heatmaps for comparing the same metric across plates.
    
    Args:
        df: DataFrame containing multi-plate data
        metric_col: Column name for the metric to visualize
        plate_col: Column name for plate identification
        max_plates: Maximum number of plates to display
        title: Overall plot title
        well_col: Column name containing well positions
        plate_layout: Plate format ('96-well', '384-well', or 'auto')
    
    Returns:
        Plotly Figure with multiple heatmap subplots
    
    Example:
        >>> fig = create_multi_plate_heatmap(df, 'Z_lptA', 'PlateID', 
        ...                                 title='Z_lptA Across Plates')
    """
    if plate_col not in df.columns:
        raise ValueError(f"Plate column '{plate_col}' not found in DataFrame")
    if metric_col not in df.columns:
        raise ValueError(f"Metric column '{metric_col}' not found in DataFrame")
    
    # Get unique plates
    plates = df[plate_col].unique()[:max_plates]
    n_plates = len(plates)
    
    if n_plates == 0:
        raise ValueError("No plates found in data")
    
    # Determine subplot layout
    if n_plates <= 2:
        rows, cols = 1, n_plates
    elif n_plates <= 4:
        rows, cols = 2, 2
    elif n_plates <= 6:
        rows, cols = 2, 3
    else:
        rows, cols = 3, 3
    
    # Auto-detect plate format
    if plate_layout == 'auto':
        plate_layout = detect_plate_format(df, well_col)
    
    layout_info = PLATE_LAYOUTS[plate_layout]
    n_rows, n_cols = layout_info['rows'], layout_info['cols']
    
    # Create subplots
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f'Plate {plate}' for plate in plates],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # Determine common color scale
    all_data = df[metric_col].dropna()
    if len(all_data) > 0:
        if 'Z_' in metric_col or 'B_' in metric_col:
            # Diverging colormap centered at 0
            data_range = max(abs(all_data.min()), abs(all_data.max()))
            zmin, zmax, zmid = -data_range, data_range, 0
            colormap = color_manager.get_diverging_colormap()
        else:
            # Sequential colormap
            zmin, zmax, zmid = all_data.min(), all_data.max(), None
            colormap = color_manager.get_sequential_colormap()
    else:
        zmin = zmax = zmid = 0
        colormap = color_manager.get_sequential_colormap()
    
    # Create heatmap for each plate
    for i, plate in enumerate(plates):
        row_idx = i // cols + 1
        col_idx = i % cols + 1
        
        plate_data = df[df[plate_col] == plate]
        df_formatted = format_well_positions(plate_data, well_col)
        
        # Create matrix
        matrix = np.full((n_rows, n_cols), np.nan)
        hover_text = np.full((n_rows, n_cols), '', dtype=object)
        
        row_labels = list(layout_info['row_labels'])
        col_labels = [str(j) for j in range(1, n_cols + 1)]
        
        # Fill matrix
        for _, row in df_formatted.iterrows():
            if pd.notna(row['Row_Idx']) and pd.notna(row['Col_Idx']):
                r_idx = int(row['Row_Idx'])
                c_idx = int(row['Col_Idx'])
                
                if 0 <= r_idx < n_rows and 0 <= c_idx < n_cols:
                    value = row[metric_col]
                    matrix[r_idx, c_idx] = value
                    
                    well_id = row[well_col]
                    if pd.notna(value):
                        hover_text[r_idx, c_idx] = (
                            f"Plate: {plate}<br>"
                            f"Well: {well_id}<br>"
                            f"{metric_col}: {format_number_for_display(value)}"
                        )
                    else:
                        hover_text[r_idx, c_idx] = f"Plate: {plate}<br>Well: {well_id}<br>No data"
        
        # Add heatmap trace
        show_colorbar = (i == len(plates) - 1)  # Only show colorbar for last plot
        
        heatmap_args = {
            'z': matrix,
            'x': col_labels,
            'y': row_labels,
            'colorscale': colormap,
            'zmin': zmin,
            'zmax': zmax,
            'hovertemplate': '%{text}<extra></extra>',
            'text': hover_text,
            'showscale': show_colorbar
        }
        
        if zmid is not None:
            heatmap_args['zmid'] = zmid
        
        if show_colorbar:
            heatmap_args['colorbar'] = {
                'title': metric_col.replace('_', ' '),
                'titleside': 'right'
            }
        
        fig.add_trace(
            go.Heatmap(**heatmap_args),
            row=row_idx, col=col_idx
        )
        
        # Update axes for this subplot
        fig.update_xaxes(
            showticklabels=False,
            row=row_idx, col=col_idx
        )
        fig.update_yaxes(
            showticklabels=False,
            autorange='reversed',
            row=row_idx, col=col_idx
        )
    
    # Update layout
    fig = PlotlyTheme.apply_theme(fig, title)
    fig.update_layout(
        width=max(600, cols * 200),
        height=max(400, rows * 200)
    )
    
    return fig


# Export main functions
__all__ = [
    'detect_plate_format',
    'format_well_positions',
    'handle_missing_wells',
    'create_plate_heatmap',
    'create_comparison_heatmaps',
    'create_multi_plate_heatmap',
    'PLATE_LAYOUTS'
]