#!/usr/bin/env python3
"""
Demo script showcasing the bio-hit-finder visualization modules.

This script demonstrates how to use the various visualization components
with sample data that mimics the structure of processed plate data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Set up imports for visualization modules
try:
    from visualizations import (
        create_histogram_with_overlay,
        create_scatter_plot,
        create_viability_bar_chart,
        create_zscore_comparison_chart,
        create_plate_heatmap,
        create_comparison_heatmaps,
        PlotExporter,
        create_summary_figure
    )
    print("✓ All visualization modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required dependencies are installed:")
    print("pip install plotly pandas numpy pyyaml")
    exit(1)


def generate_sample_data(n_plates: int = 2, wells_per_plate: int = 96) -> pd.DataFrame:
    """Generate sample plate data for demonstration."""
    np.random.seed(42)  # For reproducible results
    
    data_list = []
    
    for plate_id in range(1, n_plates + 1):
        # Generate well positions for 96-well format
        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        cols = list(range(1, 13))
        
        plate_data = []
        for row in rows:
            for col in cols:
                well = f"{row}{col:02d}"
                
                # Generate realistic biological data
                # Background signal with some noise
                bg_lpta = np.random.lognormal(mean=3.0, sigma=0.3)
                bt_lpta = np.random.lognormal(mean=4.5, sigma=0.2)
                bg_ldtd = np.random.lognormal(mean=2.8, sigma=0.4)
                bt_ldtd = np.random.lognormal(mean=4.3, sigma=0.25)
                
                # Calculate ratios
                ratio_lpta = bg_lpta / bt_lpta
                ratio_ldtd = bg_ldtd / bt_ldtd
                
                # Add some edge effects (higher variability at edges)
                is_edge = row in ['A', 'H'] or col in [1, 12]
                if is_edge:
                    ratio_lpta *= np.random.normal(1.0, 0.15)
                    ratio_ldtd *= np.random.normal(1.0, 0.15)
                
                # Add some hits (low ratios)
                if np.random.random() < 0.05:  # 5% hit rate
                    ratio_lpta *= np.random.uniform(0.3, 0.7)
                    ratio_ldtd *= np.random.uniform(0.4, 0.8)
                
                # Calculate Z-scores (simplified)
                z_lpta = (ratio_lpta - 1.0) / 0.2
                z_ldtd = (ratio_ldtd - 1.0) / 0.18
                
                # Calculate B-scores (with some row/column bias correction)
                b_lpta = z_lpta + np.random.normal(0, 0.1)
                b_ldtd = z_ldtd + np.random.normal(0, 0.1)
                
                # Viability based on ATP levels
                atp_level = bt_lpta * np.random.uniform(0.8, 1.2)
                viable = atp_level > (np.median([bt_lpta]) * 0.3)
                
                plate_data.append({
                    'PlateID': f'Plate_{plate_id}',
                    'Well': well,
                    'Row': row,
                    'Col': col,
                    'BG_lptA': bg_lpta,
                    'BT_lptA': bt_lpta,
                    'BG_ldtD': bg_ldtd,
                    'BT_ldtD': bt_ldtd,
                    'Ratio_lptA': ratio_lpta,
                    'Ratio_ldtD': ratio_ldtd,
                    'Z_lptA': z_lpta,
                    'Z_ldtD': z_ldtd,
                    'B_lptA': b_lpta,
                    'B_ldtD': b_ldtd,
                    'ATP_Level': atp_level,
                    'Viable': viable
                })
        
        data_list.extend(plate_data)
    
    return pd.DataFrame(data_list)


def demo_charts(df: pd.DataFrame) -> None:
    """Demonstrate chart functionality."""
    print("\n=== Chart Demonstrations ===")
    
    try:
        # 1. Histogram with overlay
        print("Creating histogram with box plot overlay...")
        fig = create_histogram_with_overlay(
            df, 'Ratio_lptA',
            title='Distribution of Ratio_lptA',
            show_box=True
        )
        print(f"✓ Histogram created with {len(df['Ratio_lptA'].dropna())} data points")
        
        # 2. Scatter plot
        print("Creating scatter plot...")
        fig = create_scatter_plot(
            df, 'Ratio_lptA', 'Ratio_ldtD',
            color_col='PlateID',
            title='Ratio_lptA vs Ratio_ldtD by Plate',
            hover_data=['Well']
        )
        print(f"✓ Scatter plot created with {len(df)} points")
        
        # 3. Viability bar chart
        print("Creating viability bar chart...")
        fig = create_viability_bar_chart(df, title='Viability Counts by Plate')
        print(f"✓ Viability bar chart created for {df['PlateID'].nunique()} plates")
        
        # 4. Z-score comparison
        print("Creating Z-score comparison...")
        fig = create_zscore_comparison_chart(
            df, 'Z_lptA', 'B_lptA',
            title='Raw Z-score vs B-score Comparison (lptA)'
        )
        print("✓ Z-score comparison chart created")
        
    except Exception as e:
        print(f"❌ Error in chart demo: {e}")


def demo_heatmaps(df: pd.DataFrame) -> None:
    """Demonstrate heatmap functionality."""
    print("\n=== Heatmap Demonstrations ===")
    
    try:
        # 1. Single plate heatmap
        print("Creating plate heatmap...")
        plate_id = df['PlateID'].iloc[0]
        fig = create_plate_heatmap(
            df, 'Z_lptA',
            title=f'Z_lptA Heatmap - {plate_id}',
            plate_id=plate_id
        )
        print(f"✓ Plate heatmap created for {plate_id}")
        
        # 2. Comparison heatmaps
        print("Creating comparison heatmaps...")
        fig = create_comparison_heatmaps(
            df, 'Z_lptA', 'B_lptA',
            plate_id=plate_id,
            title='Raw Z vs B-score Comparison'
        )
        print("✓ Comparison heatmaps created")
        
    except Exception as e:
        print(f"❌ Error in heatmap demo: {e}")


def demo_export(df: pd.DataFrame) -> None:
    """Demonstrate export functionality."""
    print("\n=== Export Demonstrations ===")
    
    try:
        # Create output directory
        output_dir = Path("demo_exports")
        output_dir.mkdir(exist_ok=True)
        
        # Initialize exporter
        exporter = PlotExporter(output_dir, dpi=150)  # Lower DPI for demo
        print(f"✓ Export directory created: {output_dir.absolute()}")
        
        # Create and export a summary figure
        print("Creating summary figure...")
        summary_fig = create_summary_figure(df, title='Demo Plate Analysis Summary')
        
        # Export in multiple formats
        exported_files = exporter.export_figure(
            summary_fig,
            filename='demo_summary',
            formats=['png', 'html']  # Skip SVG/PDF for demo
        )
        
        print(f"✓ Summary figure exported to {len(exported_files)} formats:")
        for file_path in exported_files:
            print(f"  - {file_path}")
        
        # Demo publication charts
        print("Creating publication-ready charts...")
        pub_charts = exporter.create_publication_charts(df)
        print(f"✓ Created {len(pub_charts)} publication chart sets")
        
    except Exception as e:
        print(f"❌ Error in export demo: {e}")


def main():
    """Run the visualization demonstrations."""
    print("Bio-Hit-Finder Visualization Demo")
    print("=" * 40)
    
    # Generate sample data
    print("Generating sample plate data...")
    df = generate_sample_data(n_plates=2, wells_per_plate=96)
    print(f"✓ Generated data: {len(df)} wells across {df['PlateID'].nunique()} plates")
    
    # Show data summary
    print(f"\nData Summary:")
    print(f"  - Plate IDs: {', '.join(df['PlateID'].unique())}")
    print(f"  - Wells per plate: {len(df) // df['PlateID'].nunique()}")
    print(f"  - Viable wells: {df['Viable'].sum()} ({df['Viable'].mean()*100:.1f}%)")
    print(f"  - Mean Ratio_lptA: {df['Ratio_lptA'].mean():.3f} ± {df['Ratio_lptA'].std():.3f}")
    print(f"  - Mean Ratio_ldtD: {df['Ratio_ldtD'].mean():.3f} ± {df['Ratio_ldtD'].std():.3f}")
    
    # Run demonstrations
    demo_charts(df)
    demo_heatmaps(df)
    demo_export(df)
    
    print("\n" + "=" * 40)
    print("Demo completed successfully!")
    print("\nTo integrate these visualizations into your Streamlit app:")
    print("1. Import the required functions from the visualizations module")
    print("2. Create figures using your processed data")
    print("3. Display with st.plotly_chart(fig)")
    print("4. Use PlotExporter for downloadable exports")
    
    print("\nExample integration:")
    print("""
import streamlit as st
from visualizations import create_histogram_with_overlay, create_plate_heatmap

# In your Streamlit app
fig = create_histogram_with_overlay(processed_data, 'Z_lptA', 'Z-score Distribution')
st.plotly_chart(fig, width='stretch')

heatmap_fig = create_plate_heatmap(processed_data, 'Z_lptA', title='Plate Heatmap')
st.plotly_chart(heatmap_fig, width='stretch')
    """)


if __name__ == "__main__":
    main()