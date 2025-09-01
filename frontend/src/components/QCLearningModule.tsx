import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Eye, 
  Calculator,
  Target,
  Activity
} from 'lucide-react';
import ScientificTooltip from '@/components/ui/scientific-tooltip';

const QCLearningModule = () => {
  const [zFactorParams, setZFactorParams] = useState({
    positiveMean: 800,
    positiveStd: 50,
    negativeMean: 200,
    negativeStd: 30
  });

  const [selectedEdgePattern, setSelectedEdgePattern] = useState('none');

  // Calculate Z'-factor
  const calculateZPrime = () => {
    const { positiveMean, positiveStd, negativeMean, negativeStd } = zFactorParams;
    const zPrime = 1 - (3 * (positiveStd + negativeStd)) / Math.abs(positiveMean - negativeMean);
    return Math.max(0, Math.min(1, zPrime)).toFixed(3);
  };

  const getZPrimeQuality = (zPrime: number) => {
    if (zPrime >= 0.5) return { label: 'Excellent', color: 'bg-green-500', textColor: 'text-green-700' };
    if (zPrime >= 0.3) return { label: 'Acceptable', color: 'bg-yellow-500', textColor: 'text-yellow-700' };
    return { label: 'Poor', color: 'bg-red-500', textColor: 'text-red-700' };
  };

  const edgeEffectPatterns = [
    {
      id: 'none',
      name: 'No Edge Effects',
      description: 'Uniform signal across the plate',
      severity: 'None',
      color: 'bg-green-100 border-green-300',
      pattern: Array(8).fill(null).map(() => Array(12).fill(100))
    },
    {
      id: 'evaporation',
      name: 'Evaporation Edge Effect',
      description: 'Higher signals at plate edges due to evaporation',
      severity: 'Moderate',
      color: 'bg-orange-100 border-orange-300',
      pattern: Array(8).fill(null).map((_, row) => 
        Array(12).fill(null).map((_, col) => {
          const edgeDistance = Math.min(row, 7-row, col, 11-col);
          return 100 + (3 - edgeDistance) * 20;
        })
      )
    },
    {
      id: 'temperature',
      name: 'Temperature Gradient',
      description: 'Signal variation due to temperature differences',
      severity: 'High',
      color: 'bg-red-100 border-red-300',
      pattern: Array(8).fill(null).map((_, row) => 
        Array(12).fill(null).map((_, col) => {
          return 100 + (row - 3.5) * 15 + (col - 5.5) * 10;
        })
      )
    },
    {
      id: 'pipetting',
      name: 'Pipetting Bias',
      description: 'Systematic errors in reagent dispensing',
      severity: 'High',
      color: 'bg-purple-100 border-purple-300',
      pattern: Array(8).fill(null).map((_, row) => 
        Array(12).fill(null).map((_, col) => {
          const pattern = Math.sin(row * 0.8) * Math.cos(col * 0.6);
          return 100 + pattern * 40;
        })
      )
    }
  ];

  const robustStatsExample = [
    {
      method: 'Mean ± SD',
      values: [98, 102, 99, 101, 103, 97, 500], // outlier included
      result: '128.6 ± 151.2',
      interpretation: 'Heavily influenced by outlier (500)',
      reliable: false
    },
    {
      method: 'Median ± MAD',
      values: [98, 102, 99, 101, 103, 97, 500],
      result: '101.0 ± 4.4',
      interpretation: 'Resistant to outlier influence',
      reliable: true
    }
  ];

  const currentZPrime = parseFloat(calculateZPrime());
  const zPrimeQuality = getZPrimeQuality(currentZPrime);
  const selectedPattern = edgeEffectPatterns.find(p => p.id === selectedEdgePattern) || edgeEffectPatterns[0];

  return (
    <section className="py-16 bg-muted/20">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-light tracking-tight mb-4">
            Interactive Quality Control Learning
          </h2>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            Explore key quality control concepts through interactive simulations. 
            Understanding these metrics is essential for reliable hit identification in high-throughput screening.
          </p>
        </div>

        <Tabs defaultValue="z-factor" className="space-y-8">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="z-factor" className="flex items-center gap-2">
              <Calculator className="h-4 w-4" />
              Z'-Factor
            </TabsTrigger>
            <TabsTrigger value="edge-effects" className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Edge Effects
            </TabsTrigger>
            <TabsTrigger value="robust-stats" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Robust Statistics
            </TabsTrigger>
            <TabsTrigger value="spatial-bias" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              B-Scoring
            </TabsTrigger>
          </TabsList>

          {/* Z'-Factor Calculator */}
          <TabsContent value="z-factor" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-primary" />
                  Interactive <ScientificTooltip term="Z'-factor">Z'-Factor</ScientificTooltip> Calculator
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <label className="text-sm font-medium mb-3 block">
                        Positive Control Mean: {zFactorParams.positiveMean}
                      </label>
                      <Slider
                        value={[zFactorParams.positiveMean]}
                        onValueChange={(value) => setZFactorParams(prev => ({ ...prev, positiveMean: value[0] }))}
                        min={300}
                        max={1000}
                        step={10}
                        className="w-full"
                      />
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium mb-3 block">
                        Positive Control Std Dev: {zFactorParams.positiveStd}
                      </label>
                      <Slider
                        value={[zFactorParams.positiveStd]}
                        onValueChange={(value) => setZFactorParams(prev => ({ ...prev, positiveStd: value[0] }))}
                        min={10}
                        max={150}
                        step={5}
                        className="w-full"
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-3 block">
                        Negative Control Mean: {zFactorParams.negativeMean}
                      </label>
                      <Slider
                        value={[zFactorParams.negativeMean]}
                        onValueChange={(value) => setZFactorParams(prev => ({ ...prev, negativeMean: value[0] }))}
                        min={50}
                        max={400}
                        step={10}
                        className="w-full"
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium mb-3 block">
                        Negative Control Std Dev: {zFactorParams.negativeStd}
                      </label>
                      <Slider
                        value={[zFactorParams.negativeStd]}
                        onValueChange={(value) => setZFactorParams(prev => ({ ...prev, negativeStd: value[0] }))}
                        min={5}
                        max={100}
                        step={5}
                        className="w-full"
                      />
                    </div>
                  </div>

                  <div className="space-y-6">
                    <Card className={`p-6 text-center ${zPrimeQuality.color.replace('bg-', 'bg-opacity-10 border-')}`}>
                      <div className="text-4xl font-light text-primary mb-2">
                        {calculateZPrime()}
                      </div>
                      <div className={`text-lg font-medium mb-2 ${zPrimeQuality.textColor}`}>
                        {zPrimeQuality.label}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Z'-Factor Value
                      </div>
                    </Card>

                    <div className="bg-muted/30 p-4 rounded-lg">
                      <div className="text-sm font-medium mb-2">Formula:</div>
                      <div className="font-mono text-xs bg-background p-2 rounded border mb-3">
                        Z' = 1 - (3 × (σ_p + σ_n)) / |μ_p - μ_n|
                      </div>
                      <div className="text-xs text-muted-foreground space-y-1">
                        <div>σ_p, σ_n = Standard deviations of positive/negative controls</div>
                        <div>μ_p, μ_n = Means of positive/negative controls</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="text-center p-3 bg-green-50 rounded border">
                        <div className="font-medium text-green-800">≥0.5</div>
                        <div className="text-green-600">Excellent</div>
                      </div>
                      <div className="text-center p-3 bg-yellow-50 rounded border">
                        <div className="font-medium text-yellow-800">0.3-0.5</div>
                        <div className="text-yellow-600">Acceptable</div>
                      </div>
                      <div className="text-center p-3 bg-red-50 rounded border">
                        <div className="font-medium text-red-800">&lt;0.3</div>
                        <div className="text-red-600">Poor</div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Edge Effects Visualization */}
          <TabsContent value="edge-effects" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-primary" />
                  Edge Effect Pattern Recognition
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-3 block">Select Edge Effect Pattern:</label>
                      <div className="grid grid-cols-1 gap-3">
                        {edgeEffectPatterns.map((pattern) => (
                          <Button
                            key={pattern.id}
                            variant={selectedEdgePattern === pattern.id ? "default" : "outline"}
                            onClick={() => setSelectedEdgePattern(pattern.id)}
                            className="justify-start text-left h-auto p-4"
                          >
                            <div>
                              <div className="font-medium">{pattern.name}</div>
                              <div className="text-xs text-muted-foreground">{pattern.description}</div>
                              <Badge variant="outline" className="mt-1 text-xs">
                                {pattern.severity}
                              </Badge>
                            </div>
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <Card className={selectedPattern.color}>
                      <CardContent className="p-4">
                        <div className="text-center mb-4">
                          <div className="font-medium">{selectedPattern.name}</div>
                          <div className="text-sm text-muted-foreground">96-well Plate Simulation</div>
                        </div>
                        
                        {/* Simplified plate visualization */}
                        <div className="grid grid-cols-12 gap-0.5 max-w-xs mx-auto">
                          {selectedPattern.pattern.map((row, rowIndex) =>
                            row.map((value, colIndex) => (
                              <div
                                key={`${rowIndex}-${colIndex}`}
                                className="aspect-square rounded-sm"
                                style={{
                                  backgroundColor: `hsl(${Math.max(0, Math.min(120, (value - 50) * 2))}, 70%, ${Math.min(90, Math.max(20, value / 2))}%)`,
                                  border: '1px solid rgba(0,0,0,0.1)'
                                }}
                                title={`Well ${String.fromCharCode(65 + rowIndex)}${colIndex + 1}: ${Math.round(value)}`}
                              />
                            ))
                          )}
                        </div>

                        <div className="mt-4 text-center">
                          <div className="flex justify-center items-center gap-4 text-xs">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-red-400 rounded"></div>
                              <span>High</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-yellow-400 rounded"></div>
                              <span>Medium</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-green-400 rounded"></div>
                              <span>Low</span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <div className="bg-muted/30 p-4 rounded-lg">
                      <div className="text-sm font-medium mb-2">Impact on Analysis:</div>
                      <ul className="text-xs space-y-1 text-muted-foreground">
                        <li>• Edge effects create systematic bias in hit identification</li>
                        <li>• <ScientificTooltip term="B-scoring">B-scoring</ScientificTooltip> correction removes spatial artifacts</li>
                        <li>• <ScientificTooltip term="Moran's I">Spatial correlation analysis</ScientificTooltip> detects patterns</li>
                        <li>• Quality control flags problematic plates automatically</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Robust Statistics */}
          <TabsContent value="robust-stats" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Robust Statistics vs Traditional Methods
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-medium mb-3">Data Example (with outlier):</h4>
                      <div className="bg-muted/30 p-4 rounded border">
                        <div className="font-mono text-sm mb-2">
                          Values: [98, 102, 99, 101, 103, 97, <span className="text-red-500 font-bold">500</span>]
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Typical screening data with one extreme outlier (instrument error, dust, etc.)
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      {robustStatsExample.map((example, index) => (
                        <Card key={index} className={`border-l-4 ${example.reliable ? 'border-l-green-500 bg-green-50' : 'border-l-red-500 bg-red-50'}`}>
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between mb-2">
                              <div className="font-medium">{example.method}</div>
                              {example.reliable ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : (
                                <AlertTriangle className="h-4 w-4 text-red-500" />
                              )}
                            </div>
                            <div className="text-lg font-mono mb-2">{example.result}</div>
                            <div className="text-sm text-muted-foreground">{example.interpretation}</div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="bg-primary/10 p-4 rounded-lg border-l-4 border-l-primary">
                      <div className="font-medium mb-2">Why Robust Statistics?</div>
                      <ul className="text-sm text-muted-foreground space-y-2">
                        <li>• <strong>Outlier Resistance:</strong> Up to 50% contamination tolerance</li>
                        <li>• <strong>No Distribution Assumptions:</strong> Works with any data shape</li>
                        <li>• <strong>Screening-Optimized:</strong> Designed for HTS data characteristics</li>
                        <li>• <strong>Reproducible:</strong> Less sensitive to experimental variation</li>
                      </ul>
                    </div>

                    <div className="space-y-3">
                      <div className="text-center p-4 bg-background border rounded">
                        <div className="text-2xl font-light text-primary mb-1">3.2x</div>
                        <div className="text-sm font-medium">False Positive Reduction</div>
                        <div className="text-xs text-muted-foreground">vs traditional statistics</div>
                      </div>

                      <div className="text-center p-4 bg-background border rounded">
                        <div className="text-2xl font-light text-primary mb-1">85%</div>
                        <div className="text-sm font-medium">Hit Validation Success</div>
                        <div className="text-xs text-muted-foreground">in secondary assays</div>
                      </div>
                    </div>

                    <div className="bg-muted/30 p-4 rounded-lg">
                      <div className="text-sm font-medium mb-2">
                        <ScientificTooltip term="MAD">MAD</ScientificTooltip> Calculation:
                      </div>
                      <div className="font-mono text-xs bg-background p-2 rounded border mb-2">
                        MAD = 1.4826 × median(|x_i - median(x)|)
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Consistency factor (1.4826) makes MAD comparable to standard deviation for normal distributions
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* B-Scoring Explanation */}
          <TabsContent value="spatial-bias" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  <ScientificTooltip term="B-scoring">B-Scoring</ScientificTooltip> Spatial Bias Correction
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-medium mb-3">Median-Polish Algorithm:</h4>
                      <div className="space-y-3 text-sm">
                        <div className="flex items-start gap-3 p-3 bg-blue-50 rounded border">
                          <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-medium">1</div>
                          <div>
                            <div className="font-medium">Calculate row medians</div>
                            <div className="text-muted-foreground text-xs">Remove systematic row effects (e.g., pipetting bias)</div>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-green-50 rounded border">
                          <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-medium">2</div>
                          <div>
                            <div className="font-medium">Calculate column medians</div>
                            <div className="text-muted-foreground text-xs">Remove systematic column effects (e.g., temperature gradient)</div>
                          </div>
                        </div>

                        <div className="flex items-start gap-3 p-3 bg-orange-50 rounded border">
                          <div className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-medium">3</div>
                          <div>
                            <div className="font-medium">Apply median polish</div>
                            <div className="text-muted-foreground text-xs">Iteratively remove additive row and column effects</div>
                          </div>
                        </div>

                        <div className="flex items-start gap-3 p-3 bg-purple-50 rounded border">
                          <div className="w-6 h-6 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs font-medium">4</div>
                          <div>
                            <div className="font-medium">Scale by <ScientificTooltip term="MAD">MAD</ScientificTooltip></div>
                            <div className="text-muted-foreground text-xs">Robust scaling using median absolute deviation</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-muted/30 p-4 rounded-lg">
                      <div className="font-medium mb-2">B-Score Formula:</div>
                      <div className="font-mono text-xs bg-background p-2 rounded border mb-2">
                        B = (value - r_med - c_med + p_med) / MAD
                      </div>
                      <div className="text-xs text-muted-foreground space-y-1">
                        <div>r_med = row median, c_med = column median</div>
                        <div>p_med = plate median, MAD = median absolute deviation</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h4 className="font-medium mb-3">Before vs After Correction:</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center">
                          <div className="text-sm font-medium mb-2">Raw Z-Scores</div>
                          <div className="w-full aspect-square bg-gradient-to-br from-red-200 via-yellow-200 to-red-300 rounded border mb-2"></div>
                          <div className="text-xs text-muted-foreground">Spatial artifacts visible</div>
                        </div>
                        
                        <div className="text-center">
                          <div className="text-sm font-medium mb-2">B-Scores</div>
                          <div className="w-full aspect-square bg-gradient-to-br from-green-100 via-white to-green-100 rounded border mb-2"></div>
                          <div className="text-xs text-muted-foreground">Artifacts corrected</div>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-center">
                      <Card className="p-4 border-l-4 border-l-red-500">
                        <div className="text-2xl font-light text-red-600 mb-1">23%</div>
                        <div className="text-sm font-medium">False Positives</div>
                        <div className="text-xs text-muted-foreground">Without B-scoring</div>
                      </Card>
                      
                      <Card className="p-4 border-l-4 border-l-green-500">
                        <div className="text-2xl font-light text-green-600 mb-1">7%</div>
                        <div className="text-sm font-medium">False Positives</div>
                        <div className="text-xs text-muted-foreground">With B-scoring</div>
                      </Card>
                    </div>

                    <div className="bg-primary/10 p-4 rounded-lg border-l-4 border-l-primary">
                      <div className="font-medium mb-2">When to Apply B-Scoring:</div>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Visual inspection shows spatial patterns</li>
                        <li>• <ScientificTooltip term="Moran's I">Moran's I</ScientificTooltip> statistic indicates clustering</li>
                        <li>• Edge effects detected in QC analysis</li>
                        <li>• Row/column systematic bias apparent</li>
                        <li>• Standard practice for all 384+ well plates</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
};

export default QCLearningModule;