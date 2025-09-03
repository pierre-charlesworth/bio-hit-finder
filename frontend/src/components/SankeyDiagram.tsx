import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AnalysisResult } from '@/types/analysis';
import { Sankey, ResponsiveContainer, Tooltip } from 'recharts';

interface SankeyNode {
  name: string;
  id: number;
}

interface SankeyLink {
  source: number;
  target: number;
  value: number;
  color?: string;
}

interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

interface SankeyDiagramProps {
  analysisData: AnalysisResult;
}

const SankeyDiagram = ({ analysisData }: SankeyDiagramProps) => {
  // Extract counts from analysis data
  const totalWells = analysisData.total_wells;
  const reporterHits = analysisData.summary?.stage1_reporter_hits || 0;
  const vitalityHits = analysisData.summary?.stage2_vitality_hits || 0;
  const platformHits = analysisData.summary?.stage3_platform_hits || 0;

  // Create Sankey data structure
  const sankeyData: SankeyData = {
    nodes: [
      { name: `Total Wells (${totalWells})`, id: 0 },
      { name: `Reporter Hits (${reporterHits})`, id: 1 },
      { name: `Vitality Hits (${vitalityHits})`, id: 2 },
      { name: `Platform Hits (${platformHits})`, id: 3 }
    ],
    links: [
      {
        source: 0,
        target: 1,
        value: reporterHits,
        color: 'rgba(59, 130, 246, 0.6)' // blue
      },
      {
        source: 0,
        target: 2,
        value: vitalityHits,
        color: 'rgba(16, 185, 129, 0.6)' // green
      },
      {
        source: 1,
        target: 3,
        value: platformHits,
        color: 'rgba(239, 68, 68, 0.8)' // red - final hits
      },
      {
        source: 2,
        target: 3,
        value: platformHits,
        color: 'rgba(239, 68, 68, 0.8)' // red - final hits
      }
    ]
  };

  // Custom tooltip component
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload?.length) return null;
    
    const data = payload[0];
    if (data.payload.source !== undefined) {
      // This is a link
      const sourceNode = sankeyData.nodes[data.payload.source];
      const targetNode = sankeyData.nodes[data.payload.target];
      return (
        <div className="bg-white p-3 border border-border rounded shadow-lg">
          <p className="font-medium">{`${sourceNode.name} → ${targetNode.name}`}</p>
          <p className="text-sm text-muted-foreground">{`${data.payload.value} compounds`}</p>
        </div>
      );
    }
    return null;
  };

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
        <div className="h-80 w-full mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <Sankey
              data={sankeyData}
              nodePadding={10}
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
              <Tooltip content={<CustomTooltip />} />
            </Sankey>
          </ResponsiveContainer>
        </div>
        
        {/* Summary statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">{reporterHits}</div>
            <div className="text-xs text-muted-foreground">Reporter Hits</div>
            <Badge variant="secondary" className="text-xs mt-1">
              {((reporterHits / totalWells) * 100).toFixed(1)}%
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">{vitalityHits}</div>
            <div className="text-xs text-muted-foreground">Vitality Hits</div>
            <Badge variant="secondary" className="text-xs mt-1">
              {((vitalityHits / totalWells) * 100).toFixed(1)}%
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-red-600">{platformHits}</div>
            <div className="text-xs text-muted-foreground">Platform Hits</div>
            <Badge variant="secondary" className="text-xs mt-1">
              {((platformHits / totalWells) * 100).toFixed(1)}%
            </Badge>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">
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