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

  const getStageWidth = (percentage: number) => {
    const minWidth = 20; // Minimum width percentage
    const maxWidth = 100; // Maximum width percentage
    return Math.max(minWidth, (percentage / 100) * maxWidth);
  };

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
          Flow shows compound filtering through biological evidence requirements
        </p>
      </CardHeader>
      <CardContent className="p-6">
        <div className="relative">
          {/* Funnel stages */}
          <div className="space-y-4">
            {stages.map((stage, index) => {
              const width = getStageWidth(stage.percentage);
              const previousStage = index > 0 ? stages[index - 1] : null;
              const retentionRate = previousStage ? getRetentionRate(stage.count, previousStage.count) : 100;
              
              return (
                <div key={stage.name} className="relative">
                  {/* Stage bar */}
                  <div className="flex items-center gap-4 mb-2">
                    <div 
                      className="relative h-16 rounded-lg flex items-center justify-center transition-all duration-300 hover:shadow-lg"
                      style={{ 
                        backgroundColor: stage.color,
                        width: `${width}%`,
                        minWidth: '200px'
                      }}
                    >
                      <div className="text-white font-semibold text-center">
                        <div className="text-xl">{stage.count}</div>
                        <div className="text-xs opacity-90">{stage.name}</div>
                      </div>
                    </div>
                    
                    {/* Stage info */}
                    <div className="flex-1 flex items-center gap-2">
                      <Badge variant="secondary">
                        {stage.percentage.toFixed(1)}%
                      </Badge>
                      {index > 0 && (
                        <Badge variant="outline">
                          {retentionRate.toFixed(1)}% retention
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {/* Connection arrow */}
                  {index < stages.length - 1 && (
                    <div className="flex items-center justify-center py-2">
                      <div className="w-0 h-0 border-l-[8px] border-r-[8px] border-t-[12px] border-l-transparent border-r-transparent border-t-muted-foreground/30"></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          
          {/* Summary stats */}
          <div className="mt-6 pt-4 border-t border-border">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-semibold text-blue-600">{stages[1].count}</div>
                <div className="text-xs text-muted-foreground">Reporter Hits</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-green-600">{stages[2].count}</div>
                <div className="text-xs text-muted-foreground">Vitality Hits</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-red-600">{stages[3].count}</div>
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