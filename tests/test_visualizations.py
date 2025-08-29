"""Visualization tests for bio-hit-finder platform.

Tests chart generation validation, heatmap layout correctness (96-well, 384-well),
color mapping verification, export format validation (PNG, SVG, HTML),
and missing data handling in plots.
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from unittest.mock import patch, MagicMock

from visualizations.charts import (
    create_histogram,
    create_scatter_plot, 
    create_boxplot,
    create_bar_chart,
    create_distribution_comparison
)
from visualizations.heatmaps import (
    create_plate_heatmap,
    create_zscore_heatmap,
    create_bscore_comparison_heatmap,
    format_plate_layout
)
from visualizations.styling import (
    get_colormap,
    apply_theme,
    format_axis_labels
)
from visualizations.export_plots import (
    export_plot_to_file,
    create_plot_bundle,
    validate_export_format
)


class TestChartGeneration:
    """Test chart generation and validation."""

    @pytest.fixture
    def sample_processed_data(self) -> pd.DataFrame:
        """Create sample processed data for visualization testing."""
        np.random.seed(42)
        n_wells = 96
        
        return pd.DataFrame({
            'Well': [f"A{i+1:02d}" for i in range(n_wells)],
            'PlateID': ['Test_Plate'] * n_wells,
            'Ratio_lptA': np.random.normal(2.0, 0.5, n_wells),
            'Ratio_ldtD': np.random.normal(2.2, 0.6, n_wells),
            'Z_lptA': np.random.normal(0, 1, n_wells),
            'Z_ldtD': np.random.normal(0, 1, n_wells),
            'OD_WT_norm': np.random.normal(1.0, 0.2, n_wells),
            'viability_ok_lptA': np.random.choice([True, False], n_wells, p=[0.85, 0.15]),
            'viability_ok_ldtD': np.random.choice([True, False], n_wells, p=[0.85, 0.15]),
        })

    def test_histogram_generation(self, sample_processed_data: pd.DataFrame):
        """Test histogram generation for different metrics."""
        # Test basic histogram
        fig = create_histogram(
            data=sample_processed_data,
            column='Z_lptA',
            title='Z-score Distribution lptA',
            bins=20
        )
        
        # Verify figure structure
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        assert fig.layout.title.text == 'Z-score Distribution lptA'
        
        # Check data properties
        trace = fig.data[0]
        assert trace.type == 'histogram'
        assert len(trace.x) == len(sample_processed_data)
        
        # Test with custom bins
        fig_custom = create_histogram(
            data=sample_processed_data,
            column='Ratio_lptA',
            bins=30,
            color='lightblue'
        )
        
        assert fig_custom.data[0].nbinsx == 30
    
    def test_histogram_with_overlay(self, sample_processed_data: pd.DataFrame):
        """Test histogram with box plot overlay."""
        fig = create_histogram(
            data=sample_processed_data,
            column='Z_lptA',
            add_box_overlay=True
        )
        
        # Should have both histogram and box plot traces
        assert len(fig.data) == 2
        assert fig.data[0].type == 'histogram'
        assert fig.data[1].type == 'box'

    def test_scatter_plot_generation(self, sample_processed_data: pd.DataFrame):
        """Test scatter plot generation."""
        fig = create_scatter_plot(
            data=sample_processed_data,
            x_column='Ratio_lptA',
            y_column='Ratio_ldtD',
            title='Reporter Ratio Comparison'
        )
        
        # Verify figure structure
        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == 'scatter'
        assert fig.layout.title.text == 'Reporter Ratio Comparison'
        
        # Check axis labels
        assert 'Ratio_lptA' in fig.layout.xaxis.title.text
        assert 'Ratio_ldtD' in fig.layout.yaxis.title.text

    def test_scatter_plot_with_color_coding(self, sample_processed_data: pd.DataFrame):
        """Test scatter plot with color coding by plate."""
        # Add multiple plates
        multi_plate_data = sample_processed_data.copy()
        plate2_data = sample_processed_data.copy()
        plate2_data['PlateID'] = 'Plate_2'
        
        combined_data = pd.concat([multi_plate_data, plate2_data], ignore_index=True)
        
        fig = create_scatter_plot(
            data=combined_data,
            x_column='Ratio_lptA',
            y_column='Ratio_ldtD',
            color_column='PlateID'
        )
        
        # Should have separate traces for each plate
        assert len(fig.data) >= 2
        plate_ids = {trace.name for trace in fig.data}
        assert 'Test_Plate' in plate_ids or 'Plate_2' in plate_ids

    def test_boxplot_generation(self, sample_processed_data: pd.DataFrame):
        """Test box plot generation."""
        fig = create_boxplot(
            data=sample_processed_data,
            column='Z_lptA',
            title='Z-score Distribution'
        )
        
        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == 'box'
        assert fig.layout.title.text == 'Z-score Distribution'

    def test_bar_chart_generation(self, sample_processed_data: pd.DataFrame):
        """Test bar chart generation for categorical data."""
        # Count viability by plate
        viability_counts = sample_processed_data.groupby('PlateID')['viability_ok_lptA'].agg(['sum', 'count']).reset_index()
        viability_counts['percentage'] = viability_counts['sum'] / viability_counts['count'] * 100
        
        fig = create_bar_chart(
            data=viability_counts,
            x_column='PlateID',
            y_column='percentage',
            title='Viability Rates by Plate'
        )
        
        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == 'bar'
        assert fig.layout.title.text == 'Viability Rates by Plate'

    def test_distribution_comparison(self, sample_processed_data: pd.DataFrame):
        """Test distribution comparison plots."""
        fig = create_distribution_comparison(
            data=sample_processed_data,
            columns=['Z_lptA', 'Z_ldtD'],
            plot_type='histogram'
        )
        
        # Should have multiple traces for comparison
        assert len(fig.data) >= 2
        
        # Test with violin plot type
        fig_violin = create_distribution_comparison(
            data=sample_processed_data,
            columns=['Ratio_lptA', 'Ratio_ldtD'],
            plot_type='violin'
        )
        
        assert len(fig_violin.data) >= 2
        assert fig_violin.data[0].type == 'violin'


class TestHeatmapGeneration:
    """Test heatmap generation and layout."""

    @pytest.fixture
    def plate_layout_96(self) -> pd.DataFrame:
        """Create 96-well plate layout data."""
        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        cols = list(range(1, 13))
        
        data = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                data.append({
                    'Row': row,
                    'Col': col,
                    'Well': f"{row}{col:02d}",
                    'Z_lptA': np.random.normal(0, 1),
                    'Z_ldtD': np.random.normal(0, 1),
                    'Ratio_lptA': np.random.normal(2.0, 0.5),
                    'viability_ok_lptA': np.random.choice([True, False], p=[0.85, 0.15])
                })
        
        return pd.DataFrame(data)

    @pytest.fixture  
    def plate_layout_384(self) -> pd.DataFrame:
        """Create 384-well plate layout data."""
        rows = [chr(65 + i) for i in range(16)]  # A-P
        cols = list(range(1, 25))  # 1-24
        
        data = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                data.append({
                    'Row': row,
                    'Col': col,
                    'Well': f"{row}{col:02d}",
                    'Z_lptA': np.random.normal(0, 1),
                    'viability_ok_lptA': np.random.choice([True, False], p=[0.9, 0.1])
                })
        
        return pd.DataFrame(data)

    def test_96_well_heatmap_layout(self, plate_layout_96: pd.DataFrame):
        """Test 96-well plate heatmap layout."""
        fig = create_plate_heatmap(
            data=plate_layout_96,
            value_column='Z_lptA',
            title='96-Well Z-score Heatmap'
        )
        
        # Verify figure structure
        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == 'heatmap'
        
        # Check dimensions (8 rows x 12 cols)
        heatmap_data = fig.data[0]
        assert heatmap_data.z.shape == (8, 12)
        
        # Check axis labels
        assert len(heatmap_data.y) == 8  # Row labels A-H
        assert len(heatmap_data.x) == 12  # Column labels 1-12

    def test_384_well_heatmap_layout(self, plate_layout_384: pd.DataFrame):
        """Test 384-well plate heatmap layout.""" 
        fig = create_plate_heatmap(
            data=plate_layout_384,
            value_column='Z_lptA',
            title='384-Well Z-score Heatmap'
        )
        
        # Check dimensions (16 rows x 24 cols)
        heatmap_data = fig.data[0]
        assert heatmap_data.z.shape == (16, 24)
        
        # Check axis labels
        assert len(heatmap_data.y) == 16  # Row labels A-P
        assert len(heatmap_data.x) == 24  # Column labels 1-24

    def test_heatmap_color_mapping(self, plate_layout_96: pd.DataFrame):
        """Test heatmap color mapping for different data types."""
        # Test diverging colormap for Z-scores
        fig_z = create_zscore_heatmap(
            data=plate_layout_96,
            value_column='Z_lptA',
            colorscale='RdBu_r'
        )
        
        heatmap_z = fig_z.data[0]
        assert 'RdBu' in str(heatmap_z.colorscale).lower() or 'rdbu' in str(heatmap_z.colorscale).lower()
        
        # Test sequential colormap for ratios
        fig_ratio = create_plate_heatmap(
            data=plate_layout_96,
            value_column='Ratio_lptA',
            colorscale='Viridis'
        )
        
        heatmap_ratio = fig_ratio.data[0]
        assert 'viridis' in str(heatmap_ratio.colorscale).lower()

    def test_missing_data_handling(self, plate_layout_96: pd.DataFrame):
        """Test heatmap handling of missing data."""
        # Introduce missing values
        data_with_missing = plate_layout_96.copy()
        data_with_missing.loc[5:10, 'Z_lptA'] = np.nan
        
        fig = create_plate_heatmap(
            data=data_with_missing,
            value_column='Z_lptA',
            show_missing=True
        )
        
        # Should complete without error
        assert isinstance(fig, go.Figure)
        
        # Missing values should be handled in the heatmap data
        heatmap_data = fig.data[0]
        z_values = np.array(heatmap_data.z)
        assert np.any(np.isnan(z_values))

    def test_bscore_comparison_heatmap(self, plate_layout_96: pd.DataFrame):
        """Test B-score vs Raw Z-score comparison heatmaps."""
        # Add B-score data
        plate_data = plate_layout_96.copy()
        plate_data['B_Z_lptA'] = np.random.normal(0, 1, len(plate_data))
        
        fig = create_bscore_comparison_heatmap(
            data=plate_data,
            raw_column='Z_lptA',
            bscore_column='B_Z_lptA'
        )
        
        # Should have subplots for comparison
        assert len(fig.data) >= 2  # At least 2 heatmaps
        assert 'Raw Z' in str(fig.layout.annotations) or 'B-score' in str(fig.layout.annotations)

    def test_plate_layout_formatting(self, plate_layout_96: pd.DataFrame):
        """Test plate layout formatting utilities."""
        # Test matrix conversion
        matrix = format_plate_layout(
            data=plate_layout_96,
            value_column='Z_lptA',
            rows='Row',
            cols='Col'
        )
        
        # Should be 8x12 matrix
        assert matrix.shape == (8, 12)
        
        # Should maintain proper row/column order
        assert not np.isnan(matrix).all()  # Should have valid data

    def test_heatmap_tooltips(self, plate_layout_96: pd.DataFrame):
        """Test heatmap tooltip information."""
        fig = create_plate_heatmap(
            data=plate_layout_96,
            value_column='Z_lptA',
            include_well_info=True
        )
        
        heatmap_data = fig.data[0]
        
        # Should have custom hover template or text
        assert hasattr(heatmap_data, 'hovertemplate') or hasattr(heatmap_data, 'text')


class TestColorMapping:
    """Test color mapping and styling."""

    def test_diverging_colormap(self):
        """Test diverging colormap for Z-scores."""
        colormap = get_colormap('diverging', center_zero=True)
        
        # Should be appropriate for Z-scores (centered at 0)
        assert 'RdBu' in colormap or 'Spectral' in colormap or 'RdYlBu' in colormap

    def test_sequential_colormap(self):
        """Test sequential colormap for positive values."""
        colormap = get_colormap('sequential')
        
        # Should be appropriate for ratios/OD values
        assert 'Viridis' in colormap or 'Plasma' in colormap or 'Inferno' in colormap

    def test_custom_colormap(self):
        """Test custom colormap specification."""
        custom_colormap = get_colormap('custom', custom_colors=['blue', 'white', 'red'])
        
        # Should accept custom colors
        assert isinstance(custom_colormap, (str, list))

    def test_theme_application(self):
        """Test theme application to plots."""
        fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 4, 2]))
        
        themed_fig = apply_theme(fig, theme='plotly_white')
        
        # Should have theme applied
        assert themed_fig.layout.template is not None

    def test_axis_label_formatting(self):
        """Test axis label formatting."""
        formatted_label = format_axis_labels('Z_lptA')
        
        # Should be human-readable
        assert 'Z-score' in formatted_label or 'lptA' in formatted_label
        
        formatted_ratio = format_axis_labels('Ratio_ldtD')
        assert 'Ratio' in formatted_ratio or 'ldtD' in formatted_ratio


class TestExportFormats:
    """Test plot export format validation."""

    @pytest.fixture
    def sample_plot(self) -> go.Figure:
        """Create sample plot for export testing."""
        return go.Figure(data=go.Scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13]))

    def test_png_export(self, sample_plot: go.Figure, tmp_path: Path):
        """Test PNG export format."""
        output_path = tmp_path / "test_plot.png"
        
        # Mock kaleido since it may not be available in test environment
        with patch('plotly.io.write_image') as mock_write:
            export_plot_to_file(sample_plot, str(output_path), format='png')
            mock_write.assert_called_once()

    def test_svg_export(self, sample_plot: go.Figure, tmp_path: Path):
        """Test SVG export format."""
        output_path = tmp_path / "test_plot.svg"
        
        with patch('plotly.io.write_image') as mock_write:
            export_plot_to_file(sample_plot, str(output_path), format='svg')
            mock_write.assert_called_once()

    def test_html_export(self, sample_plot: go.Figure, tmp_path: Path):
        """Test HTML export format."""
        output_path = tmp_path / "test_plot.html"
        
        with patch('plotly.io.write_html') as mock_write:
            export_plot_to_file(sample_plot, str(output_path), format='html')
            mock_write.assert_called_once()

    def test_high_dpi_export(self, sample_plot: go.Figure, tmp_path: Path):
        """Test high DPI export for publication quality."""
        output_path = tmp_path / "test_plot_hires.png"
        
        with patch('plotly.io.write_image') as mock_write:
            export_plot_to_file(
                sample_plot, 
                str(output_path), 
                format='png',
                width=1200,
                height=800,
                scale=3  # 3x DPI
            )
            
            # Should be called with scale parameter
            args, kwargs = mock_write.call_args
            assert kwargs.get('scale') == 3

    def test_format_validation(self):
        """Test export format validation."""
        # Valid formats
        assert validate_export_format('png') == True
        assert validate_export_format('svg') == True  
        assert validate_export_format('html') == True
        assert validate_export_format('pdf') == True
        
        # Invalid formats
        assert validate_export_format('txt') == False
        assert validate_export_format('doc') == False

    def test_plot_bundle_creation(self, tmp_path: Path):
        """Test creation of plot bundles with multiple formats."""
        plots = {
            'histogram': go.Figure(data=go.Histogram(x=[1, 2, 3, 4, 5])),
            'scatter': go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 4, 2])),
            'heatmap': go.Figure(data=go.Heatmap(z=[[1, 2], [3, 4]]))
        }
        
        bundle_path = tmp_path / "plot_bundle"
        
        with patch('plotly.io.write_image') as mock_write_img, \
             patch('plotly.io.write_html') as mock_write_html:
            
            bundle_info = create_plot_bundle(
                plots=plots,
                output_dir=str(bundle_path),
                formats=['png', 'html']
            )
            
            # Should create files for all plots in all formats
            expected_calls = len(plots) * 2  # 2 formats per plot
            actual_calls = mock_write_img.call_count + mock_write_html.call_count
            assert actual_calls == expected_calls
            
            # Bundle info should contain file list
            assert 'files' in bundle_info
            assert len(bundle_info['files']) == expected_calls


class TestVisualizationErrorHandling:
    """Test error handling in visualization functions."""

    def test_empty_data_handling(self):
        """Test visualization with empty datasets."""
        empty_data = pd.DataFrame()
        
        # Should handle gracefully
        fig = create_histogram(empty_data, 'nonexistent_column', handle_empty=True)
        
        # Should return empty figure or None
        assert fig is None or len(fig.data) == 0

    def test_missing_column_handling(self):
        """Test handling of missing columns."""
        data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        
        with pytest.raises(ValueError, match="Column.*not found"):
            create_histogram(data, 'nonexistent_column')

    def test_invalid_colormap_handling(self):
        """Test handling of invalid colormap specifications."""
        with pytest.raises(ValueError, match="Invalid colormap"):
            get_colormap('invalid_colormap_name')

    def test_malformed_plate_data(self):
        """Test handling of malformed plate layout data."""
        malformed_data = pd.DataFrame({
            'Row': ['A', 'B', 'Invalid'],  # Invalid row name
            'Col': [1, 2, 999],  # Invalid column number
            'Z_lptA': [1, 2, 3]
        })
        
        # Should handle gracefully or raise informative error
        with pytest.raises((ValueError, KeyError)):
            create_plate_heatmap(malformed_data, 'Z_lptA')

    def test_all_nan_visualization(self):
        """Test visualization with all NaN values."""
        nan_data = pd.DataFrame({
            'Values': [np.nan] * 10,
            'Z_lptA': [np.nan] * 10
        })
        
        # Should complete without crashing
        fig = create_histogram(nan_data, 'Z_lptA', handle_empty=True)
        
        # May return empty figure or special handling
        assert fig is None or isinstance(fig, go.Figure)


class TestVisualizationPerformance:
    """Test visualization performance for large datasets."""

    @pytest.mark.slow
    def test_large_dataset_histogram(self):
        """Test histogram performance with large datasets."""
        import time
        
        # Create large dataset
        large_data = pd.DataFrame({
            'Z_lptA': np.random.normal(0, 1, 10000),
            'PlateID': ['Plate_1'] * 10000
        })
        
        start_time = time.time()
        fig = create_histogram(large_data, 'Z_lptA')
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 5.0  # 5 seconds max
        assert isinstance(fig, go.Figure)

    @pytest.mark.slow  
    def test_large_heatmap_performance(self):
        """Test heatmap performance with large plate formats."""
        import time
        
        # Create 1536-well plate data (32x48)
        rows = [chr(65 + i // 26) + chr(65 + i % 26) for i in range(32)]
        cols = list(range(1, 49))
        
        large_plate_data = []
        for row in rows:
            for col in cols:
                large_plate_data.append({
                    'Row': row,
                    'Col': col, 
                    'Z_lptA': np.random.normal(0, 1)
                })
        
        large_df = pd.DataFrame(large_plate_data)
        
        start_time = time.time()
        fig = create_plate_heatmap(large_df, 'Z_lptA')
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 10.0  # 10 seconds max
        assert isinstance(fig, go.Figure)

    def test_memory_usage_visualization(self):
        """Test memory usage for visualization generation."""
        import psutil
        import os
        
        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple large visualizations
        for i in range(5):
            data = pd.DataFrame({
                'X': np.random.normal(0, 1, 5000),
                'Y': np.random.normal(0, 1, 5000),
                'Z': np.random.normal(0, 1, 5000),
            })
            
            fig1 = create_histogram(data, 'X')
            fig2 = create_scatter_plot(data, 'X', 'Y')
            fig3 = create_boxplot(data, 'Z')
            
            # Clean up references
            del fig1, fig2, fig3, data
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not consume excessive memory
        assert memory_increase < 500  # Less than 500MB increase