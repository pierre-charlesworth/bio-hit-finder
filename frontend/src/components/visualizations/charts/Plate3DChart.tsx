import { useMemo } from 'react';
import PlotlyWrapper from '../shared/PlotlyWrapper';
import ChartContainer from '../shared/ChartContainer';
import { DataProcessor, WellData } from '../shared/DataProcessor';
import { AnalysisResult } from '@/types/analysis';

interface Plate3DChartProps {
  analysisData: AnalysisResult;
  dataColumn: keyof WellData;
  title: string;
  description?: string;
  colorScale?: string;
  showColorbar?: boolean;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  className?: string;
  height?: number;
}

/**
 * 3D plate visualization showing each well as a vertical bar in its grid position
 * Height represents signal intensity (OD, luminescence, Z-score, etc.)
 * Color gradient provides additional visual intensity mapping
 *
 * Ideal for:
 * - High-throughput screening results visualization
 * - QC for edge effects and spatial artifacts
 * - Quick visual comparison of replicate plates
 */
const Plate3DChart = ({
  analysisData,
  dataColumn,
  title,
  description,
  colorScale = 'Viridis',
  showColorbar = true,
  onExport,
  className,
  height = 600
}: Plate3DChartProps) => {

  const { plotData, statistics, warnings } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);

    // Parse well positions and extract values
    const plateData: { row: number; col: number; value: number; wellId: string }[] = [];
    const values: number[] = [];

    wellData.forEach((well) => {
      const wellId = well.Well;
      const value = well[dataColumn];

      if (wellId && typeof value === 'number' && !isNaN(value)) {
        // Parse well ID (e.g., "A01" -> row=0, col=0)
        const rowLetter = wellId.charAt(0);
        const colNumber = parseInt(wellId.substring(1), 10);

        const row = rowLetter.charCodeAt(0) - 'A'.charCodeAt(0);
        const col = colNumber - 1;

        // Standard 96-well plate: 8 rows (A-H) × 12 columns (1-12)
        if (row >= 0 && row < 8 && col >= 0 && col < 12) {
          plateData.push({ row, col, value, wellId });
          values.push(value);
        }
      }
    });

    if (plateData.length === 0) {
      return {
        plotData: null,
        statistics: null,
        warnings: ['No valid well data found for 3D visualization']
      };
    }

    // Create meshgrid for 3D bar positions
    const x: number[] = [];
    const y: number[] = [];
    const z: number[] = [];
    const colors: number[] = [];
    const text: string[] = [];

    // Generate bars for each well
    plateData.forEach(({ row, col, value, wellId }) => {
      // Create a bar at this position
      // Each bar is defined by 8 vertices (a rectangular prism)
      const barWidth = 0.8;
      const barDepth = 0.8;

      // Base vertices (z=0)
      const x0 = col - barWidth / 2;
      const x1 = col + barWidth / 2;
      const y0 = row - barDepth / 2;
      const y1 = row + barDepth / 2;

      // We'll use surface3d to create bars
      // Store position and value for the bar top
      x.push(col);
      y.push(row);
      z.push(value);
      colors.push(value);
      text.push(`${wellId}<br>Value: ${value.toFixed(3)}`);
    });

    const stats = DataProcessor.calculateStatistics(values);
    const dataWarnings = DataProcessor.validateData(wellData);

    return {
      plotData: { x, y, z, colors, text, plateData },
      statistics: stats,
      warnings: dataWarnings.filter(w => w.severity === 'warning' || w.severity === 'error')
    };
  }, [analysisData, dataColumn]);

  if (!plotData) {
    return (
      <ChartContainer
        title={title}
        description={description}
        statistics={statistics}
        warnings={warnings}
        onExport={onExport}
        className={className}
      >
        <div className="flex items-center justify-center h-96 text-muted-foreground">
          No valid data for 3D plate visualization
        </div>
      </ChartContainer>
    );
  }

  // Helper function to create vertices and faces for a 3D bar
  const createBar = (x: number, y: number, z: number, width: number) => {
    const w = width / 2;
    const x0 = x - w, x1 = x + w;
    const y0 = y - w, y1 = y + w;

    return {
      x: [x0, x1, x1, x0, x0, x1, x1, x0],
      y: [y0, y0, y1, y1, y0, y0, y1, y1],
      z: [0, 0, 0, 0, z, z, z, z],
      i: [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
      j: [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
      k: [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    };
  };

  // Create individual bars grouped by similar values for better color mapping
  const barWidth = 0.35;
  const minValue = Math.min(...plotData.colors);
  const maxValue = Math.max(...plotData.colors);

  // Normalize colors to 0-1 range for colorscale
  const normalizeValue = (val: number) => {
    if (maxValue === minValue) return 0.5;
    return (val - minValue) / (maxValue - minValue);
  };

  // Create all bars as a single mesh3d trace
  const allX: number[] = [];
  const allY: number[] = [];
  const allZ: number[] = [];
  const allI: number[] = [];
  const allJ: number[] = [];
  const allK: number[] = [];
  const allColors: number[] = [];
  const allText: string[] = [];

  plotData.plateData.forEach((d, idx) => {
    const bar = createBar(d.col, d.row, d.value, barWidth);
    const offset = idx * 8; // 8 vertices per bar

    allX.push(...bar.x);
    allY.push(...bar.y);
    allZ.push(...bar.z);
    allI.push(...bar.i.map(i => i + offset));
    allJ.push(...bar.j.map(j => j + offset));
    allK.push(...bar.k.map(k => k + offset));

    // Assign color to all 8 vertices of this bar
    const normalizedValue = normalizeValue(d.value);
    for (let i = 0; i < 8; i++) {
      allColors.push(normalizedValue);
    }
  });

  const barsTrace = {
    type: 'mesh3d' as const,
    x: allX,
    y: allY,
    z: allZ,
    i: allI,
    j: allJ,
    k: allK,
    intensity: allColors,
    colorscale: colorScale,
    showscale: false,
    hoverinfo: 'skip' as const,
    flatshading: false,
    lighting: {
      ambient: 0.8,
      diffuse: 0.8,
      specular: 0.3,
      roughness: 0.5,
      fresnel: 0.2
    }
  };

  // Colorbar trace
  const colorbarTrace = {
    type: 'scatter3d' as const,
    mode: 'markers' as const,
    x: [-100, -100],
    y: [-100, -100],
    z: [minValue, maxValue],
    marker: {
      size: 0.01,
      color: [minValue, maxValue],
      colorscale: colorScale,
      showscale: showColorbar,
      cmin: minValue,
      cmax: maxValue,
      colorbar: {
        title: {
          text: dataColumn as string,
          side: 'right'
        },
        thickness: 15,
        len: 0.6,
        x: 1.0,
        xpad: 10
      }
    },
    hoverinfo: 'skip' as const,
    showlegend: false
  };

  const layout = {
    scene: {
      xaxis: {
        title: 'Column',
        tickmode: 'linear' as const,
        tick0: 0,
        dtick: 1,
        range: [-0.5, 11.5]
      },
      yaxis: {
        title: 'Row',
        tickmode: 'array' as const,
        tickvals: [0, 1, 2, 3, 4, 5, 6, 7],
        ticktext: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
        range: [-0.5, 7.5]
      },
      zaxis: {
        title: dataColumn as string
      },
      camera: {
        eye: { x: 1.5, y: 1.5, z: 1.3 },
        center: { x: 0, y: 0, z: -0.1 }
      },
      aspectmode: 'manual' as const,
      aspectratio: { x: 1.5, y: 1, z: 0.8 }
    },
    margin: { l: 0, r: 100, t: 0, b: 0 },
    hovermode: 'closest' as const,
    showlegend: false,
    autosize: true,
    height: height
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['toImage'] as any[],
    responsive: true
  };

  return (
    <ChartContainer
      title={title}
      description={description}
      warnings={warnings}
      onExport={onExport}
      className={className}
      height={height}
    >
      <PlotlyWrapper
        data={[barsTrace, colorbarTrace]}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
      />
    </ChartContainer>
  );
};

export default Plate3DChart;