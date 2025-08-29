# Getting Started with Bio Hit Finder

Welcome to Bio Hit Finder, a comprehensive platform for analyzing biological plate-based screening data. This guide will help you get up and running quickly.

## What is Bio Hit Finder?

Bio Hit Finder is a web-based platform designed to process and analyze high-throughput screening data from biological assays. It specializes in:

- **Dual Reporter Analysis**: Processing BG (BetaGlo) and BT (BacTiter) measurements for lptA and ldtD genes
- **Growth Assessment**: Analyzing OD measurements for WT, ΔtolC, and SA strains
- **Statistical Analysis**: Robust Z-score and B-score calculations for hit identification
- **Quality Control**: Edge effect detection and spatial artifact analysis
- **Visualization**: Interactive plots, heatmaps, and publication-ready figures

## Prerequisites

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum (8GB recommended for large datasets)
- **Storage**: 1GB free space for installation and sample data

### Technical Knowledge

- **Required**: Basic familiarity with CSV files and web browsers
- **Helpful**: Understanding of statistical concepts (Z-scores, median, standard deviation)
- **Not Required**: Programming experience (the platform is fully web-based)

## Installation

### Method 1: Standard Installation (Recommended)

1. **Download the Platform**
   ```bash
   git clone https://github.com/bio-hit-finder/bio-hit-finder.git
   cd bio-hit-finder
   ```

2. **Install Dependencies**
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using conda
   conda env create -f environment.yml
   conda activate bio-hit-finder
   ```

3. **Launch the Application**
   ```bash
   streamlit run app.py
   ```

4. **Open in Browser**
   - The application will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, click the URL shown in the terminal

### Method 2: Docker Installation

1. **Pull and Run Docker Image**
   ```bash
   docker pull biohitfinder/platform:latest
   docker run -p 8501:8501 biohitfinder/platform:latest
   ```

2. **Access in Browser**
   - Navigate to `http://localhost:8501`

### Method 3: Cloud Deployment

Access the hosted version at `https://bio-hit-finder.streamlit.app` (no installation required).

## First Launch

When you first launch Bio Hit Finder, you'll see the main interface with several tabs:

### 1. Welcome Tab
- Overview of platform capabilities
- Quick access to demo mode
- Recent updates and announcements

### 2. Data Upload Tab
- File upload interface
- Data validation and preview
- Format checking and error reporting

### 3. Analysis Tabs
- **Summary**: Overview statistics and quality metrics
- **Hits**: Ranked potential hits with filtering options
- **Visualizations**: Interactive charts and plots
- **Heatmaps**: Plate-based spatial visualizations
- **QC Report**: Quality control diagnostics

## Quick Start Workflow

### Step 1: Try Demo Mode

1. Click **"🚀 Start Demo"** on the welcome page
2. Select **"Standard Workflow"** for a complete walkthrough
3. Follow the guided tour to understand all features

### Step 2: Load Sample Data

1. Navigate to the **"Data Upload"** tab
2. Click **"Load Demo Data"** to try with sample files
3. Or upload your own CSV file using the file uploader

### Step 3: Review Data Quality

1. Check the **"Summary"** tab for overview statistics
2. Look for warnings about missing data or outliers
3. Review the **"QC Report"** for spatial artifacts

### Step 4: Identify Hits

1. Go to the **"Hits"** tab
2. Adjust Z-score thresholds using the sidebar controls
3. Review the ranked hit list and individual well details

### Step 5: Visualize Results

1. Explore the **"Visualizations"** tab for distribution plots
2. Use the **"Heatmaps"** tab to see spatial patterns
3. Download plots for presentations or publications

### Step 6: Export Results

1. Use the **"Export"** section to download processed data
2. Generate PDF reports for documentation
3. Create publication-ready figures

## Understanding Your Data

### Input Data Format

Your CSV file should contain these **required columns**:

| Column | Description | Example Values |
|--------|-------------|----------------|
| `BG_lptA` | BetaGlo signal for lptA reporter | 1052.3, 987.1, 1134.6 |
| `BT_lptA` | BacTiter signal for lptA (viability) | 2134.5, 2087.3, 2203.1 |
| `BG_ldtD` | BetaGlo signal for ldtD reporter | 876.2, 823.7, 912.8 |
| `BT_ldtD` | BacTiter signal for ldtD (viability) | 1567.8, 1489.2, 1623.4 |
| `OD_WT` | Optical density for wild-type strain | 0.48, 0.51, 0.49 |
| `OD_tolC` | Optical density for ΔtolC strain | 0.42, 0.38, 0.41 |
| `OD_SA` | Optical density for SA strain | 0.45, 0.47, 0.44 |

### Optional Columns

| Column | Description | Example Values |
|--------|-------------|----------------|
| `PlateID` | Unique plate identifier | PLATE_001, BATCH_A_01 |
| `Well` | Well position | A01, B12, H07 |
| `Row` | Row letter | A, B, C, ..., H |
| `Col` | Column number | 1, 2, 3, ..., 12 |
| `Treatment` | Treatment type | DMSO, Compound, Control |
| `Compound_ID` | Compound identifier | CMPD_0001, KIN_0234 |

### Data Quality Checklist

Before analysis, ensure your data meets these criteria:

✅ **File Format**: CSV with comma separators
✅ **Column Names**: Exact match to required column names (case-sensitive)
✅ **Numeric Values**: All measurement columns contain numeric values
✅ **Missing Data**: Less than 5% missing values per column
✅ **Plate Layout**: Consistent well positions (if using positional columns)
✅ **Value Ranges**: Reasonable ranges for your assay type

## Common Issues and Solutions

### Problem: "Column not found" error

**Cause**: Column names don't match exactly
**Solution**: Check spelling and case sensitivity of column names

### Problem: "Invalid numeric values" warning

**Cause**: Non-numeric data in measurement columns
**Solution**: Replace text values with numbers or leave blank for missing data

### Problem: Application won't start

**Cause**: Missing dependencies or Python version issues
**Solution**: 
```bash
pip install --upgrade streamlit pandas numpy plotly
python --version  # Should be 3.11+
```

### Problem: Slow performance with large files

**Cause**: Large dataset size or insufficient memory
**Solution**: 
- Use subsets for initial exploration
- Consider using the Polars backend for better performance
- Increase system memory or use cloud deployment

## Getting Help

### Documentation Resources

- **User Guides**: Detailed guides for each analysis type
- **API Reference**: Technical documentation for developers  
- **FAQ**: Answers to frequently asked questions
- **Troubleshooting**: Solutions to common problems

### Community Support

- **GitHub Issues**: Report bugs and request features
- **Discussion Forum**: Ask questions and share experiences
- **Email Support**: Direct technical support (premium users)

### Sample Data

Use the provided sample datasets to practice:

- `sample_plate_normal.csv` - Standard biological variation
- `sample_plate_hits.csv` - Dataset with obvious hits
- `sample_plate_edge_effects.csv` - Demonstrating spatial artifacts
- `multi_plate_dataset.csv` - Multi-plate analysis example

## Next Steps

Now that you have Bio Hit Finder running:

1. **📖 Read the Data Format Guide** to understand input requirements
2. **🎯 Try the Hit Analysis Guide** for detailed analysis workflows  
3. **📊 Explore the Visualization Guide** for plot customization
4. **🔍 Learn Quality Control** to ensure reliable results

## Updates and Versioning

Bio Hit Finder follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes requiring data or workflow updates
- **MINOR**: New features and enhancements (backward compatible)
- **PATCH**: Bug fixes and minor improvements

Check the **Release Notes** for detailed information about each update.

---

**Ready to start analyzing your data? Continue to the [Data Format Guide](data_format.md) for detailed input specifications.**