# PRD Extension: Multi-Stage Hit Calling for Dual-Readout Screening Platform

## Executive Summary

This document extends the original PRD to support **dual-readout compound screening** with tiered hit calling, as implemented in the user's Excel workflow. The platform combines **reporter assays** (biochemical activity) with **vitality assays** (growth pattern analysis) to identify compounds with both target engagement and physiological relevance.

## 1. Additional Requirements Overview

### 1.1 Multi-Stage Hit Classification
The platform must support **three sequential stages** of hit detection:
1. **Reporter Hits (LumHit)**: Compounds showing biochemical activity (Z≥2) with viable cells
2. **Vitality Hits (OMpatternOK)**: Compounds showing target-specific growth inhibition patterns
3. **Platform Hits**: Compounds passing both reporter and vitality criteria

### 1.2 Enhanced Data Processing
- **Pre-calculated median handling**: Support Excel files with pre-computed statistics
- **Strain-specific OD normalization**: Using plate-wide medians for percentage calculations
- **Dual viability gating**: ATP-based (existing) + growth-based (new) viability assessment

## 2. Extended Calculations & Formulas

### 2.1 OD Percentage Normalization (New)

**Purpose**: Calculate growth as percentage of plate-wide median for strain comparison.

**Formulas**:
```
WT_med = median(OD_WT)    # Calculate from experimental data
TC_med = median(OD_tolC)  # Calculate from experimental data  
SA_med = median(OD_SA)    # Calculate from experimental data

WT% = OD_WT / WT_med
tolC% = OD_tolC / TC_med  
SA% = OD_SA / SA_med
```

**Implementation Notes**:
- Calculate plate-wide medians from the experimental OD values
- Use only the raw experimental data from Excel (BG_*, BT_*, OD_*)
- Ignore any pre-calculated columns in the Excel file
- Store calculated medians as metadata for reproducibility

### 2.2 Enhanced Viability Assessment

**Current PRD**: ATP-based viability only
```
viability_ok_lptA = BT_lptA >= f * median(BT_lptA)
```

**Extended**: Dual viability assessment
```
PassViab_lptA = viability_ok_lptA  # ATP-based (existing)
PassViab_ldtD = viability_ok_ldtD  # ATP-based (existing)
```

### 2.3 Multi-Stage Hit Calling (New)

#### Stage 1: Reporter Hit Detection
```
LumHit = OR(
    AND(Z_lptA >= Z_threshold_lptA, PassViab_lptA),
    AND(Z_ldtD >= Z_threshold_ldtD, PassViab_ldtD)
)
```

**Configurable Parameters**:
- `Z_threshold_lptA` (default: 2.0)
- `Z_threshold_ldtD` (default: 2.0)

**Logic**: Either reporter shows strong signal (Z≥threshold) AND passes ATP viability

#### Stage 2: Vitality Hit Detection
```
OMpatternOK = AND(
    tolC% <= tolC_max,     # ΔtolC strain inhibited (compound penetrates)
    WT% > WT_min,          # Wild type survives (not generally toxic)
    SA% > SA_min           # SA strain survives (compound specificity)
)
```

**Configurable Parameters**:
- `tolC_max` (default: 0.8) - Maximum tolC growth for target engagement
- `WT_min` (default: 0.8) - Minimum WT growth to avoid general toxicity
- `SA_min` (default: 0.8) - Minimum SA growth for compound specificity

**Logic**: Compound shows **target-specific growth inhibition pattern**

#### Stage 3: Platform Hit (Final)
```
PlatformHit = AND(LumHit, OMpatternOK)
```

**Logic**: Must pass **both** biochemical activity and physiological relevance

## 3. Implementation Architecture

### 3.1 New Modules Required

#### 3.1.1 `analytics/vitality_analysis.py`
```python
class VitalityAnalyzer:
    def calculate_plate_medians(df) -> Dict[str, float]  # Calculate from OD data
    def calculate_od_percentages(df) -> pd.DataFrame     # WT%, tolC%, SA%
    def detect_vitality_hits(df, config) -> pd.DataFrame
```

#### 3.1.2 `analytics/multi_stage_hits.py`
```python
class MultiStageHitCaller:
    def stage1_reporter_hits(df, config)
    def stage2_vitality_hits(df, config)  
    def stage3_platform_hits(df, config)
    def generate_hit_summary(df)
```

#### 3.1.3 Enhanced `core/plate_processor.py`
```python
class AdvancedPlateProcessor(PlateProcessor):
    def process_dual_readout_plate(df, plate_id, config)
    def calculate_all_percentages(df) -> pd.DataFrame  # Add WT%, tolC%, SA%
```

### 3.2 Configuration Extensions

#### 3.2.1 Extended `config.yaml`
```yaml
# Multi-stage hit calling
hit_calling:
  # Stage 1: Reporter hits
  reporter:
    z_threshold_lptA: 2.0
    z_threshold_ldtD: 2.0
    require_viability: true
  
  # Stage 2: Vitality hits  
  vitality:
    tolC_max_percent: 0.8    # ≤80% growth for target engagement
    WT_min_percent: 0.8      # >80% growth to avoid toxicity
    SA_min_percent: 0.8      # >80% growth for specificity
  
  # Stage 3: Combined criteria
  platform:
    require_both: true       # Both reporter AND vitality

# OD normalization method
od_normalization:
  method: "percentage"       # "percentage" or "median_ratio" 
  calculate_medians: true    # Calculate medians from experimental OD data
```

### 3.3 UI Enhancements

#### 3.3.1 Extended Hits Tab
- **Hit Type Filter**: Reporter Only | Vitality Only | Platform Hits (Both)
- **Stage-wise Counts**: Show counts for each stage
- **Hit Classification Columns**: `LumHit`, `OMpatternOK`, `PlatformHit`

#### 3.3.2 New "Multi-Stage Analysis" Tab
- **Hit Funnel Visualization**: Stage 1 → Stage 2 → Stage 3 flow
- **Venn Diagram**: Reporter vs Vitality hit overlap
- **Strain Growth Patterns**: WT%, tolC%, SA% distributions

## 4. Validation Requirements

### 4.1 Numerical Accuracy
- **Excel Compatibility**: Results must match user's Excel calculations within 1e-9 tolerance
- **Formula Validation**: Each stage calculation verified against known examples
- **Edge Cases**: Handle missing medians, zero denominators, boundary conditions

### 4.2 Multi-Stage Logic Testing
- **Stage Isolation**: Test each stage independently
- **Cascade Testing**: Verify proper stage 1→2→3 flow
- **Boundary Testing**: Compounds at threshold boundaries
- **Real Data Validation**: Process user's actual Excel file and match results exactly

## 5. Example Workflow

### 5.1 Input Processing
```python
# Load Excel with experimental data only
df = pd.read_excel("naicons_data.xlsx")

# Clean and process data (removes any pre-calculated columns)
processor = AdvancedPlateProcessor()
processed_df = processor.process_dual_readout_plate(df, "NaiconsPlate", config)

# Medians calculated from experimental data
# WT_med = median(OD_WT), TC_med = median(OD_tolC), SA_med = median(OD_SA)
print(f"Calculated medians: WT_med={processed_df.attrs['WT_med']:.3f}")
```

### 5.2 Multi-Stage Hit Calling
```python
hit_caller = MultiStageHitCaller()

# Stage 1: Reporter hits (Z≥2 + viable)
stage1_hits = hit_caller.stage1_reporter_hits(processed_df, config)
print(f"Stage 1: {len(stage1_hits)} reporter hits")

# Stage 2: Vitality hits (growth pattern)  
stage2_hits = hit_caller.stage2_vitality_hits(processed_df, config)
print(f"Stage 2: {len(stage2_hits)} vitality hits")

# Stage 3: Platform hits (both)
platform_hits = hit_caller.stage3_platform_hits(processed_df, config)
print(f"Final: {len(platform_hits)} platform hits")
```

### 5.3 Results Analysis
```python
# Hit summary with breakdown
summary = hit_caller.generate_hit_summary(processed_df)
"""
{
  'total_wells': 80,
  'reporter_hits': 15,      # LumHit = True
  'vitality_hits': 8,       # OMpatternOK = True  
  'platform_hits': 5,      # Both = True
  'reporter_only': 10,     # LumHit=True, OMpatternOK=False
  'vitality_only': 3,      # LumHit=False, OMpatternOK=True
  'neither': 62            # Both = False
}
"""
```

## 6. Export Enhancements

### 6.1 Extended CSV Exports
- **Hit Classification Columns**: `LumHit`, `OMpatternOK`, `PlatformHit`
- **Stage Metrics**: `WT%`, `tolC%`, `SA%`, `PassViab_lptA`, `PassViab_ldtD`
- **Metadata**: Plate medians used for calculations

### 6.2 Multi-Stage Reports
- **Hit Funnel Report**: Visual progression through stages
- **Compound Profiles**: Detailed view of platform hits with both readouts
- **Method Documentation**: Exact formulas and thresholds used

## 7. Backward Compatibility

### 7.1 Legacy Support
- **Single-Stage Mode**: Original PRD workflow remains unchanged
- **Auto-Detection**: Detect data format and apply appropriate workflow
- **Configuration Switch**: `hit_calling.mode: "single" | "multi"`

### 7.2 Migration Path
- **Existing Users**: Default to single-stage mode
- **New Users**: Multi-stage mode when dual-readout data detected
- **Upgrade Path**: Clear documentation for switching modes

## 8. Success Metrics

### 8.1 Functional Validation
- ✅ Process user's Excel file with 100% numerical accuracy
- ✅ Generate identical hit classifications as Excel formulas
- ✅ Handle 80 wells with multi-stage analysis in <500ms
- ✅ Support both single and multi-stage workflows

### 8.2 User Experience
- ✅ Intuitive UI for multi-stage hit exploration
- ✅ Clear visualization of hit funnel and overlaps
- ✅ Export compatibility with existing downstream analysis tools

## 9. Implementation Priority

### Phase 1: Core Multi-Stage Logic (Week 1)
- Implement VitalityAnalyzer and MultiStageHitCaller
- Add OD percentage calculations
- Create configuration framework

### Phase 2: UI Integration (Week 1-2)  
- Extend Hits tab with stage filters
- Add Multi-Stage Analysis tab
- Update visualizations

### Phase 3: Validation & Testing (Week 2)
- Golden tests with user's Excel file
- Edge case testing
- Performance optimization

This extension transforms the platform from a single-readout reporter assay analyzer into a comprehensive **dual-readout screening platform** suitable for pharmaceutical and biotechnology compound discovery workflows.