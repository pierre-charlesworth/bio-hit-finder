import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface FunnelStage {
  label: string;
  count: number;
  color?: string;
}

interface SimpleFunnelProps {
  title?: string;
  stages: FunnelStage[];
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

const SimpleFunnel: React.FC<SimpleFunnelProps> = ({ 
  title,
  stages, 
  orientation = 'horizontal',
  className = "" 
}) => {
  const maxCount = stages[0]?.count || 1;
  
  if (orientation === 'vertical') {
    return (
      <Card className={className}>
        {title && (
          <CardHeader>
            <CardTitle className="text-center">{title}</CardTitle>
          </CardHeader>
        )}
        <CardContent>
          <div className="space-y-4">
            {stages.map((stage, index) => {
              const percentage = (stage.count / maxCount) * 100;
              const width = Math.max(20, percentage);
              
              return (
                <div key={stage.label} className="text-center">
                  <div 
                    className={`mx-auto h-12 rounded-lg flex items-center justify-center text-white font-medium transition-all duration-300 hover:shadow-lg`}
                    style={{ 
                      width: `${width}%`,
                      backgroundColor: stage.color || '#3b82f6',
                      minWidth: '120px'
                    }}
                  >
                    <span className="text-sm">
                      {stage.count} {stage.label}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {percentage.toFixed(1)}%
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Horizontal orientation (default)
  return (
    <Card className={className}>
      {title && (
        <CardHeader>
          <CardTitle className="text-center">{title}</CardTitle>
        </CardHeader>
      )}
      <CardContent>
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-2">
          {stages.map((stage, index) => {
            const percentage = (stage.count / maxCount) * 100;
            
            return (
              <React.Fragment key={stage.label}>
                <div className="flex-shrink-0 text-center min-w-[100px]">
                  <div 
                    className="h-16 w-full rounded-lg flex flex-col items-center justify-center text-white font-medium shadow-md transition-all duration-300 hover:shadow-lg"
                    style={{ backgroundColor: stage.color || '#3b82f6' }}
                  >
                    <div className="text-lg font-bold">{stage.count}</div>
                    <div className="text-xs opacity-90">{stage.label}</div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {percentage.toFixed(1)}%
                  </div>
                </div>
                
                {index < stages.length - 1 && (
                  <div className="flex-shrink-0 px-2">
                    <div className="w-8 h-0.5 bg-gradient-to-r from-gray-300 to-gray-400 relative">
                      <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-gray-400 rotate-45"></div>
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
        
        {/* Summary */}
        <div className="mt-4 pt-4 border-t text-center">
          <div className="text-sm text-muted-foreground">
            Overall conversion: <span className="font-semibold text-foreground">
              {stages.length > 1 
                ? ((stages[stages.length - 1].count / stages[0].count) * 100).toFixed(1)
                : 0}%
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SimpleFunnel;