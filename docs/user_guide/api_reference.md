# API Reference Guide

This guide provides comprehensive documentation for programmatic usage of Bio Hit Finder components. Use this when you need to integrate Bio Hit Finder into custom workflows or perform batch analysis.

## Table of Contents

1. [Installation for API Usage](#installation-for-api-usage)
2. [Core Components](#core-components)
3. [Data Processing Pipeline](#data-processing-pipeline)
4. [Statistical Analysis](#statistical-analysis)
5. [Quality Control](#quality-control)
6. [Visualization](#visualization)
7. [Export Functions](#export-functions)
8. [Example Workflows](#example-workflows)

## Installation for API Usage

### Basic Installation

```python
# Install with all dependencies
pip install bio-hit-finder[all]

# Or minimal installation
pip install bio-hit-finder
```

### Development Installation

```bash
git clone https://github.com/bio-hit-finder/bio-hit-finder.git
cd bio-hit-finder
pip install -e ".[dev]"
```

### Import Statement

```python
import bio_hit_finder as bhf
from bio_hit_finder import (
    PlateProcessor,
    EdgeEffectDetector,
    BScoreProcessor,
    create_histogram,
    create_heatmap
)
```

## Core Components

### PlateProcessor

Main class for data processing and analysis.

```python
class PlateProcessor:
    """Main processor for plate-based screening data."""
    
    def __init__(
        self,
        viability_threshold: float = 0.3,
        z_threshold: float = 2.0,
        backend: str = 'pandas',
        n_jobs: int = 1,
        low_memory: bool = False
    ):
        """
        Initialize plate processor.
        
        Parameters:
        -----------
        viability_threshold : float, default=0.3
            Minimum relative viability (BT/median(BT))
        z_threshold : float, default=2.0
            Z-score threshold for hit calling
        backend : str, default='pandas'
            Data processing backend ('pandas' or 'polars')
        n_jobs : int, default=1
            Number of parallel jobs (-1 for all cores)
        low_memory : bool, default=False
            Enable memory optimization for large datasets
        """
```

#### Methods

##### process_dataframe()

```python
def process_dataframe(
    self, 
    df: pd.DataFrame,
    plate_id_col: str = 'PlateID',
    well_col: str = 'Well'
) -> pd.DataFrame:
    """
    Process a DataFrame containing plate data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data with required columns
    plate_id_col : str, default='PlateID'
        Column name for plate identifiers
    well_col : str, default='Well'  
        Column name for well positions
        
    Returns:
    --------
    pd.DataFrame
        Processed data with calculated metrics
        
    Raises:
    -------
    PlateProcessingError
        If required columns missing or data validation fails
        
    Examples:
    ---------
    >>> processor = PlateProcessor()
    >>> results = processor.process_dataframe(raw_data)
    >>> print(results.columns.tolist())
    ['PlateID', 'Well', 'BG_lptA', 'BT_lptA', ..., 'Ratio_lptA', 'Z_lptA', ...]
    """
```

##### process_file()

```python
def process_file(
    self,
    file_path: str,
    sheet_name: str = None
) -> pd.DataFrame:
    """
    Process data from CSV or Excel file.
    
    Parameters:
    -----------
    file_path : str
        Path to input file (.csv or .xlsx)
    sheet_name : str, optional
        Excel sheet name (if None, uses first sheet)
        
    Returns:
    --------
    pd.DataFrame
        Processed data with calculated metrics
        
    Examples:
    ---------
    >>> processor = PlateProcessor()
    >>> results = processor.process_file('data/plate001.csv')
    >>> hits = results[results['Z_lptA'].abs() > 2.0]
    """
```

##### calculate_summary_statistics()

```python
def calculate_summary_statistics(
    self,
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Calculate summary statistics for processed data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Processed plate data
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing summary statistics
        
    Examples:
    ---------
    >>> stats = processor.calculate_summary_statistics(results)
    >>> print(f"Hit rate: {stats['hit_rate']:.1%}")
    >>> print(f"CV ratio_lptA: {stats['cv_ratio_lptA']:.1%}")
    """
```

### Core Calculation Functions

#### calculate_reporter_ratios()

```python
def calculate_reporter_ratios(
    df: pd.DataFrame,
    bg_cols: List[str] = ['BG_lptA', 'BG_ldtD'],
    bt_cols: List[str] = ['BT_lptA', 'BT_ldtD']
) -> pd.DataFrame:
    """
    Calculate reporter ratios (BG/BT) for each target.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data
    bg_cols : List[str]
        BetaGlo column names
    bt_cols : List[str] 
        BacTiter column names
        
    Returns:
    --------
    pd.DataFrame
        Data with added ratio columns
        
    Examples:
    ---------
    >>> df_with_ratios = calculate_reporter_ratios(raw_data)
    >>> print(df_with_ratios[['Ratio_lptA', 'Ratio_ldtD']].head())
    """
```

#### calculate_robust_zscore()

```python
def calculate_robust_zscore(
    values: np.ndarray,
    center: str = 'median',
    scale: str = 'mad'
) -> np.ndarray:
    """
    Calculate robust Z-scores using median and MAD.
    
    Parameters:
    -----------
    values : np.ndarray
        Input values
    center : str, default='median'
        Centering method ('median' or 'mean')
    scale : str, default='mad' 
        Scaling method ('mad' or 'std')
        
    Returns:
    --------
    np.ndarray
        Z-scores
        
    Examples:
    ---------
    >>> z_scores = calculate_robust_zscore(df['Ratio_lptA'].values)
    >>> hits = np.abs(z_scores) > 2.0
    """
```

#### apply_viability_gate()

```python
def apply_viability_gate(
    df: pd.DataFrame,
    bt_cols: List[str] = ['BT_lptA', 'BT_ldtD'],
    threshold: float = 0.3,
    method: str = 'plate_median'
) -> pd.DataFrame:
    """
    Apply viability gating to filter low-viability wells.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data
    bt_cols : List[str]
        BacTiter column names  
    threshold : float, default=0.3
        Minimum relative viability
    method : str, default='plate_median'
        Reference calculation method
        
    Returns:
    --------
    pd.DataFrame
        Data with viability gate columns added
        
    Examples:
    ---------
    >>> gated_data = apply_viability_gate(processed_data)
    >>> viable_hits = gated_data[
    ...     (gated_data['Z_lptA'].abs() > 2.0) &
    ...     (gated_data['Viability_Gate_lptA'] == True)
    ... ]
    """
```

## Statistical Analysis

### BScoreProcessor

Handles B-score calculation for spatial bias correction.

```python
class BScoreProcessor:
    """B-score calculation for spatial bias correction."""
    
    def __init__(
        self,
        max_iter: int = 100,
        tolerance: float = 1e-6,
        min_wells_per_row: int = 3,
        min_wells_per_col: int = 3
    ):
        """
        Initialize B-score processor.
        
        Parameters:
        -----------
        max_iter : int, default=100
            Maximum iterations for median polish
        tolerance : float, default=1e-6
            Convergence tolerance
        min_wells_per_row : int, default=3
            Minimum valid wells per row
        min_wells_per_col : int, default=3
            Minimum valid wells per column
        """
```

#### Methods

##### calculate_bscores()

```python
def calculate_bscores(
    self,
    df: pd.DataFrame,
    value_cols: List[str] = None,
    row_col: str = 'Row',
    col_col: str = 'Col'
) -> pd.DataFrame:
    """
    Calculate B-scores using median polish algorithm.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data with spatial layout
    value_cols : List[str], optional
        Columns to process (default: ratio columns)  
    row_col : str, default='Row'
        Row identifier column
    col_col : str, default='Col'
        Column identifier column
        
    Returns:
    --------
    pd.DataFrame
        Data with B-score columns added
        
    Examples:
    ---------
    >>> bscore_processor = BScoreProcessor()
    >>> corrected_data = bscore_processor.calculate_bscores(plate_data)
    >>> print(corrected_data[['B_lptA', 'B_ldtD']].head())
    """
```

## Quality Control

### EdgeEffectDetector

Detects and quantifies spatial artifacts in plate data.

```python
class EdgeEffectDetector:
    """Detector for edge effects and spatial artifacts."""
    
    def __init__(
        self,
        edge_definition: str = 'outer',
        min_edge_wells: int = 16
    ):
        """
        Initialize edge effect detector.
        
        Parameters:
        -----------
        edge_definition : str, default='outer'
            How to define edge wells ('outer', 'corner', or 'custom')
        min_edge_wells : int, default=16
            Minimum number of edge wells required
        """
```

#### Methods

##### analyze_edge_effects()

```python
def analyze_edge_effects(
    self,
    df: pd.DataFrame,
    value_cols: List[str] = None
) -> Dict[str, Any]:
    """
    Analyze edge effects in plate data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Plate data with Row/Col information
    value_cols : List[str], optional
        Columns to analyze (default: ratio columns)
        
    Returns:
    --------
    Dict[str, Any]
        Edge effect analysis results
        
    Examples:
    ---------
    >>> detector = EdgeEffectDetector()
    >>> edge_analysis = detector.analyze_edge_effects(plate_data)
    >>> print(f"Edge score: {edge_analysis['edge_score']:.2f}")
    >>> print(f"Warning level: {edge_analysis['warning_level']}")
    """
```

##### get_edge_wells()

```python
def get_edge_wells(
    self,
    df: pd.DataFrame,
    n_rows: int = 8,
    n_cols: int = 12
) -> List[str]:
    """
    Identify edge wells based on plate layout.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Plate data
    n_rows : int, default=8
        Number of plate rows
    n_cols : int, default=12
        Number of plate columns
        
    Returns:
    --------
    List[str]
        List of edge well identifiers
        
    Examples:
    ---------
    >>> edge_wells = detector.get_edge_wells(plate_data)
    >>> print(f"Edge wells: {edge_wells[:5]}...")  # A01, A02, A03...
    """
```

## Visualization

### Chart Functions

#### create_histogram()

```python
def create_histogram(
    df: pd.DataFrame,
    column: str,
    title: str = None,
    bins: int = 30,
    color: str = 'blue',
    show_stats: bool = True
) -> go.Figure:
    """
    Create histogram with optional statistics overlay.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Data to plot
    column : str
        Column name to histogram
    title : str, optional
        Plot title
    bins : int, default=30
        Number of histogram bins
    color : str, default='blue'
        Histogram color
    show_stats : bool, default=True
        Whether to show mean/median lines
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive histogram
        
    Examples:
    ---------
    >>> fig = create_histogram(results, 'Ratio_lptA', title='lptA Ratios')
    >>> fig.show()  # Display in notebook
    >>> fig.write_html('histogram.html')  # Save to file
    """
```

#### create_scatter_plot()

```python
def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str = None,
    size_col: str = None,
    title: str = None,
    hover_data: List[str] = None
) -> go.Figure:
    """
    Create interactive scatter plot.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Data to plot
    x_col : str
        X-axis column name
    y_col : str  
        Y-axis column name
    color_col : str, optional
        Column for color coding
    size_col : str, optional
        Column for point sizing
    title : str, optional
        Plot title
    hover_data : List[str], optional
        Additional columns for hover info
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive scatter plot
        
    Examples:
    ---------
    >>> fig = create_scatter_plot(
    ...     results, 
    ...     'Z_lptA', 
    ...     'Z_ldtD',
    ...     color_col='Hit_Status',
    ...     hover_data=['Well', 'Compound_ID']
    ... )
    >>> fig.show()
    """
```

#### create_plate_heatmap()

```python
def create_plate_heatmap(
    df: pd.DataFrame,
    value_col: str,
    row_col: str = 'Row',
    col_col: str = 'Col',
    title: str = None,
    colorscale: str = 'RdBu_r',
    show_values: bool = False
) -> go.Figure:
    """
    Create plate layout heatmap.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Plate data with positional information
    value_col : str
        Column to visualize as heatmap
    row_col : str, default='Row'
        Row position column
    col_col : str, default='Col' 
        Column position column
    title : str, optional
        Plot title
    colorscale : str, default='RdBu_r'
        Color scale name
    show_values : bool, default=False
        Whether to show values on heatmap
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plate heatmap
        
    Examples:
    ---------
    >>> fig = create_plate_heatmap(
    ...     results, 
    ...     'Z_lptA',
    ...     title='lptA Z-Scores by Well Position'
    ... )
    >>> fig.show()
    """
```

## Export Functions

### Data Export

#### export_results()

```python
def export_results(
    df: pd.DataFrame,
    output_path: str,
    format: str = 'csv',
    include_metadata: bool = True
) -> None:
    """
    Export processed results to file.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Results to export
    output_path : str
        Output file path
    format : str, default='csv'
        Export format ('csv', 'excel', 'parquet')
    include_metadata : bool, default=True
        Whether to include analysis metadata
        
    Examples:
    ---------
    >>> export_results(results, 'output/analysis_results.csv')
    >>> export_results(hits_only, 'output/hits.xlsx', format='excel')
    """
```

#### export_hit_list()

```python
def export_hit_list(
    df: pd.DataFrame,
    output_path: str,
    z_threshold: float = 2.0,
    include_borderline: bool = True,
    sort_by: str = 'max_z_score'
) -> None:
    """
    Export ranked hit list.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Processed results
    output_path : str
        Output file path
    z_threshold : float, default=2.0
        Minimum |Z-score| for hits
    include_borderline : bool, default=True
        Include borderline hits (1.5 < |Z| < threshold)
    sort_by : str, default='max_z_score'
        Sorting criteria
        
    Examples:
    ---------
    >>> export_hit_list(
    ...     results, 
    ...     'hits.csv', 
    ...     z_threshold=2.5,
    ...     sort_by='compound_id'
    ... )
    """
```

### Report Generation

#### generate_pdf_report()

```python
def generate_pdf_report(
    df: pd.DataFrame,
    output_path: str,
    include_plots: bool = True,
    template: str = 'standard'
) -> None:
    """
    Generate comprehensive PDF report.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Analysis results
    output_path : str
        Output PDF path
    include_plots : bool, default=True
        Whether to include visualizations
    template : str, default='standard'
        Report template ('standard', 'minimal', 'detailed')
        
    Examples:
    ---------
    >>> generate_pdf_report(
    ...     results, 
    ...     'analysis_report.pdf',
    ...     template='detailed'
    ... )
    """
```

## Example Workflows

### Basic Analysis Pipeline

```python
import pandas as pd
from bio_hit_finder import PlateProcessor, EdgeEffectDetector

# Initialize processor
processor = PlateProcessor(
    viability_threshold=0.3,
    z_threshold=2.0
)

# Load and process data
raw_data = pd.read_csv('plate_data.csv')
results = processor.process_dataframe(raw_data)

# Calculate summary statistics
summary = processor.calculate_summary_statistics(results)
print(f"Hit rate: {summary['hit_rate']:.1%}")

# Identify hits
hits = results[
    (results['Z_lptA'].abs() > 2.0) | 
    (results['Z_ldtD'].abs() > 2.0)
]
print(f"Found {len(hits)} potential hits")

# Export results
results.to_csv('processed_results.csv', index=False)
hits.to_csv('hit_list.csv', index=False)
```

### Quality Control Workflow

```python
from bio_hit_finder import EdgeEffectDetector, BScoreProcessor

# Check for edge effects
detector = EdgeEffectDetector()
edge_analysis = detector.analyze_edge_effects(results)

print(f"Edge effect score: {edge_analysis['edge_score']:.2f}")
print(f"Warning level: {edge_analysis['warning_level']}")

# Apply B-score correction if needed
if edge_analysis['edge_score'] > 0.4:
    print("Applying B-score correction...")
    bscore_processor = BScoreProcessor()
    corrected_results = bscore_processor.calculate_bscores(results)
    
    # Use B-scores for hit calling
    b_score_hits = corrected_results[
        (corrected_results['B_lptA'].abs() > 2.0) | 
        (corrected_results['B_ldtD'].abs() > 2.0)
    ]
    print(f"B-score hits: {len(b_score_hits)}")
```

### Multi-Plate Analysis

```python
import glob
from pathlib import Path

# Process multiple plates
plate_files = glob.glob('data/plate_*.csv')
all_results = []

processor = PlateProcessor()

for file_path in plate_files:
    print(f"Processing {Path(file_path).name}...")
    plate_results = processor.process_file(file_path)
    all_results.append(plate_results)

# Combine all plates
combined_results = pd.concat(all_results, ignore_index=True)

# Analyze across plates
plate_summary = combined_results.groupby('PlateID').agg({
    'Z_lptA': ['mean', 'std'],
    'Z_ldtD': ['mean', 'std'],
    'Viability_Gate_lptA': 'mean'
}).round(3)

print("Per-plate summary:")
print(plate_summary)
```

### Custom Analysis

```python
# Custom hit scoring function
def calculate_hit_score(df):
    """Calculate custom hit score combining both targets."""
    df['Combined_Z'] = np.sqrt(df['Z_lptA']**2 + df['Z_ldtD']**2)
    df['Hit_Score'] = np.where(
        (df['Viability_Gate_lptA'] == True) & 
        (df['Viability_Gate_ldtD'] == True),
        df['Combined_Z'],
        0
    )
    return df

# Apply custom scoring
results_with_score = calculate_hit_score(results)

# Rank by custom score
top_hits = results_with_score.nlargest(20, 'Hit_Score')
print("Top 20 compounds by combined hit score:")
print(top_hits[['Well', 'Compound_ID', 'Hit_Score', 'Z_lptA', 'Z_ldtD']])
```

### Batch Processing with Configuration

```python
import yaml
from bio_hit_finder import PlateProcessor

# Load configuration
with open('analysis_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize with config
processor = PlateProcessor(**config['processing'])

# Process all files in directory
input_dir = Path(config['paths']['input'])
output_dir = Path(config['paths']['output'])
output_dir.mkdir(exist_ok=True)

for csv_file in input_dir.glob('*.csv'):
    print(f"Processing {csv_file.name}...")
    
    # Process data
    results = processor.process_file(csv_file)
    
    # Export results
    output_file = output_dir / f"processed_{csv_file.name}"
    results.to_csv(output_file, index=False)
    
    # Generate report if requested
    if config.get('generate_reports', False):
        report_file = output_dir / f"report_{csv_file.stem}.pdf"
        generate_pdf_report(results, report_file)

print("Batch processing complete!")
```

### Configuration File Example

```yaml
# analysis_config.yaml
processing:
  viability_threshold: 0.3
  z_threshold: 2.0
  backend: 'pandas'
  n_jobs: -1

paths:
  input: 'data/raw/'
  output: 'results/'

quality_control:
  check_edge_effects: true
  apply_bscore_correction: true
  edge_threshold: 0.4

export:
  formats: ['csv', 'excel']
  include_plots: true
  generate_reports: true

hit_calling:
  primary_threshold: 2.0
  secondary_threshold: 1.5
  viability_gate: true
  fdr_correction: false
```

---

**For more examples and advanced usage, see the [GitHub repository examples directory](https://github.com/bio-hit-finder/examples).**