import { useMemo } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { CoreColors } from '../shared/ColorSchemes';
import { AnalysisResult } from '@/types/analysis';

// Available metrics for comparison
export type MetricColumn = 'Z_lptA' | 'Z_ldtD' | 'B_lptA' | 'B_ldtD' | 'Ratio_lptA' | 'Ratio_ldtD' | 'OD_WT' | 'OD_tolC' | 'OD_SA';

interface MultiMetricHistogramProps {
  analysisData: AnalysisResult;
  columns: MetricColumn[];
  title?: string;
  description?: string;
  overlay?: boolean; // If true, overlay histograms; if false, create subplots
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Compare multiple metrics on the same plot
 * Supports both overlay mode and subplot mode
 */
const MultiMetricHistogram = ({
  analysisData,
  columns,
  title,
  description,
  overlay = true,
  onExport,
  className,
  height = 400
}: MultiMetricHistogramProps) => {
  
  // Process data for all metrics
  const { chartData, stats, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    
    // Extract data for each column
    const metricData: { [key: string]: number[] } = {};
    const metricStats: { [key: string]: { mean: number; std: number; count: number; min: number; max: number } } = {};
    
    let hasValidData = false;
    
    for (const col of columns) {
      const rawData = wellData
        .map(well => well[col])
        .filter(val => val !== null && val !== undefined && !isNaN(val));
      
      if (rawData.length > 0) {
        metricData[col] = rawData;
        
        const mean = rawData.reduce((sum, val) => sum + val, 0) / rawData.length;
        const variance = rawData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / rawData.length;
        const std = Math.sqrt(variance);
        
        metricStats[col] = {
          mean,
          std,
          count: rawData.length,
          min: Math.min(...rawData),
          max: Math.max(...rawData)
        };
        
        hasValidData = true;
      }
    }
    
    if (!hasValidData) {
      return {
        chartData: null,
        stats: null,
        warnings: ['No valid data found for selected metrics']
      };
    }
    
    const dataWarnings = DataProcessor.validateData(wellData);
    
    return {
      chartData: metricData,
      stats: metricStats,
      warnings: dataWarnings
    };
  }, [analysisData, columns]);

  // Generate colors for metrics
  const metricColors = useMemo(() => {
    const colorPalette = [
      CoreColors.primary,
      CoreColors.secondary,
      CoreColors.accent,
      CoreColors.success,
      CoreColors.warning,
      CoreColors.info,
      '#8B5CF6', // Purple
      '#F59E0B', // Amber
      '#EF4444', // Red
      '#10B981'  // Emerald
    ];
    
    const colors: { [key: string]: string } = {};
    columns.forEach((col, index) => {
      colors[col] = colorPalette[index % colorPalette.length];
    });
    
    return colors;
  }, [columns]);

  // Create Plotly data
  const plotlyData = useMemo(() => {
    if (!chartData) return [];
    
    if (overlay) {
      // Overlay mode - all histograms on same plot
      return columns
        .filter(col => chartData[col])
        .map((col, index) => ({
          x: chartData[col],
          type: 'histogram',
          name: col.replace('_', ' '),
          marker: {
            color: metricColors[col],
            opacity: 0.6
          },
          nbinsx: 30,
          hovertemplate: 
            `<b>${col.replace('_', ' ')}</b><br>` +
            'Value: %{x:.3f}<br>' +
            'Count: %{y}<br>' +
            '<extra></extra>'
        }));
    } else {
      // Subplot mode - separate histogram for each metric
      const validColumns = columns.filter(col => chartData[col]);
      const nCols = Math.min(2, validColumns.length);
      const nRows = Math.ceil(validColumns.length / nCols);
      
      return validColumns.map((col, index) => {
        const row = Math.floor(index / nCols) + 1;
        const colIdx = (index % nCols) + 1;
        
        return {
          x: chartData[col],
          type: 'histogram',
          name: col.replace('_', ' '),
          marker: {
            color: metricColors[col],
            opacity: 0.7
          },
          nbinsx: 30,
          showlegend: false,
          xaxis: nCols > 1 || nRows > 1 ? `x${index === 0 ? '' : index + 1}` : 'x',
          yaxis: nCols > 1 || nRows > 1 ? `y${index === 0 ? '' : index + 1}` : 'y',
          hovertemplate: 
            `<b>${col.replace('_', ' ')}</b><br>` +
            'Value: %{x:.3f}<br>' +
            'Count: %{y}<br>' +
            '<extra></extra>'
        };
      });
    }
  }, [chartData, columns, overlay, metricColors]);

  // Create layout
  const layout = useMemo(() => {
    if (!chartData) return {};
    
    if (overlay) {
      // Overlay layout
      return {
        title: {
          text: '',
          font: { size: 14 }
        },
        xaxis: {
          title: 'Value',
          showgrid: true,
          gridcolor: '#E5E7EB'
        },
        yaxis: {
          title: 'Frequency',
          showgrid: true,
          gridcolor: '#E5E7EB'
        },
        barmode: 'overlay',
        showlegend: true,
        legend: {
          orientation: 'h',
          x: 0.5,
          xanchor: 'center',
          y: 1.1,
          bgcolor: 'rgba(255,255,255,0.9)',
          bordercolor: '#E5E7EB',
          borderwidth: 1
        }
      };
    } else {
      // Subplot layout
      const validColumns = columns.filter(col => chartData[col]);
      const nCols = Math.min(2, validColumns.length);
      const nRows = Math.ceil(validColumns.length / nCols);
      
      const subplotLayout: any = {
        title: {
          text: '',
          font: { size: 14 }
        },
        showlegend: false,
        annotations: []
      };
      
      // Create axes for subplots
      for (let i = 0; i < validColumns.length; i++) {
        const row = Math.floor(i / nCols) + 1;
        const colIdx = (i % nCols) + 1;
        const col = validColumns[i];
        
        const xDomain = [
          (colIdx - 1) / nCols + 0.02,
          colIdx / nCols - 0.02
        ];
        const yDomain = [
          (nRows - row) / nRows + 0.02,
          (nRows - row + 1) / nRows - 0.02
        ];
        
        const axisPrefix = i === 0 ? '' : (i + 1).toString();
        
        subplotLayout[`xaxis${axisPrefix}`] = {
          domain: xDomain,
          title: col.replace('_', ' '),
          showgrid: true,
          gridcolor: '#E5E7EB'
        };
        
        subplotLayout[`yaxis${axisPrefix}`] = {
          domain: yDomain,
          title: i % nCols === 0 ? 'Frequency' : '',
          showgrid: true,
          gridcolor: '#E5E7EB'
        };
        
        // Add subplot title annotation
        subplotLayout.annotations.push({
          x: xDomain[0] + (xDomain[1] - xDomain[0]) / 2,
          y: yDomain[1] + 0.03,
          text: `<b>${col.replace('_', ' ')}</b>`,
          showarrow: false,
          font: { size: 12 },
          xref: 'paper',
          yref: 'paper'
        });
      }
      
      return subplotLayout;
    }
  }, [chartData, columns, overlay]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!stats) return '';
    
    const validMetrics = Object.keys(stats);
    let text = `Comparing distributions of ${validMetrics.length} metric${validMetrics.length > 1 ? 's' : ''}: ${validMetrics.map(col => col.replace('_', ' ')).join(', ')}. `;
    
    // Analyze distribution characteristics
    const zScores = validMetrics.filter(col => col.startsWith('Z_') || col.startsWith('B_'));
    const ratios = validMetrics.filter(col => col.startsWith('Ratio_'));
    const ods = validMetrics.filter(col => col.startsWith('OD_'));
    
    if (zScores.length > 0) {
      const wellNormalized = zScores.filter(col => Math.abs(stats[col].mean) < 0.1 && Math.abs(stats[col].std - 1) < 0.2);
      if (wellNormalized.length === zScores.length) {
        text += 'All Z-score metrics are well-normalized (μ≈0, σ≈1). ';
      } else if (wellNormalized.length > 0) {
        text += `${wellNormalized.length}/${zScores.length} Z-score metrics show good normalization. `;
      } else {
        text += 'Z-score normalization may be suboptimal, check for outliers or data quality issues. ';
      }
    }
    
    if (ratios.length > 0) {
      const avgRatio = ratios.reduce((sum, col) => sum + stats[col].mean, 0) / ratios.length;
      if (avgRatio > 1.2) {
        text += 'Reporter ratios are elevated, suggesting potential bioactivity. ';
      } else if (avgRatio < 0.8) {
        text += 'Reporter ratios are reduced, may indicate cytotoxic effects. ';
      } else {
        text += 'Reporter ratios centered around baseline levels. ';
      }
    }
    
    if (ods.length > 0) {
      text += 'OD measurements reflect bacterial growth and culture density. ';
    }
    
    return text.trim();
  }, [stats]);

  // Generate default title if not provided
  const chartTitle = title || `Multi-Metric Distribution Comparison${overlay ? ' (Overlay)' : ' (Subplots)'}`;

  return (
    <ChartContainer
      title={chartTitle}
      description={description || `Compare distributions of ${columns.length} metrics ${overlay ? 'overlaid on the same plot' : 'in separate subplots'}`}
      dataCount={stats ? Math.max(...Object.values(stats).map(s => s.count)) : 0}
      warnings={warnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`Histogram comparison of selected metrics${overlay ? ' with overlay visualization' : ' with subplot layout'}`}
      interpretation={interpretation}
      references={[
        'Z-scores and B-scores should be normalized (μ≈0, σ≈1)',
        'Reporter ratios (BG/BT) indicate outer membrane disruption',
        'OD measurements reflect bacterial growth density'
      ]}
    >
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

export default MultiMetricHistogram;