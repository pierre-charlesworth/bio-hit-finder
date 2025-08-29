# Analysis Guide

This comprehensive guide explains how to perform various types of analysis with Bio Hit Finder, from basic data processing to advanced statistical methods and quality control.

## Table of Contents

1. [Understanding the Calculations](#understanding-the-calculations)
2. [Basic Analysis Workflow](#basic-analysis-workflow)
3. [Hit Identification](#hit-identification)
4. [Quality Control Analysis](#quality-control-analysis)
5. [Statistical Methods](#statistical-methods)
6. [Multi-Plate Analysis](#multi-plate-analysis)
7. [Advanced Features](#advanced-features)

## Understanding the Calculations

### Core Metrics

Bio Hit Finder calculates several key metrics from your raw data:

#### 1. Reporter Ratios

**Purpose**: Normalize reporter activity by cell viability

**Formulas**:
```
Ratio_lptA = BG_lptA / BT_lptA
Ratio_ldtD = BG_ldtD / BT_ldtD
```

**Interpretation**:
- Lower ratios indicate potential inhibition of target genes
- Ratios account for differences in cell density/viability between wells
- Typical range: 0.3-0.8 for most assays

#### 2. OD Normalization

**Purpose**: Standardize growth measurements across the plate

**Formulas**:
```
OD_WT_norm = OD_WT / median(OD_WT)
OD_tolC_norm = OD_tolC / median(OD_tolC)  
OD_SA_norm = OD_SA / median(OD_SA)
```

**Interpretation**:
- Values around 1.0 indicate typical growth
- Values < 0.7 suggest growth inhibition
- Values > 1.3 may indicate enhanced growth

#### 3. Robust Z-Scores

**Purpose**: Statistical normalization for hit identification

**Formula**:
```
Z = (value - median) / (1.4826 × MAD)
where MAD = median(|X - median(X)|)
```

**Interpretation**:
- Z-scores follow approximately standard normal distribution
- |Z| > 2 indicates significant deviation (potential hits)
- |Z| > 3 indicates strong hits
- Robust to outliers (uses median/MAD instead of mean/SD)

#### 4. Viability Gating

**Purpose**: Filter out wells with insufficient cell viability

**Formula**:
```
viability_ok = BT >= f × median(BT)
default f = 0.3 (30% of median viability)
```

**Interpretation**:
- Only wells with adequate viability are considered for hit calling
- Prevents false positives from dead/dying cells
- Adjustable threshold based on assay requirements

## Basic Analysis Workflow

### Step 1: Data Upload and Validation

1. **Upload Your Data**
   - Navigate to the "Data Upload" tab
   - Click "Browse files" and select your CSV file
   - Wait for upload and initial validation

2. **Review Data Summary**
   - Check total wells and plates processed
   - Verify missing data percentages are acceptable (<5%)
   - Look for warnings about data quality issues

3. **Preview Raw Data**
   - Examine the first few rows to ensure correct formatting
   - Verify column names match expectations
   - Check value ranges are reasonable for your assay

### Step 2: Initial Analysis

1. **Automatic Processing**
   - Platform automatically calculates all core metrics
   - Processing typically takes 10-30 seconds for single plates
   - Progress bar shows calculation status

2. **Review Summary Statistics**
   - Go to "Summary" tab for overview
   - Check coefficient of variation (CV) for each metric
   - Look for any obvious data quality flags

### Step 3: Quality Assessment

1. **Check Overall Quality**
   - CV should be < 30% for most metrics
   - Missing data should be < 5% per column
   - Dynamic range (max/min) should be > 3-fold

2. **Spatial Analysis**
   - Go to "QC Report" tab
   - Look for edge effects or systematic patterns
   - Check heat maps for spatial artifacts

### Step 4: Hit Identification

1. **Set Thresholds**
   - Adjust Z-score cutoffs in sidebar (typically 2.0-3.0)
   - Set viability thresholds (typically 0.3)
   - Consider false discovery rate requirements

2. **Review Hit List**
   - Go to "Hits" tab for ranked results
   - Examine individual hit profiles
   - Cross-reference with known compounds if available

## Hit Identification

### Setting Appropriate Thresholds

#### Z-Score Cutoffs

| Threshold | Interpretation | False Positive Rate | Use Case |
|-----------|----------------|-------------------|----------|
| |Z| > 1.5 | Moderate deviation | ~13% | Exploratory screening |
| |Z| > 2.0 | Significant deviation | ~5% | Standard screening |
| |Z| > 2.5 | Strong deviation | ~1% | High-confidence hits |
| |Z| > 3.0 | Very strong deviation | ~0.3% | Ultra-stringent screening |

#### Viability Thresholds

| Threshold | Interpretation | Use Case |
|-----------|----------------|----------|
| BT > 0.1 × median | Very permissive | Early compound assessment |
| BT > 0.3 × median | Standard | Most screening applications |
| BT > 0.5 × median | Conservative | High-quality hit selection |
| BT > 0.7 × median | Very conservative | Cytostatic vs. cytotoxic |

### Hit Categories

The platform automatically categorizes hits based on their statistical properties:

#### Strong Hits
- **Criteria**: |Z| > 3.0 and viability gate passed
- **Interpretation**: High-confidence candidates
- **Next steps**: Immediate follow-up recommended

#### Moderate Hits  
- **Criteria**: 2.0 < |Z| < 3.0 and viability gate passed
- **Interpretation**: Potential candidates requiring validation
- **Next steps**: Secondary screening or dose-response

#### Borderline Hits
- **Criteria**: 1.5 < |Z| < 2.0 and viability gate passed  
- **Interpretation**: Weak activity, may be false positives
- **Next steps**: Consider for cherry-picking or deprioritize

#### Cytotoxic Compounds
- **Criteria**: Any |Z| but failed viability gate
- **Interpretation**: Growth inhibition rather than target-specific
- **Next steps**: May be of interest for cytotoxicity studies

### Dual-Target Analysis

For experiments targeting both lptA and ldtD:

#### Hit Combinations

| lptA Status | ldtD Status | Category | Interpretation |
|------------|-------------|----------|----------------|
| Hit | Hit | **Dual Hit** | Affects both targets |
| Hit | Non-hit | **lptA Specific** | Selective for lptA |
| Non-hit | Hit | **ldtD Specific** | Selective for ldtD |
| Non-hit | Non-hit | **Inactive** | No apparent activity |

#### Selectivity Analysis

```python
# Example selectivity calculation
selectivity_ratio = abs(Z_lptA) / abs(Z_ldtD)

# Interpretation:
# Ratio > 2: Selective for lptA
# Ratio < 0.5: Selective for ldtD  
# 0.5 ≤ Ratio ≤ 2: Dual activity
```

## Quality Control Analysis

### Edge Effect Detection

#### What are Edge Effects?

Edge effects are systematic differences between wells at the plate edges versus interior wells, commonly caused by:

- **Evaporation**: Liquid loss from edge wells during incubation
- **Temperature gradients**: Uneven heating in incubators
- **Handling artifacts**: Pipetting or washing inconsistencies
- **Media artifacts**: Uneven media distribution

#### Detection Methods

The platform uses several statistical tests:

1. **Spatial Correlation**: Correlation between well position and signal
2. **Edge vs. Interior**: T-test comparing edge and interior wells
3. **Row/Column Effects**: ANOVA testing for systematic row or column bias

#### Interpretation

| Edge Score | Warning Level | Interpretation | Action Required |
|------------|---------------|----------------|-----------------|
| 0.0 - 0.2 | None | No significant edge effects | None |
| 0.2 - 0.4 | Minor | Small edge effects detected | Monitor, consider noting in reports |
| 0.4 - 0.6 | Moderate | Clear edge effects present | Consider B-score correction |
| 0.6 - 1.0 | Severe | Strong spatial artifacts | B-score correction recommended |

### B-Score Correction

#### When to Use B-Scores

Use B-score correction when:
- Edge effects are detected (score > 0.4)
- Clear row or column patterns visible in heat maps
- Standard Z-scores show spatial clustering
- Multi-plate analysis with batch effects

#### How B-Scores Work

B-scores use median polish to remove systematic row and column effects:

1. **Median Polish**: Iteratively removes row and column medians
2. **Residual Calculation**: Remaining values after effect removal
3. **Robust Scaling**: Convert residuals to Z-score-like values

#### Interpreting B-Scores

- B-scores replace Z-scores when spatial correction is needed
- Hit calling uses same thresholds (typically |B| > 2.0)
- B-scores are more reliable in the presence of spatial artifacts
- Always compare heat maps before and after B-score correction

### Plate Quality Metrics

#### Overall Quality Assessment

| Metric | Good | Acceptable | Poor | Action |
|--------|------|------------|------|--------|
| **CV of Control Wells** | < 15% | 15-25% | > 25% | Repeat experiment |
| **Z-Factor** | > 0.5 | 0.2-0.5 | < 0.2 | Optimize assay |
| **Signal-to-Background** | > 3 | 2-3 | < 2 | Check reagents |
| **Missing Data Rate** | < 2% | 2-5% | > 5% | Check instruments |

#### Control Well Analysis

For plates with designated control wells:

```python
# Negative controls (DMSO)
neg_controls = data[data['Control_Type'] == 'Negative']
neg_cv = neg_controls['Ratio_lptA'].std() / neg_controls['Ratio_lptA'].mean()

# Positive controls
pos_controls = data[data['Control_Type'] == 'Positive']  
separation = pos_controls['Ratio_lptA'].mean() - neg_controls['Ratio_lptA'].mean()
```

## Statistical Methods

### Robust Statistics

#### Why Use Robust Methods?

- **Outlier Resistance**: Median and MAD less affected by extreme values
- **Non-Normal Distributions**: Many biological measurements are skewed
- **Small Sample Sizes**: More reliable with limited control wells
- **Reproducibility**: More consistent results across experiments

#### Robust vs. Classical Statistics

| Method | Classical | Robust | When to Use |
|--------|-----------|---------|-------------|
| **Center** | Mean (μ) | Median | Always for biological data |
| **Spread** | Standard Deviation (σ) | MAD × 1.4826 | When outliers present |
| **Normalization** | (x - μ) / σ | (x - median) / (1.4826 × MAD) | Standard for screening |

### Statistical Significance

#### P-Value Interpretation

When comparing groups or treatments:

| P-Value | Interpretation | Action |
|---------|----------------|--------|
| p < 0.001 | Highly significant | Strong evidence for effect |
| p < 0.01 | Significant | Good evidence for effect |
| p < 0.05 | Marginally significant | Moderate evidence |
| p > 0.05 | Not significant | Insufficient evidence |

#### Multiple Testing Correction

For screens with many comparisons, consider:

- **Bonferroni Correction**: Divide α by number of tests
- **FDR Control**: Use Benjamini-Hochberg procedure
- **Built-in Correction**: Platform can apply FDR correction to hit lists

### Power Analysis

#### Sample Size Considerations

For adequate statistical power:

| Effect Size | Minimum Wells per Group | Recommended |
|-------------|------------------------|-------------|
| Large (>2-fold) | 8 | 12 |
| Medium (1.5-fold) | 16 | 24 |
| Small (<1.5-fold) | 32 | 48 |

## Multi-Plate Analysis

### Batch Effect Assessment

#### Common Sources of Batch Effects

- **Day-to-day variation**: Different experiment dates
- **Operator differences**: Different personnel
- **Reagent lots**: Different batches of reagents
- **Instrument drift**: Changes in instrument performance

#### Detection Methods

1. **Principal Component Analysis**: Look for clustering by batch
2. **Box Plots by Plate**: Visual inspection of plate-to-plate variation
3. **Statistical Tests**: ANOVA testing for plate effects

#### Correction Strategies

1. **Plate-Wise Normalization**: Calculate Z-scores within each plate
2. **Empirical Bayes**: Use ComBat or similar methods
3. **Mixed-Effect Models**: Account for plate as random effect

### Aggregating Results

#### Hit Confirmation Across Plates

For compounds tested on multiple plates:

```python
# Reproducibility analysis
compound_summary = data.groupby('Compound_ID').agg({
    'Z_lptA': ['mean', 'std', 'count'],
    'Hit_Status': 'mean'  # Fraction of plates showing hit
})

# Require hits in >50% of plates
confirmed_hits = compound_summary[
    compound_summary['Hit_Status']['mean'] > 0.5
]
```

## Advanced Features

### Custom Thresholds

#### Setting Experiment-Specific Cutoffs

Based on your specific requirements:

```python
# Conservative approach (low false positive rate)
z_threshold = 3.0
viability_threshold = 0.5

# Exploratory approach (higher sensitivity)
z_threshold = 1.5
viability_threshold = 0.2

# Balanced approach (standard screening)
z_threshold = 2.0
viability_threshold = 0.3
```

### Integration with External Tools

#### Exporting for Further Analysis

The platform can export data in various formats:

- **CSV**: For Excel or statistical software
- **R-compatible**: For advanced statistical analysis
- **Python pickle**: For machine learning workflows
- **GraphPad Prism**: For publication-quality graphs

#### API Access

For programmatic analysis:

```python
import bio_hit_finder as bhf

# Load and process data
processor = bhf.PlateProcessor()
results = processor.process_file('your_data.csv')

# Custom analysis
hits = results[results['Z_lptA'].abs() > 2.0]
```

## Troubleshooting Analysis Issues

### Common Problems

#### Problem: "No hits found"
**Possible Causes**:
- Thresholds too stringent
- Poor assay quality
- Lack of active compounds
- Data quality issues

**Solutions**:
- Lower Z-score threshold (try 1.5)
- Check positive controls
- Verify data format and ranges
- Review QC metrics

#### Problem: "Too many hits"
**Possible Causes**:
- Thresholds too permissive
- Edge effects or spatial artifacts
- Assay optimization needed
- Cytotoxic compound library

**Solutions**:
- Raise Z-score threshold (try 2.5 or 3.0)
- Apply B-score correction
- Strengthen viability gating
- Check for systematic artifacts

#### Problem: "Inconsistent results across plates"
**Possible Causes**:
- Batch effects
- Reagent variability
- Instrument drift
- Different operators

**Solutions**:
- Use plate-wise normalization
- Include more control wells
- Standardize protocols
- Apply batch correction methods

### Performance Optimization

#### Large Dataset Handling

For experiments with >1000 plates:

1. **Use Polars Backend**: Faster than Pandas for large data
2. **Chunk Processing**: Process plates in batches
3. **Parallel Computing**: Use multiple CPU cores
4. **Memory Management**: Monitor RAM usage

#### Speed Improvements

```python
# Enable parallel processing
processor = PlateProcessor(n_jobs=-1)

# Use faster backend
processor = PlateProcessor(backend='polars')

# Reduce memory usage
processor = PlateProcessor(low_memory=True)
```

---

**Ready to dive deeper? Continue to the [Interpretation Guide](interpretation_guide.md) for detailed guidance on understanding and acting on your results.**