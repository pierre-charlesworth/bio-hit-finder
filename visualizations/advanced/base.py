"""Base classes and utilities for advanced visualizations."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import streamlit as st
import numpy as np


class BaseVisualization(ABC):
    """Abstract base class for all advanced visualizations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.theme = self.config.get('visualization_params', {}).get('color_scheme', 'scientific')
        
    @abstractmethod
    def create_figure(self, data: pd.DataFrame, **kwargs) -> go.Figure:
        """Create the main visualization figure."""
        pass
    
    def apply_scientific_theme(self, fig: go.Figure) -> go.Figure:
        """Apply consistent scientific theme to figures."""
        fig.update_layout(
            template="plotly_white",
            font=dict(family="Arial", size=12),
            title_font_size=14,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=60, r=60, t=80, b=60)
        )
        return fig
    
    def add_alert_annotations(self, fig: go.Figure, alerts: List[Dict[str, Any]]) -> go.Figure:
        """Add alert annotations to figures."""
        for alert in alerts:
            fig.add_annotation(
                x=alert.get('x', 0.5),
                y=alert.get('y', 0.95),
                xref="paper",
                yref="paper",
                text=f"⚠️ {alert['message']}",
                showarrow=False,
                font=dict(color="red", size=12),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
        return fig


class QCMetricsCalculator:
    """Calculator for quality control metrics."""
    
    @staticmethod
    def calculate_z_factor(positive_controls: pd.Series, negative_controls: pd.Series) -> float:
        """Calculate Z-factor for assay quality assessment.
        
        Z-factor = 1 - (3 * (std_pos + std_neg) / |mean_pos - mean_neg|)
        
        Returns:
            float: Z-factor value (>0.5 excellent, 0.0-0.5 marginal, <0 poor)
        """
        if len(positive_controls) < 2 or len(negative_controls) < 2:
            return np.nan
            
        mean_pos = positive_controls.mean()
        mean_neg = negative_controls.mean()
        std_pos = positive_controls.std()
        std_neg = negative_controls.std()
        
        if abs(mean_pos - mean_neg) == 0:
            return np.nan
            
        z_factor = 1 - (3 * (std_pos + std_neg) / abs(mean_pos - mean_neg))
        return z_factor
    
    @staticmethod
    def calculate_signal_to_background(signal: pd.Series, background: pd.Series) -> float:
        """Calculate signal-to-background ratio."""
        if len(signal) == 0 or len(background) == 0:
            return np.nan
        return signal.mean() / background.mean() if background.mean() != 0 else np.nan
    
    @staticmethod
    def calculate_cv_percent(data: pd.Series) -> float:
        """Calculate coefficient of variation as percentage."""
        if len(data) == 0 or data.mean() == 0:
            return np.nan
        return (data.std() / data.mean()) * 100
    
    @staticmethod
    def detect_qc_alerts(z_factor: float, sb_ratio: float, cv_percent: float, 
                        config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect QC alerts based on configured thresholds."""
        alerts = []
        
        # Z-factor alerts
        z_min = config.get('visualization_features', {}).get('qc_dashboard', {}).get('alert_thresholds', {}).get('z_factor_min', 0.5)
        if not np.isnan(z_factor):
            if z_factor < 0:
                alerts.append({'message': f'Poor Z-factor: {z_factor:.2f}', 'severity': 'high'})
            elif z_factor < z_min:
                alerts.append({'message': f'Marginal Z-factor: {z_factor:.2f}', 'severity': 'medium'})
        
        # S:B ratio alerts (adapted for P90/median approach)
        sb_min = config.get('visualization_features', {}).get('qc_dashboard', {}).get('alert_thresholds', {}).get('sb_ratio_min', 1.5)
        if not np.isnan(sb_ratio) and sb_ratio < sb_min:
            alerts.append({'message': f'Low dynamic range (P90/median): {sb_ratio:.2f}', 'severity': 'medium'})
        
        # CV% alerts
        cv_max = config.get('visualization_features', {}).get('qc_dashboard', {}).get('alert_thresholds', {}).get('cv_percent_max', 20.0)
        if not np.isnan(cv_percent) and cv_percent > cv_max:
            alerts.append({'message': f'High CV%: {cv_percent:.1f}%', 'severity': 'medium'})
        
        return alerts