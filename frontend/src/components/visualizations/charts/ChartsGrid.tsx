import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BarChart3, TrendingUp, Activity, Download, Settings } from 'lucide-react';
import { AnalysisResult } from '@/types/analysis';

import HistogramChart from './HistogramChart';
import ScatterChart from './ScatterChart';  
import BarChart from './BarChart';

interface ChartsGridProps {
  analysisData: AnalysisResult;
  zScoreThreshold?: number;
  onExportAll?: () => void;
  className?: string;
}

/**
 * Main visualization container with responsive grid layout
 * Matches original Streamlit visualization tab structure
 */
const ChartsGrid = ({
  analysisData,
  zScoreThreshold = 2.0,
  onExportAll,
  className = ''
}: ChartsGridProps) => {

  const [exportFormat, setExportFormat] = useState<'png' | 'svg' | 'pdf'>('png');
  const [selectedView, setSelectedView] = useState<'grid' | 'individual'>('grid');

  // Extract summary statistics for overview
  const totalWells = analysisData?.total_wells || 0;
  const summary = analysisData?.summary;

  const handleChartExport = (chartName: string, format: 'png' | 'svg' | 'pdf') => {
    console.log(`Exporting ${chartName} as ${format.toUpperCase()}`);
    // TODO: Implement individual chart export
  };

  const handleExportAll = () => {
    if (onExportAll) {
      onExportAll();
    } else {
      console.log(`Exporting all charts as ${exportFormat.toUpperCase()}`);
      // TODO: Implement batch export functionality
    }
  };

  if (!analysisData || !analysisData.results || analysisData.results.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-12 text-center">
          <div className="text-muted-foreground">
            <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No Data Available</h3>
            <p className="text-sm">
              Process your plate data to see comprehensive statistical visualizations including 
              Z-score distributions, ratio correlations, and viability analysis.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Statistical Visualizations
                <Badge variant="secondary" className="ml-2">
                  {totalWells.toLocaleString()} wells
                </Badge>
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Interactive statistical analysis of dual-reporter screening data with quality control metrics
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              {/* View toggle */}
              <Tabs value={selectedView} onValueChange={(v) => setSelectedView(v as 'grid' | 'individual')}>
                <TabsList className="grid w-32 grid-cols-2">
                  <TabsTrigger value="grid" className="text-xs">Grid</TabsTrigger>
                  <TabsTrigger value="individual" className="text-xs">Tabs</TabsTrigger>
                </TabsList>
              </Tabs>

              {/* Export controls */}
              <div className="flex items-center gap-1">
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as 'png' | 'svg' | 'pdf')}
                  className="text-xs px-2 py-1 border border-border rounded"
                >
                  <option value="png">PNG</option>
                  <option value="svg">SVG</option>
                  <option value="pdf">PDF</option>
                </select>
                <Button variant="outline" size="sm" onClick={handleExportAll}>
                  <Download className="h-3 w-3 mr-1" />
                  Export All
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Chart content */}
      {selectedView === 'grid' ? (
        /* Grid Layout (2x2) */
        <div className="grid md:grid-cols-2 gap-6">
          {/* Z_lptA Histogram */}
          <HistogramChart
            analysisData={analysisData}
            column="Z_lptA"
            title="Z-Score Distribution (lptA)"
            description="σE-regulated reporter for LPS transport disruption"
            color="#3B82F6" // blue
            threshold={zScoreThreshold}
            showThresholds={true}
            onExport={(format) => handleChartExport('Z_lptA_histogram', format)}
          />

          {/* Z_ldtD Histogram */}
          <HistogramChart
            analysisData={analysisData}
            column="Z_ldtD"
            title="Z-Score Distribution (ldtD)"
            description="Cpx-regulated reporter for peptidoglycan stress"
            color="#059669" // emerald
            threshold={zScoreThreshold}
            showThresholds={true}
            onExport={(format) => handleChartExport('Z_ldtD_histogram', format)}
          />

          {/* Ratio Correlation Scatter */}
          <ScatterChart
            analysisData={analysisData}
            xColumn="Ratio_lptA"
            yColumn="Ratio_ldtD"
            colorColumn="PlateID"
            title="Reporter Correlation"
            description="Dual-reporter correlation analysis by plate"
            showTrendline={true}
            onExport={(format) => handleChartExport('ratio_correlation', format)}
          />

          {/* Viability Bar Chart */}
          <BarChart
            analysisData={analysisData}
            title="Viability by Plate"
            description="ATP-based viability assessment for quality control"
            showPercentages={false}
            onExport={(format) => handleChartExport('viability_bars', format)}
          />
        </div>
      ) : (
        /* Tabbed Layout */
        <Tabs defaultValue="distributions" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="distributions" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Distributions
            </TabsTrigger>
            <TabsTrigger value="correlations" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Correlations
            </TabsTrigger>
            <TabsTrigger value="quality" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Quality Control
            </TabsTrigger>
          </TabsList>

          <TabsContent value="distributions" className="space-y-6 mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              <HistogramChart
                analysisData={analysisData}
                column="Z_lptA"
                title="Z-Score Distribution (lptA)"
                description="σE-regulated reporter for LPS transport disruption"
                color="#3B82F6"
                threshold={zScoreThreshold}
                showThresholds={true}
                height={500}
                onExport={(format) => handleChartExport('Z_lptA_histogram', format)}
              />
              <HistogramChart
                analysisData={analysisData}
                column="Z_ldtD"
                title="Z-Score Distribution (ldtD)"
                description="Cpx-regulated reporter for peptidoglycan stress"
                color="#059669"
                threshold={zScoreThreshold}
                showThresholds={true}
                height={500}
                onExport={(format) => handleChartExport('Z_ldtD_histogram', format)}
              />
            </div>
          </TabsContent>

          <TabsContent value="correlations" className="mt-6">
            <ScatterChart
              analysisData={analysisData}
              xColumn="Ratio_lptA"
              yColumn="Ratio_ldtD"
              colorColumn="PlateID"
              title="Reporter Correlation Analysis"
              description="Correlation between dual reporters reveals envelope system interactions"
              showTrendline={true}
              height={600}
              onExport={(format) => handleChartExport('ratio_correlation', format)}
            />
          </TabsContent>

          <TabsContent value="quality" className="mt-6">
            <BarChart
              analysisData={analysisData}
              title="Viability Quality Control"
              description="ATP-based viability assessment ensures data quality and identifies problematic plates"
              showPercentages={true}
              height={500}
              onExport={(format) => handleChartExport('viability_qc', format)}
            />
          </TabsContent>
        </Tabs>
      )}

      {/* Summary statistics footer */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-sm">
            <div>
              <div className="font-medium text-blue-600">
                {summary?.stage1_reporter_hits || 0}
              </div>
              <div className="text-muted-foreground">Reporter Hits</div>
            </div>
            <div>
              <div className="font-medium text-purple-600">
                {summary?.stage2_vitality_hits || 0}
              </div>
              <div className="text-muted-foreground">Vitality Hits</div>
            </div>
            <div>
              <div className="font-medium text-green-600">
                {summary?.stage3_platform_hits || 0}
              </div>
              <div className="text-muted-foreground">Platform Hits</div>
            </div>
            <div>
              <div className="font-medium text-gray-600">
                ±{zScoreThreshold}
              </div>
              <div className="text-muted-foreground">Z-Score Threshold</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChartsGrid;