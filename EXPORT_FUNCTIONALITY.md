# Export Functionality Documentation

This document provides comprehensive documentation for the bio-hit-finder export functionality, including CSV exports, PDF report generation, and ZIP bundle creation.

## Overview

The export module provides four main capabilities:

1. **CSV Export** - Structured data export in multiple formats
2. **PDF Report Generation** - Professional QC reports with formulas and visualizations
3. **ZIP Bundle Creation** - Self-contained packages with all analysis artifacts
4. **Data Integrity** - Hash verification and complete provenance tracking

## Module Structure

```
export/
├── __init__.py              # Main module exports
├── csv_export.py            # CSV export functionality
├── pdf_generator.py         # PDF report generation
├── bundle.py                # ZIP bundle creation
└── example_usage.py         # Usage examples and demos

templates/
└── report.html              # Jinja2 template for PDF reports
```

## Quick Start

```python
from export import CSVExporter, PDFReportGenerator, BundleExporter

# Initialize exporters with configuration
config = {...}  # Your configuration dictionary
csv_exporter = CSVExporter(config)
pdf_generator = PDFReportGenerator(config=config)
bundle_exporter = BundleExporter(config)

# Export processed plate data
csv_exporter.export_processed_plate(df, "plate_data.csv")
pdf_generator.generate_report(df, "qc_report.pdf", config)
bundle_exporter.create_bundle(df, "analysis_bundle.zip")
```

## CSV Export Functionality

### CSVExporter Class

The `CSVExporter` class provides comprehensive CSV export capabilities with proper Excel formatting and complete provenance information.

#### Key Methods

##### export_processed_plate(df, filename, metadata=None)
Exports a single processed plate with all calculated columns.

```python
# Export single plate
csv_exporter = CSVExporter(config)
csv_exporter.export_processed_plate(
    plate_df, 
    "plate_001_processed.csv",
    metadata={"processing_params": {...}}
)
```

**Output includes:**
- All raw measurements (BG_lptA, BT_lptA, BG_ldtD, BT_ldtD, OD values)
- Calculated ratios (Ratio_lptA, Ratio_ldtD)
- Normalized OD values (OD_WT_norm, OD_tolC_norm, OD_SA_norm)
- Robust Z-scores (Z_lptA, Z_ldtD, Z_Ratio_lptA, Z_Ratio_ldtD)
- B-scores (if calculated)
- Quality flags (Viability_Flag, Edge_Flag)

##### export_combined_dataset(df, filename, metadata=None)
Exports combined multi-plate dataset with PlateID column.

```python
# Export combined dataset
csv_exporter.export_combined_dataset(
    combined_df,
    "combined_dataset.csv",
    metadata=metadata
)
```

##### export_top_hits(df, top_n, filename, score_column=None, metadata=None)
Exports ranked top hits based on maximum absolute Z-scores.

```python
# Export top 50 hits
csv_exporter.export_top_hits(
    df, 
    50, 
    "top_50_hits.csv",
    metadata=metadata
)
```

**Features:**
- Automatic ranking by maximum absolute Z-score
- Custom ranking column support
- Hit_Rank column added
- Complete hit context preserved

##### export_summary_stats(df, filename, metadata=None)
Exports per-plate summary statistics.

```python
# Export summary statistics
csv_exporter.export_summary_stats(
    df,
    "summary_statistics.csv", 
    metadata=metadata
)
```

**Summary includes:**
- Well counts and viability rates
- Statistical summaries (mean, median, std, MAD, min, max) for key metrics
- Quality flag summaries
- Hit counts at different Z-score thresholds

##### export_quality_report(df, filename, metadata=None)
Exports quality control report with key metrics.

#### Column Ordering

All CSV exports use standardized column ordering:
1. Identifiers: PlateID, Well, Row, Col
2. Raw measurements: BG/BT values, OD values
3. Calculated ratios: Ratio_lptA, Ratio_ldtD
4. Normalized values: OD_*_norm
5. Z-scores: Z_*
6. B-scores: B_* (if available)
7. Quality flags: Viability_Flag, Edge_Flag, Control_Type

#### Metadata Headers

All exports include comprehensive metadata headers:
```
# Bio-Hit-Finder Export
# Generated: 2024-01-15 14:30:25
# Software Version: 1.0.0
# Processing Parameters:
#   viability_threshold: 0.3
#   z_score_cutoff: 2.0
#   bscore_enabled: false
# Plate Information:
#   total_plates: 2
#   total_wells: 768
```

## PDF Report Generation

### PDFReportGenerator Class

Creates comprehensive QC reports with embedded formulas, visualizations, and statistical summaries.

#### Key Methods

##### generate_report(df, output_path, config, include_plots=True)
Generates complete PDF QC report.

```python
pdf_generator = PDFReportGenerator(config=config)
pdf_generator.generate_report(
    df,
    "qc_report.pdf", 
    config,
    include_plots=True
)
```

**Report Sections:**
1. **Executive Summary** - Key metrics and processing timestamp
2. **Processing Methodology** - Detailed methodology descriptions
3. **Mathematical Formulas** - Exact formulas with KaTeX rendering:
   - Reporter Ratios: `Ratio_lptA = BG_lptA / BT_lptA`
   - OD Normalization: `OD_WT_norm = OD_WT / median(OD_WT)`
   - Robust Z-score: `Z = (value - median) / (1.4826 × MAD)`
   - Viability Gate: `Viability_Flag = ATP < f × median(ATP)`
4. **Plate-by-Plate Analysis** - Per-plate summaries with quality assessment
5. **Data Visualizations** - Embedded plots (PNG format)
6. **Processing Configuration** - Complete parameter settings
7. **Technical Notes** - Implementation details and caveats

#### Template System

Uses Jinja2 templating with `templates/report.html`:
- Professional layout optimized for WeasyPrint
- Responsive design for A4 page format
- Custom filters for number formatting
- Quality indicators with color coding
- Formula rendering with proper mathematical notation

#### Customization

```python
# Custom configuration
config = {
    'export': {
        'pdf': {
            'include_formulas': True,
            'include_methodology': True,
            'page_format': 'A4',
            'margins': {
                'top': 20, 'bottom': 20, 
                'left': 15, 'right': 15
            }
        }
    }
}
```

### Quick Summary Generation

```python
from export import generate_quick_summary

# Generate lightweight summary without plots
generate_quick_summary(df, "quick_summary.pdf", config)
```

## ZIP Bundle Creation

### BundleExporter Class

Creates self-contained ZIP bundles with complete analysis results and integrity verification.

#### Key Methods

##### create_bundle(df, output_path, include_plots=True, plot_formats=['png', 'html'], progress_callback=None)

```python
def progress_callback(pct):
    print(f"Progress: {pct*100:.1f}%")

bundle_exporter = BundleExporter(config)
bundle_exporter.create_bundle(
    df,
    "analysis_bundle.zip",
    include_plots=True,
    plot_formats=['png', 'html'],
    progress_callback=progress_callback
)
```

#### Bundle Structure

```
analysis_bundle.zip
├── data/
│   ├── plate_001_processed.csv
│   ├── plate_002_processed.csv  
│   ├── combined_dataset.csv
│   ├── top_hits.csv
│   └── summary_statistics.csv
├── reports/
│   └── qc_report.pdf
├── visualizations/
│   ├── z_score_distributions.png
│   ├── ratio_distributions.png
│   ├── scatter_plots.html
│   └── heatmap_plate_001.png
├── metadata/
│   └── config.yaml
└── manifest.json
```

#### Bundle Integrity

##### verify_bundle_integrity(bundle_path)
Verifies bundle integrity using SHA-256 hashes.

```python
verification = bundle_exporter.verify_bundle_integrity("bundle.zip")
print(f"Status: {verification['status']}")
print(f"Verified files: {verification['verified_files']}")
```

##### extract_bundle_info(bundle_path)
Extracts metadata from existing bundles.

```python
info = bundle_exporter.extract_bundle_info("bundle.zip")
print(f"Created: {info['bundle_info']['created_timestamp']}")
print(f"Files: {info['integrity']['total_files']}")
```

#### Manifest Format

```json
{
  "bundle_info": {
    "created_timestamp": "2024-01-15T14:30:25.123456",
    "creator": "Bio-Hit-Finder Export System",
    "version": "1.0.0",
    "description": "Comprehensive analysis results bundle"
  },
  "processing_metadata": {
    "processing_timestamp": "2024-01-15T14:30:25.123456",
    "input_data": {
      "total_wells": 768,
      "total_plates": 2,
      "columns": ["PlateID", "Well", ...]
    },
    "processing_parameters": {
      "viability_threshold": 0.3,
      "z_score_cutoff": 2.0
    }
  },
  "contents": {
    "data/combined_dataset.csv": {
      "description": "Combined dataset from all plates",
      "size_bytes": 145692,
      "hash": "a1b2c3..."
    }
  },
  "integrity": {
    "total_files": 12,
    "hash_algorithm": "SHA-256"
  }
}
```

### Convenience Functions

```python
from export import create_analysis_bundle

# One-line bundle creation
create_analysis_bundle(
    df, 
    "quick_bundle.zip",
    config,
    include_plots=False
)
```

## Configuration Integration

### Export Settings

The export functionality integrates with `config.yaml`:

```yaml
export:
  # Default formats for ZIP bundles
  formats:
    - "csv"
    - "png" 
    - "html"
    - "pdf"
  
  # PDF report settings
  pdf:
    include_formulas: true
    include_methodology: true
    page_format: "A4"
    margins:
      top: 20
      bottom: 20
      left: 15
      right: 15
```

### Metadata Creation

```python
from export import create_export_metadata

metadata = create_export_metadata(
    config,
    processing_info={'demo': True, 'wells': 768},
    software_version="1.0.0"
)
```

## Performance Characteristics

### Targets (as specified in PRD)

- **CSV export**: < 1s for 10 plates (~20,000 rows)
- **PDF generation**: < 5s with embedded plots  
- **ZIP bundle**: < 10s for complete package

### Memory Usage

- Efficient streaming for large datasets
- Temporary file cleanup
- Progress callbacks for UI integration

### Optimization Features

- Column ordering optimization
- Robust statistics using pandas/numpy
- Plotly figure optimization for PDF embedding
- ZIP compression with optimal settings

## Error Handling

### File I/O Operations

- Comprehensive error handling for disk operations
- Automatic directory creation
- File permission validation
- Cleanup on failure

### Data Validation

- Missing column handling
- Data type validation  
- Edge case management (zero MAD, empty plates)
- Graceful degradation

### Progress Reporting

```python
def progress_callback(pct: float):
    """Progress callback function."""
    print(f"Export progress: {pct*100:.1f}%")

# Use with bundle creation
bundle_exporter.create_bundle(
    df, "bundle.zip", 
    progress_callback=progress_callback
)
```

## Integration Examples

### Streamlit Integration

```python
import streamlit as st
from export import CSVExporter, PDFReportGenerator, BundleExporter

def create_download_buttons(df, config):
    """Create download buttons in Streamlit."""
    
    # CSV downloads
    if st.button("Download CSV Data"):
        csv_exporter = CSVExporter(config)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            csv_exporter.export_combined_dataset(df, f.name)
            st.download_button(
                "Download Combined Dataset",
                data=open(f.name, 'rb').read(),
                file_name="combined_dataset.csv",
                mime="text/csv"
            )
    
    # PDF report
    if st.button("Generate PDF Report"):
        pdf_generator = PDFReportGenerator(config=config)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_generator.generate_report(df, f.name, config)
            st.download_button(
                "Download QC Report",
                data=open(f.name, 'rb').read(),
                file_name="qc_report.pdf",
                mime="application/pdf"
            )
    
    # Complete bundle
    if st.button("Create Analysis Bundle"):
        with st.spinner("Creating bundle..."):
            bundle_exporter = BundleExporter(config)
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
                
                progress_bar = st.progress(0)
                def update_progress(pct):
                    progress_bar.progress(pct)
                
                bundle_exporter.create_bundle(
                    df, f.name, 
                    include_plots=True,
                    progress_callback=update_progress
                )
                
                st.download_button(
                    "Download Analysis Bundle",
                    data=open(f.name, 'rb').read(),
                    file_name="analysis_bundle.zip",
                    mime="application/zip"
                )
```

### Command Line Integration

```python
import argparse
from pathlib import Path
import pandas as pd
from export import create_analysis_bundle

def main():
    parser = argparse.ArgumentParser(description='Export processed plate data')
    parser.add_argument('input_file', help='Processed data CSV file')
    parser.add_argument('output_bundle', help='Output bundle path')
    parser.add_argument('--config', help='Configuration YAML file')
    parser.add_argument('--no-plots', action='store_true', help='Exclude plots')
    
    args = parser.parse_args()
    
    # Load data and config
    df = pd.read_csv(args.input_file)
    
    if args.config:
        with open(args.config) as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    # Create bundle
    create_analysis_bundle(
        df, 
        args.output_bundle,
        config,
        include_plots=not args.no_plots
    )
    
    print(f"✓ Created analysis bundle: {args.output_bundle}")

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Common Issues

1. **WeasyPrint Installation**
   ```bash
   # Windows
   pip install weasyprint
   
   # May require GTK+ libraries on Windows
   # See WeasyPrint documentation for details
   ```

2. **Font Issues in PDF**
   - Ensure DejaVu fonts are available
   - Check WeasyPrint font configuration
   - Use fallback fonts if needed

3. **Large Dataset Memory Usage**
   - Process plates individually for very large datasets
   - Use plot_formats=['png'] only for memory efficiency
   - Disable plots for memory-constrained environments

4. **Permission Errors**
   - Ensure output directories are writable
   - Check file locks on existing files
   - Use temporary directories when needed

### Validation

Run the validation script to check setup:

```bash
python validate_export_structure.py
```

### Dependencies

Ensure all required packages are installed:

```bash
pip install -r requirements.txt
```

Required packages for export functionality:
- pandas>=2.0.0
- numpy>=1.24.0  
- plotly>=5.15.0
- jinja2>=3.1.0
- weasyprint>=60.0
- pyyaml>=6.0
- kaleido>=0.2.1 (for plotly image export)

## API Reference

### Complete Method Signatures

```python
class CSVExporter:
    def __init__(self, config: Optional[Dict] = None)
    
    def export_processed_plate(
        self, df: pd.DataFrame, filename: Union[str, Path], 
        metadata: Optional[Dict] = None
    ) -> Path
    
    def export_combined_dataset(
        self, df: pd.DataFrame, filename: Union[str, Path],
        metadata: Optional[Dict] = None  
    ) -> Path
    
    def export_top_hits(
        self, df: pd.DataFrame, top_n: int, filename: Union[str, Path],
        score_column: Optional[str] = None, metadata: Optional[Dict] = None
    ) -> Path
    
    def export_summary_stats(
        self, df: pd.DataFrame, filename: Union[str, Path],
        metadata: Optional[Dict] = None
    ) -> Path

class PDFReportGenerator:
    def __init__(self, templates_dir: Optional[Path] = None, config: Optional[Dict] = None)
    
    def generate_report(
        self, df: pd.DataFrame, output_path: Union[str, Path],
        config: Optional[Dict] = None, include_plots: bool = True
    ) -> Path

class BundleExporter:
    def __init__(self, config: Optional[Dict] = None)
    
    def create_bundle(
        self, df: pd.DataFrame, output_path: Union[str, Path],
        include_plots: bool = True, plot_formats: List[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Path
    
    def verify_bundle_integrity(self, bundle_path: Union[str, Path]) -> Dict[str, Any]
    
    def extract_bundle_info(self, bundle_path: Union[str, Path]) -> Dict[str, Any]
```

For complete usage examples, see `export/example_usage.py`.