import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { TrendingDown, Info } from 'lucide-react';

interface FunnelStage {
  label: string;
  count: number;
  color: string;
  percentage?: number;
  description?: string;
}

interface FunnelDiagramEnhancedProps {
  title: string;
  stages: FunnelStage[];
  className?: string;
  showMiniChart?: boolean;
  showDropoffRates?: boolean;
}

const FunnelDiagramEnhanced: React.FC<FunnelDiagramEnhancedProps> = ({ 
  title, 
  stages, 
  className = "",
  showMiniChart = true,
  showDropoffRates = true
}) => {
  // Calculate percentages and dropoff rates
  const processedStages = useMemo(() => {
    const baseCount = stages[0]?.count || 1;
    
    return stages.map((stage, index) => {
      const percentage = (stage.count / baseCount) * 100;
      const previousCount = index > 0 ? stages[index - 1].count : stage.count;
      const dropoffRate = index > 0 
        ? ((previousCount - stage.count) / previousCount) * 100 
        : 0;
      
      return {
        ...stage,
        percentage,
        dropoffRate,
        retained: index > 0 ? ((stage.count / previousCount) * 100) : 100
      };
    });
  }, [stages]);

  // Data for mini bar chart
  const chartData = processedStages.map(stage => ({
    name: stage.label,
    count: stage.count,
    percentage: stage.percentage
  }));

  const chartConfig = {
    count: {
      label: "Count",
      color: "#3b82f6",
    },
  };

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {/* Main Funnel Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="text-center flex items-center justify-center gap-2">
            <TrendingDown className="h-5 w-5" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {processedStages.map((stage, index) => {
              // Calculate responsive width (wider containers get more dramatic funnel effect)
              const maxWidth = 100;
              const minWidth = 25;
              const width = Math.max(minWidth, (stage.percentage / 100) * maxWidth);

              return (
                <div key={stage.label} className="relative">
                  {/* Stage Container */}
                  <div 
                    className="mx-auto transition-all duration-500 hover:scale-[1.02]"
                    style={{ width: `${width}%` }}
                  >
                    {/* Main Stage Bar */}
                    <div 
                      className="relative h-20 rounded-xl flex items-center justify-between px-6 shadow-lg border border-white/20 backdrop-blur-sm"
                      style={{ 
                        backgroundColor: stage.color,
                        background: `linear-gradient(135deg, ${stage.color} 0%, ${stage.color}cc 100%)`
                      }}
                    >
                      {/* Left Side - Numbers */}
                      <div className="text-white">
                        <div className="text-2xl font-bold">{stage.count.toLocaleString()}</div>
                        <div className="text-sm opacity-90">{stage.label}</div>
                      </div>

                      {/* Right Side - Percentage */}
                      <div className="text-right text-white">
                        <div className="text-xl font-semibold">{stage.percentage.toFixed(1)}%</div>
                        {index > 0 && showDropoffRates && (
                          <div className="text-xs opacity-90">
                            -{stage.dropoffRate.toFixed(1)}% lost
                          </div>
                        )}
                      </div>

                      {/* Stage Description Tooltip */}
                      {stage.description && (
                        <Button
                          variant="ghost" 
                          size="sm"
                          className="absolute -top-2 -right-2 h-6 w-6 p-0 bg-white/20 hover:bg-white/30 text-white border-white/30"
                        >
                          <Info className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Connecting Flow */}
                  {index < processedStages.length - 1 && (
                    <div className="flex justify-center py-3">
                      <div className="relative">
                        {/* Animated Flow Lines */}
                        <svg 
                          width="120" 
                          height="32" 
                          className="overflow-visible"
                          viewBox="0 0 120 32"
                        >
                          {/* Background flow shape */}
                          <path
                            d="M 20 4 L 100 4 L 85 28 L 35 28 Z"
                            fill="rgb(241, 245, 249)"
                            className="opacity-40"
                          />
                          
                          {/* Center flow arrow */}
                          <polygon
                            points="55,12 65,12 60,20"
                            fill={stage.color}
                            className="opacity-70"
                          />
                          
                          {/* Flow percentage text */}
                          <text
                            x="60"
                            y="8"
                            textAnchor="middle"
                            className="text-xs fill-gray-600"
                            fontSize="10"
                          >
                            {processedStages[index + 1]?.retained.toFixed(0)}%
                          </text>
                        </svg>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Analytics Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Summary Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Pipeline Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm font-medium">Overall Conversion</span>
                <Badge variant="outline" className="text-lg px-3 py-1">
                  {stages.length > 1 
                    ? ((stages[stages.length - 1].count / stages[0].count) * 100).toFixed(2)
                    : 0}%
                </Badge>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm font-medium">Total Filtered</span>
                <Badge variant="secondary" className="px-3 py-1">
                  {stages.length > 1 
                    ? (stages[0].count - stages[stages.length - 1].count).toLocaleString()
                    : 0}
                </Badge>
              </div>

              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm font-medium">Pipeline Efficiency</span>
                <Badge 
                  variant={
                    stages.length > 1 && ((stages[stages.length - 1].count / stages[0].count) * 100) > 5 
                      ? "default" 
                      : "destructive"
                  }
                  className="px-3 py-1"
                >
                  {stages.length > 1 
                    ? ((stages[stages.length - 1].count / stages[0].count) * 100) > 5 ? 'Good' : 'Low'
                    : 'N/A'}
                </Badge>
              </div>

              <div className="flex justify-between items-center py-2">
                <span className="text-sm font-medium">Final Success Rate</span>
                <Badge variant="outline" className="px-3 py-1">
                  1 in {stages.length > 1 ? Math.round(stages[0].count / stages[stages.length - 1].count) : 1}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Mini Bar Chart */}
        {showMiniChart && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Stage Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={chartConfig} className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <XAxis 
                      dataKey="name" 
                      tick={{ fontSize: 10 }} 
                      interval={0}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fontSize: 10 }} />
                    <ChartTooltip 
                      content={<ChartTooltipContent />}
                      formatter={(value, name) => [
                        typeof value === 'number' ? value.toLocaleString() : value, 
                        'Count'
                      ]}
                    />
                    <Bar 
                      dataKey="count" 
                      fill="#3b82f6"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default FunnelDiagramEnhanced;