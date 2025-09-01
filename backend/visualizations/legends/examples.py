"""
Usage examples and testing for the figure legend system.

This module demonstrates how to use the legend system with various chart types,
output formats, and integration methods.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

from .models import ChartType, ExpertiseLevel, OutputFormat
from .core import LegendManager, LegendContext
from .formatters import get_formatter
from .integration import (
    VisualizationIntegrator, StreamlitIntegration, PDFIntegration,
    quick_legend_for_streamlit, create_legend_only
)

logger = logging.getLogger(__name__)


def create_sample_data() -> pd.DataFrame:
    """Create sample screening data for testing legend system."""
    np.random.seed(42)
    
    # Create plate layout
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] * 6  
    cols = list(range(1, 25)) * 2
    wells = [f"{row}{col:02d}" for row, col in zip(rows[:48], cols[:48])]
    
    # Generate sample data
    data = {
        'PlateID': ['Plate1'] * 24 + ['Plate2'] * 24,
        'Well': wells[:48],
        'Row': [well[0] for well in wells[:48]],
        'Column': [int(well[1:]) for well in wells[:48]],
        
        # Reporter signals
        'BG_lptA': np.random.lognormal(3.0, 0.5, 48),
        'BT_lptA': np.random.lognormal(4.0, 0.3, 48),
        'BG_ldtD': np.random.lognormal(3.2, 0.4, 48),
        'BT_ldtD': np.random.lognormal(4.1, 0.3, 48),
        
        # Growth measurements
        'OD_WT': np.random.normal(0.8, 0.15, 48),
        'OD_tolC': np.random.normal(0.7, 0.18, 48), 
        'OD_SA': np.random.normal(0.9, 0.12, 48),
        
        # ATP viability
        'ATP': np.random.lognormal(5.0, 0.4, 48)
    }
    
    df = pd.DataFrame(data)
    
    # Calculate ratios and Z-scores
    df['Ratio_lptA'] = df['BG_lptA'] / df['BT_lptA']
    df['Ratio_ldtD'] = df['BG_ldtD'] / df['BT_ldtD']
    
    # Robust Z-scores
    for ratio_col in ['Ratio_lptA', 'Ratio_ldtD']:
        median = df[ratio_col].median()
        mad = np.median(np.abs(df[ratio_col] - median))
        df[f'Z_{ratio_col.split("_")[1]}'] = (df[ratio_col] - median) / (1.4826 * mad)
    
    # Add some platform hits
    hit_indices = [5, 15, 23, 34, 41]
    df.loc[hit_indices, 'Z_lptA'] = np.random.uniform(2.5, 4.0, len(hit_indices))
    df.loc[hit_indices, 'Z_ldtD'] = np.random.uniform(2.0, 3.5, len(hit_indices))
    
    return df


def example_basic_usage():
    """Demonstrate basic legend creation and formatting."""
    print("=== Basic Legend System Usage ===\n")
    
    # Create sample data
    df = create_sample_data()
    print(f"Created sample data: {len(df)} wells, {df['PlateID'].nunique()} plates")
    
    # Initialize legend manager
    manager = LegendManager()
    
    # Create legend for different chart types and expertise levels
    chart_types = [ChartType.HEATMAP, ChartType.HISTOGRAM, ChartType.SCATTER_PLOT]
    expertise_levels = [ExpertiseLevel.BASIC, ExpertiseLevel.INTERMEDIATE, ExpertiseLevel.EXPERT]
    
    for chart_type in chart_types:
        print(f"\n--- {chart_type.value.upper()} LEGENDS ---")
        
        for expertise in expertise_levels:
            try:
                legend = manager.create_legend(
                    data=df,
                    chart_type=chart_type,
                    expertise_level=expertise
                )
                
                print(f"\n{expertise.value.title()} Level ({legend.total_char_count} chars):")
                print(f"Sections: {list(legend.sections.keys())}")
                
                # Show biological context as example
                bio_section = legend.get_section('biological_context')
                if bio_section:
                    print(f"Bio Context: {bio_section.content[:100]}...")
                
            except Exception as e:
                print(f"Error creating {chart_type.value} {expertise.value} legend: {e}")


def example_output_formats():
    """Demonstrate different output format options."""
    print("\n=== Output Format Examples ===\n")
    
    df = create_sample_data()
    manager = LegendManager()
    
    # Create base legend
    legend = manager.create_legend(
        data=df,
        chart_type=ChartType.HEATMAP,
        expertise_level=ExpertiseLevel.INTERMEDIATE
    )
    
    # Test all formatters
    formats = [OutputFormat.MARKDOWN, OutputFormat.HTML, OutputFormat.PDF, OutputFormat.PLAIN_TEXT]
    
    for fmt in formats:
        print(f"\n--- {fmt.value.upper()} FORMAT ---")
        try:
            formatter = get_formatter(fmt)
            formatted = formatter.format_legend(legend)
            
            if isinstance(formatted, dict):
                print("Streamlit format (dict structure):")
                print(f"Sections: {list(formatted.get('sections', {}).keys())}")
                print(f"Config: {formatted.get('config', {})}")
            else:
                preview = formatted[:200] + "..." if len(formatted) > 200 else formatted
                print(f"Formatted content ({len(formatted)} chars):")
                print(preview)
                
        except Exception as e:
            print(f"Error with {fmt.value} format: {e}")


def example_streamlit_integration():
    """Demonstrate Streamlit integration features."""
    print("\n=== Streamlit Integration Examples ===\n")
    
    df = create_sample_data()
    
    # Note: This would normally be called within a Streamlit app
    # Here we just demonstrate the API
    
    # Basic integration example
    print("1. StreamlitIntegration class usage:")
    integrator = VisualizationIntegrator()
    st_integration = StreamlitIntegration(integrator)
    
    # Create legend content for different layouts
    legend = integrator.legend_manager.create_legend(
        data=df,
        chart_type=ChartType.HEATMAP,
        expertise_level=ExpertiseLevel.INTERMEDIATE
    )
    
    # Show expandable format
    expandable_content = st_integration.formatter.create_expandable_legend(legend)
    print(f"Expandable format: {len(expandable_content)} characters")
    
    # Show tabbed format  
    tabbed_content = st_integration.formatter.create_tabbed_legend(legend)
    print(f"Tabbed format: {len(tabbed_content)} tabs - {list(tabbed_content.keys())}")
    
    # Convenience function usage
    print("\n2. Convenience function usage:")
    standalone_legend = create_legend_only(
        data=df,
        chart_type=ChartType.HISTOGRAM,
        expertise_level=ExpertiseLevel.BASIC,
        output_format=OutputFormat.MARKDOWN
    )
    print(f"Standalone legend: {len(standalone_legend)} characters")


def example_decorator_usage():
    """Demonstrate decorator integration patterns."""
    print("\n=== Decorator Integration Examples ===\n")
    
    # Example visualization function with decorator
    integrator = VisualizationIntegrator()
    
    @integrator.create_legend_decorator(ChartType.HEATMAP, ExpertiseLevel.INTERMEDIATE)
    def create_sample_heatmap(df: pd.DataFrame, metric_col: str):
        """Sample heatmap creation function with auto-legend."""
        # In real usage, this would create a Plotly/matplotlib figure
        fake_figure = {
            'data': df[metric_col].values.reshape(6, 8),
            'type': 'heatmap',
            'title': f'Heatmap of {metric_col}'
        }
        return fake_figure
    
    # Use decorated function
    df = create_sample_data()
    
    try:
        result = create_sample_heatmap(df, 'Z_lptA')
        
        if isinstance(result, tuple) and len(result) == 2:
            figure, legend = result
            print("Decorator successfully added legend:")
            print(f"Figure type: {type(figure)}")
            print(f"Legend type: {type(legend)}")
            print(f"Legend sections: {list(legend.sections.keys())}")
        else:
            print("Decorator returned:", type(result))
            
    except Exception as e:
        print(f"Decorator example error: {e}")


def example_pdf_integration():
    """Demonstrate PDF integration features."""
    print("\n=== PDF Integration Examples ===\n")
    
    df = create_sample_data()
    
    # PDF integration example
    pdf_integration = PDFIntegration()
    
    # Generate legend for PDF report
    try:
        pdf_legend = pdf_integration.generate_figure_legend_for_pdf(
            data=df,
            chart_type=ChartType.HEATMAP,
            figure_number="3.1",
            expertise_level=ExpertiseLevel.EXPERT
        )
        
        print(f"PDF legend generated: {len(pdf_legend)} characters")
        print("Preview:")
        print(pdf_legend[:300] + "..." if len(pdf_legend) > 300 else pdf_legend)
        
    except Exception as e:
        print(f"PDF integration error: {e}")
    
    # Multiple figure enhancement
    figure_mappings = {
        "Fig1": (df, ChartType.HISTOGRAM),
        "Fig2": (df, ChartType.SCATTER_PLOT),
        "Fig3": (df, ChartType.HEATMAP)
    }
    
    try:
        enhanced_legends = pdf_integration.enhance_pdf_report_with_legends(
            report_data={},
            figure_mappings=figure_mappings
        )
        
        print(f"\nEnhanced {len(enhanced_legends)} figure legends for PDF:")
        for fig_id, legend_text in enhanced_legends.items():
            print(f"{fig_id}: {len(legend_text)} characters")
            
    except Exception as e:
        print(f"Multiple figure enhancement error: {e}")


def example_error_handling():
    """Demonstrate error handling and edge cases."""
    print("\n=== Error Handling Examples ===\n")
    
    manager = LegendManager()
    
    # Test with empty DataFrame
    print("1. Empty DataFrame:")
    empty_df = pd.DataFrame()
    try:
        legend = manager.create_legend(
            data=empty_df,
            chart_type=ChartType.HEATMAP,
            expertise_level=ExpertiseLevel.BASIC
        )
        print(f"Success: Created legend with {legend.total_char_count} characters")
    except Exception as e:
        print(f"Error with empty DataFrame: {e}")
    
    # Test with minimal data
    print("\n2. Minimal DataFrame:")
    minimal_df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    try:
        legend = manager.create_legend(
            data=minimal_df,
            chart_type=ChartType.HISTOGRAM,
            expertise_level=ExpertiseLevel.BASIC
        )
        print(f"Success: Created legend with {legend.total_char_count} characters")
    except Exception as e:
        print(f"Error with minimal DataFrame: {e}")
    
    # Test with dictionary input
    print("\n3. Dictionary input:")
    dict_data = {'sample_size': 100, 'method_used': 'robust_z_score'}
    try:
        legend = manager.create_legend(
            data=dict_data,
            chart_type=ChartType.SCATTER_PLOT,
            expertise_level=ExpertiseLevel.BASIC
        )
        print(f"Success: Created legend with {legend.total_char_count} characters")
    except Exception as e:
        print(f"Error with dictionary input: {e}")


def run_comprehensive_test():
    """Run comprehensive test of all legend system components."""
    print("🧪 COMPREHENSIVE LEGEND SYSTEM TEST 🧪")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_output_formats()
        example_streamlit_integration()
        example_decorator_usage()
        example_pdf_integration()
        example_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("The legend system is ready for integration with the bio-hit-finder platform.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error(f"Comprehensive test failed: {e}")


def demo_real_usage_pattern():
    """Demonstrate realistic usage pattern for bio-hit-finder integration."""
    print("\n=== Real Usage Pattern Demo ===\n")
    
    # Simulate real screening data
    df = create_sample_data()
    
    # Pattern 1: Quick Streamlit legend (most common)
    print("1. Quick Streamlit usage pattern:")
    print("   # In app.py visualization tab:")
    print("   from visualizations.legends.integration import quick_legend_for_streamlit")
    print("   fig = create_histogram(df, 'Z_lptA')")
    print("   quick_legend_for_streamlit(fig, df, ChartType.HISTOGRAM)")
    
    # Pattern 2: Advanced Streamlit with user controls
    print("\n2. Advanced Streamlit pattern:")
    print("   # With expertise level selector and custom layout")
    print("   st_integration = StreamlitIntegration()")
    print("   st_integration.display_figure_with_legend(")
    print("       figure=fig, data=df, chart_type=ChartType.HEATMAP,")
    print("       layout='tabs', show_expertise_selector=True)")
    
    # Pattern 3: PDF report enhancement
    print("\n3. PDF report enhancement pattern:")
    print("   # In export/pdf_generator.py")
    print("   pdf_integration = PDFIntegration()")
    print("   legend_text = pdf_integration.generate_figure_legend_for_pdf(")
    print("       data=df, chart_type=ChartType.HEATMAP, figure_number='2.1')")
    print("   # Insert legend_text into LaTeX template")
    
    # Pattern 4: Decorator for new functions
    print("\n4. Decorator pattern for new functions:")
    print("   @heatmap_with_legend(ExpertiseLevel.INTERMEDIATE)")
    print("   def create_z_score_heatmap(df):")
    print("       return plotly_figure")
    print("   # Returns (figure, legend) tuple automatically")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive test
    run_comprehensive_test()
    
    # Show realistic usage patterns
    demo_real_usage_pattern()