"""Quality Control Dashboard for the BREAKthrough OM screening platform."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

from .base import BaseVisualization, QCMetricsCalculator


class QCDashboard(BaseVisualization):
    """Quality Control Dashboard with real-time monitoring capabilities."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.calculator = QCMetricsCalculator()
    
    def create_figure(self, data: pd.DataFrame, **kwargs) -> go.Figure:
        """Create main QC dashboard figure with multiple metrics."""
        # This is the main entry point that creates the dashboard
        plate_metrics = self.calculate_plate_metrics(data)
        return self.create_metrics_overview(plate_metrics)
    
    def calculate_plate_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive QC metrics for the plate."""
        metrics = {}
        
        # Identify control wells (assuming they're marked or can be identified)
        # For now, using well positions - this can be made configurable
        control_wells = self._identify_control_wells(data)
        
        # Calculate metrics for each reporter
        for reporter in ['lptA', 'ldtD']:
            if f'Z_{reporter}' in data.columns and f'Ratio_{reporter}' in data.columns:
                reporter_metrics = self._calculate_reporter_metrics(data, reporter, control_wells)
                metrics[reporter] = reporter_metrics
        
        # Calculate overall plate metrics
        metrics['overall'] = self._calculate_overall_metrics(data, control_wells)
        
        # Detect alerts
        metrics['alerts'] = self._detect_all_alerts(metrics)
        
        return metrics
    
    def _identify_control_wells(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """Identify control wells based on well positions."""
        # Standard control well positions for 384-well plates
        # This should be made configurable via config
        positive_controls = []
        negative_controls = []
        
        if 'Well' in data.columns:
            # Typical control positions (can be customized)
            wells = data['Well'].tolist()
            
            # Positive controls often in specific positions
            for well in wells:
                if well in ['A1', 'A2', 'A23', 'A24', 'P1', 'P2', 'P23', 'P24']:
                    positive_controls.append(well)
                elif well in ['B1', 'B2', 'B23', 'B24', 'O1', 'O2', 'O23', 'O24']:
                    negative_controls.append(well)
        
        return {
            'positive': positive_controls,
            'negative': negative_controls
        }
    
    def _calculate_reporter_metrics(self, data: pd.DataFrame, reporter: str, 
                                  control_wells: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate QC metrics for a specific reporter."""
        ratio_col = f'Ratio_{reporter}'
        z_col = f'Z_{reporter}'
        
        metrics = {}
        
        # Get control well data
        pos_controls = data[data['Well'].isin(control_wells['positive'])][ratio_col].dropna()
        neg_controls = data[data['Well'].isin(control_wells['negative'])][ratio_col].dropna()
        
        # Calculate Z-factor
        metrics['z_factor'] = self.calculator.calculate_z_factor(pos_controls, neg_controls)
        
        # Calculate S:B ratio
        metrics['sb_ratio'] = self.calculator.calculate_signal_to_background(pos_controls, neg_controls)
        
        # Calculate CV% for controls
        metrics['pos_cv'] = self.calculator.calculate_cv_percent(pos_controls)
        metrics['neg_cv'] = self.calculator.calculate_cv_percent(neg_controls)
        
        # Calculate overall metrics
        all_ratios = data[ratio_col].dropna()
        metrics['median_ratio'] = all_ratios.median()
        metrics['mad_ratio'] = np.median(np.abs(all_ratios - metrics['median_ratio'])) * 1.4826
        
        # Z-score metrics
        if z_col in data.columns:
            z_scores = data[z_col].dropna()
            metrics['z_score_range'] = z_scores.max() - z_scores.min()
            metrics['outlier_count'] = len(z_scores[np.abs(z_scores) > 3])
        
        return metrics
    
    def _calculate_overall_metrics(self, data: pd.DataFrame, control_wells: Dict[str, List[str]]) -> Dict[str, Any]:
        """Calculate overall plate-level metrics."""
        metrics = {}
        
        # Viability metrics
        if 'ATP' in data.columns:
            atp_data = data['ATP'].dropna()
            metrics['viability_median'] = atp_data.median()
            metrics['viability_cv'] = self.calculator.calculate_cv_percent(atp_data)
        
        # Edge effect metrics (if available)
        if 'Row' in data.columns and 'Column' in data.columns:
            metrics['edge_wells'] = len(data[(data['Row'].isin([1, 16])) | (data['Column'].isin([1, 24]))])
            metrics['total_wells'] = len(data)
            metrics['edge_percentage'] = (metrics['edge_wells'] / metrics['total_wells']) * 100
        
        # Hit calling metrics
        hit_columns = ['reporter_hit', 'vitality_hit', 'platform_hit']
        for col in hit_columns:
            if col in data.columns:
                metrics[f'{col}_count'] = data[col].sum()
                metrics[f'{col}_rate'] = (data[col].sum() / len(data)) * 100
        
        return metrics
    
    def _detect_all_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect all QC alerts across all metrics."""
        alerts = []
        
        # Reporter-specific alerts
        for reporter in ['lptA', 'ldtD']:
            if reporter in metrics:
                reporter_alerts = self.calculator.detect_qc_alerts(
                    metrics[reporter].get('z_factor', np.nan),
                    metrics[reporter].get('sb_ratio', np.nan),
                    metrics[reporter].get('pos_cv', np.nan),
                    self.config
                )
                for alert in reporter_alerts:
                    alert['reporter'] = reporter
                    alerts.append(alert)
        
        # Overall alerts
        overall = metrics.get('overall', {})
        if overall.get('viability_cv', 0) > 30:
            alerts.append({'message': f"High viability CV%: {overall['viability_cv']:.1f}%", 'severity': 'medium'})
        
        return alerts
    
    def create_metrics_overview(self, metrics: Dict[str, Any]) -> go.Figure:
        """Create comprehensive metrics overview figure."""
        # Create subplots for different metric categories
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[
                'Z-Factor Performance', 'Signal-to-Background Ratios', 'Control CV%',
                'Hit Rates', 'Quality Alerts', 'Plate Summary'
            ],
            specs=[
                [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "table"}, {"type": "indicator"}]
            ]
        )
        
        # Z-Factor plot
        if 'lptA' in metrics and 'ldtD' in metrics:
            reporters = ['lptA', 'ldtD']
            z_factors = [metrics[r].get('z_factor', 0) for r in reporters]
            
            fig.add_trace(
                go.Bar(
                    x=reporters,
                    y=z_factors,
                    name='Z-Factor',
                    marker_color=['green' if z > 0.5 else 'orange' if z > 0 else 'red' for z in z_factors],
                    text=[f'{z:.3f}' for z in z_factors],
                    textposition='auto'
                ),
                row=1, col=1
            )
            
            # Add Z-factor reference lines
            fig.add_hline(y=0.5, line_dash="dash", line_color="green", 
                         annotation_text="Excellent (≥0.5)", row=1, col=1)
            fig.add_hline(y=0.0, line_dash="dash", line_color="orange", 
                         annotation_text="Marginal (0-0.5)", row=1, col=1)
        
        # S:B Ratio plot
        if 'lptA' in metrics and 'ldtD' in metrics:
            sb_ratios = [metrics[r].get('sb_ratio', 0) for r in reporters]
            
            fig.add_trace(
                go.Bar(
                    x=reporters,
                    y=sb_ratios,
                    name='S:B Ratio',
                    marker_color=['green' if sb > 3 else 'orange' for sb in sb_ratios],
                    text=[f'{sb:.2f}' for sb in sb_ratios],
                    textposition='auto'
                ),
                row=1, col=2
            )
        
        # Control CV% plot
        if 'lptA' in metrics and 'ldtD' in metrics:
            pos_cvs = [metrics[r].get('pos_cv', 0) for r in reporters]
            neg_cvs = [metrics[r].get('neg_cv', 0) for r in reporters]
            
            fig.add_trace(
                go.Bar(
                    x=reporters,
                    y=pos_cvs,
                    name='Positive CV%',
                    marker_color='lightblue',
                    text=[f'{cv:.1f}%' for cv in pos_cvs],
                    textposition='auto'
                ),
                row=1, col=3
            )
            
            fig.add_trace(
                go.Bar(
                    x=reporters,
                    y=neg_cvs,
                    name='Negative CV%',
                    marker_color='lightcoral',
                    text=[f'{cv:.1f}%' for cv in neg_cvs],
                    textposition='auto'
                ),
                row=1, col=3
            )
        
        # Hit rates plot
        overall = metrics.get('overall', {})
        hit_types = ['Reporter', 'Vitality', 'Platform']
        hit_rates = [
            overall.get('reporter_hit_rate', 0),
            overall.get('vitality_hit_rate', 0),
            overall.get('platform_hit_rate', 0)
        ]
        
        fig.add_trace(
            go.Bar(
                x=hit_types,
                y=hit_rates,
                name='Hit Rate %',
                marker_color='steelblue',
                text=[f'{rate:.1f}%' for rate in hit_rates],
                textposition='auto'
            ),
            row=2, col=1
        )
        
        # Alerts table
        alerts = metrics.get('alerts', [])
        if alerts:
            alert_data = [[alert.get('reporter', 'Overall'), alert['message'], alert['severity']] for alert in alerts]
            fig.add_trace(
                go.Table(
                    header=dict(values=['Reporter', 'Alert Message', 'Severity'],
                               fill_color='lightgray'),
                    cells=dict(values=list(zip(*alert_data)) if alert_data else [[], [], []],
                              fill_color=[['red' if severity == 'high' else 'orange' if severity == 'medium' else 'white' 
                                         for severity in [alert['severity'] for alert in alerts]]])
                ),
                row=2, col=2
            )
        else:
            fig.add_trace(
                go.Table(
                    header=dict(values=['Status'], fill_color='lightgreen'),
                    cells=dict(values=[['All QC checks passed']], fill_color='lightgreen')
                ),
                row=2, col=2
            )
        
        # Overall quality indicator
        overall_score = self._calculate_overall_quality_score(metrics)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=overall_score,
                title={'text': "Overall Quality Score"},
                delta={'reference': 80, 'position': "bottom"},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "gray"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 80}}
            ),
            row=2, col=3
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Quality Control Dashboard",
            showlegend=False
        )
        
        # Apply scientific theme
        self.apply_scientific_theme(fig)
        
        return fig
    
    def _calculate_overall_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)."""
        scores = []
        
        # Z-factor scores
        for reporter in ['lptA', 'ldtD']:
            if reporter in metrics:
                z_factor = metrics[reporter].get('z_factor', 0)
                if z_factor >= 0.5:
                    scores.append(100)
                elif z_factor >= 0:
                    scores.append(60)
                else:
                    scores.append(20)
        
        # S:B ratio scores
        for reporter in ['lptA', 'ldtD']:
            if reporter in metrics:
                sb_ratio = metrics[reporter].get('sb_ratio', 0)
                if sb_ratio >= 3:
                    scores.append(100)
                elif sb_ratio >= 2:
                    scores.append(70)
                else:
                    scores.append(40)
        
        # Alert penalty
        alerts = metrics.get('alerts', [])
        alert_penalty = len([a for a in alerts if a['severity'] == 'high']) * 20
        alert_penalty += len([a for a in alerts if a['severity'] == 'medium']) * 10
        
        if scores:
            base_score = np.mean(scores)
            return max(0, base_score - alert_penalty)
        else:
            return 50  # Default score when no data available
    
    def render_dashboard(self, data: pd.DataFrame) -> None:
        """Render the complete QC dashboard in Streamlit."""
        st.subheader("🔬 Quality Control Dashboard")
        
        # Create main dashboard
        fig = self.create_figure(data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional detailed metrics
        with st.expander("📊 Detailed QC Metrics"):
            metrics = self.calculate_plate_metrics(data)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**lptA Reporter**")
                if 'lptA' in metrics:
                    lpta_metrics = metrics['lptA']
                    st.metric("Z-Factor", f"{lpta_metrics.get('z_factor', 0):.3f}")
                    st.metric("S:B Ratio", f"{lpta_metrics.get('sb_ratio', 0):.2f}")
                    st.metric("Pos Ctrl CV%", f"{lpta_metrics.get('pos_cv', 0):.1f}%")
            
            with col2:
                st.write("**ldtD Reporter**")
                if 'ldtD' in metrics:
                    ldtd_metrics = metrics['ldtD']
                    st.metric("Z-Factor", f"{ldtd_metrics.get('z_factor', 0):.3f}")
                    st.metric("S:B Ratio", f"{ldtd_metrics.get('sb_ratio', 0):.2f}")
                    st.metric("Pos Ctrl CV%", f"{ldtd_metrics.get('pos_cv', 0):.1f}%")
            
            with col3:
                st.write("**Overall Plate**")
                overall = metrics.get('overall', {})
                st.metric("Total Wells", overall.get('total_wells', 0))
                st.metric("Platform Hits", overall.get('platform_hit_count', 0))
                st.metric("Hit Rate", f"{overall.get('platform_hit_rate', 0):.2f}%")