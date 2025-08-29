# Multi-Stage Hit Calling Implementation Plan

## Overview
Implementation plan for extending the bio-hit-finder platform to support dual-readout screening with tiered hit calling as specified in the PRD extension.

## Phase 1: Core Multi-Stage Logic Implementation

### Task 1.1: Vitality Analysis Module
**File**: `analytics/vitality_analysis.py`
**Agent**: `data-scientist`
**Estimated Time**: 4-6 hours

**Requirements**:
- Calculate plate medians from experimental OD data (WT_med, TC_med, SA_med)
- Calculate OD percentages: WT% = OD_WT/WT_med, etc.
- Implement vitality hit detection: AND(tolC%≤0.8, WT%>0.8, SA%>0.8)
- Use only raw experimental values from Excel

**Deliverables**:
```python
class VitalityAnalyzer:
    def calculate_plate_medians(self, df) -> Dict[str, float]
    def calculate_od_percentages(self, df) -> pd.DataFrame
    def detect_vitality_hits(self, df, config) -> pd.DataFrame
```

### Task 1.2: Multi-Stage Hit Caller
**File**: `analytics/multi_stage_hits.py`  
**Agent**: `python-backend-engineer`
**Estimated Time**: 6-8 hours

**Requirements**:
- Stage 1: Reporter hits (Z≥2 AND PassViab)
- Stage 2: Vitality hits (growth pattern analysis)
- Stage 3: Platform hits (Stage1 AND Stage2)
- Configurable thresholds for all stages
- Comprehensive hit summary statistics

**Deliverables**:
```python
class MultiStageHitCaller:
    def stage1_reporter_hits(self, df, config) -> pd.DataFrame
    def stage2_vitality_hits(self, df, config) -> pd.DataFrame  
    def stage3_platform_hits(self, df, config) -> pd.DataFrame
    def generate_hit_summary(self, df) -> Dict[str, Any]
```

### Task 1.3: Enhanced Plate Processor
**File**: `core/plate_processor.py` (extend existing)
**Agent**: `python-backend-engineer`
**Estimated Time**: 3-4 hours

**Requirements**:
- Detect dual-readout data format automatically
- Calculate OD percentages from experimental data
- Integrate vitality and multi-stage analysis
- Maintain backward compatibility with existing single-stage mode

**Deliverables**:
```python
class AdvancedPlateProcessor(PlateProcessor):
    def process_dual_readout_plate(self, df, plate_id, config) -> pd.DataFrame
    def calculate_all_percentages(self, df) -> pd.DataFrame
```

### Task 1.4: Configuration Framework Extension
**File**: `config.yaml` (extend existing)
**Agent**: `backend-architect` 
**Estimated Time**: 2-3 hours

**Requirements**:
- Multi-stage hit calling parameters
- OD normalization method selection
- Threshold configurations for all stages
- Backward compatibility switches

## Phase 2: UI Integration

### Task 2.1: Enhanced Hits Tab
**File**: `app.py` (modify existing)
**Agent**: `frontend-developer`
**Estimated Time**: 4-5 hours

**Requirements**:
- Hit type filtering (Reporter | Vitality | Platform)
- Stage-wise hit counts display
- Additional columns: LumHit, OMpatternOK, PlatformHit
- Updated download functionality

### Task 2.2: Multi-Stage Analysis Tab
**File**: `app.py` (new tab)
**Agent**: `ui-ux-designer + frontend-developer`
**Estimated Time**: 6-8 hours

**Requirements**:
- Hit funnel visualization (Stage 1→2→3)
- Venn diagram for hit overlap
- Strain growth pattern distributions
- Interactive exploration of hit classifications

### Task 2.3: Enhanced Visualizations
**File**: `visualizations/` (extend existing)
**Agent**: `frontend-developer`
**Estimated Time**: 4-6 hours

**Requirements**:
- Multi-stage hit funnel charts
- Growth pattern scatter plots (WT% vs tolC% vs SA%)
- Hit classification heatmaps
- Stage comparison visualizations

## Phase 3: Testing & Validation

### Task 3.1: Golden Test Implementation
**File**: `tests/test_multi_stage_golden.py`
**Agent**: `test-automator`
**Estimated Time**: 6-8 hours

**Requirements**:
- Process user's Excel file exactly
- Validate numerical accuracy (≤1e-9 tolerance)
- Compare each stage result against Excel formulas
- Test all edge cases and boundary conditions

### Task 3.2: Integration Testing
**File**: `tests/test_multi_stage_integration.py`
**Agent**: `test-automator`  
**Estimated Time**: 4-6 hours

**Requirements**:
- End-to-end multi-stage workflow testing
- UI interaction testing for new features
- Export functionality validation
- Performance benchmarking

### Task 3.3: User Acceptance Testing
**Agent**: `docs-architect`
**Estimated Time**: 3-4 hours

**Requirements**:
- Process user's actual Excel file
- Generate identical results to existing workflow
- Validate hit classifications match exactly
- Performance meets requirements (<500ms for 80 wells)

## Phase 4: Documentation & Deployment

### Task 4.1: Technical Documentation
**Files**: Update existing docs
**Agent**: `docs-architect`
**Estimated Time**: 3-4 hours

**Requirements**:
- Update user guide with multi-stage workflow
- API documentation for new modules
- Configuration guide for dual-readout mode
- Migration guide from single-stage

### Task 4.2: Sample Data Generation  
**File**: `data/` (extend existing)
**Agent**: `data-scientist`
**Estimated Time**: 2-3 hours

**Requirements**:
- Generate synthetic dual-readout data
- Include summary rows with medians
- Create demo scenarios for each hit type
- Test data for edge cases

## Implementation Schedule

### Week 1: Core Implementation
- **Days 1-2**: Tasks 1.1, 1.2 (Vitality & Multi-stage modules)
- **Days 3-4**: Tasks 1.3, 1.4 (Processor & Configuration)
- **Day 5**: Integration testing of core logic

### Week 2: UI & Validation
- **Days 1-2**: Tasks 2.1, 2.2 (UI enhancements)
- **Days 3-4**: Task 2.3, 3.1 (Visualizations & Golden tests)
- **Day 5**: Tasks 3.2, 3.3 (Integration & User acceptance testing)

### Week 3: Polish & Deploy
- **Days 1-2**: Tasks 4.1, 4.2 (Documentation & Sample data)
- **Days 3-4**: Bug fixes and performance optimization
- **Day 5**: Final validation and deployment

## Success Criteria

### Technical Validation
- ✅ User's Excel file processes with 100% numerical accuracy
- ✅ All 80 wells classified identically to Excel formulas
- ✅ Performance: <500ms processing time for dual-readout analysis
- ✅ Memory: <1GB for multi-stage analysis

### Functional Requirements
- ✅ Three-stage hit calling pipeline working correctly
- ✅ OD percentage calculations match Excel exactly
- ✅ Configurable thresholds for all stages
- ✅ Backward compatibility with existing single-stage mode

### User Experience
- ✅ Intuitive UI for exploring multi-stage results
- ✅ Clear visualization of hit progression
- ✅ Export functionality maintains all hit classification data
- ✅ Documentation sufficient for user adoption

## Risk Mitigation

### Technical Risks
- **Formula Complexity**: Start with golden tests using user's exact Excel data
- **Performance Impact**: Profile each stage and optimize bottlenecks
- **Integration Complexity**: Maintain clear separation between single/multi-stage modes

### User Adoption Risks  
- **Learning Curve**: Comprehensive documentation and intuitive UI design
- **Migration Issues**: Strong backward compatibility and clear upgrade path
- **Validation Concerns**: Exact numerical matching with existing Excel workflow

This plan transforms the bio-hit-finder from a single-readout tool into a comprehensive dual-readout screening platform while maintaining full compatibility with existing workflows.