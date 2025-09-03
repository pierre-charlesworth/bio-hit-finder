import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AnalysisResult } from '@/types/analysis';

interface FunnelStage {
  name: string;
  count: number;
  percentage: number;
  color: string;
}

interface FunnelDiagramProps {
  analysisData: AnalysisResult;
}

const FunnelDiagram = ({ analysisData }: FunnelDiagramProps) => {
  const stages: FunnelStage[] = [
    {
      name: "Total Wells",
      count: analysisData.total_wells,
      percentage: 100,
      color: "#3B82F6" // blue
    },
    {
      name: "Reporter Hits", 
      count: analysisData.summary?.stage1_reporter_hits || 0,
      percentage: ((analysisData.summary?.stage1_reporter_hits || 0) / analysisData.total_wells * 100),
      color: "#F59E0B" // orange
    },
    {
      name: "Vitality Hits",
      count: analysisData.summary?.stage2_vitality_hits || 0, 
      percentage: ((analysisData.summary?.stage2_vitality_hits || 0) / analysisData.total_wells * 100),
      color: "#10B981" // green
    },
    {
      name: "Platform Hits",
      count: analysisData.summary?.stage3_platform_hits || 0,
      percentage: ((analysisData.summary?.stage3_platform_hits || 0) / analysisData.total_wells * 100),
      color: "#EF4444" // red
    }
  ];

  const getRetentionRate = (currentStage: number, previousStage: number) => {
    if (previousStage === 0) return 0;
    return (currentStage / previousStage * 100);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-lg font-semibold">OM Permeabilizer Discovery Pipeline</span>
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Funnel shows compound filtering through biological evidence requirements
        </p>
      </CardHeader>
      <CardContent className="p-6">
        <div className="relative flex flex-col items-center">
          {/* Funnel stages */}
          <div className="space-y-1 w-full max-w-md">
            {stages.map((stage, index) => {
              // Calculate funnel width based on percentage (narrowing down)
              const funnelWidth = Math.max(30, stage.percentage); // Minimum 30% for visibility
              const previousStage = index > 0 ? stages[index - 1] : null;
              const retentionRate = previousStage ? getRetentionRate(stage.count, previousStage.count) : 100;
              
              return (
                <div key={stage.name} className="relative flex flex-col items-center">
                  {/* Funnel segment */}
                  <div className="relative group">
                    <div 
                      className="h-16 flex items-center justify-center transition-all duration-300 hover:brightness-110 relative"
                      style={{ 
                        backgroundColor: stage.color,
                        width: `${funnelWidth}%`,
                        clipPath: index === 0 
                          ? 'polygon(0% 0%, 100% 0%, 85% 100%, 15% 100%)'  // Top trapezoid
                          : index === stages.length - 1 
                          ? 'polygon(15% 0%, 85% 0%, 50% 100%, 50% 100%)'   // Bottom triangle
                          : 'polygon(15% 0%, 85% 0%, 70% 100%, 30% 100%)'   // Middle trapezoids
                      }}
                    >
                      <div className="text-white font-semibold text-center relative z-10">
                        <div className="text-lg font-bold">{stage.count}</div>
                        <div className="text-xs opacity-90 font-medium">{stage.name}</div>
                      </div>
                    </div>
                    
                    {/* Hover tooltip */}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20">
                      {stage.percentage.toFixed(1)}% of total
                      {index > 0 && ` (${retentionRate.toFixed(1)}% retention)`}
                    </div>
                  </div>
                  
                  {/* Stats beside funnel */}
                  <div className="flex items-center gap-2 mt-1 mb-2">
                    <Badge variant="secondary" className="text-xs">
                      {stage.percentage.toFixed(1)}%
                    </Badge>
                    {index > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {retentionRate.toFixed(1)}% kept
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Summary stats */}
          <div className="mt-8 pt-4 border-t border-border w-full">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-semibold text-blue-600">{stages[1].count}</div>
                <div className="text-xs text-muted-foreground">Reporter Hits</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-orange-600">{stages[2].count}</div>
                <div className="text-xs text-muted-foreground">Vitality Hits</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-green-600">{stages[3].count}</div>
                <div className="text-xs text-muted-foreground">Platform Hits</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-purple-600">
                  {stages[3].count > 0 ? `${((stages[3].count / stages[0].count) * 100).toFixed(2)}%` : '0%'}
                </div>
                <div className="text-xs text-muted-foreground">Overall Success Rate</div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default FunnelDiagram;