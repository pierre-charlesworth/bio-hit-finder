import Plot, { PlotParams } from 'react-plotly.js';
import { Loader2 } from 'lucide-react';

interface PlotlyWrapperProps extends Omit<PlotParams, 'config' | 'layout'> {
  data: PlotParams['data'];
  layout?: Partial<PlotParams['layout']>;
  config?: Partial<PlotParams['config']>;
  height?: number;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

/**
 * Common Plotly.js wrapper with scientific theming and consistent configuration
 */
const PlotlyWrapper = ({
  data,
  layout = {},
  config = {},
  height = 400,
  loading = false,
  error = null,
  className = '',
  ...plotProps
}: PlotlyWrapperProps) => {
  // Default scientific theme configuration
  const defaultLayout: Partial<PlotParams['layout']> = {
    // Layout styling
    height,
    margin: { l: 60, r: 40, t: 40, b: 60 },
    
    // Font configuration for scientific publications
    font: {
      family: 'Inter, system-ui, -apple-system, sans-serif',
      size: 12,
      color: '#374151' // text-gray-700
    },
    
    // Background colors matching shadcn theme
    paper_bgcolor: 'rgba(0,0,0,0)', // transparent
    plot_bgcolor: 'rgba(0,0,0,0)',  // transparent
    
    // Grid styling
    xaxis: {
      gridcolor: '#E5E7EB', // gray-200
      gridwidth: 1,
      zeroline: false,
      linecolor: '#9CA3AF', // gray-400
      linewidth: 1,
      tickcolor: '#9CA3AF',
      tickfont: { size: 11, color: '#6B7280' }, // gray-500
      title: {
        font: { size: 13, color: '#374151' } // gray-700
      }
    },
    yaxis: {
      gridcolor: '#E5E7EB', // gray-200
      gridwidth: 1,
      zeroline: false,
      linecolor: '#9CA3AF', // gray-400
      linewidth: 1,
      tickcolor: '#9CA3AF',
      tickfont: { size: 11, color: '#6B7280' }, // gray-500
      title: {
        font: { size: 13, color: '#374151' } // gray-700
      }
    },
    
    // Legend styling
    legend: {
      bgcolor: 'rgba(255,255,255,0.9)',
      bordercolor: '#E5E7EB',
      borderwidth: 1,
      font: { size: 11 }
    },
    
    // Hover styling
    hoverlabel: {
      bgcolor: 'rgba(0,0,0,0.8)',
      bordercolor: 'rgba(0,0,0,0)',
      font: { size: 12, color: 'white', family: 'Inter' }
    },
    
    // Animation
    transition: {
      duration: 300,
      easing: 'cubic-in-out'
    }
  };

  // Default configuration for scientific charts
  const defaultConfig: Partial<PlotParams['config']> = {
    // Remove Plotly branding and toolbar
    displayModeBar: true,
    displaylogo: false,
    
    // Scientific-relevant tools only
    modeBarButtonsToRemove: [
      'select2d',
      'lasso2d',
      'autoScale2d',
      'hoverClosestCartesian',
      'hoverCompareCartesian',
      'toggleSpikelines'
    ],
    
    // Export options for publication
    toImageButtonOptions: {
      format: 'png',
      filename: 'scientific_chart',
      height: height,
      width: height * 1.2, // 5:6 aspect ratio for publications
      scale: 2 // High DPI for crisp images
    },
    
    // Responsive behavior
    responsive: true,
    
    // Locale for consistent number formatting
    locale: 'en-US'
  };

  // Merge configurations with user overrides
  const mergedLayout = {
    ...defaultLayout,
    ...layout,
    // Deep merge axis configurations
    xaxis: { ...defaultLayout.xaxis, ...layout.xaxis },
    yaxis: { ...defaultLayout.yaxis, ...layout.yaxis },
    legend: { ...defaultLayout.legend, ...layout.legend }
  };

  const mergedConfig = {
    ...defaultConfig,
    ...config,
    toImageButtonOptions: {
      ...defaultConfig.toImageButtonOptions,
      ...config.toImageButtonOptions
    }
  };

  // Error state
  if (error) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`} style={{ height }}>
        <div className="text-center">
          <div className="text-red-500 text-sm font-medium mb-2">Visualization Error</div>
          <div className="text-gray-600 text-xs">{error}</div>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-2 mx-auto" />
          <div className="text-gray-600 text-sm">Loading visualization...</div>
        </div>
      </div>
    );
  }

  // Ensure we have data to render
  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`} style={{ height }}>
        <div className="text-center">
          <div className="text-gray-500 text-sm">No data available</div>
          <div className="text-gray-400 text-xs mt-1">Process data to see visualization</div>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <Plot
        data={data}
        layout={mergedLayout}
        config={mergedConfig}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        {...plotProps}
      />
    </div>
  );
};

export default PlotlyWrapper;