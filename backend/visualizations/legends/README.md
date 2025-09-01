# Figure Legend System Architecture

## Overview

The bio-hit-finder figure legend system provides comprehensive, scientifically accurate legends for all visualization types in the platform. The system supports multiple expertise levels, output formats, and seamless integration with existing visualization functions.

## Architecture Components

### 1. Core Classes (`core.py`)

#### `LegendManager`
- Main interface for legend generation
- Coordinates template engine, formatters, and configuration
- Provides validation and analysis capabilities

#### `LegendContext` 
- Container for all information needed to generate a legend
- Automatically extracts statistical, biological, and technical context from data
- Handles configuration and expertise level management

#### `LegendConfig`
- Configuration management with hierarchical defaults
- Expertise-level, chart-type, and format-specific settings

### 2. Data Models (`models.py`)

#### Core Data Classes
- `LegendContent`: Complete legend with sections and metadata
- `LegendSection`: Individual legend section with type and priority
- `LegendMetadata`: Chart and data metadata for legend generation

#### Enums for Type Safety
- `ExpertiseLevel`: BASIC, INTERMEDIATE, EXPERT
- `ChartType`: All supported visualization types
- `OutputFormat`: HTML, PDF, STREAMLIT, MARKDOWN, PLAIN_TEXT

#### Context Classes
- `StatisticalContext`: Statistical methods and thresholds
- `BiologicalContext`: Platform and assay information  
- `TechnicalContext`: Processing and methodology details

### 3. Template System (`templates.py`)

#### `LegendTemplate` (Abstract Base Class)
- Defines interface for chart-type specific templates
- Handles section generation and priority assignment

#### Specialized Templates
- `HistogramTemplate`: Statistical distributions and methods
- `HeatmapTemplate`: Spatial patterns and color schemes
- `ScatterPlotTemplate`: Correlations and quadrant analysis

#### `TemplateRegistry`
- Manages chart-type to template mappings
- Supports custom template registration

#### `LegendTemplateEngine`
- Orchestrates template-based legend generation
- Handles variable substitution and content filtering

### 4. Output Formatters (`formatters.py`)

#### Format-Specific Formatters
- `HTMLFormatter`: Web display with CSS styling
- `PDFFormatter`: LaTeX-compatible formatting for reports
- `StreamlitFormatter`: Markdown with Streamlit-specific features
- `MarkdownFormatter`: Standard markdown output
- `PlainTextFormatter`: Simple text output

#### `FormatterFactory`
- Creates appropriate formatter for each output type
- Supports custom formatter registration

### 5. Integration System (`integration.py`)

#### `VisualizationIntegrator`
- Seamless integration with existing visualization functions
- Decorator-based and manual integration approaches
- Figure metadata storage for legend retrieval

#### Specialized Integrations
- `StreamlitIntegration`: Interactive web app features
- `PDFIntegration`: Report generation optimization

### 6. Configuration Management (`config.py`)

#### `LegendConfiguration`
- Hierarchical configuration system
- File-based configuration loading (YAML/JSON)
- Validation and export capabilities

#### Configuration Classes
- `ExpertiseConfig`: Expertise-level specific settings
- `ChartTypeConfig`: Chart-type specific preferences
- `OutputFormatConfig`: Format-specific styling

## Integration Strategies

### 1. Decorator Integration (Recommended)

```python
from visualizations.legends.integration import VisualizationIntegrator

integrator = VisualizationIntegrator()

@integrator.create_legend_decorator(ChartType.HEATMAP)
def create_plate_heatmap(df, metric_col, title):
    # Existing heatmap function
    return fig
```

### 2. Manual Integration

```python
# Add legend to existing figure
enhanced_fig, legend_text = integrator.add_legend_to_figure(
    figure=existing_fig,
    data=df,
    chart_type=ChartType.HISTOGRAM,
    expertise_level=ExpertiseLevel.INTERMEDIATE
)
```

### 3. Streamlit Integration

```python
from visualizations.legends.integration import StreamlitIntegration

st_integration = StreamlitIntegration()

# Interactive display with legend
st_integration.display_figure_with_legend(
    figure=fig,
    data=df,
    chart_type=ChartType.HEATMAP,
    layout='tabs'  # or 'columns', 'expandable'
)
```

### 4. PDF Report Integration

```python
from visualizations.legends.integration import PDFIntegration

pdf_integration = PDFIntegration()

# Add PDF-optimized legend
fig, latex_legend = pdf_integration.add_legend_to_pdf_figure(
    figure=fig,
    data=df,
    chart_type=ChartType.SCATTER_PLOT,
    expertise_level=ExpertiseLevel.EXPERT
)
```

## Implementation Plan

### Phase 1: Core Infrastructure (Completed)
- [x] Data models and enums
- [x] Core legend management classes
- [x] Basic template system
- [x] Output formatters
- [x] Configuration management

### Phase 2: Integration Layer
1. **Update existing visualization functions**:
   - Modify `visualizations/heatmaps.py` functions
   - Enhance `visualizations/charts.py` functions
   - Update QC dashboard components

2. **Streamlit integration**:
   - Add legend display options to main app
   - Implement expertise level selector
   - Add legend export functionality

3. **PDF report enhancement**:
   - Integrate with `export/pdf_generator.py`
   - Add legend sections to report templates
   - Implement figure caption generation

### Phase 3: Advanced Features
1. **Template customization**:
   - User-defined custom templates
   - Laboratory-specific biological context
   - Custom statistical method descriptions

2. **Interactive features**:
   - Dynamic legend updates based on user selections
   - Collapsible legend sections
   - Expertise level switching

3. **Validation and quality control**:
   - Automated legend completeness checking
   - Scientific accuracy validation
   - Consistency checks across figures

## Configuration Examples

### Basic Configuration (`legend_config.yaml`)

```yaml
expertise_levels:
  basic:
    include_formulas: false
    max_length: 500
    preferred_sections: ['description', 'interpretation']
  
  intermediate:
    include_formulas: true
    max_length: 1200
    preferred_sections: ['description', 'biological_context', 'statistical_methods', 'interpretation']
  
  expert:
    include_formulas: true
    include_references: true
    max_length: 2500

chart_types:
  heatmap:
    emphasize_color_scheme: true
    include_spatial_context: true
  
  histogram:
    emphasize_statistical_methods: true

biological_context:
  platform_name: "Custom Platform"
  custom_reporters:
    gfp: "Green fluorescent protein reporter"
```

### Custom Biological Context

```python
from visualizations.legends.config import get_global_configuration

config = get_global_configuration()
biological_defaults = config.get_biological_defaults()

# Customize for your platform
biological_defaults.update({
    'platform_name': 'Your Custom Platform',
    'reporters': {
        'your_reporter': 'Custom reporter description'
    }
})
```

## Usage Examples

### Basic Usage

```python
from visualizations.legends import LegendManager, LegendContext, ChartType, ExpertiseLevel

# Create legend for any visualization
legend_manager = LegendManager()
context = LegendContext(
    data=your_dataframe,
    chart_type=ChartType.HEATMAP,
    expertise_level=ExpertiseLevel.INTERMEDIATE
)

legend_text = legend_manager.generate_and_format(context)
```

### Advanced Usage with Custom Configuration

```python
from visualizations.legends.config import LegendConfiguration

# Load custom configuration
config = LegendConfiguration('my_custom_config.yaml')

# Create legend manager with custom config
legend_manager = LegendManager(config.create_context_config(
    ExpertiseLevel.EXPERT,
    ChartType.HEATMAP, 
    OutputFormat.PDF
))
```

## Extension Points

### 1. Custom Chart Types

```python
# Add new chart type
class MyCustomTemplate(LegendTemplate):
    def generate_sections(self, context):
        # Generate custom sections
        return sections

# Register template
template_registry.register_template(ChartType.MY_CUSTOM, MyCustomTemplate())
```

### 2. Custom Output Formats

```python
# Add new output format
class MyCustomFormatter(LegendFormatter):
    def format(self, legend_content):
        # Custom formatting logic
        return formatted_text

# Register formatter  
FormatterFactory.register_formatter(OutputFormat.MY_FORMAT, MyCustomFormatter)
```

### 3. Custom Biological Context

```python
# Extend biological context for your platform
custom_biological = {
    'platform_name': 'Your Platform',
    'reporters': {
        'reporter1': 'Description 1',
        'reporter2': 'Description 2'
    },
    'custom_interpretations': {
        'pattern1': 'Custom interpretation'
    }
}

config.get_biological_defaults().update(custom_biological)
```

## Scientific Accuracy Features

### 1. Biological Context
- Platform-specific terminology and background
- Reporter gene function and pathway information
- Strain characteristics and experimental rationale
- Mechanistic insights and interpretation guidance

### 2. Statistical Methods
- Formula documentation with LaTeX formatting
- Method assumptions and limitations
- Threshold selection rationale
- Quality control procedures

### 3. Expertise-Level Adaptation
- **Basic**: Minimal jargon, focus on interpretation
- **Intermediate**: Balanced technical detail
- **Expert**: Complete methodology and references

### 4. Validation Framework
- Completeness checking (essential sections present)
- Scientific accuracy validation
- Consistency across related figures
- Length and readability optimization

## Performance Considerations

### Caching Strategy
- Template compilation caching
- Configuration object reuse
- Metadata extraction optimization

### Memory Management  
- Lazy loading of templates
- Efficient string manipulation
- Minimal object duplication

### Scalability
- Batch legend generation for reports
- Parallel processing for large datasets
- Streaming output for very long legends

## Testing Strategy

### Unit Tests
- Individual component testing
- Data model validation
- Template generation verification
- Formatter output validation

### Integration Tests
- End-to-end legend generation
- Streamlit integration testing
- PDF export validation
- Configuration loading verification

### Scientific Accuracy Tests
- Biological context accuracy
- Statistical method descriptions
- Formula correctness
- Reference completeness

## Future Enhancements

### 1. Machine Learning Integration
- Automatic biological context detection
- Smart template selection based on data patterns
- Quality score prediction for legend completeness

### 2. Collaborative Features
- Multi-user legend editing
- Version control for custom templates
- Shared configuration repositories

### 3. Advanced Visualization Support
- Interactive legend elements
- Dynamic content based on figure interactions
- Multi-figure legend coordination

### 4. Standards Compliance
- Journal-specific formatting templates
- Regulatory submission formats
- International guideline compliance

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install pyyaml plotly pandas numpy
   ```

2. **Configuration File Not Found**
   ```python
   # Use default configuration
   legend_manager = LegendManager()
   ```

3. **Template Not Found**
   ```python
   # Register custom template or use generic
   template_registry.register_template(chart_type, custom_template)
   ```

4. **Integration Issues**
   ```python
   # Check function registration
   integrator.register_function('my_function', ChartType.HEATMAP)
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for legend system
logger = logging.getLogger('visualizations.legends')
logger.setLevel(logging.DEBUG)
```

## Contributing

### Adding New Templates
1. Inherit from `LegendTemplate`
2. Implement `generate_sections()` method
3. Register with `TemplateRegistry`
4. Add tests and documentation

### Adding New Formatters
1. Inherit from `LegendFormatter` 
2. Implement `format()` method
3. Register with `FormatterFactory`
4. Add format-specific tests

### Extending Configuration
1. Update relevant config dataclasses
2. Add validation logic
3. Update sample configuration
4. Document new options

## License

This legend system is part of the bio-hit-finder platform and follows the same license terms.