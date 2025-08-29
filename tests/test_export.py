"""Export functionality tests for bio-hit-finder platform.

Tests CSV export format validation, PDF generation testing, ZIP bundle integrity checks,
Manifest.json structure validation, and file I/O error handling.
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import os

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, mock_open

from export.csv_export import (
    export_processed_data,
    export_top_hits,
    export_plate_summary,
    validate_csv_format,
    create_csv_metadata
)
from export.pdf_generator import (
    generate_qc_report,
    create_formula_section,
    render_plots_to_pdf,
    validate_pdf_content
)
from export.bundle import (
    create_export_bundle,
    validate_bundle_integrity,
    create_manifest,
    compress_bundle_files
)


class TestCSVExport:
    """Test CSV export functionality."""

    @pytest.fixture
    def sample_processed_data(self) -> pd.DataFrame:
        """Create sample processed data for export testing."""
        np.random.seed(42)
        n_wells = 96
        
        return pd.DataFrame({
            'Well': [f"A{i+1:02d}" for i in range(n_wells)],
            'PlateID': ['Test_Plate'] * n_wells,
            'Row': ['A'] * n_wells,
            'Col': list(range(1, n_wells + 1)),
            'BG_lptA': np.random.normal(1000, 200, n_wells),
            'BT_lptA': np.random.normal(500, 100, n_wells),
            'BG_ldtD': np.random.normal(1200, 250, n_wells),
            'BT_ldtD': np.random.normal(600, 120, n_wells),
            'OD_WT': np.random.normal(1.5, 0.3, n_wells),
            'OD_tolC': np.random.normal(1.2, 0.25, n_wells),
            'OD_SA': np.random.normal(1.0, 0.2, n_wells),
            'Ratio_lptA': np.random.normal(2.0, 0.5, n_wells),
            'Ratio_ldtD': np.random.normal(2.2, 0.6, n_wells),
            'OD_WT_norm': np.random.normal(1.0, 0.2, n_wells),
            'OD_tolC_norm': np.random.normal(1.0, 0.2, n_wells),
            'OD_SA_norm': np.random.normal(1.0, 0.2, n_wells),
            'Z_lptA': np.random.normal(0, 1, n_wells),
            'Z_ldtD': np.random.normal(0, 1, n_wells),
            'viability_ok_lptA': np.random.choice([True, False], n_wells, p=[0.85, 0.15]),
            'viability_fail_lptA': np.random.choice([True, False], n_wells, p=[0.15, 0.85]),
            'viability_ok_ldtD': np.random.choice([True, False], n_wells, p=[0.85, 0.15]),
            'viability_fail_ldtD': np.random.choice([True, False], n_wells, p=[0.15, 0.85]),
        })

    def test_basic_csv_export(self, sample_processed_data: pd.DataFrame, tmp_path: Path):
        """Test basic CSV export functionality."""
        output_file = tmp_path / "test_export.csv"
        
        # Export data
        result = export_processed_data(sample_processed_data, str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        assert result['status'] == 'success'
        assert result['file_path'] == str(output_file)
        
        # Verify content
        reimported = pd.read_csv(output_file)
        
        # Check basic structure
        assert len(reimported) == len(sample_processed_data)
        assert set(reimported.columns) == set(sample_processed_data.columns)
        
        # Check data integrity
        pd.testing.assert_frame_equal(
            reimported.sort_values('Well').reset_index(drop=True),
            sample_processed_data.sort_values('Well').reset_index(drop=True),
            check_exact=False,
            rtol=1e-10
        )

    def test_csv_numerical_precision(self, sample_processed_data: pd.DataFrame, tmp_path: Path):
        """Test CSV numerical precision preservation."""
        # Add high-precision values
        precision_data = sample_processed_data.copy()
        precision_data['High_Precision'] = [1.123456789012345] * len(precision_data)
        
        output_file = tmp_path / "precision_test.csv"
        export_processed_data(precision_data, str(output_file))
        
        # Reimport and check precision
        reimported = pd.read_csv(output_file)
        
        # Should maintain reasonable precision (CSV limitation)
        original_values = precision_data['Ratio_lptA'].values
        reimported_values = reimported['Ratio_lptA'].values
        
        np.testing.assert_allclose(
            original_values,
            reimported_values,
            rtol=1e-9,
            atol=1e-12,
            err_msg="CSV export precision requirement violated"
        )

    def test_csv_with_missing_values(self, sample_processed_data: pd.DataFrame, tmp_path: Path):
        """Test CSV export with missing/NaN values."""
        # Introduce missing values
        data_with_nan = sample_processed_data.copy()
        data_with_nan.loc[5:10, 'Z_lptA'] = np.nan
        data_with_nan.loc[15:20, 'Ratio_ldtD'] = np.nan
        
        output_file = tmp_path / "test_with_nan.csv"
        export_processed_data(data_with_nan, str(output_file))
        
        # Verify file created and readable
        assert output_file.exists()
        
        reimported = pd.read_csv(output_file)
        
        # Check NaN values are preserved
        assert reimported['Z_lptA'].iloc[5:11].isna().all()
        assert reimported['Ratio_ldtD'].iloc[15:21].isna().all()

    def test_top_hits_export(self, sample_processed_data: pd.DataFrame, tmp_path: Path):
        """Test top hits export functionality."""
        # Add max Z-score column for ranking
        sample_processed_data['max_abs_z'] = np.maximum(
            np.abs(sample_processed_data['Z_lptA']),
            np.abs(sample_processed_data['Z_ldtD'])
        )
        
        output_file = tmp_path / "top_hits.csv"
        
        result = export_top_hits(
            data=sample_processed_data,
            output_path=str(output_file),
            top_n=20,
            rank_by='max_abs_z'
        )
        
        # Verify export
        assert result['status'] == 'success'
        assert output_file.exists()
        
        # Check content
        top_hits = pd.read_csv(output_file)
        
        # Should have exactly top_n rows (or fewer if not enough data)
        assert len(top_hits) <= 20
        
        # Should be sorted by ranking metric
        if len(top_hits) > 1:
            rank_values = top_hits['max_abs_z'].values
            assert np.all(rank_values[:-1] >= rank_values[1:])  # Descending order

    def test_plate_summary_export(self, sample_processed_data: pd.DataFrame, tmp_path: Path):
        """Test plate summary export functionality."""
        output_file = tmp_path / "plate_summary.csv"
        
        result = export_plate_summary(
            data=sample_processed_data,
            output_path=str(output_file)
        )
        
        # Verify export
        assert result['status'] == 'success'
        assert output_file.exists()
        
        # Check content structure
        summary = pd.read_csv(output_file)
        
        # Should have summary statistics
        expected_columns = [
            'PlateID', 'total_wells', 'viable_wells_lptA', 'viable_wells_ldtD',
            'median_z_lptA', 'median_z_ldtD', 'mad_z_lptA', 'mad_z_ldtD'
        ]
        
        for col in expected_columns:
            assert col in summary.columns, f"Missing summary column: {col}"

    def test_csv_format_validation(self):
        """Test CSV format validation."""
        # Valid CSV content
        valid_csv_path = tempfile.mktemp(suffix='.csv')
        try:
            pd.DataFrame({'A': [1, 2], 'B': [3, 4]}).to_csv(valid_csv_path, index=False)
            assert validate_csv_format(valid_csv_path) == True
        finally:
            if os.path.exists(valid_csv_path):
                os.unlink(valid_csv_path)
        
        # Invalid CSV (non-existent file)
        assert validate_csv_format('/nonexistent/file.csv') == False

    def test_csv_metadata_creation(self, sample_processed_data: pd.DataFrame):
        """Test CSV metadata creation."""
        metadata = create_csv_metadata(
            data=sample_processed_data,
            config={'viability_threshold': 0.3, 'z_cutoff': 2.0}
        )
        
        # Should contain essential metadata
        assert 'row_count' in metadata
        assert 'column_count' in metadata
        assert 'export_timestamp' in metadata
        assert 'config' in metadata
        
        # Verify values
        assert metadata['row_count'] == len(sample_processed_data)
        assert metadata['column_count'] == len(sample_processed_data.columns)


class TestPDFGeneration:
    """Test PDF generation functionality."""

    @pytest.fixture
    def sample_config(self) -> Dict[str, Any]:
        """Sample configuration for PDF generation."""
        return {
            'viability_threshold': 0.3,
            'z_score_threshold': 2.0,
            'bscore_enabled': True,
            'edge_detection_enabled': True,
            'plate_type': '96-well'
        }

    def test_basic_pdf_generation(self, tmp_path: Path, sample_config: Dict[str, Any]):
        """Test basic PDF report generation."""
        # Create minimal sample data
        sample_data = pd.DataFrame({
            'Well': ['A01', 'A02', 'A03'],
            'PlateID': ['Test_Plate'] * 3,
            'Z_lptA': [0.5, -1.2, 2.3],
            'Z_ldtD': [-0.8, 1.5, -0.9],
            'viability_ok_lptA': [True, True, False],
        })
        
        output_file = tmp_path / "test_report.pdf"
        
        # Mock PDF generation since WeasyPrint may not be available
        with patch('export.pdf_generator.HTML') as mock_html, \
             patch('export.pdf_generator.render_template') as mock_template:
            
            mock_template.return_value = "<html><body>Test Report</body></html>"
            mock_pdf = MagicMock()
            mock_html.return_value.write_pdf = MagicMock()
            
            result = generate_qc_report(
                processed_data=sample_data,
                output_path=str(output_file),
                config=sample_config
            )
            
            # Should attempt to generate PDF
            assert result['status'] == 'success'
            mock_template.assert_called_once()

    def test_formula_section_generation(self, sample_config: Dict[str, Any]):
        """Test formula section generation for PDF."""
        formulas_html = create_formula_section(config=sample_config)
        
        # Should contain mathematical formulas
        assert isinstance(formulas_html, str)
        assert len(formulas_html) > 0
        
        # Should contain key formulas from PRD
        assert 'Ratio' in formulas_html or 'ratio' in formulas_html
        assert 'median' in formulas_html
        assert 'MAD' in formulas_html or 'mad' in formulas_html

    def test_plots_to_pdf_rendering(self, tmp_path: Path):
        """Test rendering plots to PDF."""
        import plotly.graph_objects as go
        
        # Create sample plots
        plots = {
            'histogram': go.Figure(data=go.Histogram(x=[1, 2, 3, 4, 5])),
            'scatter': go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 4, 2]))
        }
        
        output_dir = tmp_path / "plots"
        output_dir.mkdir()
        
        with patch('plotly.io.write_image') as mock_write:
            result = render_plots_to_pdf(
                plots=plots,
                output_dir=str(output_dir)
            )
            
            # Should attempt to render all plots
            assert result['status'] == 'success'
            assert mock_write.call_count == len(plots)

    def test_pdf_content_validation(self, tmp_path: Path):
        """Test PDF content validation."""
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n%%EOF")
        
        # Basic validation should pass
        assert validate_pdf_content(str(pdf_file)) == True
        
        # Non-existent file should fail
        assert validate_pdf_content(str(tmp_path / "nonexistent.pdf")) == False

    def test_pdf_with_mathematical_formulas(self, sample_config: Dict[str, Any]):
        """Test PDF generation with mathematical formulas."""
        # Test formula rendering
        formulas = create_formula_section(sample_config)
        
        # Should contain LaTeX-style or HTML-rendered formulas
        expected_formulas = [
            'BG_lptA / BT_lptA',  # Reporter ratio
            '1.4826',  # Robust scaling factor
            'median',  # Statistical median
        ]
        
        for formula in expected_formulas:
            assert formula in formulas or formula.replace('_', '') in formulas

    def test_pdf_error_handling(self, tmp_path: Path):
        """Test PDF generation error handling."""
        invalid_data = pd.DataFrame()  # Empty data
        
        output_file = tmp_path / "error_test.pdf"
        
        with patch('export.pdf_generator.render_template', side_effect=Exception("Template error")):
            result = generate_qc_report(
                processed_data=invalid_data,
                output_path=str(output_file),
                config={}
            )
            
            # Should handle error gracefully
            assert result['status'] == 'error'
            assert 'error_message' in result


class TestZIPBundle:
    """Test ZIP bundle creation and validation."""

    @pytest.fixture
    def sample_bundle_data(self) -> Dict[str, Any]:
        """Sample data for bundle creation."""
        return {
            'processed_data': pd.DataFrame({
                'Well': ['A01', 'A02', 'A03'],
                'Z_lptA': [0.5, -1.2, 2.3],
                'Z_ldtD': [-0.8, 1.5, -0.9],
            }),
            'config': {
                'viability_threshold': 0.3,
                'z_score_threshold': 2.0,
                'export_timestamp': '2024-01-15T10:30:00'
            },
            'plots': {
                'histogram': 'mock_histogram_data',
                'scatter': 'mock_scatter_data'
            }
        }

    def test_basic_bundle_creation(self, sample_bundle_data: Dict[str, Any], tmp_path: Path):
        """Test basic ZIP bundle creation."""
        bundle_path = tmp_path / "test_bundle.zip"
        
        with patch('export.csv_export.export_processed_data') as mock_csv, \
             patch('export.pdf_generator.generate_qc_report') as mock_pdf, \
             patch('plotly.io.write_image') as mock_plot:
            
            mock_csv.return_value = {'status': 'success', 'file_path': 'data.csv'}
            mock_pdf.return_value = {'status': 'success', 'file_path': 'report.pdf'}
            mock_plot.return_value = None
            
            result = create_export_bundle(
                processed_data=sample_bundle_data['processed_data'],
                output_path=str(bundle_path),
                config=sample_bundle_data['config'],
                include_plots=True
            )
            
            # Should create bundle successfully
            assert result['status'] == 'success'
            assert 'manifest' in result

    def test_bundle_integrity_validation(self, tmp_path: Path):
        """Test ZIP bundle integrity validation."""
        # Create a test ZIP file
        bundle_path = tmp_path / "test_bundle.zip"
        
        with zipfile.ZipFile(bundle_path, 'w') as zf:
            zf.writestr("manifest.json", '{"version": "1.0", "files": ["data.csv"]}')
            zf.writestr("data.csv", "Well,Z_lptA\nA01,0.5")
            zf.writestr("report.pdf", "%PDF-1.4 mock content")
        
        # Validate integrity
        validation_result = validate_bundle_integrity(str(bundle_path))
        
        assert validation_result['is_valid'] == True
        assert 'files' in validation_result
        assert len(validation_result['files']) == 3  # manifest + csv + pdf

    def test_manifest_creation(self, sample_bundle_data: Dict[str, Any]):
        """Test manifest.json creation."""
        files_list = ['processed_data.csv', 'report.pdf', 'histogram.png']
        
        manifest = create_manifest(
            config=sample_bundle_data['config'],
            files=files_list,
            data_summary={'total_wells': 96, 'plates': 1}
        )
        
        # Should contain required fields
        assert 'version' in manifest
        assert 'export_timestamp' in manifest
        assert 'config' in manifest
        assert 'files' in manifest
        assert 'data_summary' in manifest
        
        # Verify content
        assert manifest['files'] == files_list
        assert manifest['config'] == sample_bundle_data['config']

    def test_bundle_compression(self, tmp_path: Path):
        """Test bundle file compression."""
        # Create test files
        test_files = []
        for i in range(3):
            test_file = tmp_path / f"test_file_{i}.txt"
            test_file.write_text("Test content " * 1000)  # Create substantial content
            test_files.append(str(test_file))
        
        bundle_path = tmp_path / "compressed_bundle.zip"
        
        result = compress_bundle_files(
            files=test_files,
            output_path=str(bundle_path),
            compression_level=6
        )
        
        # Should create compressed bundle
        assert result['status'] == 'success'
        assert bundle_path.exists()
        
        # Verify compression
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            assert len(zf.namelist()) == len(test_files)

    def test_bundle_with_missing_files(self, tmp_path: Path):
        """Test bundle creation with missing source files."""
        bundle_path = tmp_path / "incomplete_bundle.zip"
        
        # Try to create bundle with non-existent files
        missing_files = ['/nonexistent/file1.csv', '/nonexistent/file2.pdf']
        
        result = compress_bundle_files(
            files=missing_files,
            output_path=str(bundle_path)
        )
        
        # Should handle missing files gracefully
        assert result['status'] == 'error' or result['status'] == 'partial'
        assert 'missing_files' in result or 'error_message' in result

    def test_bundle_file_permissions(self, tmp_path: Path):
        """Test bundle creation with various file permissions."""
        # Create test file
        test_file = tmp_path / "test_data.csv"
        test_file.write_text("Well,Z_lptA\nA01,0.5")
        
        # Create bundle
        bundle_path = tmp_path / "permissions_test.zip"
        
        result = compress_bundle_files(
            files=[str(test_file)],
            output_path=str(bundle_path)
        )
        
        assert result['status'] == 'success'
        assert bundle_path.exists()
        
        # Verify bundle is readable
        with zipfile.ZipFile(bundle_path, 'r') as zf:
            content = zf.read(test_file.name).decode('utf-8')
            assert 'A01,0.5' in content


class TestExportErrorHandling:
    """Test error handling in export operations."""

    def test_invalid_output_path(self):
        """Test handling of invalid output paths."""
        sample_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        
        # Invalid directory
        invalid_path = "/nonexistent/directory/output.csv"
        
        result = export_processed_data(sample_data, invalid_path)
        
        # Should handle error gracefully
        assert result['status'] == 'error'
        assert 'error_message' in result

    def test_permission_denied_export(self, tmp_path: Path):
        """Test handling of permission denied errors."""
        sample_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        
        # Create directory without write permissions (if possible)
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()
        
        output_path = restricted_dir / "output.csv"
        
        # Mock permission error
        with patch('pandas.DataFrame.to_csv', side_effect=PermissionError("Access denied")):
            result = export_processed_data(sample_data, str(output_path))
            
            assert result['status'] == 'error'
            assert 'permission' in result['error_message'].lower()

    def test_disk_space_error(self):
        """Test handling of disk space errors."""
        sample_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        
        # Mock disk space error
        with patch('pandas.DataFrame.to_csv', side_effect=OSError("No space left on device")):
            result = export_processed_data(sample_data, "/tmp/output.csv")
            
            assert result['status'] == 'error'
            assert 'space' in result['error_message'].lower()

    def test_corrupted_data_export(self):
        """Test export with corrupted/invalid data."""
        # Create DataFrame with problematic data
        corrupted_data = pd.DataFrame({
            'Values': [float('inf'), float('-inf'), float('nan'), 1, 2]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            try:
                result = export_processed_data(corrupted_data, tmp_file.name)
                
                # Should handle infinite/NaN values
                assert result['status'] == 'success' or 'warning' in result
                
                # Verify file is readable
                if result['status'] == 'success':
                    reimported = pd.read_csv(tmp_file.name)
                    assert len(reimported) == len(corrupted_data)
                    
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    def test_empty_data_export(self):
        """Test export with empty datasets."""
        empty_data = pd.DataFrame()
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            try:
                result = export_processed_data(empty_data, tmp_file.name)
                
                # Should handle empty data gracefully
                assert result['status'] in ['success', 'warning']
                
                # File should exist and be valid CSV
                if result['status'] == 'success':
                    assert os.path.exists(tmp_file.name)
                    
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)


class TestExportConfiguration:
    """Test export configuration and customization."""

    def test_custom_csv_formatting(self, tmp_path: Path):
        """Test custom CSV formatting options."""
        sample_data = pd.DataFrame({
            'Values': [1.123456789, 2.987654321, 3.555555555],
            'Text': ['A', 'B', 'C']
        })
        
        output_file = tmp_path / "custom_format.csv"
        
        result = export_processed_data(
            sample_data, 
            str(output_file),
            float_precision=4,
            include_index=False
        )
        
        assert result['status'] == 'success'
        
        # Check formatting
        with open(output_file, 'r') as f:
            content = f.read()
            # Should have limited decimal places
            assert '1.1235' in content or '1.123' in content

    def test_export_with_custom_columns(self, tmp_path: Path):
        """Test export with custom column selection."""
        full_data = pd.DataFrame({
            'Well': ['A01', 'A02'],
            'Z_lptA': [0.5, -1.2],
            'Z_ldtD': [-0.8, 1.5],
            'Internal_Use': ['secret', 'data'],
            'Ratio_lptA': [2.0, 2.5]
        })
        
        output_file = tmp_path / "custom_columns.csv"
        
        selected_columns = ['Well', 'Z_lptA', 'Z_ldtD', 'Ratio_lptA']
        
        result = export_processed_data(
            full_data[selected_columns],
            str(output_file)
        )
        
        assert result['status'] == 'success'
        
        # Verify only selected columns exported
        reimported = pd.read_csv(output_file)
        assert set(reimported.columns) == set(selected_columns)
        assert 'Internal_Use' not in reimported.columns

    def test_export_metadata_inclusion(self, tmp_path: Path):
        """Test inclusion of metadata in exports."""
        sample_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        config = {'version': '1.0', 'threshold': 0.3}
        
        output_file = tmp_path / "with_metadata.csv"
        
        # Create metadata
        metadata = create_csv_metadata(sample_data, config)
        
        # Should contain configuration info
        assert metadata['config']['threshold'] == 0.3
        assert metadata['row_count'] == 2
        
        # Metadata should be serializable
        json.dumps(metadata)  # Should not raise exception