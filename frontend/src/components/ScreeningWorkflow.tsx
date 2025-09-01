import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, FlaskConical, BarChart3, Target, CheckCircle } from 'lucide-react';
import ScientificTooltip from '@/components/ui/scientific-tooltip';

const ScreeningWorkflow = () => {
  const stages = [
    {
      id: 1,
      title: "Reporter Screen",
      subtitle: "Envelope Stress Detection",
      icon: FlaskConical,
      description: "Dual-reporter system detects outer membrane disruption through stress response activation",
      criteria: [
        "lptA Z-score ≥ 2.0 (LPS transport stress)",
        "ldtD Z-score ≥ 2.0 (peptidoglycan stress)",
        "ATP-based viability gating (BT > 0.3 × median)"
      ],
      hitRate: "~8%",
      hitCount: "70/880",
      biology: "Compounds triggering envelope stress pathways",
      color: "bg-blue-500",
      borderColor: "border-l-blue-500"
    },
    {
      id: 2,
      title: "Vitality Screen", 
      subtitle: "Selectivity Profiling",
      icon: BarChart3,
      description: "Three-strain growth analysis confirms outer membrane-specific activity patterns",
      criteria: [
        "E. coli WT: >80% growth (protected by intact OM)",
        "E. coli ΔtolC: ≤80% growth (sensitized strain)",
        "S. aureus: >80% growth (no OM target)"
      ],
      hitRate: "~6.5%",
      hitCount: "57/880", 
      biology: "OM-selective compounds with therapeutic windows",
      color: "bg-orange-500",
      borderColor: "border-l-orange-500"
    },
    {
      id: 3,
      title: "Platform Hits",
      subtitle: "Dual Validation",
      icon: Target,
      description: "Compounds satisfying both reporter activation and vitality criteria",
      criteria: [
        "Pass Stage 1: Reporter activation (lptA OR ldtD)",
        "Pass Stage 2: Selective growth inhibition pattern", 
        "Cross-validated: Independent evidence of OM activity"
      ],
      hitRate: "~1%",
      hitCount: "9/880",
      biology: "High-confidence OM permeabilizers for development",
      color: "bg-green-500",
      borderColor: "border-l-green-500"
    }
  ];

  const qualityMetrics = [
    {
      metric: "Z'-Factor",
      value: "≥0.5",
      description: "Excellent assay performance",
      tooltip: "Z'-factor"
    },
    {
      metric: "Edge Effects",
      value: "<5%",
      description: "Spatial artifact control",
      tooltip: "Moran's I"
    },
    {
      metric: "False Positive Rate",
      value: "<0.1%",
      description: "High-confidence hits",
      tooltip: "B-scoring"
    },
    {
      metric: "Reproducibility",
      value: ">90%",
      description: "Cross-plate validation",
      tooltip: "MAD"
    }
  ];

  return (
    <section className="py-16">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-light tracking-tight mb-4">
            Three-Stage Screening Workflow
          </h2>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            Multi-dimensional hit calling pipeline combines biological reporters with strain selectivity 
            profiling to identify <strong>outer membrane permeabilizers</strong> with high confidence and low false positive rates.
          </p>
        </div>

        {/* Main Workflow */}
        <div className="relative mb-16">
          {/* Desktop Flow */}
          <div className="hidden md:flex items-center justify-center gap-8">
            {stages.map((stage, index) => {
              const IconComponent = stage.icon;
              return (
                <React.Fragment key={stage.id}>
                  <Card className={`w-80 ${stage.borderColor} border-l-4 hover:shadow-lg transition-shadow`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className={`w-12 h-12 ${stage.color} rounded-full flex items-center justify-center text-white`}>
                          <IconComponent className="h-6 w-6" />
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          Stage {stage.id}
                        </Badge>
                      </div>
                      <CardTitle className="text-lg">{stage.title}</CardTitle>
                      <p className="text-sm text-muted-foreground">{stage.subtitle}</p>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4">
                        {stage.description}
                      </p>
                      
                      <div className="space-y-3">
                        <div>
                          <div className="text-xs font-medium text-foreground mb-2">Criteria:</div>
                          <ul className="text-xs space-y-1 text-muted-foreground">
                            {stage.criteria.map((criterion, idx) => (
                              <li key={idx} className="flex items-start gap-2">
                                <div className="w-1 h-1 rounded-full bg-primary mt-2 flex-shrink-0"></div>
                                {criterion}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="flex items-center justify-between pt-3 border-t">
                          <div>
                            <div className="text-lg font-light text-primary">{stage.hitRate}</div>
                            <div className="text-xs text-muted-foreground">Hit Rate</div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium text-foreground">{stage.hitCount}</div>
                            <div className="text-xs text-muted-foreground">Extracts</div>
                          </div>
                        </div>

                        <div className="bg-muted/30 p-3 rounded text-xs">
                          <div className="font-medium mb-1">Biology:</div>
                          <div className="text-muted-foreground">{stage.biology}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {index < stages.length - 1 && (
                    <div className="flex flex-col items-center">
                      <ArrowRight className="h-8 w-8 text-muted-foreground" />
                      <div className="text-xs text-muted-foreground mt-2">AND</div>
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Mobile Flow */}
          <div className="md:hidden space-y-6">
            {stages.map((stage, index) => {
              const IconComponent = stage.icon;
              return (
                <div key={stage.id} className="relative">
                  <Card className={`${stage.borderColor} border-l-4`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className={`w-10 h-10 ${stage.color} rounded-full flex items-center justify-center text-white`}>
                          <IconComponent className="h-5 w-5" />
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          Stage {stage.id} • {stage.hitRate}
                        </Badge>
                      </div>
                      <CardTitle className="text-lg">{stage.title}</CardTitle>
                      <p className="text-sm text-muted-foreground">{stage.description}</p>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xs text-muted-foreground">
                        {stage.biology}
                      </div>
                    </CardContent>
                  </Card>
                  
                  {index < stages.length - 1 && (
                    <div className="flex justify-center my-4">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <div className="w-px h-6 bg-border"></div>
                        <ArrowRight className="h-4 w-4" />
                        <div className="text-xs">AND</div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Quality Control Metrics */}
        <div className="bg-muted/30 rounded-lg border p-8">
          <div className="text-center mb-8">
            <h3 className="text-xl font-medium mb-2 flex items-center justify-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Quality Control Framework
            </h3>
            <p className="text-sm text-muted-foreground">
              Multi-dimensional quality assessment ensures reliable hit identification and minimizes false positives
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {qualityMetrics.map((qc, index) => (
              <Card key={index} className="text-center">
                <CardContent className="p-4">
                  <div className="text-2xl font-light text-primary mb-2">
                    {qc.value}
                  </div>
                  <div className="text-sm font-medium text-foreground mb-1">
                    <ScientificTooltip term={qc.tooltip}>
                      {qc.metric}
                    </ScientificTooltip>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {qc.description}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-8 text-center">
            <div className="inline-flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                Reporter Screening
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                Vitality Profiling
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Platform Validation
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ScreeningWorkflow;