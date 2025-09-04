/**
 * PlateHeatmap.tsx
 * 
 * Core heatmap rendering component with well positioning and interactive features
 * Handles efficient rendering of up to 1536 wells with scientific color mapping
 */

import { useMemo, useRef, useCallback, useState, useEffect } from 'react';
import { 
  createPlateLayout, 
  generateAxisLabels, 
  findNearestWell,
  WellPosition,
  PlateFormat 
} from '../shared/WellPositionMapper';
import { 
  mapValueToColor, 
  ColorScale, 
  getColorScaleForDataType,
  calculateOptimalDomain 
} from '../shared/ColorScaleMapper';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import HeatmapTooltip, { TooltipData, TooltipPosition } from '../shared/HeatmapTooltip';
import { AnalysisResult } from '@/types/analysis';

export interface PlateHeatmapProps {
  analysisData: AnalysisResult;
  dataType: keyof WellData;
  colorScale?: ColorScale;
  width?: number;
  height?: number;
  onWellClick?: (well: WellPosition, data: WellData) => void;
  onSelectionChange?: (selectedWells: string[]) => void;
  selectedWells?: string[];
  showTooltips?: boolean;
  showAxisLabels?: boolean;
  showGrid?: boolean;
  className?: string;
}

/**
 * High-performance plate heatmap with SVG rendering
 */
const PlateHeatmap = ({
  analysisData,
  dataType,
  colorScale,
  width = 800,
  height = 600,
  onWellClick,
  onSelectionChange,
  selectedWells = [],
  showTooltips = true,
  showAxisLabels = true,
  showGrid = false,
  className = ''
}: PlateHeatmapProps) => {
  
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltipData, setTooltipData] = useState<TooltipData | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<TooltipPosition>({
    x: 0, y: 0, visible: false
  });
  const [containerBounds, setContainerBounds] = useState<DOMRect | null>(null);

  // Process data and create plate layout
  const { plateLayout, wellDataMap, dataValues, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    const wellMap = new Map<string, WellData>();
    const values: number[] = [];

    wellData.forEach(well => {
      wellMap.set(well.Well, well);
      const value = well[dataType];
      if (isFinite(value)) {
        values.push(value);
      }
    });

    const layout = createPlateLayout(
      wellData.map(w => w.Well),
      width,
      height
    );

    const dataWarnings = DataProcessor.validateData(wellData);

    return {
      plateLayout: layout,
      wellDataMap: wellMap,
      dataValues: values,
      warnings: dataWarnings
    };
  }, [analysisData, dataType, width, height]);

  // Determine color scale
  const activeColorScale = useMemo(() => {
    if (colorScale) return colorScale;
    
    const autoScale = getColorScaleForDataType(String(dataType));
    
    // Calculate optimal domain from actual data
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

  // Generate axis labels
  const axisLabels = useMemo(() => {
    return generateAxisLabels(plateLayout.format);
  }, [plateLayout.format]);

  // Update container bounds for tooltip positioning
  useEffect(() => {
    const updateBounds = () => {
      if (svgRef.current) {
        setContainerBounds(svgRef.current.getBoundingClientRect());
      }
    };

    updateBounds();
    window.addEventListener('resize', updateBounds);
    return () => window.removeEventListener('resize', updateBounds);
  }, []);

  // Handle mouse events
  const handleMouseMove = useCallback((event: React.MouseEvent<SVGSVGElement>) => {
    if (!showTooltips || !svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const nearestWell = findNearestWell(x, y, plateLayout.wells, 25);
    
    if (nearestWell) {
      const wellData = wellDataMap.get(nearestWell.wellId);
      if (wellData) {
        const value = wellData[dataType];
        const colorMapping = mapValueToColor(value, activeColorScale);

        setTooltipData({
          wellPosition: nearestWell,
          wellData,
          colorValue: value,
          colorIntensity: colorMapping.intensity,
          dataType: String(dataType)
        });

        setTooltipPosition({
          x: event.clientX,
          y: event.clientY,
          visible: true
        });
        return;
      }
    }

    setTooltipPosition(prev => ({ ...prev, visible: false }));
  }, [showTooltips, plateLayout.wells, wellDataMap, dataType, activeColorScale]);

  const handleMouseLeave = useCallback(() => {
    setTooltipPosition(prev => ({ ...prev, visible: false }));
  }, []);

  const handleWellClick = useCallback((well: WellPosition) => {
    const wellData = wellDataMap.get(well.wellId);
    if (wellData && onWellClick) {
      onWellClick(well, wellData);
    }

    // Handle selection
    if (onSelectionChange) {
      const newSelection = selectedWells.includes(well.wellId)
        ? selectedWells.filter(id => id !== well.wellId)
        : [...selectedWells, well.wellId];
      onSelectionChange(newSelection);
    }
  }, [wellDataMap, onWellClick, onSelectionChange, selectedWells]);

  // Calculate well size based on plate format
  const wellSize = useMemo(() => {
    const availableWidth = width * 0.8; // Leave margin for labels
    const availableHeight = height * 0.8;
    
    const wellWidth = availableWidth / plateLayout.format.columns;
    const wellHeight = availableHeight / plateLayout.format.rows;
    
    return Math.min(wellWidth, wellHeight) * 0.8; // Add spacing between wells
  }, [width, height, plateLayout.format]);

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="border border-border rounded-lg bg-background"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {/* Background Grid */}
        {showGrid && (
          <defs>
            <pattern
              id="grid"
              width={width / plateLayout.format.columns}
              height={height / plateLayout.format.rows}
              patternUnits="userSpaceOnUse"
            >
              <path
                d={`M ${width / plateLayout.format.columns} 0 L 0 0 0 ${height / plateLayout.format.rows}`}
                fill="none"
                stroke="#E5E7EB"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
        )}
        
        {showGrid && (
          <rect width="100%" height="100%" fill="url(#grid)" />
        )}

        {/* Axis Labels */}
        {showAxisLabels && (
          <g className="axis-labels">
            {/* Row labels */}
            {axisLabels.rowLabels.map((label, index) => {
              const y = (height * 0.1) + ((index + 0.5) * (height * 0.8) / plateLayout.format.rows);
              return (
                <text
                  key={`row-${label}`}
                  x={width * 0.05}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="text-xs fill-muted-foreground font-medium"
                >
                  {label}
                </text>
              );
            })}

            {/* Column labels */}
            {axisLabels.columnLabels.map((label, index) => {
              const x = (width * 0.1) + ((index + 0.5) * (width * 0.8) / plateLayout.format.columns);
              return (
                <text
                  key={`col-${label}`}
                  x={x}
                  y={height * 0.05}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="text-xs fill-muted-foreground font-medium"
                >
                  {label}
                </text>
              );
            })}
          </g>
        )}

        {/* Wells */}
        <g className="wells">
          {plateLayout.wells.map((well) => {
            const wellData = wellDataMap.get(well.wellId);
            if (!wellData) return null;

            const value = wellData[dataType];
            const colorMapping = mapValueToColor(value, activeColorScale);
            const isSelected = selectedWells.includes(well.wellId);
            const isViable = wellData.PassViab;

            return (
              <g key={well.wellId}>
                {/* Well background */}
                <circle
                  cx={well.x}
                  cy={well.y}
                  r={wellSize / 2}
                  fill={colorMapping.color}
                  stroke={isSelected ? "#2563EB" : (isViable ? "#D1D5DB" : "#EF4444")}
                  strokeWidth={isSelected ? 2 : 1}
                  className="cursor-pointer transition-all duration-200 hover:stroke-2"
                  onClick={() => handleWellClick(well)}
                  opacity={isViable ? 1 : 0.6}
                />

                {/* Non-viable indicator */}
                {!isViable && (
                  <circle
                    cx={well.x}
                    cy={well.y}
                    r={wellSize / 6}
                    fill="white"
                    stroke="#EF4444"
                    strokeWidth={1}
                    pointerEvents="none"
                  />
                )}

                {/* Hit indicator for strong Z-scores */}
                {isViable && (Math.abs(wellData.Z_lptA || 0) >= 2 || Math.abs(wellData.Z_ldtD || 0) >= 2) && (
                  <circle
                    cx={well.x + wellSize * 0.3}
                    cy={well.y - wellSize * 0.3}
                    r={wellSize / 8}
                    fill="#FFD700"
                    stroke="white"
                    strokeWidth={1}
                    pointerEvents="none"
                  />
                )}
              </g>
            );
          })}
        </g>

        {/* Selection indicator */}
        {selectedWells.length > 0 && (
          <g className="selection-info">
            <text
              x={width - 10}
              y={20}
              textAnchor="end"
              className="text-sm fill-primary font-medium"
            >
              {selectedWells.length} selected
            </text>
          </g>
        )}
      </svg>

      {/* Tooltip */}
      {showTooltips && (
        <HeatmapTooltip
          data={tooltipData}
          position={tooltipPosition}
          containerBounds={containerBounds}
        />
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="absolute bottom-2 left-2 text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
          ⚠️ {warnings.length} data warning{warnings.length > 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

export default PlateHeatmap;