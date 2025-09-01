"""Example usage of the export functionality.

This module demonstrates how to use all the export capabilities
of the bio-hit-finder platform for comprehensive data export.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import numpy as np

from . import (
    CSVExporter,
    PDFReportGenerator,
    BundleExporter,
    create_export_metadata,
    generate_quick_summary,
    create_analysis_bundle
)

logger = logging.getLogger(__name__)


def demo_csv_exports(df: pd.DataFrame, output_dir: Path, config: Dict) -> None:
    """Demonstrate CSV export functionality.
    
    Args:
        df: Processed DataFrame
        output_dir: Directory for outputs
        config: Configuration dictionary
    """
    print("=== CSV Export Demo ===")
    
    # Initialize CSV exporter
    csv_exporter = CSVExporter(config)
    
    # Create export metadata
    metadata = create_export_metadata(
        config, 
        processing_info={'demo': True, 'wells': len(df)},
        software_version="1.0.0"
    )
    
    # Export processed plate data
    if 'PlateID' in df.columns:
        # Export each plate separately
        for plate_id in df['PlateID'].unique():
            plate_df = df[df['PlateID'] == plate_id]
            output_file = output_dir / f"plate_{plate_id}_processed.csv"
            csv_exporter.export_processed_plate(plate_df, output_file, metadata)
            print(f"✓ Exported plate {plate_id} to {output_file}")
    
    # Export combined dataset
    combined_file = output_dir / "combined_dataset.csv"
    csv_exporter.export_combined_dataset(df, combined_file, metadata)
    print(f"✓ Exported combined dataset to {combined_file}")
    
    # Export top hits
    top_hits_file = output_dir / "top_50_hits.csv"
    csv_exporter.export_top_hits(df, 50, top_hits_file, metadata=metadata)
    print(f"✓ Exported top hits to {top_hits_file}")
    
    # Export summary statistics
    summary_file = output_dir / "summary_statistics.csv"
    csv_exporter.export_summary_stats(df, summary_file, metadata)
    print(f"✓ Exported summary statistics to {summary_file}")
    
    # Export quality report
    qc_file = output_dir / "qc_report.csv"
    csv_exporter.export_quality_report(df, qc_file, metadata)
    print(f"✓ Exported QC report to {qc_file}")


def demo_pdf_generation(df: pd.DataFrame, output_dir: Path, config: Dict) -> None:
    """Demonstrate PDF report generation.
    
    Args:
        df: Processed DataFrame
        output_dir: Directory for outputs
        config: Configuration dictionary
    """
    print("\n=== PDF Report Demo ===")
    
    # Initialize PDF generator
    pdf_generator = PDFReportGenerator(config=config)
    
    # Generate full report with plots
    full_report = output_dir / "full_qc_report.pdf"
    try:
        pdf_generator.generate_report(df, full_report, config, include_plots=True)
        print(f"✓ Generated full report with plots: {full_report}")
    except Exception as e:
        print(f"✗ Failed to generate full report: {e}")
    
    # Generate quick summary without plots
    quick_report = output_dir / "quick_summary.pdf"
    try:
        generate_quick_summary(df, quick_report, config)
        print(f"✓ Generated quick summary: {quick_report}")
    except Exception as e:
        print(f"✗ Failed to generate quick summary: {e}")


def demo_bundle_creation(df: pd.DataFrame, output_dir: Path, config: Dict) -> None:
    """Demonstrate ZIP bundle creation.
    
    Args:
        df: Processed DataFrame
        output_dir: Directory for outputs
        config: Configuration dictionary
    """
    print("\n=== Bundle Creation Demo ===")
    
    # Initialize bundle exporter
    bundle_exporter = BundleExporter(config)
    
    # Create comprehensive bundle
    bundle_path = output_dir / "analysis_bundle.zip"
    
    def progress_callback(pct: float):
        print(f"Bundle creation progress: {pct*100:.1f}%")
    
    try:
        bundle_exporter.create_bundle(
            df, 
            bundle_path, 
            include_plots=True,
            plot_formats=['png', 'html'],
            progress_callback=progress_callback
        )
        print(f"✓ Created comprehensive bundle: {bundle_path}")
        
        # Verify bundle integrity
        verification = bundle_exporter.verify_bundle_integrity(bundle_path)
        print(f"Bundle verification: {verification['status']}")
        print(f"Verified files: {verification['verified_files']}")
        
        # Extract bundle info
        bundle_info = bundle_exporter.extract_bundle_info(bundle_path)
        print(f"Bundle contains {bundle_info['integrity']['total_files']} files")
        
    except Exception as e:
        print(f"✗ Failed to create bundle: {e}")
    
    # Alternative: Use convenience function
    convenience_bundle = output_dir / "quick_bundle.zip"
    try:
        create_analysis_bundle(df, convenience_bundle, config, include_plots=False)
        print(f"✓ Created quick bundle using convenience function: {convenience_bundle}")
    except Exception as e:
        print(f"✗ Failed to create quick bundle: {e}")


def create_sample_data() -> pd.DataFrame:
    """Create sample processed data for demonstration.
    
    Returns:
        Sample DataFrame with processed plate data
    """
    np.random.seed(42)
    
    # Generate sample data for 2 plates, 384 wells each
    plates = ['Plate_001', 'Plate_002']
    wells_per_plate = 384
    
    data = []
    
    for plate_id in plates:
        for well_idx in range(wells_per_plate):
            # Create well position (96-well format for simplicity)
            row = chr(ord('A') + (well_idx // 24))
            col = (well_idx % 24) + 1
            
            # Generate realistic measurement data
            bg_lpta = np.random.lognormal(3.0, 0.5)
            bt_lpta = np.random.lognormal(4.0, 0.3)
            bg_ldtd = np.random.lognormal(2.8, 0.6)
            bt_ldtd = np.random.lognormal(3.8, 0.4)
            
            # Calculate ratios
            ratio_lpta = bg_lpta / bt_lpta
            ratio_ldtd = bg_ldtd / bt_ldtd
            
            # Add some hits (outliers)
            if np.random.random() < 0.05:  # 5% hits
                ratio_lpta *= np.random.choice([0.3, 3.0])  # Strong hits
            if np.random.random() < 0.03:  # 3% hits
                ratio_ldtd *= np.random.choice([0.2, 4.0])
            
            # OD measurements
            od_wt = np.random.lognormal(0.5, 0.2)
            od_tolc = np.random.lognormal(0.4, 0.3)
            od_sa = np.random.lognormal(0.6, 0.25)
            
            data.append({
                'PlateID': plate_id,
                'Well': f"{row}{col:02d}",
                'Row': row,
                'Col': col,
                'BG_lptA': bg_lpta,
                'BT_lptA': bt_lpta,
                'BG_ldtD': bg_ldtd,
                'BT_ldtD': bt_ldtd,
                'Ratio_lptA': ratio_lpta,
                'Ratio_ldtD': ratio_ldtd,
                'OD_WT': od_wt,
                'OD_tolC': od_tolc,
                'OD_SA': od_sa
            })
    
    df = pd.DataFrame(data)
    
    # Calculate normalized OD values
    for plate_id in plates:
        plate_mask = df['PlateID'] == plate_id
        for od_col in ['OD_WT', 'OD_tolC', 'OD_SA']:
            norm_col = od_col + '_norm'
            plate_median = df.loc[plate_mask, od_col].median()
            df.loc[plate_mask, norm_col] = df.loc[plate_mask, od_col] / plate_median
    
    # Calculate Z-scores using robust statistics
    for plate_id in plates:
        plate_mask = df['PlateID'] == plate_id
        
        for col in ['Ratio_lptA', 'Ratio_ldtD', 'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm']:
            z_col = 'Z_' + col.replace('_norm', '')
            values = df.loc[plate_mask, col]
            median_val = values.median()
            mad_val = np.median(np.abs(values - median_val))
            
            # Avoid division by zero
            if mad_val > 0:
                df.loc[plate_mask, z_col] = (values - median_val) / (1.4826 * mad_val)
            else:
                df.loc[plate_mask, z_col] = 0.0
    
    # Add quality flags
    for plate_id in plates:
        plate_mask = df['PlateID'] == plate_id
        
        # Viability flag based on BT_lptA (ATP proxy)
        atp_threshold = df.loc[plate_mask, 'BT_lptA'].median() * 0.3
        df.loc[plate_mask, 'Viability_Flag'] = df.loc[plate_mask, 'BT_lptA'] < atp_threshold
        
        # Simple edge flag (first/last rows and columns)
        edge_wells = (df.loc[plate_mask, 'Row'].isin(['A', 'P']) | 
                     df.loc[plate_mask, 'Col'].isin([1, 24]))
        df.loc[plate_mask, 'Edge_Flag'] = edge_wells
    
    return df


def run_full_export_demo():
    """Run complete export functionality demonstration."""
    print("Bio-Hit-Finder Export Functionality Demo")
    print("=" * 50)
    
    # Create sample configuration
    config = {
        'processing': {
            'viability_threshold': 0.3,
            'z_score_cutoff': 2.0,
            'top_n_hits': 50
        },
        'bscore': {
            'enabled': False,
            'max_iterations': 10,
            'tolerance': 1e-6
        },
        'export': {
            'formats': ['csv', 'png', 'html', 'pdf'],
            'pdf': {
                'include_formulas': True,
                'include_methodology': True,
                'page_format': 'A4',
                'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
            }
        },
        'edge_warning': {
            'metric': 'Z_lptA',
            'min_group_wells': 16
        }
    }
    
    # Create sample data
    print("Creating sample processed data...")
    df = create_sample_data()
    print(f"Generated {len(df)} wells from {df['PlateID'].nunique()} plates")
    
    # Create output directory
    output_dir = Path("demo_exports")
    output_dir.mkdir(exist_ok=True)
    
    # Run demonstrations
    try:
        demo_csv_exports(df, output_dir, config)
        demo_pdf_generation(df, output_dir, config)
        demo_bundle_creation(df, output_dir, config)
        
        print(f"\n✓ Demo completed successfully!")
        print(f"All outputs saved to: {output_dir.absolute()}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"✗ Demo failed: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demonstration
    run_full_export_demo()