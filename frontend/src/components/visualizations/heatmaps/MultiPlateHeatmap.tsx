import { useMemo, useState } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { 
  createPlateLayout, 
  generateAxisLabels, 
  WellPosition,
  PlateFormat 
} from '../shared/WellPositionMapper';
import { CoreColors } from '../shared/ColorSchemes';
import { AnalysisResult } from '@/types/analysis';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';

// Available metrics for visualization
export type MultiPlateMetric = 'Z_lptA' | 'Z_ldtD' | 'B_lptA' | 'B_ldtD' | 'Ratio_lptA' | 'Ratio_ldtD' | 'PassViab';

interface MultiPlateHeatmapProps {
  analysisData: AnalysisResult;
  metric?: MultiPlateMetric;
  maxPlates?: number;
  title?: string;
  description?: string;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Multiple heatmaps for comparing the same metric across plates
 * Displays up to 9 plates in a grid layout with synchronized color scales
 */
const MultiPlateHeatmap = ({
  analysisData,
  metric = 'Z_lptA',
  maxPlates = 6,
  title,
  description,
  onExport,
  className,
  height = 600
}: MultiPlateHeatmapProps) => {
  
  // Internal state for metric selection
  const [selectedMetric, setSelectedMetric] = useState<MultiPlateMetric>(metric);
  const [selectedPlates, setSelectedPlates] = useState<string[]>([]);

  // Process data for multi-plate heatmaps
  const { chartData, plateOptions, stats, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    
    if (!wellData || wellData.length === 0) {
      return {
        chartData: null,
        plateOptions: [],
        stats: null,
        warnings: ['No well data available']
      };
    }
    
    // Get available plates
    const allPlates = [...new Set(wellData.map(well => well.PlateID))].sort();
    const platesToShow = selectedPlates.length > 0 ? selectedPlates : allPlates.slice(0, maxPlates);
    
    if (platesToShow.length === 0) {
      return {
        chartData: null,
        plateOptions: allPlates,
        stats: null,
        warnings: ['No plates selected for display']
      };
    }
    
    // Filter data for selected plates
    const filteredData = wellData.filter(well => platesToShow.includes(well.PlateID));
    
    // Extract metric data
    const metricData = filteredData
      .map(well => well[selectedMetric])
      .filter(val => val !== null && val !== undefined && !isNaN(val));
    
    if (metricData.length === 0) {
      return {
        chartData: null,
        plateOptions: allPlates,
        stats: null,
        warnings: [`No valid data for ${selectedMetric} in selected plates`]
      };
    }
    
    // Detect plate format
    const plateFormat: PlateFormat = filteredData.some(well => {
      const match = well.Well?.match(/^[A-P]/);
      return match && match[0] > 'H';
    }) ? '384-well' : '96-well';
    
    const layout = createPlateLayout(plateFormat);
    
    // Determine subplot grid layout
    const nPlates = platesToShow.length;
    let gridRows: number, gridCols: number;
    
    if (nPlates <= 2) {
      gridRows = 1;
      gridCols = nPlates;
    } else if (nPlates <= 4) {
      gridRows = 2;
      gridCols = 2;
    } else if (nPlates <= 6) {
      gridRows = 2;
      gridCols = 3;
    } else {
      gridRows = 3;
      gridCols = 3;
    }
    
    // Calculate color scale range
    let colorRange: [number, number];
    let colorMid: number | null = null;
    
    if (selectedMetric.startsWith('Z_') || selectedMetric.startsWith('B_')) {
      // Diverging colormap centered at 0
      const absMax = Math.max(...metricData.map(Math.abs));
      colorRange = [-absMax, absMax];
      colorMid = 0;
    } else {
      // Sequential colormap
      colorRange = [Math.min(...metricData), Math.max(...metricData)];
    }
    
    // Create matrices for each plate
    const plateMatrices: { [plateId: string]: {
      matrix: (number | null)[][];
      hoverText: string[][];
    }} = {};
    
    for (const plateId of platesToShow) {
      const plateData = filteredData.filter(well => well.PlateID === plateId);
      
      const matrix = Array(layout.rows).fill(null).map(() => Array(layout.cols).fill(null));
      const hoverText = Array(layout.rows).fill(null).map(() => Array(layout.cols).fill(''));
      
      for (const well of plateData) {
        const wellMatch = well.Well?.match(/^([A-P])(\d+)$/);
        if (!wellMatch) continue;
        
        const rowLetter = wellMatch[1];
        const colNumber = parseInt(wellMatch[2]);
        const rowIdx = rowLetter.charCodeAt(0) - 'A'.charCodeAt(0);
        const colIdx = colNumber - 1;
        
        if (rowIdx >= 0 && rowIdx < layout.rows && colIdx >= 0 && colIdx < layout.cols) {
          const value = well[selectedMetric];
          matrix[rowIdx][colIdx] = value;
          
          if (value !== null && value !== undefined && !isNaN(value)) {
            hoverText[rowIdx][colIdx] = `Plate: ${plateId}<br>Well: ${well.Well}<br>${selectedMetric}: ${value.toFixed(3)}`;
          } else {
            hoverText[rowIdx][colIdx] = `Plate: ${plateId}<br>Well: ${well.Well}<br>No data`;
          }
        }
      }
      
      plateMatrices[plateId] = { matrix, hoverText };
    }
    
    // Calculate statistics per plate
    const plateStats: { [plateId: string]: { mean: number; std: number; count: number } } = {};
    for (const plateId of platesToShow) {
      const plateData = filteredData
        .filter(well => well.PlateID === plateId)
        .map(well => well[selectedMetric])
        .filter(val => val !== null && val !== undefined && !isNaN(val));
      
      if (plateData.length > 0) {
        const mean = plateData.reduce((sum, val) => sum + val, 0) / plateData.length;
        const variance = plateData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / plateData.length;
        plateStats[plateId] = {
          mean,
          std: Math.sqrt(variance),
          count: plateData.length
        };
      }
    }
    
    const dataWarnings = DataProcessor.validateData(wellData);
    
    return {
      chartData: {
        plateMatrices,
        platesToShow,
        layout,
        colorRange,
        colorMid,
        gridRows,
        gridCols,
        plateFormat
      },
      plateOptions: allPlates,
      stats: plateStats,
      warnings: dataWarnings
    };
  }, [analysisData, selectedMetric, selectedPlates, maxPlates]);

  // Create Plotly data for multi-plate heatmaps
  const plotlyData = useMemo(() => {
    if (!chartData) return [];
    
    const { plateMatrices, platesToShow, layout, colorRange, colorMid } = chartData;
    const { rowLabels, colLabels } = generateAxisLabels(layout);
    
    // Define colorscale
    const colorscale = selectedMetric.startsWith('Z_') || selectedMetric.startsWith('B_') 
      ? [
          [0, '#3B82F6'],    // Blue (negative)
          [0.5, '#FFFFFF'],  // White (zero)
          [1, '#EF4444']     // Red (positive)
        ]
      : [
          [0, '#FFFFFF'],    // White (low)
          [1, '#1F2937']     // Dark (high)
        ];
    
    return platesToShow.map((plateId, index) => {
      const { matrix, hoverText } = plateMatrices[plateId];
      const showColorbar = index === platesToShow.length - 1; // Only show colorbar for last plot
      
      // Calculate subplot position
      const row = Math.floor(index / chartData.gridCols) + 1;
      const col = (index % chartData.gridCols) + 1;
      
      const trace: any = {
        z: matrix,
        x: colLabels,
        y: rowLabels,
        type: 'heatmap',
        colorscale: colorscale,
        zmin: colorRange[0],
        zmax: colorRange[1],
        hovertemplate: '%{text}<extra></extra>',
        text: hoverText,
        showscale: showColorbar,
        xaxis: chartData.gridRows > 1 || chartData.gridCols > 1 ? `x${index === 0 ? '' : index + 1}` : 'x',
        yaxis: chartData.gridRows > 1 || chartData.gridCols > 1 ? `y${index === 0 ? '' : index + 1}` : 'y'
      };
      
      if (colorMid !== null) {
        trace.zmid = colorMid;
      }
      
      if (showColorbar) {
        trace.colorbar = {
          title: selectedMetric.replace('_', ' '),
          titleside: 'right',
          thickness: 15,
          len: 0.6
        };
      }
      
      return trace;
    });
  }, [chartData, selectedMetric]);

  // Create layout for multi-plate subplots
  const layout = useMemo(() => {
    if (!chartData) return {};
    
    const { platesToShow, layout: plateLayout, gridRows, gridCols } = chartData;
    const { rowLabels, colLabels } = generateAxisLabels(plateLayout);
    
    const baseLayout: any = {
      title: {
        text: '',
        font: { size: 14 }
      },
      showlegend: false,
      plot_bgcolor: 'white',
      paper_bgcolor: 'white',
      annotations: []
    };
    
    // Create axes and annotations for each subplot
    for (let i = 0; i < platesToShow.length; i++) {
      const plateId = platesToShow[i];
      const row = Math.floor(i / gridCols) + 1;
      const col = (i % gridCols) + 1;
      
      // Calculate subplot domain
      const xDomain = [
        (col - 1) / gridCols + 0.02,
        col / gridCols - 0.02
      ];
      const yDomain = [
        (gridRows - row) / gridRows + 0.02,
        (gridRows - row + 1) / gridRows - 0.02
      ];
      
      const axisPrefix = i === 0 ? '' : (i + 1).toString();
      
      // Set up axes
      baseLayout[`xaxis${axisPrefix}`] = {
        domain: xDomain,
        showticklabels: false,
        showgrid: false,
        zeroline: false
      };
      
      baseLayout[`yaxis${axisPrefix}`] = {
        domain: yDomain,
        showticklabels: false,
        showgrid: false,
        zeroline: false,
        autorange: 'reversed', // A at top
        scaleanchor: `x${axisPrefix}`,
        scaleratio: 1
      };
      
      // Add plate title annotation
      baseLayout.annotations.push({
        x: xDomain[0] + (xDomain[1] - xDomain[0]) / 2,
        y: yDomain[1] + 0.03,
        text: `<b>Plate ${plateId}</b>`,
        showarrow: false,
        font: { size: 12 },
        xref: 'paper',
        yref: 'paper'
      });
      
      // Add statistics annotation if available
      if (stats && stats[plateId]) {
        const stat = stats[plateId];
        baseLayout.annotations.push({
          x: xDomain[0] + 0.02,
          y: yDomain[0] + 0.02,
          text: `μ=${stat.mean.toFixed(2)}<br>σ=${stat.std.toFixed(2)}<br>n=${stat.count}`,
          showarrow: false,
          font: { size: 9 },
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: '#E5E7EB',
          borderwidth: 1,
          xref: 'paper',
          yref: 'paper',
          align: 'left'
        });
      }
    }
    
    return baseLayout;
  }, [chartData, stats]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!stats || !chartData) return '';
    
    const { platesToShow } = chartData;
    const statValues = Object.values(stats).filter(s => s !== undefined);
    
    if (statValues.length === 0) return '';
    
    const avgMean = statValues.reduce((sum, s) => sum + s.mean, 0) / statValues.length;
    const avgStd = statValues.reduce((sum, s) => sum + s.std, 0) / statValues.length;
    const meanVariation = Math.sqrt(statValues.reduce((sum, s) => sum + Math.pow(s.mean - avgMean, 2), 0) / statValues.length);
    
    let text = `Comparing ${selectedMetric.replace('_', ' ')} across ${platesToShow.length} plates. `;
    text += `Overall mean: ${avgMean.toFixed(2)} ± ${avgStd.toFixed(2)}. `;
    
    if (meanVariation < 0.1) {
      text += 'Minimal inter-plate variation suggests consistent assay performance. ';
    } else if (meanVariation < 0.3) {
      text += 'Moderate inter-plate variation within acceptable range. ';
    } else {
      text += 'High inter-plate variation may indicate batch effects or assay drift. ';
    }
    
    // Add metric-specific insights
    if (selectedMetric.startsWith('Z_') || selectedMetric.startsWith('B_')) {
      text += 'Well-normalized plates should show μ≈0, σ≈1. ';
    } else if (selectedMetric.startsWith('Ratio_')) {
      text += 'Reporter ratios indicate outer membrane disruption activity. ';
    } else if (selectedMetric === 'PassViab') {
      text += 'Viability patterns show metabolically active regions. ';
    }
    
    text += 'Spatial patterns may reveal systematic effects or contamination issues.';
    
    return text;
  }, [stats, chartData, selectedMetric]);

  // Generate default title
  const chartTitle = title || `${selectedMetric.replace('_', ' ')} Across Multiple Plates`;

  // Available metrics for selection
  const metricOptions: { value: MultiPlateMetric; label: string }[] = [
    { value: 'Z_lptA', label: 'Z-score lptA' },
    { value: 'Z_ldtD', label: 'Z-score ldtD' },
    { value: 'B_lptA', label: 'B-score lptA' },
    { value: 'B_ldtD', label: 'B-score ldtD' },
    { value: 'Ratio_lptA', label: 'Ratio lptA' },
    { value: 'Ratio_ldtD', label: 'Ratio ldtD' },
    { value: 'PassViab', label: 'Viability' }
  ];

  return (
    <ChartContainer
      title={chartTitle}
      description={description || `Multiple plate heatmaps showing ${selectedMetric.replace('_', ' ')} distribution patterns`}
      dataCount={stats ? Object.values(stats).reduce((sum, s) => sum + (s?.count || 0), 0) : 0}
      warnings={warnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`Multi-plate heatmap visualization with synchronized color scales`}
      interpretation={interpretation}
      references={[
        'Synchronized color scales enable direct comparison between plates',
        'Spatial patterns may indicate edge effects or systematic biases',
        'Statistics overlay shows plate-specific normalization quality'
      ]}
    >
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Metric:</label>
          <Select value={selectedMetric} onValueChange={(value: MultiPlateMetric) => setSelectedMetric(value)}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {metricOptions.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {plateOptions && plateOptions.length > maxPlates && (
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Max Plates:</label>
            <span className="text-sm text-gray-600">{Math.min(maxPlates, plateOptions.length)}</span>
          </div>
        )}
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">
            Showing {chartData?.platesToShow.length || 0} of {plateOptions.length} plates
          </span>
        </div>
      </div>

      <PlotlyWrapper
        data={plotlyData}
        layout={layout}
        height={height}
        loading={!chartData}
        error={warnings.length > 0 ? warnings[0] : null}
      />
    </ChartContainer>
  );
};

export default MultiPlateHeatmap;