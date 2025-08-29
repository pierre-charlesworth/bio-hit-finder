# Data Format Specification

This guide provides comprehensive information about input data requirements, formatting standards, and best practices for preparing your screening data for Bio Hit Finder.

## Overview

Bio Hit Finder processes tabular data representing high-throughput screening results from biological assays. The platform expects specific measurement columns and supports various optional metadata fields for enhanced analysis.

## Required Data Columns

### Core Measurements

These columns **must** be present in your CSV file:

#### Reporter Measurements (lptA Gene)

| Column | Type | Description | Units | Typical Range |
|--------|------|-------------|-------|---------------|
| `BG_lptA` | Float | BetaGlo luminescence for lptA reporter | RLU (Relative Light Units) | 100 - 5,000 |
| `BT_lptA` | Float | BacTiter luminescence for lptA (ATP/viability) | RLU | 500 - 10,000 |

#### Reporter Measurements (ldtD Gene)

| Column | Type | Description | Units | Typical Range |
|--------|------|-------------|-------|---------------|
| `BG_ldtD` | Float | BetaGlo luminescence for ldtD reporter | RLU | 100 - 4,000 |
| `BT_ldtD` | Float | BacTiter luminescence for ldtD (ATP/viability) | RLU | 500 - 8,000 |

#### Growth Measurements

| Column | Type | Description | Units | Typical Range |
|--------|------|-------------|-------|---------------|
| `OD_WT` | Float | Optical density for wild-type strain | OD600 | 0.1 - 2.0 |
| `OD_tolC` | Float | Optical density for ΔtolC strain | OD600 | 0.1 - 1.5 |
| `OD_SA` | Float | Optical density for SA strain | OD600 | 0.1 - 1.2 |

### Column Naming Requirements

- **Case Sensitive**: Column names must match exactly (e.g., `BG_lptA`, not `bg_lpta` or `BG_LPTA`)
- **No Spaces**: Use underscores, not spaces (`BT_lptA`, not `BT lptA`)
- **Consistent Format**: All files should use the same column names

## Optional Metadata Columns

### Positional Information

| Column | Type | Description | Example Values | Notes |
|--------|------|-------------|----------------|-------|
| `PlateID` | String | Unique plate identifier | `PLATE_001`, `EXP_2024_01_A` | Recommended for multi-plate analysis |
| `Well` | String | Standard well position | `A01`, `B12`, `H07` | Format: Letter + zero-padded number |
| `Row` | String | Row letter | `A`, `B`, `C`, ..., `H` (96-well)<br>`A`, `B`, ..., `P` (384-well) | Single letter, uppercase |
| `Col` | Integer | Column number | `1`, `2`, `3`, ..., `12` (96-well)<br>`1`, `2`, ..., `24` (384-well) | 1-indexed |

### Experimental Metadata

| Column | Type | Description | Example Values | Purpose |
|--------|------|-------------|----------------|---------|
| `Treatment` | String | Treatment type | `DMSO`, `Compound`, `Positive_Control` | Experimental design tracking |
| `Control_Type` | String | Control designation | `Negative`, `Positive`, `Test`, `Blank` | Quality control analysis |
| `Compound_ID` | String | Compound identifier | `CMPD_0001`, `KIN_0234`, `ZINC123456` | Hit tracking and lookup |
| `Concentration` | Float | Compound concentration | `10.0`, `1.0`, `0.1` | Dose-response analysis |
| `Concentration_Unit` | String | Concentration unit | `uM`, `nM`, `mg/mL` | Standardization |

### Experimental Context

| Column | Type | Description | Example Values | Use Case |
|--------|------|-------------|----------------|----------|
| `Experiment_Date` | String | Date of experiment | `2024-01-15`, `2024-01-15T14:30:00` | Batch effect analysis |
| `Operator` | String | Person who ran experiment | `Dr. Smith`, `JS_001` | Quality tracking |
| `Library_Name` | String | Compound library used | `Kinase_Inhibitors_v2`, `FDA_Approved` | Source tracking |
| `Assay_Type` | String | Type of assay | `Cell_Viability`, `Reporter_Gene` | Method documentation |
| `Replicate` | Integer | Replicate number | `1`, `2`, `3` | Statistical analysis |

## File Format Requirements

### CSV Specifications

- **File Extension**: `.csv` (required)
- **Delimiter**: Comma (`,`) - standard CSV format
- **Text Encoding**: UTF-8 (recommended) or ASCII
- **Line Endings**: Any standard format (Windows CRLF, Unix LF, Mac CR)
- **Header Row**: First row must contain column names
- **Quotes**: Optional for text fields, required if values contain commas

### Example File Structure

```csv
PlateID,Well,Row,Col,BG_lptA,BT_lptA,BG_ldtD,BT_ldtD,OD_WT,OD_tolC,OD_SA,Treatment,Compound_ID
PLATE_001,A01,A,1,1052.3,2134.5,876.2,1567.8,0.48,0.42,0.45,DMSO,
PLATE_001,A02,A,2,987.1,2087.3,823.7,1489.2,0.51,0.38,0.47,Compound,CMPD_0001
PLATE_001,A03,A,3,1134.6,2203.1,912.8,1623.4,0.49,0.41,0.44,Compound,CMPD_0002
```

## Data Quality Standards

### Numeric Values

- **Positive Numbers**: All measurement values should be positive
- **Reasonable Ranges**: Values should fall within expected assay ranges
- **No Text**: Measurement columns should contain only numeric values
- **Missing Data**: Use empty cells or `NaN` for missing values (not 0 or text)

### Missing Data Handling

| Situation | Recommended Approach | Example |
|-----------|---------------------|---------|
| Failed measurement | Leave cell empty | `,1234.5,` |
| Below detection limit | Use detection limit value | `50.0` |
| Instrument error | Leave empty, note in metadata | `,` |
| Systematic failure | Consider excluding entire well | Remove row |

**Maximum Missing Data**: Keep below 5% per column for reliable analysis

### Data Validation Checklist

Before uploading, verify your data meets these requirements:

#### ✅ File Format
- [ ] File has `.csv` extension
- [ ] Opens correctly in Excel or text editor
- [ ] Uses comma separators
- [ ] Has header row with column names

#### ✅ Required Columns
- [ ] `BG_lptA` column present and numeric
- [ ] `BT_lptA` column present and numeric  
- [ ] `BG_ldtD` column present and numeric
- [ ] `BT_ldtD` column present and numeric
- [ ] `OD_WT` column present and numeric
- [ ] `OD_tolC` column present and numeric
- [ ] `OD_SA` column present and numeric

#### ✅ Data Quality
- [ ] All values are positive numbers
- [ ] Missing data < 5% per column
- [ ] No obvious outliers or data entry errors
- [ ] Reasonable dynamic ranges for your assay

#### ✅ Optional Enhancements
- [ ] Well positions included if available
- [ ] Plate IDs for multi-plate datasets
- [ ] Control type annotations
- [ ] Compound identifiers for hit tracking

## Plate Layout Standards

### 96-Well Format

```
   1  2  3  4  5  6  7  8  9 10 11 12
A  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
B  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
C  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
D  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
E  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
F  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
G  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
H  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■  ■
```

- **Rows**: A-H (8 rows)
- **Columns**: 1-12 (12 columns)
- **Total Wells**: 96
- **Well Format**: `A01`, `B12`, `H07`

### 384-Well Format

```
   1  2  3  4  5  6 ... 22 23 24
A  ■  ■  ■  ■  ■  ■      ■  ■  ■
B  ■  ■  ■  ■  ■  ■      ■  ■  ■
C  ■  ■  ■  ■  ■  ■      ■  ■  ■
⋮  ⋮  ⋮  ⋮  ⋮  ⋮  ⋮      ⋮  ⋮  ⋮
P  ■  ■  ■  ■  ■  ■      ■  ■  ■
```

- **Rows**: A-P (16 rows)  
- **Columns**: 1-24 (24 columns)
- **Total Wells**: 384
- **Well Format**: `A01`, `P24`, `H13`

### Control Placement Recommendations

#### Negative Controls (DMSO)
- **96-well**: Columns 1 and 12 (16 wells total)
- **384-well**: Columns 1, 2, 23, 24 (64 wells total)

#### Positive Controls
- **96-well**: Wells H01-H06 (6 wells)
- **384-well**: Wells O01-O12 (12 wells)

## Common Data Preparation Workflows

### From Plate Reader Software

1. **Export from Instrument Software**
   - Choose CSV format with headers
   - Include well positions if available
   - Export raw values (not normalized)

2. **Combine Multiple Reads**
   ```python
   # Example Python code for combining files
   import pandas as pd
   
   bg_lptA = pd.read_csv('bg_lptA_readings.csv')
   bt_lptA = pd.read_csv('bt_lptA_readings.csv')
   # ... combine into single DataFrame
   ```

3. **Add Metadata**
   - Include plate IDs, dates, operators
   - Mark control wells appropriately
   - Add compound IDs if available

### From LIMS Systems

1. **Database Query**
   - Export with all required measurement columns
   - Include experimental metadata
   - Ensure consistent naming conventions

2. **Quality Check**
   - Verify no duplicate wells
   - Check for missing critical data
   - Validate numeric ranges

### From Excel Spreadsheets

1. **Standardize Format**
   - Ensure data is in tabular format (not pivot table)
   - Column headers in first row
   - No merged cells or complex formatting

2. **Save as CSV**
   - File → Save As → CSV (Comma delimited)
   - Choose UTF-8 encoding if available

## Advanced Data Structures

### Multi-Plate Datasets

For experiments spanning multiple plates:

```csv
PlateID,Well,Row,Col,BG_lptA,BT_lptA,BG_ldtD,BT_ldtD,OD_WT,OD_tolC,OD_SA
PLATE_001,A01,A,1,1052.3,2134.5,876.2,1567.8,0.48,0.42,0.45
PLATE_001,A02,A,2,987.1,2087.3,823.7,1489.2,0.51,0.38,0.47
PLATE_002,A01,A,1,1098.7,2201.3,891.5,1612.4,0.52,0.39,0.46
PLATE_002,A02,A,2,1023.4,2156.8,845.2,1578.9,0.49,0.41,0.48
```

### Time Series Data

For experiments with multiple time points:

```csv
PlateID,Well,TimePoint,Hours,BG_lptA,BT_lptA,BG_ldtD,BT_ldtD,OD_WT,OD_tolC,OD_SA
PLATE_001,A01,T0,0,1052.3,2134.5,876.2,1567.8,0.48,0.42,0.45
PLATE_001,A01,T1,4,1098.7,2201.3,891.5,1612.4,0.52,0.39,0.46
PLATE_001,A01,T2,8,1145.2,2278.6,923.8,1689.3,0.57,0.36,0.49
```

### Dose-Response Series

For concentration-response experiments:

```csv
PlateID,Well,Compound_ID,Concentration,Conc_Unit,BG_lptA,BT_lptA,BG_ldtD,BT_ldtD
PLATE_001,A01,CMPD_001,100,uM,245.7,2134.5,198.3,1567.8
PLATE_001,A02,CMPD_001,10,uM,567.2,2087.3,423.6,1489.2
PLATE_001,A03,CMPD_001,1,uM,892.4,2203.1,756.1,1623.4
```

## Troubleshooting Data Issues

### Common Problems and Solutions

#### Problem: "Invalid column names"
**Symptoms**: Error message about missing required columns
**Solutions**:
- Check column name spelling (case-sensitive)
- Remove extra spaces before/after names
- Use underscores, not spaces in names

#### Problem: "Non-numeric values detected"
**Symptoms**: Warning about text in measurement columns
**Solutions**:
```csv
# Wrong
BG_lptA
"Not_Detected"
"Error"
"<50"

# Right  
BG_lptA
50.0

50.0
```

#### Problem: "Too many missing values"
**Symptoms**: Analysis fails due to insufficient data
**Solutions**:
- Check that missing values are truly empty (not zero)
- Consider excluding wells/plates with systematic failures
- Verify instrument was working correctly

#### Problem: "Outlier values detected"
**Symptoms**: Warnings about extreme values
**Investigation**:
```python
# Check value ranges
print(data.describe())

# Look for data entry errors
print(data[data['BG_lptA'] > 10000])  # Check very high values
print(data[data['BG_lptA'] < 10])     # Check very low values
```

### Data Validation Tools

Bio Hit Finder includes built-in validation that checks:

- ✅ Required columns present
- ✅ Numeric data types
- ✅ Reasonable value ranges  
- ✅ Missing data percentages
- ✅ Duplicate well positions
- ✅ Plate layout consistency

## Best Practices Summary

1. **Start Simple**: Begin with just the required columns, add metadata later
2. **Validate Early**: Check data quality before full analysis
3. **Document Everything**: Include experimental context in metadata
4. **Be Consistent**: Use the same format across all experiments
5. **Keep Backups**: Save original raw data files
6. **Version Control**: Track changes to data processing workflows

---

**Ready to analyze your data? Continue to the [Analysis Guide](analysis_guide.md) for detailed analysis workflows.**