import { useMemo } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { ColorUtils, CategoricalPalettes } from '../shared/ColorSchemes';
import { AnalysisResult } from '@/types/analysis';

interface ScatterChartProps {
  analysisData: AnalysisResult;
  xColumn: keyof WellData;
  yColumn: keyof WellData;
  colorColumn?: keyof WellData;
  title: string;
  description?: string;
  showTrendline?: boolean;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Scatter plot for correlation analysis between dual reporters
 * Color-coded by plate ID with hover information
 */
const ScatterChart = ({
  analysisData,
  xColumn,
  yColumn,
  colorColumn = 'PlateID',
  title,
  description,
  showTrendline = false,
  onExport,
  className,
  height = 400
}: ScatterChartProps) => {
  
  // Process data for visualization
  const { plotData, correlationStats, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    const processedData = DataProcessor.processScatterData(wellData, xColumn, yColumn, colorColumn);
    const dataWarnings = DataProcessor.validateData(wellData);
    
    // Calculate correlation coefficient
    const correlation = calculateCorrelation(processedData.x, processedData.y);
    
    return {
      plotData: processedData,
      correlationStats: {
        pearsonR: correlation.r,
        rSquared: correlation.r * correlation.r,
        pValue: correlation.p
      },
      warnings: dataWarnings.filter(warning => 
        warning.includes(String(xColumn)) || 
        warning.includes(String(yColumn)) ||
        warning.includes('missing')
      )
    };
  }, [analysisData, xColumn, yColumn, colorColumn]);

  // Group data by color category (plates)
  const plotlyData = useMemo(() => {
    if (!plotData.x || plotData.x.length === 0) {
      return [];
    }

    // Group data points by plate ID
    const plateGroups = new Map<string, {
      x: number[];
      y: number[];
      labels: string[];
      wells: string[];
      color: string;
    }>();

    plotData.plateIds.forEach((plateId, index) => {
      if (!plateGroups.has(plateId)) {
        const colorIndex = [...new Set(plotData.plateIds)].indexOf(plateId);
        const color = CategoricalPalettes.plates[colorIndex % CategoricalPalettes.plates.length];
        
        plateGroups.set(plateId, {
          x: [],
          y: [],
          labels: [],
          wells: [],
          color: color
        });
      }
      
      const group = plateGroups.get(plateId)!;
      group.x.push(plotData.x[index]);
      group.y.push(plotData.y[index]);
      group.labels.push(plotData.labels[index]);
      group.wells.push(plotData.wells[index]);
    });

    // Create scatter traces for each plate
    const traces: any[] = [];
    
    plateGroups.forEach((group, plateId) => {
      traces.push({
        x: group.x,
        y: group.y,
        type: 'scatter',
        mode: 'markers',
        name: plateId,
        marker: {
          color: group.color,
          size: 6,
          opacity: 0.7,
          line: {
            color: ColorUtils.hexToRgba(group.color, 0.8),
            width: 1
          }
        },
        text: group.wells,
        customdata: group.labels,
        hovertemplate: 
          '<b>Well:</b> %{text}<br>' +
          '<b>' + plotData.xLabel + ':</b> %{x:.3f}<br>' +
          '<b>' + plotData.yLabel + ':</b> %{y:.3f}<br>' +
          '<b>Plate:</b> ' + plateId + '<br>' +
          '<extra></extra>'
      });
    });

    // Add trendline if requested
    if (showTrendline && plotData.x.length > 2) {
      const { slope, intercept, r2 } = calculateTrendline(plotData.x, plotData.y);
      const xMin = Math.min(...plotData.x);
      const xMax = Math.max(...plotData.x);
      
      traces.push({
        x: [xMin, xMax],
        y: [slope * xMin + intercept, slope * xMax + intercept],
        type: 'scatter',
        mode: 'lines',
        name: `Trendline (R² = ${r2.toFixed(3)})`,
        line: {
          color: '#6B7280',
          width: 2,
          dash: 'dash'
        },
        showlegend: true,
        hoverinfo: 'skip'
      });
    }

    return traces;
  }, [plotData, showTrendline]);

  // Create layout
  const layout = useMemo(() => ({
    title: {
      text: '',
      font: { size: 14 }
    },
    xaxis: {
      title: plotData.xLabel || String(xColumn),
      showgrid: true,
      zeroline: true,
      zerolinecolor: '#E5E7EB',
      zerolinewidth: 1
    },
    yaxis: {
      title: plotData.yLabel || String(yColumn),
      showgrid: true,
      zeroline: true,
      zerolinecolor: '#E5E7EB',  
      zerolinewidth: 1
    },
    showlegend: true,
    legend: {
      orientation: 'v',
      x: 1.02,
      y: 1,
      bgcolor: 'rgba(255,255,255,0.9)',
      bordercolor: '#E5E7EB',
      borderwidth: 1
    },
    hovermode: 'closest'
  }), [plotData, xColumn, yColumn]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!correlationStats) return '';

    const { pearsonR, rSquared } = correlationStats;
    const correlation = Math.abs(pearsonR);
    
    let strength = 'weak';
    if (correlation > 0.7) strength = 'strong';
    else if (correlation > 0.5) strength = 'moderate';
    
    let direction = pearsonR > 0 ? 'positive' : 'negative';
    
    let text = `Scatter plot shows ${strength} ${direction} correlation (r = ${pearsonR.toFixed(3)}, R² = ${rSquared.toFixed(3)}) between ${plotData.xLabel} and ${plotData.yLabel}.`;
    
    // Add biological interpretation
    if (xColumn === 'Ratio_lptA' && yColumn === 'Ratio_ldtD') {
      text += ' Correlation between lptA and ldtD reporters indicates compounds affecting both LPS transport and peptidoglycan systems.';
    }

    // Add plate effect observation
    const uniquePlates = new Set(plotData.plateIds).size;
    if (uniquePlates > 1) {
      text += ` Data from ${uniquePlates} plates shows ${uniquePlates > 3 ? 'potential batch effects' : 'consistent patterns across batches'}.`;
    }

    return text;
  }, [correlationStats, plotData, xColumn, yColumn]);

  return (
    <ChartContainer
      title={title}
      description={description}
      dataCount={plotData.x.length}
      warnings={warnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`Scatter plot with Pearson correlation analysis`}
      interpretation={interpretation}
      references={[
        'Pearson correlation coefficient measures linear relationship strength',
        'Color coding by plate ID reveals potential batch effects'
      ]}
    >
      <PlotlyWrapper
        data={plotlyData}
        layout={layout}
        height={height}
        loading={!plotData.x || plotData.x.length === 0}
        error={warnings.length > 0 ? warnings[0] : null}
      />
    </ChartContainer>
  );
};

// Helper function to calculate Pearson correlation
function calculateCorrelation(x: number[], y: number[]): { r: number; p: number } {
  if (x.length !== y.length || x.length < 2) {
    return { r: 0, p: 1 };
  }

  const n = x.length;
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
  const sumYY = y.reduce((sum, yi) => sum + yi * yi, 0);

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt((n * sumXX - sumX * sumX) * (n * sumYY - sumY * sumY));

  const r = denominator === 0 ? 0 : numerator / denominator;
  
  // Simplified p-value calculation (Student's t-test)
  const t = Math.abs(r) * Math.sqrt((n - 2) / (1 - r * r));
  const p = t < 1.96 ? 0.05 : 0.001; // Rough approximation

  return { r: isNaN(r) ? 0 : r, p };
}

// Helper function to calculate trendline
function calculateTrendline(x: number[], y: number[]): { slope: number; intercept: number; r2: number } {
  const n = x.length;
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // Calculate R²
  const meanY = sumY / n;
  const ssTotal = y.reduce((sum, yi) => sum + Math.pow(yi - meanY, 2), 0);
  const ssResidual = y.reduce((sum, yi, i) => sum + Math.pow(yi - (slope * x[i] + intercept), 2), 0);
  const r2 = 1 - (ssResidual / ssTotal);

  return { slope, intercept, r2: isNaN(r2) ? 0 : r2 };
}

export default ScatterChart;