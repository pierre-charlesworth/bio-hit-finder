/**
 * HeatmapDashboard.tsx
 * 
 * Complete heatmap integration dashboard with all advanced features
 * Combines plate visualization, controls, legends, and spatial analysis
 */

import { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Grid3X3, Download, Maximize2, Minimize2, Settings } from 'lucide-react';

import PlateHeatmap from './PlateHeatmap';
import HeatmapControls from './HeatmapControls';
import PlateSelector from './PlateSelector';
import ColorScaleLegend from './ColorScaleLegend';
import EdgeEffectOverlay from './EdgeEffectOverlay';
import { 
  createPlateLayout, 
  WellPosition 
} from '../shared/WellPositionMapper';
import { 
  getColorScaleForDataType, 
  ColorScale,
  calculateOptimalDomain 
} from '../shared/ColorScaleMapper';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { AnalysisResult } from '@/types/analysis';

export interface HeatmapDashboardProps {
  analysisData: AnalysisResult;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
}

/**
 * Complete heatmap analysis dashboard
 */
const HeatmapDashboard = ({
  analysisData,
  onExport,
  className = ''
}: HeatmapDashboardProps) => {

  // State management
  const [dataType, setDataType] = useState<keyof WellData>('Z_lptA');
  const [selectedPlates, setSelectedPlates] = useState<string[]>([]);
  const [selectedWells, setSelectedWells] = useState<string[]>([]);
  const [colorScale, setColorScale] = useState<ColorScale | null>(null);
  const [showTooltips, setShowTooltips] = useState(true);
  const [showAxisLabels, setShowAxisLabels] = useState(true);
  const [showGrid, setShowGrid] = useState(false);
  const [showEdgeEffects, setShowEdgeEffects] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [controlsVisible, setControlsVisible] = useState(true);

  // Process data based on selections
  const { filteredData, plateLayout, wellDataMap, dataValues } = useMemo(() => {
    let wellData = DataProcessor.extractWellData(analysisData);
    
    // Filter by selected plates if any
    if (selectedPlates.length > 0) {
      wellData = wellData.filter(well => 
        selectedPlates.includes(well.PlateID || 'Unknown')
      );
    }

    // Create well data map
    const wellMap = new Map<string, WellData>();
    const values: number[] = [];
    
    wellData.forEach(well => {
      wellMap.set(well.Well, well);
      const value = well[dataType];
      if (isFinite(value)) {
        values.push(value);
      }
    });

    // Create plate layout
    const layout = createPlateLayout(
      wellData.map(w => w.Well),
      isFullscreen ? 1200 : 800,
      isFullscreen ? 800 : 600
    );

    return {
      filteredData: wellData,
      plateLayout: layout,
      wellDataMap: wellMap,
      dataValues: values
    };
  }, [analysisData, selectedPlates, dataType, isFullscreen]);

  // Determine active color scale
  const activeColorScale = useMemo(() => {
    if (colorScale) return colorScale;

    const autoScale = getColorScaleForDataType(String(dataType));
    
    // Calculate optimal domain from filtered data
    if (dataValues.length > 0) {
      const optimalDomain = calculateOptimalDomain(
        dataValues,
        autoScale.type,
        { 
          symmetric: autoScale.type === 'diverging',
          center: autoScale.center 
        }
      );
      
      return {
        ...autoScale,
        domain: optimalDomain
      };
    }
    
    return autoScale;
  }, [colorScale, dataType, dataValues]);

  // Handle well selection
  const handleWellClick = useCallback((well: WellPosition, data: WellData) => {
    console.log('Well clicked:', well.wellId, data);
    // Could trigger detailed well analysis modal
  }, []);

  const handleWellSelectionChange = useCallback((wells: string[]) => {
    setSelectedWells(wells);
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedWells([]);
  }, []);

  // Handle export
  const handleExport = useCallback((format: 'png' | 'svg' | 'pdf') => {
    console.log(`Exporting heatmap as ${format}`);
    onExport?.(format);
  }, [onExport]);

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    const totalWells = filteredData.length;
    const viableWells = filteredData.filter(w => w.PassViab).length;
    const hits = filteredData.filter(w => 
      Math.abs(w.Z_lptA || 0) >= 2 || Math.abs(w.Z_ldtD || 0) >= 2
    ).length;

    return {
      totalWells,
      viableWells,
      hits,
      viabilityRate: totalWells > 0 ? viableWells / totalWells : 0,
      hitRate: viableWells > 0 ? hits / viableWells : 0,
      selectedPlates: selectedPlates.length
    };
  }, [filteredData, selectedPlates]);

  if (filteredData.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-12 text-center">
          <Grid3X3 className="h-16 w-16 mx-auto mb-4 opacity-50 text-muted-foreground" />
          <h3 className="text-lg font-medium mb-2">No Plate Data Available</h3>
          <p className="text-sm text-muted-foreground">
            Upload plate data or select plates to view interactive heatmaps with 
            spatial analysis and quality control features.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Grid3X3 className="h-6 w-6" />
              <div>
                <CardTitle>Plate Heatmap Analysis</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Interactive spatial visualization with quality control and hit analysis
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Summary Stats */}
              <div className="flex gap-2">
                <Badge variant="outline" className="text-xs">
                  {summaryStats.totalWells} wells
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {summaryStats.hits} hits ({(summaryStats.hitRate * 100).toFixed(1)}%)
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {(summaryStats.viabilityRate * 100).toFixed(1)}% viable
                </Badge>
              </div>

              {/* Controls Toggle */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setControlsVisible(!controlsVisible)}
                className="flex items-center gap-1"
              >
                <Settings className="h-4 w-4" />
                {controlsVisible ? 'Hide' : 'Show'} Controls
              </Button>

              {/* Fullscreen Toggle */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="flex items-center gap-1"
              >
                {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                {isFullscreen ? 'Exit' : 'Expand'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className={`grid gap-6 ${
        isFullscreen 
          ? 'grid-cols-1' 
          : controlsVisible 
            ? 'grid-cols-1 lg:grid-cols-4' 
            : 'grid-cols-1'
      }`}>
        
        {/* Controls Panel */}
        {controlsVisible && !isFullscreen && (
          <div className="lg:col-span-1 space-y-4">
            {/* Data Type and Appearance Controls */}
            <HeatmapControls
              dataType={dataType}
              colorScale={activeColorScale}
              onDataTypeChange={setDataType}
              onColorScaleChange={setColorScale}
              onExport={handleExport}
              showTooltips={showTooltips}
              onTooltipToggle={setShowTooltips}
              showAxisLabels={showAxisLabels}
              onAxisLabelsToggle={setShowAxisLabels}
              showGrid={showGrid}
              onGridToggle={setShowGrid}
              selectedWells={selectedWells}
              onClearSelection={handleClearSelection}
            />

            {/* Color Scale Legend */}
            <ColorScaleLegend
              colorScale={activeColorScale}
              dataValues={dataValues}
              dataType={String(dataType)}
              selectedCount={selectedWells.length}
              height={250}
            />

            {/* Plate Selection */}
            <PlateSelector
              analysisData={analysisData}
              selectedPlates={selectedPlates}
              onSelectionChange={setSelectedPlates}
            />
          </div>
        )}

        {/* Main Heatmap Panel */}
        <div className={`${
          isFullscreen 
            ? 'col-span-1' 
            : controlsVisible 
              ? 'lg:col-span-3' 
              : 'col-span-1'
        }`}>
          <Card className="relative">
            <CardContent className="p-6">
              <div className="relative">
                {/* Main Heatmap */}
                <PlateHeatmap
                  analysisData={analysisData}
                  dataType={dataType}
                  colorScale={activeColorScale}
                  width={isFullscreen ? 1200 : 800}
                  height={isFullscreen ? 800 : 600}
                  onWellClick={handleWellClick}
                  onSelectionChange={handleWellSelectionChange}
                  selectedWells={selectedWells}
                  showTooltips={showTooltips}
                  showAxisLabels={showAxisLabels}
                  showGrid={showGrid}
                />

                {/* Edge Effect Overlay */}
                <EdgeEffectOverlay
                  wells={plateLayout.wells}
                  wellData={wellDataMap}
                  dataType={dataType}
                  visible={showEdgeEffects}
                  onToggleVisibility={setShowEdgeEffects}
                />
              </div>

              {/* Bottom Controls */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="flex items-center gap-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowEdgeEffects(!showEdgeEffects)}
                    className="flex items-center gap-1"
                  >
                    Spatial Analysis
                    {showEdgeEffects && <Badge variant="secondary" className="ml-1 text-xs">ON</Badge>}
                  </Button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {plateLayout.format.name} format • {filteredData.length} wells
                    {selectedWells.length > 0 && ` • ${selectedWells.length} selected`}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Fullscreen Controls */}
      {isFullscreen && (
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Quick Data Type Switch */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Data Type</h4>
                <div className="flex gap-1">
                  {(['Z_lptA', 'Z_ldtD', 'Ratio_lptA', 'Ratio_ldtD'] as const).map(type => (
                    <Button
                      key={type}
                      variant={dataType === type ? "default" : "outline"}
                      size="sm"
                      onClick={() => setDataType(type)}
                      className="text-xs"
                    >
                      {type.replace('_', ' ')}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Quick Export */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Export</h4>
                <div className="flex gap-1">
                  <Button variant="outline" size="sm" onClick={() => handleExport('png')}>
                    <Download className="h-3 w-3 mr-1" />
                    PNG
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleExport('svg')}>
                    <Download className="h-3 w-3 mr-1" />
                    SVG
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleExport('pdf')}>
                    <Download className="h-3 w-3 mr-1" />
                    PDF
                  </Button>
                </div>
              </div>

              {/* Color Scale Legend */}
              <ColorScaleLegend
                colorScale={activeColorScale}
                dataValues={dataValues}
                dataType={String(dataType)}
                selectedCount={selectedWells.length}
                orientation="horizontal"
                height={60}
                width={200}
                showInterpretation={false}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default HeatmapDashboard;