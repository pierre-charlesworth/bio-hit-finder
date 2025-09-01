import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BarChart3, TrendingUp, AlertTriangle, Download, Eye, Loader2 } from 'lucide-react';
import { useAnalysis } from '@/contexts/AnalysisContext';
import { useAnalysisDefaults } from '@/hooks/useApi';

const AnalysisDashboard = () => {
  const { currentAnalysis, isAnalyzing } = useAnalysis();
  const { data: analysisDefaults, isLoading: configLoading } = useAnalysisDefaults();

  // Calculate actual results from analysis data
  const results = currentAnalysis ? {
    totalWells: currentAnalysis.total_wells,
    platformHits: currentAnalysis.summary?.stage3_platform_hits || 0,
    reporterHits: currentAnalysis.summary?.stage1_reporter_hits || 0,
    vitalityHits: currentAnalysis.summary?.stage2_vitality_hits || 0,
    platformHitRate: currentAnalysis.summary?.stage3_platform_hit_rate || 0,
    reporterHitRate: currentAnalysis.summary?.stage1_reporter_hit_rate || 0,
    vitalityHitRate: currentAnalysis.summary?.stage2_vitality_hit_rate || 0,
    analysisType: currentAnalysis.analysis_type || 'multi-stage',
    fileName: currentAnalysis.file_name || 'Demo Data'
  } : null;

  // Use config defaults for thresholds
  const config = analysisDefaults || {
    z_score_threshold: 2.0,
    viability_gate: 0.3,
    b_score_iterations: 5,
    edge_effect_warning_threshold: 0.15
  };

  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-light tracking-tight mb-4">Analysis Dashboard</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            {results ? `Results from ${results.fileName}` : 'Run demo or upload data to see analysis results'}
          </p>
          {isAnalyzing && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Analyzing...</span>
            </div>
          )}
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-12">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light">{results?.totalWells || '—'}</div>
              <div className="text-sm text-muted-foreground">Total Wells</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light text-green-600">{results?.platformHits || '—'}</div>
              <div className="text-sm text-muted-foreground">Platform Hits</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light">{results ? `${(results.platformHitRate * 100).toFixed(1)}%` : '—'}</div>
              <div className="text-sm text-muted-foreground">Platform Hit Rate</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light text-blue-600">{results?.reporterHits || '—'}</div>
              <div className="text-sm text-muted-foreground">Reporter Hits</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light text-purple-600">{results?.vitalityHits || '—'}</div>
              <div className="text-sm text-muted-foreground">Vitality Hits</div>
            </CardContent>
          </Card>
        </div>

        {/* Analysis Results */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                B-Score Analysis
              </CardTitle>
              <CardDescription>
                Statistical analysis results with hit calling
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Z-Score Threshold:</span>
                  <Badge variant="outline">±{config.z_score_threshold}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Viability Gate:</span>
                  <Badge variant="outline">{config.viability_gate}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">B-Score Iterations:</span>
                  <Badge variant="outline">{config.b_score_iterations}</Badge>
                </div>
                <div className="pt-4 space-y-2">
                  <Button variant="outline" size="sm" className="w-full">
                    <Eye className="h-4 w-4 mr-2" />
                    View B-Score Heatmap
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Edge Effects Detection
              </CardTitle>
              <CardDescription>
                Spatial analysis and correction factors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Edge Wells Detected:</span>
                  <Badge variant={results ? "destructive" : "outline"}>
                    {results ? '—' : '—'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Correction Applied:</span>
                  <Badge variant="secondary">
                    {config?.quality_control?.spatial_correction ? 'Yes' : 'No'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Warning Threshold:</span>
                  <Badge variant="outline">
                    {(config.edge_effect_warning_threshold * 100).toFixed(0)}%
                  </Badge>
                </div>
                <div className="pt-4 space-y-2">
                  <Button variant="outline" size="sm" className="w-full">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    View Spatial Analysis
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Visualizations Grid */}
        <Card>
          <CardHeader>
            <CardTitle>Visualization Suite</CardTitle>
            <CardDescription>
              Interactive charts and heatmaps for data exploration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="border border-border rounded-lg p-6 text-center hover:bg-muted/50 transition-colors cursor-pointer">
                <div className="h-32 bg-gradient-to-br from-primary/20 to-primary/5 rounded mb-4 flex items-center justify-center">
                  <BarChart3 className="h-12 w-12 text-primary/60" />
                </div>
                <h3 className="font-medium mb-2">Dose-Response Curves</h3>
                <p className="text-sm text-muted-foreground">IC50 analysis and curve fitting</p>
              </div>
              
              <div className="border border-border rounded-lg p-6 text-center hover:bg-muted/50 transition-colors cursor-pointer">
                <div className="h-32 bg-gradient-to-br from-secondary/20 to-secondary/5 rounded mb-4 flex items-center justify-center">
                  <div className="grid grid-cols-4 gap-1">
                    {Array.from({ length: 16 }).map((_, i) => (
                      <div key={i} className="w-2 h-2 bg-secondary/60 rounded-sm"></div>
                    ))}
                  </div>
                </div>
                <h3 className="font-medium mb-2">Plate Heatmaps</h3>
                <p className="text-sm text-muted-foreground">Spatial distribution visualization</p>
              </div>
              
              <div className="border border-border rounded-lg p-6 text-center hover:bg-muted/50 transition-colors cursor-pointer">
                <div className="h-32 bg-gradient-to-br from-accent/20 to-accent/5 rounded mb-4 flex items-center justify-center">
                  <TrendingUp className="h-12 w-12 text-accent-foreground/60" />
                </div>
                <h3 className="font-medium mb-2">Quality Control</h3>
                <p className="text-sm text-muted-foreground">Z-factor and control metrics</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Export Options */}
        <div className="mt-12 text-center">
          <Card className="inline-block">
            <CardContent className="p-6">
              <h3 className="text-lg font-medium mb-4">Export Results</h3>
              <div className="flex gap-3">
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  CSV Report
                </Button>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  PDF Summary
                </Button>
                <Button>
                  <Download className="h-4 w-4 mr-2" />
                  Complete Package
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default AnalysisDashboard;