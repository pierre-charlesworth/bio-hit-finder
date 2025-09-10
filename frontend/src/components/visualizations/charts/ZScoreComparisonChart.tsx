import { useMemo } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { CoreColors } from '../shared/ColorSchemes';
import { AnalysisResult } from '@/types/analysis';

interface ZScoreComparisonChartProps {
  analysisData: AnalysisResult;
  rawColumn: 'Z_lptA' | 'Z_ldtD';
  bscoreColumn: 'B_lptA' | 'B_ldtD';
  title?: string;
  description?: string;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Side-by-side comparison of Raw Z-scores vs B-scores
 * Shows distribution histograms with statistical summaries
 */
const ZScoreComparisonChart = ({
  analysisData,
  rawColumn,
  bscoreColumn,
  title,
  description,
  onExport,
  className,
  height = 400
}: ZScoreComparisonChartProps) => {
  
  // Process data for comparison
  const { chartData, stats, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    
    // Extract and clean data
    const rawData = wellData
      .map(well => well[rawColumn])
      .filter(val => val !== null && val !== undefined && !isNaN(val));
    
    const bscoreData = wellData
      .map(well => well[bscoreColumn])
      .filter(val => val !== null && val !== undefined && !isNaN(val));
    
    if (rawData.length === 0 || bscoreData.length === 0) {
      return {
        chartData: null,
        stats: null,
        warnings: ['Insufficient data for comparison']
      };
    }
    
    // Calculate common data range for consistent binning
    const allData = [...rawData, ...bscoreData];
    const minVal = Math.min(...allData);
    const maxVal = Math.max(...allData);
    const range = maxVal - minVal;
    
    // Use quantiles for better range if data has outliers
    allData.sort((a, b) => a - b);
    const q001 = allData[Math.floor(allData.length * 0.001)];
    const q999 = allData[Math.floor(allData.length * 0.999)];
    
    const dataRange = [
      isNaN(q001) ? minVal : q001,
      isNaN(q999) ? maxVal : q999
    ];
    
    // Calculate statistics
    const rawStats = {
      mean: rawData.reduce((sum, val) => sum + val, 0) / rawData.length,
      std: Math.sqrt(rawData.reduce((sum, val) => {
        const diff = val - (rawData.reduce((s, v) => s + v, 0) / rawData.length);
        return sum + diff * diff;
      }, 0) / rawData.length),
      count: rawData.length
    };
    
    const bscoreStats = {
      mean: bscoreData.reduce((sum, val) => sum + val, 0) / bscoreData.length,
      std: Math.sqrt(bscoreData.reduce((sum, val) => {
        const diff = val - (bscoreData.reduce((s, v) => s + v, 0) / bscoreData.length);
        return sum + diff * diff;
      }, 0) / bscoreData.length),
      count: bscoreData.length
    };
    
    const dataWarnings = DataProcessor.validateData(wellData);
    
    return {
      chartData: {
        rawData,
        bscoreData,
        dataRange,
        rawStats,
        bscoreStats
      },
      stats: { rawStats, bscoreStats },
      warnings: dataWarnings
    };
  }, [analysisData, rawColumn, bscoreColumn]);

  // Create Plotly data and layout for side-by-side histograms
  const plotlyData = useMemo(() => {
    if (!chartData) return [];
    
    const { rawData, bscoreData, dataRange } = chartData;
    const binSize = (dataRange[1] - dataRange[0]) / 40;
    
    return [
      {
        x: rawData,
        type: 'histogram',
        name: 'Raw Z-scores',
        xbins: {
          start: dataRange[0],
          end: dataRange[1],
          size: binSize
        },
        marker: {
          color: CoreColors.primary,
          opacity: 0.7
        },
        yaxis: 'y',
        xaxis: 'x',
        showlegend: false,
        hovertemplate: 
          '<b>Raw Z-score</b><br>' +
          'Value: %{x:.3f}<br>' +
          'Count: %{y}<br>' +
          '<extra></extra>'
      },
      {
        x: bscoreData,
        type: 'histogram',
        name: 'B-scores',
        xbins: {
          start: dataRange[0],
          end: dataRange[1],
          size: binSize
        },
        marker: {
          color: CoreColors.secondary,
          opacity: 0.7
        },
        yaxis: 'y2',
        xaxis: 'x2',
        showlegend: false,
        hovertemplate: 
          '<b>B-score</b><br>' +
          'Value: %{x:.3f}<br>' +
          'Count: %{y}<br>' +
          '<extra></extra>'
      }
    ];
  }, [chartData]);

  // Create layout with subplots
  const layout = useMemo(() => {
    if (!chartData) return {};
    
    const { rawStats, bscoreStats } = chartData;
    
    return {
      title: {
        text: '',
        font: { size: 14 }
      },
      // Left subplot (Raw Z-scores)
      xaxis: {
        domain: [0, 0.48],
        title: 'Raw Z-score',
        showgrid: true,
        gridcolor: '#E5E7EB'
      },
      yaxis: {
        title: 'Frequency',
        showgrid: true,
        gridcolor: '#E5E7EB'
      },
      // Right subplot (B-scores)  
      xaxis2: {
        domain: [0.52, 1],
        title: 'B-score',
        showgrid: true,
        gridcolor: '#E5E7EB'
      },
      yaxis2: {
        anchor: 'x2',
        showgrid: true,
        gridcolor: '#E5E7EB'
      },
      // Reference lines at 0
      shapes: [
        {
          type: 'line',
          x0: 0, x1: 0,
          y0: 0, y1: 1,
          xref: 'x', yref: 'paper',
          line: {
            color: 'gray',
            width: 1,
            dash: 'dash'
          },
          opacity: 0.7
        },
        {
          type: 'line',
          x0: 0, x1: 0,
          y0: 0, y1: 1,
          xref: 'x2', yref: 'paper',
          line: {
            color: 'gray',
            width: 1,
            dash: 'dash'
          },
          opacity: 0.7
        }
      ],
      // Statistical annotations
      annotations: [
        {
          x: 0.24, y: 1.02,
          xref: 'paper', yref: 'paper',
          text: `Raw Z: μ=${rawStats.mean.toFixed(2)}, σ=${rawStats.std.toFixed(2)}`,
          showarrow: false,
          font: { size: 10 },
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: '#E5E7EB',
          borderwidth: 1
        },
        {
          x: 0.74, y: 1.02,
          xref: 'paper', yref: 'paper',
          text: `B-score: μ=${bscoreStats.mean.toFixed(2)}, σ=${bscoreStats.std.toFixed(2)}`,
          showarrow: false,
          font: { size: 10 },
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: '#E5E7EB',
          borderwidth: 1
        },
        // Subplot titles
        {
          x: 0.24, y: 0.95,
          xref: 'paper', yref: 'paper',
          text: `<b>Raw Z-scores (${rawColumn})</b>`,
          showarrow: false,
          font: { size: 12 }
        },
        {
          x: 0.76, y: 0.95,
          xref: 'paper', yref: 'paper',
          text: `<b>B-scores (${bscoreColumn})</b>`,
          showarrow: false,
          font: { size: 12 }
        }
      ]
    };
  }, [chartData, rawColumn, bscoreColumn]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!stats) return '';
    
    const { rawStats, bscoreStats } = stats;
    const rawNormality = Math.abs(rawStats.mean) < 0.1 && Math.abs(rawStats.std - 1) < 0.2;
    const bscoreNormality = Math.abs(bscoreStats.mean) < 0.1 && Math.abs(bscoreStats.std - 1) < 0.2;
    
    let text = `Comparing raw Z-scores (μ=${rawStats.mean.toFixed(2)}, σ=${rawStats.std.toFixed(2)}) `;
    text += `with B-scores (μ=${bscoreStats.mean.toFixed(2)}, σ=${bscoreStats.std.toFixed(2)}). `;
    
    if (rawNormality && bscoreNormality) {
      text += 'Both distributions are well-normalized (μ≈0, σ≈1), indicating robust statistical processing.';
    } else if (bscoreNormality && !rawNormality) {
      text += 'B-scoring has improved normalization compared to raw Z-scores, reducing systematic biases.';
    } else if (!bscoreNormality && rawNormality) {
      text += 'Raw Z-scores show good normalization. B-scoring may have introduced artifacts or the data may lack systematic biases to correct.';
    } else {
      text += 'Neither distribution is well-normalized, suggesting potential data quality issues or extreme outliers.';
    }
    
    // Add biological context
    text += ' B-scoring applies median polish to remove row/column effects common in plate-based assays.';
    
    return text;
  }, [stats]);

  // Generate default title if not provided
  const chartTitle = title || `${rawColumn} vs ${bscoreColumn} Distribution Comparison`;

  return (
    <ChartContainer
      title={chartTitle}
      description={description || 'Side-by-side comparison of raw Z-scores and B-scores showing the effect of bias correction'}
      dataCount={chartData ? Math.min(chartData.rawStats.count, chartData.bscoreStats.count) : 0}
      warnings={warnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`Robust Z-scores (raw) vs B-scores (median polish bias correction)`}
      interpretation={interpretation}
      references={[
        'Robust Z-scores: Z = (x - median) / (1.4826 × MAD)',
        'B-scores: Median polish followed by robust scaling',
        'Both methods use MAD for robust variance estimation'
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

export default ZScoreComparisonChart;