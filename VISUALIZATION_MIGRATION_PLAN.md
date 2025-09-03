# 📊 BREAKthrough Platform - Visualization Migration Plan

## Executive Summary

This document outlines the comprehensive migration strategy for transferring all scientific visualizations from the legacy Streamlit frontend to the new React-based frontend. The migration preserves analytical capabilities while modernizing the user experience through React components and interactive Plotly.js visualizations.

## Current Status Assessment

### ✅ Completed Migrations
- **Sankey Flow Diagram** - OM Permeabilizer Discovery Pipeline
  - **Technology**: Plotly.js with react-plotly.js wrapper
  - **Status**: Complete and deployed
  - **Features**: Interactive tooltips, color-coded flows, responsive design

### 🎯 Pending Migrations
- **4 Core Statistical Charts** (Visualizations Tab)
- **Comprehensive Heatmap System** (Heatmaps Tab) 
- **Advanced QC Dashboard** (QC Report Tab)
- **Export/PDF Generation** functionality

## Detailed Analysis of Legacy Visualizations

### 1. Core Statistical Charts Suite

#### **Chart 1: Z_lptA Distribution Histogram**
```python
# Legacy Implementation (Streamlit)
fig1 = px.histogram(df, x='Z_lptA', nbins=50, title="Raw Z_lptA Distribution")
fig1.add_vline(x=z_cutoff, line_dash="dash", line_color="red")
```

**Analysis:**
- **Purpose**: Shows distribution of lptA reporter Z-scores with threshold visualization
- **Data Source**: `df['Z_lptA']` column from processed analysis data
- **Key Features**: 
  - 50-bin histogram with steelblue color
  - Red dashed threshold lines at ±z_cutoff
  - Threshold annotation labels
  - Expandable scientific legend system
- **User Interaction**: Hover tooltips, zoom/pan capabilities

#### **Chart 2: Z_ldtD Distribution Histogram**
```python
# Legacy Implementation (Streamlit)  
fig2 = px.histogram(df, x='Z_ldtD', nbins=50, title="Raw Z_ldtD Distribution")
fig2.add_vline(x=z_cutoff, line_dash="dash", line_color="red")
```

**Analysis:**
- **Purpose**: Shows distribution of ldtD reporter Z-scores with threshold visualization
- **Data Source**: `df['Z_ldtD']` column from processed analysis data
- **Key Features**:
  - 50-bin histogram with darkgreen color  
  - Red dashed threshold lines at ±z_cutoff
  - Scientific interpretation legends
- **Biological Significance**: Cpx-regulated stress response detection

#### **Chart 3: Ratio Correlation Scatter Plot**
```python
# Legacy Implementation (Streamlit)
fig3 = px.scatter(df, x='Ratio_lptA', y='Ratio_ldtD', color='PlateID', 
                  title="Ratio_lptA vs Ratio_ldtD", hover_data=['Well'])
```

**Analysis:**
- **Purpose**: Correlation analysis between dual reporters
- **Data Source**: `df['Ratio_lptA']`, `df['Ratio_ldtD']`, `df['PlateID']`
- **Key Features**:
  - Color-coded by plate ID for batch effect analysis
  - Well identification on hover
  - Correlation pattern visualization
- **Scientific Value**: Identifies compounds affecting both envelope systems

#### **Chart 4: Viability Bar Chart by Plate**
```python
# Legacy Implementation (Streamlit)
fig4 = px.bar(plot_df, x='PlateID', y='Count', color='Status',
              title="Viability Counts by Plate (lptA)")
```

**Analysis:**
- **Purpose**: Quality control visualization of viable vs non-viable wells
- **Data Processing**: Complex aggregation from `df.groupby('PlateID')['viability_ok_lptA']`
- **Key Features**:
  - Stacked bars showing viable (lightblue) vs non-viable (lightcoral)
  - Plate-wise comparison for batch effects
  - Legend with scientific context
- **QC Value**: Identifies plates with poor viability rates

### 2. Advanced Heatmap System

#### **Heatmap Architecture Overview**
```python
# Legacy Implementation Structure
- Family/Extract selection system
- Data type toggles (Raw Z, B-scores, Ratios)
- Plate layout reconstruction (96/384/1536-well formats)  
- Color mapping with scientific scales
- Edge effect visualization overlay
```

**Analysis:**
- **Complexity**: High - most sophisticated visualization in the system
- **Data Sources**: Multiple data types per well position
- **Key Features**:
  - **Plate Layout**: Automatic detection of plate format (96/384/1536-well)
  - **Data Type Selection**: Raw Z-scores, B-scores, Reporter ratios, OD measurements
  - **Family Filtering**: Extract/family-based data segmentation
  - **Color Mapping**: Scientific color scales (blue-white-red for Z-scores)
  - **Edge Detection**: Visual overlay of spatial artifacts
  - **Export Options**: High-resolution publication formats

**Technical Components:**
1. **Well Position Mapping**: Row/column to (x,y) coordinate conversion
2. **Data Transformation**: Z-score to color intensity mapping
3. **Interactive Selection**: Click-to-identify well functionality  
4. **Legend System**: Dynamic color scale with statistical interpretation
5. **Quality Overlays**: Edge effect warnings and spatial correlation indicators

### 3. QC Dashboard System

#### **QC Dashboard Architecture**
```python
# Legacy Implementation (visualizations/advanced/qc_dashboard.py)
class QCDashboard:
    - Multi-panel subplot system
    - Statistical distribution analysis  
    - Quality metrics calculation
    - Automated flagging system
```

**Analysis:**
- **Purpose**: Comprehensive quality control assessment
- **Components**:
  - **Distribution Analysis**: Statistical normality testing
  - **Control Performance**: Z' factor calculations  
  - **Spatial Analysis**: Edge effect quantification
  - **Batch Effects**: Inter-plate comparison metrics
  - **Hit Rate Analysis**: Expected vs observed rates
- **Output**: Automated QC report with pass/fail indicators

### 4. Export System

#### **Publication-Ready Export Features**
```python
# Legacy Implementation (visualizations/export_plots.py)
- PDF report generation
- High-resolution PNG exports
- Publication formatting (fonts, DPI, sizing)
- Batch export capabilities
```

## Migration Architecture

### Technology Stack

#### **Frontend Components**
```typescript
// Core Visualization Library
import Plot from 'react-plotly.js';

// UI Framework  
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// State Management
import { useAnalysis } from '@/contexts/AnalysisContext';

// Styling
import { cn } from '@/lib/utils';
```

#### **Data Flow Architecture**
```
Backend (Python/FastAPI) 
    ↓ JSON API
React Context (AnalysisContext)
    ↓ Props
Visualization Components
    ↓ Data Processing  
Plotly.js Rendering Engine
```

### Component Hierarchy

```typescript
// Proposed Component Structure
src/components/visualizations/
├── charts/
│   ├── HistogramChart.tsx           // Z-score distributions
│   ├── ScatterChart.tsx             // Ratio correlations
│   ├── BarChart.tsx                 // Viability data
│   └── ChartContainer.tsx           // Shared wrapper
├── heatmaps/
│   ├── PlateHeatmap.tsx             // Core heatmap rendering
│   ├── HeatmapControls.tsx          // Data type selection
│   ├── PlateSelector.tsx            // Family/extract picker
│   ├── ColorScaleLegend.tsx         // Dynamic color scales
│   └── HeatmapDashboard.tsx         // Container component
├── dashboard/
│   ├── QCDashboard.tsx              // Quality control overview
│   ├── QCMetrics.tsx                // Individual QC indicators
│   ├── StatisticalSummary.tsx       // Distribution analysis
│   └── QCControls.tsx               // Configuration panel
├── export/
│   ├── ExportManager.tsx            // Export coordination
│   ├── PDFExporter.tsx              // PDF generation
│   └── ImageExporter.tsx            // PNG/SVG export
└── shared/
    ├── PlotlyWrapper.tsx            // Common Plotly config
    ├── DataProcessor.tsx            // Data transformation utils
    ├── ColorSchemes.tsx             // Scientific color palettes
    └── LoadingStates.tsx            // Loading/error handling
```

## Implementation Phases

### Phase 1: Foundation & Core Charts (Weeks 1-2)

#### **Week 1: Infrastructure Setup**
```typescript
// Deliverables:
1. PlotlyWrapper.tsx - Common configuration and theming
2. DataProcessor.tsx - Data transformation utilities  
3. ColorSchemes.tsx - Scientific color palettes
4. ChartContainer.tsx - Shared wrapper with loading states
5. Basic error handling and loading components
```

**Technical Tasks:**
- Set up shared Plotly configuration (theme, responsive settings)
- Implement data validation and error boundaries
- Create consistent loading states and error messages
- Establish TypeScript interfaces for chart data

#### **Week 2: Core Statistical Charts**
```typescript
// Deliverables:
1. HistogramChart.tsx - Z-score distribution visualization
2. ScatterChart.tsx - Ratio correlation analysis
3. BarChart.tsx - Viability data representation
4. ChartsGrid.tsx - Layout container for visualization tab
5. Integration with AnalysisDashboard.tsx
```

**Features Implementation:**
- Interactive histograms with threshold lines
- Color-coded scatter plots with plate identification
- Stacked bar charts with viability status
- Hover tooltips with well information
- Responsive grid layout system

**Testing Criteria:**
- [ ] Charts render correctly with demo data
- [ ] Interactive features work (hover, zoom, pan)
- [ ] Threshold lines display at correct Z-score values  
- [ ] Color coding matches scientific conventions
- [ ] Charts respond to window resizing

### Phase 2: Advanced Heatmap System (Weeks 3-4)

#### **Week 3: Core Heatmap Engine**
```typescript
// Deliverables:
1. PlateHeatmap.tsx - Core heatmap rendering with well positioning
2. WellPositionMapper.tsx - Plate format detection and coordinate mapping
3. ColorScaleMapper.tsx - Scientific color scale implementation
4. HeatmapTooltip.tsx - Interactive well information display
5. Basic plate layout rendering (96/384-well support)
```

**Technical Challenges:**
- **Well Position Calculation**: Converting A01, B02 format to (x,y) coordinates
- **Plate Format Detection**: Auto-detecting 96/384/1536-well layouts
- **Color Mapping**: Scientific scales (diverging blue-white-red for Z-scores)
- **Performance**: Efficient rendering of 1500+ data points
- **Interactivity**: Click-to-select wells with data display

#### **Week 4: Heatmap Controls & Integration**  
```typescript
// Deliverables:
1. HeatmapControls.tsx - Data type selection (Z-scores, ratios, etc.)
2. PlateSelector.tsx - Family/extract filtering system
3. ColorScaleLegend.tsx - Dynamic legend with statistical interpretation
4. EdgeEffectOverlay.tsx - Spatial artifact visualization
5. HeatmapDashboard.tsx - Complete integration
```

**Advanced Features:**
- Dynamic data type switching without re-render
- Extract/family filtering with data aggregation
- Edge effect detection and overlay visualization  
- Publication-ready color scales and legends
- Export functionality for high-resolution images

**Testing Criteria:**
- [ ] Correct well positioning for all plate formats
- [ ] Color scales accurately represent data ranges
- [ ] Interactive features work smoothly with large datasets
- [ ] Edge effect overlays highlight spatial artifacts
- [ ] Family/extract filtering updates data correctly

### Phase 3: QC Dashboard & Advanced Features (Weeks 5-6)

#### **Week 5: QC Dashboard Foundation**
```typescript
// Deliverables:
1. QCDashboard.tsx - Multi-panel quality control overview
2. QCMetrics.tsx - Individual metric displays (Z', CV, S/B ratio)
3. DistributionAnalysis.tsx - Statistical distribution visualization
4. QCIndicators.tsx - Pass/fail status indicators  
5. QCDataProcessor.tsx - Quality metric calculations
```

**QC Metrics Implementation:**
- **Z' Factor Calculation**: `1 - (3 × (SD_pos + SD_neg) / |mean_pos - mean_neg|)`
- **Coefficient of Variation**: `(SD/mean) × 100%` for control wells
- **Signal-to-Background**: Positive signal / background noise ratios
- **Hit Rate Analysis**: Observed vs expected hit percentages
- **Spatial Correlation**: Moran's I statistic for edge effects

#### **Week 6: Advanced QC Features & Integration**
```typescript
// Deliverables:
1. BatchComparison.tsx - Inter-plate quality comparison
2. QCReportGenerator.tsx - Automated report creation
3. QCControls.tsx - Configuration and threshold settings
4. QCExport.tsx - PDF report generation
5. Complete QC tab integration
```

**Advanced QC Features:**
- Multi-plate batch effect analysis
- Automated quality flags and recommendations
- Configurable quality thresholds
- Historical QC trend tracking
- Automated report generation with interpretations

### Phase 4: Export System & Polish (Weeks 7-8)

#### **Week 7: Export Infrastructure**
```typescript
// Deliverables:
1. ExportManager.tsx - Centralized export coordination
2. PlotlyExporter.tsx - Native Plotly export capabilities
3. PDFGenerator.tsx - Multi-page PDF report creation
4. ImageExporter.tsx - High-resolution image export
5. ExportConfig.tsx - Publication formatting options
```

**Export Features:**
- Individual chart export (PNG, SVG, PDF)
- Complete analysis report generation
- Publication-ready formatting options
- Batch export capabilities
- Custom sizing and DPI settings

#### **Week 8: Performance Optimization & Final Polish**
```typescript
// Deliverables:
1. Performance optimization (lazy loading, memoization)
2. Error handling improvements  
3. Loading state enhancements
4. Mobile responsiveness improvements
5. Accessibility compliance (WCAG 2.1)
6. Documentation and testing completion
```

**Optimization Strategies:**
- React.memo for expensive chart re-renders
- useMemo for data processing operations
- Lazy loading for heavy components
- Intersection Observer for off-screen charts
- Code splitting for visualization bundles

## Data Requirements & API Specifications

### Current Data Flow
```typescript
// Existing API Response Structure
interface AnalysisResult {
  success: boolean;
  results: WellData[];           // Individual well measurements
  summary: SummaryStats;         // Aggregated statistics  
  total_wells: number;
  file_name: string;
  analysis_type: string;
}

interface WellData {
  Well: string;                  // A01, B02, etc.
  Z_lptA: number;               // Reporter Z-scores
  Z_ldtD: number;
  Ratio_lptA: number;           // BG/BT ratios
  Ratio_ldtD: number;
  OD_WT: number;                // Vitality measurements
  OD_tolC: number;
  OD_SA: number;
  PassViab: boolean;            // Viability flags
  PlateID: string;              // Batch identifier
}
```

### Additional API Endpoints Needed

#### **Heatmap Data Endpoint**
```typescript
// GET /api/v1/analysis/heatmap-data
interface HeatmapDataRequest {
  analysisId: string;
  dataType: 'z_scores' | 'ratios' | 'od_values' | 'b_scores';
  plateFamily?: string;
  extract?: string;
}

interface HeatmapDataResponse {
  plateFormat: 96 | 384 | 1536;
  wells: HeatmapWell[];
  colorScale: {
    min: number;
    max: number;
    type: 'diverging' | 'sequential';
  };
  edgeEffects: EdgeEffectData[];
}
```

#### **QC Metrics Endpoint**
```typescript
// GET /api/v1/analysis/qc-metrics  
interface QCMetricsResponse {
  plateMetrics: {
    [plateId: string]: {
      zPrimeFactor: number;
      coefficientVariation: number;
      signalToBackground: number;
      edgeEffectScore: number;
      qualityGrade: 'A' | 'B' | 'C' | 'D' | 'F';
    };
  };
  overallMetrics: {
    averageZPrime: number;
    hitRate: number;
    expectedHitRate: number;
    qualityFlags: string[];
  };
}
```

## Quality Assurance & Testing Strategy

### Testing Framework
```typescript
// Unit Testing (Jest + React Testing Library)
- Component rendering tests
- User interaction simulation  
- Data processing validation
- Error boundary testing

// Integration Testing  
- API data flow testing
- Chart interactivity testing
- Export functionality validation
- Cross-component communication

// Visual Regression Testing (Chromatic)
- Chart rendering consistency
- Layout responsiveness
- Color scheme accuracy
- Publication formatting
```

### Performance Benchmarks
```typescript
// Performance Targets
- Initial chart render: < 500ms
- Data processing: < 200ms for 1000 wells  
- Interactive updates: < 100ms
- Heatmap rendering: < 1000ms for 384-well plate
- Export generation: < 3000ms for PDF report
```

### Accessibility Requirements
```typescript
// WCAG 2.1 Compliance
- Alt text for all visualizations
- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios ≥ 4.5:1
- Focus indicators for interactive elements
- Alternative data tables for chart content
```

## Risk Assessment & Mitigation

### High-Risk Areas

#### **1. Heatmap Performance**
**Risk**: Large datasets (1536-well plates) may cause browser performance issues
**Mitigation**: 
- Implement virtualization for large heatmaps
- Use Canvas rendering for static elements
- Lazy loading for off-screen sections
- Progressive data loading

#### **2. Scientific Accuracy**
**Risk**: Data transformation errors could lead to incorrect scientific interpretations
**Mitigation**:
- Comprehensive unit testing of statistical calculations
- Side-by-side validation with Streamlit output
- Scientific review of color scales and thresholds
- Data validation at API boundaries

#### **3. Export Quality**
**Risk**: Generated exports may not meet publication standards
**Mitigation**:
- Vector-based exports (SVG) for scalability
- Configurable DPI and sizing options
- Font embedding for consistency
- Professional color profiles

### Medium-Risk Areas

#### **1. Browser Compatibility**
**Risk**: Plotly.js may have issues with older browsers
**Mitigation**: 
- Polyfills for ES6+ features
- Graceful degradation for unsupported features
- Browser testing matrix
- Alternative visualization fallbacks

#### **2. Data Volume Scaling**
**Risk**: Large multi-plate experiments may overwhelm the frontend
**Mitigation**:
- Pagination for large datasets
- Background processing for complex calculations
- Progress indicators for long operations
- Memory management optimization

## Success Metrics & Validation

### Functional Success Criteria
- [ ] All Streamlit visualizations reproduced with equivalent functionality
- [ ] Interactive features work correctly (hover, zoom, selection)
- [ ] Export capabilities match or exceed Streamlit functionality
- [ ] Scientific accuracy validated against reference implementations
- [ ] Performance meets or exceeds target benchmarks

### User Experience Metrics
- [ ] Loading times improved over Streamlit baseline
- [ ] Mobile responsiveness achieved (tablet/desktop optimization)
- [ ] Accessibility compliance verified
- [ ] User feedback positive from beta testing
- [ ] Documentation complete and accurate

### Technical Quality Metrics
- [ ] Test coverage ≥ 85% for visualization components
- [ ] No console errors or warnings in production
- [ ] Bundle size optimized (lazy loading implemented)
- [ ] Memory usage stable over extended use
- [ ] Error handling comprehensive and user-friendly

## Post-Migration Maintenance

### Ongoing Maintenance Tasks
1. **Scientific Updates**: New statistical methods or QC metrics
2. **Performance Monitoring**: Chart rendering performance tracking
3. **User Feature Requests**: Additional visualization types
4. **Browser Updates**: Compatibility with new browser versions
5. **Data Format Changes**: Backend API evolution support

### Future Enhancement Opportunities
1. **Real-time Updates**: WebSocket integration for live data
2. **Advanced Interactions**: Brushing and linking between charts
3. **Machine Learning**: Automated pattern recognition in heatmaps
4. **Collaborative Features**: Annotation and sharing capabilities
5. **Mobile App**: Native mobile visualization support

## Conclusion

This comprehensive migration plan provides a structured approach to transferring all scientific visualizations from the legacy Streamlit frontend to the modern React application. The phased implementation strategy minimizes risk while ensuring scientific accuracy and enhanced user experience.

The migration will result in:
- **Enhanced Performance**: Faster loading and interaction
- **Better User Experience**: Modern UI/UX with responsive design  
- **Improved Accessibility**: WCAG 2.1 compliance
- **Advanced Features**: Enhanced interactivity and export capabilities
- **Future-Proof Architecture**: Scalable component-based system

Success depends on careful attention to scientific accuracy, performance optimization, and comprehensive testing throughout the implementation process.