"""
Data models and type definitions for the figure legend system.

This module defines the core data structures used throughout the legend system,
including enums for chart types and expertise levels, and dataclasses for
organizing legend content and metadata.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import pandas as pd


class ChartType(Enum):
    """Supported chart types for legend generation."""
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram" 
    SCATTER_PLOT = "scatter_plot"
    BAR_CHART = "bar_chart"
    BOX_PLOT = "box_plot"
    LINE_PLOT = "line_plot"
    CORRELATION_MATRIX = "correlation_matrix"
    DISTRIBUTION_PLOT = "distribution_plot"


class ExpertiseLevel(Enum):
    """User expertise levels determining legend complexity and detail."""
    BASIC = "basic"           # ≤500 chars, minimal jargon, practical focus
    INTERMEDIATE = "intermediate"  # ≤1200 chars, balanced technical detail
    EXPERT = "expert"         # ≤2500 chars, complete methodology and references


class OutputFormat(Enum):
    """Supported output formats for legend rendering."""
    HTML = "html"
    STREAMLIT = "streamlit"
    PDF = "pdf"
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"


class ContentSection(Enum):
    """Legend content section types."""
    BIOLOGICAL_CONTEXT = "biological_context"
    STATISTICAL_METHODS = "statistical_methods"
    INTERPRETATION_GUIDE = "interpretation_guide"
    QUALITY_CONTROL = "quality_control"
    TECHNICAL_DETAILS = "technical_details"
    REFERENCES = "references"
    LIMITATIONS = "limitations"


@dataclass
class StatisticalContext:
    """Statistical information extracted from data analysis."""
    sample_size: int
    median_value: Optional[float] = None
    mad_value: Optional[float] = None
    z_score_range: Optional[tuple] = None
    correlation_coefficient: Optional[float] = None
    significance_threshold: float = 2.0
    p_value: Optional[float] = None
    normality_test: Optional[str] = None
    outlier_count: Optional[int] = None
    method_used: str = "robust_z_score"


@dataclass  
class BiologicalContext:
    """Biological information relevant to the visualization."""
    reporter_systems: List[str]
    stress_pathways: List[str] 
    strain_types: List[str]
    assay_type: str = "BREAKthrough_OM"
    biological_process: str = "envelope_stress_response"
    mechanism_of_action: Optional[str] = None
    therapeutic_relevance: Optional[str] = None


@dataclass
class TechnicalContext:
    """Technical assay and platform information."""
    plate_format: str = "384_well"
    detection_method: str = "luminescence"
    normalization_method: str = "BG_BT_ratio"
    processing_software: str = "bio-hit-finder"
    quality_metrics: Dict[str, float] = None
    edge_effects_detected: bool = False
    b_scoring_applied: bool = False
    viability_threshold: float = 0.3
    
    def __post_init__(self):
        """Initialize empty quality_metrics dict if None provided."""
        if self.quality_metrics is None:
            self.quality_metrics = {}


@dataclass
class LegendMetadata:
    """Metadata describing the visualization and analysis context."""
    chart_type: ChartType
    expertise_level: ExpertiseLevel
    data_characteristics: Dict[str, Any]
    statistical_context: StatisticalContext
    biological_context: BiologicalContext
    technical_context: TechnicalContext
    creation_timestamp: Optional[str] = None
    analysis_parameters: Optional[Dict[str, Any]] = None


@dataclass
class LegendSection:
    """Individual section of legend content."""
    section_type: ContentSection
    title: str
    content: str
    char_count: int
    priority: int = 1  # 1=high, 2=medium, 3=low
    
    def __post_init__(self):
        """Calculate character count after initialization."""
        self.char_count = len(self.content)


@dataclass  
class LegendContent:
    """Complete legend content organized by sections."""
    sections: Dict[ContentSection, LegendSection]
    total_char_count: int
    expertise_level: ExpertiseLevel
    chart_type: ChartType
    
    def __post_init__(self):
        """Calculate total character count after initialization."""
        self.total_char_count = sum(section.char_count for section in self.sections.values())
    
    def get_section(self, section_type: ContentSection) -> Optional[LegendSection]:
        """Get a specific legend section."""
        return self.sections.get(section_type)
    
    def get_priority_sections(self, max_priority: int = 2) -> Dict[ContentSection, LegendSection]:
        """Get sections up to specified priority level."""
        return {
            section_type: section 
            for section_type, section in self.sections.items()
            if section.priority <= max_priority
        }
    
    def to_text(self, separator: str = "\n\n") -> str:
        """Convert all sections to plain text."""
        return separator.join([
            f"{section.title}\n{section.content}" 
            for section in self.sections.values()
        ])


@dataclass
class LegendConfig:
    """Configuration for legend generation."""
    max_char_limits: Dict[ExpertiseLevel, int]
    section_priorities: Dict[ContentSection, int]
    include_formulas: bool = True
    include_references: bool = True
    biological_context_template: str = "BREAKthrough_OM"
    custom_terminology: Optional[Dict[str, str]] = None
    
    @classmethod
    def default(cls) -> 'LegendConfig':
        """Create default configuration."""
        return cls(
            max_char_limits={
                ExpertiseLevel.BASIC: 500,
                ExpertiseLevel.INTERMEDIATE: 1200,
                ExpertiseLevel.EXPERT: 2500
            },
            section_priorities={
                ContentSection.BIOLOGICAL_CONTEXT: 1,
                ContentSection.INTERPRETATION_GUIDE: 1,
                ContentSection.STATISTICAL_METHODS: 2,
                ContentSection.QUALITY_CONTROL: 2,
                ContentSection.TECHNICAL_DETAILS: 3,
                ContentSection.REFERENCES: 3,
                ContentSection.LIMITATIONS: 3
            }
        )


# Type aliases for commonly used types
DataFrameType = Union[pd.DataFrame, Dict[str, Any]]
PlotlyFigure = Any  # Avoid plotly import dependency
MatplotlibFigure = Any  # Avoid matplotlib import dependency
VisualizationData = Dict[str, Any]