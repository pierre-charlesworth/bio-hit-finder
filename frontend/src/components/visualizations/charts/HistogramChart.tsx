import { useMemo } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { CoreColors } from '../shared/ColorSchemes';
import { AnalysisResult } from '@/types/analysis';

interface HistogramChartProps {
  analysisData: AnalysisResult;
  column: keyof WellData;
  title: string;
  description?: string;
  color?: string;
  threshold?: number;
  showThresholds?: boolean;
  bins?: number;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Histogram chart for Z-score distributions with threshold visualization
 * Matches the original Streamlit implementation
 */
const HistogramChart = ({
  analysisData,
  column,
  title,
  description,
  color = CoreColors.reporterHits,
  threshold = 2.0,
  showThresholds = true,
  bins = 50,
  onExport,
  className,
  height = 400
}: HistogramChartProps) => {
  
  // Process data for visualization
  const { plotData, statistics, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    const processedData = DataProcessor.processHistogramData(wellData, column, title, color, threshold);
    const stats = DataProcessor.calculateStatistics(processedData.values);
    const dataWarnings = DataProcessor.validateData(wellData);
    
    return {
      plotData: processedData,
      statistics: stats,
      warnings: dataWarnings.filter(warning => 
        warning.includes(String(column)) || warning.includes('missing')
      )
    };
  }, [analysisData, column, title, color, threshold]);

  // Create Plotly data
  const plotlyData = useMemo(() => {
    if (!plotData.values || plotData.values.length === 0) {
      return [];
    }

    const data: any[] = [
      {
        x: plotData.values,
        type: 'histogram',
        nbinsx: bins,
        name: 'Distribution',
        marker: {
          color: plotData.color,
          opacity: 0.7,
          line: {
            color: plotData.color,
            width: 1
          }
        },
        hovertemplate: 
          '<b>Range:</b> %{x}<br>' +
          '<b>Count:</b> %{y}<br>' +
          '<extra></extra>'
      }
    ];

    return data;
  }, [plotData, bins]);

  // Create layout with threshold lines
  const layout = useMemo(() => {
    const baseLayout: any = {
      title: {
        text: '',
        font: { size: 14 }
      },
      xaxis: {
        title: plotData.xLabel || String(column),
        showgrid: true,
        zeroline: true,
        zerolinecolor: CoreColors.muted,
        zerolinewidth: 1
      },
      yaxis: {
        title: plotData.yLabel || 'Frequency',
        showgrid: true
      },
      bargap: 0.05,
      showlegend: false
    };

    // Add threshold lines if enabled
    if (showThresholds && threshold) {
      baseLayout.shapes = [
        // Positive threshold line
        {
          type: 'line',
          x0: threshold,
          x1: threshold,
          y0: 0,
          y1: 1,
          yref: 'paper',
          line: {
            color: CoreColors.threshold,
            width: 2,
            dash: 'dash'
          }
        },
        // Negative threshold line  
        {
          type: 'line',
          x0: -threshold,
          x1: -threshold,
          y0: 0,
          y1: 1,
          yref: 'paper',
          line: {
            color: CoreColors.threshold,
            width: 2,
            dash: 'dash'
          }
        }
      ];

      // Add threshold annotations
      baseLayout.annotations = [
        {
          x: threshold,
          y: 0.95,
          yref: 'paper',
          text: `+${threshold}`,
          showarrow: false,
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: CoreColors.threshold,
          borderwidth: 1,
          font: { size: 10, color: CoreColors.threshold }
        },
        {
          x: -threshold,
          y: 0.95,
          yref: 'paper',
          text: `-${threshold}`,
          showarrow: false,
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: CoreColors.threshold,
          borderwidth: 1,
          font: { size: 10, color: CoreColors.threshold }
        }
      ];
    }

    return baseLayout;
  }, [plotData, column, showThresholds, threshold]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!statistics) return '';

    const { mean, std, count } = statistics;
    const outlierThreshold = threshold || 2.0;
    const outliers = plotData.values.filter(v => Math.abs(v) > outlierThreshold).length;
    const outlierRate = count > 0 ? (outliers / count) * 100 : 0;

    let text = `Distribution shows mean = ${mean.toFixed(2)}, SD = ${std.toFixed(2)} with ${count} measurements.`;
    
    if (showThresholds) {
      text += ` ${outliers} wells (${outlierRate.toFixed(1)}%) exceed ±${outlierThreshold} threshold, indicating potential hits.`;
    }

    // Add normality assessment
    if (Math.abs(mean) > 0.5) {
      text += ' Distribution appears shifted from zero, suggesting systematic bias.';
    }

    return text;
  }, [statistics, plotData.values, threshold, showThresholds]);

  return (
    <ChartContainer
      title={title}
      description={description}
      dataCount={plotData.values.length}
      warnings={warnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`${bins}-bin histogram with robust statistics`}
      interpretation={interpretation}
      references={[
        'Robust Z-scores calculated using median and MAD (1.4826 × MAD)',
        'Threshold lines indicate statistical significance boundaries'
      ]}
    >
      <PlotlyWrapper
        data={plotlyData}
        layout={layout}
        height={height}
        loading={!plotData.values || plotData.values.length === 0}
        error={warnings.length > 0 ? warnings[0] : null}
      />
    </ChartContainer>
  );
};

export default HistogramChart;