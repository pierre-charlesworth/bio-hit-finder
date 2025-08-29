# API Documentation

This document provides comprehensive technical documentation for Bio Hit Finder's internal APIs and modules. Use this for development, debugging, and extending the platform.

## Table of Contents

1. [Core API](#core-api)
2. [Analytics API](#analytics-api)
3. [Visualization API](#visualization-api)
4. [Export API](#export-api)
5. [Configuration API](#configuration-api)
6. [Error Handling](#error-handling)
7. [Extension Points](#extension-points)

## Core API

### PlateProcessor

The main processing engine for biological plate data.

#### Class Definition

```python
class PlateProcessor:
    """Main processor for plate-based screening data analysis."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        viability_threshold: float = 0.3,
        z_threshold: float = 2.0,
        backend: str = 'pandas',
        n_jobs: int = 1,
        low_memory: bool = False
    ) -> None:
        """
        Initialize the plate processor.
        
        Parameters:
        -----------
        config : Dict[str, Any], optional
            Configuration dictionary overriding defaults
        viability_threshold : float, default=0.3
            Minimum relative viability for hit calling (0.0-1.0)
        z_threshold : float, default=2.0
            Z-score threshold for statistical significance (>0.0)
        backend : str, default='pandas'
            Data processing backend ('pandas' or 'polars')
        n_jobs : int, default=1
            Number of parallel processing jobs (-1 for all cores)
        low_memory : bool, default=False
            Enable memory-efficient processing for large datasets
            
        Raises:
        -------
        ValueError
            If parameters are out of valid ranges
        ImportError
            If specified backend is not available
        """
```

#### Methods

##### process_dataframe()

```python
def process_dataframe(
    self,
    df: pd.DataFrame,
    plate_id_col: str = 'PlateID',
    well_col: str = 'Well',
    validate_data: bool = True
) -> pd.DataFrame:
    """
    Process a DataFrame containing plate screening data.
    
    This method performs the complete analysis pipeline including:
    - Data validation and cleaning
    - Reporter ratio calculations
    - Statistical normalization (Z-scores)
    - Viability gating
    - Hit classification
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame with required measurement columns:
        - BG_lptA, BT_lptA: lptA reporter and viability
        - BG_ldtD, BT_ldtD: ldtD reporter and viability  
        - OD_WT, OD_tolC, OD_SA: Growth measurements
    plate_id_col : str, default='PlateID'
        Column name containing plate identifiers
    well_col : str, default='Well'
        Column name containing well positions (e.g., 'A01', 'B12')
    validate_data : bool, default=True
        Whether to perform comprehensive data validation
        
    Returns:
    --------
    pd.DataFrame
        Processed DataFrame with additional calculated columns:
        - Ratio_lptA, Ratio_ldtD: Reporter ratios (BG/BT)
        - Z_lptA, Z_ldtD: Robust Z-scores for ratios
        - OD_*_norm: Normalized OD measurements
        - Viability_Gate_*: Viability flags (True/False)
        - Hit_* : Hit classification flags
        
    Raises:
    -------
    PlateProcessingError
        Base exception for processing failures
    DataValidationError
        If required columns are missing or data is invalid
    CalculationError
        If statistical calculations fail
        
    Examples:
    ---------
    >>> processor = PlateProcessor(z_threshold=2.5)
    >>> results = processor.process_dataframe(raw_data)
    >>> hits = results[results['Hit_lptA'] | results['Hit_ldtD']]
    >>> print(f"Found {len(hits)} hits")
    """
```

##### process_file()

```python
def process_file(
    self,
    file_path: Union[str, Path],
    sheet_name: Optional[str] = None,
    **read_kwargs
) -> pd.DataFrame:
    """
    Process data from a file (CSV or Excel).
    
    Parameters:
    -----------
    file_path : Union[str, Path]
        Path to input file (.csv or .xlsx/.xls)
    sheet_name : str, optional
        Excel sheet name (if None, uses first sheet)
    **read_kwargs
        Additional arguments passed to pd.read_csv() or pd.read_excel()
        
    Returns:
    --------
    pd.DataFrame
        Processed data with calculated metrics
        
    Raises:
    -------
    FileNotFoundError
        If input file doesn't exist
    ValueError
        If file format is not supported
    PlateProcessingError
        If processing fails
        
    Examples:
    ---------
    >>> processor = PlateProcessor()
    >>> results = processor.process_file('data/plate001.csv')
    >>> 
    >>> # Excel with specific sheet
    >>> results = processor.process_file('data/plates.xlsx', sheet_name='Plate1')
    """
```

##### calculate_summary_statistics()

```python
def calculate_summary_statistics(
    self,
    df: pd.DataFrame,
    group_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive summary statistics for processed data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Processed plate data (output from process_dataframe)
    group_by : str, optional
        Column name to group statistics by (e.g., 'PlateID')
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing:
        - 'overall': Overall statistics across all data
        - 'by_plate': Per-plate statistics (if group_by specified)
        - 'quality_metrics': Data quality indicators
        - 'hit_statistics': Hit calling results
        
    Examples:
    ---------
    >>> stats = processor.calculate_summary_statistics(results)
    >>> print(f"Overall hit rate: {stats['overall']['hit_rate']:.1%}")
    >>> print(f"CV of ratios: {stats['overall']['cv_ratio_lptA']:.1%}")
    """
```

### Core Calculation Functions

#### calculate_reporter_ratios()

```python
def calculate_reporter_ratios(
    df: pd.DataFrame,
    bg_cols: Optional[List[str]] = None,
    bt_cols: Optional[List[str]] = None,
    ratio_suffix: str = 'Ratio',
    min_viability: float = 1.0
) -> pd.DataFrame:
    """
    Calculate reporter ratios (BG/BT) with optional filtering.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data with BG and BT columns
    bg_cols : List[str], optional
        BetaGlo column names (default: ['BG_lptA', 'BG_ldtD'])
    bt_cols : List[str], optional  
        BacTiter column names (default: ['BT_lptA', 'BT_ldtD'])
    ratio_suffix : str, default='Ratio'
        Prefix for ratio column names
    min_viability : float, default=1.0
        Minimum BT value for valid ratio calculation
        
    Returns:
    --------
    pd.DataFrame
        Input DataFrame with added ratio columns
        
    Mathematical Formula:
    --------------------
    Ratio_X = BG_X / BT_X, where BT_X >= min_viability
    
    Invalid ratios (BT_X < min_viability) are set to NaN
        
    Examples:
    ---------
    >>> df_with_ratios = calculate_reporter_ratios(data)
    >>> print(df_with_ratios[['Ratio_lptA', 'Ratio_ldtD']].describe())
    """
```

#### calculate_robust_zscore()

```python
def calculate_robust_zscore(
    values: np.ndarray,
    center: str = 'median',
    scale: str = 'mad',
    nan_policy: str = 'omit'
) -> np.ndarray:
    """
    Calculate robust Z-scores using median and MAD.
    
    Parameters:
    -----------
    values : np.ndarray
        Input numeric values
    center : str, default='median'
        Centering method:
        - 'median': Use median (robust)
        - 'mean': Use arithmetic mean (classical)
    scale : str, default='mad'
        Scaling method:
        - 'mad': Median Absolute Deviation (robust)
        - 'std': Standard deviation (classical)
    nan_policy : str, default='omit'
        How to handle NaN values:
        - 'omit': Ignore NaN values in calculation
        - 'propagate': Return NaN if any input is NaN
        - 'raise': Raise error if NaN values present
        
    Returns:
    --------
    np.ndarray
        Array of Z-scores with same shape as input
        
    Mathematical Formulas:
    ---------------------
    Robust Z-score: Z = (x - median) / (1.4826 * MAD)
    Classical Z-score: Z = (x - mean) / std
    
    Where MAD = median(|X - median(X)|)
    Factor 1.4826 ≈ 1/Φ⁻¹(3/4) makes MAD equivalent to σ for normal data
    
    Notes:
    ------
    - Robust method is less sensitive to outliers
    - Classical method assumes normal distribution
    - Returns NaN for constant input values
        
    Examples:
    ---------
    >>> data = np.random.normal(100, 15, 1000)
    >>> z_robust = calculate_robust_zscore(data)
    >>> z_classical = calculate_robust_zscore(data, center='mean', scale='std')
    """
```

#### apply_viability_gate()

```python
def apply_viability_gate(
    df: pd.DataFrame,
    bt_cols: Optional[List[str]] = None,
    threshold: float = 0.3,
    method: str = 'plate_median',
    suffix: str = 'Viability_Gate'
) -> pd.DataFrame:
    """
    Apply viability gating to identify wells with sufficient cell viability.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data with BacTiter measurements
    bt_cols : List[str], optional
        BacTiter column names (default: ['BT_lptA', 'BT_ldtD'])
    threshold : float, default=0.3
        Minimum relative viability (0.0-1.0)
    method : str, default='plate_median'
        Reference calculation method:
        - 'plate_median': Use median within each plate
        - 'overall_median': Use median across all data
        - 'control_median': Use median of control wells
    suffix : str, default='Viability_Gate'
        Suffix for gate column names
        
    Returns:
    --------
    pd.DataFrame
        Input DataFrame with added boolean gate columns
        
    Mathematical Formula:
    --------------------
    Viability_Gate_X = BT_X >= (threshold × reference_BT_X)
    
    Where reference depends on method:
    - plate_median: median(BT_X) within plate
    - overall_median: median(BT_X) across all data
    - control_median: median(BT_X) for control wells only
        
    Examples:
    ---------
    >>> gated_data = apply_viability_gate(data, threshold=0.3)
    >>> viable_wells = gated_data[gated_data['Viability_Gate_lptA']]
    >>> print(f"Viable wells: {len(viable_wells)}/{len(data)}")
    """
```

## Analytics API

### BScoreProcessor

Spatial bias correction using median polish algorithm.

#### Class Definition

```python
class BScoreProcessor:
    """B-score calculation for spatial bias correction in plate data."""
    
    def __init__(
        self,
        max_iter: int = 100,
        tolerance: float = 1e-6,
        min_wells_per_row: int = 3,
        min_wells_per_col: int = 3,
        fill_missing: str = 'median'
    ) -> None:
        """
        Initialize B-score processor.
        
        Parameters:
        -----------
        max_iter : int, default=100
            Maximum iterations for median polish algorithm
        tolerance : float, default=1e-6
            Convergence tolerance for median polish
        min_wells_per_row : int, default=3
            Minimum valid wells required per row
        min_wells_per_col : int, default=3
            Minimum valid wells required per column
        fill_missing : str, default='median'
            Method for filling missing values:
            - 'median': Use row/column median
            - 'mean': Use row/column mean
            - 'zero': Fill with zero
            - 'skip': Skip wells with missing values
        """
```

#### Methods

##### calculate_bscores()

```python
def calculate_bscores(
    self,
    df: pd.DataFrame,
    value_cols: Optional[List[str]] = None,
    row_col: str = 'Row',
    col_col: str = 'Col',
    plate_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate B-scores using median polish spatial correction.
    
    The median polish algorithm iteratively removes row and column effects:
    1. Subtract row medians from all values in each row
    2. Subtract column medians from all values in each column  
    3. Repeat until convergence (change < tolerance)
    4. Scale final residuals to Z-score equivalent
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input data with spatial layout information
    value_cols : List[str], optional
        Columns to process (default: ['Ratio_lptA', 'Ratio_ldtD'])
    row_col : str, default='Row'
        Column containing row identifiers (A, B, C, ...)
    col_col : str, default='Col'  
        Column containing column numbers (1, 2, 3, ...)
    plate_col : str, optional
        Column containing plate IDs (for multi-plate processing)
        
    Returns:
    --------
    pd.DataFrame
        Input DataFrame with added B-score columns (B_lptA, B_ldtD, etc.)
        
    Mathematical Details:
    --------------------
    1. Arrange data in plate layout matrix M[i,j]
    2. Iteratively apply:
        - M[i,j] = M[i,j] - median(M[i,:])  # Remove row effects
        - M[i,j] = M[i,j] - median(M[:,j])  # Remove column effects
    3. Continue until |change| < tolerance
    4. Scale residuals: B[i,j] = M[i,j] / (1.4826 * MAD(M))
        
    Raises:
    -------
    ValueError
        If insufficient data for spatial correction
    ConvergenceError
        If median polish fails to converge
        
    Examples:
    ---------
    >>> processor = BScoreProcessor(max_iter=50)
    >>> corrected = processor.calculate_bscores(plate_data)
    >>> print(corrected[['B_lptA', 'B_ldtD']].describe())
    """
```

##### diagnose_spatial_effects()

```python
def diagnose_spatial_effects(
    self,
    df: pd.DataFrame,
    value_col: str,
    row_col: str = 'Row',
    col_col: str = 'Col'
) -> Dict[str, Any]:
    """
    Diagnose spatial effects before B-score correction.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input plate data
    value_col : str
        Column to analyze for spatial effects
    row_col : str, default='Row'
        Row identifier column
    col_col : str, default='Col'
        Column identifier column
        
    Returns:
    --------
    Dict[str, Any]
        Diagnostic information:
        - 'row_effects': Row-wise statistics
        - 'col_effects': Column-wise statistics  
        - 'spatial_correlation': Correlation with position
        - 'recommendation': Whether B-scores are recommended
        
    Examples:
    ---------
    >>> diagnosis = processor.diagnose_spatial_effects(data, 'Ratio_lptA')
    >>> if diagnosis['recommendation'] == 'apply_bscores':
    >>>     corrected = processor.calculate_bscores(data)
    """
```

### EdgeEffectDetector

Detection and quantification of plate edge effects.

#### Class Definition

```python
class EdgeEffectDetector:
    """Detector for edge effects and spatial artifacts in plate data."""
    
    def __init__(
        self,
        edge_definition: str = 'outer',
        min_edge_wells: int = 16,
        statistical_test: str = 'mannwhitney'
    ) -> None:
        """
        Initialize edge effect detector.
        
        Parameters:
        -----------
        edge_definition : str, default='outer'
            How to define edge wells:
            - 'outer': Outermost row and column
            - 'outer2': Two outermost rows and columns  
            - 'corners': Just corner wells
            - 'custom': User-defined edge wells
        min_edge_wells : int, default=16
            Minimum number of edge wells required for analysis
        statistical_test : str, default='mannwhitney'
            Statistical test for edge vs. interior comparison:
            - 'mannwhitney': Mann-Whitney U test (non-parametric)
            - 'ttest': Independent t-test (parametric)
            - 'kstest': Kolmogorov-Smirnov test
        """
```

#### Methods

##### analyze_edge_effects()

```python
def analyze_edge_effects(
    self,
    df: pd.DataFrame,
    value_cols: Optional[List[str]] = None,
    row_col: str = 'Row',
    col_col: str = 'Col',
    plate_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive analysis of edge effects in plate data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Plate data with positional information
    value_cols : List[str], optional
        Columns to analyze (default: ratio columns)
    row_col : str, default='Row'
        Row identifier column  
    col_col : str, default='Col'
        Column identifier column
    plate_col : str, optional
        Plate identifier for multi-plate analysis
        
    Returns:
    --------
    Dict[str, Any]
        Comprehensive edge effect analysis:
        - 'edge_score': Overall edge effect magnitude (0-1)
        - 'warning_level': WarningLevel enum (NONE/MINOR/MODERATE/SEVERE)
        - 'p_values': Statistical test results
        - 'effect_sizes': Cohen's d or equivalent effect sizes
        - 'edge_wells': List of identified edge wells
        - 'interior_wells': List of interior wells
        - 'recommendations': Suggested actions
        
    Statistical Methods:
    -------------------
    1. Edge vs. Interior Comparison:
        - Statistical test (Mann-Whitney U, t-test, or K-S)
        - Effect size calculation (Cohen's d, Glass's delta)
        - Multiple comparison correction (Bonferroni)
    
    2. Spatial Correlation:
        - Correlation with distance from center
        - Correlation with distance from edges
        - Gradient analysis (row/column trends)
    
    3. Pattern Recognition:
        - Systematic row effects
        - Systematic column effects  
        - Corner effects vs. general edge effects
        
    Examples:
    ---------
    >>> detector = EdgeEffectDetector(edge_definition='outer2')
    >>> analysis = detector.analyze_edge_effects(plate_data)
    >>> print(f"Edge score: {analysis['edge_score']:.3f}")
    >>> if analysis['warning_level'] == WarningLevel.SEVERE:
    >>>     print("Strong edge effects detected - apply B-score correction")
    """
```

##### get_edge_wells()

```python
def get_edge_wells(
    self,
    df: pd.DataFrame,
    n_rows: Optional[int] = None,
    n_cols: Optional[int] = None,
    row_col: str = 'Row',
    col_col: str = 'Col'
) -> Dict[str, List[str]]:
    """
    Identify edge and interior wells based on plate layout.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Plate data with positional information
    n_rows : int, optional
        Number of rows (auto-detected if None)
    n_cols : int, optional
        Number of columns (auto-detected if None)
    row_col : str, default='Row'
        Row identifier column
    col_col : str, default='Col'
        Column identifier column
        
    Returns:
    --------
    Dict[str, List[str]]
        Dictionary containing:
        - 'edge_wells': List of edge well identifiers
        - 'interior_wells': List of interior well identifiers
        - 'corner_wells': List of corner well identifiers
        - 'plate_dimensions': Tuple of (n_rows, n_cols)
        
    Examples:
    ---------
    >>> wells = detector.get_edge_wells(plate_data)
    >>> print(f"Edge wells: {len(wells['edge_wells'])}")
    >>> print(f"Interior wells: {len(wells['interior_wells'])}")
    """
```

## Visualization API

### Chart Generation Functions

#### create_histogram()

```python
def create_histogram(
    df: pd.DataFrame,
    column: str,
    title: Optional[str] = None,
    bins: Union[int, str] = 'auto',
    color: str = '#1f77b4',
    show_stats: bool = True,
    show_normal: bool = False,
    height: int = 400,
    width: int = 600
) -> go.Figure:
    """
    Create interactive histogram with statistical overlays.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Data to plot
    column : str
        Column name to create histogram for
    title : str, optional
        Plot title (auto-generated if None)
    bins : Union[int, str], default='auto'
        Number of bins or binning method:
        - int: Specific number of bins
        - 'auto': Automatic binning (Sturges' rule)
        - 'fd': Freedman-Diaconis rule
        - 'scott': Scott's rule
    color : str, default='#1f77b4'
        Histogram bar color (hex, rgb, or named color)
    show_stats : bool, default=True
        Whether to show mean/median lines and statistics
    show_normal : bool, default=False
        Whether to overlay normal distribution curve
    height : int, default=400
        Plot height in pixels
    width : int, default=600
        Plot width in pixels
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive histogram with optional statistical overlays
        
    Features:
    ---------
    - Interactive zoom and pan
    - Hover information with bin counts
    - Statistical overlays (mean, median, std dev)
    - Normal distribution overlay option
    - Customizable appearance and dimensions
        
    Examples:
    ---------
    >>> fig = create_histogram(results, 'Ratio_lptA', 
    ...                       title='lptA Reporter Ratios',
    ...                       bins=30, show_normal=True)
    >>> fig.show()
    >>> fig.write_html('histogram.html')
    """
```

#### create_scatter_plot()

```python
def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    symbol_col: Optional[str] = None,
    title: Optional[str] = None,
    hover_data: Optional[List[str]] = None,
    trendline: Optional[str] = None,
    height: int = 500,
    width: int = 700
) -> go.Figure:
    """
    Create interactive scatter plot with advanced features.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Data to plot
    x_col : str
        X-axis column name
    y_col : str
        Y-axis column name  
    color_col : str, optional
        Column for color coding points
    size_col : str, optional
        Column for sizing points
    symbol_col : str, optional
        Column for point symbols
    title : str, optional
        Plot title (auto-generated if None)
    hover_data : List[str], optional
        Additional columns to show in hover tooltips
    trendline : str, optional
        Trendline type:
        - 'ols': Ordinary least squares
        - 'lowess': Locally weighted scatterplot smoothing
        - None: No trendline
    height : int, default=500
        Plot height in pixels
    width : int, default=700
        Plot width in pixels
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive scatter plot with optional enhancements
        
    Features:
    ---------
    - Multi-dimensional visualization (x, y, color, size, symbol)
    - Interactive selection and filtering
    - Customizable hover information
    - Statistical trendlines
    - Export capabilities (PNG, SVG, HTML)
        
    Examples:
    ---------
    >>> fig = create_scatter_plot(
    ...     results, 'Z_lptA', 'Z_ldtD',
    ...     color_col='Hit_Status',
    ...     size_col='OD_WT_norm',
    ...     hover_data=['Well', 'Compound_ID'],
    ...     trendline='ols'
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
    plate_col: Optional[str] = None,
    title: Optional[str] = None,
    colorscale: str = 'RdBu_r',
    show_values: bool = False,
    mask_invalid: bool = True,
    height: int = 400,
    width: int = 600
) -> go.Figure:
    """
    Create plate layout heatmap for spatial visualization.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Plate data with positional information
    value_col : str
        Column to visualize as heatmap colors
    row_col : str, default='Row'
        Row position column (A, B, C, ...)
    col_col : str, default='Col'
        Column position column (1, 2, 3, ...)
    plate_col : str, optional
        Plate identifier (creates subplots if multiple plates)
    title : str, optional
        Plot title (auto-generated if None)
    colorscale : str, default='RdBu_r'
        Plotly colorscale name:
        - 'RdBu_r': Red-Blue reversed (blue=low, red=high)
        - 'Viridis': Purple-Yellow-Green
        - 'Plasma': Purple-Pink-Yellow
        - 'Blues': White to Blue
    show_values : bool, default=False
        Whether to display values as text on heatmap
    mask_invalid : bool, default=True
        Whether to mask NaN/invalid values
    height : int, default=400
        Plot height in pixels (per subplot)
    width : int, default=600
        Plot width in pixels
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plate heatmap with hover information
        
    Features:
    ---------
    - Automatic plate layout detection (96, 384, 1536-well)
    - Multi-plate subplot support
    - Interactive hover with well details
    - Customizable color mapping
    - Missing value handling
        
    Supported Plate Formats:
    -----------------------
    - 96-well: 8 rows × 12 columns (A01-H12)
    - 384-well: 16 rows × 24 columns (A01-P24)
    - 1536-well: 32 rows × 48 columns (A01-AF48)
        
    Examples:
    ---------
    >>> fig = create_plate_heatmap(
    ...     results, 'Z_lptA',
    ...     title='lptA Z-Scores by Well Position',
    ...     colorscale='RdBu_r'
    ... )
    >>> fig.show()
    >>> 
    >>> # Multi-plate heatmap
    >>> fig = create_plate_heatmap(
    ...     multi_plate_data, 'B_ldtD',
    ...     plate_col='PlateID',
    ...     title='B-Scores Across Plates'
    ... )
    """
```

## Export API

### Data Export Functions

#### export_results()

```python
def export_results(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    format: str = 'csv',
    include_metadata: bool = True,
    compression: Optional[str] = None,
    **kwargs
) -> None:
    """
    Export processed results to various file formats.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Results DataFrame to export
    output_path : Union[str, Path]
        Output file path
    format : str, default='csv'
        Export format:
        - 'csv': Comma-separated values
        - 'excel': Excel workbook (.xlsx)
        - 'parquet': Apache Parquet (efficient for large data)
        - 'feather': Apache Arrow Feather (fast I/O)
        - 'hdf5': Hierarchical Data Format 5
    include_metadata : bool, default=True
        Whether to include analysis metadata
    compression : str, optional
        Compression method ('gzip', 'bz2', 'xz' for CSV; 
        'snappy', 'gzip' for Parquet)
    **kwargs
        Additional arguments passed to pandas export functions
        
    Metadata Included:
    -----------------
    - Analysis parameters (thresholds, methods)
    - Processing timestamp
    - Software version
    - Data quality metrics
    - Column descriptions
        
    Examples:
    ---------
    >>> export_results(results, 'output/results.csv')
    >>> export_results(results, 'output/results.xlsx', 
    ...                include_metadata=True)
    >>> export_results(results, 'output/results.parquet', 
    ...                format='parquet', compression='snappy')
    """
```

#### export_hit_list()

```python
def export_hit_list(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    z_threshold: float = 2.0,
    include_borderline: bool = True,
    sort_by: str = 'max_z_score',
    max_hits: Optional[int] = None,
    format: str = 'excel'
) -> None:
    """
    Export curated hit list with ranking and annotation.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Processed results DataFrame
    output_path : Union[str, Path]
        Output file path
    z_threshold : float, default=2.0
        Minimum |Z-score| for hit inclusion
    include_borderline : bool, default=True
        Include borderline hits (1.5 ≤ |Z| < threshold)
    sort_by : str, default='max_z_score'
        Sorting criteria:
        - 'max_z_score': Maximum |Z-score| across targets
        - 'combined_z': Combined Z-score magnitude
        - 'selectivity': Target selectivity ratio
        - 'compound_id': Alphabetical by compound ID
    max_hits : int, optional
        Maximum number of hits to export
    format : str, default='excel'
        Export format ('excel', 'csv')
        
    Output Structure:
    ----------------
    - Hit_Rank: Sequential ranking
    - Compound_ID: Compound identifier
    - Well: Well position
    - Max_Z_Score: Maximum |Z-score|
    - Hit_Category: Strong/Moderate/Borderline
    - Target_Selectivity: lptA/ldtD selectivity
    - All original measurements and calculated metrics
        
    Examples:
    ---------
    >>> export_hit_list(results, 'hits.xlsx', 
    ...                 z_threshold=2.5, max_hits=100)
    >>> export_hit_list(results, 'top_hits.csv',
    ...                 sort_by='selectivity', max_hits=50)
    """
```

### Report Generation

#### generate_pdf_report()

```python
def generate_pdf_report(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    template: str = 'standard',
    include_plots: bool = True,
    plot_formats: List[str] = ['png'],
    dpi: int = 300,
    **template_kwargs
) -> None:
    """
    Generate comprehensive PDF analysis report.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Processed analysis results
    output_path : Union[str, Path]
        Output PDF file path
    template : str, default='standard'
        Report template:
        - 'standard': Full analysis report
        - 'summary': Executive summary only
        - 'qc_only': Quality control focus
        - 'hits_only': Hit analysis focus
    include_plots : bool, default=True
        Whether to include visualization plots
    plot_formats : List[str], default=['png']
        Plot formats to embed ('png', 'svg', 'jpeg')
    dpi : int, default=300
        Plot resolution for print quality
    **template_kwargs
        Additional variables for template rendering
        
    Report Sections:
    ---------------
    1. Executive Summary
        - Key findings and statistics
        - Data quality assessment
        - Hit summary with counts
    
    2. Methods and Parameters
        - Analysis workflow description
        - Statistical methods used
        - Parameter settings
    
    3. Data Quality Assessment
        - Missing data analysis
        - Outlier detection results
        - Spatial artifact assessment
    
    4. Statistical Analysis
        - Distribution analysis
        - Hit identification results
        - Quality control metrics
    
    5. Visualizations
        - Histograms of key metrics
        - Scatter plots and correlations
        - Plate heatmaps
        - QC diagnostic plots
    
    6. Hit Analysis
        - Ranked hit list
        - Hit characteristics analysis
        - Target selectivity assessment
    
    7. Recommendations
        - Follow-up suggestions
        - Quality improvement recommendations
        - Statistical considerations
        
    Examples:
    ---------
    >>> generate_pdf_report(results, 'analysis_report.pdf')
    >>> generate_pdf_report(results, 'summary.pdf', 
    ...                     template='summary', 
    ...                     experiment_title='Kinase Screen #1')
    """
```

## Configuration API

### ConfigManager

```python
class ConfigManager:
    """Centralized configuration management system."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager.
        
        Parameters:
        -----------
        config_path : Union[str, Path], optional
            Path to YAML configuration file
        """
        
    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value with validation."""
        
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration values and types."""
```

### Default Configuration Schema

```yaml
# Default configuration structure
analysis:
  viability_threshold: 0.3          # Minimum relative viability
  z_threshold: 2.0                  # Z-score threshold for hits
  missing_data_threshold: 0.05      # Maximum missing data rate
  outlier_detection: true           # Enable outlier detection
  
processing:
  backend: 'pandas'                 # Data processing backend
  n_jobs: 1                        # Parallel processing jobs
  chunk_size: 1000                 # Chunk size for large data
  low_memory: false                # Memory optimization
  cache_results: true              # Enable result caching
  
quality_control:
  enable_edge_detection: true      # Edge effect detection
  edge_threshold: 0.4              # Edge effect significance
  apply_bscore_correction: 'auto'  # B-score correction
  spatial_analysis: true           # Spatial pattern analysis
  
visualization:
  theme: 'plotly'                  # Plot theme
  color_palette: 'viridis'         # Default color scheme
  figure_size: [800, 600]          # Default figure dimensions
  dpi: 300                         # Plot resolution
  
export:
  default_format: 'csv'            # Default export format
  include_metadata: true           # Include analysis metadata
  compression: null                # Compression method
  precision: 6                     # Numeric precision
  
logging:
  level: 'INFO'                    # Log level
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: null                       # Log file path (null = console only)
```

## Error Handling

### Exception Hierarchy

```python
class BioHitFinderError(Exception):
    """Base exception for Bio Hit Finder."""
    pass

class PlateProcessingError(BioHitFinderError):
    """Base exception for plate processing errors."""
    pass

class DataValidationError(PlateProcessingError):
    """Raised when input data validation fails."""
    pass

class CalculationError(PlateProcessingError):
    """Raised when statistical calculations fail."""
    pass

class ConfigurationError(BioHitFinderError):
    """Raised when configuration is invalid."""
    pass

class VisualizationError(BioHitFinderError):
    """Raised when plot generation fails."""
    pass

class ExportError(BioHitFinderError):
    """Raised when data export fails."""
    pass
```

### Error Context and Logging

```python
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def error_context(operation: str, **context_info):
    """Context manager for enhanced error reporting."""
    try:
        logger.info(f"Starting {operation}")
        yield
        logger.info(f"Completed {operation}")
    except Exception as e:
        error_msg = f"Failed {operation}: {str(e)}"
        if context_info:
            error_msg += f" Context: {context_info}"
        logger.error(error_msg, exc_info=True)
        raise
```

## Extension Points

### Custom Processors

```python
class CustomProcessor(PlateProcessor):
    """Example of extending PlateProcessor."""
    
    def custom_calculation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add custom calculations to the pipeline."""
        # Your custom logic here
        return df
    
    def process_dataframe(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Override to include custom calculations."""
        # Call parent method
        result = super().process_dataframe(df, **kwargs)
        
        # Add custom calculations
        result = self.custom_calculation(result)
        
        return result
```

### Plugin Architecture

```python
class PluginManager:
    """Manager for Bio Hit Finder plugins."""
    
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, name: str, plugin_class):
        """Register a new plugin."""
        self.plugins[name] = plugin_class
    
    def get_plugin(self, name: str):
        """Get a registered plugin."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugins."""
        return list(self.plugins.keys())

# Global plugin manager
plugin_manager = PluginManager()

# Example plugin registration
@plugin_manager.register_plugin('custom_export')
class CustomExportPlugin:
    def export(self, df: pd.DataFrame, path: str, **kwargs):
        # Custom export logic
        pass
```

---

This API documentation provides comprehensive technical details for developers working with or extending Bio Hit Finder. All functions include detailed docstrings, parameter specifications, return values, and practical examples.