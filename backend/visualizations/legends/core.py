"""
Core legend management classes for the figure legend system.

This module provides the main orchestration classes for legend generation,
including context extraction from data analysis and intelligent content creation.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from .models import (
    ChartType, ExpertiseLevel, LegendMetadata, LegendContent, LegendSection,
    ContentSection, StatisticalContext, BiologicalContext, TechnicalContext,
    LegendConfig, DataFrameType
)

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts metadata and context information from data analysis results."""
    
    @staticmethod
    def extract_statistical_context(
        data: DataFrameType, 
        metric_columns: Optional[List[str]] = None
    ) -> StatisticalContext:
        """Extract statistical information from DataFrame."""
        try:
            if isinstance(data, dict):
                # Convert dict to DataFrame if possible
                if 'data' in data and isinstance(data['data'], pd.DataFrame):
                    df = data['data']
                else:
                    # Create minimal statistical context from dict
                    return StatisticalContext(
                        sample_size=data.get('sample_size', 0),
                        method_used=data.get('method_used', 'unknown')
                    )
            else:
                df = data
            
            # Identify metric columns if not provided
            if metric_columns is None:
                metric_columns = [col for col in df.columns if 
                                col.startswith(('Z_', 'Ratio_', 'BG_', 'BT_', 'OD_'))]
            
            if not metric_columns:
                return StatisticalContext(sample_size=len(df))
            
            # Calculate statistical properties for first metric column
            primary_metric = df[metric_columns[0]].dropna()
            
            if len(primary_metric) == 0:
                return StatisticalContext(sample_size=len(df))
            
            median_val = primary_metric.median()
            mad_val = np.median(np.abs(primary_metric - median_val))
            z_min, z_max = primary_metric.min(), primary_metric.max()
            outlier_count = len(primary_metric[np.abs(primary_metric - median_val) > 3 * mad_val])
            
            return StatisticalContext(
                sample_size=len(df),
                median_value=median_val,
                mad_value=mad_val,
                z_score_range=(z_min, z_max),
                outlier_count=outlier_count,
                method_used="robust_z_score" if 'Z_' in metric_columns[0] else "ratio_analysis"
            )
            
        except Exception as e:
            logger.warning(f"Error extracting statistical context: {e}")
            return StatisticalContext(sample_size=0)
    
    @staticmethod
    def extract_biological_context(
        data: DataFrameType,
        config: Optional[Dict[str, Any]] = None
    ) -> BiologicalContext:
        """Extract biological context from data structure."""
        try:
            # Default BREAKthrough platform context
            reporter_systems = ["lptA", "ldtD"]
            stress_pathways = ["σE envelope stress", "Cpx envelope stress"]
            strain_types = ["E. coli WT", "E. coli ΔtolC", "S. aureus"]
            
            # Extract from data if available
            if isinstance(data, pd.DataFrame):
                # Infer reporter systems from column names
                if any('lptA' in col for col in data.columns):
                    reporter_systems = ["lptA"]
                if any('ldtD' in col for col in data.columns):
                    if "lptA" in reporter_systems:
                        reporter_systems = ["lptA", "ldtD"]
                    else:
                        reporter_systems = ["ldtD"]
                        
                # Infer strain types from column names
                if any('WT' in col for col in data.columns):
                    strain_types = []
                    if any('WT' in col for col in data.columns):
                        strain_types.append("E. coli WT")
                    if any('tolC' in col for col in data.columns):
                        strain_types.append("E. coli ΔtolC")
                    if any('SA' in col for col in data.columns):
                        strain_types.append("S. aureus")
            
            # Override with config if provided
            if config:
                reporter_systems = config.get('reporter_systems', reporter_systems)
                strain_types = config.get('strain_types', strain_types)
            
            return BiologicalContext(
                reporter_systems=reporter_systems,
                stress_pathways=stress_pathways,
                strain_types=strain_types,
                assay_type="BREAKthrough_OM",
                biological_process="envelope_stress_response",
                therapeutic_relevance="antimicrobial_adjuvant_discovery"
            )
            
        except Exception as e:
            logger.warning(f"Error extracting biological context: {e}")
            return BiologicalContext(
                reporter_systems=["lptA", "ldtD"],
                stress_pathways=["σE envelope stress", "Cpx envelope stress"],
                strain_types=["E. coli WT", "E. coli ΔtolC", "S. aureus"]
            )
    
    @staticmethod
    def extract_technical_context(
        data: DataFrameType,
        config: Optional[Dict[str, Any]] = None
    ) -> TechnicalContext:
        """Extract technical assay information."""
        try:
            quality_metrics = {}
            edge_effects = False
            b_scoring = False
            viability_threshold = 0.3
            
            # Extract from config if provided
            if config:
                quality_metrics = config.get('quality_metrics', {})
                edge_effects = config.get('edge_effects_detected', False)
                b_scoring = config.get('b_scoring_applied', False)
                viability_threshold = config.get('viability_threshold', 0.3)
            
            # Infer from data structure
            if isinstance(data, pd.DataFrame):
                # Detect if B-scoring was applied
                if any('B_' in col for col in data.columns):
                    b_scoring = True
                
                # Check for edge effect flags
                if 'Edge_Flag' in data.columns:
                    edge_effects = data['Edge_Flag'].any() if not data['Edge_Flag'].isna().all() else False
                
                # Calculate basic quality metrics
                if 'Z_lptA' in data.columns:
                    z_values = data['Z_lptA'].dropna()
                    if len(z_values) > 0:
                        quality_metrics['z_score_range'] = float(z_values.max() - z_values.min())
                        quality_metrics['outlier_fraction'] = float(len(z_values[np.abs(z_values) > 3]) / len(z_values))
            
            return TechnicalContext(
                plate_format="384_well",
                detection_method="luminescence",
                normalization_method="BG_BT_ratio",
                processing_software="bio-hit-finder",
                quality_metrics=quality_metrics,
                edge_effects_detected=edge_effects,
                b_scoring_applied=b_scoring,
                viability_threshold=viability_threshold
            )
            
        except Exception as e:
            logger.warning(f"Error extracting technical context: {e}")
            return TechnicalContext(
                quality_metrics={},
                edge_effects_detected=False,
                b_scoring_applied=False
            )


class LegendContext:
    """Manages context extraction and preparation for legend generation."""
    
    def __init__(self, config: Optional[LegendConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or LegendConfig.default()
        self.extractor = MetadataExtractor()
    
    def create_metadata(
        self,
        data: DataFrameType,
        chart_type: ChartType,
        expertise_level: ExpertiseLevel,
        analysis_config: Optional[Dict[str, Any]] = None
    ) -> LegendMetadata:
        """Create complete metadata for legend generation."""
        try:
            # Extract contexts
            statistical_context = self.extractor.extract_statistical_context(data)
            biological_context = self.extractor.extract_biological_context(data, analysis_config)
            technical_context = self.extractor.extract_technical_context(data, analysis_config)
            
            # Extract data characteristics
            data_characteristics = self._extract_data_characteristics(data)
            
            return LegendMetadata(
                chart_type=chart_type,
                expertise_level=expertise_level,
                data_characteristics=data_characteristics,
                statistical_context=statistical_context,
                biological_context=biological_context,
                technical_context=technical_context,
                creation_timestamp=datetime.now().isoformat(),
                analysis_parameters=analysis_config
            )
            
        except Exception as e:
            logger.error(f"Error creating legend metadata: {e}")
            raise
    
    def _extract_data_characteristics(self, data: DataFrameType) -> Dict[str, Any]:
        """Extract basic data characteristics."""
        try:
            if isinstance(data, pd.DataFrame):
                characteristics = {
                    'total_rows': len(data),
                    'total_columns': len(data.columns),
                    'column_names': list(data.columns),
                    'has_missing_values': data.isnull().any().any(),
                    'numeric_columns': list(data.select_dtypes(include=[np.number]).columns)
                }
                
                # Identify plate information
                if 'PlateID' in data.columns:
                    characteristics['plate_count'] = data['PlateID'].nunique()
                    characteristics['plates'] = list(data['PlateID'].unique())
                
                # Identify well information
                if 'Well' in data.columns:
                    characteristics['well_count'] = data['Well'].nunique()
                
                return characteristics
            else:
                return {'data_type': type(data).__name__, 'structure': 'non_dataframe'}
                
        except Exception as e:
            logger.warning(f"Error extracting data characteristics: {e}")
            return {'error': str(e)}


class LegendManager:
    """Main orchestration class for legend generation and management."""
    
    def __init__(self, config: Optional[LegendConfig] = None):
        """Initialize legend manager with configuration."""
        self.config = config or LegendConfig.default()
        self.context_manager = LegendContext(self.config)
        self._template_registry = None  # Will be set by template system
        
        logger.info("LegendManager initialized")
    
    def create_legend(
        self,
        data: DataFrameType,
        chart_type: ChartType,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
        analysis_config: Optional[Dict[str, Any]] = None,
        custom_content: Optional[Dict[ContentSection, str]] = None
    ) -> LegendContent:
        """Create complete legend content for a visualization."""
        try:
            # Create metadata
            metadata = self.context_manager.create_metadata(
                data, chart_type, expertise_level, analysis_config
            )
            
            # Get template system (imported here to avoid circular imports)
            if self._template_registry is None:
                from .templates import TemplateRegistry
                self._template_registry = TemplateRegistry()
            
            # Generate content using templates
            sections = self._template_registry.generate_content(metadata, custom_content)
            
            # Apply character limits
            sections = self._apply_character_limits(sections, expertise_level)
            
            return LegendContent(
                sections=sections,
                total_char_count=0,  # Will be calculated in __post_init__
                expertise_level=expertise_level,
                chart_type=chart_type
            )
            
        except Exception as e:
            logger.error(f"Error creating legend: {e}")
            raise
    
    def _apply_character_limits(
        self,
        sections: Dict[ContentSection, LegendSection],
        expertise_level: ExpertiseLevel
    ) -> Dict[ContentSection, LegendSection]:
        """Apply character limits based on expertise level."""
        max_chars = self.config.max_char_limits[expertise_level]
        
        # Calculate current total
        total_chars = sum(section.char_count for section in sections.values())
        
        if total_chars <= max_chars:
            return sections
        
        # Need to trim content - prioritize sections
        prioritized_sections = sorted(
            sections.items(),
            key=lambda x: (x[1].priority, -x[1].char_count)
        )
        
        trimmed_sections = {}
        remaining_chars = max_chars
        
        for section_type, section in prioritized_sections:
            if remaining_chars <= 0:
                break
                
            if section.char_count <= remaining_chars:
                trimmed_sections[section_type] = section
                remaining_chars -= section.char_count
            else:
                # Trim this section to fit
                trimmed_content = section.content[:remaining_chars-3] + "..."
                trimmed_sections[section_type] = LegendSection(
                    section_type=section_type,
                    title=section.title,
                    content=trimmed_content,
                    char_count=len(trimmed_content),
                    priority=section.priority
                )
                remaining_chars = 0
        
        logger.info(f"Applied character limits: {total_chars} -> {sum(s.char_count for s in trimmed_sections.values())}")
        return trimmed_sections
    
    def validate_legend(self, legend: LegendContent) -> bool:
        """Validate legend content for completeness and accuracy."""
        try:
            # Check character limits
            max_chars = self.config.max_char_limits[legend.expertise_level]
            if legend.total_char_count > max_chars:
                logger.warning(f"Legend exceeds character limit: {legend.total_char_count} > {max_chars}")
                return False
            
            # Check required sections for expertise level
            required_sections = {
                ExpertiseLevel.BASIC: [ContentSection.BIOLOGICAL_CONTEXT, ContentSection.INTERPRETATION_GUIDE],
                ExpertiseLevel.INTERMEDIATE: [ContentSection.BIOLOGICAL_CONTEXT, ContentSection.STATISTICAL_METHODS, 
                                            ContentSection.INTERPRETATION_GUIDE],
                ExpertiseLevel.EXPERT: [ContentSection.BIOLOGICAL_CONTEXT, ContentSection.STATISTICAL_METHODS,
                                      ContentSection.INTERPRETATION_GUIDE, ContentSection.QUALITY_CONTROL]
            }
            
            required = required_sections.get(legend.expertise_level, [])
            missing = [section for section in required if section not in legend.sections]
            
            if missing:
                logger.warning(f"Missing required sections: {missing}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating legend: {e}")
            return False