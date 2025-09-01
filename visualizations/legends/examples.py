"""
Usage examples for the figure legend system.

This module provides comprehensive examples showing how to integrate
the legend system with existing bio-hit-finder visualizations.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any
import logging

from .core import LegendManager, LegendContext
from .models import ChartType, ExpertiseLevel, OutputFormat
from .integration import VisualizationIntegrator, StreamlitIntegration
from .config import get_global_configuration

logger = logging.getLogger(__name__)


def create_sample_data() -> pd.DataFrame:
    """Create sample plate data for examples."""
    
    np.random.seed(42)  # For reproducible examples
    
    n_wells = 384
    wells = [f"{chr(65 + i//24)}{(i%24)+1:02d}" for i in range(n_wells)]
    
    data = pd.DataFrame({
        'Well': wells,
        'PlateID': 'DEMO_001',
        'Ratio_lptA': np.random.lognormal(0, 0.3, n_wells),
        'Ratio_ldtD': np.random.lognormal(0, 0.25, n_wells),
        'BG_lptA': np.random.normal(1000, 200, n_wells),
        'BT_lptA': np.random.normal(800, 150, n_wells),
        'BG_ldtD': np.random.normal(900, 180, n_wells),
        'BT_ldtD': np.random.normal(750, 120, n_wells),
        'ATP': np.random.normal(500, 100, n_wells),
        'OD_WT': np.random.normal(0.8, 0.15, n_wells),
        'OD_tolC': np.random.normal(0.6, 0.12, n_wells),
        'OD_SA': np.random.normal(0.9, 0.18, n_wells)
    })
    
    # Calculate derived metrics
    data['Z_lptA'] = (data['Ratio_lptA'] - data['Ratio_lptA'].median()) / (1.4826 * np.median(np.abs(data['Ratio_lptA'] - data['Ratio_lptA'].median())))
    data['Z_ldtD'] = (data['Ratio_ldtD'] - data['Ratio_ldtD'].median()) / (1.4826 * np.median(np.abs(data['Ratio_ldtD'] - data['Ratio_ldtD'].median())))
    
    # Add quality control flags
    viability_threshold = 0.3 * data['ATP'].median()
    data['Viability_Flag'] = data['ATP'] < viability_threshold
    data['Viable'] = ~data['Viability_Flag']
    
    # Add some edge effects
    edge_wells = [w for w in wells if w.startswith(('A', 'P')) or w.endswith(('01', '24'))]
    data['Edge_Flag'] = data['Well'].isin(edge_wells[:20])  # Flag some edge wells
    
    return data


def example_basic_legend_generation():
    """Example 1: Basic legend generation for different chart types."""
    
    print("=== Example 1: Basic Legend Generation ===")
    
    # Create sample data
    data = create_sample_data()
    
    # Initialize legend manager
    legend_manager = LegendManager()
    
    # Example 1.1: Heatmap legend
    print("\n1.1 Heatmap Legend (Intermediate Level):")
    context = LegendContext(
        data=data,
        chart_type=ChartType.HEATMAP,
        expertise_level=ExpertiseLevel.INTERMEDIATE,
        output_format=OutputFormat.MARKDOWN,
        config={'metric_col': 'Z_lptA', 'title': 'Z-scores for lptA Reporter'}
    )
    
    legend_text = legend_manager.generate_and_format(context)
    print(legend_text)
    
    # Example 1.2: Histogram legend for basic users
    print("\n1.2 Histogram Legend (Basic Level):")
    context = LegendContext(
        data=data,
        chart_type=ChartType.HISTOGRAM,
        expertise_level=ExpertiseLevel.BASIC,
        output_format=OutputFormat.PLAIN_TEXT,
        config={'column': 'Ratio_lptA', 'title': 'Distribution of lptA Ratios'}
    )
    
    legend_text = legend_manager.generate_and_format(context)
    print(legend_text)
    
    # Example 1.3: Scatter plot legend for experts
    print("\n1.3 Scatter Plot Legend (Expert Level):")
    context = LegendContext(
        data=data,
        chart_type=ChartType.SCATTER_PLOT,
        expertise_level=ExpertiseLevel.EXPERT,
        output_format=OutputFormat.HTML,
        config={
            'x_variable': 'Z_lptA',
            'y_variable': 'Z_ldtD', 
            'correlation': 0.45,
            'title': 'Correlation Analysis: lptA vs ldtD Responses'
        }
    )
    
    legend_content = legend_manager.generate_legend(context)
    legend_text = legend_manager.format_legend(legend_content, OutputFormat.HTML)
    print(legend_text)


def example_integration_with_existing_functions():
    """Example 2: Integration with existing visualization functions."""
    
    print("\n=== Example 2: Integration with Existing Functions ===")
    
    # Create sample data
    data = create_sample_data()
    
    # Initialize integrator
    integrator = VisualizationIntegrator()
    
    # Example 2.1: Using decorator approach
    print("\n2.1 Decorator Integration:")
    
    @integrator.create_legend_decorator(ChartType.HEATMAP, expertise_level=ExpertiseLevel.INTERMEDIATE)
    def create_demo_heatmap(df: pd.DataFrame, metric_col: str, title: str) -> go.Figure:
        """Demo heatmap function with legend integration."""
        
        # Simplified heatmap creation
        fig = go.Figure(data=go.Heatmap(
            z=df[metric_col].values.reshape(16, 24),  # 384-well layout
            colorscale='RdBu_r',
            zmid=0
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Column',
            yaxis_title='Row'
        )
        
        return fig
    
    # Create figure with automatic legend generation
    fig = create_demo_heatmap(data, 'Z_lptA', 'Z-scores for lptA Reporter')
    
    # Extract legend information
    legend_info = integrator.extract_legend_from_figure(fig)
    if legend_info:
        print("Legend successfully attached to figure")
        print("Legend preview:", legend_info['text'][:200] + "...")
    
    # Example 2.2: Manual legend addition
    print("\n2.2 Manual Legend Addition:")
    
    # Create a simple figure
    simple_fig = go.Figure()
    simple_fig.add_trace(go.Histogram(x=data['Ratio_lptA'], name='lptA Ratios'))
    simple_fig.update_layout(title='Distribution of lptA Reporter Ratios')
    
    # Add legend manually
    enhanced_fig, legend_text = integrator.add_legend_to_figure(
        figure=simple_fig,
        data=data,
        chart_type=ChartType.HISTOGRAM,
        expertise_level=ExpertiseLevel.INTERMEDIATE,
        output_format=OutputFormat.STREAMLIT
    )
    
    print("Manual legend added:")
    print(legend_text[:300] + "...")


def example_streamlit_integration():
    """Example 3: Streamlit-specific integration."""
    
    print("\n=== Example 3: Streamlit Integration ===")
    
    # Note: This example shows the code structure for Streamlit
    # In actual use, this would run within a Streamlit app
    
    data = create_sample_data()
    streamlit_integration = StreamlitIntegration()
    
    print("Streamlit integration code example:")
    
    code_example = '''
    import streamlit as st
    from visualizations.legends.integration import StreamlitIntegration
    
    # Initialize integration
    st_integration = StreamlitIntegration()
    
    # Create expertise level selector
    expertise_level = st_integration.create_expertise_selector()
    
    # Create your visualization
    fig = create_your_visualization(data)
    
    # Display with integrated legend
    st_integration.display_figure_with_legend(
        figure=fig,
        data=data,
        chart_type=ChartType.HEATMAP,
        expertise_level=expertise_level,
        layout='tabs'  # or 'columns', 'expandable'
    )
    '''
    
    print(code_example)


def example_pdf_integration():
    """Example 4: PDF report integration."""
    
    print("\n=== Example 4: PDF Integration ===")
    
    from .integration import PDFIntegration
    
    data = create_sample_data()
    pdf_integration = PDFIntegration()
    
    # Create a sample figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['Z_lptA'], 
        y=data['Z_ldtD'],
        mode='markers',
        name='Wells'
    ))
    fig.update_layout(
        title='Correlation: lptA vs ldtD Z-scores',
        xaxis_title='Z_lptA',
        yaxis_title='Z_ldtD'
    )
    
    # Add PDF-optimized legend
    enhanced_fig, latex_legend = pdf_integration.add_legend_to_pdf_figure(
        figure=fig,
        data=data,
        chart_type=ChartType.SCATTER_PLOT,
        expertise_level=ExpertiseLevel.EXPERT,
        include_formulas=True
    )
    
    print("PDF-optimized legend (LaTeX format):")
    print(latex_legend)
    
    # Create brief figure caption
    caption = pdf_integration.create_figure_caption(
        figure_number=1,
        chart_type=ChartType.SCATTER_PLOT,
        data=data,
        brief=True
    )
    
    print("\nBrief figure caption:")
    print(caption)


def example_custom_configuration():
    """Example 5: Custom configuration and templates."""
    
    print("\n=== Example 5: Custom Configuration ===")
    
    from .config import LegendConfiguration, create_sample_configuration_file
    
    # Create custom configuration
    config = LegendConfiguration()
    
    # Show default biological context
    biological_defaults = config.get_biological_defaults()
    print("Default biological context:")
    for key, value in biological_defaults.items():
        if isinstance(value, str):
            print(f"  {key}: {value}")
    
    # Get expertise-specific configuration
    expert_config = config.get_expertise_config(ExpertiseLevel.EXPERT)
    print(f"\nExpert configuration:")
    print(f"  Include formulas: {expert_config.include_formulas}")
    print(f"  Max length: {expert_config.max_length}")
    print(f"  Preferred sections: {expert_config.preferred_sections}")
    
    # Export sample configuration
    print("\nExporting sample configuration file...")
    create_sample_configuration_file("legend_config_sample.yaml")
    print("Sample configuration created as 'legend_config_sample.yaml'")


def example_expertise_level_comparison():
    """Example 6: Compare legends across expertise levels."""
    
    print("\n=== Example 6: Expertise Level Comparison ===")
    
    data = create_sample_data()
    legend_manager = LegendManager()
    
    base_context_config = {
        'data': data,
        'chart_type': ChartType.HEATMAP,
        'output_format': OutputFormat.MARKDOWN,
        'config': {'metric_col': 'Z_lptA', 'title': 'Z-scores Heatmap'}
    }
    
    for expertise_level in [ExpertiseLevel.BASIC, ExpertiseLevel.INTERMEDIATE, ExpertiseLevel.EXPERT]:
        print(f"\n--- {expertise_level.value.upper()} LEVEL ---")
        
        context = LegendContext(
            expertise_level=expertise_level,
            **base_context_config
        )
        
        legend_text = legend_manager.generate_and_format(context)
        # Show first 300 characters as preview
        print(legend_text[:300] + "..." if len(legend_text) > 300 else legend_text)
        print(f"Total length: {len(legend_text)} characters")


def example_validation_and_quality_control():
    """Example 7: Legend validation and quality control."""
    
    print("\n=== Example 7: Validation and Quality Control ===")
    
    data = create_sample_data()
    legend_manager = LegendManager()
    
    # Generate legend content
    context = LegendContext(
        data=data,
        chart_type=ChartType.HISTOGRAM,
        expertise_level=ExpertiseLevel.INTERMEDIATE,
        output_format=OutputFormat.HTML,
        config={'column': 'Z_lptA'}
    )
    
    legend_content = legend_manager.generate_legend(context)
    
    # Validate completeness
    validation_results = legend_manager.validate_legend_completeness(legend_content)
    
    print("Legend validation results:")
    for criterion, passed in validation_results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {criterion}")
    
    # Analyze data characteristics
    data_characteristics = legend_manager.analyze_data_characteristics(data)
    
    print("\nData characteristics detected:")
    print(f"  Shape: {data_characteristics['shape']}")
    print(f"  Has multiple plates: {data_characteristics['has_multiple_plates']}")
    print(f"  Metrics present: {list(data_characteristics['metrics_present'].keys())}")
    print(f"  Quality flags: {data_characteristics['quality_flags']}")


def run_all_examples():
    """Run all examples in sequence."""
    
    print("BIO-HIT-FINDER FIGURE LEGEND SYSTEM EXAMPLES")
    print("=" * 50)
    
    try:
        example_basic_legend_generation()
        example_integration_with_existing_functions()
        example_streamlit_integration()
        example_pdf_integration()
        example_custom_configuration()
        example_expertise_level_comparison()
        example_validation_and_quality_control()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nExample failed with error: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    # Run examples when script is executed directly
    run_all_examples()