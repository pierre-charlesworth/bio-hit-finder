/**
 * ColorScaleLegend.tsx
 * 
 * Dynamic legend component with statistical interpretation
 * Displays color scale mapping with scientific context and data distribution
 */

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  ColorScale, 
  generateColorScaleLegend,
  mapValueToColor 
} from '../shared/ColorScaleMapper';
import { Info, TrendingUp, Activity } from 'lucide-react';

export interface ColorScaleLegendProps {
  colorScale: ColorScale;
  dataValues: number[];
  dataType: string;
  selectedCount?: number;
  showStatistics?: boolean;
  showInterpretation?: boolean;
  orientation?: 'horizontal' | 'vertical';
  height?: number;
  width?: number;
  className?: string;
}

/**
 * Scientific color scale legend with data distribution overlay
 */
const ColorScaleLegend = ({
  colorScale,
  dataValues,
  dataType,
  selectedCount = 0,
  showStatistics = true,
  showInterpretation = true,
  orientation = 'vertical',
  height = 300,
  width = 60,
  className = ''
}: ColorScaleLegendProps) => {

  // Calculate data statistics
  const statistics = useMemo(() => {
    const finiteValues = dataValues.filter(v => isFinite(v));
    
    if (finiteValues.length === 0) {
      return {
        count: 0,
        min: 0,
        max: 0,
        mean: 0,
        median: 0,
        std: 0,
        p25: 0,
        p75: 0
      };
    }

    const sorted = finiteValues.slice().sort((a, b) => a - b);
    const mean = finiteValues.reduce((sum, v) => sum + v, 0) / finiteValues.length;
    const variance = finiteValues.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / finiteValues.length;
    
    return {
      count: finiteValues.length,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      mean,
      median: sorted[Math.floor(sorted.length / 2)],
      std: Math.sqrt(variance),
      p25: sorted[Math.floor(sorted.length * 0.25)],
      p75: sorted[Math.floor(sorted.length * 0.75)]
    };
  }, [dataValues]);

  // Generate legend steps
  const legendSteps = useMemo(() => {
    return generateColorScaleLegend(colorScale, 50);
  }, [colorScale]);

  // Calculate data distribution on the color scale
  const dataDistribution = useMemo(() => {
    const [minDomain, maxDomain] = colorScale.domain;
    const binCount = 20;
    const binWidth = (maxDomain - minDomain) / binCount;
    const bins = new Array(binCount).fill(0);

    dataValues.filter(v => isFinite(v)).forEach(value => {
      const clampedValue = Math.max(minDomain, Math.min(maxDomain, value));
      const binIndex = Math.min(binCount - 1, Math.floor((clampedValue - minDomain) / binWidth));
      bins[binIndex]++;
    });

    const maxBinCount = Math.max(...bins);
    
    return bins.map((count, index) => ({
      value: minDomain + (index + 0.5) * binWidth,
      count,
      percentage: maxBinCount > 0 ? count / maxBinCount : 0
    }));
  }, [dataValues, colorScale]);

  // Generate scientific interpretation
  const interpretation = useMemo(() => {
    const { mean, std, count } = statistics;
    const [minDomain, maxDomain] = colorScale.domain;
    
    if (count === 0) return 'No data available for interpretation.';

    let text = '';

    // Data type specific interpretation
    if (dataType.toLowerCase().includes('z_score')) {
      const outliers = dataValues.filter(v => Math.abs(v) > 2).length;
      const outlierRate = count > 0 ? (outliers / count) * 100 : 0;
      
      text = `Z-score distribution (μ=${mean.toFixed(2)}, σ=${std.toFixed(2)}) with ${outliers} outliers (${outlierRate.toFixed(1)}%) exceeding ±2 threshold. `;
      
      if (Math.abs(mean) > 0.5) {
        text += 'Distribution appears shifted, suggesting systematic bias. ';
      }
      
      if (outlierRate > 5) {
        text += 'High outlier rate indicates potential biological hits or technical artifacts.';
      } else if (outlierRate < 1) {
        text += 'Low outlier rate suggests well-controlled assay conditions.';
      }
    } else if (dataType.toLowerCase().includes('ratio')) {
      const highRatio = dataValues.filter(v => v > 1.5).length;
      const highRatioRate = count > 0 ? (highRatio / count) * 100 : 0;
      
      text = `Ratio distribution centered at ${mean.toFixed(2)} with ${highRatio} wells (${highRatioRate.toFixed(1)}%) showing >1.5-fold changes. `;
      text += 'Values >1.5 indicate significant reporter activation.';
    } else if (dataType.toLowerCase().includes('viab')) {
      const viable = dataValues.filter(v => v > 0.3).length;
      const viabilityRate = count > 0 ? (viable / count) * 100 : 0;
      
      text = `Viability assessment shows ${viable} viable wells (${viabilityRate.toFixed(1)}%). `;
      
      if (viabilityRate >= 80) {
        text += 'Excellent viability indicates high-quality assay conditions.';
      } else if (viabilityRate >= 70) {
        text += 'Good viability within acceptable range for screening.';
      } else {
        text += 'Low viability may indicate cytotoxic conditions or technical problems.';
      }
    }

    return text;
  }, [statistics, dataType, dataValues, colorScale]);

  const isHorizontal = orientation === 'horizontal';

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Activity className="h-4 w-4" />
          {colorScale.name}
          {selectedCount > 0 && (
            <Badge variant="secondary" className="ml-auto text-xs">
              {selectedCount} selected
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        
        {/* Color Scale */}
        <div className="relative">
          <svg
            width={isHorizontal ? width : 40}
            height={isHorizontal ? 40 : height}
            className="border border-border rounded"
          >
            {/* Color gradient */}
            <defs>
              <linearGradient
                id="colorGradient"
                x1="0%"
                y1={isHorizontal ? "0%" : "100%"}
                x2={isHorizontal ? "100%" : "0%"}
                y2={isHorizontal ? "0%" : "0%"}
              >
                {colorScale.colors.map((color, index) => (
                  <stop
                    key={index}
                    offset={`${(index / (colorScale.colors.length - 1)) * 100}%`}
                    stopColor={color}
                  />
                ))}
              </linearGradient>
            </defs>
            
            <rect
              width="100%"
              height="100%"
              fill="url(#colorGradient)"
            />

            {/* Data distribution overlay */}
            {dataDistribution.length > 0 && (
              <g className="data-distribution" opacity="0.3">
                {dataDistribution.map((bin, index) => {
                  if (bin.percentage === 0) return null;
                  
                  const position = (bin.value - colorScale.domain[0]) / 
                                 (colorScale.domain[1] - colorScale.domain[0]);
                  
                  if (isHorizontal) {
                    const x = position * width;
                    const barHeight = bin.percentage * 20;
                    return (
                      <rect
                        key={index}
                        x={x - 1}
                        y={40 - barHeight}
                        width={2}
                        height={barHeight}
                        fill="rgba(0,0,0,0.6)"
                      />
                    );
                  } else {
                    const y = (1 - position) * height;
                    const barWidth = bin.percentage * 20;
                    return (
                      <rect
                        key={index}
                        x={40 - barWidth}
                        y={y - 1}
                        width={barWidth}
                        height={2}
                        fill="rgba(0,0,0,0.6)"
                      />
                    );
                  }
                })}
              </g>
            )}
          </svg>

          {/* Scale labels */}
          <div className={`absolute ${isHorizontal ? 'top-full mt-1' : 'left-full ml-2'} flex ${
            isHorizontal ? 'justify-between w-full' : 'flex-col justify-between h-full'
          } text-xs text-muted-foreground`}>
            <span>{colorScale.domain[1].toFixed(1)}</span>
            {colorScale.center !== undefined && (
              <span className={isHorizontal ? '' : 'text-center'}>
                {colorScale.center.toFixed(1)}
              </span>
            )}
            <span>{colorScale.domain[0].toFixed(1)}</span>
          </div>
        </div>

        {/* Statistics */}
        {showStatistics && statistics.count > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              Distribution
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-muted-foreground">Count:</span>
                <span className="font-medium ml-1">{statistics.count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Range:</span>
                <span className="font-medium ml-1">
                  {statistics.min.toFixed(2)} – {statistics.max.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Mean:</span>
                <span className="font-medium ml-1">{statistics.mean.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Std:</span>
                <span className="font-medium ml-1">{statistics.std.toFixed(2)}</span>
              </div>
            </div>

            {/* Percentiles */}
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Q1: {statistics.p25.toFixed(2)}</span>
              <span>Median: {statistics.median.toFixed(2)}</span>
              <span>Q3: {statistics.p75.toFixed(2)}</span>
            </div>
          </div>
        )}

        {/* Scientific Interpretation */}
        {showInterpretation && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium flex items-center gap-1">
              <Info className="h-3 w-3" />
              Interpretation
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {interpretation}
            </p>
          </div>
        )}

        {/* Color Scale Info */}
        <div className="pt-2 border-t">
          <p className="text-xs text-muted-foreground">
            {colorScale.description}
          </p>
          {colorScale.type === 'diverging' && (
            <p className="text-xs text-muted-foreground mt-1">
              Diverging scale centered at {colorScale.center || 0}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ColorScaleLegend;