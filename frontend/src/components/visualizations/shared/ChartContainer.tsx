import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Info, Download, Expand, Minimize } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface ChartContainerProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  
  // Status and feedback
  loading?: boolean;
  error?: string | null;
  warnings?: string[];
  
  // Metadata and statistics  
  dataCount?: number;
  lastUpdated?: Date;
  processingTime?: number;
  
  // Interactive features
  onExport?: (format: 'png' | 'svg' | 'pdf') => void;
  onExpand?: () => void;
  expandable?: boolean;
  
  // Styling
  className?: string;
  height?: number;
  showMetadata?: boolean;
  
  // Scientific context
  methodology?: string;
  interpretation?: string;
  references?: string[];
}

/**
 * Standardized container for scientific visualizations with metadata, 
 * error handling, and export capabilities
 */
const ChartContainer = ({
  title,
  description,
  children,
  loading = false,
  error = null,
  warnings = [],
  dataCount,
  lastUpdated,
  processingTime,
  onExport,
  onExpand,
  expandable = false,
  className = '',
  height,
  showMetadata = true,
  methodology,
  interpretation,
  references = []
}: ChartContainerProps) => {
  
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const handleExpand = () => {
    if (onExpand) {
      onExpand();
    } else {
      setIsExpanded(!isExpanded);
    }
  };

  const handleExport = (format: 'png' | 'svg' | 'pdf') => {
    if (onExport) {
      onExport(format);
    }
  };

  return (
    <Card className={cn(
      'w-full transition-all duration-200',
      isExpanded && 'fixed inset-4 z-50 shadow-2xl',
      className
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2 text-lg">
              {title}
              
              {/* Data count badge */}
              {dataCount !== undefined && (
                <Badge variant="secondary" className="text-xs">
                  {dataCount.toLocaleString()} wells
                </Badge>
              )}
              
              {/* Warning indicator */}
              {warnings.length > 0 && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  {warnings.length} warning{warnings.length > 1 ? 's' : ''}
                </Badge>
              )}
            </CardTitle>
            
            {description && (
              <CardDescription className="mt-1">
                {description}
              </CardDescription>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1 ml-4">
            {/* Metadata toggle */}
            {showMetadata && (dataCount !== undefined || lastUpdated || methodology) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
                className="text-xs"
              >
                <Info className="h-3 w-3" />
              </Button>
            )}

            {/* Export dropdown */}
            {onExport && (
              <div className="relative group">
                <Button variant="ghost" size="sm" className="text-xs">
                  <Download className="h-3 w-3" />
                </Button>
                <div className="absolute right-0 top-full mt-1 hidden group-hover:block z-10">
                  <div className="bg-white border border-border rounded shadow-lg py-1 min-w-24">
                    <button
                      onClick={() => handleExport('png')}
                      className="block w-full px-3 py-1 text-xs text-left hover:bg-gray-50"
                    >
                      PNG
                    </button>
                    <button
                      onClick={() => handleExport('svg')}
                      className="block w-full px-3 py-1 text-xs text-left hover:bg-gray-50"
                    >
                      SVG
                    </button>
                    <button
                      onClick={() => handleExport('pdf')}
                      className="block w-full px-3 py-1 text-xs text-left hover:bg-gray-50"
                    >
                      PDF
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Expand/minimize button */}
            {expandable && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleExpand}
                className="text-xs"
              >
                {isExpanded ? (
                  <Minimize className="h-3 w-3" />
                ) : (
                  <Expand className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>
        </div>

        {/* Metadata panel */}
        {showDetails && showMetadata && (
          <div className="mt-3 p-3 bg-muted/20 rounded-lg border">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              {dataCount !== undefined && (
                <div>
                  <div className="font-medium text-muted-foreground">Data Points</div>
                  <div>{dataCount.toLocaleString()}</div>
                </div>
              )}
              
              {lastUpdated && (
                <div>
                  <div className="font-medium text-muted-foreground">Updated</div>
                  <div>{lastUpdated.toLocaleTimeString()}</div>
                </div>
              )}
              
              {processingTime !== undefined && (
                <div>
                  <div className="font-medium text-muted-foreground">Processing</div>
                  <div>{processingTime}ms</div>
                </div>
              )}
              
              {methodology && (
                <div className="col-span-2 md:col-span-1">
                  <div className="font-medium text-muted-foreground">Method</div>
                  <div>{methodology}</div>
                </div>
              )}
            </div>

            {/* Warnings */}
            {warnings.length > 0 && (
              <div className="mt-3 pt-3 border-t border-border">
                <div className="font-medium text-muted-foreground text-xs mb-1">
                  Data Quality Warnings:
                </div>
                <div className="space-y-1">
                  {warnings.map((warning, index) => (
                    <div key={index} className="flex items-start gap-2 text-xs text-amber-700">
                      <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                      <span>{warning}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Scientific interpretation */}
            {interpretation && (
              <div className="mt-3 pt-3 border-t border-border">
                <div className="font-medium text-muted-foreground text-xs mb-1">
                  Scientific Interpretation:
                </div>
                <div className="text-xs text-gray-700">{interpretation}</div>
              </div>
            )}

            {/* References */}
            {references.length > 0 && (
              <div className="mt-3 pt-3 border-t border-border">
                <div className="font-medium text-muted-foreground text-xs mb-1">
                  References:
                </div>
                <div className="space-y-1">
                  {references.map((ref, index) => (
                    <div key={index} className="text-xs text-gray-600">
                      {index + 1}. {ref}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        <div 
          className="w-full"
          style={{ 
            height: height || (isExpanded ? 'calc(100vh - 200px)' : '400px'),
            minHeight: '300px'
          }}
        >
          {children}
        </div>
      </CardContent>
    </Card>
  );
};

export default ChartContainer;