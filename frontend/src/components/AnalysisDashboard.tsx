import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BarChart3, TrendingUp, AlertTriangle, Download, Eye } from 'lucide-react';

const AnalysisDashboard = () => {
  const mockResults = {
    totalWells: 1536,
    hits: 47,
    hitRate: 3.1,
    plateCount: 4,
    processingTime: "1.2s"
  };

  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-light tracking-tight mb-4">Analysis Dashboard</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Real-time analysis results with B-scoring, edge effect detection, and hit identification.
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-12">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light">{mockResults.totalWells}</div>
              <div className="text-sm text-muted-foreground">Total Wells</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light text-green-600">{mockResults.hits}</div>
              <div className="text-sm text-muted-foreground">Hits Found</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light">{mockResults.hitRate}%</div>
              <div className="text-sm text-muted-foreground">Hit Rate</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light">{mockResults.plateCount}</div>
              <div className="text-sm text-muted-foreground">Plates</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-light">{mockResults.processingTime}</div>
              <div className="text-sm text-muted-foreground">Process Time</div>
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
                  <Badge variant="outline">±2.5</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Viability Gate:</span>
                  <Badge variant="outline">0.3</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">B-Score Iterations:</span>
                  <Badge variant="outline">3</Badge>
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
                  <Badge variant="destructive">12</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Correction Applied:</span>
                  <Badge variant="secondary">Yes</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Warning Threshold:</span>
                  <Badge variant="outline">15%</Badge>
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