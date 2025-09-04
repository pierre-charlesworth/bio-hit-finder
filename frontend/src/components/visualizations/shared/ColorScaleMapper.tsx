/**
 * ColorScaleMapper.tsx
 * 
 * Scientific color scale implementation for biological data visualization
 * Handles Z-scores, ratios, and other continuous data types
 */

export interface ColorScale {
  name: string;
  type: 'diverging' | 'sequential' | 'categorical';
  colors: string[];
  domain: [number, number];
  center?: number;
  description: string;
}

export interface ColorMapping {
  color: string;
  rgb: [number, number, number];
  value: number;
  intensity: number;
}

// Scientific color scales for different data types
export const COLOR_SCALES: Record<string, ColorScale> = {
  // Z-score diverging scale (blue-white-red)
  zScore: {
    name: 'Z-Score',
    type: 'diverging',
    colors: [
      '#053061', '#2166AC', '#4393C3', '#92C5DE', '#D1E5F0',
      '#F7F7F7',
      '#FDDBC7', '#F4A582', '#D6604D', '#B2182B', '#67001F'
    ],
    domain: [-4, 4],
    center: 0,
    description: 'Blue (negative) to white (zero) to red (positive) Z-scores'
  },

  // Ratio sequential scale (white to blue)
  ratio: {
    name: 'Ratio',
    type: 'sequential',
    colors: [
      '#F7FBFF', '#DEEBF7', '#C6DBEF', '#9ECAE1', '#6BAED6',
      '#4292C6', '#2171B5', '#08519C', '#08306B'
    ],
    domain: [0, 2],
    description: 'White (low) to dark blue (high) ratios'
  },

  // Viability sequential scale (white to green)
  viability: {
    name: 'Viability',
    type: 'sequential',
    colors: [
      '#F7FCF5', '#E5F5E0', '#C7E9C0', '#A1D99B', '#74C476',
      '#41AB5D', '#238B45', '#006D2C', '#00441B'
    ],
    domain: [0, 1],
    description: 'White (dead) to dark green (viable) cells'
  },

  // B-score diverging scale (purple-white-orange)
  bScore: {
    name: 'B-Score',
    type: 'diverging',
    colors: [
      '#40004B', '#762A83', '#9970AB', '#C2A5CF', '#E7D4E8',
      '#F7F7F7',
      '#FDE0EF', '#F1B6DA', '#DE77AE', '#C51B7D', '#8E0152'
    ],
    domain: [-3, 3],
    center: 0,
    description: 'Purple (negative) to white (zero) to pink (positive) B-scores'
  },

  // Edge effect warning scale (white to red)
  edgeEffect: {
    name: 'Edge Effect',
    type: 'sequential',
    colors: [
      '#FFFFFF', '#FFF5F0', '#FEE0D2', '#FCBBA1', '#FC9272',
      '#FB6A4A', '#EF3B2C', '#CB181D', '#A50F15', '#67000D'
    ],
    domain: [0, 1],
    description: 'White (no effect) to red (strong edge effect)'
  },

  // Quality control scale (red-yellow-green)
  qualityControl: {
    name: 'Quality Control',
    type: 'diverging',
    colors: [
      '#D73027', '#F46D43', '#FDAE61', '#FEE08B', '#FFFFBF',
      '#E6F598', '#ABDDA4', '#66C2A5', '#3288BD', '#5E4FA2'
    ],
    domain: [0, 1],
    center: 0.5,
    description: 'Red (poor) to yellow (acceptable) to green (excellent) quality'
  }
};

/**
 * Maps a data value to a color using the specified scale
 */
export function mapValueToColor(
  value: number,
  scale: ColorScale,
  options: {
    handleOutliers?: boolean;
    outlierColor?: string;
    missingColor?: string;
  } = {}
): ColorMapping {
  const {
    handleOutliers = true,
    outlierColor = '#808080', // Gray for outliers
    missingColor = '#FFFFFF'  // White for missing
  } = options;

  // Handle missing/invalid values
  if (!isFinite(value)) {
    return {
      color: missingColor,
      rgb: hexToRgb(missingColor),
      value: NaN,
      intensity: 0
    };
  }

  const [minValue, maxValue] = scale.domain;
  let normalizedValue: number;

  // Handle outliers
  if (handleOutliers && (value < minValue || value > maxValue)) {
    return {
      color: outlierColor,
      rgb: hexToRgb(outlierColor),
      value,
      intensity: value > maxValue ? 1 : 0
    };
  }

  // Clamp value to domain
  const clampedValue = Math.max(minValue, Math.min(maxValue, value));

  // Calculate normalized position (0-1)
  if (scale.type === 'diverging' && scale.center !== undefined) {
    // Diverging scale with center point
    const center = scale.center;
    if (clampedValue <= center) {
      // Map to first half of colors
      normalizedValue = 0.5 * (clampedValue - minValue) / (center - minValue);
    } else {
      // Map to second half of colors
      normalizedValue = 0.5 + 0.5 * (clampedValue - center) / (maxValue - center);
    }
  } else {
    // Sequential or linear diverging scale
    normalizedValue = (clampedValue - minValue) / (maxValue - minValue);
  }

  // Get color from scale
  const color = interpolateColorScale(normalizedValue, scale.colors);
  
  return {
    color,
    rgb: hexToRgb(color),
    value: clampedValue,
    intensity: normalizedValue
  };
}

/**
 * Interpolates between colors in a color scale
 */
function interpolateColorScale(position: number, colors: string[]): string {
  // Clamp position to [0, 1]
  position = Math.max(0, Math.min(1, position));

  if (colors.length === 1) {
    return colors[0];
  }

  // Calculate segment
  const segments = colors.length - 1;
  const scaledPosition = position * segments;
  const segmentIndex = Math.floor(scaledPosition);
  const segmentPosition = scaledPosition - segmentIndex;

  // Handle edge cases
  if (segmentIndex >= segments) {
    return colors[colors.length - 1];
  }
  if (segmentIndex < 0) {
    return colors[0];
  }

  // Interpolate between adjacent colors
  const color1 = colors[segmentIndex];
  const color2 = colors[segmentIndex + 1];

  return interpolateColors(color1, color2, segmentPosition);
}

/**
 * Interpolates between two hex colors
 */
function interpolateColors(color1: string, color2: string, factor: number): string {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);

  const r = Math.round(rgb1[0] + (rgb2[0] - rgb1[0]) * factor);
  const g = Math.round(rgb1[1] + (rgb2[1] - rgb1[1]) * factor);
  const b = Math.round(rgb1[2] + (rgb2[2] - rgb1[2]) * factor);

  return rgbToHex(r, g, b);
}

/**
 * Converts hex color to RGB array
 */
function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16)
  ] : [0, 0, 0];
}

/**
 * Converts RGB values to hex color
 */
function rgbToHex(r: number, g: number, b: number): string {
  return "#" + [r, g, b].map(x => {
    const hex = Math.max(0, Math.min(255, x)).toString(16);
    return hex.length === 1 ? "0" + hex : hex;
  }).join("");
}

/**
 * Generates color scale for legend display
 */
export function generateColorScaleLegend(
  scale: ColorScale,
  steps: number = 100
): Array<{ value: number; color: string; label?: string }> {
  const legend: Array<{ value: number; color: string; label?: string }> = [];
  const [minValue, maxValue] = scale.domain;

  for (let i = 0; i <= steps; i++) {
    const position = i / steps;
    const value = minValue + (maxValue - minValue) * position;
    const colorMapping = mapValueToColor(value, scale);

    // Add labels at key points
    let label: string | undefined;
    if (i === 0) {
      label = formatScaleValue(minValue);
    } else if (i === steps) {
      label = formatScaleValue(maxValue);
    } else if (scale.center !== undefined && Math.abs(value - scale.center) < 0.01) {
      label = formatScaleValue(scale.center);
    } else if (i % (steps / 4) === 0) {
      label = formatScaleValue(value);
    }

    legend.push({
      value,
      color: colorMapping.color,
      label
    });
  }

  return legend;
}

/**
 * Formats values for display in legends
 */
function formatScaleValue(value: number): string {
  if (Math.abs(value) >= 100) {
    return value.toFixed(0);
  } else if (Math.abs(value) >= 10) {
    return value.toFixed(1);
  } else {
    return value.toFixed(2);
  }
}

/**
 * Calculates optimal color scale domain from data
 */
export function calculateOptimalDomain(
  values: number[],
  scaleType: 'diverging' | 'sequential',
  options: {
    percentile?: number;
    symmetric?: boolean;
    center?: number;
  } = {}
): [number, number] {
  const { percentile = 0.02, symmetric = true, center = 0 } = options;

  // Filter finite values
  const finiteValues = values.filter(v => isFinite(v));
  
  if (finiteValues.length === 0) {
    return [-1, 1];
  }

  // Sort values
  finiteValues.sort((a, b) => a - b);

  // Calculate percentiles
  const lowerIndex = Math.floor(finiteValues.length * percentile);
  const upperIndex = Math.ceil(finiteValues.length * (1 - percentile)) - 1;

  let minValue = finiteValues[lowerIndex];
  let maxValue = finiteValues[upperIndex];

  if (scaleType === 'diverging' && symmetric) {
    // Make domain symmetric around center
    const maxAbs = Math.max(Math.abs(minValue - center), Math.abs(maxValue - center));
    minValue = center - maxAbs;
    maxValue = center + maxAbs;
  }

  return [minValue, maxValue];
}

/**
 * Gets appropriate color scale for data type
 */
export function getColorScaleForDataType(dataType: string): ColorScale {
  const lowerDataType = dataType.toLowerCase();
  
  if (lowerDataType.includes('z_score') || lowerDataType.includes('zscore')) {
    return COLOR_SCALES.zScore;
  } else if (lowerDataType.includes('b_score') || lowerDataType.includes('bscore')) {
    return COLOR_SCALES.bScore;
  } else if (lowerDataType.includes('ratio')) {
    return COLOR_SCALES.ratio;
  } else if (lowerDataType.includes('viab')) {
    return COLOR_SCALES.viability;
  } else if (lowerDataType.includes('edge')) {
    return COLOR_SCALES.edgeEffect;
  } else if (lowerDataType.includes('qc') || lowerDataType.includes('quality')) {
    return COLOR_SCALES.qualityControl;
  }

  // Default to Z-score scale
  return COLOR_SCALES.zScore;
}

/**
 * Validates color scale configuration
 */
export function validateColorScale(scale: ColorScale): string[] {
  const warnings: string[] = [];

  if (scale.colors.length < 2) {
    warnings.push('Color scale must have at least 2 colors');
  }

  if (scale.domain[0] >= scale.domain[1]) {
    warnings.push('Color scale domain must have min < max');
  }

  if (scale.type === 'diverging' && scale.center === undefined) {
    warnings.push('Diverging color scale should specify a center value');
  }

  // Validate hex colors
  for (const color of scale.colors) {
    if (!/^#[0-9A-F]{6}$/i.test(color)) {
      warnings.push(`Invalid hex color: ${color}`);
    }
  }

  return warnings;
}

/**
 * Creates custom color scale
 */
export function createCustomColorScale(
  name: string,
  colors: string[],
  domain: [number, number],
  type: 'diverging' | 'sequential' = 'sequential',
  center?: number
): ColorScale {
  return {
    name,
    type,
    colors,
    domain,
    center,
    description: `Custom ${type} scale: ${name}`
  };
}