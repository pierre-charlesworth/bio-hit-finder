"""Advanced analytics modules for the bio-hit-finder platform.

This package provides sophisticated statistical analysis tools for plate-based
assays, including B-scoring for bias correction, edge effect detection, and
multi-stage hit calling for dual-readout compound screening.

Modules:
    bscore: Median-polish B-scoring implementation
    edge_effects: Edge effect detection and spatial analysis
    hit_calling: Multi-stage hit calling analytics and reporting
"""

from .bscore import (
    median_polish,
    calculate_bscore,
    BScoreProcessor,
    BScoreError,
    apply_bscoring_to_dataframe,
    validate_bscore_matrix,
)

from .edge_effects import (
    EdgeEffectDetector,
    EdgeEffectResult,
    WarningLevel,
    EdgeEffectError,
    detect_edge_effects_simple,
    is_edge_effect_significant,
    format_edge_effect_summary,
)

from .hit_calling import (
    HitCallingAnalyzer,
    HitCallingError,
    analyze_multi_plate_hits,
    format_hit_calling_report,
)

__all__ = [
    # B-scoring exports
    'median_polish',
    'calculate_bscore', 
    'BScoreProcessor',
    'BScoreError',
    'apply_bscoring_to_dataframe',
    'validate_bscore_matrix',
    
    # Edge effects exports
    'EdgeEffectDetector',
    'EdgeEffectResult',
    'WarningLevel',
    'EdgeEffectError',
    'detect_edge_effects_simple',
    'is_edge_effect_significant',
    'format_edge_effect_summary',
    
    # Hit calling exports
    'HitCallingAnalyzer',
    'HitCallingError',
    'analyze_multi_plate_hits',
    'format_hit_calling_report',
]