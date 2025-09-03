import { AnalysisResult } from '@/types/analysis';

/**
 * Individual well data structure from analysis results
 */
export interface WellData {
  Well: string;
  Z_lptA: number;
  Z_ldtD: number;
  Ratio_lptA: number;
  Ratio_ldtD: number;
  OD_WT?: number;
  OD_tolC?: number;
  OD_SA?: number;
  PassViab: boolean;
  PlateID: string;
  [key: string]: any; // Allow additional fields
}

/**
 * Processed histogram data for Plotly
 */
export interface HistogramData {
  values: number[];
  title: string;
  xLabel: string;
  yLabel: string;
  color: string;
  threshold?: number;
}

/**
 * Processed scatter plot data for Plotly
 */
export interface ScatterData {
  x: number[];
  y: number[];
  labels: string[];
  colors: string[];
  plateIds: string[];
  wells: string[];
  xLabel: string;
  yLabel: string;
}

/**
 * Processed bar chart data for Plotly
 */
export interface BarData {
  categories: string[];
  values: number[];
  labels: string[];
  colors: string[];
  xLabel: string;
  yLabel: string;
}

/**
 * Viability status for bar chart
 */
interface ViabilityCount {
  plateId: string;
  viable: number;
  nonViable: number;
  total: number;
  viabilityRate: number;
}

/**
 * Statistical summary for datasets
 */
export interface StatisticalSummary {
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  count: number;
  q25: number;
  q75: number;
}

/**
 * Data processing utilities for scientific visualizations
 */
export class DataProcessor {
  
  /**
   * Extract well data array from analysis results
   */
  static extractWellData(analysisData: AnalysisResult): WellData[] {
    if (!analysisData?.results || !Array.isArray(analysisData.results)) {
      return [];
    }
    
    return analysisData.results as WellData[];
  }

  /**
   * Process data for histogram visualization
   */
  static processHistogramData(
    wellData: WellData[], 
    column: keyof WellData,
    title: string,
    color: string = '#3B82F6',
    threshold?: number
  ): HistogramData {
    const values = wellData
      .map(well => well[column])
      .filter((value): value is number => 
        typeof value === 'number' && !isNaN(value) && isFinite(value)
      );

    return {
      values,
      title,
      xLabel: this.getColumnLabel(column),
      yLabel: 'Frequency',
      color,
      threshold
    };
  }

  /**
   * Process data for scatter plot visualization
   */
  static processScatterData(
    wellData: WellData[],
    xColumn: keyof WellData,
    yColumn: keyof WellData,
    colorColumn: keyof WellData = 'PlateID'
  ): ScatterData {
    const validData = wellData.filter(well => {
      const x = well[xColumn];
      const y = well[yColumn];
      return typeof x === 'number' && typeof y === 'number' && 
             !isNaN(x) && !isNaN(y) && isFinite(x) && isFinite(y);
    });

    const x = validData.map(well => well[xColumn] as number);
    const y = validData.map(well => well[yColumn] as number);
    const labels = validData.map(well => `${well.Well}: (${well[xColumn]}, ${well[yColumn]})`);
    const plateIds = validData.map(well => well.PlateID || 'Unknown');
    const wells = validData.map(well => well.Well);

    // Generate colors for different plates
    const uniquePlates = [...new Set(plateIds)];
    const colorPalette = this.generateColorPalette(uniquePlates.length);
    const plateColorMap = new Map(uniquePlates.map((plate, i) => [plate, colorPalette[i]]));
    const colors = plateIds.map(plateId => plateColorMap.get(plateId) || '#64748B');

    return {
      x,
      y,
      labels,
      colors,
      plateIds,
      wells,
      xLabel: this.getColumnLabel(xColumn),
      yLabel: this.getColumnLabel(yColumn)
    };
  }

  /**
   * Process viability data for bar chart visualization
   */
  static processViabilityData(wellData: WellData[]): BarData {
    const viabilityCounts = this.calculateViabilityCounts(wellData);
    
    const categories: string[] = [];
    const viableValues: number[] = [];
    const nonViableValues: number[] = [];
    
    viabilityCounts.forEach(count => {
      categories.push(count.plateId);
      viableValues.push(count.viable);
      nonViableValues.push(count.nonViable);
    });

    // Create stacked bar chart data
    const values = viableValues.concat(nonViableValues);
    const labels = categories.map(plate => `${plate} (Viable)`).concat(
      categories.map(plate => `${plate} (Non-Viable)`)
    );
    const colors = Array(categories.length).fill('#10B981').concat(
      Array(categories.length).fill('#EF4444')
    );

    return {
      categories,
      values,
      labels,
      colors,
      xLabel: 'Plate ID',
      yLabel: 'Well Count'
    };
  }

  /**
   * Calculate viability statistics by plate
   */
  static calculateViabilityCounts(wellData: WellData[]): ViabilityCount[] {
    const plateGroups = wellData.reduce((groups, well) => {
      const plateId = well.PlateID || 'Unknown';
      if (!groups[plateId]) {
        groups[plateId] = [];
      }
      groups[plateId].push(well);
      return groups;
    }, {} as Record<string, WellData[]>);

    return Object.entries(plateGroups).map(([plateId, wells]) => {
      const viable = wells.filter(well => well.PassViab === true).length;
      const nonViable = wells.filter(well => well.PassViab === false).length;
      const total = wells.length;
      
      return {
        plateId,
        viable,
        nonViable,
        total,
        viabilityRate: total > 0 ? viable / total : 0
      };
    });
  }

  /**
   * Calculate statistical summary for a dataset
   */
  static calculateStatistics(values: number[]): StatisticalSummary {
    if (values.length === 0) {
      return {
        mean: 0, median: 0, std: 0, min: 0, max: 0, count: 0, q25: 0, q75: 0
      };
    }

    const sorted = [...values].sort((a, b) => a - b);
    const count = values.length;
    
    const mean = values.reduce((sum, val) => sum + val, 0) / count;
    const median = this.calculatePercentile(sorted, 0.5);
    const q25 = this.calculatePercentile(sorted, 0.25);
    const q75 = this.calculatePercentile(sorted, 0.75);
    
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / count;
    const std = Math.sqrt(variance);

    return {
      mean,
      median,
      std,
      min: Math.min(...values),
      max: Math.max(...values),
      count,
      q25,
      q75
    };
  }

  /**
   * Calculate percentile value
   */
  private static calculatePercentile(sortedValues: number[], percentile: number): number {
    const index = (sortedValues.length - 1) * percentile;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index - lower;
    
    if (upper >= sortedValues.length) {
      return sortedValues[sortedValues.length - 1];
    }
    
    return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
  }

  /**
   * Generate color palette for categorical data
   */
  private static generateColorPalette(count: number): string[] {
    const baseColors = [
      '#3B82F6', // blue
      '#8B5CF6', // purple
      '#10B981', // green
      '#F59E0B', // amber
      '#EF4444', // red
      '#06B6D4', // cyan
      '#84CC16', // lime
      '#F97316', // orange
      '#EC4899', // pink
      '#6366F1'  // indigo
    ];

    if (count <= baseColors.length) {
      return baseColors.slice(0, count);
    }

    // Generate additional colors by varying saturation/lightness
    const colors = [...baseColors];
    for (let i = baseColors.length; i < count; i++) {
      const baseIndex = i % baseColors.length;
      const variation = Math.floor(i / baseColors.length);
      const baseColor = baseColors[baseIndex];
      
      // Simple color variation by adjusting opacity
      colors.push(baseColor + (80 - variation * 10).toString(16));
    }

    return colors;
  }

  /**
   * Get display label for data column
   */
  private static getColumnLabel(column: keyof WellData): string {
    const labelMap: Record<string, string> = {
      'Z_lptA': 'Z-Score (lptA)',
      'Z_ldtD': 'Z-Score (ldtD)', 
      'Ratio_lptA': 'Ratio lptA (BG/BT)',
      'Ratio_ldtD': 'Ratio ldtD (BG/BT)',
      'OD_WT': 'OD Wild Type',
      'OD_tolC': 'OD ΔtolC',
      'OD_SA': 'OD S. aureus',
      'PassViab': 'Viability',
      'PlateID': 'Plate ID',
      'Well': 'Well Position'
    };

    return labelMap[column as string] || String(column);
  }

  /**
   * Validate data quality and return warnings
   */
  static validateData(wellData: WellData[]): string[] {
    const warnings: string[] = [];

    if (wellData.length === 0) {
      warnings.push('No data available for visualization');
      return warnings;
    }

    // Check for missing Z-scores
    const missingZlptA = wellData.filter(well => 
      typeof well.Z_lptA !== 'number' || isNaN(well.Z_lptA)
    ).length;
    
    const missingZldtD = wellData.filter(well => 
      typeof well.Z_ldtD !== 'number' || isNaN(well.Z_ldtD)
    ).length;

    if (missingZlptA > 0) {
      warnings.push(`${missingZlptA} wells missing Z_lptA values`);
    }
    
    if (missingZldtD > 0) {
      warnings.push(`${missingZldtD} wells missing Z_ldtD values`);
    }

    // Check for extreme outliers (Z-scores beyond ±10)
    const extremeOutliers = wellData.filter(well => 
      Math.abs(well.Z_lptA) > 10 || Math.abs(well.Z_ldtD) > 10
    ).length;

    if (extremeOutliers > 0) {
      warnings.push(`${extremeOutliers} wells with extreme Z-scores (±10)`);
    }

    // Check viability rate
    const viableWells = wellData.filter(well => well.PassViab === true).length;
    const viabilityRate = viableWells / wellData.length;
    
    if (viabilityRate < 0.7) {
      warnings.push(`Low viability rate: ${(viabilityRate * 100).toFixed(1)}%`);
    }

    return warnings;
  }
}

export default DataProcessor;