"""
Output formatters for different display formats.

This module provides formatters that convert legend content into various output
formats including Streamlit markdown, HTML, PDF, and plain text.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from .models import (
    LegendContent, LegendSection, ContentSection, ExpertiseLevel, 
    OutputFormat, ChartType
)

logger = logging.getLogger(__name__)


class BaseFormatter(ABC):
    """Abstract base class for legend formatters."""
    
    def __init__(self, output_format: OutputFormat):
        """Initialize formatter with output format."""
        self.output_format = output_format
    
    @abstractmethod
    def format_legend(self, legend: LegendContent, **kwargs) -> str:
        """Format complete legend content."""
        pass
    
    @abstractmethod
    def format_section(self, section: LegendSection, **kwargs) -> str:
        """Format individual legend section."""
        pass
    
    def format_title(self, title: str, level: int = 1, **kwargs) -> str:
        """Format section titles (to be overridden by subclasses)."""
        return title


class StreamlitFormatter(BaseFormatter):
    """Formatter for Streamlit markdown output with interactive components."""
    
    def __init__(self):
        super().__init__(OutputFormat.STREAMLIT)
        self.icon_map = {
            ContentSection.BIOLOGICAL_CONTEXT: "🔬",
            ContentSection.STATISTICAL_METHODS: "📊", 
            ContentSection.INTERPRETATION_GUIDE: "🎯",
            ContentSection.QUALITY_CONTROL: "⚙️",
            ContentSection.TECHNICAL_DETAILS: "🧮",
            ContentSection.REFERENCES: "📚",
            ContentSection.LIMITATIONS: "⚠️"
        }
    
    def format_legend(
        self, 
        legend: LegendContent, 
        layout: str = "tabs",
        show_expertise_selector: bool = True,
        expand_by_default: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Format legend for Streamlit display with interactive options.
        
        Args:
            legend: Legend content to format
            layout: 'tabs', 'expander', 'columns', or 'sequential'
            show_expertise_selector: Whether to include expertise level selector
            expand_by_default: Whether expandable sections start expanded
            
        Returns:
            Dictionary with formatted content and display instructions
        """
        try:
            formatted_sections = {}
            display_config = {
                'layout': layout,
                'expertise_level': legend.expertise_level.value,
                'chart_type': legend.chart_type.value,
                'total_char_count': legend.total_char_count,
                'expand_by_default': expand_by_default
            }
            
            # Format each section
            for section_type, section in legend.sections.items():
                formatted_sections[section_type.value] = {
                    'title': self._format_section_title(section),
                    'content': self._format_section_content(section),
                    'icon': self.icon_map.get(section_type, "📋"),
                    'priority': section.priority,
                    'char_count': section.char_count
                }
            
            # Add metadata
            if show_expertise_selector:
                display_config['expertise_options'] = [
                    "Basic", "Intermediate", "Expert"
                ]
                display_config['current_expertise'] = legend.expertise_level.value.title()
            
            return {
                'sections': formatted_sections,
                'config': display_config,
                'summary': self._create_summary(legend)
            }
            
        except Exception as e:
            logger.error(f"Error formatting legend for Streamlit: {e}")
            return {'error': str(e)}
    
    def format_section(self, section: LegendSection, **kwargs) -> str:
        """Format individual section for Streamlit markdown."""
        title = self._format_section_title(section)
        content = self._format_section_content(section)
        return f"**{title}**\n\n{content}"
    
    def create_expandable_legend(
        self, 
        legend: LegendContent,
        title: str = "📖 Figure Legend",
        expanded: bool = False
    ) -> str:
        """Create expandable legend content for st.expander()."""
        sections_text = []
        
        # Sort sections by priority
        sorted_sections = sorted(
            legend.sections.items(),
            key=lambda x: (x[1].priority, x[0].value)
        )
        
        for section_type, section in sorted_sections:
            icon = self.icon_map.get(section_type, "📋")
            formatted_section = f"**{icon} {section.title.replace('🔬 ', '').replace('📊 ', '').replace('🎯 ', '').replace('⚙️ ', '').replace('🧮 ', '')}**\n\n{section.content}\n\n"
            sections_text.append(formatted_section)
        
        return "".join(sections_text).strip()
    
    def create_tabbed_legend(self, legend: LegendContent) -> Dict[str, str]:
        """Create content for st.tabs() display."""
        tab_content = {}
        
        # Priority-based tab ordering
        priority_sections = legend.get_priority_sections(max_priority=1)
        secondary_sections = legend.get_priority_sections(max_priority=2)
        all_sections = legend.get_priority_sections(max_priority=3)
        
        # Main tabs (priority 1)
        for section_type, section in priority_sections.items():
            clean_title = section.title.split(' ', 1)[-1]  # Remove emoji
            tab_content[clean_title] = section.content
        
        # Additional tab for secondary content if present
        if len(secondary_sections) > len(priority_sections):
            additional_content = []
            for section_type, section in secondary_sections.items():
                if section_type not in priority_sections:
                    additional_content.append(f"**{section.title}**\n\n{section.content}")
            
            if additional_content:
                tab_content["Details"] = "\n\n---\n\n".join(additional_content)
        
        return tab_content
    
    def _format_section_title(self, section: LegendSection) -> str:
        """Format section title for Streamlit."""
        return section.title
    
    def _format_section_content(self, section: LegendSection) -> str:
        """Format section content for Streamlit markdown."""
        content = section.content
        
        # Enhance formulas for better Streamlit display
        content = re.sub(r'Z = \((.*?)\)', r'**Z = (\1)**', content)
        content = re.sub(r'r = ([\d.]+)', r'**r = \1**', content)
        content = re.sub(r'p<([\d.]+)', r'*p* < \1', content)
        content = re.sub(r'n=(\d+)', r'*n* = \1', content)
        
        # Add emphasis to key terms
        content = re.sub(r'σE', r'**σE**', content)
        content = re.sub(r'Cpx', r'**Cpx**', content)
        content = re.sub(r'BREAKthrough', r'**BREAKthrough**', content)
        content = re.sub(r'MAD', r'**MAD**', content)
        
        return content
    
    def _create_summary(self, legend: LegendContent) -> str:
        """Create a brief summary of the legend."""
        expertise_label = legend.expertise_level.value.title()
        section_count = len(legend.sections)
        
        return (f"*{expertise_label} level explanation with {section_count} sections "
                f"({legend.total_char_count} characters)*")


class HTMLFormatter(BaseFormatter):
    """Formatter for HTML output with CSS styling."""
    
    def __init__(self):
        super().__init__(OutputFormat.HTML)
        self.css_classes = {
            ContentSection.BIOLOGICAL_CONTEXT: "legend-bio",
            ContentSection.STATISTICAL_METHODS: "legend-stats",
            ContentSection.INTERPRETATION_GUIDE: "legend-interpret",
            ContentSection.QUALITY_CONTROL: "legend-qc",
            ContentSection.TECHNICAL_DETAILS: "legend-tech",
            ContentSection.REFERENCES: "legend-refs",
            ContentSection.LIMITATIONS: "legend-limits"
        }
    
    def format_legend(
        self, 
        legend: LegendContent,
        include_css: bool = True,
        container_class: str = "figure-legend",
        **kwargs
    ) -> str:
        """Format legend as HTML with CSS styling."""
        try:
            sections_html = []
            
            # Sort sections by priority
            sorted_sections = sorted(
                legend.sections.items(),
                key=lambda x: (x[1].priority, x[0].value)
            )
            
            for section_type, section in sorted_sections:
                section_html = self.format_section(section, section_type=section_type)
                sections_html.append(section_html)
            
            # Combine into complete HTML
            legend_html = f'''
            <div class="{container_class} expertise-{legend.expertise_level.value}">
                <div class="legend-header">
                    <h3>Figure Legend</h3>
                    <span class="expertise-badge">{legend.expertise_level.value.title()} Level</span>
                </div>
                <div class="legend-content">
                    {"".join(sections_html)}
                </div>
                <div class="legend-footer">
                    <small>{len(legend.sections)} sections • {legend.total_char_count} characters</small>
                </div>
            </div>
            '''
            
            if include_css:
                css = self._get_default_css()
                return f"<style>{css}</style>\n{legend_html}"
            else:
                return legend_html
                
        except Exception as e:
            logger.error(f"Error formatting legend as HTML: {e}")
            return f'<div class="error">Error formatting legend: {e}</div>'
    
    def format_section(self, section: LegendSection, section_type: ContentSection = None, **kwargs) -> str:
        """Format individual section as HTML."""
        css_class = self.css_classes.get(section_type, "legend-section")
        
        # Extract emoji from title for separate styling
        title_parts = section.title.split(' ', 1)
        if len(title_parts) == 2 and title_parts[0] in ['🔬', '📊', '🎯', '⚙️', '🧮', '📚', '⚠️']:
            emoji, title_text = title_parts
            title_html = f'<span class="section-icon">{emoji}</span><span class="section-title">{title_text}</span>'
        else:
            title_html = section.title
        
        # Format content with enhanced markup
        content = self._enhance_content_markup(section.content)
        
        return f'''
        <div class="{css_class}" data-priority="{section.priority}">
            <h4 class="section-header">{title_html}</h4>
            <div class="section-content">{content}</div>
            <div class="section-meta">
                <span class="char-count">{section.char_count} chars</span>
            </div>
        </div>
        '''
    
    def _enhance_content_markup(self, content: str) -> str:
        """Enhance content with HTML markup for better display."""
        # Convert scientific notation and formulas
        content = re.sub(r'Z = \((.*?)\)', r'<strong>Z = (\1)</strong>', content)
        content = re.sub(r'r = ([\d.]+)', r'<strong>r = \1</strong>', content)
        content = re.sub(r'p<([\d.]+)', r'<em>p</em> &lt; \1', content)
        content = re.sub(r'n=(\d+)', r'<em>n</em> = \1', content)
        
        # Scientific terms
        content = re.sub(r'σE', r'<strong>σE</strong>', content)
        content = re.sub(r'Cpx', r'<strong>Cpx</strong>', content)
        content = re.sub(r'BREAKthrough', r'<strong>BREAKthrough</strong>', content)
        content = re.sub(r'\bMAD\b', r'<strong>MAD</strong>', content)
        
        # Convert line breaks
        content = content.replace('\n', '<br>')
        
        return content
    
    def _get_default_css(self) -> str:
        """Get default CSS styles for legend display."""
        return """
        .figure-legend {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
        }
        
        .legend-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }
        
        .legend-header h3 {
            margin: 0;
            color: #495057;
            font-size: 1.25rem;
        }
        
        .expertise-badge {
            background: #007bff;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .expertise-basic .expertise-badge { background: #28a745; }
        .expertise-intermediate .expertise-badge { background: #ffc107; color: #212529; }
        .expertise-expert .expertise-badge { background: #dc3545; }
        
        .legend-section {
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        
        .legend-bio { border-left-color: #28a745; }
        .legend-stats { border-left-color: #007bff; }
        .legend-interpret { border-left-color: #17a2b8; }
        .legend-qc { border-left-color: #ffc107; }
        .legend-tech { border-left-color: #6f42c1; }
        .legend-refs { border-left-color: #fd7e14; }
        .legend-limits { border-left-color: #dc3545; }
        
        .section-header {
            margin: 0 0 10px 0;
            color: #343a40;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .section-icon {
            font-size: 1.2rem;
        }
        
        .section-content {
            color: #495057;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .section-meta {
            text-align: right;
            color: #6c757d;
            font-size: 0.8rem;
        }
        
        .legend-footer {
            text-align: center;
            color: #6c757d;
            font-size: 0.875rem;
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #dee2e6;
        }
        
        /* Priority-based opacity */
        .legend-section[data-priority="3"] {
            opacity: 0.85;
        }
        """


class PDFFormatter(BaseFormatter):
    """Formatter for PDF output with LaTeX-compatible formatting."""
    
    def __init__(self):
        super().__init__(OutputFormat.PDF)
        self.section_numbering = {
            ContentSection.BIOLOGICAL_CONTEXT: "1",
            ContentSection.STATISTICAL_METHODS: "2",
            ContentSection.INTERPRETATION_GUIDE: "3",
            ContentSection.QUALITY_CONTROL: "4",
            ContentSection.TECHNICAL_DETAILS: "5",
            ContentSection.REFERENCES: "6",
            ContentSection.LIMITATIONS: "7"
        }
    
    def format_legend(
        self, 
        legend: LegendContent,
        include_header: bool = True,
        figure_number: str = "1",
        **kwargs
    ) -> str:
        """Format legend for PDF inclusion with LaTeX compatibility."""
        try:
            sections_text = []
            
            if include_header:
                header = self._create_pdf_header(legend, figure_number)
                sections_text.append(header)
            
            # Sort sections by priority and format
            sorted_sections = sorted(
                legend.sections.items(),
                key=lambda x: (x[1].priority, self.section_numbering.get(x[0], "9"))
            )
            
            for i, (section_type, section) in enumerate(sorted_sections, 1):
                section_text = self.format_section(
                    section, 
                    number=str(i),
                    section_type=section_type
                )
                sections_text.append(section_text)
            
            return "\n\n".join(sections_text)
            
        except Exception as e:
            logger.error(f"Error formatting legend for PDF: {e}")
            return f"Error formatting legend: {e}"
    
    def format_section(self, section: LegendSection, number: str = "", section_type: ContentSection = None, **kwargs) -> str:
        """Format individual section for PDF."""
        # Clean title for LaTeX (remove emojis, format properly)
        clean_title = re.sub(r'[🔬📊🎯⚙️🧮📚⚠️]\s*', '', section.title)
        
        # Format content for LaTeX compatibility
        content = self._format_content_for_latex(section.content)
        
        # Create numbered subsection
        if number:
            return f"\\textbf{{{number}. {clean_title}}}\n\n{content}"
        else:
            return f"\\textbf{{{clean_title}}}\n\n{content}"
    
    def _create_pdf_header(self, legend: LegendContent, figure_number: str) -> str:
        """Create PDF header with figure information."""
        chart_type = legend.chart_type.value.replace('_', ' ').title()
        expertise = legend.expertise_level.value.title()
        
        return (f"\\textbf{{Figure {figure_number} Legend: {chart_type} Analysis}} "
                f"\\emph{{({expertise} Level Explanation)}}")
    
    def _format_content_for_latex(self, content: str) -> str:
        """Format content for LaTeX compatibility."""
        # Escape special LaTeX characters
        latex_escapes = {
            '#': '\\#',
            '$': '\\$', 
            '%': '\\%',
            '&': '\\&',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '^': '\\textasciicircum{}',
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }
        
        for char, escape in latex_escapes.items():
            content = content.replace(char, escape)
        
        # Format mathematical expressions
        content = re.sub(r'Z = \((.*?)\)', r'$Z = (\1)$', content)
        content = re.sub(r'r = ([\d.]+)', r'$r = \1$', content)
        content = re.sub(r'p<([\d.]+)', r'$p < \1$', content)
        content = re.sub(r'n=(\d+)', r'$n = \1$', content)
        
        # Format Greek letters
        content = content.replace('σE', '$\\sigma$E')
        content = content.replace('≥', '$\\geq$')
        content = content.replace('≤', '$\\leq$')
        content = content.replace('×', '$\\times$')
        
        # Emphasize key terms
        content = re.sub(r'\bBREAKthrough\b', r'\\textbf{BREAKthrough}', content)
        content = re.sub(r'\bMAD\b', r'\\textbf{MAD}', content)
        content = re.sub(r'\bCpx\b', r'\\textbf{Cpx}', content)
        
        return content


class PlainTextFormatter(BaseFormatter):
    """Formatter for plain text output."""
    
    def __init__(self):
        super().__init__(OutputFormat.PLAIN_TEXT)
    
    def format_legend(self, legend: LegendContent, width: int = 80, **kwargs) -> str:
        """Format legend as plain text with specified line width."""
        try:
            lines = []
            
            # Header
            title = f"FIGURE LEGEND ({legend.expertise_level.value.upper()} LEVEL)"
            lines.append("=" * width)
            lines.append(title.center(width))
            lines.append("=" * width)
            lines.append("")
            
            # Sections
            sorted_sections = sorted(
                legend.sections.items(),
                key=lambda x: (x[1].priority, x[0].value)
            )
            
            for i, (section_type, section) in enumerate(sorted_sections, 1):
                section_text = self.format_section(section, number=i, width=width)
                lines.append(section_text)
                lines.append("")  # Blank line between sections
            
            # Footer
            lines.append("-" * width)
            lines.append(f"Total: {len(legend.sections)} sections, {legend.total_char_count} characters".center(width))
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting legend as plain text: {e}")
            return f"Error formatting legend: {e}"
    
    def format_section(self, section: LegendSection, number: int = None, width: int = 80, **kwargs) -> str:
        """Format individual section as plain text."""
        # Clean title
        clean_title = re.sub(r'[🔬📊🎯⚙️🧮📚⚠️]\s*', '', section.title).upper()
        
        # Section header
        if number:
            header = f"{number}. {clean_title}"
        else:
            header = clean_title
            
        lines = [header, "-" * len(header)]
        
        # Wrap content to specified width
        content = section.content
        words = content.split()
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    lines.append(word)  # Word is longer than width
            else:
                current_line.append(word)
                current_length += len(word) + (1 if current_line else 0)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)


class MarkdownFormatter(BaseFormatter):
    """Formatter for Markdown output."""
    
    def __init__(self):
        super().__init__(OutputFormat.MARKDOWN)
    
    def format_legend(self, legend: LegendContent, **kwargs) -> str:
        """Format legend as Markdown."""
        try:
            lines = []
            
            # Header
            lines.append(f"# Figure Legend")
            lines.append(f"*{legend.expertise_level.value.title()} Level • {legend.chart_type.value.replace('_', ' ').title()}*")
            lines.append("")
            
            # Sections
            sorted_sections = sorted(
                legend.sections.items(),
                key=lambda x: (x[1].priority, x[0].value)
            )
            
            for section_type, section in sorted_sections:
                section_md = self.format_section(section)
                lines.append(section_md)
                lines.append("")
            
            # Footer
            lines.append("---")
            lines.append(f"*{len(legend.sections)} sections • {legend.total_char_count} characters*")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting legend as Markdown: {e}")
            return f"**Error formatting legend:** {e}"
    
    def format_section(self, section: LegendSection, **kwargs) -> str:
        """Format individual section as Markdown."""
        # Use title as-is (includes emoji)
        title = section.title
        content = section.content
        
        # Enhance content formatting
        content = re.sub(r'Z = \((.*?)\)', r'**Z = (\1)**', content)
        content = re.sub(r'r = ([\d.]+)', r'**r = \1**', content) 
        content = re.sub(r'p<([\d.]+)', r'*p* < \1', content)
        content = re.sub(r'n=(\d+)', r'*n* = \1', content)
        
        # Scientific terms
        content = re.sub(r'σE', r'**σE**', content)
        content = re.sub(r'Cpx', r'**Cpx**', content)
        content = re.sub(r'BREAKthrough', r'**BREAKthrough**', content)
        content = re.sub(r'\bMAD\b', r'**MAD**', content)
        
        return f"## {title}\n\n{content}"


# Formatter factory function
def get_formatter(output_format: OutputFormat) -> BaseFormatter:
    """Get appropriate formatter for output format."""
    formatters = {
        OutputFormat.STREAMLIT: StreamlitFormatter,
        OutputFormat.HTML: HTMLFormatter,
        OutputFormat.PDF: PDFFormatter,
        OutputFormat.PLAIN_TEXT: PlainTextFormatter,
        OutputFormat.MARKDOWN: MarkdownFormatter
    }
    
    formatter_class = formatters.get(output_format)
    if not formatter_class:
        raise ValueError(f"No formatter available for output format: {output_format}")
    
    return formatter_class()