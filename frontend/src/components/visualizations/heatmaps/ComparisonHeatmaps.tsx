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
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

// Available metrics for comparison
export type ComparisonMetric = 'Z_lptA' | 'Z_ldtD' | 'B_lptA' | 'B_ldtD' | 'Ratio_lptA' | 'Ratio_ldtD';

interface ComparisonHeatmapsProps {
  analysisData: AnalysisResult;
  metric1?: ComparisonMetric;
  metric2?: ComparisonMetric;
  selectedPlateId?: string;
  title?: string;
  description?: string;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Side-by-side comparison heatmaps (e.g., Raw Z vs B-score)
 * Shows plate layout with synchronized color scales for direct comparison
 */
const ComparisonHeatmaps = ({
  analysisData,
  metric1 = 'Z_lptA',
  metric2 = 'B_lptA',
  selectedPlateId,
  title,
  description,
  onExport,
  className,
  height = 500
}: ComparisonHeatmapsProps) => {
  
  // Internal state for metric selection if not controlled
  const [internalMetric1, setInternalMetric1] = useState<ComparisonMetric>(metric1);
  const [internalMetric2, setInternalMetric2] = useState<ComparisonMetric>(metric2);
  const [internalPlateId, setInternalPlateId] = useState<string>(selectedPlateId || '');

  // Use controlled or internal state
  const currentMetric1 = metric1 || internalMetric1;
  const currentMetric2 = metric2 || internalMetric2;
  const currentPlateId = selectedPlateId || internalPlateId;

  // Process data for comparison heatmaps
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
    const plates = [...new Set(wellData.map(well => well.PlateID))].sort();
    
    // Filter by selected plate if specified
    let filteredData = wellData;
    if (currentPlateId) {
      filteredData = wellData.filter(well => well.PlateID === currentPlateId);
      if (filteredData.length === 0) {
        return {
          chartData: null,
          plateOptions: plates,
          stats: null,
          warnings: [`No data found for plate ${currentPlateId}`]
        };
      }
    }
    
    // Extract data for both metrics
    const metric1Data = filteredData
      .map(well => well[currentMetric1])
      .filter(val => val !== null && val !== undefined && !isNaN(val));
    
    const metric2Data = filteredData
      .map(well => well[currentMetric2])
      .filter(val => val !== null && val !== undefined && !isNaN(val));
    
    if (metric1Data.length === 0 && metric2Data.length === 0) {
      return {
        chartData: null,
        plateOptions: plates,
        stats: null,
        warnings: ['No valid data for selected metrics']
      };
    }
    
    // Detect plate format
    const plateFormat: PlateFormat = filteredData.some(well => {
      const match = well.Well?.match(/^[A-P]/);
      return match && match[0] > 'H';
    }) ? '384-well' : '96-well';
    
    const layout = createPlateLayout(plateFormat);
    
    // Calculate common color scale range
    const allData = [...metric1Data, ...metric2Data];
    const absMax = Math.max(...allData.map(Math.abs));
    const colorRange = [-absMax, absMax];
    
    // Create matrices for both metrics
    const matrix1 = Array(layout.rows).fill(null).map(() => Array(layout.cols).fill(null));
    const matrix2 = Array(layout.rows).fill(null).map(() => Array(layout.cols).fill(null));
    const hoverText1 = Array(layout.rows).fill(null).map(() => Array(layout.cols).fill(''));
    const hoverText2 = Array(layout.rows).fill(null).map(() => Array(layout.cols).fill(''));
    
    // Fill matrices
    for (const well of filteredData) {
      const wellMatch = well.Well?.match(/^([A-P])(\d+)$/);
      if (!wellMatch) continue;
      
      const rowLetter = wellMatch[1];
      const colNumber = parseInt(wellMatch[2]);
      const rowIdx = rowLetter.charCodeAt(0) - 'A'.charCodeAt(0);
      const colIdx = colNumber - 1;
      
      if (rowIdx >= 0 && rowIdx < layout.rows && colIdx >= 0 && colIdx < layout.cols) {
        const value1 = well[currentMetric1];
        const value2 = well[currentMetric2];
        
        matrix1[rowIdx][colIdx] = value1;
        matrix2[rowIdx][colIdx] = value2;
        
        hoverText1[rowIdx][colIdx] = `Well: ${well.Well}<br>${currentMetric1}: ${value1?.toFixed(3) || 'N/A'}`;
        hoverText2[rowIdx][colIdx] = `Well: ${well.Well}<br>${currentMetric2}: ${value2?.toFixed(3) || 'N/A'}`;
      }
    }
    
    // Calculate statistics
    const calculateStats = (data: number[]) => ({
      mean: data.reduce((sum, val) => sum + val, 0) / data.length,
      std: Math.sqrt(data.reduce((sum, val) => {
        const mean = data.reduce((s, v) => s + v, 0) / data.length;
        return sum + Math.pow(val - mean, 2);
      }, 0) / data.length),
      min: Math.min(...data),
      max: Math.max(...data),
      count: data.length
    });
    
    const dataWarnings = DataProcessor.validateData(wellData);
    
    return {
      chartData: {
        matrix1,
        matrix2,
        hoverText1,
        hoverText2,
        layout,
        colorRange,
        plateFormat
      },
      plateOptions: plates,
      stats: {
        metric1: metric1Data.length > 0 ? calculateStats(metric1Data) : null,
        metric2: metric2Data.length > 0 ? calculateStats(metric2Data) : null
      },
      warnings: dataWarnings
    };
  }, [analysisData, currentMetric1, currentMetric2, currentPlateId]);

  // Create Plotly data for side-by-side heatmaps
  const plotlyData = useMemo(() => {
    if (!chartData) return [];
    
    const { matrix1, matrix2, hoverText1, hoverText2, layout, colorRange } = chartData;
    const { rowLabels, colLabels } = generateAxisLabels(layout);
    
    // Define colorscale for diverging data (Z-scores, B-scores)
    const colorscale = [
      [0, '#3B82F6'],    // Blue (negative)
      [0.5, '#FFFFFF'],  // White (zero)
      [1, '#EF4444']     // Red (positive)
    ];
    
    return [
      {
        z: matrix1,
        x: colLabels,
        y: rowLabels,
        type: 'heatmap',
        colorscale: colorscale,
        zmin: colorRange[0],
        zmax: colorRange[1],
        zmid: 0,
        hovertemplate: '%{text}<extra></extra>',
        text: hoverText1,
        showscale: false, // Hide colorbar for first plot
        xaxis: 'x',
        yaxis: 'y'
      },
      {
        z: matrix2,
        x: colLabels,
        y: rowLabels,
        type: 'heatmap',
        colorscale: colorscale,
        zmin: colorRange[0],
        zmax: colorRange[1],
        zmid: 0,
        hovertemplate: '%{text}<extra></extra>',
        text: hoverText2,
        showscale: true, // Show colorbar for second plot
        colorbar: {
          title: 'Score',
          titleside: 'right',
          thickness: 15,
          len: 0.8
        },
        xaxis: 'x2',
        yaxis: 'y2'
      }
    ];
  }, [chartData]);

  // Create layout for side-by-side subplots
  const layout = useMemo(() => {
    if (!chartData) return {};
    
    const { layout: plateLayout } = chartData;
    const { rowLabels, colLabels } = generateAxisLabels(plateLayout);
    
    return {
      title: {
        text: '',
        font: { size: 14 }
      },
      // First heatmap (left)
      xaxis: {
        domain: [0, 0.45],
        title: 'Column',
        side: 'top',
        tickmode: 'array',
        tickvals: colLabels.map((_, i) => i),
        ticktext: colLabels,
        showgrid: false
      },
      yaxis: {
        title: 'Row',
        tickmode: 'array',
        tickvals: rowLabels.map((_, i) => i),
        ticktext: rowLabels,
        autorange: 'reversed', // A at top
        showgrid: false,
        scaleanchor: 'x',
        scaleratio: 1
      },
      // Second heatmap (right)
      xaxis2: {
        domain: [0.55, 1],
        title: 'Column',
        side: 'top',
        tickmode: 'array',
        tickvals: colLabels.map((_, i) => i),
        ticktext: colLabels,
        showgrid: false
      },
      yaxis2: {
        anchor: 'x2',
        tickmode: 'array',
        tickvals: rowLabels.map((_, i) => i),
        ticktext: rowLabels,
        autorange: 'reversed', // A at top
        showgrid: false,
        showticklabels: false, // Hide for cleaner look
        scaleanchor: 'x2',
        scaleratio: 1
      },
      // Subplot titles
      annotations: [
        {
          x: 0.225, y: 1.05,
          xref: 'paper', yref: 'paper',
          text: `<b>${currentMetric1.replace('_', ' ')}</b>`,
          showarrow: false,
          font: { size: 14 }
        },
        {
          x: 0.775, y: 1.05,
          xref: 'paper', yref: 'paper',
          text: `<b>${currentMetric2.replace('_', ' ')}</b>`,
          showarrow: false,
          font: { size: 14 }
        }
      ],
      showlegend: false,
      plot_bgcolor: 'white',
      paper_bgcolor: 'white'
    };
  }, [chartData, currentMetric1, currentMetric2]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!stats) return '';
    
    let text = `Comparing ${currentMetric1.replace('_', ' ')} vs ${currentMetric2.replace('_', ' ')} `;
    
    if (currentPlateId) {
      text += `for plate ${currentPlateId}. `;
    } else {
      text += 'across all plates. ';
    }
    
    if (stats.metric1 && stats.metric2) {
      text += `First metric: μ=${stats.metric1.mean.toFixed(2)}, σ=${stats.metric1.std.toFixed(2)}. `;
      text += `Second metric: μ=${stats.metric2.mean.toFixed(2)}, σ=${stats.metric2.std.toFixed(2)}. `;
      
      // Analyze differences
      const meanDiff = Math.abs(stats.metric1.mean - stats.metric2.mean);
      const stdDiff = Math.abs(stats.metric1.std - stats.metric2.std);
      
      if (currentMetric1.startsWith('Z_') && currentMetric2.startsWith('B_')) {
        if (meanDiff < 0.1 && stdDiff < 0.2) {
          text += 'Both metrics show similar normalization, indicating minimal systematic bias correction needed.';
        } else {
          text += 'B-scoring has altered the distribution compared to raw Z-scores, suggesting systematic bias correction.';
        }
      } else {
        text += 'Side-by-side comparison reveals spatial patterns and differences between the two metrics.';
      }
    }
    
    return text;
  }, [stats, currentMetric1, currentMetric2, currentPlateId]);

  // Generate default title
  const chartTitle = title || `${currentMetric1.replace('_', ' ')} vs ${currentMetric2.replace('_', ' ')} Comparison${currentPlateId ? ` - Plate ${currentPlateId}` : ''}`;

  // Available metrics for selection
  const metricOptions: { value: ComparisonMetric; label: string }[] = [
    { value: 'Z_lptA', label: 'Z-score lptA' },
    { value: 'Z_ldtD', label: 'Z-score ldtD' },
    { value: 'B_lptA', label: 'B-score lptA' },
    { value: 'B_ldtD', label: 'B-score ldtD' },
    { value: 'Ratio_lptA', label: 'Ratio lptA' },
    { value: 'Ratio_ldtD', label: 'Ratio ldtD' }
  ];

  return (
    <ChartContainer
      title={chartTitle}
      description={description || 'Side-by-side heatmap comparison showing spatial distribution patterns'}
      dataCount={stats?.metric1?.count || stats?.metric2?.count || 0}
      warnings={warnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`Plate heatmap comparison with synchronized color scales`}
      interpretation={interpretation}
      references={[
        'Spatial patterns may indicate edge effects or systematic biases',
        'Color scale synchronized for direct visual comparison',
        'Missing wells appear as gaps in the heatmap'
      ]}
    >
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Metric 1:</label>
          <Select value={currentMetric1} onValueChange={(value: ComparisonMetric) => setInternalMetric1(value)}>
            <SelectTrigger className="w-32">
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
        
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Metric 2:</label>
          <Select value={currentMetric2} onValueChange={(value: ComparisonMetric) => setInternalMetric2(value)}>
            <SelectTrigger className="w-32">
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
        
        {plateOptions && plateOptions.length > 1 && (
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Plate:</label>
            <Select value={currentPlateId} onValueChange={setInternalPlateId}>
              <SelectTrigger className="w-24">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Plates</SelectItem>
                {plateOptions.map(plate => (
                  <SelectItem key={plate} value={plate}>
                    {plate}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
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

export default ComparisonHeatmaps;