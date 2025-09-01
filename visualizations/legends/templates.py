"""
Template system for chart-specific legend generation.

This module provides specialized templates for different visualization types,
with expertise-level adaptive content and variable substitution capabilities.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import re

from .models import (
    ChartType, ExpertiseLevel, LegendMetadata, LegendSection, 
    ContentSection, StatisticalContext, BiologicalContext, TechnicalContext
)

logger = logging.getLogger(__name__)


class BaseTemplate(ABC):
    """Abstract base class for chart-specific legend templates."""
    
    def __init__(self, chart_type: ChartType):
        """Initialize template with chart type."""
        self.chart_type = chart_type
    
    @abstractmethod
    def generate_biological_context(
        self, 
        metadata: LegendMetadata
    ) -> Dict[ExpertiseLevel, str]:
        """Generate biological context content for all expertise levels."""
        pass
    
    @abstractmethod
    def generate_statistical_methods(
        self, 
        metadata: LegendMetadata
    ) -> Dict[ExpertiseLevel, str]:
        """Generate statistical methods content for all expertise levels."""
        pass
    
    @abstractmethod
    def generate_interpretation_guide(
        self, 
        metadata: LegendMetadata
    ) -> Dict[ExpertiseLevel, str]:
        """Generate interpretation guide content for all expertise levels."""
        pass
    
    def generate_quality_control(
        self, 
        metadata: LegendMetadata
    ) -> Dict[ExpertiseLevel, str]:
        """Generate quality control content (common across chart types)."""
        tech_ctx = metadata.technical_context
        stat_ctx = metadata.statistical_context
        
        basic = f"Data quality: {stat_ctx.sample_size} samples processed."
        
        intermediate = (
            f"Quality assessment: n={stat_ctx.sample_size} samples. "
            f"{'Edge effects detected - ' if tech_ctx.edge_effects_detected else ''}"
            f"{'B-score correction applied.' if tech_ctx.b_scoring_applied else 'Raw Z-scores used.'}"
        )
        
        expert = (
            f"Multi-dimensional quality control: Sample size n={stat_ctx.sample_size}. "
            f"Edge effects: {'Detected via spatial correlation analysis' if tech_ctx.edge_effects_detected else 'None detected'}. "
            f"Bias correction: {'Applied median-polish B-scoring' if tech_ctx.b_scoring_applied else 'Raw robust Z-scores'}. "
            f"Viability threshold: {tech_ctx.viability_threshold:.1f}× median ATP. "
            f"Processing: {tech_ctx.processing_software} platform."
        )
        
        return {
            ExpertiseLevel.BASIC: basic,
            ExpertiseLevel.INTERMEDIATE: intermediate,
            ExpertiseLevel.EXPERT: expert
        }
    
    def generate_technical_details(
        self, 
        metadata: LegendMetadata
    ) -> Dict[ExpertiseLevel, str]:
        """Generate technical details content (common across chart types)."""
        tech_ctx = metadata.technical_context
        bio_ctx = metadata.biological_context
        
        basic = f"{bio_ctx.assay_type} platform with {tech_ctx.plate_format} plates."
        
        intermediate = (
            f"Platform: {bio_ctx.assay_type} screening using {tech_ctx.plate_format} format. "
            f"Detection: {tech_ctx.detection_method}. "
            f"Normalization: {tech_ctx.normalization_method}."
        )
        
        expert = (
            f"Technical specifications: {bio_ctx.assay_type} outer membrane screening platform. "
            f"Plate format: {tech_ctx.plate_format} ({tech_ctx.detection_method} detection). "
            f"Normalization: {tech_ctx.normalization_method} with viability gating (threshold={tech_ctx.viability_threshold}). "
            f"Data processing: {tech_ctx.processing_software} v1.0 with robust statistical methods."
        )
        
        return {
            ExpertiseLevel.BASIC: basic,
            ExpertiseLevel.INTERMEDIATE: intermediate,
            ExpertiseLevel.EXPERT: expert
        }
    
    def substitute_variables(self, template: str, metadata: LegendMetadata) -> str:
        """Substitute variables in template strings."""
        try:
            stat_ctx = metadata.statistical_context
            bio_ctx = metadata.biological_context
            tech_ctx = metadata.technical_context
            data_chars = metadata.data_characteristics
            
            # Define substitution variables
            variables = {
                'sample_size': str(stat_ctx.sample_size),
                'median_value': f"{stat_ctx.median_value:.3f}" if stat_ctx.median_value else "N/A",
                'mad_value': f"{stat_ctx.mad_value:.3f}" if stat_ctx.mad_value else "N/A",
                'z_min': f"{stat_ctx.z_score_range[0]:.2f}" if stat_ctx.z_score_range else "N/A",
                'z_max': f"{stat_ctx.z_score_range[1]:.2f}" if stat_ctx.z_score_range else "N/A",
                'outlier_count': str(stat_ctx.outlier_count) if stat_ctx.outlier_count else "0",
                'significance_threshold': str(stat_ctx.significance_threshold),
                'reporter_systems': ", ".join(bio_ctx.reporter_systems),
                'strain_types': ", ".join(bio_ctx.strain_types),
                'plate_format': tech_ctx.plate_format,
                'viability_threshold': str(tech_ctx.viability_threshold),
                'b_scoring_status': "applied" if tech_ctx.b_scoring_applied else "not applied",
                'edge_effects_status': "detected" if tech_ctx.edge_effects_detected else "none detected",
                'plate_count': str(data_chars.get('plate_count', 1)),
                'total_wells': str(data_chars.get('total_rows', 0))
            }
            
            # Perform substitutions
            result = template
            for var, value in variables.items():
                result = result.replace(f"{{{var}}}", value)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error substituting variables in template: {e}")
            return template


class HeatmapTemplate(BaseTemplate):
    """Template for heatmap visualization legends."""
    
    def __init__(self):
        super().__init__(ChartType.HEATMAP)
    
    def generate_biological_context(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate biological context for heatmaps."""
        bio_ctx = metadata.biological_context
        
        basic = (
            f"This heatmap shows bacterial stress responses across plate wells. "
            f"Red areas indicate high stress, blue indicates low stress or growth inhibition. "
            f"Each well contains a different compound tested against {bio_ctx.assay_type} reporters."
        )
        
        intermediate = (
            f"Z-score heatmap of {bio_ctx.biological_process} activation using {', '.join(bio_ctx.reporter_systems)} reporters. "
            f"The {bio_ctx.assay_type} platform detects outer membrane disruption through dual stress pathway monitoring "
            f"({', '.join(bio_ctx.stress_pathways)}). Red indicates envelope stress activation, "
            f"blue represents growth inhibition or pathway suppression."
        )
        
        expert = (
            f"Spatial Z-score heatmap of {bio_ctx.biological_process} using {', '.join(bio_ctx.reporter_systems)} "
            f"sentinel reporters. {bio_ctx.reporter_systems[0] if bio_ctx.reporter_systems else 'lptA'} monitors "
            f"σE-regulated LPS transport machinery integrity, while "
            f"{bio_ctx.reporter_systems[1] if len(bio_ctx.reporter_systems) > 1 else 'ldtD'} "
            f"detects Cpx-regulated peptidoglycan remodeling responses. Color intensity reflects statistical "
            f"significance of envelope perturbation, enabling identification of compounds that disrupt "
            f"Gram-negative OM barrier function for {bio_ctx.therapeutic_relevance}."
        )
        
        return {
            ExpertiseLevel.BASIC: self.substitute_variables(basic, metadata),
            ExpertiseLevel.INTERMEDIATE: self.substitute_variables(intermediate, metadata),
            ExpertiseLevel.EXPERT: self.substitute_variables(expert, metadata)
        }
    
    def generate_statistical_methods(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate statistical methods for heatmaps."""
        stat_ctx = metadata.statistical_context
        tech_ctx = metadata.technical_context
        
        basic = (
            f"Colors represent normalized compound effects. Values calculated using robust statistics "
            f"to handle outliers. Red = high effect, blue = low effect, white = average."
        )
        
        intermediate = (
            f"Robust Z-scores calculated using median and MAD: Z = (value - median) / (1.4826 × MAD). "
            f"Range: {stat_ctx.z_score_range[0]:.2f} to {stat_ctx.z_score_range[1]:.2f}. " if stat_ctx.z_score_range else "" +
            f"Values ≥{stat_ctx.significance_threshold} indicate significant activation (p<0.05). "
            f"{'B-score correction applied for systematic bias removal.' if tech_ctx.b_scoring_applied else 'Raw Z-scores displayed.'}"
        )
        
        expert = (
            f"Robust Z-transformation using Hampel identifier with consistency constant 1.4826, "
            f"resistant to {stat_ctx.outlier_count}/{stat_ctx.sample_size} outliers " if stat_ctx.outlier_count else "" +
            f"({(stat_ctx.outlier_count/stat_ctx.sample_size)*100:.1f}% contamination tolerance). " if stat_ctx.outlier_count and stat_ctx.sample_size else "" +
            f"{'Systematic row/column bias corrected via median-polish algorithm (B-scoring) prior to robust scaling. ' if tech_ctx.b_scoring_applied else ''}"
            f"Spatial correlation analysis {'detected' if tech_ctx.edge_effects_detected else 'found no'} "
            f"edge effects. Color scale: diverging blue-white-red centered at Z=0, "
            f"with significance thresholds at ±{stat_ctx.significance_threshold} (95% confidence)."
        )
        
        return {
            ExpertiseLevel.BASIC: self.substitute_variables(basic, metadata),
            ExpertiseLevel.INTERMEDIATE: self.substitute_variables(intermediate, metadata),
            ExpertiseLevel.EXPERT: self.substitute_variables(expert, metadata)
        }
    
    def generate_interpretation_guide(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate interpretation guide for heatmaps."""
        
        basic = (
            "Look for red or dark blue areas as potential hits. Random scattered patterns are good - "
            "avoid systematic patterns like edges or lines which may be technical artifacts. "
            "Each colored square represents one compound test."
        )
        
        intermediate = (
            "Interpretation patterns: (1) Random distribution = genuine bioactive compounds; "
            "(2) Edge enhancement = evaporation artifacts; (3) Row/column streaks = pipetting bias; "
            "(4) Clustered hits = compound similarity or concentration effects. "
            "Strong hits (|Z| ≥ 3) warrant secondary validation."
        )
        
        expert = (
            "Spatial pattern analysis: Genuine hits exhibit random distribution with no positional correlation. "
            "Systematic patterns indicate technical artifacts: peripheral enhancement (evaporation), "
            "linear gradients (thermal/dispensing), quadrant bias (handling). "
            "Moran's I spatial autocorrelation test quantifies pattern significance. "
            "Hit validation hierarchy: |Z| ≥ 3.0 (strong, p<0.001), 2.0-3.0 (moderate, p<0.05), "
            "with cross-validation against orthogonal reporters for mechanism confirmation."
        )
        
        return {
            ExpertiseLevel.BASIC: basic,
            ExpertiseLevel.INTERMEDIATE: intermediate,
            ExpertiseLevel.EXPERT: expert
        }


class HistogramTemplate(BaseTemplate):
    """Template for histogram visualization legends."""
    
    def __init__(self):
        super().__init__(ChartType.HISTOGRAM)
    
    def generate_biological_context(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate biological context for histograms."""
        bio_ctx = metadata.biological_context
        
        basic = (
            f"This histogram shows the distribution of compound effects on bacterial stress responses. "
            f"Most compounds cluster in the center (inactive), with few strong effects on the edges. "
            f"Data from {bio_ctx.assay_type} screening platform."
        )
        
        intermediate = (
            f"Distribution of {bio_ctx.biological_process} measurements from "
            f"{', '.join(bio_ctx.reporter_systems)} dual-reporter system. "
            f"The {bio_ctx.assay_type} platform monitors envelope stress through "
            f"{', '.join(bio_ctx.stress_pathways)} pathways. "
            f"Central peak represents inactive compounds, tail deviations indicate bioactive hits."
        )
        
        expert = (
            f"Frequency distribution of {bio_ctx.biological_process} reporter ratios "
            f"(β-galactosidase/ATP normalization) from {bio_ctx.assay_type} screening. "
            f"Dual-reporter system ({', '.join(bio_ctx.reporter_systems)}) provides orthogonal "
            f"detection of LPS transport stress and peptidoglycan remodeling via "
            f"{', '.join(bio_ctx.stress_pathways)} regulatory networks. "
            f"Distribution shape reflects library composition and biological activity prevalence "
            f"for {bio_ctx.therapeutic_relevance} applications."
        )
        
        return {
            ExpertiseLevel.BASIC: self.substitute_variables(basic, metadata),
            ExpertiseLevel.INTERMEDIATE: self.substitute_variables(intermediate, metadata),
            ExpertiseLevel.EXPERT: self.substitute_variables(expert, metadata)
        }
    
    def generate_statistical_methods(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate statistical methods for histograms."""
        stat_ctx = metadata.statistical_context
        
        basic = (
            f"Shows {stat_ctx.sample_size} measurements. Red line shows the middle value (median). "
            f"Most values cluster around the center, with few extreme values on the sides."
        )
        
        intermediate = (
            f"Distribution of robust Z-scores from {stat_ctx.sample_size} samples. "
            f"Median-centered with MAD-based scaling: Z = (value - median) / (1.4826 × MAD). "
            f"Expected approximately normal distribution after robust normalization. "
            f"Red vertical line indicates median position."
        )
        
        expert = (
            f"Normalized distribution of {stat_ctx.method_used} statistics (n={stat_ctx.sample_size}). "
            f"Robust transformation using median={stat_ctx.median_value:.3f}, " if stat_ctx.median_value else "" +
            f"MAD={stat_ctx.mad_value:.3f}. " if stat_ctx.mad_value else "" +
            f"Hampel identifier with consistency factor 1.4826 for normal-equivalent scaling. "
            f"Outlier tolerance: up to 50% contamination vs. 0% for parametric methods. "
            f"Kolmogorov-Smirnov normality assessment post-transformation. "
            f"Tail analysis: {stat_ctx.outlier_count} extreme outliers (|Z| > 3) " if stat_ctx.outlier_count else "" +
            f"representing potential bioactive compounds."
        )
        
        return {
            ExpertiseLevel.BASIC: self.substitute_variables(basic, metadata),
            ExpertiseLevel.INTERMEDIATE: self.substitute_variables(intermediate, metadata),
            ExpertiseLevel.EXPERT: self.substitute_variables(expert, metadata)
        }
    
    def generate_interpretation_guide(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate interpretation guide for histograms."""
        stat_ctx = metadata.statistical_context
        
        basic = (
            "The main peak shows most compounds are inactive (normal). "
            f"Look for values beyond ±{stat_ctx.significance_threshold} as potential hits. "
            f"Symmetric bell shape indicates good data quality."
        )
        
        intermediate = (
            f"Central distribution represents inactive compounds (|Z| < {stat_ctx.significance_threshold}). "
            f"Right tail (Z ≥ {stat_ctx.significance_threshold}): stress-inducing compounds. "
            f"Left tail (Z ≤ -{stat_ctx.significance_threshold}): growth-inhibiting compounds. "
            f"Bimodal distributions may indicate compound concentration effects or batch variations."
        )
        
        expert = (
            f"Statistical interpretation: Central peak (μ≈0, σ≈1) represents null hypothesis (no effect). "
            f"Significance thresholds: Z ≥ {stat_ctx.significance_threshold} (p<0.05), "
            f"Z ≥ 3.0 (p<0.001, strong hits). "
            f"Distribution deviations from normality indicate: heavy tails (genuine bioactivity), "
            f"skewness (systematic bias), multimodality (subpopulation effects). "
            f"Hit rate estimation: tail probability beyond threshold provides library activity prevalence. "
            f"Quality assessment: approximate normality validates robust normalization effectiveness."
        )
        
        return {
            ExpertiseLevel.BASIC: basic,
            ExpertiseLevel.INTERMEDIATE: intermediate,
            ExpertiseLevel.EXPERT: expert
        }


class ScatterPlotTemplate(BaseTemplate):
    """Template for scatter plot visualization legends."""
    
    def __init__(self):
        super().__init__(ChartType.SCATTER_PLOT)
    
    def generate_biological_context(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate biological context for scatter plots."""
        bio_ctx = metadata.biological_context
        
        basic = (
            f"Each dot represents one compound tested. X and Y axes show different measurements. "
            f"Dots in upper right corner affect both systems - these are priority hits. "
            f"Data from {bio_ctx.assay_type} screening."
        )
        
        intermediate = (
            f"Correlation plot comparing {bio_ctx.biological_process} measurements from dual reporters. "
            f"X-axis: {bio_ctx.reporter_systems[0] if bio_ctx.reporter_systems else 'lptA'} (LPS transport stress), "
            f"Y-axis: {bio_ctx.reporter_systems[1] if len(bio_ctx.reporter_systems) > 1 else 'ldtD'} "
            f"(peptidoglycan remodeling). Strong correlation indicates broad envelope stress; "
            f"weak correlation suggests pathway-specific targeting."
        )
        
        expert = (
            f"Pathway selectivity analysis via {', '.join(bio_ctx.reporter_systems)} reporter correlation. "
            f"X-axis: σE-regulated LPS transport reporter (outer membrane biogenesis). "
            f"Y-axis: Cpx-regulated L,D-transpeptidase reporter (structural compensation). "
            f"Correlation patterns reveal mechanism-of-action: strong positive correlation (r>0.7) = "
            f"general membrane disruptors; weak correlation (r<0.3) = pathway-specific compounds "
            f"with enhanced selectivity for {bio_ctx.therapeutic_relevance}."
        )
        
        return {
            ExpertiseLevel.BASIC: self.substitute_variables(basic, metadata),
            ExpertiseLevel.INTERMEDIATE: self.substitute_variables(intermediate, metadata),
            ExpertiseLevel.EXPERT: self.substitute_variables(expert, metadata)
        }
    
    def generate_statistical_methods(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate statistical methods for scatter plots."""
        stat_ctx = metadata.statistical_context
        
        basic = (
            f"Each point represents one of {stat_ctx.sample_size} compounds. "
            f"Line shows the relationship between measurements. "
            f"Tight clustering around line means measurements are related."
        )
        
        intermediate = (
            f"Correlation analysis of {stat_ctx.sample_size} compounds. "
            f"Pearson correlation coefficient r = {stat_ctx.correlation_coefficient:.3f}" if stat_ctx.correlation_coefficient else "Correlation coefficient calculated" +
            f" indicates linear relationship strength. "
            f"95% confidence interval shown as shaded region around regression line. "
            f"Outliers beyond 2.5×IQR flagged for investigation."
        )
        
        expert = (
            f"Bivariate correlation analysis (n={stat_ctx.sample_size}) with robust outlier detection. "
            f"Pearson r = {stat_ctx.correlation_coefficient:.3f}" if stat_ctx.correlation_coefficient else "Statistical correlation" +
            f" quantifies linear association between orthogonal reporter pathways. "
            f"Spearman rank correlation assessed for non-linear relationships. "
            f"Mahalanobis distance outlier detection identifies compounds with unusual reporter profiles. "
            f"Homoscedasticity evaluation validates correlation assumptions."
        )
        
        return {
            ExpertiseLevel.BASIC: self.substitute_variables(basic, metadata),
            ExpertiseLevel.INTERMEDIATE: self.substitute_variables(intermediate, metadata),
            ExpertiseLevel.EXPERT: self.substitute_variables(expert, metadata)
        }
    
    def generate_interpretation_guide(self, metadata: LegendMetadata) -> Dict[ExpertiseLevel, str]:
        """Generate interpretation guide for scatter plots."""
        
        basic = (
            "Upper right quadrant: compounds affecting both systems (priority hits). "
            "Lower left quadrant: inactive compounds. "
            "Upper left/lower right: selective compounds affecting only one system."
        )
        
        intermediate = (
            "Quadrant analysis: (1) Upper right = dual-positive hits (broad envelope stress); "
            "(2) Lower left = dual-negative (inactive/growth inhibitors); "
            "(3) Off-diagonal = pathway-selective compounds. "
            "Strong correlation suggests general membrane disruptors; weak correlation indicates selectivity."
        )
        
        expert = (
            "Mechanistic interpretation via quadrant analysis: Q1 (upper right) = broad-spectrum "
            "envelope disruptors with potential for combination therapy; Q3 (lower left) = "
            "growth inhibitors or inactive compounds; Q2/Q4 (off-diagonal) = pathway-selective "
            "compounds with mechanism specificity. Correlation strength (r) indicates: "
            "r>0.7 (general membrane disruption), 0.3<r<0.7 (mixed mechanisms), "
            "r<0.3 (pathway-specific targeting with enhanced therapeutic index)."
        )
        
        return {
            ExpertiseLevel.BASIC: basic,
            ExpertiseLevel.INTERMEDIATE: intermediate,
            ExpertiseLevel.EXPERT: expert
        }


class TemplateRegistry:
    """Registry for managing chart-specific templates."""
    
    def __init__(self):
        """Initialize template registry with default templates."""
        self.templates: Dict[ChartType, BaseTemplate] = {
            ChartType.HEATMAP: HeatmapTemplate(),
            ChartType.HISTOGRAM: HistogramTemplate(),
            ChartType.SCATTER_PLOT: ScatterPlotTemplate(),
            # Add more templates as needed
        }
        
        logger.info(f"TemplateRegistry initialized with {len(self.templates)} templates")
    
    def register_template(self, chart_type: ChartType, template: BaseTemplate):
        """Register a new template for a chart type."""
        self.templates[chart_type] = template
        logger.info(f"Registered template for {chart_type}")
    
    def get_template(self, chart_type: ChartType) -> Optional[BaseTemplate]:
        """Get template for specific chart type."""
        return self.templates.get(chart_type)
    
    def generate_content(
        self, 
        metadata: LegendMetadata,
        custom_content: Optional[Dict[ContentSection, str]] = None
    ) -> Dict[ContentSection, LegendSection]:
        """Generate complete legend content using appropriate template."""
        try:
            template = self.get_template(metadata.chart_type)
            if not template:
                raise ValueError(f"No template available for chart type: {metadata.chart_type}")
            
            sections = {}
            
            # Generate biological context
            bio_content = template.generate_biological_context(metadata)
            sections[ContentSection.BIOLOGICAL_CONTEXT] = LegendSection(
                section_type=ContentSection.BIOLOGICAL_CONTEXT,
                title="🔬 Biological Context",
                content=bio_content[metadata.expertise_level],
                char_count=0,  # Will be calculated in __post_init__
                priority=1
            )
            
            # Generate statistical methods
            stat_content = template.generate_statistical_methods(metadata)
            sections[ContentSection.STATISTICAL_METHODS] = LegendSection(
                section_type=ContentSection.STATISTICAL_METHODS,
                title="📊 Statistical Methods",
                content=stat_content[metadata.expertise_level],
                char_count=0,
                priority=2
            )
            
            # Generate interpretation guide
            interp_content = template.generate_interpretation_guide(metadata)
            sections[ContentSection.INTERPRETATION_GUIDE] = LegendSection(
                section_type=ContentSection.INTERPRETATION_GUIDE,
                title="🎯 Interpretation Guide",
                content=interp_content[metadata.expertise_level],
                char_count=0,
                priority=1
            )
            
            # Generate quality control (if needed)
            if metadata.expertise_level in [ExpertiseLevel.INTERMEDIATE, ExpertiseLevel.EXPERT]:
                qc_content = template.generate_quality_control(metadata)
                sections[ContentSection.QUALITY_CONTROL] = LegendSection(
                    section_type=ContentSection.QUALITY_CONTROL,
                    title="⚙️ Quality Control",
                    content=qc_content[metadata.expertise_level],
                    char_count=0,
                    priority=2
                )
            
            # Generate technical details (if expert level)
            if metadata.expertise_level == ExpertiseLevel.EXPERT:
                tech_content = template.generate_technical_details(metadata)
                sections[ContentSection.TECHNICAL_DETAILS] = LegendSection(
                    section_type=ContentSection.TECHNICAL_DETAILS,
                    title="🧮 Technical Details",
                    content=tech_content[metadata.expertise_level],
                    char_count=0,
                    priority=3
                )
            
            # Apply custom content if provided
            if custom_content:
                for section_type, content in custom_content.items():
                    if section_type in sections:
                        sections[section_type].content = content
            
            return sections
            
        except Exception as e:
            logger.error(f"Error generating legend content: {e}")
            raise