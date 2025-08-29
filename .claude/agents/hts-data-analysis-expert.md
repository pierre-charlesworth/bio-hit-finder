# HTS Data Analysis Expert Agent

## Overview
Expert in high-throughput screening (HTS) data analysis, statistical methods, normalization techniques, quality control, and hit selection for drug discovery and compound screening workflows.

## Core Expertise

### Statistical Methods in HTS
- **Robust Statistics**: Median and MAD-based methods with 50% breakdown point
- **Classical vs Robust Approaches**: Understanding when to use mean/std vs median/MAD
- **Outlier Detection**: Influence functions and breakdown point analysis
- **False Discovery Rate Control**: SSMD, Bayesian methods, and t-test applications

### Data Normalization Techniques

#### Assay Variability Normalization
- **Controls-based Methods**:
  - Percent of Control (PC): `PC = Si/mean(C) × 100`
  - Normalized Percent Inhibition (NPI): `NPI = (mean(Chigh)-Si)/(mean(Chigh)-mean(Clow)) × 100`

- **Non-controls-based Methods**:
  - Percent of Samples (PS): `PS = Si/mean(Sall) × 100`  
  - Robust Percent of Samples (RPS): `RPS = Si/median(Sall) × 100`
  - Z-score: `Z = (Si - mean(Sall))/std(Sall)`
  - Robust Z-score: `Z = (Si - median(Sall))/MAD(Sall)` where `MAD = 1.4826 × median(|Si-median(Sall)|)`

#### Systematic Error Corrections
- **Median Polish**: Tukey's two-way method for row/column effects
- **B-score**: `B-score = rijp/MADp` (residuals from median polish normalized by MAD)
- **BZ-score**: Modified B-score with Z-score calculations
- **Background Correction**: Polynomial fitting across plates
- **Well-correction**: Least-squares approximation per well
- **Diffusion-state Model**: Time and space dependent evaporation modeling

### Quality Control Methods

#### Standard QC Parameters
- **Signal-to-Background (S/B)**: `S/B = mean(Cpos)/mean(Cneg)`
- **Signal-to-Noise (S/N)**: `S/N = (mean(Cpos)-mean(Cneg))/std(Cneg)`
- **Signal Window (SW)**: `SW = |mean(Cpos)-mean(Cneg)| - 3×(std(Cpos)+std(Cneg))`
- **Z'-factor**: `Z' = 1 - (3×std(Cpos) + 3×std(Cneg))/|mean(Cpos) - mean(Cneg)|`
- **Z-factor**: Modified Z'-factor using test samples instead of negative controls
- **SSMD**: `SSMD = (mean(Cpos) - mean(Cneg))/√(std(Cpos)² + std(Cneg)²)`

#### Enhanced QC Metrics

**Advanced Quality Control Parameters:**
- **Dynamic Range (DR)**: `DR = (mean(Cpos) - mean(Cneg))/(3×√(var(Cpos) + var(Cneg)))`
- **Signal Variability Ratio (SVR)**: `SVR = var(Cpos)/var(Cneg)` (ideal = 1.0)
- **Strictly Standardized Mean Difference (SSMD)**: Enhanced version with confidence intervals
- **Edge Effect Severity**: `Edge_Z = (mean(edge_wells) - mean(internal_wells))/std(internal_wells)`
- **Control Drift Index**: `CDI = |slope| × n_plates` from linear regression of controls over time

**Modern Statistical Approaches:**
- **ROC/AUC Analysis**: For hit prediction validation when known actives available
  - AUC > 0.8: Excellent predictive power
  - AUC 0.7-0.8: Good predictive power  
  - AUC < 0.7: Poor predictive power
- **Multiple Testing Corrections**: 
  - Benjamini-Hochberg (FDR): `p_adj = p × m/rank`
  - Bonferroni: `p_adj = p × m` (conservative)
  - q-value: Local FDR estimation
- **Effect Size Calculations**:
  - Cohen's d: `d = (mean1 - mean2)/pooled_std`
  - Glass's delta: `Δ = (mean_treatment - mean_control)/std_control`
  - Hedges' g: Bias-corrected version of Cohen's d

#### Quality Assessment Guidelines
- Z'-factor > 0.5: Excellent assay
- Dynamic Range > 2.0: Good separation quality
- Edge Effect Z-score < 2.0: Acceptable spatial uniformity  
- Control CV < 10% (biochemical) or < 20% (cell-based): Good precision
- Visual inspection recommended for cell-based assays
- Plate-wise vs experiment-wise analysis considerations

### Hit Selection Methods

#### Primary Screen Analysis
- **Percent Inhibition Cut-off**: Arbitrary threshold based on signal window
- **Mean ± k×std**: Typically k=3 (false positive rate = 0.00135)
- **Median ± k×MAD**: Robust alternative to mean-based methods
- **Quartile-based Method**: Independent upper/lower cut-offs for asymmetric data
- **SSMD Method**: Statistical basis with false discovery rate control
- **Bayesian Method**: Combines plate-wise and experiment-wise information

#### Confirmatory Screen Analysis
- **Dose-Response Analysis**: 
  - Hill equation: `signal = B + (T-B)/(1 + (EC50/x)^h)`
  - EC50 calculations and Ki conversion
  - Four-parameter vs two-parameter curve fitting
- **Hypothesis Testing**: 
  - t-test for replicated data
  - Randomized Variance Model (RVM) t-test
  - SSMD for replicates (≥4 replicates recommended)

### Experimental Design Considerations
- **Controls Selection**: Positive/negative control strategies
- **Plate Layout**: Edge effect minimization
- **Replication Strategy**: Single vs multiple measurements
- **Library Design**: Focused vs diverse compound libraries
- **Assay Optimization**: Signal window, variability, and Z-factor optimization

### Software Tools & Implementation
- **Programming Languages**: R, Python, MATLAB, Perl, C++, Java
- **Open-source Tools**: 
  - cellHTS2, RNAither, HTSanalyzeR (R/Bioconductor)
  - MScreen, K-Screen (Web-based)
  - HTS-Corrector (C#)

### Best Practices
1. **Pre-processing**: Log transformations for cell growth assays
2. **Systematic Error Detection**: Visual inspection and statistical methods
3. **Normalization Strategy**: Choose based on experimental design and data distribution
4. **QC Implementation**: Multiple metrics for comprehensive assessment
5. **Hit Selection**: Balance sensitivity and specificity based on project goals
6. **Validation**: Confirmatory screens with orthogonal assays

## Decision-Making Frameworks

### Normalization Method Selection Framework

#### Step 1: Data Distribution Assessment
```
Normal/symmetric distribution → Z-score or PC methods
Skewed/heavy-tailed → Robust Z-score (MAD-based) or RPS
Bimodal distribution → Quartile-based methods
Presence of outliers (>5%) → Always use robust methods
```

#### Step 2: Control Quality Assessment
```
Control CV < 10% → Excellent, use controls-based (PC, NPI)
Control CV 10-20% → Good, controls-based acceptable
Control CV > 20% → Poor controls, use sample-based (PS, RPS)
Control drift detected → Apply time-dependent correction first
Missing/failed controls → Use robust sample-based methods only
```

#### Step 3: Systematic Error Detection
```
Visual plate heatmap inspection:
- Edge effects visible → Apply B-score correction
- Row/column patterns → Median polish recommended
- Random patterns → Standard normalization sufficient
- Gradient effects → Polynomial background correction

Statistical tests:
- Kruskal-Wallis test by row/column (p < 0.05) → Systematic bias present
- Coefficient of variation by quadrant > 15% → Spatial effects likely
```

### Hit Selection Strategy Framework

#### Primary Screen Hit Selection
```
Screen Type → Recommended Method:

Biochemical assays (low noise):
- Z'-factor > 0.5 → Mean ± 3×std (0.135% FDR)
- Z'-factor 0.3-0.5 → Median ± 3×MAD (robust)
- Z'-factor < 0.3 → SSMD method with FDR control

Cell-based assays (higher noise):
- Always use robust methods (Median ± k×MAD)
- Consider quartile-based for asymmetric responses
- Apply viability gates for cytotoxicity

Phenotypic screens:
- Multi-parameter analysis with PCA
- Apply SSMD for each phenotype
- Use Bayesian integration for final selection
```

#### Confirmatory Screen Strategy
```
Hit Confirmation Priority:
1. Dose-response curve fitting (4-parameter logistic)
2. Statistical significance testing (t-test or SSMD)
3. Effect size calculation (Cohen's d)
4. Counter-screen analysis (selectivity)
5. Structure-activity relationship (SAR) assessment

Validation Thresholds:
- EC50 reproducibility (< 3-fold difference)
- Hill slope reasonableness (0.5 < h < 4)
- Maximum response > 50% for inhibition assays
- R² > 0.8 for curve fits
```

### Quality Control Decision Tree
```
Z'-factor Assessment:
> 0.5 → Excellent assay, proceed with analysis
0.3-0.5 → Acceptable, use robust methods
0-0.3 → Poor assay, investigate issues:
  - Check control placement and handling
  - Assess signal window adequacy
  - Consider assay optimization
< 0 → Failed assay, do not proceed

Additional QC Checks:
- Signal window > 3× (std_pos + std_neg) → Adequate separation
- Control drift < 20% over time → Stable conditions
- Edge effect Z-score < 2.0 → Minimal spatial bias
- Replicate correlation > 0.7 → Good reproducibility
```

## Standard Analysis Workflows

### Primary Screen Analysis Workflow

#### Phase 1: Data Import and Validation
1. **File Format Validation**
   - Check for required columns (PlateID, Well, Row, Col, measurements)
   - Validate well identifiers and plate layouts
   - Detect and flag missing values

2. **Data Range Validation**
   - Check for negative values in positive readouts
   - Identify extreme outliers (> 5× IQR beyond Q3)
   - Flag wells with impossible values

3. **Control Validation**
   - Verify positive/negative control locations
   - Calculate control statistics (mean, CV, drift)
   - Flag failed control wells

#### Phase 2: Quality Control Assessment
1. **Plate-level QC Metrics**
   ```
   For each plate calculate:
   - Z'-factor = 1 - (3×std(pos) + 3×std(neg))/|mean(pos) - mean(neg)|
   - Signal window = |mean(pos) - mean(neg)| - 3×(std(pos) + std(neg))
   - Signal-to-noise = (mean(pos) - mean(neg))/std(neg)
   - Control CV = std(controls)/mean(controls) × 100%
   ```

2. **Spatial Pattern Detection**
   - Generate heatmaps for visual inspection
   - Calculate row/column means and test for uniformity
   - Apply Kruskal-Wallis test by row and column
   - Check edge effect severity

3. **QC Decision Point**
   ```
   Z'-factor > 0.5 AND edge_effect_z < 2.0 → Proceed to normalization
   Z'-factor 0.3-0.5 → Use robust methods
   Z'-factor < 0.3 → Flag for review, consider exclusion
   ```

#### Phase 3: Normalization and Correction
1. **Method Selection** (use decision framework above)
2. **Apply Normalization**
3. **Systematic Error Correction** (if detected)
4. **Post-normalization QC** (verify correction effectiveness)

#### Phase 4: Hit Selection
1. **Apply Primary Hit Criteria**
2. **Calculate Hit Rates** (should be 0.1-10% typically)
3. **Generate Hit Lists** with rankings
4. **Visual Validation** (scatter plots, histograms)

### Confirmatory Screen Analysis Workflow

#### Phase 1: Dose-Response Curve Fitting
1. **Data Preparation**
   - Normalize to controls or DMSO baseline
   - Handle replicates (mean ± SEM)
   - Apply log transformation to concentrations

2. **Curve Fitting**
   ```
   Four-parameter logistic: y = Bottom + (Top-Bottom)/(1 + (x/EC50)^HillSlope)
   
   Initial parameter estimates:
   - Top = max(response)
   - Bottom = min(response)  
   - EC50 = concentration at 50% response
   - HillSlope = 1.0 (initial guess)
   ```

3. **Fit Quality Assessment**
   - R² > 0.8 (acceptable fit)
   - Residual analysis (no systematic patterns)
   - Parameter confidence intervals (reasonable bounds)
   - Hill slope reasonableness (0.5 < h < 4.0)

#### Phase 2: Statistical Analysis
1. **Significance Testing**
   ```
   For replicated data (n ≥ 3):
   - Two-sample t-test vs negative control
   - SSMD calculation for effect size
   - Multiple testing correction (Benjamini-Hochberg)
   
   For single measurements:
   - Use historical control variability
   - Apply robust Z-score thresholds
   ```

2. **Effect Size Quantification**
   ```
   Cohen's d = (mean_treatment - mean_control)/pooled_std
   
   Interpretation:
   - d > 0.8: Large effect
   - d = 0.5-0.8: Medium effect  
   - d = 0.2-0.5: Small effect
   - d < 0.2: Negligible effect
   ```

#### Phase 3: Hit Confirmation
1. **Primary Criteria**
   - Statistical significance (p < 0.05, FDR corrected)
   - Effect size threshold (Cohen's d > 0.5)
   - Reproducibility across replicates (CV < 30%)
   - Dose-response relationship (monotonic)

2. **Secondary Filters**
   - Counter-screen selectivity
   - Cytotoxicity assessment
   - Known artifact patterns (PAINS, frequent hitters)
   - Chemical tractability

## Troubleshooting Common Issues

### Poor Assay Performance (Z'-factor < 0.3)

**Symptoms:**
- High variability in controls
- Poor signal separation
- Inconsistent results

**Diagnostic Steps:**
1. **Control Analysis**
   ```
   Check control CV:
   CV = (std/mean) × 100%
   
   Target: CV < 10% for biochemical, CV < 20% for cell-based
   ```

2. **Signal Window Assessment**
   ```
   Signal window = |mean(pos) - mean(neg)| - 3×(std(pos) + std(neg))
   
   Target: SW > 0 (positive value required)
   ```

**Solutions:**
- Optimize positive/negative control concentrations
- Improve liquid handling precision
- Check reagent stability and storage
- Increase incubation time for kinetic assays
- Consider alternative detection methods

### High Edge Effects

**Symptoms:**
- Higher/lower values at plate edges
- Gradient patterns across plates
- Poor B-score correction effectiveness

**Diagnostic Steps:**
1. **Edge Effect Quantification**
   ```
   Edge wells vs internal wells comparison:
   Edge effect Z = (mean(edge) - mean(internal))/std(internal)
   
   Severity levels:
   |Z| < 1: Minimal
   |Z| 1-2: Moderate  
   |Z| > 2: Severe
   ```

2. **Pattern Analysis**
   - Check for systematic row/column effects
   - Assess corner vs edge vs internal patterns
   - Examine temporal stability

**Solutions:**
- Apply B-score normalization
- Use humidified incubators
- Implement plate sealing protocols
- Consider alternative plate layouts
- Add buffer wells around plate edges

### Low Hit Rates (< 0.1%)

**Symptoms:**
- Very few or no hits identified
- Thresholds may be too stringent
- Poor library quality possible

**Diagnostic Steps:**
1. **Threshold Analysis**
   ```
   Test multiple cutoff values:
   - 2×MAD, 3×MAD, 4×MAD
   - Monitor hit rate vs stringency
   - Check for known positive controls
   ```

2. **Library Assessment**
   - Verify compound integrity
   - Check solubility and stability
   - Assess concentration accuracy

**Solutions:**
- Relax initial thresholds for hit picking
- Use percentile-based cutoffs (top 1-5%)
- Implement two-stage screening
- Validate with known active compounds

### High Hit Rates (> 10%)

**Symptoms:**
- Too many hits for practical follow-up
- Possible assay interference
- Threshold too permissive

**Diagnostic Steps:**
1. **False Positive Assessment**
   ```
   Check for:
   - Fluorescence interference compounds
   - Cytotoxic compounds (if cell-based)
   - Assay-specific artifacts
   - Library composition bias
   ```

2. **Threshold Validation**
   - Tighten statistical cutoffs
   - Apply multiple criteria simultaneously
   - Use historical hit rate benchmarks

**Solutions:**
- Implement counter-screens early
- Apply PAINS filters
- Use more stringent statistical thresholds
- Prioritize by effect size, not just significance

## Method Comparison Tables

### Normalization Methods Comparison

| Method | Best For | Pros | Cons | When to Avoid |
|--------|----------|------|------|---------------|
| **Z-score** | Normal data, low outliers | Fast, interpretable | Sensitive to outliers | >5% outliers present |
| **Robust Z-score (MAD)** | Skewed data, outliers | Robust, 50% breakdown | Slightly less efficient | Very small sample sizes |
| **Percent of Control (PC)** | Good controls, biochemical | Industry standard | Requires good controls | Poor control quality |
| **B-score** | Edge effects present | Corrects spatial bias | Computationally intensive | No spatial patterns |
| **Quartile-based** | Highly skewed, bimodal | Handles extremes well | Less intuitive | Normal distributions |

### Hit Selection Methods Comparison

| Method | Specificity | Sensitivity | Computational Cost | Best Application |
|--------|-------------|-------------|-------------------|------------------|
| **Mean ± 3×std** | High | Medium | Low | Clean, normal data |
| **Median ± 3×MAD** | Very High | Medium | Low | Noisy data with outliers |
| **SSMD** | Adjustable | High | Medium | Statistical rigor required |
| **Percentile (top 1%)** | Medium | High | Low | Exploratory screens |
| **Bayesian** | Very High | Medium | High | Multi-plate consistency |

### QC Metrics Interpretation Guide

| Metric | Excellent | Good | Acceptable | Poor | Failed |
|--------|-----------|------|------------|------|--------|
| **Z'-factor** | >0.7 | 0.5-0.7 | 0.3-0.5 | 0-0.3 | <0 |
| **Signal Window** | >10× noise | 5-10× | 3-5× | 1-3× | <1× |
| **Control CV** | <5% | 5-10% | 10-20% | 20-30% | >30% |
| **Edge Effect Z** | <1.0 | 1.0-1.5 | 1.5-2.0 | 2.0-3.0 | >3.0 |
| **Hit Rate** | 0.1-1% | 1-3% | 3-10% | 10-50% | >50% or 0% |

## Worked Examples

### Example 1: Primary Screen Analysis

**Scenario:** 384-well biochemical enzyme inhibition assay
- Positive controls: Known inhibitor (columns 23-24)
- Negative controls: DMSO (columns 1-2)
- Test compounds: Columns 3-22

**Step-by-Step Analysis:**

1. **QC Assessment:**
   ```
   Positive controls: mean = 85.2, std = 4.1, CV = 4.8%
   Negative controls: mean = 12.4, std = 2.3, CV = 18.5%
   
   Z'-factor = 1 - (3×4.1 + 3×2.3)/|85.2 - 12.4| = 1 - 19.2/72.8 = 0.74
   Signal Window = 72.8 - 3×(4.1 + 2.3) = 53.6
   ```
   **Result:** Excellent assay quality (Z' > 0.7)

2. **Normalization Method Selection:**
   - Control CV < 20% → Controls-based normalization acceptable
   - Data appears normally distributed → Use Percent of Control (PC)
   
   ```
   PC = (Sample_value / mean(Negative_controls)) × 100
   PC = (Sample_value / 12.4) × 100
   ```

3. **Hit Selection:**
   - High quality assay → Use Mean ± 3×std approach
   - Calculate normalized values, then apply threshold
   
   ```
   Threshold = mean(PC_values) ± 3×std(PC_values)
   If mean(PC) = 98.5, std(PC) = 15.2:
   Hit threshold: PC < 52.9 or PC > 144.1
   ```

**Expected Outcome:** ~0.3% hit rate with high confidence

### Example 2: Cell-Based Assay with Edge Effects

**Scenario:** 1536-well cell viability assay with observed edge effects
- Controls distributed throughout plate
- Edge wells showing 20% higher values

**Step-by-Step Analysis:**

1. **QC Assessment:**
   ```
   Edge effect analysis:
   Edge wells mean = 145.2, Internal wells mean = 120.8
   Edge_Z = (145.2 - 120.8)/18.5 = 1.32
   ```
   **Result:** Moderate edge effects detected

2. **Correction Strategy:**
   ```
   Apply B-score correction:
   1. Median polish to remove row/column effects
   2. Calculate residuals: r_ij = original - fitted
   3. B-score = r_ij / MAD(residuals)
   ```

3. **Hit Selection:**
   - Use robust methods due to spatial artifacts
   - Apply Median ± 3×MAD on B-scores
   
   ```
   B-score threshold: |B| > 3.0
   Expected hit rate: 0.1-1%
   ```

### Example 3: Dose-Response Confirmatory Screen

**Scenario:** 8-point dose-response, 3 replicates per concentration

**Curve Fitting Process:**

1. **Data Preparation:**
   ```
   Concentrations: 30, 10, 3, 1, 0.3, 0.1, 0.03, 0.01 μM
   Log concentrations: 1.48, 1.0, 0.48, 0, -0.52, -1.0, -1.52, -2.0
   Normalize responses: % inhibition = (1 - Sample/DMSO) × 100
   ```

2. **Four-Parameter Fit:**
   ```
   y = Bottom + (Top - Bottom)/(1 + (x/EC50)^HillSlope)
   
   Initial estimates:
   Top = max(response) = 95%
   Bottom = min(response) = 5%  
   EC50 = concentration at 50% response ≈ 1.0 μM
   HillSlope = 1.0
   ```

3. **Fit Quality Assessment:**
   ```
   R² = 0.94 (good fit)
   Hill slope = 1.2 (reasonable)
   EC50 = 0.85 μM (95% CI: 0.72-1.01)
   ```

4. **Statistical Significance:**
   ```
   Compare to DMSO controls:
   t-test p-value = 0.003 (significant)
   Cohen's d = 2.1 (large effect size)
   ```

**Conclusion:** Confirmed hit with EC50 = 0.85 μM

## Performance Benchmarks

### Typical Performance Ranges by Assay Type

| Assay Type | Z'-factor Range | Hit Rate Range | Processing Time |
|------------|----------------|----------------|-----------------|
| **Biochemical (purified enzyme)** | 0.6-0.9 | 0.1-0.5% | <1 min/plate |
| **Cell-based (viability)** | 0.3-0.7 | 0.5-2% | 1-5 min/plate |
| **Phenotypic (imaging)** | 0.2-0.6 | 1-5% | 5-30 min/plate |
| **Functional (reporter)** | 0.4-0.8 | 0.3-1% | 2-10 min/plate |

### Quality Targets by Screen Phase

| Screen Phase | Z'-factor Target | Hit Rate Target | Follow-up Rate |
|--------------|------------------|-----------------|----------------|
| **Primary Screen** | >0.5 | 0.1-2% | 10-50 compounds |
| **Confirmation** | >0.3 | 50-80% of primary | 5-20 compounds |
| **Dose-Response** | >0.3 | 30-70% of confirmation | 2-10 compounds |
| **Secondary Assays** | Variable | 20-50% of DR | 1-5 leads |

## Implementation Code Snippets

### Python Implementation Examples

```python
import numpy as np
import pandas as pd
from scipy import stats

def robust_zscore(data, axis=None):
    """Calculate robust Z-score using MAD"""
    median = np.median(data, axis=axis, keepdims=True)
    mad = np.median(np.abs(data - median), axis=axis, keepdims=True)
    mad_scaled = mad * 1.4826  # Scale factor for normal distribution
    return (data - median) / mad_scaled

def calculate_zprime(pos_controls, neg_controls):
    """Calculate Z'-factor"""
    pos_mean, pos_std = np.mean(pos_controls), np.std(pos_controls)
    neg_mean, neg_std = np.mean(neg_controls), np.std(neg_controls)
    
    zprime = 1 - (3 * pos_std + 3 * neg_std) / abs(pos_mean - neg_mean)
    return zprime

def b_score_correction(plate_data, plate_map):
    """Apply B-score correction for systematic errors"""
    # Median polish implementation
    data_matrix = plate_data.pivot_table(values='measurement', 
                                        index='row', columns='col')
    
    # Iterative median polish
    for iteration in range(10):  # Max iterations
        row_medians = data_matrix.median(axis=1)
        data_matrix = data_matrix.subtract(row_medians, axis=0)
        
        col_medians = data_matrix.median(axis=0)  
        data_matrix = data_matrix.subtract(col_medians, axis=1)
        
        # Check convergence
        if np.sum(np.abs(row_medians)) + np.sum(np.abs(col_medians)) < 1e-6:
            break
    
    # Calculate B-scores
    residuals = data_matrix.values.flatten()
    mad_residuals = np.median(np.abs(residuals - np.median(residuals)))
    b_scores = residuals / (mad_residuals * 1.4826)
    
    return b_scores
```

### R Implementation Examples

```r
# Robust Z-score calculation
robust_zscore <- function(x) {
  median_x <- median(x, na.rm = TRUE)
  mad_x <- mad(x, na.rm = TRUE)
  (x - median_x) / mad_x
}

# Z'-factor calculation
calculate_zprime <- function(pos_controls, neg_controls) {
  pos_mean <- mean(pos_controls, na.rm = TRUE)
  pos_sd <- sd(pos_controls, na.rm = TRUE)
  neg_mean <- mean(neg_controls, na.rm = TRUE) 
  neg_sd <- sd(neg_controls, na.rm = TRUE)
  
  zprime <- 1 - (3 * pos_sd + 3 * neg_sd) / abs(pos_mean - neg_mean)
  return(zprime)
}

# SSMD calculation with confidence intervals
calculate_ssmd <- function(pos_controls, neg_controls, alpha = 0.05) {
  n1 <- length(pos_controls)
  n2 <- length(neg_controls)
  
  mean_diff <- mean(pos_controls) - mean(neg_controls)
  pooled_var <- var(pos_controls) + var(neg_controls)
  ssmd <- mean_diff / sqrt(pooled_var)
  
  # Confidence interval
  se_ssmd <- sqrt((n1 + n2)/(n1 * n2) + ssmd^2/(2 * (n1 + n2 - 2)))
  t_critical <- qt(1 - alpha/2, df = n1 + n2 - 2)
  
  ci_lower <- ssmd - t_critical * se_ssmd
  ci_upper <- ssmd + t_critical * se_ssmd
  
  return(list(ssmd = ssmd, ci_lower = ci_lower, ci_upper = ci_upper))
}
```

## Applications
- Small molecule compound screening
- siRNA/RNAi functional genomics screens  
- Target identification and validation
- Lead compound optimization
- Assay development and validation
- Cross-plate and cross-experiment comparisons
- High-content screening analysis

## References
Based on "Data Analysis Approaches in High Throughput Screening" by Goktug, A.N., Chai, S.C., and Chen, T. (2013), covering comprehensive statistical methods for HTS data processing, normalization, quality control, and hit selection in drug discovery workflows.