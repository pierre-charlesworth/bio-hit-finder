# Hit Scoring Methodology

## Overview

The bio-hit-finder platform implements a **3-stage funnel pipeline** for identifying compounds that activate envelope stress reporters in bacterial screens. The pipeline progressively filters hits through:

1. **Stage 1: Reporter Hit Detection** - Statistical analysis of dual-reporter activation
2. **Stage 2: Vitality Hit Detection** - Growth pattern analysis across strains
3. **Stage 3: Platform Hit Integration** - Combined hit calling with confidence scoring

**Key Principle**: All statistical normalization (median, MAD) is calculated **per-plate** to account for plate-to-plate variability.

## Biological Context

### Dual-Readout Reporters
- **lptA**: σE-regulated reporter (outer membrane stress)
- **ldtD**: Cpx-regulated reporter (inner membrane/periplasmic stress)

### Reporter Ratio Calculation
```
Ratio = BG (BetaGlo ATP) / BT (BacTiter Growth)
```
This normalizes reporter activation (ATP production) by bacterial growth.

### Strain Panel
- **WT strain**: Wild-type reference
- **tolC strain**: Efflux-deficient (compound accumulation)
- **SA strain**: Suppressor-activated (stress pathway activated)

---

## Stage 1: Reporter Hit Detection

### Formula: Robust Z-Score (MAD-based)

**Per-plate calculation** (CRITICAL requirement):

```
Z = (Ratio - Median_plate) / (1.4826 × MAD_plate)

where:
  Ratio = well's reporter ratio value
  Median_plate = median of all ratios on that plate
  MAD_plate = Median Absolute Deviation on that plate
  1.4826 = scaling factor to approximate σ
```

### MAD Calculation
```
MAD = median(|Ratio_i - Median_plate|)
```

### Hit Criteria
A well is called a **Reporter Hit** if:
```
Z_lptA ≥ 2.0  OR  Z_ldtD ≥ 2.0
```

### Viability QC Warning (NOT a filter)
- `PassViab` column indicates if ATP levels suggest viable cells
- **Important**: Low viability adds a warning flag (`Stage1_ViabilityWarning`) but does NOT prevent hit calling
- Rationale: Some compounds may affect ATP while still inducing reporter activation

### Implementation Reference
**File**: `backend/analytics/multi_stage_hits.py`
**Function**: `stage1_reporter_hits()` (lines 84-143)

**File**: `backend/core/calculations.py`
**Function**: `calculate_robust_zscore_columns()` (lines 156-243)
- Uses `per_plate=True` to ensure grouping by PlateID
- Calculates median and MAD separately for each plate

---

## Stage 2: Vitality Hit Detection

### Growth Pattern Analysis

Vitality hits identify compounds that selectively affect growth based on strain genotype.

### Normalized Growth Calculation
For each strain (WT, tolC, SA):
```
Strain% = OD_strain / OD_WT
```

### Hit Criteria
A well is called a **Vitality Hit** if:
```
tolC% ≤ 0.8  AND  WT% > 0.8  AND  SA% > 0.8
```

**Biological Interpretation**:
- Compound accumulates in efflux-deficient strain (tolC)
- Does not kill wild-type or suppressor-activated strains
- Suggests envelope stress mechanism

### Implementation Reference
**File**: `backend/analytics/vitality_analysis.py`
**Function**: `detect_vitality_hits()` (lines 1-150)

---

## Stage 3: Platform Hit Integration

### Combined Hit Calling

The final platform hits combine reporter and vitality signals:

```python
Stage3_PlatformHit = Stage1_ReporterHit AND Stage2_VitalityHit
```

### Hit Type Classification
- **"dual"**: Both lptA and ldtD reporters activated (Z ≥ 2.0)
- **"lptA"**: Only lptA activated (σE-specific)
- **"ldtD"**: Only ldtD activated (Cpx-specific)

### Confidence Scoring
```
Confidence = (max(Z_lptA, Z_ldtD) - threshold) / threshold
```

Higher Z-scores above threshold increase confidence.

### Implementation Reference
**File**: `backend/analytics/multi_stage_hits.py`
**Function**: `stage3_platform_hits()` (lines 201-256)

---

## Critical Implementation Details

### 1. Per-Plate Normalization (REQUIRED)

**Why**: Plate-to-plate variability in reagents, incubation, reading conditions requires independent normalization.

**How**: Group data by `PlateID` before calculating median/MAD:

```python
for plate_id in df['PlateID'].unique():
    plate_mask = df['PlateID'] == plate_id
    plate_values = df.loc[plate_mask, 'Ratio_lptA']

    # Calculate per-plate statistics
    median_plate = nan_safe_median(plate_values)
    mad_plate = mad(plate_values)

    # Apply Z-score formula
    z_scores = (plate_values - median_plate) / (1.4826 * mad_plate)
    df.loc[plate_mask, 'Z_lptA'] = z_scores
```

**Verification**: Z-scores should match Excel calculations when Excel uses per-plate references.

### 2. NaN Handling

All statistical functions use `nan_safe_median()` and `nan_safe_std()` to handle:
- Empty wells
- Failed measurements
- Outlier exclusion

### 3. Column Mapping

Raw Excel columns are mapped to standardized names:
```python
'BG_lptA' → BetaGlo ATP for lptA reporter
'BT_lptA' → BacTiter growth for lptA reporter
'Ratio_lptA' → BG_lptA / BT_lptA
'Z_lptA' → Robust Z-score for Ratio_lptA
'B_lptA' → B-score (if calculated)
```

---

## Default Thresholds

```python
z_score_threshold = 2.0        # Reporter activation threshold
viability_gate = 0.3            # ATP warning level (not a filter)
b_score_iterations = 5          # B-score smoothing iterations
edge_effect_threshold = 0.15    # Spatial QC warning
```

---

## Pipeline Flow

```
Raw Data (Excel)
    ↓
Column Mapping
    ↓
Ratio Calculation (BG/BT)
    ↓
Per-Plate Z-Score Calculation
    ↓
Stage 1: Reporter Hits (Z ≥ 2.0)
    ↓
Stage 2: Vitality Hits (growth pattern)
    ↓
Stage 3: Platform Hits (Stage1 AND Stage2)
    ↓
Results with Confidence Scores
```

---

## Example Calculation

**Well E02, Plate_1**:
- BG_lptA: 11,818,972
- BT_lptA: 2,436
- Ratio_lptA: 4,851.79

**Plate_1 Statistics** (calculated from all wells on Plate_1):
- Median(Ratio_lptA): 2,851.71
- MAD(Ratio_lptA): 1,032.92

**Z-Score Calculation**:
```
Z_lptA = (4,851.79 - 2,851.71) / (1.4826 × 1,032.92)
Z_lptA = 2,000.08 / 1,531.42
Z_lptA = 1.306
```

**Result**: Z < 2.0 → Not a reporter hit

---

## Key Files

1. **Core Calculations**: `backend/core/calculations.py`
   - `calculate_robust_zscore()` - Individual Z-score calculation
   - `calculate_robust_zscore_columns()` - Per-plate batch calculation

2. **Multi-Stage Pipeline**: `backend/analytics/multi_stage_hits.py`
   - `stage1_reporter_hits()` - Reporter hit detection
   - `stage2_vitality_hits()` - Vitality wrapper
   - `stage3_platform_hits()` - Final integration

3. **Vitality Analysis**: `backend/analytics/vitality_analysis.py`
   - `detect_vitality_hits()` - Growth pattern detection

4. **Statistics Utilities**: `backend/core/statistics.py`
   - `nan_safe_median()` - Robust median
   - `mad()` - Median absolute deviation

---

## Notes for AI Implementation

1. **Always calculate median/MAD per-plate** - Do not pool across plates
2. **Viability is QC only** - Do not filter hits based on PassViab
3. **Handle NaN values** - Use robust statistics that skip NaN
4. **Z-score threshold is 2.0** - Based on statistical significance (≈95% CI)
5. **Reporter OR logic** - Either lptA OR ldtD activation triggers Stage 1
6. **Vitality AND logic** - All three growth conditions must be met
7. **Platform AND logic** - Both Stage 1 AND Stage 2 required for final hit

---

## Version History

- **v1.0**: Initial implementation with cross-plate normalization
- **v1.1**: Fixed to per-plate normalization (2025-01)
- **v1.2**: Viability changed from filter to QC warning
