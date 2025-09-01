"""
Integration layer for seamless connection with existing visualization functions.

This module provides decorators and helper functions to easily add legends to 
existing visualization functions without requiring major code changes.
"""

import logging
import functools
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
import streamlit as st
import pandas as pd

from .models import (
    ChartType, ExpertiseLevel, LegendContent, LegendConfig,
    OutputFormat, DataFrameType
)
from .core import LegendManager
from .formatters import StreamlitFormatter, PDFFormatter, HTMLFormatter, get_formatter

logger = logging.getLogger(__name__)


class VisualizationIntegrator:
    """Main integration class for adding legends to existing visualization functions."""
    
    def __init__(self, config: Optional[LegendConfig] = None):
        """Initialize integrator with optional configuration."""
        self.config = config or LegendConfig.default()
        self.legend_manager = LegendManager(self.config)
        self.streamlit_formatter = StreamlitFormatter()
        
        logger.info("VisualizationIntegrator initialized")
    
    def create_legend_decorator(
        self, 
        chart_type: ChartType,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    ) -> Callable:
        """Create a decorator that automatically adds legends to visualization functions.
        
        Usage:
            @integrator.create_legend_decorator(ChartType.HEATMAP)
            def create_heatmap(df, metric_col):
                fig = px.imshow(df.pivot(...))
                return fig
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract data from function arguments
                data = self._extract_data_from_args(args, kwargs)
                
                # Call original function
                result = func(*args, **kwargs)
                
                # Create legend
                try:
                    legend = self.legend_manager.create_legend(
                        data=data,
                        chart_type=chart_type,
                        expertise_level=expertise_level,
                        analysis_config=kwargs.get('legend_config')
                    )
                    
                    # Return both figure and legend
                    if isinstance(result, tuple):
                        # Function already returns multiple values
                        return (*result, legend)
                    else:
                        # Function returns single figure
                        return result, legend
                        
                except Exception as e:
                    logger.warning(f"Failed to create legend for {func.__name__}: {e}")
                    return result
            
            return wrapper
        return decorator
    
    def add_legend_to_figure(
        self,
        figure: Any,
        data: DataFrameType,
        chart_type: ChartType,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
        output_format: OutputFormat = OutputFormat.STREAMLIT,
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, Union[str, Dict[str, Any]]]:
        """Manually add legend to an existing figure.
        
        Args:
            figure: The visualization figure (Plotly, matplotlib, etc.)
            data: Data used to create the figure
            chart_type: Type of chart for appropriate template
            expertise_level: Level of detail for legend
            output_format: Format for legend output
            analysis_config: Optional configuration for analysis context
            
        Returns:
            Tuple of (figure, formatted_legend)
        """
        try:
            # Create legend content
            legend = self.legend_manager.create_legend(
                data=data,
                chart_type=chart_type,
                expertise_level=expertise_level,
                analysis_config=analysis_config
            )
            
            # Format for output
            formatter = get_formatter(output_format)
            formatted_legend = formatter.format_legend(legend)
            
            return figure, formatted_legend
            
        except Exception as e:
            logger.error(f"Error adding legend to figure: {e}")
            return figure, f"Error creating legend: {e}"
    
    def _extract_data_from_args(self, args: tuple, kwargs: dict) -> DataFrameType:
        """Extract DataFrame from function arguments."""
        # Common patterns for data extraction
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                return arg
        
        # Check kwargs for common data parameter names
        data_keys = ['data', 'df', 'dataframe', 'dataset']
        for key in data_keys:
            if key in kwargs and isinstance(kwargs[key], pd.DataFrame):
                return kwargs[key]
        
        # Return empty dict if no DataFrame found
        logger.warning("No DataFrame found in function arguments")
        return {}


class StreamlitIntegration:
    """Streamlit-specific integration helpers."""
    
    def __init__(self, integrator: Optional[VisualizationIntegrator] = None):
        """Initialize with optional integrator instance."""
        self.integrator = integrator or VisualizationIntegrator()
        self.formatter = StreamlitFormatter()
    
    def display_figure_with_legend(
        self,
        figure: Any,
        data: DataFrameType,
        chart_type: ChartType,
        layout: str = "expander",
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
        legend_title: str = "📖 Figure Legend",
        expanded: bool = False,
        show_expertise_selector: bool = True
    ):
        """Display figure with legend in Streamlit interface.
        
        Args:
            figure: Plotly/matplotlib figure to display
            data: Data used to create the figure
            chart_type: Type of chart for appropriate template
            layout: 'expander', 'tabs', 'columns', or 'below'
            expertise_level: Level of detail for legend
            legend_title: Title for legend section
            expanded: Whether expander starts expanded
            show_expertise_selector: Whether to show expertise level selector
        """
        try:
            # Display the figure
            st.plotly_chart(figure, use_container_width=True)
            
            # Handle expertise level selection if enabled
            current_expertise = expertise_level
            if show_expertise_selector:
                expertise_options = ["Basic", "Intermediate", "Expert"]
                selected = st.selectbox(
                    "Legend Detail Level",
                    expertise_options,
                    index=expertise_options.index(expertise_level.value.title()),
                    key=f"expertise_{id(figure)}"
                )
                current_expertise = ExpertiseLevel(selected.lower())
            
            # Create and display legend
            legend = self.integrator.legend_manager.create_legend(
                data=data,
                chart_type=chart_type,
                expertise_level=current_expertise
            )
            
            self._display_legend_with_layout(legend, layout, legend_title, expanded)
            
        except Exception as e:
            logger.error(f"Error displaying figure with legend: {e}")
            st.error(f"Error creating legend: {e}")
    
    def _display_legend_with_layout(
        self, 
        legend: LegendContent, 
        layout: str, 
        title: str, 
        expanded: bool
    ):
        """Display legend content using specified layout."""
        if layout == "expander":
            with st.expander(title, expanded=expanded):
                content = self.formatter.create_expandable_legend(legend)
                st.markdown(content)
        
        elif layout == "tabs":
            tab_content = self.formatter.create_tabbed_legend(legend)
            if tab_content:
                tabs = st.tabs(list(tab_content.keys()))
                for tab, content in zip(tabs, tab_content.values()):
                    with tab:
                        st.markdown(content)
        
        elif layout == "columns":
            cols = st.columns([2, 1])
            with cols[1]:
                st.subheader("Legend")
                content = self.formatter.create_expandable_legend(legend)
                st.markdown(content)
        
        elif layout == "below":
            st.subheader(title)
            content = self.formatter.create_expandable_legend(legend)
            st.markdown(content)
    
    def create_legend_sidebar(
        self,
        data: DataFrameType,
        chart_type: ChartType,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    ):
        """Create legend content in Streamlit sidebar."""
        try:
            with st.sidebar:
                st.subheader("📖 Legend")
                
                # Expertise selector
                expertise_options = ["Basic", "Intermediate", "Expert"]
                selected = st.selectbox(
                    "Detail Level",
                    expertise_options,
                    index=expertise_options.index(expertise_level.value.title()),
                    key="sidebar_expertise"
                )
                current_expertise = ExpertiseLevel(selected.lower())
                
                # Create and display legend
                legend = self.integrator.legend_manager.create_legend(
                    data=data,
                    chart_type=chart_type,
                    expertise_level=current_expertise
                )
                
                content = self.formatter.create_expandable_legend(legend)
                st.markdown(content)
                
        except Exception as e:
            logger.error(f"Error creating sidebar legend: {e}")
            st.sidebar.error(f"Error creating legend: {e}")
    
    def add_legend_to_plotly_figure(
        self,
        figure: Any,
        legend_content: str,
        position: str = "bottom"
    ) -> Any:
        """Add legend text directly to Plotly figure as annotation.
        
        Args:
            figure: Plotly figure object
            legend_content: Formatted legend text
            position: 'bottom', 'right', or 'overlay'
            
        Returns:
            Modified Plotly figure with legend annotation
        """
        try:
            # Truncate content for figure annotation (max ~200 chars)
            short_content = legend_content[:200] + "..." if len(legend_content) > 200 else legend_content
            
            annotation_config = {
                'text': short_content,
                'showarrow': False,
                'font': dict(size=10, color='gray'),
                'bgcolor': 'rgba(255,255,255,0.8)',
                'bordercolor': 'gray',
                'borderwidth': 1,
                'borderpad': 4
            }
            
            if position == "bottom":
                annotation_config.update({
                    'x': 0.5,
                    'y': -0.15,
                    'xref': 'paper',
                    'yref': 'paper',
                    'xanchor': 'center',
                    'yanchor': 'top'
                })
            elif position == "right":
                annotation_config.update({
                    'x': 1.02,
                    'y': 0.5,
                    'xref': 'paper', 
                    'yref': 'paper',
                    'xanchor': 'left',
                    'yanchor': 'middle'
                })
            elif position == "overlay":
                annotation_config.update({
                    'x': 0.02,
                    'y': 0.98,
                    'xref': 'paper',
                    'yref': 'paper', 
                    'xanchor': 'left',
                    'yanchor': 'top'
                })
            
            figure.add_annotation(**annotation_config)
            return figure
            
        except Exception as e:
            logger.error(f"Error adding legend to Plotly figure: {e}")
            return figure


class PDFIntegration:
    """PDF report integration helpers."""
    
    def __init__(self, integrator: Optional[VisualizationIntegrator] = None):
        """Initialize with optional integrator instance."""
        self.integrator = integrator or VisualizationIntegrator()
        self.formatter = PDFFormatter()
    
    def generate_figure_legend_for_pdf(
        self,
        data: DataFrameType,
        chart_type: ChartType,
        figure_number: str = "1",
        expertise_level: ExpertiseLevel = ExpertiseLevel.EXPERT
    ) -> str:
        """Generate legend text for PDF report inclusion.
        
        Args:
            data: Data used to create the figure
            chart_type: Type of chart for appropriate template
            figure_number: Figure number for PDF reference
            expertise_level: Level of detail for legend
            
        Returns:
            LaTeX-formatted legend text for PDF inclusion
        """
        try:
            # Create legend content
            legend = self.integrator.legend_manager.create_legend(
                data=data,
                chart_type=chart_type,
                expertise_level=expertise_level
            )
            
            # Format for PDF
            formatted_legend = self.formatter.format_legend(
                legend,
                figure_number=figure_number,
                include_header=True
            )
            
            return formatted_legend
            
        except Exception as e:
            logger.error(f"Error generating PDF legend: {e}")
            return f"Error generating legend: {e}"
    
    def enhance_pdf_report_with_legends(
        self,
        report_data: Dict[str, Any],
        figure_mappings: Dict[str, Tuple[DataFrameType, ChartType]]
    ) -> Dict[str, str]:
        """Enhance PDF report data with comprehensive figure legends.
        
        Args:
            report_data: Existing PDF report data
            figure_mappings: Maps figure IDs to (data, chart_type) tuples
            
        Returns:
            Dictionary of figure IDs to legend content
        """
        enhanced_legends = {}
        
        for figure_id, (data, chart_type) in figure_mappings.items():
            try:
                legend_text = self.generate_figure_legend_for_pdf(
                    data=data,
                    chart_type=chart_type,
                    figure_number=figure_id,
                    expertise_level=ExpertiseLevel.EXPERT
                )
                enhanced_legends[figure_id] = legend_text
                
            except Exception as e:
                logger.error(f"Error creating legend for figure {figure_id}: {e}")
                enhanced_legends[figure_id] = f"Legend unavailable: {e}"
        
        return enhanced_legends


# Convenience functions for common use cases
def quick_legend_for_streamlit(
    figure: Any,
    data: DataFrameType, 
    chart_type: ChartType,
    title: str = "📖 Figure Legend"
) -> None:
    """Quick way to add expandable legend below a Streamlit figure."""
    integrator = VisualizationIntegrator()
    st_integration = StreamlitIntegration(integrator)
    
    # Display figure
    st.plotly_chart(figure, use_container_width=True)
    
    # Add legend
    try:
        legend = integrator.legend_manager.create_legend(
            data=data,
            chart_type=chart_type,
            expertise_level=ExpertiseLevel.INTERMEDIATE
        )
        
        with st.expander(title, expanded=False):
            content = st_integration.formatter.create_expandable_legend(legend)
            st.markdown(content)
            
    except Exception as e:
        st.error(f"Error creating legend: {e}")


def create_legend_only(
    data: DataFrameType,
    chart_type: ChartType,
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
    output_format: OutputFormat = OutputFormat.MARKDOWN
) -> str:
    """Create standalone legend content without visualization.
    
    Useful for documentation, reports, or separate legend displays.
    """
    try:
        integrator = VisualizationIntegrator()
        legend = integrator.legend_manager.create_legend(
            data=data,
            chart_type=chart_type,
            expertise_level=expertise_level
        )
        
        formatter = get_formatter(output_format)
        return formatter.format_legend(legend)
        
    except Exception as e:
        logger.error(f"Error creating standalone legend: {e}")
        return f"Error creating legend: {e}"


# Decorators for common chart types
def heatmap_with_legend(
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
):
    """Decorator for heatmap functions."""
    integrator = VisualizationIntegrator()
    return integrator.create_legend_decorator(ChartType.HEATMAP, expertise_level)


def histogram_with_legend(
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
):
    """Decorator for histogram functions.""" 
    integrator = VisualizationIntegrator()
    return integrator.create_legend_decorator(ChartType.HISTOGRAM, expertise_level)


def scatter_with_legend(
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
):
    """Decorator for scatter plot functions."""
    integrator = VisualizationIntegrator()
    return integrator.create_legend_decorator(ChartType.SCATTER_PLOT, expertise_level)