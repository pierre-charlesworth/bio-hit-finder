# System Architecture

This document provides a comprehensive overview of the Bio Hit Finder platform architecture, design decisions, and technical implementation details.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Overview](#component-overview)
3. [Data Flow](#data-flow)
4. [Module Organization](#module-organization)
5. [Design Patterns](#design-patterns)
6. [Performance Considerations](#performance-considerations)
7. [Security Architecture](#security-architecture)

## High-Level Architecture

Bio Hit Finder follows a modular, layered architecture designed for scalability, maintainability, and extensibility.

```
┌─────────────────────────────────────────────────────┐
│                 Presentation Layer                  │
│  ┌─────────────────────────────────────────────┐   │
│  │            Streamlit UI                     │   │
│  │  ┌─────────┬─────────┬─────────┬─────────┐  │   │
│  │  │ Upload  │Analysis │Visualiz │ Export  │  │   │
│  │  │   Tab   │  Tabs   │ ations  │   Tab   │  │   │
│  │  └─────────┴─────────┴─────────┴─────────┘  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│                Application Layer                    │
│  ┌─────────────────────────────────────────────┐   │
│  │           Demo Mode System                  │   │
│  │        Interactive Tutorials               │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │        Session State Management            │   │
│  │         Caching & Performance              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│                  Business Layer                     │
│  ┌─────────────┬─────────────┬─────────────────┐   │
│  │    Core     │ Analytics   │  Visualizations │   │
│  │ Processing  │   Module    │     Module      │   │
│  │             │             │                 │   │
│  │ ┌─────────┐ │ ┌─────────┐ │ ┌─────────────┐ │   │
│  │ │Plate    │ │ │B-Score  │ │ │Charts       │ │   │
│  │ │Processor│ │ │Processor│ │ │& Heatmaps   │ │   │
│  │ └─────────┘ │ └─────────┘ │ └─────────────┘ │   │
│  │ ┌─────────┐ │ ┌─────────┐ │ ┌─────────────┐ │   │
│  │ │Statistics│ │ │Edge     │ │ │Styling &    │ │   │
│  │ │Calculator│ │ │Effects  │ │ │Themes       │ │   │
│  │ └─────────┘ │ └─────────┘ │ └─────────────┘ │   │
│  └─────────────┴─────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│                Export & I/O Layer                   │
│  ┌─────────────┬─────────────┬─────────────────┐   │
│  │   Export    │   Report    │   Data I/O      │   │
│  │   Module    │ Generation  │    Module       │   │
│  │             │             │                 │   │
│  │ ┌─────────┐ │ ┌─────────┐ │ ┌─────────────┐ │   │
│  │ │CSV/Excel│ │ │PDF      │ │ │File         │ │   │
│  │ │Export   │ │ │Generator│ │ │Validation   │ │   │
│  │ └─────────┘ │ └─────────┘ │ └─────────────┘ │   │
│  │ ┌─────────┐ │ ┌─────────┐ │ ┌─────────────┐ │   │
│  │ │Bundle   │ │ │Template │ │ │Data         │ │   │
│  │ │Creation │ │ │Engine   │ │ │Parsers      │ │   │
│  │ └─────────┘ │ └─────────┘ │ └─────────────┘ │   │
│  └─────────────┴─────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│                   Data Layer                        │
│  ┌─────────────┬─────────────┬─────────────────┐   │
│  │   Pandas/   │  Configuration│   Sample Data   │   │
│  │   Polars    │    System     │   & Fixtures    │   │
│  │  DataFrames │               │                 │   │
│  └─────────────┴─────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Component Overview

### Core Components

#### 1. PlateProcessor (`core/plate_processor.py`)
**Purpose**: Central orchestrator for data processing pipeline
**Responsibilities**:
- Data validation and cleaning
- Coordinate calculation modules
- Error handling and logging
- Performance optimization

**Key Features**:
```python
class PlateProcessor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)
        self.calculators = self._initialize_calculators()
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Validation → Calculations → QC → Return results
```

#### 2. Calculation Engine (`core/calculations.py`)
**Purpose**: Statistical and biological calculations
**Components**:
- Reporter ratio calculations (BG/BT)
- Robust Z-score computation
- OD normalization
- Viability gating

**Mathematical Foundation**:
```python
# Robust Z-score using median and MAD
Z = (value - median(values)) / (1.4826 * MAD(values))

# Where MAD = median(|X - median(X)|)
# Factor 1.4826 makes MAD equivalent to standard deviation for normal distributions
```

#### 3. Analytics Integration (`core/analytics_integration.py`)
**Purpose**: Interface between core processing and specialized analytics
**Functions**:
- B-score calculation coordination
- Edge effect detection integration
- Multi-plate analysis support

### Analytics Modules

#### 1. B-Score Processor (`analytics/bscore.py`)
**Purpose**: Spatial bias correction using median polish algorithm
**Algorithm**: 
```python
def median_polish(matrix, max_iter=100, tolerance=1e-6):
    """
    Iterative algorithm to remove row and column effects:
    1. Subtract row medians
    2. Subtract column medians  
    3. Repeat until convergence
    4. Scale residuals to Z-score equivalent
    """
```

**Implementation Details**:
- Handles missing data gracefully
- Configurable iteration limits
- Memory-efficient for large plates

#### 2. Edge Effect Detector (`analytics/edge_effects.py`)
**Purpose**: Identify and quantify spatial artifacts
**Detection Methods**:
- Statistical comparison (edge vs. interior)
- Spatial correlation analysis
- Pattern recognition

**Warning Levels**:
```python
class WarningLevel(Enum):
    NONE = "No significant edge effects"
    MINOR = "Minor edge effects detected"
    MODERATE = "Clear edge effects present"
    SEVERE = "Strong spatial artifacts"
```

### Visualization System

#### 1. Chart Generation (`visualizations/charts.py`)
**Purpose**: Create interactive statistical plots
**Chart Types**:
- Histograms with statistical overlays
- Scatter plots with color coding
- Box plots for group comparisons
- Correlation matrices

**Technology Stack**:
- Plotly for interactivity
- Customizable themes and styling
- Export-ready formatting

#### 2. Heatmap System (`visualizations/heatmaps.py`)
**Purpose**: Spatial visualization of plate data
**Features**:
- Automatic plate layout detection
- Multiple color schemes
- Value overlay options
- Zoom and pan functionality

**Plate Format Support**:
```python
SUPPORTED_FORMATS = {
    96: {'rows': 8, 'cols': 12, 'row_labels': 'A-H'},
    384: {'rows': 16, 'cols': 24, 'row_labels': 'A-P'},
    1536: {'rows': 32, 'cols': 48, 'row_labels': 'A-AF'}  # Future
}
```

### Export System

#### 1. Data Export (`export/csv_export.py`, `export/bundle.py`)
**Purpose**: Generate analysis outputs in various formats
**Formats Supported**:
- CSV (comma-separated values)
- Excel with multiple sheets
- Parquet for large datasets
- ZIP bundles with metadata

#### 2. Report Generation (`export/pdf_generator.py`)
**Purpose**: Create publication-ready reports
**Features**:
- Jinja2 templating system
- Automatic plot embedding
- Custom styling and branding
- Batch report generation

**Template Structure**:
```html
<!-- templates/report.html -->
<html>
<head>{{ report_styles }}</head>
<body>
    <h1>{{ experiment_title }}</h1>
    <section class="summary">{{ summary_stats }}</section>
    <section class="plots">{{ embedded_plots }}</section>
    <section class="methods">{{ methods_text }}</section>
</body>
</html>
```

## Data Flow

### 1. Input Processing Flow

```
Raw CSV/Excel File
       │
       ▼
File Validation
   │   │
   │   ├─ Format check (.csv, .xlsx)
   │   ├─ Size validation (<100MB default)
   │   └─ Encoding detection (UTF-8)
   │
   ▼
Column Validation
   │   │
   │   ├─ Required columns present
   │   ├─ Data type validation
   │   └─ Range checks
   │
   ▼
Data Cleaning
   │   │
   │   ├─ Missing value handling
   │   ├─ Outlier detection
   │   └─ Duplicate removal
   │
   ▼
Processed DataFrame
```

### 2. Analysis Processing Flow

```
Cleaned Data
       │
       ▼ ┌─────────────────────────┐
Reporter Ratio Calculation
       │ │ Ratio_lptA = BG_lptA/BT_lptA │
       │ │ Ratio_ldtD = BG_ldtD/BT_ldtD │
       ▼ └─────────────────────────┘
OD Normalization  
       │ ┌─────────────────────────────┐
       │ │ OD_norm = OD / median(OD)   │
       ▼ └─────────────────────────────┘
Robust Z-Score Calculation
       │ ┌──────────────────────────────┐
       │ │ Z = (x-med) / (1.4826*MAD)   │
       ▼ └──────────────────────────────┘
Viability Gating
       │ ┌──────────────────────────────┐
       │ │ Gate = BT > f*median(BT)     │
       ▼ └──────────────────────────────┘
Hit Classification
       │ ┌──────────────────────────────┐
       │ │ Hit = |Z|>threshold & Gate   │
       ▼ └──────────────────────────────┘
Results DataFrame
```

### 3. Quality Control Flow

```
Analysis Results
       │
       ▼
Edge Effect Detection
   │   │
   │   ├─ Spatial correlation analysis
   │   ├─ Edge vs interior comparison
   │   └─ Pattern recognition
   │
   ▼
B-Score Calculation (if needed)
   │   │
   │   ├─ Median polish algorithm
   │   ├─ Spatial bias removal
   │   └─ Residual scaling
   │
   ▼
Quality Metrics
   │   │
   │   ├─ CV calculations
   │   ├─ Z-factor computation
   │   └─ Missing data assessment
   │
   ▼
QC Report Generation
```

## Module Organization

### Directory Structure

```
bio-hit-finder/
├── app.py                    # Main Streamlit application
├── config.yaml              # Configuration settings
├── demo_mode.py             # Interactive demo system
├── sample_data_generator.py # Sample data creation
│
├── core/                    # Core processing modules
│   ├── __init__.py
│   ├── calculations.py      # Mathematical operations
│   ├── plate_processor.py   # Main processing engine
│   ├── statistics.py        # Statistical functions
│   └── analytics_integration.py # Analytics coordination
│
├── analytics/               # Advanced analysis modules
│   ├── __init__.py
│   ├── bscore.py           # B-score calculations
│   └── edge_effects.py     # Spatial analysis
│
├── visualizations/          # Plotting and visualization
│   ├── __init__.py
│   ├── charts.py           # Statistical plots
│   ├── heatmaps.py         # Spatial visualizations
│   ├── styling.py          # Themes and appearance
│   └── export_plots.py     # Plot export utilities
│
├── export/                  # Output generation
│   ├── __init__.py
│   ├── csv_export.py       # Data export functions
│   ├── pdf_generator.py    # Report generation
│   ├── bundle.py           # ZIP bundle creation
│   └── example_usage.py    # Usage examples
│
├── templates/               # Report templates
│   ├── __init__.py
│   └── report.html         # Main report template
│
├── assets/                  # Static resources
│   ├── __init__.py
│   └── styles.css          # Custom CSS
│
├── data/                    # Sample data and fixtures
│   ├── sample_plate_*.csv  # Demo datasets
│   └── sample_data_README.md
│
├── tests/                   # Test suite
│   ├── fixtures/           # Test data
│   ├── test_*.py          # Unit tests
│   └── README.md
│
└── docs/                    # Documentation
    ├── user_guide/         # User documentation
    ├── development/        # Developer docs
    └── tasks/              # Development tasks
```

### Import Dependencies

```python
# External dependencies
import streamlit as st           # Web framework
import pandas as pd             # Data manipulation
import numpy as np              # Numerical computing
import plotly.express as px     # Interactive plotting
import plotly.graph_objects as go
import yaml                     # Configuration files
import jinja2                   # Template rendering
import weasyprint              # PDF generation
import scipy.stats             # Statistical functions

# Internal modules (example)
from core import PlateProcessor
from analytics import BScoreProcessor, EdgeEffectDetector
from visualizations import create_histogram, create_heatmap
from export import generate_pdf_report, create_export_bundle
```

## Design Patterns

### 1. Factory Pattern (Processor Creation)

```python
class ProcessorFactory:
    """Factory for creating different types of processors."""
    
    @staticmethod
    def create_processor(processor_type: str, config: Dict) -> BaseProcessor:
        processors = {
            'plate': PlateProcessor,
            'bscore': BScoreProcessor,
            'edge_effects': EdgeEffectDetector
        }
        
        if processor_type not in processors:
            raise ValueError(f"Unknown processor type: {processor_type}")
        
        return processors[processor_type](config)
```

### 2. Strategy Pattern (Calculation Methods)

```python
class CalculationStrategy(ABC):
    """Abstract base for calculation strategies."""
    
    @abstractmethod
    def calculate(self, data: np.ndarray) -> np.ndarray:
        pass

class RobustZScoreStrategy(CalculationStrategy):
    def calculate(self, data: np.ndarray) -> np.ndarray:
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        return (data - median) / (1.4826 * mad)

class ClassicalZScoreStrategy(CalculationStrategy):
    def calculate(self, data: np.ndarray) -> np.ndarray:
        mean = np.mean(data)
        std = np.std(data)
        return (data - mean) / std
```

### 3. Observer Pattern (Progress Tracking)

```python
class ProcessingObserver(ABC):
    @abstractmethod
    def update(self, progress: float, message: str):
        pass

class StreamlitProgressObserver(ProcessingObserver):
    def __init__(self):
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def update(self, progress: float, message: str):
        self.progress_bar.progress(progress)
        self.status_text.text(message)
```

### 4. Configuration Pattern

```python
# config.yaml
analysis:
  viability_threshold: 0.3
  z_threshold: 2.0
  missing_data_threshold: 0.05

processing:
  backend: 'pandas'  # or 'polars'
  n_jobs: -1
  chunk_size: 1000

visualization:
  theme: 'plotly'
  color_palette: 'viridis'
  figure_size: [800, 600]

export:
  formats: ['csv', 'excel', 'pdf']
  compression: true
  include_metadata: true
```

## Performance Considerations

### 1. Data Processing Optimization

#### Memory Management
```python
class LowMemoryProcessor:
    """Processor optimized for large datasets."""
    
    def process_chunked(self, df: pd.DataFrame, chunk_size: int = 1000):
        """Process data in chunks to manage memory."""
        results = []
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            processed_chunk = self._process_chunk(chunk)
            results.append(processed_chunk)
            
        return pd.concat(results, ignore_index=True)
```

#### Parallel Processing
```python
from multiprocessing import Pool
from functools import partial

def parallel_zscore_calculation(df: pd.DataFrame, n_jobs: int = -1):
    """Calculate Z-scores in parallel across columns."""
    
    if n_jobs == -1:
        n_jobs = multiprocessing.cpu_count()
    
    columns_to_process = ['Ratio_lptA', 'Ratio_ldtD', 'OD_WT_norm']
    
    with Pool(n_jobs) as pool:
        calculate_func = partial(calculate_robust_zscore)
        results = pool.map(calculate_func, [df[col].values for col in columns_to_process])
    
    for col, z_scores in zip(columns_to_process, results):
        df[f'Z_{col}'] = z_scores
    
    return df
```

### 2. Caching Strategy

```python
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_and_process_data(file_path: str, config: Dict) -> pd.DataFrame:
    """Cached data loading and processing."""
    processor = PlateProcessor(config)
    return processor.process_file(file_path)

@st.cache_data
def generate_summary_statistics(df: pd.DataFrame) -> Dict:
    """Cached summary statistics calculation."""
    return calculate_summary_statistics(df)
```

### 3. Backend Selection

```python
class DataBackend:
    """Abstraction for different data processing backends."""
    
    @staticmethod
    def create_backend(backend_type: str):
        if backend_type == 'pandas':
            return PandasBackend()
        elif backend_type == 'polars':
            return PolarsBackend()
        else:
            raise ValueError(f"Unsupported backend: {backend_type}")

class PolarsBackend:
    """Polars backend for improved performance."""
    
    def process_dataframe(self, df_pandas: pd.DataFrame) -> pd.DataFrame:
        import polars as pl
        
        # Convert to Polars
        df_polars = pl.from_pandas(df_pandas)
        
        # Perform calculations
        df_processed = df_polars.with_columns([
            (pl.col('BG_lptA') / pl.col('BT_lptA')).alias('Ratio_lptA'),
            (pl.col('BG_ldtD') / pl.col('BT_ldtD')).alias('Ratio_ldtD')
        ])
        
        # Convert back to Pandas for compatibility
        return df_processed.to_pandas()
```

### 4. Performance Monitoring

```python
import time
import psutil
from contextlib import contextmanager

@contextmanager
def performance_monitor(operation_name: str):
    """Context manager for monitoring performance."""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    try:
        yield
    finally:
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        duration = end_time - start_time
        memory_delta = end_memory - start_memory
        
        st.info(f"{operation_name} completed in {duration:.2f}s, "
                f"memory delta: {memory_delta/1024/1024:.1f}MB")
```

## Security Architecture

### 1. Input Validation

```python
class DataValidator:
    """Comprehensive data validation system."""
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = ['.csv', '.xlsx']
    REQUIRED_COLUMNS = ['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 
                       'OD_WT', 'OD_tolC', 'OD_SA']
    
    def validate_file(self, uploaded_file) -> bool:
        """Validate uploaded file for security and format."""
        
        # Size check
        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {uploaded_file.size} bytes")
        
        # Extension check
        if not any(uploaded_file.name.endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
            raise ValueError(f"Invalid file type: {uploaded_file.name}")
        
        return True
    
    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Validate required columns are present."""
        missing_columns = set(self.REQUIRED_COLUMNS) - set(df.columns)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        return True
    
    def validate_data_types(self, df: pd.DataFrame) -> bool:
        """Validate data types for measurement columns."""
        for col in self.REQUIRED_COLUMNS:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column {col} must contain numeric values")
        
        return True
```

### 2. Safe File Handling

```python
import tempfile
import os
from pathlib import Path

class SecureFileHandler:
    """Secure file handling for uploads and processing."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def save_uploaded_file(self, uploaded_file) -> Path:
        """Safely save uploaded file to temporary location."""
        
        # Generate secure filename
        safe_filename = self._sanitize_filename(uploaded_file.name)
        file_path = Path(self.temp_dir) / safe_filename
        
        # Write file with restricted permissions
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Set restrictive permissions
        os.chmod(file_path, 0o600)
        
        return file_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove potentially dangerous characters from filename."""
        import re
        
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        # Keep only alphanumeric, dots, hyphens, and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Ensure reasonable length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:240] + ext
        
        return filename
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
```

### 3. Configuration Security

```python
class ConfigManager:
    """Secure configuration management."""
    
    ALLOWED_CONFIG_KEYS = {
        'viability_threshold': (float, 0.0, 1.0),
        'z_threshold': (float, 0.5, 5.0),
        'max_file_size': (int, 1024, 1024*1024*1024),  # 1KB to 1GB
    }
    
    def validate_config(self, config: Dict) -> Dict:
        """Validate configuration parameters."""
        validated_config = {}
        
        for key, value in config.items():
            if key not in self.ALLOWED_CONFIG_KEYS:
                continue  # Skip unknown keys
            
            expected_type, min_val, max_val = self.ALLOWED_CONFIG_KEYS[key]
            
            # Type validation
            if not isinstance(value, expected_type):
                raise ValueError(f"Config {key} must be {expected_type.__name__}")
            
            # Range validation
            if not (min_val <= value <= max_val):
                raise ValueError(f"Config {key} must be between {min_val} and {max_val}")
            
            validated_config[key] = value
        
        return validated_config
```

## Deployment Architecture

### 1. Local Deployment

```bash
# Standard local deployment
streamlit run app.py

# With custom configuration
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

### 2. Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 3. Cloud Deployment Options

#### Streamlit Cloud
```yaml
# .streamlit/config.toml
[server]
maxUploadSize = 1000
maxMessageSize = 1000

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

#### AWS/Azure/GCP
- Container deployment using Docker
- Auto-scaling based on usage
- Load balancer for high availability
- Persistent storage for user data

---

This architecture supports the platform's core requirements of performance, scalability, and maintainability while providing clear separation of concerns and extensibility for future enhancements.