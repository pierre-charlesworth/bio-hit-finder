import { useMemo } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { CoreColors } from '../shared/ColorSchemes';
import { AnalysisResult } from '@/types/analysis';

interface BarChartProps {
  analysisData: AnalysisResult;
  title: string;
  description?: string;
  showPercentages?: boolean;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * Stacked bar chart for viability data by plate
 * Shows viable vs non-viable well counts
 */
const BarChart = ({
  analysisData,
  title,
  description,
  showPercentages = false,
  onExport,
  className,
  height = 400
}: BarChartProps) => {
  
  // Process viability data
  const { viabilityData, overallStats, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    const viabilityCounts = DataProcessor.calculateViabilityCounts(wellData);
    const dataWarnings = DataProcessor.validateData(wellData);
    
    // Calculate overall statistics
    const totalWells = wellData.length;
    const totalViable = viabilityCounts.reduce((sum, plate) => sum + plate.viable, 0);
    const overallViabilityRate = totalWells > 0 ? totalViable / totalWells : 0;
    
    // Identify problematic plates (< 70% viability)
    const problematicPlates = viabilityCounts.filter(plate => plate.viabilityRate < 0.7);
    
    return {
      viabilityData: viabilityCounts,
      overallStats: {
        totalWells,
        totalViable,
        totalNonViable: totalWells - totalViable,
        overallViabilityRate,
        problematicPlates: problematicPlates.length
      },
      warnings: dataWarnings.filter(warning => 
        warning.includes('viability') || warning.includes('Low viability')
      )
    };
  }, [analysisData]);

  // Create Plotly data for stacked bar chart
  const plotlyData = useMemo(() => {
    if (!viabilityData || viabilityData.length === 0) {
      return [];
    }

    const plateIds = viabilityData.map(plate => plate.plateId);
    const viableCounts = viabilityData.map(plate => plate.viable);
    const nonViableCounts = viabilityData.map(plate => plate.nonViable);
    
    // Create stacked bar data
    const traces: any[] = [
      {
        x: plateIds,
        y: viableCounts,
        type: 'bar',
        name: 'Viable',
        marker: {
          color: CoreColors.success,
          opacity: 0.8
        },
        text: showPercentages 
          ? viabilityData.map(plate => `${(plate.viabilityRate * 100).toFixed(1)}%`)
          : viableCounts.map(count => count.toString()),
        textposition: 'inside',
        textfont: { color: 'white', size: 10 },
        hovertemplate: 
          '<b>Plate:</b> %{x}<br>' +
          '<b>Viable Wells:</b> %{y}<br>' +
          '<b>Percentage:</b> %{customdata:.1f}%<br>' +
          '<extra></extra>',
        customdata: viabilityData.map(plate => plate.viabilityRate * 100)
      },
      {
        x: plateIds,
        y: nonViableCounts,
        type: 'bar',
        name: 'Non-Viable',
        marker: {
          color: CoreColors.error,
          opacity: 0.8
        },
        text: showPercentages
          ? viabilityData.map(plate => `${((1 - plate.viabilityRate) * 100).toFixed(1)}%`)
          : nonViableCounts.map(count => count.toString()),
        textposition: 'inside',
        textfont: { color: 'white', size: 10 },
        hovertemplate: 
          '<b>Plate:</b> %{x}<br>' +
          '<b>Non-Viable Wells:</b> %{y}<br>' +
          '<b>Percentage:</b> %{customdata:.1f}%<br>' +
          '<extra></extra>',
        customdata: viabilityData.map(plate => (1 - plate.viabilityRate) * 100)
      }
    ];

    return traces;
  }, [viabilityData, showPercentages]);

  // Create layout
  const layout = useMemo(() => {
    const baseLayout: any = {
      title: {
        text: '',
        font: { size: 14 }
      },
      xaxis: {
        title: 'Plate ID',
        showgrid: false,
        tickangle: viabilityData.length > 6 ? -45 : 0
      },
      yaxis: {
        title: showPercentages ? 'Percentage (%)' : 'Well Count',
        showgrid: true,
        ...(showPercentages && {
          range: [0, 100],
          ticksuffix: '%'
        })
      },
      barmode: 'stack',
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

    // Add warning line for low viability (70% threshold)
    if (showPercentages) {
      baseLayout.shapes = [
        {
          type: 'line',
          x0: -0.5,
          x1: viabilityData.length - 0.5,
          y0: 70,
          y1: 70,
          line: {
            color: CoreColors.warning,
            width: 2,
            dash: 'dash'
          }
        }
      ];

      baseLayout.annotations = [
        {
          x: viabilityData.length - 1,
          y: 70,
          text: '70% threshold',
          showarrow: false,
          bgcolor: 'rgba(255,255,255,0.8)',
          bordercolor: CoreColors.warning,
          borderwidth: 1,
          font: { size: 10, color: CoreColors.warning },
          xanchor: 'right'
        }
      ];
    }

    return baseLayout;
  }, [viabilityData, showPercentages]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    if (!overallStats) return '';

    const { overallViabilityRate, problematicPlates, totalWells } = overallStats;
    
    let text = `Overall viability rate: ${(overallViabilityRate * 100).toFixed(1)}% across ${totalWells} wells.`;
    
    if (overallViabilityRate >= 0.8) {
      text += ' Excellent viability indicates high data quality.';
    } else if (overallViabilityRate >= 0.7) {
      text += ' Good viability within acceptable range.';
    } else {
      text += ' Low viability may indicate assay problems or cytotoxic conditions.';
    }

    if (problematicPlates > 0) {
      text += ` ${problematicPlates} plate(s) show concerning viability rates (<70%), suggesting potential technical issues or batch effects.`;
    }

    // Add biological context
    text += ' ATP-based viability gating ensures analysis includes only metabolically active cells, improving hit quality.';

    return text;
  }, [overallStats]);

  // Generate quality warnings
  const qualityWarnings = useMemo(() => {
    const qualityWarns = [...warnings];
    
    if (overallStats.overallViabilityRate < 0.7) {
      qualityWarns.push(`Overall viability rate (${(overallStats.overallViabilityRate * 100).toFixed(1)}%) is below 70%`);
    }
    
    if (overallStats.problematicPlates > 0) {
      qualityWarns.push(`${overallStats.problematicPlates} plates have viability rates below 70%`);
    }

    return qualityWarns;
  }, [warnings, overallStats]);

  return (
    <ChartContainer
      title={title}
      description={description}
      dataCount={overallStats.totalWells}
      warnings={qualityWarnings}
      onExport={onExport}
      expandable={true}
      height={height}
      className={className}
      methodology={`ATP-based viability assessment with 30% threshold gating`}
      interpretation={interpretation}
      references={[
        'ATP levels measured via BacTiter-Glo® luminescent viability assay',
        'Viability threshold (f=0.3) filters out cytotoxic artifacts',
        '70% viability rate considered minimum for reliable analysis'
      ]}
    >
      <PlotlyWrapper
        data={plotlyData}
        layout={layout}
        height={height}
        loading={!viabilityData || viabilityData.length === 0}
        error={qualityWarnings.length > 0 ? qualityWarnings[0] : null}
      />
    </ChartContainer>
  );
};

export default BarChart;