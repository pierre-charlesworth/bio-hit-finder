"""
Bio-Hit-Finder Comprehensive Figure Legend System

This package provides intelligent, scientifically rigorous figure legends for all
visualizations in the bio-hit-finder platform. The system supports multiple
expertise levels (basic, intermediate, expert) and output formats (Streamlit, PDF, HTML).

Core Components:
- Data models for legend content and metadata
- Template system for chart-type specific legends
- Context extraction from data analysis results
- Multi-format output (HTML, PDF, Streamlit, plain text)
- Integration layer for existing visualization functions

Usage:
    from visualizations.legends import LegendManager, ChartType, ExpertiseLevel
    
    manager = LegendManager()
    legend = manager.create_legend(
        data=df, 
        chart_type=ChartType.HEATMAP,
        expertise_level=ExpertiseLevel.INTERMEDIATE
    )

Author: Bio-Hit-Finder Platform Team
Version: 1.0.0
License: MIT
"""

from .models import (
    ChartType,
    ExpertiseLevel,
    OutputFormat,
    LegendMetadata,
    LegendContent,
    StatisticalContext,
    BiologicalContext,
    TechnicalContext
)

from .core import (
    LegendManager,
    LegendContext,
    MetadataExtractor
)

from .templates import (
    TemplateRegistry,
    HeatmapTemplate,
    HistogramTemplate,
    ScatterPlotTemplate
)

from .formatters import (
    HTMLFormatter,
    StreamlitFormatter,
    PDFFormatter,
    PlainTextFormatter
)

from .integration import (
    VisualizationIntegrator,
    StreamlitIntegration,
    PDFIntegration
)

__version__ = "1.0.0"
__author__ = "Bio-Hit-Finder Platform Team"
__all__ = [
    # Core enums and data models
    "ChartType",
    "ExpertiseLevel", 
    "OutputFormat",
    "LegendMetadata",
    "LegendContent",
    "StatisticalContext",
    "BiologicalContext", 
    "TechnicalContext",
    
    # Core functionality
    "LegendManager",
    "LegendContext",
    "MetadataExtractor",
    
    # Template system
    "TemplateRegistry",
    "HeatmapTemplate",
    "HistogramTemplate", 
    "ScatterPlotTemplate",
    
    # Output formatters
    "HTMLFormatter",
    "StreamlitFormatter",
    "PDFFormatter",
    "PlainTextFormatter",
    
    # Integration layer
    "VisualizationIntegrator",
    "StreamlitIntegration",
    "PDFIntegration"
]