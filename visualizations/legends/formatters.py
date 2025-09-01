"""
Output formatters for figure legends.

This module provides formatters that convert LegendContent objects into
format-specific output suitable for different contexts (HTML, PDF, Streamlit, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import html
import re
import logging
from datetime import datetime

from .models import LegendContent, LegendSection, OutputFormat, ExpertiseLevel

logger = logging.getLogger(__name__)


class LegendFormatter(ABC):
    """Abstract base class for legend formatters."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def format(self, legend_content: LegendContent) -> str:
        """Format legend content for specific output type."""
        pass
    
    def _format_section_title(self, title: str) -> str:
        """Format section title. Override in subclasses for specific styling."""
        return title
    
    def _format_section_content(self, content: str, use_bullet_points: bool = False) -> str:
        """Format section content. Override in subclasses for specific styling."""
        if use_bullet_points:
            # Convert bullet point markers to appropriate format
            content = re.sub(r'^•\s*', '• ', content, flags=re.MULTILINE)
        return content
    
    def _should_include_section(self, section: LegendSection, 
                               legend_content: LegendContent) -> bool:
        """Determine if section should be included in output."""
        
        # Check if section has content
        if not section.content or not section.content.strip():
            return False
        
        # Check expertise level compatibility
        expertise_order = {
            ExpertiseLevel.BASIC: 0,
            ExpertiseLevel.INTERMEDIATE: 1,
            ExpertiseLevel.EXPERT: 2
        }
        
        section_level = expertise_order.get(section.expertise_level, 1)
        target_level = expertise_order.get(legend_content.expertise_level, 1)
        
        return section_level <= target_level


class HTMLFormatter(LegendFormatter):
    """HTML formatter for web display."""
    
    def format(self, legend_content: LegendContent) -> str:
        """Format legend as HTML."""
        
        html_parts = ['<div class="figure-legend">']
        
        # Add metadata if available
        if legend_content.metadata:
            html_parts.append(self._format_metadata_html(legend_content.metadata))
        
        # Process sections
        for section in legend_content.sections:
            if self._should_include_section(section, legend_content):
                html_parts.append(self._format_section_html(section))
        
        # Add timestamp
        html_parts.append(f'<div class="legend-timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _format_section_html(self, section: LegendSection) -> str:
        """Format individual section as HTML."""
        
        section_class = f"legend-section legend-{section.section_type.value.replace('_', '-')}"
        
        html_parts = [f'<div class="{section_class}">']
        
        # Add title
        if section.title:
            title_level = 'h4' if section.expertise_level == ExpertiseLevel.EXPERT else 'h5'
            html_parts.append(f'<{title_level} class="section-title">{html.escape(section.title)}</{title_level}>')
        
        # Add content
        content = html.escape(section.content)
        
        if section.use_bullet_points:
            # Convert bullet points to HTML list
            content = self._convert_bullets_to_html_list(content)
            html_parts.append(f'<div class="section-content">{content}</div>')
        else:
            html_parts.append(f'<p class="section-content">{content}</p>')
        
        # Add formulas if present
        if section.include_formulas and '=' in section.content:
            html_parts.append(self._extract_and_format_formulas_html(section.content))
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _convert_bullets_to_html_list(self, content: str) -> str:
        """Convert bullet point text to HTML list."""
        
        lines = content.split('\n')
        list_items = []
        current_item = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('•'):
                if current_item:
                    list_items.append(' '.join(current_item))
                current_item = [line[1:].strip()]  # Remove bullet
            elif line and current_item:
                current_item.append(line)
            elif line and not current_item:
                # Non-bullet text before list
                return content  # Return original if mixed format
        
        if current_item:
            list_items.append(' '.join(current_item))
        
        if list_items:
            items_html = '\n'.join([f'<li>{item}</li>' for item in list_items])
            return f'<ul class="legend-list">\n{items_html}\n</ul>'
        
        return content
    
    def _extract_and_format_formulas_html(self, content: str) -> str:
        """Extract and format mathematical formulas."""
        
        # Simple formula detection (equations with = sign)
        formula_pattern = r'([A-Za-z_]+\s*=\s*[^.]+)'
        formulas = re.findall(formula_pattern, content)
        
        if formulas:
            formula_html = ['<div class="formulas">']
            for formula in formulas:
                # Clean up formula
                clean_formula = formula.strip().rstrip('.,')
                formula_html.append(f'<code class="formula">{html.escape(clean_formula)}</code>')
            formula_html.append('</div>')
            return '\n'.join(formula_html)
        
        return ''
    
    def _format_metadata_html(self, metadata) -> str:
        """Format metadata as HTML."""
        
        if not metadata:
            return ''
        
        meta_parts = ['<div class="legend-metadata">']
        
        if metadata.chart_title:
            meta_parts.append(f'<h3 class="chart-title">{html.escape(metadata.chart_title)}</h3>')
        
        # Add key metadata info
        if metadata.data_shape:
            rows, cols = metadata.data_shape
            meta_parts.append(f'<div class="data-info">Data: {rows:,} wells, {cols} metrics</div>')
        
        if metadata.plate_ids:
            plate_list = ', '.join(metadata.plate_ids)
            meta_parts.append(f'<div class="plate-info">Plates: {html.escape(plate_list)}</div>')
        
        meta_parts.append('</div>')
        
        return '\n'.join(meta_parts)
    
    def get_css_styles(self) -> str:
        """Get CSS styles for HTML legend formatting."""
        
        return """
        <style>
        .figure-legend {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: #333;
            max-width: 800px;
            margin: 20px 0;
        }
        
        .legend-metadata {
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
        }
        
        .chart-title {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 18px;
        }
        
        .data-info, .plate-info {
            font-size: 12px;
            color: #6c757d;
            margin: 5px 0;
        }
        
        .legend-section {
            margin: 15px 0;
        }
        
        .section-title {
            margin: 10px 0 5px 0;
            color: #495057;
            font-size: 16px;
            font-weight: 600;
        }
        
        .section-content {
            margin: 5px 0;
            text-align: justify;
        }
        
        .legend-list {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .legend-list li {
            margin: 5px 0;
        }
        
        .formulas {
            margin: 10px 0;
            padding: 10px;
            background-color: #f1f3f4;
            border-radius: 4px;
        }
        
        .formula {
            display: block;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #1a73e8;
            margin: 5px 0;
            padding: 2px 4px;
            background-color: #e8f4fd;
            border-radius: 3px;
        }
        
        .legend-timestamp {
            font-size: 11px;
            color: #868e96;
            text-align: right;
            margin-top: 15px;
            font-style: italic;
        }
        
        /* Chart-specific styles */
        .legend-description {
            border-left: 3px solid #28a745;
            padding-left: 15px;
        }
        
        .legend-biological-context {
            border-left: 3px solid #17a2b8;
            padding-left: 15px;
        }
        
        .legend-statistical-methods {
            border-left: 3px solid #ffc107;
            padding-left: 15px;
        }
        
        .legend-interpretation {
            border-left: 3px solid #6f42c1;
            padding-left: 15px;
        }
        </style>
        """


class PDFFormatter(LegendFormatter):
    """PDF formatter for report generation."""
    
    def format(self, legend_content: LegendContent) -> str:
        """Format legend for PDF output using LaTeX-style formatting."""
        
        parts = []
        
        # Add title if available
        if legend_content.metadata and legend_content.metadata.chart_title:
            title = legend_content.metadata.chart_title
            parts.append(f"\\textbf{{{self._escape_latex(title)}}}")
            parts.append("")
        
        # Process sections
        for section in legend_content.sections:
            if self._should_include_section(section, legend_content):
                parts.append(self._format_section_pdf(section))
        
        return '\n\n'.join(parts)
    
    def _format_section_pdf(self, section: LegendSection) -> str:
        """Format section for PDF output."""
        
        parts = []
        
        # Add section title
        if section.title:
            if section.expertise_level == ExpertiseLevel.EXPERT:
                parts.append(f"\\textbf{{{self._escape_latex(section.title)}}}")
            else:
                parts.append(f"\\textit{{{self._escape_latex(section.title)}}}")
        
        # Add content
        content = self._escape_latex(section.content)
        
        if section.use_bullet_points:
            content = self._convert_bullets_to_latex_list(content)
        
        # Format formulas
        if section.include_formulas:
            content = self._format_formulas_latex(content)
        
        parts.append(content)
        
        return ' '.join(parts)
    
    def _convert_bullets_to_latex_list(self, content: str) -> str:
        """Convert bullet points to LaTeX list format."""
        
        lines = content.split('\n')
        list_items = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('•'):
                list_items.append(line[1:].strip())
            elif line and not line.startswith('•'):
                # Handle non-bullet content
                if list_items:
                    # End current list and add non-bullet content
                    break
                else:
                    return content  # Not a proper bullet list
        
        if list_items:
            items_latex = '\n'.join([f'\\item {item}' for item in list_items])
            remaining_content = '\n'.join(lines[len(list_items):]).strip()
            
            result = f"\\begin{{itemize}}\n{items_latex}\n\\end{{itemize}}"
            if remaining_content:
                result += f"\n\n{remaining_content}"
            return result
        
        return content
    
    def _format_formulas_latex(self, content: str) -> str:
        """Format mathematical formulas for LaTeX."""
        
        # Replace formula patterns with LaTeX math mode
        formula_pattern = r'([A-Za-z_]+)\s*=\s*([^.]+)'
        
        def replace_formula(match):
            var_name = match.group(1)
            formula = match.group(2).strip()
            return f"${{{var_name}}} = {{{formula}}}$"
        
        return re.sub(formula_pattern, replace_formula, content)
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        
        # LaTeX special characters that need escaping
        escapes = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\textasciicircum{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '\\': r'\textbackslash{}'
        }
        
        for char, escape in escapes.items():
            text = text.replace(char, escape)
        
        return text


class StreamlitFormatter(LegendFormatter):
    """Streamlit formatter for interactive web apps."""
    
    def format(self, legend_content: LegendContent) -> str:
        """Format legend for Streamlit display using markdown."""
        
        parts = []
        
        # Add title
        if legend_content.metadata and legend_content.metadata.chart_title:
            title = legend_content.metadata.chart_title
            parts.append(f"### {title}")
            parts.append("")
        
        # Add metadata info box
        if legend_content.metadata:
            info_box = self._create_streamlit_info_box(legend_content.metadata)
            if info_box:
                parts.append(info_box)
                parts.append("")
        
        # Process sections
        for section in legend_content.sections:
            if self._should_include_section(section, legend_content):
                parts.append(self._format_section_streamlit(section))
        
        # Add collapsible technical details for expert level
        if legend_content.expertise_level == ExpertiseLevel.EXPERT:
            technical_sections = [s for s in legend_content.sections 
                                if s.section_type.value in ['methodology', 'limitations']]
            if technical_sections:
                parts.append(self._create_expandable_section(technical_sections))
        
        return '\n\n'.join(parts)
    
    def _format_section_streamlit(self, section: LegendSection) -> str:
        """Format section for Streamlit markdown."""
        
        parts = []
        
        # Section title with appropriate header level
        if section.title:
            if section.expertise_level == ExpertiseLevel.EXPERT:
                parts.append(f"#### {section.title}")
            else:
                parts.append(f"**{section.title}**")
        
        # Content
        content = section.content
        
        if section.use_bullet_points:
            content = self._format_bullets_for_markdown(content)
        
        # Highlight formulas
        if section.include_formulas:
            content = self._highlight_formulas_markdown(content)
        
        parts.append(content)
        
        return '\n'.join(parts)
    
    def _create_streamlit_info_box(self, metadata) -> str:
        """Create Streamlit info box with metadata."""
        
        if not metadata:
            return ""
        
        info_parts = []
        
        if metadata.data_shape:
            rows, cols = metadata.data_shape
            info_parts.append(f"📊 **Data:** {rows:,} wells, {cols} metrics")
        
        if metadata.plate_ids and len(metadata.plate_ids) > 0:
            plate_info = f"🧫 **Plates:** {len(metadata.plate_ids)} ({', '.join(metadata.plate_ids[:3])}{'...' if len(metadata.plate_ids) > 3 else ''})"
            info_parts.append(plate_info)
        
        if metadata.primary_metrics:
            metrics = ', '.join(metadata.primary_metrics[:3])
            if len(metadata.primary_metrics) > 3:
                metrics += f" (and {len(metadata.primary_metrics) - 3} more)"
            info_parts.append(f"📈 **Metrics:** {metrics}")
        
        if info_parts:
            return f"> {' | '.join(info_parts)}"
        
        return ""
    
    def _format_bullets_for_markdown(self, content: str) -> str:
        """Format bullet points for markdown."""
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('•'):
                # Convert to markdown bullet
                formatted_lines.append(f"- {line[1:].strip()}")
            elif line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _highlight_formulas_markdown(self, content: str) -> str:
        """Highlight formulas in markdown."""
        
        # Wrap formulas in code blocks
        formula_pattern = r'([A-Za-z_]+\s*=\s*[^.]+)'
        
        def highlight_formula(match):
            formula = match.group(1).strip().rstrip('.,')
            return f"`{formula}`"
        
        return re.sub(formula_pattern, highlight_formula, content)
    
    def _create_expandable_section(self, sections: List[LegendSection]) -> str:
        """Create expandable section for technical details."""
        
        if not sections:
            return ""
        
        content_parts = []
        for section in sections:
            content_parts.append(f"**{section.title}**")
            content_parts.append(section.content)
            content_parts.append("")
        
        # This would be used with streamlit.expander in the actual app
        return f"""
---
**🔬 Technical Details** *(Click to expand)*

{chr(10).join(content_parts)}
"""


class MarkdownFormatter(LegendFormatter):
    """Plain Markdown formatter for documentation."""
    
    def format(self, legend_content: LegendContent) -> str:
        """Format legend as plain markdown."""
        
        parts = []
        
        # Title
        if legend_content.metadata and legend_content.metadata.chart_title:
            parts.append(f"# {legend_content.metadata.chart_title}")
            parts.append("")
        
        # Process sections
        for section in legend_content.sections:
            if self._should_include_section(section, legend_content):
                parts.append(self._format_section_markdown(section))
        
        return '\n\n'.join(parts)
    
    def _format_section_markdown(self, section: LegendSection) -> str:
        """Format section as markdown."""
        
        parts = []
        
        if section.title:
            parts.append(f"## {section.title}")
        
        content = section.content
        
        if section.use_bullet_points:
            # Ensure proper bullet formatting
            lines = content.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('•'):
                    formatted_lines.append(f"- {line[1:].strip()}")
                elif line:
                    formatted_lines.append(line)
            
            content = '\n'.join(formatted_lines)
        
        parts.append(content)
        
        return '\n'.join(parts)


class PlainTextFormatter(LegendFormatter):
    """Plain text formatter for simple output."""
    
    def format(self, legend_content: LegendContent) -> str:
        """Format legend as plain text."""
        
        parts = []
        
        # Title
        if legend_content.metadata and legend_content.metadata.chart_title:
            title = legend_content.metadata.chart_title
            parts.append(title)
            parts.append("=" * len(title))
            parts.append("")
        
        # Process sections
        for section in legend_content.sections:
            if self._should_include_section(section, legend_content):
                parts.append(self._format_section_text(section))
        
        return '\n\n'.join(parts)
    
    def _format_section_text(self, section: LegendSection) -> str:
        """Format section as plain text."""
        
        parts = []
        
        if section.title:
            parts.append(section.title.upper())
            parts.append("-" * len(section.title))
        
        # Clean up content
        content = section.content
        
        # Remove HTML/markdown formatting
        content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold markdown
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Remove italic markdown
        
        parts.append(content)
        
        return '\n'.join(parts)


class FormatterFactory:
    """Factory for creating appropriate formatters."""
    
    _formatters = {
        OutputFormat.HTML: HTMLFormatter,
        OutputFormat.PDF: PDFFormatter,
        OutputFormat.STREAMLIT: StreamlitFormatter,
        OutputFormat.MARKDOWN: MarkdownFormatter,
        OutputFormat.PLAIN_TEXT: PlainTextFormatter
    }
    
    @classmethod
    def get_formatter(cls, output_format: OutputFormat, 
                     config: Optional[Dict[str, Any]] = None) -> LegendFormatter:
        """Get appropriate formatter for output format."""
        
        formatter_class = cls._formatters.get(output_format, PlainTextFormatter)
        return formatter_class(config)
    
    @classmethod
    def register_formatter(cls, output_format: OutputFormat, 
                          formatter_class: type):
        """Register custom formatter."""
        cls._formatters[output_format] = formatter_class
    
    @classmethod
    def list_supported_formats(cls) -> List[OutputFormat]:
        """List all supported output formats."""
        return list(cls._formatters.keys())