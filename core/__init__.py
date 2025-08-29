"""Core data processing modules for bio-hit-finder platform.

This package provides the essential data processing functionality for plate-based
biological assay analysis, including:

- Robust statistical functions (statistics module)
- Core calculation pipeline (calculations module) 
- Plate data processing and ingestion (plate_processor module)

All calculations follow the exact specifications in the PRD document and are
designed for numerical reproducibility and robust handling of missing values.
"""

from __future__ import annotations

import logging
from typing import Optional

# Configure logging for the core package
logger = logging.getLogger(__name__)

# Import main classes and functions for public API
from .calculations import (
    apply_viability_gate,
    calculate_od_normalization,
    calculate_plate_summary,
    calculate_reporter_ratios,
    calculate_robust_zscore_columns,
    process_plate_calculations,
    validate_plate_columns,
)
from .plate_processor import (
    ColumnMappingError,
    PlateProcessor,
    PlateProcessingError,
    get_available_excel_sheets,
    process_plate_file,
)
from .statistics import (
    calculate_robust_zscore,
    count_valid_values,
    is_constant_array,
    mad,
    nan_safe_median,
    robust_zscore,
    summary_statistics,
)
# Analytics integration imports - import these directly when needed
# from .analytics_integration import (
#     AdvancedPlateProcessor,
#     apply_analytics_to_existing_data,
#     create_advanced_processor_from_config,
# )

# Version info
__version__ = "0.1.0"
__author__ = "Bio Hit Finder Team"

# Public API - these are the recommended functions/classes for external use
__all__ = [
    # Main processor classes
    "PlateProcessor",
    
    # High-level processing functions
    "process_plate_file",
    "process_plate_calculations",
    
    # Core calculation functions  
    "calculate_reporter_ratios",
    "calculate_od_normalization", 
    "calculate_robust_zscore_columns",
    "apply_viability_gate",
    
    # Statistical functions
    "nan_safe_median",
    "mad",
    "robust_zscore",
    "calculate_robust_zscore",
    "summary_statistics",
    
    # Validation and utilities
    "validate_plate_columns",
    "calculate_plate_summary", 
    "get_available_excel_sheets",
    "count_valid_values",
    "is_constant_array",
    
    # Exceptions
    "PlateProcessingError",
    "ColumnMappingError",
]

# Package metadata
REQUIRED_COLUMNS = [
    'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD',
    'OD_WT', 'OD_tolC', 'OD_SA'
]

CALCULATED_COLUMNS = [
    'Ratio_lptA', 'Ratio_ldtD',
    'Z_lptA', 'Z_ldtD', 
    'OD_WT_norm', 'OD_tolC_norm', 'OD_SA_norm',
    'viability_ok_lptA', 'viability_fail_lptA',
    'viability_ok_ldtD', 'viability_fail_ldtD',
]

# Logging configuration function
def configure_logging(level: str = "INFO", 
                     format_string: Optional[str] = None) -> None:
    """Configure logging for the core package.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Set package logger level
    core_logger = logging.getLogger(__name__)
    core_logger.setLevel(getattr(logging, level.upper()))
    
    logger.info(f"Core package logging configured at {level} level")


# Package initialization
logger.info(f"Bio-hit-finder core package v{__version__} loaded")
logger.debug(f"Public API includes {len(__all__)} functions/classes")