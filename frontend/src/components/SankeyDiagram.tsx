import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AnalysisResult } from '@/types/analysis';
import Plot from 'react-plotly.js';

interface SankeyDiagramProps {
  analysisData: AnalysisResult;
}

const SankeyDiagram = ({ analysisData }: SankeyDiagramProps) => {
  // Extract counts from analysis data
  const totalWells = analysisData.total_wells;
  const reporterHits = analysisData.summary?.stage1_reporter_hits || 0;
  const vitalityHits = analysisData.summary?.stage2_vitality_hits || 0;
  const platformHits = analysisData.summary?.stage3_platform_hits || 0;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-lg font-semibold">OM Permeabilizer Discovery Pipeline</span>
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Sankey flow diagram showing compound filtering through biological evidence requirements
        </p>
      </CardHeader>
      <CardContent className="p-6">
        <div className="h-96 w-full mb-6">
          <Plot
            data={[
              {
                type: 'sankey',
                node: {
                  pad: 15,
                  thickness: 20,
                  line: { color: 'black', width: 0.5 },
                  label: [
                    `Total Wells<br>(${totalWells})`,
                    `Reporter Hits<br>(${reporterHits})`,
                    `Vitality Hits<br>(${vitalityHits})`,
                    `Platform Hits<br>(${platformHits})`
                  ],
                  color: ['#64748B', '#3B82F6', '#8B5CF6', '#10B981']
                },
                link: {
                  source: [0, 0, 1, 2],
                  target: [1, 2, 3, 3],
                  value: [reporterHits, vitalityHits, platformHits, platformHits],
                  color: [
                    'rgba(59, 130, 246, 0.6)',   // blue flow to reporter
                    'rgba(139, 92, 246, 0.6)',   // purple flow to vitality  
                    'rgba(16, 185, 129, 0.8)',   // green flow to platform hits
                    'rgba(16, 185, 129, 0.8)'    // green flow to platform hits
                  ]
                }
              }
            ]}
            layout={{
              title: '',
              height: 400,
              margin: { l: 50, r: 50, t: 20, b: 20 },
              font: { size: 12 }
            }}
            config={{ 
              displayModeBar: false,
              responsive: true
            }}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
        
        {/* Summary statistics matching overview colors */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">{reporterHits}</div>
            <div className="text-xs text-muted-foreground">Reporter Hits</div>
            <Badge variant="secondary" className="text-xs mt-1">
              {((reporterHits / totalWells) * 100).toFixed(1)}%
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">{vitalityHits}</div>
            <div className="text-xs text-muted-foreground">Vitality Hits</div>
            <Badge variant="secondary" className="text-xs mt-1">
              {((vitalityHits / totalWells) * 100).toFixed(1)}%
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">{platformHits}</div>
            <div className="text-xs text-muted-foreground">Platform Hits</div>
            <Badge variant="secondary" className="text-xs mt-1">
              {((platformHits / totalWells) * 100).toFixed(1)}%
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-600">
              {platformHits > 0 ? `${((platformHits / totalWells) * 100).toFixed(2)}%` : '0%'}
            </div>
            <div className="text-xs text-muted-foreground">Success Rate</div>
            <Badge variant="outline" className="text-xs mt-1">
              Final Pipeline
            </Badge>
          </div>
        </div>
        
        {/* Methodology note */}
        <div className="mt-4 p-3 bg-muted/50 rounded-lg">
          <p className="text-xs text-muted-foreground">
            <strong>Flow Logic:</strong> Total wells are filtered through independent reporter and vitality screens. 
            Platform hits represent compounds that meet both criteria, indicating outer membrane permeabilization activity.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default SankeyDiagram;