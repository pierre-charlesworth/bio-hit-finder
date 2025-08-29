"""ZIP bundle creation for comprehensive data exports.

This module creates self-contained ZIP bundles with complete analysis results,
including CSV data, PDF reports, visualizations, and processing metadata.
"""

import hashlib
import json
import logging
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any
import warnings

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import yaml

from .csv_export import CSVExporter, create_export_metadata
from .pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class BundleExporter:
    """Creates comprehensive ZIP bundles with all analysis artifacts."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize bundle exporter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.csv_exporter = CSVExporter(config)
        self.pdf_generator = PDFReportGenerator(config=config)
        
        # Bundle structure
        self.bundle_structure = {
            'data/': 'Processed data files (CSV)',
            'reports/': 'Generated reports (PDF)',
            'visualizations/': 'Plot files (PNG, SVG, HTML)',
            'metadata/': 'Processing metadata and configuration',
            'manifest.json': 'Bundle contents and integrity information'
        }
        
        logger.info("Initialized bundle exporter")
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of a file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Hexadecimal hash string
        """
        hash_sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _create_manifest(
        self, 
        bundle_contents: Dict[str, Any],
        processing_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create bundle manifest with contents and integrity information.
        
        Args:
            bundle_contents: Dictionary of bundle files and their info
            processing_metadata: Processing metadata
            
        Returns:
            Complete manifest dictionary
        """
        manifest = {
            'bundle_info': {
                'created_timestamp': datetime.now().isoformat(),
                'creator': 'Bio-Hit-Finder Export System',
                'version': '1.0.0',
                'description': 'Comprehensive analysis results bundle'
            },
            'processing_metadata': processing_metadata,
            'structure': self.bundle_structure,
            'contents': bundle_contents,
            'integrity': {
                'total_files': len(bundle_contents),
                'hash_algorithm': 'SHA-256'
            }
        }
        
        return manifest
    
    def _export_visualizations(
        self,
        df: pd.DataFrame,
        output_dir: Path,
        formats: List[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Export visualization plots in multiple formats.
        
        Args:
            df: Processed DataFrame
            output_dir: Output directory for plots
            formats: List of formats to export ('png', 'svg', 'html')
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary of exported plot information
        """
        if formats is None:
            formats = ['png', 'html']
        
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_info = {}
        
        # Import visualization modules dynamically to avoid circular imports
        try:
            from ..visualizations.charts import create_distribution_plots, create_scatter_plots
            from ..visualizations.heatmaps import create_plate_heatmap
        except ImportError as e:
            logger.warning(f"Could not import visualization modules: {e}")
            return plot_info
        
        plot_configs = [
            ('z_score_distributions', lambda: create_distribution_plots(df, metrics=['Z_lptA', 'Z_ldtD'])),
            ('ratio_distributions', lambda: create_distribution_plots(df, metrics=['Ratio_lptA', 'Ratio_ldtD'])),
            ('scatter_plots', lambda: create_scatter_plots(df)),
        ]
        
        # Add heatmaps for each plate
        if 'PlateID' in df.columns:
            for plate_id in df['PlateID'].unique():
                plate_df = df[df['PlateID'] == plate_id]
                plot_configs.append((
                    f'heatmap_{plate_id}',
                    lambda pdf=plate_df: create_plate_heatmap(pdf, metric='Z_lptA')
                ))
        else:
            plot_configs.append(('heatmap_plate', lambda: create_plate_heatmap(df, metric='Z_lptA')))
        
        total_plots = len(plot_configs) * len(formats)
        current_plot = 0
        
        for plot_name, plot_func in plot_configs:
            try:
                fig = plot_func()
                if fig is None:
                    continue
                
                plot_files = {}
                
                for fmt in formats:
                    current_plot += 1
                    if progress_callback:
                        progress_callback(current_plot / total_plots)
                    
                    filename = f"{plot_name}.{fmt}"
                    filepath = output_dir / filename
                    
                    try:
                        if fmt == 'png':
                            pio.write_image(fig, filepath, format='png', width=1200, height=800, scale=2)
                        elif fmt == 'svg':
                            pio.write_image(fig, filepath, format='svg', width=1200, height=800)
                        elif fmt == 'html':
                            pio.write_html(fig, filepath, include_plotlyjs='cdn')
                        
                        # Calculate file info
                        file_size = filepath.stat().st_size
                        file_hash = self._calculate_file_hash(filepath)
                        
                        plot_files[fmt] = {
                            'filename': filename,
                            'size_bytes': file_size,
                            'hash': file_hash
                        }
                        
                        logger.debug(f"Exported {plot_name} as {fmt}: {filepath}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to export {plot_name} as {fmt}: {e}")
                
                if plot_files:
                    plot_info[plot_name] = plot_files
                    
            except Exception as e:
                logger.warning(f"Failed to create plot {plot_name}: {e}")
        
        logger.info(f"Exported {len(plot_info)} visualization plots")
        return plot_info
    
    def create_bundle(
        self,
        df: pd.DataFrame,
        output_path: Union[str, Path],
        include_plots: bool = True,
        plot_formats: List[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Path:
        """Create comprehensive export bundle.
        
        Args:
            df: Processed DataFrame
            output_path: Output path for ZIP bundle
            include_plots: Whether to include visualization plots
            plot_formats: List of plot formats to include
            progress_callback: Optional progress callback function
            
        Returns:
            Path to created bundle
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if plot_formats is None:
            plot_formats = self.config.get('export', {}).get('formats', ['png', 'html'])
        
        logger.info(f"Creating export bundle: {output_path}")
        
        # Create temporary directory for bundle contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bundle_contents = {}
            
            # Progress tracking
            total_steps = 6 + (2 if include_plots else 0)
            current_step = 0
            
            def update_progress():
                nonlocal current_step
                current_step += 1
                if progress_callback:
                    progress_callback(current_step / total_steps)
            
            # 1. Create directory structure
            data_dir = temp_path / 'data'
            reports_dir = temp_path / 'reports'
            viz_dir = temp_path / 'visualizations'
            metadata_dir = temp_path / 'metadata'
            
            for directory in [data_dir, reports_dir, viz_dir, metadata_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            update_progress()
            
            # 2. Export CSV data files
            logger.info("Exporting CSV data files...")
            
            metadata = create_export_metadata(self.config, software_version="1.0.0")
            
            # Per-plate data
            if 'PlateID' in df.columns:
                for plate_id in df['PlateID'].unique():
                    plate_df = df[df['PlateID'] == plate_id]
                    filename = f"plate_{plate_id}_processed.csv"
                    filepath = self.csv_exporter.export_processed_plate(
                        plate_df, data_dir / filename, metadata
                    )
                    
                    bundle_contents[f"data/{filename}"] = {
                        'description': f'Processed data for plate {plate_id}',
                        'size_bytes': filepath.stat().st_size,
                        'hash': self._calculate_file_hash(filepath)
                    }
            
            # Combined dataset
            combined_file = self.csv_exporter.export_combined_dataset(
                df, data_dir / 'combined_dataset.csv', metadata
            )
            bundle_contents['data/combined_dataset.csv'] = {
                'description': 'Combined dataset from all plates',
                'size_bytes': combined_file.stat().st_size,
                'hash': self._calculate_file_hash(combined_file)
            }
            
            update_progress()
            
            # 3. Export top hits
            logger.info("Exporting top hits...")
            top_n = self.config.get('processing', {}).get('top_n_hits', 50)
            hits_file = self.csv_exporter.export_top_hits(
                df, top_n, data_dir / 'top_hits.csv', metadata=metadata
            )
            bundle_contents['data/top_hits.csv'] = {
                'description': f'Top {top_n} hits ranked by Z-score',
                'size_bytes': hits_file.stat().st_size,
                'hash': self._calculate_file_hash(hits_file)
            }
            
            update_progress()
            
            # 4. Export summary statistics
            logger.info("Exporting summary statistics...")
            summary_file = self.csv_exporter.export_summary_stats(
                df, data_dir / 'summary_statistics.csv', metadata
            )
            bundle_contents['data/summary_statistics.csv'] = {
                'description': 'Per-plate summary statistics',
                'size_bytes': summary_file.stat().st_size,
                'hash': self._calculate_file_hash(summary_file)
            }
            
            update_progress()
            
            # 5. Generate PDF report
            logger.info("Generating PDF report...")
            try:
                pdf_file = self.pdf_generator.generate_report(
                    df, reports_dir / 'qc_report.pdf', self.config, include_plots=include_plots
                )
                bundle_contents['reports/qc_report.pdf'] = {
                    'description': 'Comprehensive QC report with formulas and analysis',
                    'size_bytes': pdf_file.stat().st_size,
                    'hash': self._calculate_file_hash(pdf_file)
                }
            except Exception as e:
                logger.warning(f"Failed to generate PDF report: {e}")
            
            update_progress()
            
            # 6. Export visualizations (if requested)
            if include_plots:
                logger.info("Exporting visualizations...")
                
                def viz_progress(pct):
                    if progress_callback:
                        progress_callback((current_step - 1 + pct) / total_steps)
                
                plot_info = self._export_visualizations(
                    df, viz_dir, plot_formats, viz_progress
                )
                
                # Add plot info to bundle contents
                for plot_name, formats_info in plot_info.items():
                    for fmt, file_info in formats_info.items():
                        bundle_contents[f"visualizations/{file_info['filename']}"] = {
                            'description': f'{plot_name} plot in {fmt} format',
                            'size_bytes': file_info['size_bytes'],
                            'hash': file_info['hash']
                        }
                
                update_progress()
            
            # 7. Save metadata and configuration
            logger.info("Saving metadata...")
            
            # Configuration snapshot
            config_file = metadata_dir / 'config.yaml'
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            bundle_contents['metadata/config.yaml'] = {
                'description': 'Configuration snapshot used for processing',
                'size_bytes': config_file.stat().st_size,
                'hash': self._calculate_file_hash(config_file)
            }
            
            # Processing metadata
            processing_metadata = {
                'processing_timestamp': datetime.now().isoformat(),
                'input_data': {
                    'total_wells': len(df),
                    'total_plates': df['PlateID'].nunique() if 'PlateID' in df.columns else 1,
                    'columns': list(df.columns)
                },
                'processing_parameters': metadata.get('processing_params', {}),
                'software_version': metadata.get('version', '1.0.0')
            }
            
            # Create manifest
            manifest = self._create_manifest(bundle_contents, processing_metadata)
            
            manifest_file = temp_path / 'manifest.json'
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            bundle_contents['manifest.json'] = {
                'description': 'Bundle manifest with integrity information',
                'size_bytes': manifest_file.stat().st_size,
                'hash': self._calculate_file_hash(manifest_file)
            }
            
            update_progress()
            
            # 8. Create ZIP bundle
            logger.info("Creating ZIP bundle...")
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                for root, dirs, files in os.walk(temp_path):
                    for file in files:
                        file_path = Path(root) / file
                        arc_path = file_path.relative_to(temp_path)
                        zipf.write(file_path, arc_path)
            
            update_progress()
        
        # Verify bundle was created
        if output_path.exists():
            bundle_size = output_path.stat().st_size
            logger.info(f"Successfully created bundle: {output_path} ({bundle_size:,} bytes)")
            logger.info(f"Bundle contains {len(bundle_contents)} files")
            
            return output_path
        else:
            raise RuntimeError(f"Failed to create bundle at {output_path}")
    
    def extract_bundle_info(self, bundle_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract information from an existing bundle.
        
        Args:
            bundle_path: Path to ZIP bundle
            
        Returns:
            Bundle information dictionary
        """
        bundle_path = Path(bundle_path)
        
        if not bundle_path.exists():
            raise FileNotFoundError(f"Bundle not found: {bundle_path}")
        
        try:
            with zipfile.ZipFile(bundle_path, 'r') as zipf:
                # Try to read manifest
                if 'manifest.json' in zipf.namelist():
                    with zipf.open('manifest.json') as f:
                        manifest = json.load(f)
                    return manifest
                else:
                    # Basic info without manifest
                    file_list = zipf.namelist()
                    return {
                        'bundle_info': {
                            'created_timestamp': 'unknown',
                            'version': 'unknown'
                        },
                        'contents': {f: {'description': 'file'} for f in file_list},
                        'integrity': {'total_files': len(file_list)}
                    }
        except Exception as e:
            logger.error(f"Failed to read bundle {bundle_path}: {e}")
            raise
    
    def verify_bundle_integrity(self, bundle_path: Union[str, Path]) -> Dict[str, Any]:
        """Verify the integrity of a bundle using manifest hashes.
        
        Args:
            bundle_path: Path to ZIP bundle
            
        Returns:
            Verification results dictionary
        """
        bundle_path = Path(bundle_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract bundle
            with zipfile.ZipFile(bundle_path, 'r') as zipf:
                zipf.extractall(temp_path)
            
            # Load manifest
            manifest_file = temp_path / 'manifest.json'
            if not manifest_file.exists():
                return {'status': 'error', 'message': 'No manifest found'}
            
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Verify each file
            verification_results = {
                'status': 'success',
                'verified_files': 0,
                'failed_files': 0,
                'missing_files': 0,
                'details': {}
            }
            
            for file_path, file_info in manifest.get('contents', {}).items():
                full_path = temp_path / file_path
                
                if not full_path.exists():
                    verification_results['missing_files'] += 1
                    verification_results['details'][file_path] = 'missing'
                    continue
                
                # Calculate hash
                actual_hash = self._calculate_file_hash(full_path)
                expected_hash = file_info.get('hash')
                
                if actual_hash == expected_hash:
                    verification_results['verified_files'] += 1
                    verification_results['details'][file_path] = 'verified'
                else:
                    verification_results['failed_files'] += 1
                    verification_results['details'][file_path] = 'hash_mismatch'
            
            # Update overall status
            if verification_results['failed_files'] > 0 or verification_results['missing_files'] > 0:
                verification_results['status'] = 'failed'
            
            return verification_results


# Import os for walk function
import os


def create_analysis_bundle(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    config: Optional[Dict] = None,
    include_plots: bool = True,
    progress_callback: Optional[Callable] = None
) -> Path:
    """Convenience function to create a complete analysis bundle.
    
    Args:
        df: Processed DataFrame
        output_path: Output path for bundle
        config: Optional configuration
        include_plots: Whether to include plots
        progress_callback: Optional progress callback
        
    Returns:
        Path to created bundle
    """
    exporter = BundleExporter(config)
    return exporter.create_bundle(
        df, output_path, include_plots=include_plots, progress_callback=progress_callback
    )