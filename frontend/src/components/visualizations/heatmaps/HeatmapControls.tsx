/**
 * HeatmapControls.tsx
 * 
 * Data type selection interface and heatmap configuration controls
 * Provides scientific data type switching and visualization customization
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { 
  Activity, 
  Palette, 
  Settings, 
  Download, 
  RotateCcw,
  Info,
  Eye,
  EyeOff
} from 'lucide-react';
import { ColorScale, COLOR_SCALES } from '../shared/ColorScaleMapper';
import { WellData } from '../shared/DataProcessor';

export interface HeatmapControlsProps {
  dataType: keyof WellData;
  colorScale: ColorScale;
  onDataTypeChange: (dataType: keyof WellData) => void;
  onColorScaleChange: (scale: ColorScale) => void;
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  showTooltips: boolean;
  onTooltipToggle: (show: boolean) => void;
  showAxisLabels: boolean;
  onAxisLabelsToggle: (show: boolean) => void;
  showGrid: boolean;
  onGridToggle: (show: boolean) => void;
  selectedWells: string[];
  onClearSelection?: () => void;
  className?: string;
}

// Available data types for heatmap visualization
const DATA_TYPES: Array<{
  key: keyof WellData;
  label: string;
  description: string;
  category: 'reporter' | 'ratio' | 'quality';
}> = [
  {
    key: 'Z_lptA',
    label: 'Z-Score (lptA)',
    description: 'σE-regulated reporter for LPS transport disruption',
    category: 'reporter'
  },
  {
    key: 'Z_ldtD',
    label: 'Z-Score (ldtD)', 
    description: 'Cpx-regulated reporter for peptidoglycan stress',
    category: 'reporter'
  },
  {
    key: 'Ratio_lptA',
    label: 'Ratio (lptA)',
    description: 'Reporter expression relative to constitutive control',
    category: 'ratio'
  },
  {
    key: 'Ratio_ldtD',
    label: 'Ratio (ldtD)',
    description: 'Reporter expression relative to constitutive control', 
    category: 'ratio'
  },
  {
    key: 'PassViab',
    label: 'Viability Status',
    description: 'ATP-based cell viability assessment',
    category: 'quality'
  }
];

/**
 * Comprehensive heatmap control interface
 */
const HeatmapControls = ({
  dataType,
  colorScale,
  onDataTypeChange,
  onColorScaleChange,
  onExport,
  showTooltips,
  onTooltipToggle,
  showAxisLabels,
  onAxisLabelsToggle,
  showGrid,
  onGridToggle,
  selectedWells,
  onClearSelection,
  className = ''
}: HeatmapControlsProps) => {

  const [activeTab, setActiveTab] = useState<'data' | 'appearance' | 'export'>('data');

  const currentDataType = DATA_TYPES.find(type => type.key === dataType);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Heatmap Controls
          {selectedWells.length > 0 && (
            <Badge variant="secondary" className="ml-auto">
              {selectedWells.length} selected
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="data" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Data
            </TabsTrigger>
            <TabsTrigger value="appearance" className="flex items-center gap-2">
              <Palette className="h-4 w-4" />
              Style
            </TabsTrigger>
            <TabsTrigger value="export" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Export
            </TabsTrigger>
          </TabsList>

          {/* Data Type Selection */}
          <TabsContent value="data" className="space-y-4">
            <div className="space-y-3">
              <Label className="text-sm font-medium">Data Type</Label>
              
              {/* Current Selection Info */}
              {currentDataType && (
                <div className="p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{currentDataType.label}</span>
                    <Badge variant="outline" className="capitalize">
                      {currentDataType.category}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {currentDataType.description}
                  </p>
                </div>
              )}

              {/* Data Type Grid */}
              <div className="grid grid-cols-1 gap-2">
                {DATA_TYPES.map((type) => (
                  <Button
                    key={type.key}
                    variant={dataType === type.key ? "default" : "outline"}
                    onClick={() => onDataTypeChange(type.key)}
                    className="justify-start h-auto p-3"
                  >
                    <div className="text-left">
                      <div className="font-medium">{type.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {type.description}
                      </div>
                    </div>
                  </Button>
                ))}
              </div>

              {/* Color Scale Selection */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Color Scale</Label>
                <Select
                  value={colorScale.name}
                  onValueChange={(scaleName) => {
                    const newScale = COLOR_SCALES[scaleName] || colorScale;
                    onColorScaleChange(newScale);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(COLOR_SCALES).map(([key, scale]) => (
                      <SelectItem key={key} value={scale.name}>
                        <div className="flex items-center gap-2">
                          <div className="flex h-3 w-6">
                            {scale.colors.slice(0, 3).map((color, i) => (
                              <div
                                key={i}
                                className="flex-1"
                                style={{ backgroundColor: color }}
                              />
                            ))}
                          </div>
                          {scale.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {colorScale.description}
                </p>
              </div>
            </div>
          </TabsContent>

          {/* Appearance Controls */}
          <TabsContent value="appearance" className="space-y-4">
            <div className="space-y-4">
              {/* Display Options */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Display Options</Label>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {showTooltips ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    <Label htmlFor="tooltips">Interactive Tooltips</Label>
                  </div>
                  <Switch
                    id="tooltips"
                    checked={showTooltips}
                    onCheckedChange={onTooltipToggle}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="axis-labels">Axis Labels</Label>
                  <Switch
                    id="axis-labels"
                    checked={showAxisLabels}
                    onCheckedChange={onAxisLabelsToggle}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="grid">Background Grid</Label>
                  <Switch
                    id="grid"
                    checked={showGrid}
                    onCheckedChange={onGridToggle}
                  />
                </div>
              </div>

              {/* Selection Management */}
              {selectedWells.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Selection</Label>
                  <div className="flex items-center justify-between p-2 bg-muted/50 rounded">
                    <span className="text-sm">
                      {selectedWells.length} wells selected
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onClearSelection}
                      className="h-7"
                    >
                      <RotateCcw className="h-3 w-3 mr-1" />
                      Clear
                    </Button>
                  </div>
                </div>
              )}

              {/* Color Scale Preview */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Color Scale Preview</Label>
                <div className="h-4 rounded overflow-hidden flex">
                  {colorScale.colors.map((color, index) => (
                    <div
                      key={index}
                      className="flex-1"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{colorScale.domain[0]}</span>
                  {colorScale.center !== undefined && (
                    <span>{colorScale.center}</span>
                  )}
                  <span>{colorScale.domain[1]}</span>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Export Controls */}
          <TabsContent value="export" className="space-y-4">
            <div className="space-y-4">
              <Label className="text-sm font-medium">Export Options</Label>
              
              <div className="grid grid-cols-1 gap-2">
                <Button
                  variant="outline"
                  onClick={() => onExport?.('png')}
                  className="justify-start"
                >
                  <Download className="h-4 w-4 mr-2" />
                  High-Resolution PNG
                </Button>
                <Button
                  variant="outline"
                  onClick={() => onExport?.('svg')}
                  className="justify-start"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Vector SVG
                </Button>
                <Button
                  variant="outline"
                  onClick={() => onExport?.('pdf')}
                  className="justify-start"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Publication PDF
                </Button>
              </div>

              {/* Export Info */}
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-blue-600 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Export Guidelines</p>
                    <ul className="text-xs space-y-1">
                      <li>• PNG: Best for presentations and web use</li>
                      <li>• SVG: Scalable vector format for figures</li>
                      <li>• PDF: Publication-ready with embedded metadata</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default HeatmapControls;