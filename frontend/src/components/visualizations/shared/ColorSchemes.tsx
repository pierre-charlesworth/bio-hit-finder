/**
 * Scientific color schemes and palettes for biological data visualization
 * Designed for accessibility, publication standards, and scientific convention
 */

/**
 * Core color palette matching the dashboard design system
 */
export const CoreColors = {
  // Primary analysis colors (matching overview metrics)
  totalWells: '#64748B',    // gray-500
  reporterHits: '#3B82F6',  // blue-500  
  vitalityHits: '#8B5CF6',  // purple-500
  platformHits: '#10B981',  // emerald-500
  
  // Status colors
  success: '#10B981',       // emerald-500
  warning: '#F59E0B',       // amber-500
  error: '#EF4444',         // red-500
  info: '#3B82F6',          // blue-500
  
  // Threshold and reference colors
  threshold: '#EF4444',     // red-500 for Z-score thresholds
  reference: '#6B7280',     // gray-500 for reference lines
  
  // Background and text
  background: '#FFFFFF',    // white
  foreground: '#374151',    // gray-700
  muted: '#9CA3AF',         // gray-400
  mutedForeground: '#6B7280' // gray-500
} as const;

/**
 * Scientific color scales for different data types
 */
export const ScientificColorScales = {
  
  /**
   * Z-score color scale (diverging blue-white-red)
   * Standard in scientific literature for statistical significance
   */
  zScore: {
    name: 'Z-Score Diverging',
    colors: ['#1E40AF', '#3B82F6', '#93C5FD', '#FFFFFF', '#FCA5A5', '#EF4444', '#B91C1C'],
    scale: [-4, -2, -1, 0, 1, 2, 4],
    description: 'Blue (negative) to white (zero) to red (positive)',
    reversed: false
  },

  /**
   * B-score color scale (similar to Z-score but slightly different hues)
   */
  bScore: {
    name: 'B-Score Diverging',
    colors: ['#1E3A8A', '#2563EB', '#60A5FA', '#F8FAFC', '#F87171', '#DC2626', '#991B1B'],
    scale: [-4, -2, -1, 0, 1, 2, 4],
    description: 'Dark blue (negative) to light gray (zero) to dark red (positive)',
    reversed: false
  },

  /**
   * Ratio/fold-change color scale (sequential)
   */
  ratio: {
    name: 'Ratio Sequential',
    colors: ['#FEF3C7', '#FCD34D', '#F59E0B', '#D97706', '#92400E'],
    scale: [0, 0.5, 1, 2, 4],
    description: 'Light yellow (low) to dark amber (high)',
    reversed: false
  },

  /**
   * Viability color scale (green for viable, red for non-viable)
   */
  viability: {
    name: 'Viability Binary',
    colors: ['#EF4444', '#10B981'], // red, green
    scale: [0, 1],
    description: 'Red (non-viable) to green (viable)',
    reversed: false
  },

  /**
   * OD/growth color scale (blue sequential)
   */
  opticalDensity: {
    name: 'Optical Density',
    colors: ['#EFF6FF', '#DBEAFE', '#93C5FD', '#3B82F6', '#1D4ED8', '#1E40AF'],
    scale: [0, 0.2, 0.5, 1.0, 1.5, 2.0],
    description: 'Light blue (low OD) to dark blue (high OD)',
    reversed: false
  },

  /**
   * Quality score color scale (red-yellow-green)
   */
  quality: {
    name: 'Quality Score',
    colors: ['#DC2626', '#F59E0B', '#84CC16', '#10B981'],
    scale: [0, 0.3, 0.7, 1.0],
    description: 'Red (poor) to yellow (acceptable) to green (excellent)',
    reversed: false
  }
} as const;

/**
 * Categorical color palettes for plate/batch identification
 */
export const CategoricalPalettes = {
  
  /**
   * Primary palette for plates (up to 10 distinct colors)
   */
  plates: [
    '#3B82F6', // blue
    '#8B5CF6', // purple  
    '#10B981', // emerald
    '#F59E0B', // amber
    '#EF4444', // red
    '#06B6D4', // cyan
    '#84CC16', // lime
    '#F97316', // orange
    '#EC4899', // pink
    '#6366F1'  // indigo
  ],

  /**
   * High contrast palette for accessibility
   */
  highContrast: [
    '#000000', // black
    '#FFFFFF', // white
    '#FF0000', // red
    '#00FF00', // green
    '#0000FF', // blue
    '#FFFF00', // yellow
    '#FF00FF', // magenta
    '#00FFFF'  // cyan
  ],

  /**
   * Colorblind-friendly palette (Okabe-Ito)
   */
  colorblindFriendly: [
    '#E69F00', // orange
    '#56B4E9', // sky blue
    '#009E73', // bluish green
    '#F0E442', // yellow
    '#0072B2', // blue
    '#D55E00', // vermillion
    '#CC79A7', // reddish purple
    '#000000'  // black
  ]
} as const;

/**
 * Color utility functions
 */
export class ColorUtils {
  
  /**
   * Convert hex color to RGB values
   */
  static hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

  /**
   * Convert RGB to RGBA with opacity
   */
  static rgbToRgba(r: number, g: number, b: number, alpha: number = 1): string {
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  /**
   * Convert hex color to RGBA
   */
  static hexToRgba(hex: string, alpha: number = 1): string {
    const rgb = this.hexToRgb(hex);
    return rgb ? this.rgbToRgba(rgb.r, rgb.g, rgb.b, alpha) : hex;
  }

  /**
   * Get color for value based on scale
   */
  static getColorForValue(
    value: number, 
    scale: readonly number[], 
    colors: readonly string[]
  ): string {
    if (scale.length !== colors.length) {
      throw new Error('Scale and colors arrays must have the same length');
    }

    // Handle edge cases
    if (value <= scale[0]) return colors[0];
    if (value >= scale[scale.length - 1]) return colors[colors.length - 1];

    // Find interpolation range
    for (let i = 0; i < scale.length - 1; i++) {
      if (value >= scale[i] && value <= scale[i + 1]) {
        const t = (value - scale[i]) / (scale[i + 1] - scale[i]);
        return this.interpolateColor(colors[i], colors[i + 1], t);
      }
    }

    return colors[0]; // fallback
  }

  /**
   * Interpolate between two hex colors
   */
  static interpolateColor(color1: string, color2: string, factor: number): string {
    const rgb1 = this.hexToRgb(color1);
    const rgb2 = this.hexToRgb(color2);
    
    if (!rgb1 || !rgb2) return color1;

    const r = Math.round(rgb1.r + (rgb2.r - rgb1.r) * factor);
    const g = Math.round(rgb1.g + (rgb2.g - rgb1.g) * factor);
    const b = Math.round(rgb1.b + (rgb2.b - rgb1.b) * factor);

    return `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`;
  }

  /**
   * Check if color has sufficient contrast (WCAG AA standard)
   */
  static hasGoodContrast(color1: string, color2: string): boolean {
    const contrast = this.getContrastRatio(color1, color2);
    return contrast >= 4.5; // WCAG AA standard
  }

  /**
   * Calculate contrast ratio between two colors
   */
  static getContrastRatio(color1: string, color2: string): number {
    const l1 = this.getLuminance(color1);
    const l2 = this.getLuminance(color2);
    
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    
    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Get relative luminance of a color
   */
  private static getLuminance(hex: string): number {
    const rgb = this.hexToRgb(hex);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Generate color palette for N categories
   */
  static generateCategoricalPalette(
    count: number, 
    basePalette: readonly string[] = CategoricalPalettes.plates
  ): string[] {
    if (count <= basePalette.length) {
      return basePalette.slice(0, count) as string[];
    }

    const palette = [...basePalette];
    
    // Generate additional colors by varying opacity
    for (let i = basePalette.length; i < count; i++) {
      const baseIndex = i % basePalette.length;
      const opacity = Math.max(0.3, 1 - Math.floor(i / basePalette.length) * 0.2);
      palette.push(this.hexToRgba(basePalette[baseIndex], opacity));
    }

    return palette;
  }

  /**
   * Get appropriate text color (black or white) for background
   */
  static getTextColor(backgroundColor: string): string {
    const luminance = this.getLuminance(backgroundColor);
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
  }

  /**
   * Create Plotly-compatible colorscale
   */
  static createPlotlyColorscale(
    scale: readonly number[], 
    colors: readonly string[]
  ): Array<[number, string]> {
    const min = Math.min(...scale);
    const max = Math.max(...scale);
    const range = max - min;

    return scale.map((value, index) => {
      const normalized = range === 0 ? 0 : (value - min) / range;
      return [normalized, colors[index]] as [number, string];
    });
  }
}

export default {
  CoreColors,
  ScientificColorScales,
  CategoricalPalettes,
  ColorUtils
};