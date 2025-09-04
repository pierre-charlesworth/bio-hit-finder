/**
 * EdgeEffectOverlay.tsx
 * 
 * Spatial artifact visualization component for edge effect detection
 * Identifies and highlights spatial patterns in plate-based assays
 */

import { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { WellPosition } from '../shared/WellPositionMapper';
import { WellData } from '../shared/DataProcessor';
import { AlertTriangle, Info, Eye, EyeOff } from 'lucide-react';

export interface EdgeEffect {
  type: 'edge' | 'corner' | 'center' | 'row' | 'column';
  severity: 'low' | 'medium' | 'high';
  affectedWells: string[];
  description: string;
  statistics: {
    meanEffect: number;
    maxEffect: number;
    pValue?: number;
  };
}

export interface EdgeEffectOverlayProps {
  wells: WellPosition[];
  wellData: Map<string, WellData>;
  dataType: keyof WellData;
  visible: boolean;
  onToggleVisibility?: (visible: boolean) => void;
  threshold?: number;
  showStatistics?: boolean;
  className?: string;
}

/**
 * Spatial artifact detection and visualization overlay
 */
const EdgeEffectOverlay = ({
  wells,
  wellData,
  dataType,
  visible,
  onToggleVisibility,
  threshold = 0.15,
  showStatistics = true,
  className = ''
}: EdgeEffectOverlayProps) => {

  // Calculate edge effects using spatial correlation analysis
  const edgeEffects = useMemo(() => {
    const effects: EdgeEffect[] = [];
    
    if (wells.length === 0) return effects;

    // Determine plate dimensions
    const maxRow = Math.max(...wells.map(w => w.row));
    const maxCol = Math.max(...wells.map(w => w.column));
    
    // Extract data values with positions
    const dataPoints = wells
      .map(well => {
        const data = wellData.get(well.wellId);
        const value = data?.[dataType];
        return isFinite(value) ? {
          well,
          value: value as number,
          row: well.row,
          column: well.column
        } : null;
      })
      .filter(Boolean);

    if (dataPoints.length < 20) return effects; // Need minimum data points

    // Calculate overall mean for reference
    const overallMean = dataPoints.reduce((sum, p) => sum + p!.value, 0) / dataPoints.length;
    const overallStd = Math.sqrt(
      dataPoints.reduce((sum, p) => sum + Math.pow(p!.value - overallMean, 2), 0) / dataPoints.length
    );

    // 1. Edge Effect Analysis
    const edgeWells = dataPoints.filter(p => 
      p!.row === 0 || p!.row === maxRow || p!.column === 0 || p!.column === maxCol
    );
    const centerWells = dataPoints.filter(p => 
      p!.row > 1 && p!.row < maxRow - 1 && p!.column > 1 && p!.column < maxCol - 1
    );

    if (edgeWells.length > 0 && centerWells.length > 0) {
      const edgeMean = edgeWells.reduce((sum, p) => sum + p!.value, 0) / edgeWells.length;
      const centerMean = centerWells.reduce((sum, p) => sum + p!.value, 0) / centerWells.length;
      const effect = Math.abs(edgeMean - centerMean) / overallStd;

      if (effect > threshold) {
        effects.push({
          type: 'edge',
          severity: effect > 0.5 ? 'high' : effect > 0.3 ? 'medium' : 'low',
          affectedWells: edgeWells.map(p => p!.well.wellId),
          description: `Edge wells show ${effect > 0 ? 'elevated' : 'reduced'} values compared to center (${effect.toFixed(2)}σ difference)`,
          statistics: {
            meanEffect: edgeMean - centerMean,
            maxEffect: effect,
            pValue: calculateTTestPValue(
              edgeWells.map(p => p!.value),
              centerWells.map(p => p!.value)
            )
          }
        });
      }
    }

    // 2. Corner Effect Analysis
    const cornerWells = dataPoints.filter(p => 
      (p!.row === 0 || p!.row === maxRow) && (p!.column === 0 || p!.column === maxCol)
    );

    if (cornerWells.length >= 4) {
      const cornerMean = cornerWells.reduce((sum, p) => sum + p!.value, 0) / cornerWells.length;
      const effect = Math.abs(cornerMean - overallMean) / overallStd;

      if (effect > threshold) {
        effects.push({
          type: 'corner',
          severity: effect > 0.4 ? 'high' : effect > 0.25 ? 'medium' : 'low',
          affectedWells: cornerWells.map(p => p!.well.wellId),
          description: `Corner wells show distinct pattern (${effect.toFixed(2)}σ from mean)`,
          statistics: {
            meanEffect: cornerMean - overallMean,
            maxEffect: effect
          }
        });
      }
    }

    // 3. Row Effects Analysis
    const rowEffects = [];
    for (let row = 0; row <= maxRow; row++) {
      const rowWells = dataPoints.filter(p => p!.row === row);
      if (rowWells.length < 3) continue;

      const rowMean = rowWells.reduce((sum, p) => sum + p!.value, 0) / rowWells.length;
      const effect = Math.abs(rowMean - overallMean) / overallStd;

      if (effect > threshold) {
        rowEffects.push({
          row,
          effect,
          wells: rowWells.map(p => p!.well.wellId),
          mean: rowMean
        });
      }
    }

    if (rowEffects.length > 0) {
      const maxRowEffect = Math.max(...rowEffects.map(r => r.effect));
      effects.push({
        type: 'row',
        severity: maxRowEffect > 0.4 ? 'high' : maxRowEffect > 0.25 ? 'medium' : 'low',
        affectedWells: rowEffects.flatMap(r => r.wells),
        description: `${rowEffects.length} rows show systematic bias (max ${maxRowEffect.toFixed(2)}σ)`,
        statistics: {
          meanEffect: rowEffects.reduce((sum, r) => sum + (r.mean - overallMean), 0) / rowEffects.length,
          maxEffect: maxRowEffect
        }
      });
    }

    // 4. Column Effects Analysis  
    const colEffects = [];
    for (let col = 0; col <= maxCol; col++) {
      const colWells = dataPoints.filter(p => p!.column === col);
      if (colWells.length < 3) continue;

      const colMean = colWells.reduce((sum, p) => sum + p!.value, 0) / colWells.length;
      const effect = Math.abs(colMean - overallMean) / overallStd;

      if (effect > threshold) {
        colEffects.push({
          column: col,
          effect,
          wells: colWells.map(p => p!.well.wellId),
          mean: colMean
        });
      }
    }

    if (colEffects.length > 0) {
      const maxColEffect = Math.max(...colEffects.map(c => c.effect));
      effects.push({
        type: 'column',
        severity: maxColEffect > 0.4 ? 'high' : maxColEffect > 0.25 ? 'medium' : 'low',
        affectedWells: colEffects.flatMap(c => c.wells),
        description: `${colEffects.length} columns show systematic bias (max ${maxColEffect.toFixed(2)}σ)`,
        statistics: {
          meanEffect: colEffects.reduce((sum, c) => sum + (c.mean - overallMean), 0) / colEffects.length,
          maxEffect: maxColEffect
        }
      });
    }

    return effects.sort((a, b) => b.statistics.maxEffect - a.statistics.maxEffect);
  }, [wells, wellData, dataType, threshold]);

  // Generate SVG overlay paths for affected wells
  const overlayPaths = useMemo(() => {
    if (!visible || edgeEffects.length === 0) return [];

    return edgeEffects.map(effect => {
      const affectedPositions = wells.filter(w => effect.affectedWells.includes(w.wellId));
      
      return {
        effect,
        positions: affectedPositions,
        color: getSeverityColor(effect.severity),
        opacity: getSeverityOpacity(effect.severity)
      };
    });
  }, [visible, edgeEffects, wells]);

  if (!visible) return null;

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Toggle and Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => onToggleVisibility?.(!visible)}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            {visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            Edge Effects
          </button>
          {edgeEffects.length > 0 && (
            <Badge 
              variant={getOverallSeverityVariant(edgeEffects)}
              className="text-xs"
            >
              {edgeEffects.length} detected
            </Badge>
          )}
        </div>
      </div>

      {/* Effects List */}
      {visible && edgeEffects.length > 0 && (
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {edgeEffects.map((effect, index) => (
            <div
              key={index}
              className={`p-2 rounded border text-xs ${getSeverityBorderClass(effect.severity)}`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  <span className="font-medium capitalize">{effect.type} Effect</span>
                  <Badge variant="outline" className="text-xs">
                    {effect.severity}
                  </Badge>
                </div>
                <span className="text-muted-foreground">
                  {effect.affectedWells.length} wells
                </span>
              </div>
              <p className="text-muted-foreground">{effect.description}</p>
              
              {showStatistics && (
                <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                  <span>Effect: {effect.statistics.maxEffect.toFixed(3)}σ</span>
                  {effect.statistics.pValue && (
                    <span>p-value: {effect.statistics.pValue.toFixed(3)}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* No Effects Message */}
      {visible && edgeEffects.length === 0 && (
        <div className="p-2 text-xs text-muted-foreground border border-green-200 bg-green-50 rounded flex items-center gap-1">
          <Info className="h-3 w-3" />
          No significant spatial artifacts detected (threshold: {threshold}σ)
        </div>
      )}

      {/* SVG Overlay (returned as render props or separate component) */}
      {visible && overlayPaths.length > 0 && (
        <div className="absolute inset-0 pointer-events-none">
          <svg width="100%" height="100%" className="absolute inset-0">
            {overlayPaths.map((overlay, effectIndex) => (
              <g key={effectIndex} opacity={overlay.opacity}>
                {overlay.positions.map((position, wellIndex) => (
                  <circle
                    key={wellIndex}
                    cx={position.x}
                    cy={position.y}
                    r="8"
                    fill="none"
                    stroke={overlay.color}
                    strokeWidth="2"
                    strokeDasharray="3,2"
                  />
                ))}
              </g>
            ))}
          </svg>
        </div>
      )}
    </div>
  );
};

// Helper functions
function getSeverityColor(severity: EdgeEffect['severity']): string {
  switch (severity) {
    case 'high': return '#EF4444';
    case 'medium': return '#F59E0B';
    case 'low': return '#10B981';
    default: return '#6B7280';
  }
}

function getSeverityOpacity(severity: EdgeEffect['severity']): number {
  switch (severity) {
    case 'high': return 0.8;
    case 'medium': return 0.6;
    case 'low': return 0.4;
    default: return 0.3;
  }
}

function getSeverityBorderClass(severity: EdgeEffect['severity']): string {
  switch (severity) {
    case 'high': return 'border-red-200 bg-red-50';
    case 'medium': return 'border-yellow-200 bg-yellow-50';
    case 'low': return 'border-green-200 bg-green-50';
    default: return 'border-gray-200 bg-gray-50';
  }
}

function getOverallSeverityVariant(effects: EdgeEffect[]): 'default' | 'secondary' | 'destructive' | 'outline' {
  const hasHigh = effects.some(e => e.severity === 'high');
  const hasMedium = effects.some(e => e.severity === 'medium');
  
  if (hasHigh) return 'destructive';
  if (hasMedium) return 'secondary';
  return 'outline';
}

// Simple t-test p-value approximation
function calculateTTestPValue(group1: number[], group2: number[]): number {
  if (group1.length < 2 || group2.length < 2) return 1;

  const mean1 = group1.reduce((sum, v) => sum + v, 0) / group1.length;
  const mean2 = group2.reduce((sum, v) => sum + v, 0) / group2.length;
  
  const var1 = group1.reduce((sum, v) => sum + Math.pow(v - mean1, 2), 0) / (group1.length - 1);
  const var2 = group2.reduce((sum, v) => sum + Math.pow(v - mean2, 2), 0) / (group2.length - 1);
  
  const pooledStd = Math.sqrt(((group1.length - 1) * var1 + (group2.length - 1) * var2) / 
                             (group1.length + group2.length - 2));
  
  const tStat = Math.abs(mean1 - mean2) / (pooledStd * Math.sqrt(1/group1.length + 1/group2.length));
  
  // Rough p-value approximation (for visualization purposes)
  if (tStat > 2.6) return 0.01;
  if (tStat > 2.0) return 0.05;
  if (tStat > 1.65) return 0.1;
  return 0.2;
}

export default EdgeEffectOverlay;