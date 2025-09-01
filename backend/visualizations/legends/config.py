"""
Configuration management for the figure legend system.

This module provides configuration management, validation, and default
settings for all aspects of the legend generation system.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json
import logging
from enum import Enum

from .models import ExpertiseLevel, ChartType, OutputFormat, LegendSection

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class ExpertiseConfig:
    """Configuration for a specific expertise level."""
    
    include_formulas: bool = True
    include_technical_details: bool = True
    include_references: bool = False
    max_length: Optional[int] = None
    use_abbreviations: bool = False
    include_glossary: bool = False
    
    # Section preferences
    preferred_sections: List[str] = field(default_factory=lambda: [
        'description', 'biological_context', 'statistical_methods', 'interpretation'
    ])
    
    # Content complexity
    formula_complexity: str = 'standard'  # 'simple', 'standard', 'detailed'
    explanation_depth: str = 'moderate'   # 'minimal', 'moderate', 'comprehensive'


@dataclass
class ChartTypeConfig:
    """Configuration for a specific chart type."""
    
    # Emphasis preferences
    emphasize_color_scheme: bool = False
    emphasize_statistical_methods: bool = True
    emphasize_biological_context: bool = True
    emphasize_interpretation: bool = True
    
    # Specific sections
    include_spatial_context: bool = False    # For heatmaps
    include_correlation_info: bool = False   # For scatter plots
    include_distribution_info: bool = False # For histograms
    
    # Template preferences
    template_priority: List[str] = field(default_factory=list)
    custom_sections: Dict[str, str] = field(default_factory=dict)


@dataclass
class OutputFormatConfig:
    """Configuration for specific output formats."""
    
    # Formatting preferences
    use_html_formatting: bool = True
    use_markdown_formatting: bool = False
    max_line_length: Optional[int] = None
    
    # Style preferences
    section_separator: str = '\n\n'
    bullet_style: str = '•'
    emphasis_style: str = 'bold'  # 'bold', 'italic', 'underline'
    
    # Content preferences
    include_metadata: bool = True
    include_timestamp: bool = True
    include_validation_info: bool = False


class LegendConfiguration:
    """Main configuration manager for the legend system."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
        """
        
        self.config_file = Path(config_file) if config_file else None
        self._config_cache: Dict[str, Any] = {}
        
        # Default configurations
        self._expertise_configs = self._create_default_expertise_configs()
        self._chart_type_configs = self._create_default_chart_configs()
        self._output_format_configs = self._create_default_format_configs()
        
        # Biological and technical defaults
        self._biological_defaults = self._create_biological_defaults()
        self._technical_defaults = self._create_technical_defaults()
        
        # Load custom configuration if provided
        if self.config_file and self.config_file.exists():
            self._load_configuration_file()
    
    def _create_default_expertise_configs(self) -> Dict[ExpertiseLevel, ExpertiseConfig]:
        """Create default configurations for each expertise level."""
        
        return {
            ExpertiseLevel.BASIC: ExpertiseConfig(
                include_formulas=False,
                include_technical_details=False,
                include_references=False,
                max_length=500,
                use_abbreviations=True,
                preferred_sections=['description', 'interpretation'],
                formula_complexity='simple',
                explanation_depth='minimal'
            ),
            
            ExpertiseLevel.INTERMEDIATE: ExpertiseConfig(
                include_formulas=True,
                include_technical_details=True,
                include_references=False,
                max_length=1200,
                use_abbreviations=False,
                preferred_sections=['description', 'biological_context', 'statistical_methods', 'interpretation'],
                formula_complexity='standard',
                explanation_depth='moderate'
            ),
            
            ExpertiseLevel.EXPERT: ExpertiseConfig(
                include_formulas=True,
                include_technical_details=True,
                include_references=True,
                max_length=2500,
                use_abbreviations=False,
                include_glossary=True,
                preferred_sections=[
                    'description', 'biological_context', 'statistical_methods', 
                    'methodology', 'interpretation', 'limitations', 'references'
                ],
                formula_complexity='detailed',
                explanation_depth='comprehensive'
            )
        }
    
    def _create_default_chart_configs(self) -> Dict[ChartType, ChartTypeConfig]:
        """Create default configurations for each chart type."""
        
        configs = {}
        
        # Heatmap configuration
        configs[ChartType.HEATMAP] = ChartTypeConfig(
            emphasize_color_scheme=True,
            include_spatial_context=True,
            template_priority=['description', 'color_scheme', 'biological_context', 'interpretation']
        )
        
        # Histogram configuration
        configs[ChartType.HISTOGRAM] = ChartTypeConfig(
            emphasize_statistical_methods=True,
            include_distribution_info=True,
            template_priority=['description', 'statistical_methods', 'interpretation']
        )
        
        # Scatter plot configuration
        configs[ChartType.SCATTER_PLOT] = ChartTypeConfig(
            emphasize_statistical_methods=True,
            include_correlation_info=True,
            template_priority=['description', 'statistical_methods', 'biological_context', 'interpretation']
        )
        
        # Default configuration for other chart types
        default_config = ChartTypeConfig(
            template_priority=['description', 'biological_context', 'interpretation']
        )
        
        for chart_type in ChartType:
            if chart_type not in configs:
                configs[chart_type] = default_config
        
        return configs
    
    def _create_default_format_configs(self) -> Dict[OutputFormat, OutputFormatConfig]:
        """Create default configurations for output formats."""
        
        return {
            OutputFormat.HTML: OutputFormatConfig(
                use_html_formatting=True,
                include_metadata=True,
                include_timestamp=True,
                emphasis_style='bold'
            ),
            
            OutputFormat.PDF: OutputFormatConfig(
                use_html_formatting=False,
                max_line_length=80,
                include_metadata=True,
                include_timestamp=False,
                emphasis_style='bold'
            ),
            
            OutputFormat.STREAMLIT: OutputFormatConfig(
                use_markdown_formatting=True,
                include_metadata=True,
                include_timestamp=False,
                emphasis_style='bold'
            ),
            
            OutputFormat.MARKDOWN: OutputFormatConfig(
                use_markdown_formatting=True,
                include_metadata=False,
                include_timestamp=False,
                emphasis_style='bold'
            ),
            
            OutputFormat.PLAIN_TEXT: OutputFormatConfig(
                use_html_formatting=False,
                use_markdown_formatting=False,
                max_line_length=72,
                section_separator='\\n\\n',
                bullet_style='-',
                emphasis_style='uppercase'
            )
        }
    
    def _create_biological_defaults(self) -> Dict[str, Any]:
        """Create default biological context configuration."""
        
        return {
            'platform_name': 'BREAKthrough OM Screening Platform',
            'platform_description': 'Antimicrobial discovery platform targeting Gram-negative outer membrane disruption',
            'assay_type': 'Dual-reporter envelope stress monitoring',
            
            # Reporter descriptions
            'reporters': {
                'lptA': {
                    'full_name': 'lipopolysaccharide transport A',
                    'pathway': 'σE envelope stress response',
                    'function': 'LPS transport monitoring',
                    'significance': 'Reports outer membrane LPS transport disruption'
                },
                'ldtD': {
                    'full_name': 'L,D-transpeptidase D',
                    'pathway': 'Cpx envelope stress response', 
                    'function': 'Structural compensation monitoring',
                    'significance': 'Reports peptidoglycan remodeling and structural stress'
                }
            },
            
            # Strain information
            'strains': {
                'WT': {
                    'full_name': 'E. coli wild-type',
                    'purpose': 'Primary screening strain',
                    'characteristics': 'Normal outer membrane permeability'
                },
                'tolC': {
                    'full_name': 'E. coli ΔtolC',
                    'purpose': 'Efflux-deficient sensitization strain',
                    'characteristics': 'Impaired multidrug efflux, enhanced compound accumulation'
                },
                'SA': {
                    'full_name': 'S. aureus',
                    'purpose': 'Gram-positive selectivity control',
                    'characteristics': 'Lacks outer membrane, tests compound selectivity'
                }
            },
            
            # Standard interpretations
            'interpretations': {
                'high_z_score': 'Strong envelope stress response activation',
                'selective_response': 'Pathway-specific compound activity',
                'correlation_patterns': 'Mechanistic insights from dual-reporter comparison'
            }
        }
    
    def _create_technical_defaults(self) -> Dict[str, Any]:
        """Create default technical configuration."""
        
        return {
            'statistical_methods': {
                'robust_zscore': {
                    'formula': 'Z = (value - median) / (1.4826 × MAD)',
                    'description': 'Outlier-resistant statistical scoring',
                    'assumptions': 'Heavy-tailed distributions common in screening data'
                },
                'bscore_correction': {
                    'formula': 'B-score = median-polish residual / (1.4826 × MAD)',
                    'description': 'Systematic bias correction using median-polish',
                    'applications': 'Row/column effects, edge effects, spatial artifacts'
                },
                'viability_gating': {
                    'formula': 'Viable = ATP > f × median(ATP)',
                    'description': 'ATP-based viability threshold',
                    'default_threshold': 0.3
                }
            },
            
            'quality_control': {
                'edge_effects': 'Spatial correlation analysis of plate periphery',
                'systematic_bias': 'Row/column pattern detection',
                'distributional_qc': 'Z-score distribution assessment'
            },
            
            'thresholds': {
                'significance_zscore': 2.0,
                'strong_hit_zscore': 3.0,
                'viability_default': 0.3,
                'correlation_strong': 0.7,
                'correlation_moderate': 0.4
            }
        }
    
    def _load_configuration_file(self):
        """Load configuration from file."""
        
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    custom_config = yaml.safe_load(f)
                elif self.config_file.suffix.lower() == '.json':
                    custom_config = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config file format: {self.config_file.suffix}")
            
            # Merge with defaults
            self._merge_custom_configuration(custom_config)
            logger.info(f"Loaded configuration from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration file {self.config_file}: {e}")
            raise ConfigurationError(f"Configuration file error: {e}")
    
    def _merge_custom_configuration(self, custom_config: Dict[str, Any]):
        """Merge custom configuration with defaults."""
        
        # Update expertise configurations
        if 'expertise_levels' in custom_config:
            for level_name, config_dict in custom_config['expertise_levels'].items():
                try:
                    level = ExpertiseLevel(level_name)
                    if level in self._expertise_configs:
                        # Update existing config
                        current_config = self._expertise_configs[level]
                        for key, value in config_dict.items():
                            if hasattr(current_config, key):
                                setattr(current_config, key, value)
                except ValueError:
                    logger.warning(f"Unknown expertise level in config: {level_name}")
        
        # Update chart type configurations
        if 'chart_types' in custom_config:
            for chart_name, config_dict in custom_config['chart_types'].items():
                try:
                    chart_type = ChartType(chart_name)
                    if chart_type in self._chart_type_configs:
                        current_config = self._chart_type_configs[chart_type]
                        for key, value in config_dict.items():
                            if hasattr(current_config, key):
                                setattr(current_config, key, value)
                except ValueError:
                    logger.warning(f"Unknown chart type in config: {chart_name}")
        
        # Update biological defaults
        if 'biological_context' in custom_config:
            self._biological_defaults.update(custom_config['biological_context'])
        
        # Update technical defaults
        if 'technical_context' in custom_config:
            self._technical_defaults.update(custom_config['technical_context'])
    
    def get_expertise_config(self, expertise_level: ExpertiseLevel) -> ExpertiseConfig:
        """Get configuration for specific expertise level."""
        return self._expertise_configs.get(expertise_level, self._expertise_configs[ExpertiseLevel.INTERMEDIATE])
    
    def get_chart_type_config(self, chart_type: ChartType) -> ChartTypeConfig:
        """Get configuration for specific chart type."""
        return self._chart_type_configs.get(chart_type, ChartTypeConfig())
    
    def get_output_format_config(self, output_format: OutputFormat) -> OutputFormatConfig:
        """Get configuration for specific output format."""
        return self._output_format_configs.get(output_format, OutputFormatConfig())
    
    def get_biological_defaults(self) -> Dict[str, Any]:
        """Get biological context defaults."""
        return self._biological_defaults.copy()
    
    def get_technical_defaults(self) -> Dict[str, Any]:
        """Get technical context defaults."""
        return self._technical_defaults.copy()
    
    def create_context_config(self,
                            expertise_level: ExpertiseLevel,
                            chart_type: ChartType,
                            output_format: OutputFormat) -> Dict[str, Any]:
        """Create combined configuration for a specific context.
        
        Args:
            expertise_level: Target expertise level
            chart_type: Chart type being created
            output_format: Output format
            
        Returns:
            Combined configuration dictionary
        """
        
        config = {}
        
        # Get individual configurations
        expertise_config = self.get_expertise_config(expertise_level)
        chart_config = self.get_chart_type_config(chart_type)
        format_config = self.get_output_format_config(output_format)
        
        # Merge configurations with appropriate precedence
        config.update({
            'expertise': expertise_config,
            'chart_type': chart_config,
            'output_format': format_config,
            'biological_defaults': self.get_biological_defaults(),
            'technical_defaults': self.get_technical_defaults()
        })
        
        return config
    
    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return any issues.
        
        Returns:
            List of validation issues (empty if valid)
        """
        
        issues = []
        
        # Check expertise configurations
        for level, config in self._expertise_configs.items():
            if config.max_length and config.max_length < 100:
                issues.append(f"Max length for {level.value} too short: {config.max_length}")
            
            if not config.preferred_sections:
                issues.append(f"No preferred sections for {level.value}")
        
        # Check chart type configurations
        for chart_type, config in self._chart_type_configs.items():
            if config.template_priority and len(config.template_priority) == 0:
                issues.append(f"Empty template priority for {chart_type.value}")
        
        # Check biological defaults
        required_biological = ['platform_name', 'assay_type']
        for key in required_biological:
            if key not in self._biological_defaults:
                issues.append(f"Missing biological default: {key}")
        
        return issues
    
    def export_configuration(self, export_path: Union[str, Path], 
                           format_type: str = 'yaml') -> Path:
        """Export current configuration to file.
        
        Args:
            export_path: Path for exported configuration
            format_type: Format ('yaml' or 'json')
            
        Returns:
            Path to exported file
        """
        
        export_path = Path(export_path)
        
        # Create export dictionary
        export_data = {
            'expertise_levels': {},
            'chart_types': {},
            'output_formats': {},
            'biological_context': self._biological_defaults,
            'technical_context': self._technical_defaults
        }
        
        # Convert dataclasses to dictionaries
        for level, config in self._expertise_configs.items():
            export_data['expertise_levels'][level.value] = {
                'include_formulas': config.include_formulas,
                'include_technical_details': config.include_technical_details,
                'include_references': config.include_references,
                'max_length': config.max_length,
                'use_abbreviations': config.use_abbreviations,
                'preferred_sections': config.preferred_sections,
                'formula_complexity': config.formula_complexity,
                'explanation_depth': config.explanation_depth
            }
        
        for chart_type, config in self._chart_type_configs.items():
            export_data['chart_types'][chart_type.value] = {
                'emphasize_color_scheme': config.emphasize_color_scheme,
                'emphasize_statistical_methods': config.emphasize_statistical_methods,
                'emphasize_biological_context': config.emphasize_biological_context,
                'template_priority': config.template_priority,
                'custom_sections': config.custom_sections
            }
        
        # Write to file
        try:
            with open(export_path, 'w') as f:
                if format_type.lower() == 'yaml':
                    yaml.dump(export_data, f, default_flow_style=False, indent=2)
                elif format_type.lower() == 'json':
                    json.dump(export_data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format_type}")
            
            logger.info(f"Configuration exported to {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise ConfigurationError(f"Export failed: {e}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        
        self._expertise_configs = self._create_default_expertise_configs()
        self._chart_type_configs = self._create_default_chart_configs()
        self._output_format_configs = self._create_default_format_configs()
        self._biological_defaults = self._create_biological_defaults()
        self._technical_defaults = self._create_technical_defaults()
        
        logger.info("Configuration reset to defaults")


# Global configuration instance
_global_config: Optional[LegendConfiguration] = None


def get_global_configuration() -> LegendConfiguration:
    """Get global configuration instance."""
    global _global_config
    
    if _global_config is None:
        _global_config = LegendConfiguration()
    
    return _global_config


def set_global_configuration(config: LegendConfiguration):
    """Set global configuration instance."""
    global _global_config
    _global_config = config


def load_configuration_from_file(config_file: Union[str, Path]) -> LegendConfiguration:
    """Load configuration from file and set as global."""
    
    config = LegendConfiguration(config_file)
    set_global_configuration(config)
    return config


# Configuration validation utilities
def validate_expertise_level_config(config: Dict[str, Any]) -> List[str]:
    """Validate expertise level configuration."""
    
    issues = []
    required_fields = ['include_formulas', 'include_technical_details', 'preferred_sections']
    
    for field in required_fields:
        if field not in config:
            issues.append(f"Missing required field: {field}")
    
    if 'max_length' in config and config['max_length'] < 50:
        issues.append("Max length too short (minimum 50 characters)")
    
    return issues


def create_sample_configuration_file(output_path: Union[str, Path]):
    """Create a sample configuration file with documentation.
    
    Args:
        output_path: Path where to save sample configuration
    """
    
    sample_config = {
        'expertise_levels': {
            'basic': {
                'include_formulas': False,
                'include_technical_details': False,
                'max_length': 500,
                'preferred_sections': ['description', 'interpretation'],
                'explanation_depth': 'minimal'
            },
            'intermediate': {
                'include_formulas': True,
                'include_technical_details': True,
                'max_length': 1200,
                'preferred_sections': ['description', 'biological_context', 'statistical_methods', 'interpretation'],
                'explanation_depth': 'moderate'
            },
            'expert': {
                'include_formulas': True,
                'include_technical_details': True,
                'include_references': True,
                'max_length': 2500,
                'preferred_sections': ['description', 'biological_context', 'statistical_methods', 
                                     'methodology', 'interpretation', 'limitations'],
                'explanation_depth': 'comprehensive'
            }
        },
        'chart_types': {
            'heatmap': {
                'emphasize_color_scheme': True,
                'include_spatial_context': True
            },
            'histogram': {
                'emphasize_statistical_methods': True,
                'include_distribution_info': True
            }
        },
        'biological_context': {
            'platform_name': 'Custom Screening Platform',
            'custom_reporters': {
                'custom_gene': 'Custom reporter description'
            }
        }
    }
    
    output_path = Path(output_path)
    
    with open(output_path, 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    logger.info(f"Sample configuration created at {output_path}")


# Export commonly used items
__all__ = [
    'LegendConfiguration',
    'ExpertiseConfig', 
    'ChartTypeConfig',
    'OutputFormatConfig',
    'ConfigurationError',
    'get_global_configuration',
    'set_global_configuration', 
    'load_configuration_from_file',
    'create_sample_configuration_file'
]