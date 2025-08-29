"""
Visualization modules for bio-hit-finder platform.

This package provides comprehensive visualization capabilities for biological
plate data analysis, including interactive charts, heatmaps, and export utilities.

Modules:
    - styling: Color palettes, themes, and styling utilities
    - charts: Interactive Plotly-based chart components
    - heatmaps: Specialized plate heatmap visualizations
    - export_plots: High-quality export and publication-ready plots
"""

from .styling import (
    PlotlyTheme,
    ColorManager,
    StreamlitCSS,
    color_manager,
    COLORBLIND_FRIENDLY_PALETTE,
    PLATE_COLORS,
    get_figure_export_config,
    format_number_for_display
)

from .charts import (
    create_histogram_with_overlay,
    create_scatter_plot,
    create_viability_bar_chart,
    create_zscore_comparison_chart,
    create_multi_metric_histogram
)

from .heatmaps import (
    create_plate_heatmap,
    create_comparison_heatmaps,
    create_multi_plate_heatmap,
    detect_plate_format,
    format_well_positions,
    handle_missing_wells,
    PLATE_LAYOUTS
)

from .export_plots import (
    PlotExporter,
    create_pdf_compatible_plots,
    create_summary_figure
)

# Version info
__version__ = '1.0.0'

# Main exports for easy importing
__all__ = [
    # Styling utilities
    'PlotlyTheme',
    'ColorManager', 
    'StreamlitCSS',
    'color_manager',
    'COLORBLIND_FRIENDLY_PALETTE',
    'PLATE_COLORS',
    'get_figure_export_config',
    'format_number_for_display',
    
    # Chart functions
    'create_histogram_with_overlay',
    'create_scatter_plot',
    'create_viability_bar_chart',
    'create_zscore_comparison_chart',
    'create_multi_metric_histogram',
    
    # Heatmap functions
    'create_plate_heatmap',
    'create_comparison_heatmaps',
    'create_multi_plate_heatmap',
    'detect_plate_format',
    'format_well_positions',
    'handle_missing_wells',
    'PLATE_LAYOUTS',
    
    # Export functions
    'PlotExporter',
    'create_pdf_compatible_plots',
    'create_summary_figure'
]