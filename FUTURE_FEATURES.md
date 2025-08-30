# Future Features

This document tracks potential enhancements for the BREAKthrough OM Screening Platform.

## QC Dashboard Enhancements

### Z-Factor Analysis for Control Plates
**Status**: Planned for future release

**Description**: 
The Z-factor is a statistical measure used to evaluate assay quality based on positive and negative controls. Currently disabled because compound screening plates don't have the required ~50/50 positive/negative control distribution needed for Z-factor calculation.

**Implementation Options**:
1. **Control Well Specification**: Allow users to manually specify which wells contain positive/negative controls
2. **Separate Control Plate Upload**: Upload dedicated Z-factor validation plates alongside screening data
3. **Well Annotation System**: Implement a well tagging system to identify control types
4. **Plate Type Detection**: Automatically detect if a plate has sufficient controls for Z-factor analysis

**Technical Requirements**:
- Well annotation/tagging system
- Control plate data structure
- Z-factor calculation validation
- UI for control well specification
- Integration with existing QC dashboard

**Priority**: Medium - Useful for labs running dedicated QC plates alongside screening

### Control-Based CV% Analysis
**Status**: Planned for future release

**Description**: 
The CV% (Coefficient of Variation %) currently assumes positive/negative control wells exist on screening plates. For compound screening, control-based CV% is not applicable since wells contain test compounds, not defined controls.

**Current Issue**:
- Attempts to calculate CV% from assumed control positions (A1, A2, etc.)
- These positions aren't actual controls in screening plates
- Results in meaningless precision metrics

**Implementation Options**:
1. **Overall Plate CV%**: Measure consistency across all compound wells
2. **Replicate CV%**: Calculate variability between compound replicates (if available)
3. **Spatial CV%**: Assess measurement consistency within plate regions
4. **Control Well Specification**: Allow users to define actual control positions
5. **Separate QC Plate Mode**: Different metrics for dedicated QC vs screening plates

**Technical Requirements**:
- Plate type detection (QC vs screening)
- Alternative CV% calculations for screening data
- Control well annotation system
- Updated QC dashboard logic

**Priority**: Medium - Important for assay quality assessment

---

*Add new features below this line*