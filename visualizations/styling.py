"""
Styling configuration and themes for bio-hit-finder visualizations.

This module provides consistent color palettes, themes, and styling utilities
for all visualization components in the platform.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Union, Optional
import yaml
from pathlib import Path


# Color palettes - color-blind friendly
COLORBLIND_FRIENDLY_PALETTE = [
    '#1f77b4',  # blue
    '#ff7f0e',  # orange
    '#2ca02c',  # green
    '#d62728',  # red
    '#9467bd',  # purple
    '#8c564b',  # brown
    '#e377c2',  # pink
    '#7f7f7f',  # gray
    '#bcbd22',  # olive
    '#17becf'   # cyan
]

# Plate-specific color palette (for multi-plate studies)
PLATE_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
    '#5254a3', '#8ca252', '#bd9e39', '#ad494a', '#a55194'
]

# Diverging colormaps for Z-scores and B-scores (centered at 0)
DIVERGING_COLORMAPS = {
    'default': 'RdBu_r',
    'spectral': 'Spectral',
    'coolwarm': 'RdYlBu_r',
    'balanced': 'balance'
}

# Sequential colormaps for ratios and OD values
SEQUENTIAL_COLORMAPS = {
    'default': 'viridis',
    'plasma': 'plasma',
    'inferno': 'inferno',
    'magma': 'magma',
    'cividis': 'cividis'
}

# Viridis-based colormap for viability (good -> bad)
VIABILITY_COLORMAP = 'viridis_r'  # Reversed so dark = low viability


class PlotlyTheme:
    """Centralized Plotly theme configuration for consistent styling."""
    
    @staticmethod
    def get_base_layout() -> Dict:
        """Get base layout configuration for all Plotly figures."""
        return {
            'font': {
                'family': 'Arial, sans-serif',
                'size': 12,
                'color': '#2E3440'
            },
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': {'l': 60, 'r': 20, 't': 60, 'b': 60},
            'showlegend': True,
            'legend': {
                'orientation': 'v',
                'yanchor': 'top',
                'y': 1,
                'xanchor': 'left',
                'x': 1.02
            },
            'hovermode': 'closest'
        }
    
    @staticmethod
    def get_axis_style() -> Dict:
        """Get consistent axis styling."""
        return {
            'linecolor': '#E5E5E5',
            'linewidth': 1,
            'gridcolor': '#F0F0F0',
            'gridwidth': 1,
            'zeroline': True,
            'zerolinecolor': '#E5E5E5',
            'zerolinewidth': 2,
            'tickfont': {'size': 10, 'color': '#2E3440'},
            'titlefont': {'size': 12, 'color': '#2E3440'}
        }
    
    @staticmethod
    def apply_theme(fig: go.Figure, title: Optional[str] = None) -> go.Figure:
        """Apply consistent theme to a Plotly figure."""
        layout_updates = PlotlyTheme.get_base_layout()
        axis_style = PlotlyTheme.get_axis_style()
        
        layout_updates.update({
            'xaxis': axis_style,
            'yaxis': axis_style
        })
        
        if title:
            layout_updates['title'] = {
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 14, 'color': '#2E3440'}
            }
        
        fig.update_layout(**layout_updates)
        return fig


class ColorManager:
    """Manages color palettes and colormap selection."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize ColorManager with optional config file."""
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            # Default config path relative to project root
            config_path = Path(__file__).parent.parent / 'config.yaml'
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('visualization', {})
        except (FileNotFoundError, yaml.YAMLError):
            # Return default config if file not found or invalid
            return {
                'colormaps': {
                    'diverging': 'RdBu_r',
                    'sequential': 'viridis'
                }
            }
    
    def get_plate_colors(self, n_plates: int) -> List[str]:
        """Get color palette for multiple plates."""
        if n_plates <= len(PLATE_COLORS):
            return PLATE_COLORS[:n_plates]
        else:
            # Extend palette by cycling through colors
            extended = PLATE_COLORS * ((n_plates // len(PLATE_COLORS)) + 1)
            return extended[:n_plates]
    
    def get_diverging_colormap(self, custom: Optional[str] = None) -> str:
        """Get diverging colormap (for Z-scores, B-scores)."""
        if custom:
            return custom
        return self.config.get('colormaps', {}).get('diverging', 'RdBu_r')
    
    def get_sequential_colormap(self, custom: Optional[str] = None) -> str:
        """Get sequential colormap (for ratios, OD values)."""
        if custom:
            return custom
        return self.config.get('colormaps', {}).get('sequential', 'viridis')
    
    def get_viability_colormap(self) -> str:
        """Get colormap for viability visualization."""
        return VIABILITY_COLORMAP


class StreamlitCSS:
    """Custom CSS for Streamlit integration."""
    
    @staticmethod
    def get_plot_container_css() -> str:
        """CSS for plot containers in Streamlit."""
        return """
        <style>
        .plot-container {
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        }
        
        .plot-title {
            font-family: 'Arial', sans-serif;
            font-size: 16px;
            font-weight: bold;
            color: #2E3440;
            text-align: center;
            margin-bottom: 10px;
        }
        
        .plot-subtitle {
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            color: #666666;
            text-align: center;
            margin-bottom: 15px;
        }
        </style>
        """
    
    @staticmethod
    def get_heatmap_css() -> str:
        """CSS specifically for heatmap visualizations."""
        return """
        <style>
        .heatmap-container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        
        .heatmap-legend {
            font-family: 'Arial', sans-serif;
            font-size: 10px;
            color: #2E3440;
            text-align: center;
            margin-top: 5px;
        }
        
        .well-tooltip {
            background-color: rgba(0,0,0,0.8);
            color: white;
            padding: 5px;
            border-radius: 3px;
            font-size: 11px;
        }
        </style>
        """


def get_figure_export_config() -> Dict:
    """Get configuration for figure exports (PNG, SVG, PDF)."""
    return {
        'width': 1200,
        'height': 800,
        'scale': 2,  # For high DPI
        'format': 'png',
        'engine': 'kaleido'
    }


def format_number_for_display(value: float, precision: int = 3) -> str:
    """Format numbers consistently for display in plots."""
    if abs(value) < 1e-3 and value != 0:
        return f"{value:.2e}"
    elif abs(value) < 1:
        return f"{value:.{precision}f}"
    elif abs(value) < 100:
        return f"{value:.{max(0, precision-1)}f}"
    else:
        return f"{value:.0f}"


# Global color manager instance
color_manager = ColorManager()

# Export commonly used items
__all__ = [
    'COLORBLIND_FRIENDLY_PALETTE',
    'PLATE_COLORS', 
    'DIVERGING_COLORMAPS',
    'SEQUENTIAL_COLORMAPS',
    'VIABILITY_COLORMAP',
    'PlotlyTheme',
    'ColorManager',
    'StreamlitCSS',
    'color_manager',
    'get_figure_export_config',
    'format_number_for_display'
]