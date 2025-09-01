"""
Integration module for seamless legend integration with existing visualizations.

This module provides integration utilities that allow the legend system to work
with existing visualization functions without requiring major refactoring.
"""

from typing import Dict, List, Optional, Any, Union, Callable, Tuple
import logging
import inspect
from functools import wraps
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .core import LegendManager, LegendContext, LegendConfig
from .models import (
    ChartType, ExpertiseLevel, OutputFormat, LegendContent,
    LegendData
)
from .formatters import FormatterFactory

logger = logging.getLogger(__name__)


class VisualizationIntegrator:
    """Main integration class for adding legends to existing visualizations."""
    
    def __init__(self, legend_manager: Optional[LegendManager] = None):
        """Initialize integrator with legend manager.
        
        Args:
            legend_manager: LegendManager instance (creates default if None)
        """
        self.legend_manager = legend_manager or LegendManager()
        self._function_registry: Dict[str, ChartType] = {}
        self._integration_configs: Dict[str, Dict[str, Any]] = {}
        
        # Register default function mappings
        self._register_default_mappings()
    
    def _register_default_mappings(self):
        """Register default function name to chart type mappings."""
        
        mappings = {
            # Existing heatmap functions
            'create_plate_heatmap': ChartType.HEATMAP,
            'create_comparison_heatmaps': ChartType.COMPARISON_HEATMAP,
            'create_multi_plate_heatmap': ChartType.MULTI_PLATE_HEATMAP,
            
            # Existing chart functions
            'create_histogram_with_overlay': ChartType.HISTOGRAM,
            'create_scatter_plot': ChartType.SCATTER_PLOT,
            'create_viability_bar_chart': ChartType.BAR_CHART,
            'create_zscore_comparison_chart': ChartType.DISTRIBUTION_COMPARISON,
            'create_multi_metric_histogram': ChartType.HISTOGRAM,
            
            # QC dashboard
            'create_qc_dashboard': ChartType.QC_DASHBOARD,
            
            # PDF generator functions
            'create_distribution_plot': ChartType.HISTOGRAM,
            'create_zscore_overview': ChartType.BOX_PLOT
        }
        
        for func_name, chart_type in mappings.items():
            self._function_registry[func_name] = chart_type
    
    def register_function(self, function_name: str, chart_type: ChartType, 
                         config: Optional[Dict[str, Any]] = None):
        """Register a visualization function with its chart type.
        
        Args:
            function_name: Name of the visualization function
            chart_type: Type of chart it creates
            config: Optional configuration for integration
        """
        self._function_registry[function_name] = chart_type
        if config:
            self._integration_configs[function_name] = config
        
        logger.info(f"Registered function {function_name} as {chart_type.value}")
    
    def create_legend_decorator(self, 
                              chart_type: Optional[ChartType] = None,
                              expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
                              output_format: OutputFormat = OutputFormat.HTML,
                              auto_attach: bool = False) -> Callable:
        """Create a decorator that adds legend generation to visualization functions.
        
        Args:
            chart_type: Chart type (auto-detected if None)
            expertise_level: Target expertise level
            output_format: Output format for legend
            auto_attach: Whether to automatically attach legend to figure
            
        Returns:
            Decorator function
            
        Example:
            @integrator.create_legend_decorator(ChartType.HEATMAP)
            def my_heatmap_function(df, metric_col):
                # existing function code
                return fig
        """
        
        def decorator(func: Callable) -> Callable:
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                
                # Call original function
                result = func(*args, **kwargs)
                
                # Extract data from function arguments
                data = self._extract_data_from_args(func, args, kwargs)
                
                # Determine chart type
                detected_chart_type = chart_type
                if detected_chart_type is None:
                    detected_chart_type = self._detect_chart_type(func.__name__)
                
                if detected_chart_type and data is not None:
                    try:
                        # Create legend context
                        context = LegendContext(
                            data=data,
                            chart_type=detected_chart_type,
                            expertise_level=expertise_level,
                            output_format=output_format,
                            config=self._extract_config_from_kwargs(kwargs)
                        )
                        
                        # Generate legend
                        legend_content = self.legend_manager.generate_legend(context)
                        legend_text = self.legend_manager.format_legend(legend_content, output_format)
                        
                        # Attach legend to result if requested
                        if auto_attach and isinstance(result, go.Figure):
                            result = self._attach_legend_to_figure(result, legend_text, output_format)
                        
                        # Store legend in figure metadata for later retrieval
                        if isinstance(result, go.Figure):
                            if not hasattr(result, '_bio_hit_finder_legend'):
                                result._bio_hit_finder_legend = {}
                            result._bio_hit_finder_legend.update({
                                'content': legend_content,
                                'text': legend_text,
                                'context': context
                            })
                    
                    except Exception as e:
                        logger.warning(f"Failed to generate legend for {func.__name__}: {e}")
                
                return result
            
            return wrapper
        
        return decorator
    
    def add_legend_to_figure(self,
                           figure: go.Figure,
                           data: LegendData,
                           chart_type: ChartType,
                           expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
                           output_format: OutputFormat = OutputFormat.HTML,
                           custom_config: Optional[Dict[str, Any]] = None,
                           attach_to_figure: bool = False) -> Tuple[go.Figure, str]:
        """Add legend to an existing Plotly figure.
        
        Args:
            figure: Plotly figure to add legend to
            data: Data used to create the figure
            chart_type: Type of chart
            expertise_level: Target expertise level
            output_format: Output format for legend
            custom_config: Custom configuration
            attach_to_figure: Whether to attach legend directly to figure
            
        Returns:
            Tuple of (figure, legend_text)
        """
        
        # Create legend context
        context = LegendContext(
            data=data,
            chart_type=chart_type,
            expertise_level=expertise_level,
            output_format=output_format,
            config=custom_config or {}
        )
        
        # Generate legend
        legend_content = self.legend_manager.generate_legend(context)
        legend_text = self.legend_manager.format_legend(legend_content, output_format)
        
        # Store in figure metadata
        if not hasattr(figure, '_bio_hit_finder_legend'):
            figure._bio_hit_finder_legend = {}
        figure._bio_hit_finder_legend.update({
            'content': legend_content,
            'text': legend_text,
            'context': context
        })
        
        # Attach to figure if requested
        if attach_to_figure:
            figure = self._attach_legend_to_figure(figure, legend_text, output_format)
        
        return figure, legend_text
    
    def create_figure_with_legend(self,
                                 visualization_func: Callable,
                                 data: LegendData,
                                 chart_type: ChartType,
                                 expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
                                 output_format: OutputFormat = OutputFormat.HTML,
                                 layout_mode: str = 'side_by_side',
                                 **viz_kwargs) -> go.Figure:
        """Create a figure with integrated legend layout.
        
        Args:
            visualization_func: Function that creates the visualization
            data: Data for the visualization
            chart_type: Type of chart being created
            expertise_level: Target expertise level
            output_format: Output format (affects legend formatting)
            layout_mode: How to layout figure and legend ('side_by_side', 'below', 'popup')
            **viz_kwargs: Additional arguments for visualization function
            
        Returns:
            Combined figure with legend
        """
        
        # Create the main visualization
        main_fig = visualization_func(data, **viz_kwargs)
        
        # Generate legend
        context = LegendContext(
            data=data,
            chart_type=chart_type,
            expertise_level=expertise_level,
            output_format=OutputFormat.HTML,  # Force HTML for figure integration
            config=viz_kwargs
        )
        
        legend_content = self.legend_manager.generate_legend(context)
        legend_html = self.legend_manager.format_legend(legend_content, OutputFormat.HTML)
        
        # Create combined layout based on mode
        if layout_mode == 'side_by_side':
            return self._create_side_by_side_layout(main_fig, legend_html)
        elif layout_mode == 'below':
            return self._create_vertical_layout(main_fig, legend_html)
        else:
            # Default: attach to figure annotations
            return self._attach_legend_to_figure(main_fig, legend_html, OutputFormat.HTML)
    
    def extract_legend_from_figure(self, figure: go.Figure) -> Optional[Dict[str, Any]]:
        """Extract stored legend information from a figure.
        
        Args:
            figure: Figure with stored legend
            
        Returns:
            Dictionary with legend information or None
        """
        
        if hasattr(figure, '_bio_hit_finder_legend'):
            return figure._bio_hit_finder_legend
        
        return None
    
    def update_legend_expertise_level(self,
                                    figure: go.Figure,
                                    new_expertise_level: ExpertiseLevel) -> Optional[str]:
        """Update legend expertise level for an existing figure.
        
        Args:
            figure: Figure with stored legend
            new_expertise_level: New expertise level
            
        Returns:
            Updated legend text or None if no legend found
        """
        
        legend_info = self.extract_legend_from_figure(figure)
        if not legend_info or 'context' not in legend_info:
            return None
        
        # Update context
        context = legend_info['context']
        context.expertise_level = new_expertise_level
        
        # Regenerate legend
        legend_content = self.legend_manager.generate_legend(context)
        legend_text = self.legend_manager.format_legend(legend_content, context.output_format)
        
        # Update stored information
        figure._bio_hit_finder_legend.update({
            'content': legend_content,
            'text': legend_text,
            'context': context
        })
        
        return legend_text
    
    def _extract_data_from_args(self, func: Callable, args: tuple, kwargs: dict) -> Optional[LegendData]:
        """Extract data from function arguments."""
        
        try:
            # Get function signature
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # Common data parameter names
            data_param_names = ['df', 'data', 'dataframe', 'plate_data']
            
            # Check positional arguments
            for i, arg in enumerate(args):
                if i < len(param_names):
                    param_name = param_names[i]
                    if (isinstance(arg, pd.DataFrame) or 
                        param_name.lower() in data_param_names):
                        return arg
            
            # Check keyword arguments
            for param_name in data_param_names:
                if param_name in kwargs and isinstance(kwargs[param_name], pd.DataFrame):
                    return kwargs[param_name]
            
            # Try first DataFrame argument
            for arg in args:
                if isinstance(arg, pd.DataFrame):
                    return arg
            
            for value in kwargs.values():
                if isinstance(value, pd.DataFrame):
                    return value
        
        except Exception as e:
            logger.warning(f"Failed to extract data from function args: {e}")
        
        return None
    
    def _detect_chart_type(self, function_name: str) -> Optional[ChartType]:
        """Detect chart type from function name."""
        
        # Check registry
        if function_name in self._function_registry:
            return self._function_registry[function_name]
        
        # Pattern matching
        name_lower = function_name.lower()
        
        if 'heatmap' in name_lower:
            if 'comparison' in name_lower:
                return ChartType.COMPARISON_HEATMAP
            elif 'multi' in name_lower:
                return ChartType.MULTI_PLATE_HEATMAP
            else:
                return ChartType.HEATMAP
        elif 'histogram' in name_lower or 'hist' in name_lower:
            return ChartType.HISTOGRAM
        elif 'scatter' in name_lower:
            return ChartType.SCATTER_PLOT
        elif 'bar' in name_lower:
            return ChartType.BAR_CHART
        elif 'box' in name_lower:
            return ChartType.BOX_PLOT
        elif 'line' in name_lower:
            return ChartType.LINE_PLOT
        
        return None
    
    def _extract_config_from_kwargs(self, kwargs: dict) -> Dict[str, Any]:
        """Extract relevant configuration from function kwargs."""
        
        config = {}
        
        # Common configuration parameters
        config_params = [
            'title', 'metric_col', 'plate_layout', 'colormap', 
            'center_colormap', 'viability_threshold', 'x_col', 'y_col',
            'color_col', 'well_col', 'plate_col'
        ]
        
        for param in config_params:
            if param in kwargs:
                config[param] = kwargs[param]
        
        return config
    
    def _attach_legend_to_figure(self, 
                               figure: go.Figure, 
                               legend_text: str, 
                               output_format: OutputFormat) -> go.Figure:
        """Attach legend text to figure as annotation."""
        
        if output_format == OutputFormat.HTML:
            # For HTML, we can't directly embed in Plotly
            # Store for external rendering
            if not hasattr(figure, '_external_legend_html'):
                figure._external_legend_html = legend_text
        
        return figure
    
    def _create_side_by_side_layout(self, main_fig: go.Figure, legend_html: str) -> go.Figure:
        """Create side-by-side layout with figure and legend."""
        
        # This would require custom HTML/CSS layout
        # For now, store legend for external rendering
        main_fig._external_legend_html = legend_html
        main_fig._layout_mode = 'side_by_side'
        
        return main_fig
    
    def _create_vertical_layout(self, main_fig: go.Figure, legend_html: str) -> go.Figure:
        """Create vertical layout with figure above and legend below."""
        
        main_fig._external_legend_html = legend_html
        main_fig._layout_mode = 'below'
        
        return main_fig


class StreamlitIntegration:
    """Specialized integration for Streamlit applications."""
    
    def __init__(self, integrator: Optional[VisualizationIntegrator] = None):
        self.integrator = integrator or VisualizationIntegrator()
    
    def display_figure_with_legend(self,
                                  figure: go.Figure,
                                  data: LegendData,
                                  chart_type: ChartType,
                                  expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
                                  layout: str = 'tabs',
                                  custom_config: Optional[Dict[str, Any]] = None):
        """Display figure with legend in Streamlit.
        
        Args:
            figure: Plotly figure
            data: Data used for the figure
            chart_type: Chart type
            expertise_level: Expertise level for legend
            layout: Layout mode ('tabs', 'columns', 'expandable')
            custom_config: Custom configuration
        """
        
        import streamlit as st
        
        # Generate legend
        figure, legend_text = self.integrator.add_legend_to_figure(
            figure=figure,
            data=data,
            chart_type=chart_type,
            expertise_level=expertise_level,
            output_format=OutputFormat.STREAMLIT,
            custom_config=custom_config
        )
        
        if layout == 'tabs':
            tab1, tab2 = st.tabs(["📊 Visualization", "📝 Legend"])
            
            with tab1:
                st.plotly_chart(figure, use_container_width=True)
            
            with tab2:
                st.markdown(legend_text)
        
        elif layout == 'columns':
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.plotly_chart(figure, use_container_width=True)
            
            with col2:
                st.markdown("### Figure Legend")
                st.markdown(legend_text)
        
        elif layout == 'expandable':
            st.plotly_chart(figure, use_container_width=True)
            
            with st.expander("📖 Figure Legend", expanded=False):
                st.markdown(legend_text)
        
        else:
            # Default: vertical layout
            st.plotly_chart(figure, use_container_width=True)
            st.markdown("### Figure Legend")
            st.markdown(legend_text)
    
    def create_expertise_selector(self, 
                                key: str = "expertise_level") -> ExpertiseLevel:
        """Create Streamlit widget for expertise level selection.
        
        Args:
            key: Streamlit widget key
            
        Returns:
            Selected expertise level
        """
        
        import streamlit as st
        
        expertise_options = {
            "Basic (Minimal technical detail)": ExpertiseLevel.BASIC,
            "Intermediate (Standard detail)": ExpertiseLevel.INTERMEDIATE,
            "Expert (Full technical detail)": ExpertiseLevel.EXPERT
        }
        
        selected = st.selectbox(
            "Legend detail level:",
            options=list(expertise_options.keys()),
            index=1,  # Default to intermediate
            key=key
        )
        
        return expertise_options[selected]


class PDFIntegration:
    """Specialized integration for PDF report generation."""
    
    def __init__(self, integrator: Optional[VisualizationIntegrator] = None):
        self.integrator = integrator or VisualizationIntegrator()
    
    def add_legend_to_pdf_figure(self,
                                figure: go.Figure,
                                data: LegendData,
                                chart_type: ChartType,
                                expertise_level: ExpertiseLevel = ExpertiseLevel.EXPERT,
                                include_formulas: bool = True) -> Tuple[go.Figure, str]:
        """Add legend optimized for PDF reports.
        
        Args:
            figure: Plotly figure
            data: Source data
            chart_type: Chart type
            expertise_level: Expertise level (default Expert for reports)
            include_formulas: Whether to include mathematical formulas
            
        Returns:
            Tuple of (figure, latex_legend_text)
        """
        
        custom_config = {
            'include_formulas': include_formulas,
            'include_references': True,
            'max_length': 2000  # Longer legends acceptable in PDFs
        }
        
        figure, legend_text = self.integrator.add_legend_to_figure(
            figure=figure,
            data=data,
            chart_type=chart_type,
            expertise_level=expertise_level,
            output_format=OutputFormat.PDF,
            custom_config=custom_config
        )
        
        return figure, legend_text
    
    def create_figure_caption(self,
                            figure_number: int,
                            chart_type: ChartType,
                            data: LegendData,
                            brief: bool = True) -> str:
        """Create brief figure caption for PDF.
        
        Args:
            figure_number: Figure number in document
            chart_type: Chart type
            data: Source data
            brief: Whether to create brief or detailed caption
            
        Returns:
            Figure caption text
        """
        
        context = LegendContext(
            data=data,
            chart_type=chart_type,
            expertise_level=ExpertiseLevel.BASIC if brief else ExpertiseLevel.INTERMEDIATE,
            output_format=OutputFormat.PDF
        )
        
        # Generate minimal legend with just description
        legend_content = self.integrator.legend_manager.generate_legend(
            context, sections=['description']
        )
        
        caption = self.integrator.legend_manager.format_legend(
            legend_content, OutputFormat.PDF
        )
        
        return f"Figure {figure_number}. {caption}"


# Convenience functions for backward compatibility
def add_legend_to_existing_function(func: Callable, 
                                   chart_type: ChartType,
                                   integrator: Optional[VisualizationIntegrator] = None) -> Callable:
    """Add legend capability to existing visualization function.
    
    Args:
        func: Existing visualization function
        chart_type: Type of chart it creates
        integrator: VisualizationIntegrator instance
        
    Returns:
        Enhanced function with legend capability
    """
    
    if integrator is None:
        integrator = VisualizationIntegrator()
    
    return integrator.create_legend_decorator(chart_type, auto_attach=False)(func)


def create_quick_legend(data: LegendData,
                       chart_type: ChartType,
                       title: str = "",
                       expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
                       output_format: OutputFormat = OutputFormat.HTML) -> str:
    """Create a quick legend for any chart type.
    
    Args:
        data: Data used in visualization
        chart_type: Type of chart
        title: Chart title
        expertise_level: Target expertise level
        output_format: Output format
        
    Returns:
        Formatted legend text
    """
    
    legend_manager = LegendManager()
    context = LegendContext(
        data=data,
        chart_type=chart_type,
        expertise_level=expertise_level,
        output_format=output_format,
        config={'title': title}
    )
    
    return legend_manager.generate_and_format(context)