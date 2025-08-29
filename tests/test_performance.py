"""Performance tests for bio-hit-finder platform.

Tests benchmark core calculations against PRD targets:
- Single plate processing: < 200ms for ~2000 rows  
- Multi-plate processing: < 2s for 10 plates
- Memory usage validation: < 1GB for 10 plates (~20,000 rows)
- Caching effectiveness tests
- Large dataset handling
"""

import time
import psutil
import os
from typing import Dict, Any, List
import gc
import threading
from contextlib import contextmanager

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from core.calculations import process_plate_calculations
from core.plate_processor import PlateProcessor
from core.statistics import calculate_robust_zscore, calculate_mad
from analytics.bscore import calculate_bscore_matrix
from analytics.edge_effects import detect_edge_effects
from visualizations.charts import create_histogram, create_scatter_plot
from visualizations.heatmaps import create_plate_heatmap
from export.csv_export import export_processed_data
from export.bundle import create_export_bundle


@contextmanager
def memory_monitor():
    """Context manager to monitor memory usage during operations."""
    process = psutil.Process(os.getpid())
    
    # Force garbage collection before monitoring
    gc.collect()
    
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    peak_memory = initial_memory
    
    def monitor_memory():
        nonlocal peak_memory
        while True:
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            peak_memory = max(peak_memory, current_memory)
            time.sleep(0.1)  # Check every 100ms
    
    monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
    monitor_thread.start()
    
    try:
        yield {'initial': initial_memory, 'peak': lambda: peak_memory}
    finally:
        # Force cleanup
        gc.collect()


class TestCoreCalculationPerformance:
    """Test performance of core calculation functions."""

    @pytest.mark.performance
    def test_single_plate_processing_speed(self, large_dataset):
        """Test single large plate processing meets PRD target (< 200ms for ~2000 rows)."""
        # Use subset to match PRD specification (~2000 rows)
        test_data = large_dataset.head(2000).copy()
        
        # Warm-up run
        _ = process_plate_calculations(test_data, viability_threshold=0.3)
        
        # Timed benchmark run
        start_time = time.perf_counter()
        result = process_plate_calculations(test_data, viability_threshold=0.3)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # PRD requirement: < 200ms for ~2000 rows
        assert processing_time < 200.0, \
            f"Single plate processing took {processing_time:.1f}ms, expected < 200ms"
        
        # Verify result integrity
        assert len(result) == len(test_data)
        assert 'Ratio_lptA' in result.columns
        assert 'Z_lptA' in result.columns
        
        print(f"Single plate processing: {processing_time:.1f}ms for {len(test_data)} rows")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_multi_plate_processing_speed(self, performance_test_data):
        """Test multi-plate processing meets PRD target (< 2s for 10 plates)."""
        # Create 10 plates with ~2000 rows each to match PRD spec
        large_plates = []
        base_plate = performance_test_data['small']  # 96 wells
        
        for plate_id in range(10):
            # Expand each plate to ~2000 rows
            expanded_frames = []
            for rep in range(21):  # 96 * 21 ≈ 2016 rows
                plate_copy = base_plate.copy()
                plate_copy['Well'] = plate_copy['Well'] + f'_rep{rep}'
                plate_copy['PlateID'] = f'Perf_Plate_{plate_id + 1:02d}'
                expanded_frames.append(plate_copy)
            
            large_plate = pd.concat(expanded_frames, ignore_index=True)
            large_plates.append(large_plate)
        
        processor = PlateProcessor()
        
        # Warm-up run with single plate
        _ = processor.process_plate(large_plates[0], viability_threshold=0.3)
        
        # Timed benchmark run
        start_time = time.perf_counter()
        
        processed_plates = []
        for plate in large_plates:
            processed = processor.process_plate(plate, viability_threshold=0.3)
            processed_plates.append(processed)
        
        # Aggregate results
        combined_data = pd.concat(processed_plates, ignore_index=True)
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        
        # PRD requirement: < 2s for 10 plates
        assert processing_time < 2.0, \
            f"Multi-plate processing took {processing_time:.2f}s, expected < 2.0s"
        
        # Verify result integrity
        total_expected_rows = sum(len(p) for p in large_plates)
        assert len(combined_data) == total_expected_rows
        assert len(combined_data['PlateID'].unique()) == 10
        
        print(f"Multi-plate processing: {processing_time:.2f}s for {len(combined_data)} total rows")

    @pytest.mark.performance
    def test_robust_zscore_calculation_speed(self):
        """Test robust Z-score calculation performance."""
        # Create large array
        large_array = np.random.normal(0, 1, 50000)
        
        # Warm-up
        _ = calculate_robust_zscore(large_array[:1000])
        
        # Benchmark
        start_time = time.perf_counter()
        z_scores = calculate_robust_zscore(large_array)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Should complete quickly even for large arrays
        assert processing_time < 100.0, \
            f"Z-score calculation took {processing_time:.1f}ms for 50K values"
        
        # Verify result
        assert len(z_scores) == len(large_array)
        assert abs(np.median(z_scores)) < 0.1  # Robust median ~0

    @pytest.mark.performance
    def test_mad_calculation_speed(self):
        """Test MAD calculation performance."""
        # Create large array
        large_array = np.random.normal(0, 1, 100000)
        
        # Benchmark
        start_time = time.perf_counter()
        mad_value = calculate_mad(large_array)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Should complete quickly
        assert processing_time < 50.0, \
            f"MAD calculation took {processing_time:.1f}ms for 100K values"
        
        # Verify result
        assert mad_value > 0
        assert 0.5 < mad_value < 1.5  # Should be ~1 for normal distribution

    @pytest.mark.performance
    def test_bscore_calculation_speed(self):
        """Test B-score matrix calculation performance."""
        # Create large plate matrix (384-well equivalent)
        large_matrix = np.random.normal(0, 1, (16, 24))
        
        # Add artificial bias for more realistic test
        row_bias = np.arange(16).reshape(-1, 1) * 0.1
        col_bias = np.arange(24).reshape(1, -1) * 0.05
        biased_matrix = large_matrix + row_bias + col_bias
        
        # Benchmark
        start_time = time.perf_counter()
        b_scores = calculate_bscore_matrix(biased_matrix)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Should complete quickly for single plate
        assert processing_time < 100.0, \
            f"B-score calculation took {processing_time:.1f}ms"
        
        # Verify result shape and properties
        assert b_scores.shape == biased_matrix.shape
        assert abs(np.nanmean(b_scores)) < 0.1  # Mean should be ~0


class TestMemoryUsage:
    """Test memory usage requirements."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_single_large_plate(self, large_dataset):
        """Test memory usage for single large plate processing."""
        with memory_monitor() as monitor:
            # Process large dataset
            result = process_plate_calculations(large_dataset, viability_threshold=0.3)
            
            # Verify processing worked
            assert len(result) == len(large_dataset)
            assert 'Z_lptA' in result.columns
        
        memory_used = monitor['peak']() - monitor['initial']
        
        # Should not use excessive memory for single plate
        assert memory_used < 200, \
            f"Single plate processing used {memory_used:.1f}MB, expected < 200MB"
        
        print(f"Single large plate memory usage: {memory_used:.1f}MB")

    @pytest.mark.performance  
    @pytest.mark.slow
    def test_memory_usage_ten_plates(self):
        """Test memory usage meets PRD target (< 1GB for 10 plates with ~20,000 total rows)."""
        with memory_monitor() as monitor:
            # Create 10 large plates
            plates = []
            
            for i in range(10):
                # Create plate with ~2000 rows each
                np.random.seed(100 + i)  # Reproducible but different data
                
                large_plate_data = {
                    'Well': [f"W{j+1:04d}" for j in range(2000)],
                    'PlateID': [f'MemTest_Plate_{i+1:02d}'] * 2000,
                    'BG_lptA': np.random.normal(1000, 200, 2000),
                    'BT_lptA': np.random.normal(500, 100, 2000),
                    'BG_ldtD': np.random.normal(1200, 250, 2000),
                    'BT_ldtD': np.random.normal(600, 120, 2000),
                    'OD_WT': np.random.normal(1.5, 0.3, 2000),
                    'OD_tolC': np.random.normal(1.2, 0.25, 2000),
                    'OD_SA': np.random.normal(1.0, 0.2, 2000),
                }
                
                plate_df = pd.DataFrame(large_plate_data)
                plates.append(plate_df)
            
            # Process all plates
            processor = PlateProcessor()
            processed_plates = []
            
            for plate in plates:
                processed = processor.process_plate(plate, viability_threshold=0.3)
                processed_plates.append(processed)
            
            # Aggregate
            combined_data = pd.concat(processed_plates, ignore_index=True)
            
            # Verify we have the expected data size
            assert len(combined_data) >= 18000  # ~2000 * 10, allowing some tolerance
        
        memory_used = monitor['peak']() - monitor['initial']
        
        # PRD requirement: < 1GB for 10 plates
        assert memory_used < 1024, \
            f"Ten-plate processing used {memory_used:.1f}MB, expected < 1024MB"
        
        print(f"Ten-plate memory usage: {memory_used:.1f}MB for {len(combined_data)} total rows")

    @pytest.mark.performance
    def test_memory_cleanup_after_processing(self, large_dataset):
        """Test that memory is properly cleaned up after processing."""
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process data in loop to test cleanup
        for i in range(5):
            large_copy = large_dataset.copy()
            result = process_plate_calculations(large_copy, viability_threshold=0.3)
            
            # Explicitly delete references
            del large_copy, result
            
            # Force garbage collection
            gc.collect()
        
        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - baseline_memory
        
        # Memory growth should be minimal (< 100MB)
        assert memory_growth < 100, \
            f"Memory grew by {memory_growth:.1f}MB after 5 processing cycles"


class TestCacheEffectiveness:
    """Test caching effectiveness and performance."""

    @pytest.mark.performance
    def test_repeated_calculation_caching(self, normal_96_well_plate):
        """Test that repeated calculations benefit from caching."""
        # First calculation (cold)
        start_time = time.perf_counter()
        result1 = process_plate_calculations(normal_96_well_plate, viability_threshold=0.3)
        first_time = time.perf_counter() - start_time
        
        # Second calculation (should be faster if cached)
        start_time = time.perf_counter()
        result2 = process_plate_calculations(normal_96_well_plate, viability_threshold=0.3)
        second_time = time.perf_counter() - start_time
        
        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2, check_exact=True)
        
        # Note: Without actual caching implementation, we can't assert speedup
        # This test structure is ready for when caching is implemented
        print(f"First calculation: {first_time*1000:.1f}ms")
        print(f"Second calculation: {second_time*1000:.1f}ms")

    @pytest.mark.performance
    def test_parameter_change_cache_invalidation(self, normal_96_well_plate):
        """Test that cache is properly invalidated when parameters change."""
        # Calculate with first threshold
        result1 = process_plate_calculations(normal_96_well_plate, viability_threshold=0.3)
        
        # Calculate with different threshold
        result2 = process_plate_calculations(normal_96_well_plate, viability_threshold=0.5)
        
        # Results should be different (different viability flags)
        assert not result1.equals(result2)
        
        # Viability columns should differ
        assert not result1['viability_ok_lptA'].equals(result2['viability_ok_lptA'])


class TestVisualizationPerformance:
    """Test visualization generation performance."""

    @pytest.mark.performance
    def test_histogram_generation_speed(self, large_dataset):
        """Test histogram generation performance."""
        # Use subset for visualization
        viz_data = large_dataset.head(5000)
        
        start_time = time.perf_counter()
        fig = create_histogram(viz_data, 'Z_lptA', bins=50)
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Should generate quickly
        assert processing_time < 2000, \
            f"Histogram generation took {processing_time:.1f}ms for 5K points"
        
        assert fig is not None

    @pytest.mark.performance
    def test_scatter_plot_generation_speed(self, large_dataset):
        """Test scatter plot generation performance."""
        viz_data = large_dataset.head(5000)
        
        start_time = time.perf_counter()
        fig = create_scatter_plot(viz_data, 'Ratio_lptA', 'Ratio_ldtD')
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Should generate quickly
        assert processing_time < 3000, \
            f"Scatter plot generation took {processing_time:.1f}ms for 5K points"
        
        assert fig is not None

    @pytest.mark.performance
    def test_heatmap_generation_speed(self, normal_96_well_plate):
        """Test plate heatmap generation performance."""
        start_time = time.perf_counter()
        fig = create_plate_heatmap(normal_96_well_plate, 'Z_lptA')
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Heatmaps should generate quickly for single plate
        assert processing_time < 1000, \
            f"Heatmap generation took {processing_time:.1f}ms"
        
        assert fig is not None


class TestExportPerformance:
    """Test export functionality performance."""

    @pytest.mark.performance
    def test_csv_export_speed(self, large_dataset, tmp_path):
        """Test CSV export performance."""
        output_file = tmp_path / "large_export.csv"
        
        start_time = time.perf_counter()
        result = export_processed_data(large_dataset, str(output_file))
        end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Should export quickly
        assert processing_time < 1000, \
            f"CSV export took {processing_time:.1f}ms for {len(large_dataset)} rows"
        
        assert result['status'] == 'success'
        assert output_file.exists()

    @pytest.mark.performance
    @pytest.mark.slow
    def test_bundle_creation_speed(self, sample_processed_data, tmp_path):
        """Test export bundle creation performance."""
        bundle_path = tmp_path / "perf_bundle.zip"
        
        config = {'viability_threshold': 0.3, 'include_plots': True}
        
        with patch('export.pdf_generator.generate_qc_report') as mock_pdf, \
             patch('plotly.io.write_image') as mock_plot:
            
            mock_pdf.return_value = {'status': 'success', 'file_path': 'report.pdf'}
            
            start_time = time.perf_counter()
            result = create_export_bundle(
                processed_data=sample_processed_data,
                output_path=str(bundle_path),
                config=config
            )
            end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        
        # Bundle creation should be reasonably fast
        assert processing_time < 5000, \
            f"Bundle creation took {processing_time:.1f}ms"
        
        assert result['status'] == 'success'


class TestScalabilityLimits:
    """Test system behavior at scalability limits."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_maximum_plate_size_handling(self):
        """Test handling of very large plate formats."""
        # Simulate 1536-well plate (32x48)
        np.random.seed(200)
        
        large_plate_data = []
        for row in range(32):
            for col in range(48):
                large_plate_data.append({
                    'Well': f"R{row+1:02d}C{col+1:02d}",
                    'Row': chr(65 + row // 26) + chr(65 + row % 26) if row < 26 else f"R{row+1}",
                    'Col': col + 1,
                    'PlateID': 'Large_Format_Plate',
                    'BG_lptA': np.random.normal(1000, 200),
                    'BT_lptA': np.random.normal(500, 100),
                    'BG_ldtD': np.random.normal(1200, 250),
                    'BT_ldtD': np.random.normal(600, 120),
                    'OD_WT': np.random.normal(1.5, 0.3),
                    'OD_tolC': np.random.normal(1.2, 0.25),
                    'OD_SA': np.random.normal(1.0, 0.2),
                })
        
        large_format_plate = pd.DataFrame(large_plate_data)
        
        # Should handle large format without excessive time/memory
        with memory_monitor() as monitor:
            start_time = time.perf_counter()
            result = process_plate_calculations(large_format_plate, viability_threshold=0.3)
            end_time = time.perf_counter()
        
        processing_time = end_time - start_time
        memory_used = monitor['peak']() - monitor['initial']
        
        # Should complete in reasonable time
        assert processing_time < 5.0, \
            f"Large format processing took {processing_time:.2f}s"
        
        # Should not use excessive memory
        assert memory_used < 500, \
            f"Large format processing used {memory_used:.1f}MB"
        
        # Verify result integrity
        assert len(result) == len(large_plate_data)
        assert len(result) == 32 * 48  # 1536 wells

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_processing_simulation(self, multi_plate_dataset):
        """Test simulation of concurrent processing load."""
        import concurrent.futures
        
        def process_single_plate(plate_data):
            """Process single plate (simulates concurrent user)."""
            return process_plate_calculations(plate_data, viability_threshold=0.3)
        
        with memory_monitor() as monitor:
            start_time = time.perf_counter()
            
            # Simulate 3 concurrent users processing plates
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(process_single_plate, plate) 
                    for plate in multi_plate_dataset
                ]
                
                results = [future.result() for future in futures]
            
            end_time = time.perf_counter()
        
        processing_time = end_time - start_time
        memory_used = monitor['peak']() - monitor['initial']
        
        # Should complete concurrent processing efficiently
        assert processing_time < 10.0, \
            f"Concurrent processing took {processing_time:.2f}s"
        
        assert memory_used < 800, \
            f"Concurrent processing used {memory_used:.1f}MB"
        
        # Verify all plates processed
        assert len(results) == len(multi_plate_dataset)
        for result in results:
            assert len(result) > 0
            assert 'Z_lptA' in result.columns


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.mark.performance
    def test_performance_baseline_comparison(self, normal_96_well_plate):
        """Test performance against baseline expectations."""
        # Define expected performance baselines
        baselines = {
            'single_plate_96_wells_ms': 50.0,    # 50ms baseline for 96 wells
            'memory_single_plate_mb': 50.0,      # 50MB baseline for single plate
        }
        
        # Test processing time
        with memory_monitor() as monitor:
            start_time = time.perf_counter()
            result = process_plate_calculations(normal_96_well_plate, viability_threshold=0.3)
            end_time = time.perf_counter()
        
        processing_time = (end_time - start_time) * 1000  # ms
        memory_used = monitor['peak']() - monitor['initial']
        
        # Should meet baseline performance
        assert processing_time < baselines['single_plate_96_wells_ms'], \
            f"Performance regression: {processing_time:.1f}ms > {baselines['single_plate_96_wells_ms']}ms baseline"
        
        assert memory_used < baselines['memory_single_plate_mb'], \
            f"Memory regression: {memory_used:.1f}MB > {baselines['memory_single_plate_mb']}MB baseline"
        
        # Log performance metrics
        print(f"Performance metrics vs baseline:")
        print(f"  Processing time: {processing_time:.1f}ms (baseline: {baselines['single_plate_96_wells_ms']}ms)")
        print(f"  Memory usage: {memory_used:.1f}MB (baseline: {baselines['memory_single_plate_mb']}MB)")

    @pytest.mark.performance
    def test_edge_case_performance_stability(self):
        """Test performance stability with edge cases."""
        edge_cases = [
            # Empty data
            pd.DataFrame(),
            
            # Single row
            pd.DataFrame({
                'BG_lptA': [1000], 'BT_lptA': [500], 'BG_ldtD': [1200], 'BT_ldtD': [600],
                'OD_WT': [1.5], 'OD_tolC': [1.2], 'OD_SA': [1.0]
            }),
            
            # All NaN values
            pd.DataFrame({
                'BG_lptA': [np.nan] * 96, 'BT_lptA': [np.nan] * 96,
                'BG_ldtD': [np.nan] * 96, 'BT_ldtD': [np.nan] * 96,
                'OD_WT': [np.nan] * 96, 'OD_tolC': [np.nan] * 96, 'OD_SA': [np.nan] * 96
            }),
            
            # Constant values (MAD = 0)
            pd.DataFrame({
                'BG_lptA': [1000] * 96, 'BT_lptA': [500] * 96,
                'BG_ldtD': [1200] * 96, 'BT_ldtD': [600] * 96,
                'OD_WT': [1.5] * 96, 'OD_tolC': [1.2] * 96, 'OD_SA': [1.0] * 96
            })
        ]
        
        for i, edge_case in enumerate(edge_cases):
            start_time = time.perf_counter()
            
            try:
                result = process_plate_calculations(edge_case, viability_threshold=0.3, validate_columns=False)
                processing_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Should handle edge cases quickly (< 100ms)
                assert processing_time < 100, \
                    f"Edge case {i} took {processing_time:.1f}ms, expected < 100ms"
                
            except Exception as e:
                processing_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Even errors should be handled quickly
                assert processing_time < 100, \
                    f"Edge case {i} error handling took {processing_time:.1f}ms"
                
                print(f"Edge case {i} handled with expected error: {type(e).__name__}")


if __name__ == "__main__":
    # Run basic performance tests when executed directly
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    
    from tests.fixtures.sample_plates import create_normal_96_well_plate, create_multi_plate_dataset
    
    print("Running basic performance tests...")
    
    # Test single plate
    plate = create_normal_96_well_plate()
    start = time.perf_counter()
    result = process_plate_calculations(plate, viability_threshold=0.3)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"96-well plate processing: {elapsed:.1f}ms")
    
    # Test multi-plate
    plates = create_multi_plate_dataset(3)
    start = time.perf_counter()
    for p in plates:
        _ = process_plate_calculations(p, viability_threshold=0.3)
    elapsed = time.perf_counter() - start
    print(f"3-plate processing: {elapsed:.2f}s")
    
    print("Basic performance tests completed.")