/**
 * HeatmapTooltip.tsx
 * 
 * Interactive well information display for heatmap visualizations
 * Shows detailed data about selected wells with scientific context
 */

import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { WellPosition } from './WellPositionMapper';
import { WellData } from './DataProcessor';

export interface TooltipData {
  wellPosition: WellPosition;
  wellData: WellData;
  colorValue: number;
  colorIntensity: number;
  dataType: string;
}

export interface TooltipPosition {
  x: number;
  y: number;
  visible: boolean;
}

interface HeatmapTooltipProps {
  data: TooltipData | null;
  position: TooltipPosition;
  containerBounds?: DOMRect;
  showExtendedInfo?: boolean;
  className?: string;
}

/**
 * Tooltip component for displaying well information on heatmap hover
 */
const HeatmapTooltip = ({
  data,
  position,
  containerBounds,
  showExtendedInfo = true,
  className = ''
}: HeatmapTooltipProps) => {
  const [adjustedPosition, setAdjustedPosition] = useState({ x: 0, y: 0 });
  const [tooltipBounds, setTooltipBounds] = useState({ width: 0, height: 0 });

  // Adjust tooltip position to stay within container bounds
  useEffect(() => {
    if (!position.visible || !data || !containerBounds) {
      return;
    }

    const tooltipWidth = showExtendedInfo ? 320 : 250;
    const tooltipHeight = showExtendedInfo ? 280 : 180;

    let x = position.x + 15; // Offset from cursor
    let y = position.y - tooltipHeight / 2;

    // Adjust horizontal position
    if (x + tooltipWidth > containerBounds.right) {
      x = position.x - tooltipWidth - 15;
    }

    // Adjust vertical position
    if (y < containerBounds.top) {
      y = containerBounds.top + 10;
    } else if (y + tooltipHeight > containerBounds.bottom) {
      y = containerBounds.bottom - tooltipHeight - 10;
    }

    setAdjustedPosition({ x, y });
    setTooltipBounds({ width: tooltipWidth, height: tooltipHeight });
  }, [position, data, containerBounds, showExtendedInfo]);

  if (!position.visible || !data) {
    return null;
  }

  const { wellPosition, wellData, colorValue, colorIntensity, dataType } = data;

  return (
    <div
      className={`fixed z-50 pointer-events-none ${className}`}
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
        width: tooltipBounds.width
      }}
    >
      <Card className="shadow-lg border-2">
        <CardContent className="p-4 space-y-3">
          {/* Well Header */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-lg">{wellPosition.wellId}</h3>
              <p className="text-sm text-muted-foreground">
                Row {wellPosition.rowLabel}, Col {wellPosition.columnLabel}
              </p>
            </div>
            <Badge 
              variant={getQualityBadgeVariant(wellData)}
              className="text-xs"
            >
              {wellData.PassViab ? 'Viable' : 'Non-viable'}
            </Badge>
          </div>

          {/* Primary Data Value */}
          <div className="border-l-4 border-primary pl-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">
                {formatDataTypeLabel(dataType)}
              </span>
              <span className="text-lg font-bold">
                {formatValue(colorValue, dataType)}
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 mt-1">
              <div
                className="h-2 rounded-full transition-all duration-200"
                style={{
                  width: `${Math.abs(colorIntensity) * 100}%`,
                  backgroundColor: getIntensityColor(colorIntensity, dataType)
                }}
              />
            </div>
          </div>

          {/* Extended Information */}
          {showExtendedInfo && (
            <div className="space-y-2 border-t pt-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <TooltipField 
                  label="Z lptA" 
                  value={wellData.Z_lptA} 
                  format="decimal" 
                />
                <TooltipField 
                  label="Z ldtD" 
                  value={wellData.Z_ldtD} 
                  format="decimal" 
                />
                <TooltipField 
                  label="Ratio lptA" 
                  value={wellData.Ratio_lptA} 
                  format="ratio" 
                />
                <TooltipField 
                  label="Ratio ldtD" 
                  value={wellData.Ratio_ldtD} 
                  format="ratio" 
                />
              </div>

              {wellData.PlateID && (
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="text-xs text-muted-foreground">Plate ID:</span>
                  <Badge variant="outline" className="text-xs">
                    {wellData.PlateID}
                  </Badge>
                </div>
              )}

              {/* Scientific Interpretation */}
              <div className="text-xs text-muted-foreground pt-2 border-t">
                {getScientificInterpretation(wellData, dataType)}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Individual tooltip field component
 */
interface TooltipFieldProps {
  label: string;
  value: number;
  format: 'decimal' | 'ratio' | 'percentage';
}

const TooltipField = ({ label, value, format }: TooltipFieldProps) => (
  <div>
    <div className="text-xs text-muted-foreground">{label}</div>
    <div className="font-medium">
      {formatValue(value, format)}
    </div>
  </div>
);

/**
 * Formats values based on data type
 */
function formatValue(value: number, dataType: string): string {
  if (!isFinite(value)) {
    return 'N/A';
  }

  const lowerType = dataType.toLowerCase();

  if (lowerType.includes('ratio')) {
    return value.toFixed(3);
  } else if (lowerType.includes('viab') || lowerType.includes('percentage')) {
    return `${(value * 100).toFixed(1)}%`;
  } else if (lowerType.includes('z_score') || lowerType.includes('b_score')) {
    return value.toFixed(2);
  } else {
    // Auto-format based on magnitude
    if (Math.abs(value) >= 100) {
      return value.toFixed(0);
    } else if (Math.abs(value) >= 10) {
      return value.toFixed(1);
    } else {
      return value.toFixed(2);
    }
  }
}

/**
 * Formats data type labels for display
 */
function formatDataTypeLabel(dataType: string): string {
  const typeMap: Record<string, string> = {
    'Z_lptA': 'Z-Score (lptA)',
    'Z_ldtD': 'Z-Score (ldtD)',
    'Ratio_lptA': 'Ratio (lptA)',
    'Ratio_ldtD': 'Ratio (ldtD)',
    'PassViab': 'Viability',
    'B_lptA': 'B-Score (lptA)',
    'B_ldtD': 'B-Score (ldtD)'
  };

  return typeMap[dataType] || dataType.replace(/_/g, ' ');
}

/**
 * Gets badge variant based on well quality
 */
function getQualityBadgeVariant(wellData: WellData): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (!wellData.PassViab) {
    return 'destructive';
  }

  // Check for strong hits (high Z-scores)
  const maxZ = Math.max(Math.abs(wellData.Z_lptA || 0), Math.abs(wellData.Z_ldtD || 0));
  if (maxZ >= 2.0) {
    return 'default'; // Primary color for hits
  }

  return 'secondary';
}

/**
 * Gets color for intensity bar based on data type
 */
function getIntensityColor(intensity: number, dataType: string): string {
  const lowerType = dataType.toLowerCase();

  if (lowerType.includes('z_score') || lowerType.includes('zscore')) {
    return intensity >= 0 ? '#EF4444' : '#3B82F6'; // Red for positive, blue for negative
  } else if (lowerType.includes('b_score') || lowerType.includes('bscore')) {
    return intensity >= 0 ? '#EC4899' : '#8B5CF6'; // Pink for positive, purple for negative
  } else if (lowerType.includes('ratio')) {
    return '#3B82F6'; // Blue for ratios
  } else if (lowerType.includes('viab')) {
    return '#10B981'; // Green for viability
  }

  return '#6B7280'; // Gray default
}

/**
 * Generates scientific interpretation text
 */
function getScientificInterpretation(wellData: WellData, dataType: string): string {
  if (!wellData.PassViab) {
    return 'Non-viable well excluded from hit analysis due to low ATP levels.';
  }

  const lowerType = dataType.toLowerCase();
  
  if (lowerType.includes('z_lpta')) {
    const zScore = wellData.Z_lptA || 0;
    if (Math.abs(zScore) >= 2.0) {
      return `Strong ${zScore > 0 ? 'activation' : 'inhibition'} of σE-regulated lptA reporter, suggesting LPS transport disruption.`;
    }
    return 'lptA reporter within normal range, no significant LPS transport effects detected.';
  }

  if (lowerType.includes('z_ldtd')) {
    const zScore = wellData.Z_ldtD || 0;
    if (Math.abs(zScore) >= 2.0) {
      return `Strong ${zScore > 0 ? 'activation' : 'inhibition'} of Cpx-regulated ldtD reporter, indicating peptidoglycan stress.`;
    }
    return 'ldtD reporter within normal range, no significant peptidoglycan stress detected.';
  }

  if (lowerType.includes('ratio')) {
    return 'Reporter ratio indicates relative reporter expression levels normalized to constitutive control.';
  }

  return 'Well data within expected parameters for this assay type.';
}

export default HeatmapTooltip;