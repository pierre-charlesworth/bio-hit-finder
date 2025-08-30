"""Main Streamlit application entry point for the bio-hit-finder platform.

This is the primary entry point for the Streamlit web application.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import io
import zipfile
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

# Import core modules
from core.plate_processor import PlateProcessor, PlateProcessingError, get_available_excel_sheets
from core.calculations import calculate_plate_summary
from analytics.edge_effects import EdgeEffectDetector, WarningLevel
from analytics.bscore import BScoreProcessor
from analytics.hit_calling import HitCallingAnalyzer, analyze_multi_plate_hits, format_hit_calling_report
from sample_data_generator import create_demo_data

# Import advanced visualization modules
# from visualizations.advanced.qc_dashboard import QCDashboard  # Temporarily commented for debugging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure the Streamlit page
st.set_page_config(
    page_title="BREAKthrough OM Screening Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config.yaml: {e}. Using defaults.")
        return {}


@st.cache_data(ttl=3600)
def process_uploaded_files(files_data: Dict[str, bytes], 
                          sheet_selections: Dict[str, str],
                          viability_threshold: float,
                          apply_bscore: bool,
                          hit_calling_enabled: bool = False,
                          hit_calling_config: Optional[Dict[str, Any]] = None,
                          column_mapping: Optional[Dict[str, str]] = None) -> Optional[pd.DataFrame]:
    """Process uploaded files and return combined dataframe."""
    try:
        processor = PlateProcessor(viability_threshold=viability_threshold)
        
        # Process each file
        plate_files = {}
        sheet_names = {}
        
        for filename, file_data in files_data.items():
            # Create temporary file
            temp_path = Path(f"/tmp/{filename}")
            temp_path.parent.mkdir(exist_ok=True)
            temp_path.write_bytes(file_data)
            
            plate_id = Path(filename).stem
            plate_files[plate_id] = temp_path
            
            if filename in sheet_selections:
                sheet_names[plate_id] = sheet_selections[filename]
        
        # Process multiple plates with hit calling if enabled
        if hit_calling_enabled and hit_calling_config:
            # Process each plate individually with dual-readout method
            processed_plates = []
            for plate_id, temp_path in plate_files.items():
                sheet_name = sheet_names.get(plate_id)
                raw_df = processor.load_plate_data(temp_path, sheet_name=sheet_name)
                
                # Auto-detect columns for first plate, reuse mapping for subsequent plates
                if not processor.column_mapping:
                    processor.auto_detect_columns(raw_df)
                
                # Apply column mapping
                mapped_df = processor.apply_column_mapping(raw_df)
                
                # Process with dual-readout hit calling
                processed_df = processor.process_dual_readout_plate(mapped_df, plate_id, hit_calling_config)
                processed_plates.append(processed_df)
            
            combined_df = pd.concat(processed_plates, ignore_index=True)
        else:
            # Standard processing
            combined_df = processor.process_multiple_plates(plate_files, sheet_names)
        
        # Apply B-scoring if requested
        if apply_bscore and len(combined_df) > 0:
            bscore_processor = BScoreProcessor()
            
            # Group by plate for B-scoring
            processed_plates = []
            for plate_id in combined_df['PlateID'].unique():
                plate_df = combined_df[combined_df['PlateID'] == plate_id].copy()
                
                # Apply B-scoring to Z-scores
                for metric in ['Z_lptA', 'Z_ldtD']:
                    if metric in plate_df.columns:
                        b_scores = bscore_processor.calculate_bscores_for_plate(plate_df, metric)
                        plate_df[f'B_{metric}'] = b_scores
                
                processed_plates.append(plate_df)
            
            combined_df = pd.concat(processed_plates, ignore_index=True)
        
        # Clean up temporary files
        for temp_path in plate_files.values():
            if temp_path.exists():
                temp_path.unlink()
        
        return combined_df
        
    except Exception as e:
        logger.error(f"Failed to process files: {e}")
        st.error(f"Failed to process files: {e}")
        return None


def _unused_load_dataframe_from_bytes(filename: str, file_data: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Load DataFrame directly from bytes data without temporary files when possible.
    
    Args:
        filename: Original filename (used to determine file type)
        file_data: File content as bytes
        sheet_name: Sheet name for Excel files (None for CSV or first sheet)
        
    Returns:
        DataFrame with loaded data
        
    Raises:
        Exception: If file cannot be loaded
    """
    try:
        if filename.endswith(('.xlsx', '.xls')):
            # For Excel files, we need to use BytesIO
            excel_buffer = io.BytesIO(file_data)
            if sheet_name is None:
                df = pd.read_excel(excel_buffer)
            else:
                df = pd.read_excel(excel_buffer, sheet_name=sheet_name)
            excel_buffer.close()  # Close BytesIO buffer
        elif filename.endswith('.csv'):
            # For CSV files, use StringIO
            text_data = file_data.decode('utf-8')
            csv_buffer = io.StringIO(text_data)
            df = pd.read_csv(csv_buffer)
            csv_buffer.close()  # Close StringIO buffer
        else:
            raise ValueError(f"Unsupported file format: {filename}")
            
        # Clean column names
        df.columns = df.columns.str.strip()
        return df
        
    except Exception as e:
        logger.warning(f"Failed to load {filename} from memory, falling back to temporary file: {e}")
        raise


def get_excel_sheet_names_from_bytes(file_data: bytes) -> List[str]:
    """Get Excel sheet names directly from bytes data.
    
    Args:
        file_data: Excel file content as bytes
        
    Returns:
        List of sheet names
    """
    excel_buffer = io.BytesIO(file_data)
    try:
        with pd.ExcelFile(excel_buffer) as excel_file:
            return excel_file.sheet_names
    finally:
        excel_buffer.close()


class TemporaryFileManager:
    """Context manager for safely handling temporary files with Windows file locking."""
    
    def __init__(self, filename: str, file_data: bytes):
        self.filename = filename
        self.file_data = file_data
        self.temp_path = None
        self.excel_file = None
        
    def __enter__(self):
        # Create temporary file
        self.temp_path = Path(tempfile.gettempdir()) / self.filename
        self.temp_path.parent.mkdir(exist_ok=True)
        self.temp_path.write_bytes(self.file_data)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close any open Excel files first
        if self.excel_file is not None:
            try:
                self.excel_file.close()
            except:
                pass  # Ignore close errors
        
        # Force garbage collection
        gc.collect()
        
        # Clean up temporary file
        if self.temp_path:
            safe_cleanup_temp_file(self.temp_path)
    
    def get_sheet_names(self):
        """Get sheet names for Excel files, handling file closure properly."""
        if self.filename.endswith(('.xlsx', '.xls')):
            # Use context manager to ensure file is closed
            with pd.ExcelFile(self.temp_path) as excel_file:
                sheet_names = excel_file.sheet_names
            return sheet_names
        else:
            return [None]  # CSV has no sheets


def safe_cleanup_temp_file(temp_path: Path, max_attempts: int = 5, delay: float = 0.1) -> bool:
    """Safely clean up temporary file with retry logic for Windows file locking.
    
    Args:
        temp_path: Path to the temporary file to delete
        max_attempts: Maximum number of deletion attempts
        delay: Delay between attempts in seconds
        
    Returns:
        True if file was successfully deleted or doesn't exist, False otherwise
    """
    if not temp_path.exists():
        return True
    
    # Force garbage collection to release any lingering file handles
    gc.collect()
    
    for attempt in range(max_attempts):
        try:
            temp_path.unlink()
            return True
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(delay)
                gc.collect()  # Try to force garbage collection again
            else:
                logger.warning(f"Failed to delete temporary file {temp_path} after {max_attempts} attempts")
                return False
        except FileNotFoundError:
            # File was already deleted
            return True
        except Exception as e:
            logger.warning(f"Unexpected error deleting temporary file {temp_path}: {e}")
            return False
    
    return False


@st.cache_data(ttl=3600)
def process_all_sheets_from_files(
    files_data: Dict[str, bytes],
    viability_threshold: float,
    apply_bscore: bool,
    hit_calling_enabled: bool = False,
    hit_calling_config: Optional[Dict[str, Any]] = None,
    column_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Dict[str, Any]]:
    """Process ALL sheets from uploaded Excel files.
    
    Returns:
        Dict mapping sheet_key -> {processed_data, edge_results, processing_summary, 
                                   hit_calling_results, metadata, error, error_message}
    """
    sheet_results = {}
    processor = PlateProcessor(viability_threshold=viability_threshold)
    
    for filename, file_data in files_data.items():
        # Create temporary file
        temp_path = Path(tempfile.gettempdir()) / filename
        temp_path.parent.mkdir(exist_ok=True)
        temp_path.write_bytes(file_data)
        
        try:
            # Get all sheets for Excel files
            if filename.endswith(('.xlsx', '.xls')):
                excel_file = pd.ExcelFile(temp_path)
                sheet_names = excel_file.sheet_names
                excel_file.close()  # Explicitly close to release file handle
            else:
                sheet_names = [None]  # CSV has no sheets
            
            # Process each sheet
            for sheet_name in sheet_names:
                sheet_key = f"{filename}::{sheet_name}" if sheet_name else filename
                
                try:
                    # Load and process individual sheet
                    raw_df = processor.load_plate_data(temp_path, sheet_name=sheet_name)
                    
                    # Auto-detect columns for first sheet, reuse mapping for subsequent sheets
                    if not processor.column_mapping:
                        processor.auto_detect_columns(raw_df)
                    
                    # Apply column mapping
                    mapped_df = processor.apply_column_mapping(raw_df)
                    
                    # Generate plate ID
                    plate_id = f"{Path(filename).stem}_{sheet_name}" if sheet_name else Path(filename).stem
                    
                    # Process with appropriate method
                    if hit_calling_enabled and hit_calling_config:
                        processed_df = processor.process_dual_readout_plate(
                            mapped_df, plate_id, hit_calling_config
                        )
                    else:
                        processed_df = processor.process_single_plate(mapped_df, plate_id)
                    
                    # Apply B-scoring if requested
                    if apply_bscore and len(processed_df) > 0:
                        bscore_processor = BScoreProcessor()
                        for metric in ['Z_lptA', 'Z_ldtD']:
                            if metric in processed_df.columns:
                                b_scores = bscore_processor.calculate_bscores_for_plate(processed_df, metric)
                                processed_df[f'B_{metric}'] = b_scores
                    
                    # Calculate edge effects
                    edge_results = []
                    if len(processed_df) > 0:
                        edge_detector = EdgeEffectDetector()
                        edge_results = edge_detector.detect_edge_effects_dataframe(
                            processed_df, metric="Z_lptA"
                        )
                    
                    # Calculate processing summary
                    summary = calculate_plate_summary(processed_df)
                    
                    # Calculate hit calling results
                    hit_calling_results = {}
                    if hit_calling_enabled and hit_calling_config:
                        try:
                            plate_data = {plate_id: processed_df}
                            hit_calling_results = analyze_multi_plate_hits(plate_data, hit_calling_config)
                        except Exception as e:
                            logger.warning(f"Hit calling failed for {sheet_key}: {e}")
                    
                    # Store successful result
                    sheet_results[sheet_key] = {
                        "processed_data": processed_df,
                        "edge_results": edge_results,
                        "processing_summary": summary,
                        "hit_calling_results": hit_calling_results,
                        "metadata": {
                            "filename": filename,
                            "sheet_name": sheet_name,
                            "plate_count": len(processed_df['PlateID'].unique()) if 'PlateID' in processed_df.columns else 1,
                            "total_wells": len(processed_df)
                        },
                        "error": False,
                        "error_message": None
                    }
                    
                except Exception as e:
                    # Store error result
                    logger.error(f"Failed to process {sheet_key}: {e}")
                    sheet_results[sheet_key] = {
                        "processed_data": None,
                        "edge_results": [],
                        "processing_summary": {},
                        "hit_calling_results": {},
                        "metadata": {
                            "filename": filename,
                            "sheet_name": sheet_name,
                            "plate_count": 0,
                            "total_wells": 0
                        },
                        "error": True,
                        "error_message": str(e)
                    }
        
        finally:
            # Clean up temporary file - handle Windows file locking gracefully
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except (PermissionError, OSError) as e:
                    # Windows file locking - ignore cleanup error, file will be cleaned by OS
                    logger.debug(f"Could not delete temp file {temp_path}: {e}")
                    pass
    
    return sheet_results


def render_edge_effect_badge(warning_level: WarningLevel) -> str:
    """Render edge effect warning badge with appropriate styling."""
    level_colors = {
        WarningLevel.INFO: "info",
        WarningLevel.WARN: "warn", 
        WarningLevel.CRITICAL: "critical"
    }
    
    color_class = level_colors.get(warning_level, "info")
    return f'<span class="badge {color_class}">{warning_level.value}</span>'


def create_plate_heatmap(df: pd.DataFrame, metric: str, plate_id: str) -> go.Figure:
    """Create a heatmap for a single plate."""
    plate_df = df[df['PlateID'] == plate_id].copy() if 'PlateID' in df.columns else df.copy()
    
    # Create 8x12 matrix
    matrix = np.full((8, 12), np.nan)
    
    # Map row letters to indices
    row_mapping = {chr(ord('A') + i): i for i in range(8)}
    
    for _, row in plate_df.iterrows():
        if 'Row' in row and 'Col' in row and metric in row:
            try:
                row_idx = row_mapping.get(str(row['Row']).upper(), None)
                col_idx = int(row['Col']) - 1
                
                if row_idx is not None and 0 <= col_idx < 12:
                    matrix[row_idx, col_idx] = row[metric]
            except (ValueError, TypeError):
                continue
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[str(i+1) for i in range(12)],
        y=[chr(ord('A') + i) for i in range(8)],
        colorscale='RdBu_r' if metric.startswith(('Z_', 'B_Z')) else 'viridis',
        zmid=0 if metric.startswith(('Z_', 'B_Z')) else None,
        hovertemplate='Row: %{y}<br>Col: %{x}<br>Value: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'{metric} - {plate_id}',
        xaxis_title='Column',
        yaxis_title='Row',
        height=400,
        width=600
    )
    
    return fig


def main() -> None:
    """Main application function."""
    # Load configuration
    config = load_config()
    
    # BREAKthrough project header
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #1e3a8a, #3b82f6); border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>🧬 BREAKthrough OM Screening Platform</h1>
        <p style='color: #e0e7ff; margin: 0.5rem 0 0 0; font-size: 1.1rem;'>
            Dual-Readout Discovery of Outer Membrane Permeabilizers
        </p>
        <p style='color: #c7d2fe; margin: 0.25rem 0 0 0; font-size: 0.9rem;'>
            🇪🇺 Funded by the European Union | Novel Antimicrobial Strategies
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add custom CSS for badges
    st.markdown("""
    <style>
    .badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        display: inline-block;
        margin: 0.125rem;
    }
    .badge.info {
        background-color: #dbeafe;
        color: #1e40af;
    }
    .badge.warn {
        background-color: #fef3c7;
        color: #d97706;
    }
    .badge.critical {
        background-color: #fee2e2;
        color: #dc2626;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("Plate Data Processing Platform")
    st.subheader("Normalization, scoring, B-scoring, and reporting")
    
    # Initialize session state
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'edge_results' not in st.session_state:
        st.session_state.edge_results = []
    if 'processing_summary' not in st.session_state:
        st.session_state.processing_summary = {}
    if 'hit_calling_results' not in st.session_state:
        st.session_state.hit_calling_results = {}
    # Multi-stage hit calling is always enabled for dual-readout screening
    st.session_state.multi_stage_enabled = True
    
    # Multi-sheet session state
    if 'sheet_data' not in st.session_state:
        st.session_state.sheet_data = {}
    if 'current_sheet' not in st.session_state:
        st.session_state.current_sheet = None
    if 'available_sheets' not in st.session_state:
        st.session_state.available_sheets = []
    if 'multi_sheet_mode' not in st.session_state:
        st.session_state.multi_sheet_mode = False
    
    # Sidebar for file upload and configuration
    with st.sidebar:
        st.header("Configuration")
        
        # File upload section
        st.subheader("📁 Data Upload")
        uploaded_files = st.file_uploader(
            "Choose plate data files",
            accept_multiple_files=True,
            type=['csv', 'xlsx', 'xls'],
            help="Upload one or more plate datasets with required measurement columns"
        )
        
        # Multi-sheet processing mode toggle
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} file(s)")
            
            # Check if any files have multiple sheets
            has_multi_sheet_files = False
            for file in uploaded_files:
                if file.name.endswith(('.xlsx', '.xls')):
                    try:
                        excel_file = pd.ExcelFile(file)
                        if len(excel_file.sheet_names) > 1:
                            has_multi_sheet_files = True
                            st.info(f"📊 {file.name}: {len(excel_file.sheet_names)} sheets detected")
                        else:
                            st.info(f"📄 {file.name}: 1 sheet")
                    except Exception as e:
                        st.warning(f"Could not read sheets from {file.name}: {e}")
            
            if has_multi_sheet_files:
                st.subheader("📊 Processing Mode")
                multi_sheet_mode = st.checkbox(
                    "Multi-Sheet Mode",
                    value=st.session_state.multi_sheet_mode,
                    help="Process all sheets from Excel files simultaneously"
                )
                st.session_state.multi_sheet_mode = multi_sheet_mode
                
                if multi_sheet_mode:
                    st.success("🔄 All Excel sheets will be processed at once")
                else:
                    st.info("📄 Single-sheet mode: Select specific sheets to process")
            else:
                st.session_state.multi_sheet_mode = False
        
        # Sheet selection - available for both single and multi-sheet modes
        sheet_selections = {}
        if uploaded_files:
            for file in uploaded_files:
                if file.name.endswith(('.xlsx', '.xls')):
                    try:
                        excel_file = pd.ExcelFile(file)
                        if len(excel_file.sheet_names) > 1:
                            if st.session_state.multi_sheet_mode:
                                st.write(f"**{file.name}** - {len(excel_file.sheet_names)} sheets will be processed")
                                # In multi-sheet mode, we'll process all sheets, but still show them for info
                                with st.expander(f"View sheets in {file.name}"):
                                    for sheet in excel_file.sheet_names:
                                        st.write(f"• {sheet}")
                            else:
                                selected_sheet = st.selectbox(
                                    f"Sheet for {file.name}:",
                                    excel_file.sheet_names,
                                    key=f"sheet_{file.name}"
                                )
                                sheet_selections[file.name] = selected_sheet
                    except Exception as e:
                        st.warning(f"Could not read sheets from {file.name}: {e}")
        
        # Sheet selector for multi-sheet mode (after processing)
        if st.session_state.multi_sheet_mode and st.session_state.sheet_data:
            st.subheader("📋 Sheet Selection")
            
            # Build sheet options
            sheet_options = []
            for sheet_key, sheet_data in st.session_state.sheet_data.items():
                metadata = sheet_data['metadata']
                filename = metadata['filename']
                sheet_name = metadata['sheet_name']
                error_flag = " ❌" if sheet_data['error'] else ""
                wells = metadata['total_wells']
                
                display_name = f"{sheet_name} ({wells} wells){error_flag}"
                sheet_options.append((display_name, sheet_key))
            
            if sheet_options:
                current_selection = st.selectbox(
                    "Select Sheet:",
                    options=[option[1] for option in sheet_options],
                    format_func=lambda x: next(opt[0] for opt in sheet_options if opt[1] == x),
                    index=0 if st.session_state.current_sheet not in [opt[1] for opt in sheet_options] 
                          else [opt[1] for opt in sheet_options].index(st.session_state.current_sheet),
                    help="Switch between processed sheets instantly",
                    key="sheet_selector"
                )
                
                # Detect and handle selection changes
                if current_selection != st.session_state.current_sheet:
                    st.session_state.current_sheet = current_selection
                    st.rerun()
                else:
                    st.session_state.current_sheet = current_selection
                
                # Show sheet info
                current_data = st.session_state.sheet_data[current_selection]
                if current_data['error']:
                    st.error(f"Error: {current_data['error_message']}")
                else:
                    metadata = current_data['metadata']
                    st.success(f"✅ {metadata['total_wells']} wells processed successfully")
        
        # Hit calling is always multi-stage for dual-readout screening
        st.subheader("🔬 Hit Calling Pipeline")
        st.info("**Stage 1:** Reporter Hits → **Stage 2:** Vitality Hits → **Stage 3:** Platform Hits")
        
        # Configuration parameters
        st.subheader("⚙️ Parameters")
        
        viability_threshold = st.slider(
            "Viability Gate Threshold (f)",
            min_value=0.1,
            max_value=1.0,
            value=config.get('processing', {}).get('viability_threshold', 0.3),
            step=0.1,
            help="Wells with ATP < f × median(ATP) are flagged as low viability. Uses BacTiter luminescence assay - D-luciferin + cellular ATP → light via luciferase."
        )
        
        z_cutoff = st.number_input(
            "Z-score Cutoff for Hits",
            min_value=1.0,
            max_value=5.0,
            value=config.get('processing', {}).get('z_score_cutoff', 2.0),
            step=0.1,
            help="Minimum robust Z-score (MAD-based) to consider a potential hit. Formula: Z = (x - median) / (1.4826 × MAD), where MAD = median(|x - median(x)|). Resistant to outliers and non-normal distributions."
        )
        
        top_n = st.number_input(
            "Top N Hits to Display",
            min_value=10,
            max_value=1000,
            value=config.get('processing', {}).get('top_n_hits', 50),
            step=10,
            help="Number of top hits to show in the hits table"
        )
        
        apply_b_scoring = st.checkbox(
            "Apply B-scoring",
            value=config.get('bscore', {}).get('enabled', False),
            help="Apply median-polish row/column bias correction to remove spatial artifacts. Important for plates with edge effects or systematic row/column bias."
        )
        
        # Hit calling configuration panel
        with st.expander("🎯 Hit Calling Thresholds", expanded=True):
            st.write("**Reporter Hit Detection (Stage 1)**")
            col1, col2 = st.columns(2)
            
            with col1:
                z_threshold_lptA = st.number_input(
                    "lptA Z-score threshold",
                    min_value=1.0,
                    max_value=5.0,
                    value=config.get('hit_calling', {}).get('reporter', {}).get('z_threshold_lptA', 2.0),
                    step=0.1,
                    help="Minimum Z-score for lptA reporter hits. LptA (periplasmic bridge protein) is upregulated by σE during LPS transport stress and OM destabilization."
                )
            
            with col2:
                z_threshold_ldtD = st.number_input(
                    "ldtD Z-score threshold",
                    min_value=1.0,
                    max_value=5.0,
                    value=config.get('hit_calling', {}).get('reporter', {}).get('z_threshold_ldtD', 2.0),
                    step=0.1,
                    help="Minimum Z-score for ldtD reporter hits. LdtD (L,D-transpeptidase) is Cpx-regulated and forms 3-3 crosslinks to compensate for OM structural weakness."
                )
            
            st.write("**Vitality Hit Detection (Stage 2)**")
            col3, col4, col5 = st.columns(3)
            
            with col3:
                tolc_max_threshold = st.slider(
                        "tolC max %",
                        min_value=0.1,
                        max_value=1.0,
                        value=config.get('hit_calling', {}).get('vitality', {}).get('tolC_max_threshold', 0.8),
                        step=0.05,
                        help="E. coli ΔtolC max growth percentage (≤80%). ΔtolC has impaired OM and increased permeability, making it sensitive to OM-disrupting compounds."
                )
            
            with col4:
                wt_min_threshold = st.slider(
                    "WT min %",
                    min_value=0.1,
                    max_value=1.0,
                    value=config.get('hit_calling', {}).get('vitality', {}).get('wt_min_threshold', 0.8),
                    step=0.05,
                    help="E. coli WT min growth percentage (>80%). WT has intact OM providing natural resistance to OM-disrupting compounds."
                )
            
            with col5:
                sa_min_threshold = st.slider(
                    "SA min %",
                    min_value=0.1,
                    max_value=1.0,
                    value=config.get('hit_calling', {}).get('vitality', {}).get('sa_min_threshold', 0.8),
                    step=0.05,
                    help="S. aureus min growth percentage (>80%). Gram-positive control with no OM - should be unaffected by OM-disrupting compounds."
                )
            
            # Build hit calling configuration
            hit_calling_config = {
                'hit_calling': {
                    'multi_stage_enabled': True,
                    'reporter': {
                        'z_threshold_lptA': z_threshold_lptA,
                        'z_threshold_ldtD': z_threshold_ldtD,
                        'require_viability': True,
                        'combine_mode': 'OR'
                    },
                    'vitality': {
                        'tolC_max_threshold': tolc_max_threshold,
                        'wt_min_threshold': wt_min_threshold,
                        'sa_min_threshold': sa_min_threshold,
                        'require_all_conditions': True
                    },
                    'platform': {
                        'require_both_stages': True
                    }
                }
            }
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            edge_effect_threshold = st.slider(
                "Edge Effect Threshold",
                min_value=0.3,
                max_value=2.0,
                value=config.get('edge_warning', {}).get('levels', {}).get('warn_d', 0.8),
                step=0.1,
                help="Effect size threshold for edge effect warnings"
            )
            
            enable_spatial_analysis = st.checkbox(
                "Enable Spatial Analysis",
                value=config.get('edge_warning', {}).get('spatial_autocorr', {}).get('enabled', False),
                help="Enable computationally expensive spatial autocorrelation analysis"
            )
        
        # Column mapping override
        with st.expander("📋 Column Mapping"):
            st.write("Manual column mapping (leave empty for auto-detection)")
            
            required_columns = ['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']
            column_mapping = {}
            
            for col in required_columns:
                mapped_col = st.text_input(f"{col}:", key=f"mapping_{col}", placeholder="Auto-detect")
                if mapped_col:
                    column_mapping[col] = mapped_col
            
            if not column_mapping:
                column_mapping = None
        
        # Methodology and Scientific Background
        st.divider()
        with st.expander("🧬 Scientific Methodology", expanded=False):
            st.markdown("""
            **BREAKthrough Dual-Readout Screening Platform**
            
            This platform implements a dual-reporter system for identifying compounds that disrupt the Gram-negative outer membrane (OM):
            
            **🔬 Reporter System:**
            • **lptA**: σE-regulated LPS transport protein - detects LPS biogenesis stress
            • **ldtD**: Cpx-regulated L,D-transpeptidase - detects peptidoglycan remodeling
            
            **⚡ Three-Strain Vitality Screen:**
            • **E. coli WT**: Intact OM (resistant to OM disruptors)
            • **E. coli ΔtolC**: Compromised OM (sensitive to OM disruptors) 
            • **S. aureus**: Gram-positive control (no OM target)
            
            **📊 Statistical Analysis:**
            • Robust Z-scores using MAD (outlier-resistant)
            • Viability gating with ATP-based luminescence
            • Multi-stage hit calling pipeline
            
            **📚 Learn More:**
            • [Scientific Background](docs/user_guide/scientific_background.md)
            • **Key Publications:**
              - Silhavy et al. (2010) *Cold Spring Harb Perspect Biol*
              - Yoon & Song (2024) *J Microbiol* 
              - Chan et al. (2021) *ACS Infect Dis*
            
            **🏆 BREAKthrough Project**
            *Funded by the European Union*
            """)
        
        # Sample data load option
        st.write("**Or load sample data:**")
        if st.button("🎯 Load Sample Data", help="Load sample plate data directly to test the platform"):
            # Load sample CSV data into the uploader
            with open('sample_plate_data.csv', 'rb') as f:
                sample_data = f.read()
            
            # Store in session state to simulate file upload
            st.session_state.sample_loaded = True
            st.session_state.sample_data = {'sample_plate_data.csv': sample_data}
            st.rerun()
        
        # Use sample data if loaded, otherwise use uploaded files
        files_to_process = uploaded_files
        if hasattr(st.session_state, 'sample_loaded') and st.session_state.sample_loaded:
            files_to_process = st.session_state.sample_data
            st.info("Sample data loaded! Click 'Process Data' to analyze.")
        
        # Process data button
        process_data = st.button("Process Data", type="primary", disabled=not files_to_process)
        
        # Process files when button is clicked
        if process_data:
            with st.spinner("Processing plate data..."):
                processed_df = None
                
                if files_to_process:
                    # Convert files to bytes for caching
                    files_data = {}
                    if hasattr(st.session_state, 'sample_loaded') and st.session_state.sample_loaded:
                        # Use sample data
                        files_data = files_to_process
                    else:
                        # Use uploaded files
                        for file in files_to_process:
                            files_data[file.name] = file.getvalue()
                    
                    # Choose processing method based on multi-sheet mode
                    if st.session_state.multi_sheet_mode:
                        # Multi-sheet processing
                        sheet_results = process_all_sheets_from_files(
                            files_data, viability_threshold, apply_b_scoring, 
                            True, hit_calling_config, column_mapping  # Always enable hit calling
                        )
                        
                        # Update session state
                        st.session_state.sheet_data = sheet_results
                        
                        # Set default current sheet to first successful one
                        successful_sheets = [key for key, data in sheet_results.items() if not data['error']]
                        if successful_sheets:
                            st.session_state.current_sheet = successful_sheets[0]
                            st.session_state.available_sheets = [
                                (data['metadata']['filename'], data['metadata']['sheet_name'], key)
                                for key, data in sheet_results.items()
                            ]
                            
                            # Use first successful sheet as processed_df for backward compatibility
                            processed_df = sheet_results[successful_sheets[0]]['processed_data']
                        
                        # Show processing summary
                        total_sheets = len(sheet_results)
                        successful_sheets_count = len(successful_sheets)
                        failed_sheets = total_sheets - successful_sheets_count
                        
                        if failed_sheets > 0:
                            st.warning(f"Processed {successful_sheets_count}/{total_sheets} sheets successfully. "
                                      f"{failed_sheets} sheets failed.")
                        else:
                            st.success(f"Successfully processed all {total_sheets} sheets!")
                        
                        # Force rerun to show the sheet selector dropdown
                        st.rerun()
                    else:
                        # Single-sheet processing (existing logic)
                        processed_df = process_uploaded_files(
                            files_data, sheet_selections, viability_threshold, 
                            apply_b_scoring, True, hit_calling_config, column_mapping  # Always enable hit calling
                        )
                
                if processed_df is not None:
                    st.session_state.processed_data = processed_df
                    
                    # Calculate edge effects
                    if len(processed_df) > 0:
                        edge_detector = EdgeEffectDetector(
                            thresholds={'warn_d': edge_effect_threshold},
                            spatial_enabled=enable_spatial_analysis
                        )
                        st.session_state.edge_results = edge_detector.detect_edge_effects_dataframe(
                            processed_df, metric="Z_lptA"
                        )
                    
                    # Calculate processing summary
                    processor = PlateProcessor(viability_threshold)
                    for plate_id in processed_df['PlateID'].unique():
                        plate_df = processed_df[processed_df['PlateID'] == plate_id]
                        processor.processed_plates[plate_id] = plate_df
                    
                    st.session_state.processing_summary = processor.get_processing_summary()
                    
                    # Calculate hit calling analysis if multi-stage mode is enabled
                    # Always perform hit analysis for dual-readout screening
                    try:
                        plate_data = {plate_id: processed_df[processed_df['PlateID'] == plate_id] 
                                    for plate_id in processed_df['PlateID'].unique()}
                        hit_analysis = analyze_multi_plate_hits(plate_data, hit_calling_config)
                        st.session_state.hit_calling_results = hit_analysis
                    except Exception as e:
                        logger.warning(f"Hit calling analysis failed: {e}")
                        st.session_state.hit_calling_results = {}
                else:
                    st.error("Failed to process data. Please check your files and try again.")
    
    # Helper function to get current sheet data
    def get_current_sheet_data():
        """Get the current sheet's data based on multi-sheet mode."""
        if st.session_state.multi_sheet_mode and st.session_state.sheet_data:
            current_sheet = st.session_state.current_sheet
            if current_sheet and current_sheet in st.session_state.sheet_data:
                return st.session_state.sheet_data[current_sheet]
        
        # Fallback to legacy single-sheet data
        return {
            'processed_data': st.session_state.get('processed_data'),
            'edge_results': st.session_state.get('edge_results', []),
            'processing_summary': st.session_state.get('processing_summary', {}),
            'hit_calling_results': st.session_state.get('hit_calling_results', {}),
            'error': False,
            'error_message': None
        }
    
    # Display current plate indicator for multi-sheet mode
    if st.session_state.multi_sheet_mode and st.session_state.sheet_data and st.session_state.current_sheet:
        current_data = get_current_sheet_data()
        if not current_data['error']:
            metadata = current_data['metadata']
            filename = metadata['filename']
            sheet_name = metadata['sheet_name']
            wells_count = metadata['total_wells']
            st.info(f"📋 **Currently viewing:** {sheet_name} ({wells_count:,} wells)")
    
    # Main content tabs - dual-readout compound screening interface
    summary_tab, reporter_hits_tab, vitality_hits_tab, hit_calling_tab, viz_tab, heatmaps_tab, qc_tab = st.tabs([
        "📊 Summary", 
        "🧬 Reporter Hits",
        "⚡ Vitality Hits", 
        "🔬 Hit Calling",
        "📈 Visualizations", 
        "🔥 Heatmaps", 
        "📋 QC Report"
    ])
    
    # Get current sheet data
    current_data = get_current_sheet_data()
    df = current_data['processed_data']
    edge_results = current_data['edge_results']
    summary = current_data['processing_summary']
    hit_calling_results = current_data['hit_calling_results']
    
    # Check for sheet errors
    if current_data['error']:
        st.error(f"Sheet processing failed: {current_data['error_message']}")
        st.stop()
    
    # Summary Tab
    with summary_tab:
        st.header("Summary")
        
        if df is not None and len(df) > 0:
            # Metrics row
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Plates", 
                    summary.get('plate_count', 0),
                    help="Number of plates processed"
                )
            
            with col2:
                st.metric(
                    "Total Wells", 
                    summary.get('total_wells', 0),
                    help="Total number of wells across all plates"
                )
            
            with col3:
                missing_pct = 0
                if summary.get('total_wells', 0) > 0:
                    total_measurements = summary.get('total_wells', 0) * len(['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA'])
                    missing_measurements = df[['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']].isna().sum().sum()
                    missing_pct = (missing_measurements / total_measurements) * 100
                
                st.metric(
                    "Missing %", 
                    f"{missing_pct:.1f}%",
                    help="Percentage of missing measurements"
                )
                
            # Hit Calling Summary (if multi-stage mode is enabled and results are available)
            if hit_calling_results and any(col in df.columns for col in ['reporter_hit', 'vitality_hit', 'platform_hit']):
                st.subheader("Hit Calling Summary")
                
                hit_col1, hit_col2, hit_col3, hit_col4 = st.columns(4)
                
                with hit_col1:
                    reporter_hits = df['reporter_hit'].sum() if 'reporter_hit' in df.columns else 0
                    reporter_rate = (reporter_hits / len(df)) * 100 if len(df) > 0 else 0
                    st.metric(
                        "Reporter Hits",
                        f"{reporter_hits:,}",
                        f"{reporter_rate:.1f}%",
                        help="Stage 1: Z-score ≥ 2.0 AND viable"
                    )
                
                with hit_col2:
                    vitality_hits = df['vitality_hit'].sum() if 'vitality_hit' in df.columns else 0  
                    vitality_rate = (vitality_hits / len(df)) * 100 if len(df) > 0 else 0
                    st.metric(
                        "Vitality Hits",
                        f"{vitality_hits:,}",
                        f"{vitality_rate:.1f}%", 
                        help="Stage 2: Growth pattern analysis"
                    )
                
                with hit_col3:
                    platform_hits = df['platform_hit'].sum() if 'platform_hit' in df.columns else 0
                    platform_rate = (platform_hits / len(df)) * 100 if len(df) > 0 else 0
                    st.metric(
                        "Platform Hits", 
                        f"{platform_hits:,}",
                        f"{platform_rate:.1f}%",
                        help="Stage 3: Reporter AND Vitality"
                    )
                
                with hit_col4:
                    # Hit progression efficiency
                    if reporter_hits > 0:
                        progression_rate = (platform_hits / reporter_hits) * 100
                        st.metric(
                            "Progression Rate",
                            f"{progression_rate:.1f}%", 
                            help="Platform hits / Reporter hits"
                        )
                    else:
                        st.metric("Progression Rate", "N/A", help="No reporter hits found")
            
            # Edge Effect Badge
            st.subheader("Edge Effect Status")
            if edge_results:
                # Get the most severe warning level
                max_warning = max(result.warning_level for result in edge_results)
                st.markdown(render_edge_effect_badge(max_warning), unsafe_allow_html=True)
                
                # Expandable diagnostics
                with st.expander("🔍 Edge Effect Diagnostics"):
                    for result in edge_results:
                        st.write(f"**Plate {result.plate_id} ({result.metric})**")
                        
                        diag_col1, diag_col2, diag_col3 = st.columns(3)
                        with diag_col1:
                            st.metric("Effect Size (d)", f"{result.effect_size_d:.3f}")
                        with diag_col2:
                            st.metric("Edge Wells", result.n_edge_wells)
                        with diag_col3:
                            st.metric("Interior Wells", result.n_interior_wells)
                        
                        if not np.isnan(result.row_correlation):
                            st.write(f"Row trend correlation: {result.row_correlation:.3f}")
                        if not np.isnan(result.col_correlation):
                            st.write(f"Column trend correlation: {result.col_correlation:.3f}")
                        
                        # Corner effects
                        corner_issues = [f"{k}: {v:.1f} MADs" for k, v in result.corner_deviations.items() 
                                       if not np.isnan(v) and v > 1.2]
                        if corner_issues:
                            st.write("Corner effects:", ", ".join(corner_issues))
                        
                        st.divider()
            else:
                st.info("No edge effect analysis available. Process data first.")
            
            # Quick reference card
            with st.expander("📋 Quick Reference Card", expanded=False):
                st.markdown("""
                **⚡ At-a-Glance Summary**
                
                | **Measurement** | **Biological Meaning** | **Hit Criteria** |
                |----------------|------------------------|------------------|
                | **lptA Z-score** | LPS transport stress | ≥ 2.0 (+ viability) |
                | **ldtD Z-score** | Peptidoglycan remodeling | ≥ 2.0 (+ viability) |
                | **WT Growth** | Intact OM resistance | > 80% (normal) |
                | **ΔtolC Growth** | Compromised OM sensitivity | ≤ 80% (inhibited) |
                | **SA Growth** | Gram-positive control | > 80% (unaffected) |
                
                **🎯 Hit Classification:**
                - **Reporter Hit:** lptA OR ldtD activated + viable
                - **Vitality Hit:** WT>80% + ΔtolC≤80% + SA>80%
                - **Platform Hit:** Reporter Hit AND Vitality Hit
                
                **📊 Expected Rates (from 880 extracts):**
                - Reporter hits: ~8% | Vitality hits: ~6.5% | Platform hits: ~1%
                
                **⚠️ Key Quality Checks:**
                - Viability: BT ≥ 30% of plate median
                - Edge effects: Check spatial bias warnings  
                - B-scores: Use when systematic row/column bias detected
                
                **📐 Key Formulas:**
                """)
                
                st.latex(r"Z = \frac{x - \text{median}(X)}{1.4826 \times \text{MAD}(X)}")
                st.caption("Robust Z-score calculation")
                
                st.latex(r"Ratio = \frac{BG}{BT} \quad \text{(Reporter Signal / ATP Viability)}")
                st.caption("Normalized reporter activity")
            
            # Results interpretation guide
            with st.expander("🧬 Results Interpretation Guide", expanded=False):
                st.markdown("""
                **Understanding Your Screening Results**
                
                **🔬 Reporter Hits (Stage 1):**
                • **High lptA Z-scores** → LPS transport stress, OM integrity compromised
                • **High ldtD Z-scores** → Peptidoglycan remodeling, structural compensation
                • **Both reporters** → Dual evidence of OM disruption (strongest signal)
                
                **⚡ Vitality Hits (Stage 2):**
                • **WT > 80%, ΔtolC ≤ 80%, SA > 80%** → OM-selective activity pattern
                • **Selective toxicity** → Targets OM specifically, not general cytotoxicity
                • **Gram-positive resistance** → Confirms OM as the target
                
                **🎯 Platform Hits (Stage 3):**
                • **Biological + phenotypic evidence** → High-confidence OM permeabilizers
                • **Adjuvant candidates** → Can sensitize bacteria to existing antibiotics
                • **Expected hit rate: ~1%** → Rare, valuable compounds for combination therapy
                
                **📊 Quality Indicators:**
                • **Z-scores ≥ 2.0** → Statistically significant above background noise
                • **Viability gating** → Excludes low-ATP artifacts, focuses on viable responses  
                • **Edge effects** → Spatial artifacts that may confound results
                • **B-scores** → Corrected for systematic row/column bias when applied
                
                **🚨 Interpretation Caveats:**
                • **False positives:** Some hits may be assay artifacts or non-specific effects
                • **Dose-response needed:** Confirm activity across concentration ranges
                • **Mechanism validation:** Additional assays required to confirm OM disruption
                • **Cytotoxicity assessment:** Ensure selectivity vs mammalian cells
                """)
            
            # Download buttons
            st.subheader("Downloads")
            download_col1, download_col2 = st.columns(2)
            
            with download_col1:
                # Combined CSV download
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Combined CSV",
                    csv_data,
                    file_name="combined_plate_data.csv",
                    mime="text/csv",
                    help="Download all processed plate data as CSV"
                )
            
            with download_col2:
                # ZIP bundle download
                if st.button("📦 Download ZIP Bundle"):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Add CSV data
                        zip_file.writestr("combined_data.csv", csv_data)
                        
                        # Add processing summary
                        summary_yaml = yaml.dump(summary, default_flow_style=False)
                        zip_file.writestr("processing_summary.yaml", summary_yaml)
                        
                        # Add edge effect results if available
                        if edge_results:
                            edge_data = []
                            for result in edge_results:
                                edge_data.append(result._asdict())
                            edge_yaml = yaml.dump(edge_data, default_flow_style=False)
                            zip_file.writestr("edge_effects.yaml", edge_yaml)
                    
                    st.download_button(
                        "📥 Download ZIP Bundle",
                        zip_buffer.getvalue(),
                        file_name="plate_analysis_bundle.zip",
                        mime="application/zip",
                        help="Download complete analysis bundle with CSV, summary, and edge effects"
                    )
        else:
            st.info("👆 Upload and process plate data to see summary metrics and edge effect diagnostics.")
            
            # Show sample data structure
            st.subheader("Expected Data Structure")
            sample_cols = ['PlateID', 'Well', 'Row', 'Col', 'BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']
            # pandas (pd) is already imported at the top of the file
            sample_data = pd.DataFrame({
                col: ['Plate001', 'A01', 'A', '1', '1000', '2000', '800', '1500', '0.5', '0.3', '0.4'] if i == 0 
                     else ['Plate001', 'A02', 'A', '2', '1200', '1800', '900', '1400', '0.6', '0.4', '0.5'] if i == 1
                     else ['...'] * len(sample_cols)
                for i, col in enumerate(sample_cols)
            })
            st.dataframe(sample_data, width='stretch')
    
    # Reporter Hits Tab
    if reporter_hits_tab is not None:
        with reporter_hits_tab:
            st.header("🧬 Reporter Hits")
            
            if df is not None and len(df) > 0:
                # Check if reporter hit data is available
                if 'reporter_hit' in df.columns:
                    reporter_hits_df = df[df['reporter_hit'] == True].copy()
                    
                    # Controls for Reporter Hits
                    control_col1, control_col2 = st.columns(2)
                    
                    with control_col1:
                        rank_by_reporter = st.selectbox(
                            "Rank by:",
                            ["Raw Z", "B-score"] if apply_b_scoring else ["Raw Z"],
                            help="Metric to use for ranking reporter hits",
                            key="reporter_rank_by"
                        )
                    
                    with control_col2:
                        max_hits = len(reporter_hits_df) if len(reporter_hits_df) > 0 else 100
                        display_top_n_reporter = st.number_input(
                            "Display Top N:",
                            min_value=min(10, max_hits),
                            max_value=min(1000, max_hits),
                            value=min(max_hits, max(min(10, max_hits), min(100, max_hits))),
                            step=10,
                            key="reporter_top_n"
                        )
                    
                    # Display reporter hits summary
                    total_wells = len(df)
                    reporter_count = len(reporter_hits_df)
                    reporter_rate = (reporter_count / total_wells * 100) if total_wells > 0 else 0
                    
                    st.write(f"**Found {reporter_count:,} reporter hits ({reporter_rate:.1f}% of {total_wells:,} wells)**")
                    st.write("Reporter hits are compounds that show Z-score ≥ 2.0 for lptA OR ldtD **AND** pass viability gates (ATP levels).")
                    
                    if len(reporter_hits_df) > 0:
                        # Rank hits by selected metric
                        if rank_by_reporter == "B-score" and apply_b_scoring and all(col in reporter_hits_df.columns for col in ['B_Z_lptA', 'B_Z_ldtD']):
                            reporter_hits_df['rank_score'] = reporter_hits_df[['B_Z_lptA', 'B_Z_ldtD']].abs().max(axis=1)
                        elif all(col in reporter_hits_df.columns for col in ['Z_lptA', 'Z_ldtD']):
                            reporter_hits_df['rank_score'] = reporter_hits_df[['Z_lptA', 'Z_ldtD']].abs().max(axis=1)
                        else:
                            reporter_hits_df['rank_score'] = 0
                        
                        reporter_hits_df = reporter_hits_df.sort_values('rank_score', ascending=False).head(display_top_n_reporter)
                        
                        # Prepare display columns for reporter hits
                        display_cols = []
                        
                        # Essential columns
                        essential_cols = [
                            ('PlateID', ['PlateID', 'Plate_ID', 'plate_id']),
                            ('Well', ['Well', 'WellID', 'well_id']),
                            ('Ratio_lptA', ['Ratio_lptA']),
                            ('Ratio_ldtD', ['Ratio_ldtD'])
                        ]
                        
                        for col_name, alternatives in essential_cols:
                            for alt in alternatives:
                                if alt in reporter_hits_df.columns:
                                    display_cols.append(alt)
                                    break
                            else:
                                if col_name == 'Well' and 'Row' in reporter_hits_df.columns and 'Col' in reporter_hits_df.columns:
                                    display_cols.extend(['Row', 'Col'])
                        
                        # Add Z-score columns
                        if rank_by_reporter == "B-score" and apply_b_scoring:
                            z_cols = ['B_Z_lptA', 'B_Z_ldtD', 'Z_lptA', 'Z_ldtD']  # Show both for comparison
                        else:
                            z_cols = ['Z_lptA', 'Z_ldtD']
                            if apply_b_scoring:
                                z_cols.extend(['B_Z_lptA', 'B_Z_ldtD'])  # Show B-scores too if available
                        
                        display_cols.extend(z_cols)
                        
                        # Add viability columns
                        viability_cols = [col for col in ['viable_lptA', 'viable_ldtD'] if col in reporter_hits_df.columns]
                        display_cols.extend(viability_cols)
                        
                        # Add hit calling flag
                        display_cols.append('LumHit')
                        
                        # Filter to existing columns and remove duplicates
                        existing_display_cols = list(dict.fromkeys([col for col in display_cols if col in reporter_hits_df.columns]))
                        
                        if existing_display_cols:
                            # Format the dataframe for display
                            reporter_display = reporter_hits_df[existing_display_cols].copy()
                            
                            # Drop the ranking score column if it exists
                            if 'rank_score' in reporter_display.columns:
                                reporter_display = reporter_display.drop(columns=['rank_score'])
                            
                            # Round numeric columns
                            numeric_cols = ['Ratio_lptA', 'Ratio_ldtD'] + [col for col in z_cols if col in reporter_display.columns]
                            for col in numeric_cols:
                                if col in reporter_display.columns and pd.api.types.is_numeric_dtype(reporter_display[col]):
                                    reporter_display[col] = reporter_display[col].round(3)
                            
                            st.dataframe(reporter_display, width='stretch', height=400)
                            
                            # Download reporter hits
                            reporter_csv = reporter_display.to_csv(index=False)
                            st.download_button(
                                f"📥 Download Reporter Hits CSV ({len(reporter_display)} hits)",
                                reporter_csv,
                                file_name=f"reporter_hits_{len(reporter_display)}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.error("Cannot display reporter hits: required columns are missing")
                    else:
                        st.info("No reporter hits found with current criteria.")
                        st.write("**Reporter Hit Criteria:**")
                        st.write("- Z-score ≥ 2.0 for lptA reporter OR ldtD reporter")
                        st.write("- Must pass viability gate (ATP levels above threshold)")
                        
                else:
                    st.info("Reporter hit data not available. Enable multi-stage hit calling mode to see reporter hits.")
            else:
                st.info("👆 Process plate data first to identify reporter hits.")

    # Vitality Hits Tab - only show when multi-stage enabled  
    if vitality_hits_tab is not None:
        with vitality_hits_tab:
            st.header("⚡ Vitality Hits")
            
            if df is not None and len(df) > 0:
                # Check if vitality hit data is available
                if 'vitality_hit' in df.columns:
                    vitality_hits_df = df[df['vitality_hit'] == True].copy()
                    
                    # Controls for Vitality Hits
                    control_col1, control_col2 = st.columns(2)
                    
                    with control_col1:
                        sort_by_vitality = st.selectbox(
                            "Sort by:",
                            ["tolC% (ascending)", "WT% (descending)", "SA% (descending)"],
                            help="Metric to use for sorting vitality hits",
                            key="vitality_sort_by"
                        )
                    
                    with control_col2:
                        vitality_count = len(vitality_hits_df) if len(vitality_hits_df) > 0 else 100
                        display_top_n_vitality = st.number_input(
                            "Display Top N:",
                            min_value=min(10, vitality_count),
                            max_value=min(1000, vitality_count),
                            value=min(100, vitality_count, max(10, vitality_count)),
                            step=1 if vitality_count < 10 else 10,
                            key="vitality_top_n"
                        )
                    
                    # Display vitality hits summary
                    total_wells = len(df)
                    vitality_count = len(vitality_hits_df)
                    vitality_rate = (vitality_count / total_wells * 100) if total_wells > 0 else 0
                    
                    st.write(f"**Found {vitality_count:,} vitality hits ({vitality_rate:.1f}% of {total_wells:,} wells)**")
                    st.write("Vitality hits show the desired growth pattern: **tolC% ≤ 80%** (inhibited), **WT% > 80%** AND **SA% > 80%** (surviving).")
                    
                    if len(vitality_hits_df) > 0:
                        # Sort hits by selected metric
                        if sort_by_vitality == "tolC% (ascending)" and 'tolC%' in vitality_hits_df.columns:
                            vitality_hits_df = vitality_hits_df.sort_values('tolC%', ascending=True).head(display_top_n_vitality)
                        elif sort_by_vitality == "WT% (descending)" and 'WT%' in vitality_hits_df.columns:
                            vitality_hits_df = vitality_hits_df.sort_values('WT%', ascending=False).head(display_top_n_vitality)
                        elif sort_by_vitality == "SA% (descending)" and 'SA%' in vitality_hits_df.columns:
                            vitality_hits_df = vitality_hits_df.sort_values('SA%', ascending=False).head(display_top_n_vitality)
                        else:
                            vitality_hits_df = vitality_hits_df.head(display_top_n_vitality)
                        
                        # Prepare display columns for vitality hits
                        display_cols = []
                        
                        # Essential columns
                        essential_cols = [
                            ('PlateID', ['PlateID', 'Plate_ID', 'plate_id']),
                            ('Well', ['Well', 'WellID', 'well_id'])
                        ]
                        
                        for col_name, alternatives in essential_cols:
                            for alt in alternatives:
                                if alt in vitality_hits_df.columns:
                                    display_cols.append(alt)
                                    break
                            else:
                                if col_name == 'Well' and 'Row' in vitality_hits_df.columns and 'Col' in vitality_hits_df.columns:
                                    display_cols.extend(['Row', 'Col'])
                        
                        # Add OD percentage columns (key for vitality analysis)
                        od_pct_cols = [col for col in ['WT%', 'tolC%', 'SA%'] if col in vitality_hits_df.columns]
                        display_cols.extend(od_pct_cols)
                        
                        # Add raw OD measurements for reference
                        od_raw_cols = [col for col in ['OD_WT', 'OD_tolC', 'OD_SA'] if col in vitality_hits_df.columns]
                        display_cols.extend(od_raw_cols)
                        
                        # Add hit calling flag
                        display_cols.append('OMpatternOK')
                        
                        # Add Z-scores if available (for context)
                        
                        # Filter to existing columns and remove duplicates
                        existing_display_cols = list(dict.fromkeys([col for col in display_cols if col in vitality_hits_df.columns]))
                        
                        if existing_display_cols:
                            # Format the dataframe for display
                            vitality_display = vitality_hits_df[existing_display_cols].copy()
                            
                            # Convert OD percentages to percentage format and round
                            for col in od_pct_cols:
                                if col in vitality_display.columns and pd.api.types.is_numeric_dtype(vitality_display[col]):
                                    vitality_display[col] = (vitality_display[col] * 100).round(1)
                            
                            # Round other numeric columns
                            numeric_cols = [col for col in ['Z_lptA', 'Z_ldtD', 'B_Z_lptA', 'B_Z_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA'] if col in vitality_display.columns]
                            for col in numeric_cols:
                                if col in vitality_display.columns and pd.api.types.is_numeric_dtype(vitality_display[col]):
                                    if col.startswith('OD_'):
                                        vitality_display[col] = vitality_display[col].round(3)
                                    else:
                                        vitality_display[col] = vitality_display[col].round(3)
                            
                            st.dataframe(vitality_display, width='stretch', height=400)
                            
                            # Download vitality hits
                            vitality_csv = vitality_display.to_csv(index=False)
                            st.download_button(
                                f"📥 Download Vitality Hits CSV ({len(vitality_display)} hits)",
                                vitality_csv,
                                file_name=f"vitality_hits_{len(vitality_display)}.csv",
                                mime="text/csv"
                            )
                            
                            # Show vitality criteria summary
                            if len(od_pct_cols) >= 3:
                                st.subheader("Vitality Criteria Summary")
                                criteria_col1, criteria_col2, criteria_col3 = st.columns(3)
                                
                                with criteria_col1:
                                    avg_tolC = vitality_display['tolC%'].mean() if 'tolC%' in vitality_display.columns else 0
                                    st.metric("Avg tolC%", f"{avg_tolC:.1f}%", help="Should be ≤ 80% (inhibited)")
                                
                                with criteria_col2:
                                    avg_WT = vitality_display['WT%'].mean() if 'WT%' in vitality_display.columns else 0
                                    st.metric("Avg WT%", f"{avg_WT:.1f}%", help="Should be > 80% (surviving)")
                                
                                with criteria_col3:
                                    avg_SA = vitality_display['SA%'].mean() if 'SA%' in vitality_display.columns else 0
                                    st.metric("Avg SA%", f"{avg_SA:.1f}%", help="Should be > 80% (surviving)")
                        else:
                            st.error("Cannot display vitality hits: required columns are missing")
                    else:
                        st.info("No vitality hits found with current criteria.")
                        st.write("**Vitality Hit Criteria:**")
                        st.write("- tolC% ≤ 80% (tolC strain growth inhibited)")
                        st.write("- WT% > 80% (wild-type strain survives)")  
                        st.write("- SA% > 80% (SA strain survives)")
                        
                else:
                    st.info("Vitality hit data not available. Enable multi-stage hit calling mode to see vitality hits.")
            else:
                st.info("👆 Process plate data first to identify vitality hits.")
    
    # Hit Calling Tab - only show when multi-stage enabled
    if hit_calling_tab is not None:
        with hit_calling_tab:
            st.header("🔬 Multi-Stage Hit Calling Pipeline")
            
            # Add biological context explanation
            st.markdown("""
            **Scientific Rationale:** This three-stage pipeline identifies outer membrane (OM) permeabilizing compounds 
            through dual biological evidence and selective growth inhibition patterns.
            
            **🧬 Stage 1: Reporter Hits** - Compounds triggering OM stress response  
            **⚡ Stage 2: Vitality Hits** - Compounds with OM-selective growth inhibition  
            **🎯 Stage 3: Platform Hits** - High-confidence OM permeabilizers (both stages)
            """)
            
            if df is not None and len(df) > 0:
                # Show hit calling analysis and statistics
                if hit_calling_results:
                    st.subheader("Pipeline Results")
                    
                    # Display summary statistics
                    summary_stats = hit_calling_results.get('cross_plate_summary', {})
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_wells = summary_stats.get('total_wells', 0)
                        st.metric("Total Wells", f"{total_wells:,}")
                        
                    with col2:
                        reporter_hits = summary_stats.get('total_reporter_hits', 0)
                        reporter_rate = (reporter_hits / total_wells * 100) if total_wells > 0 else 0
                        st.metric("Reporter Hits", f"{reporter_hits:,}", f"{reporter_rate:.1f}%")
                        
                    with col3:
                        vitality_hits = summary_stats.get('total_vitality_hits', 0)
                        vitality_rate = (vitality_hits / total_wells * 100) if total_wells > 0 else 0
                        st.metric("Vitality Hits", f"{vitality_hits:,}", f"{vitality_rate:.1f}%")
                        
                    with col4:
                        platform_hits = summary_stats.get('total_platform_hits', 0)
                        platform_rate = (platform_hits / total_wells * 100) if total_wells > 0 else 0
                        st.metric("Platform Hits", f"{platform_hits:,}", f"{platform_rate:.1f}%")
                    
                    # Multiple visualization options
                    if summary_stats:
                        st.subheader("Hit Calling Pipeline Visualizations")
                        
                        # Get the hit counts
                        total_wells = summary_stats.get('total_wells', 0)
                        reporter_hits = summary_stats.get('total_reporter_hits', 0)
                        vitality_hits = summary_stats.get('total_vitality_hits', 0)
                        platform_hits = summary_stats.get('total_platform_hits', 0)
                        
                        # Use Sankey as the primary visualization
                        st.subheader("🔬 Biological Hit Calling Flow")
                        st.caption("Flow shows compound filtering through biological evidence requirements")
                        
                        # Create Sankey flow diagram
                        fig_sankey = go.Figure(data=[go.Sankey(
                            node = dict(
                                pad = 15,
                                thickness = 20,
                                line = dict(color = "black", width = 0.5),
                                label = [
                                    f"Total Wells<br>({total_wells})",
                                    f"Reporter Hits<br>({reporter_hits})", 
                                    f"Vitality Hits<br>({vitality_hits})",
                                    f"Platform Hits<br>({platform_hits})"
                                ],
                                color = ["lightblue", "orange", "lightgreen", "crimson"]
                            ),
                            link = dict(
                                source = [0, 0, 1, 2],
                                target = [1, 2, 3, 3], 
                                value = [reporter_hits, vitality_hits, platform_hits, platform_hits],
                                color = ["rgba(255,165,0,0.6)", "rgba(144,238,144,0.6)", 
                                       "rgba(220,20,60,0.8)", "rgba(220,20,60,0.8)"]
                            )
                        )])
                        
                        fig_sankey.update_layout(
                            title="OM Permeabilizer Discovery Pipeline",
                            height=400,
                            margin=dict(l=50, r=50, t=60, b=50)
                        )
                        st.plotly_chart(fig_sankey, use_container_width=True)
                    
                    # Hit analysis report
                    st.subheader("📋 Biological Analysis Report")
                    st.caption("Detailed breakdown of hit calling results with biological interpretation")
                    from analytics.hit_calling import format_hit_calling_report
                    report_text = format_hit_calling_report(hit_calling_results)
                    st.text_area("Hit Calling Report", report_text, height=300)
                    
                else:
                    st.info("🔬 Hit calling analysis will appear here after processing data. The pipeline will identify compounds that disrupt the outer membrane through biological reporter activation and selective growth inhibition.")
            else:
                st.info("📊 Process plate data to see multi-stage hit calling analysis for outer membrane permeabilizer discovery.")
    
    # Visualizations Tab
    with viz_tab:
        st.header("Visualizations")
        
        if df is not None and len(df) > 0:
            # Create 2x2 grid
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Histogram of Raw Z_lptA
                st.subheader("Raw Z_lptA Distribution")
                if 'Z_lptA' in df.columns:
                    fig1 = px.histogram(
                        df, 
                        x='Z_lptA', 
                        nbins=50,
                        title="Raw Z_lptA Distribution",
                        color_discrete_sequence=['steelblue']
                    )
                    fig1.add_vline(x=z_cutoff, line_dash="dash", line_color="red", annotation_text=f"Threshold: {z_cutoff}")
                    fig1.add_vline(x=-z_cutoff, line_dash="dash", line_color="red")
                    st.plotly_chart(fig1, width='stretch')
                else:
                    st.warning("Z_lptA column not available")
            
            with viz_col2:
                # Histogram of B_Z_lptA (if available)
                st.subheader("B-score Z_lptA Distribution")
                if apply_b_scoring and 'B_Z_lptA' in df.columns:
                    fig2 = px.histogram(
                        df, 
                        x='B_Z_lptA', 
                        nbins=50,
                        title="B-score Z_lptA Distribution",
                        color_discrete_sequence=['orange']
                    )
                    fig2.add_vline(x=z_cutoff, line_dash="dash", line_color="red", annotation_text=f"Threshold: {z_cutoff}")
                    fig2.add_vline(x=-z_cutoff, line_dash="dash", line_color="red")
                    st.plotly_chart(fig2, width='stretch')
                elif apply_b_scoring:
                    st.warning("B_Z_lptA column not available")
                else:
                    st.info("B-scoring not enabled")
            
            # Second row
            viz_col3, viz_col4 = st.columns(2)
            
            with viz_col3:
                # Scatter plot of ratios
                st.subheader("Ratio Correlation")
                if all(col in df.columns for col in ['Ratio_lptA', 'Ratio_ldtD', 'PlateID']):
                    fig3 = px.scatter(
                        df,
                        x='Ratio_lptA',
                        y='Ratio_ldtD',
                        color='PlateID',
                        title="Ratio_lptA vs Ratio_ldtD",
                        hover_data=['Well'] if 'Well' in df.columns else None
                    )
                    st.plotly_chart(fig3, width='stretch')
                else:
                    st.warning("Required ratio columns not available")
            
            with viz_col4:
                # Viability counts by plate
                st.subheader("Viability by Plate")
                if 'viable_lptA' in df.columns and 'PlateID' in df.columns:
                    viability_counts = df.groupby('PlateID')['viable_lptA'].value_counts().unstack(fill_value=0)
                    
                    fig4 = px.bar(
                        x=viability_counts.index,
                        y=[viability_counts[True], viability_counts[False]],
                        title="Viability Counts by Plate",
                        labels={'x': 'PlateID', 'y': 'Count'},
                        color_discrete_map={0: 'lightcoral', 1: 'lightblue'}
                    )
                    fig4.update_layout(showlegend=True)
                    st.plotly_chart(fig4, width='stretch')
                else:
                    st.warning("Viability data not available")
        else:
            st.info("👆 Process plate data first to see visualizations.")
    
    # Heatmaps Tab
    with heatmaps_tab:
        st.header("Heatmaps")
        
        if df is not None and len(df) > 0 and 'PlateID' in df.columns:
            # Controls
            heatmap_col1, heatmap_col2 = st.columns(2)
            
            with heatmap_col1:
                # Metric selection
                available_metrics = []
                for metric in ['Z_lptA', 'Z_ldtD', 'B_Z_lptA', 'B_Z_ldtD', 'Ratio_lptA', 'Ratio_ldtD', 'OD_norm_WT', 'OD_norm_tolC', 'OD_norm_SA']:
                    if metric in df.columns:
                        available_metrics.append(metric)
                
                selected_metric = st.selectbox(
                    "Metric:",
                    available_metrics,
                    help="Select metric to visualize in heatmap"
                )
            
            with heatmap_col2:
                # Plate selection
                plate_ids = sorted(df['PlateID'].unique())
                selected_plate = st.selectbox(
                    "Plate:",
                    plate_ids,
                    help="Select plate to visualize"
                )
            
            if selected_metric and selected_plate:
                # Create side-by-side heatmaps
                heatmap_col_left, heatmap_col_right = st.columns(2)
                
                with heatmap_col_left:
                    # Selected metric heatmap
                    fig_main = create_plate_heatmap(df, selected_metric, selected_plate)
                    st.plotly_chart(fig_main, width='stretch')
                
                with heatmap_col_right:
                    # Comparison metric (alternate between Z and B-score if available)
                    comparison_metric = None
                    if selected_metric == 'Z_lptA' and 'B_Z_lptA' in df.columns:
                        comparison_metric = 'B_Z_lptA'
                    elif selected_metric == 'B_Z_lptA' and 'Z_lptA' in df.columns:
                        comparison_metric = 'Z_lptA'
                    elif selected_metric == 'Z_ldtD' and 'B_Z_ldtD' in df.columns:
                        comparison_metric = 'B_Z_ldtD'
                    elif selected_metric == 'B_Z_ldtD' and 'Z_ldtD' in df.columns:
                        comparison_metric = 'Z_ldtD'
                    elif 'Ratio_lptA' in df.columns and selected_metric != 'Ratio_lptA':
                        comparison_metric = 'Ratio_lptA'
                    
                    if comparison_metric:
                        fig_comparison = create_plate_heatmap(df, comparison_metric, selected_plate)
                        st.plotly_chart(fig_comparison, width='stretch')
                    else:
                        st.info("No suitable comparison metric available")
        else:
            st.info("👆 Process plate data first to see heatmaps.")
    
    # QC Report Tab
    with qc_tab:
        st.header("QC Report")
        
        if df is not None and len(df) > 0:
            # Load configuration
            config = load_config()
            
            # QC Dashboard (new advanced visualization) - Temporarily disabled for debugging
            if False:  # config.get('visualization_features', {}).get('qc_dashboard', {}).get('enabled', True):
                st.subheader("🔬 Quality Control Dashboard")
                
                try:
                    st.info("QC Dashboard temporarily disabled for debugging")
                    # qc_dashboard = QCDashboard(config)
                    # qc_dashboard.render_dashboard(df)
                except Exception as e:
                    st.error(f"Error rendering QC Dashboard: {str(e)}")
                    logger.error(f"QC Dashboard error: {e}", exc_info=True)
                
                st.divider()
            
            st.subheader("📋 Quality Control Report Generation")
            st.write("**Quality Control Report Generation**")
            
            # Quick reference formulas
            with st.expander("📐 Calculation Formulas Reference", expanded=False):
                st.markdown("**Core Calculations:**")
                
                st.markdown("• **Reporter Ratios:** (β-galactosidase signal / ATP viability)")
                st.latex(r"Ratio_{lptA} = \frac{BG_{lptA}}{BT_{lptA}}, \quad Ratio_{ldtD} = \frac{BG_{ldtD}}{BT_{ldtD}}")
                
                st.markdown("• **Robust Z-scores:** (MAD-based, outlier-resistant)")
                st.latex(r"Z = \frac{x - \text{median}(X)}{1.4826 \times \text{MAD}(X)}")
                
                st.markdown("• **Viability Gating:** (ATP-based cell viability filter)")
                st.latex(r"viable = BT \geq f \times \text{median}(BT_{plate}), \quad f = 0.3")
                
                st.markdown("• **OD Normalization:** (plate-relative growth)")
                st.latex(r"OD_{norm} = \frac{OD}{\text{median}(OD_{plate})}")
                
                st.markdown("**Hit Calling Logic:**")
                
                st.markdown("• **Reporter Hit:**")
                st.latex(r"reporter\_hit = (Z_{lptA} \geq 2.0 \lor Z_{ldtD} \geq 2.0) \land viable")
                
                st.markdown("• **Vitality Hit:**")
                st.latex(r"vitality\_hit = (WT > 0.8) \land (\Delta tolC \leq 0.8) \land (SA > 0.8)")
                
                st.markdown("• **Platform Hit:**")
                st.latex(r"platform\_hit = reporter\_hit \land vitality\_hit")
                
                st.markdown("**B-score Correction (when enabled):**")
                
                st.markdown("• Median-polish iteration:")
                st.latex(r"X'_{ij} = X_{ij} - \text{median}(row_i), \quad X''_{ij} = X'_{ij} - \text{median}(col_j)")
                
                st.markdown("• Robust scaling:")
                st.latex(r"B = \frac{X''}{1.4826 \times \text{MAD}(X'')}")
                
                st.markdown("**Statistical Definitions:**")
                
                st.markdown("• **MAD (Median Absolute Deviation):**")
                st.latex(r"MAD = \text{median}(|X_i - \text{median}(X)|)")
                
                st.markdown("• **Consistency Factor:**")
                st.latex(r"1.4826 \approx \Phi^{-1}(0.75)")
                st.caption("Inverse normal CDF at 75th percentile for normal distribution consistency")
                st.markdown("• **Robustness:** Methods resist up to 50% outlier contamination")
            
            # Publication references section
            with st.expander("📚 Key Publications & References", expanded=False):
                st.markdown("""
                **Primary Literature:**
                
                **🔬 Outer Membrane Biology & LPS Transport:**
                1. **Silhavy, T.J., Kahne, D. and Walker, S.** (2010) 'The Bacterial Cell Envelope', *Cold Spring Harbor Perspectives in Biology*, 2(5), p. a000414.
                   - Foundational review of Gram-negative cell envelope structure and function
                
                2. **Yoon, Y., Song, S.** (2024) 'Structural Insights into the Lipopolysaccharide Transport (Lpt) System as a Novel Antibiotic Target', *J Microbiol.* 62, 261–275.
                   - Recent structural biology of LPS transport machinery
                
                3. **Martorana, A.M. et al.** (2011) 'Complex transcriptional organization regulates an Escherichia coli locus implicated in lipopolysaccharide biogenesis' *Research in Microbiology*, 162(5), pp. 470–482.
                   - lptA gene regulation and σE stress response pathway
                
                **⚡ Peptidoglycan Remodeling & Stress Response:**
                4. **Morè, N. et al.** (2019) 'Peptidoglycan Remodeling Enables Escherichia coli To Survive Severe Outer Membrane Assembly Defect' *mBio*, 10(1), p. 10.1128/mbio.02729-18.
                   - ldtD function and 3-3 crosslink formation during OM stress
                
                **🎯 OM Permeabilization & Antibiotic Sensitization:**
                5. **Chan, L.W. et al.** (2021) 'Selective Permeabilization of Gram-Negative Bacterial Membranes Using Multivalent Peptide Constructs for Antibiotic Sensitization' *ACS Infectious Diseases*, 7(4), p. 721.
                   - Proof-of-concept for OM permeabilizer + antibiotic combination therapy
                
                6. **Zhu, S. et al.** (2024) 'The inactivation of tolC sensitizes Escherichia coli to perturbations in lipopolysaccharide transport,' *iScience*, 27(5), p. 109592.
                   - ΔtolC strain hypersensitivity to OM perturbation
                
                **📊 Statistical Methods:**
                7. **Tukey, J.W.** (1977) 'Exploratory Data Analysis', Addison-Wesley.
                   - Median polish algorithm for B-score calculation
                
                8. **Rousseeuw, P.J. and Croux, C.** (1993) 'Alternatives to the median absolute deviation', *Journal of the American Statistical Association*, 88, pp. 1273-1283.
                   - Robust statistics and MAD-based scaling
                
                **🏆 Funding Acknowledgment:**
                - This work is supported by the **BREAKthrough project**, funded by the European Union
                - Grant focus: Novel antimicrobial strategies against Gram-negative pathogens
                """)
            
            st.divider()
            
            # Report options
            report_col1, report_col2 = st.columns(2)
            
            with report_col1:
                include_formulas = st.checkbox("Include Formulas", value=True)
                include_methodology = st.checkbox("Include Methodology", value=True)
            
            with report_col2:
                include_edge_effects = st.checkbox("Include Edge Effects", value=bool(edge_results))
                include_bscore_details = st.checkbox("Include B-score Details", value=apply_b_scoring)
            
            if st.button("📋 Generate PDF Report"):
                with st.spinner("Generating QC report..."):
                    # Create report manifest
                    manifest = {
                        'report_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'plates_processed': summary.get('plate_count', 0),
                        'total_wells': summary.get('total_wells', 0),
                        'viability_threshold': viability_threshold,
                        'z_cutoff': z_cutoff,
                        'b_scoring_applied': apply_b_scoring,
                        'edge_effects_detected': len([r for r in edge_results if r.warning_level != WarningLevel.INFO]) if edge_results else 0,
                        'sections_included': {
                            'formulas': include_formulas,
                            'methodology': include_methodology,
                            'edge_effects': include_edge_effects,
                            'bscore_details': include_bscore_details
                        }
                    }
                    
                    # Display manifest
                    st.subheader("Report Manifest")
                    st.code(yaml.dump(manifest, default_flow_style=False), language='yaml')
                    
                    # For now, create a comprehensive text report
                    # (PDF generation would require additional libraries like reportlab)
                    report_sections = []
                    
                    # Header
                    report_sections.append("# Plate Data Processing QC Report")
                    report_sections.append(f"Generated: {manifest['report_date']}")
                    report_sections.append("")
                    
                    # Summary
                    report_sections.append("## Summary")
                    report_sections.append(f"- Plates processed: {manifest['plates_processed']}")
                    report_sections.append(f"- Total wells: {manifest['total_wells']}")
                    report_sections.append(f"- Viability threshold: {manifest['viability_threshold']}")
                    report_sections.append(f"- Z-score cutoff: {manifest['z_cutoff']}")
                    report_sections.append(f"- B-scoring applied: {manifest['b_scoring_applied']}")
                    report_sections.append("")
                    
                    # Edge effects
                    if include_edge_effects and edge_results:
                        report_sections.append("## Edge Effects Analysis")
                        for result in edge_results:
                            report_sections.append(f"### Plate {result.plate_id}")
                            report_sections.append(f"- Warning level: {result.warning_level.value}")
                            report_sections.append(f"- Effect size (d): {result.effect_size_d:.3f}")
                            report_sections.append(f"- Edge wells: {result.n_edge_wells}")
                            report_sections.append(f"- Interior wells: {result.n_interior_wells}")
                            if not np.isnan(result.row_correlation):
                                report_sections.append(f"- Row correlation: {result.row_correlation:.3f}")
                            if not np.isnan(result.col_correlation):
                                report_sections.append(f"- Column correlation: {result.col_correlation:.3f}")
                            report_sections.append("")
                    
                    # Complete Scientific Formulas
                    if include_formulas:
                        report_sections.append("## Scientific Calculation Formulas")
                        
                        report_sections.append("### 1. Reporter Signal Processing")
                        report_sections.append("**BetaGlo/BacTiter Ratios (Normalized Reporter Activity):**")
                        report_sections.append("- Ratio_lptA = BG_lptA / BT_lptA")
                        report_sections.append("- Ratio_ldtD = BG_ldtD / BT_ldtD")
                        report_sections.append("")
                        report_sections.append("**Biochemical Basis:**")
                        report_sections.append("- BG (BetaGlo): β-galactosidase activity from lacZ reporter")
                        report_sections.append("- BT (BacTiter): ATP-dependent luciferase activity (viability)")
                        report_sections.append("- Ratio normalizes reporter signal to viable cell count")
                        report_sections.append("")
                        
                        report_sections.append("### 2. Growth Measurements")
                        report_sections.append("**OD Normalization (Plate-Relative Growth):**")
                        report_sections.append("- OD_WT_norm = OD_WT / median(OD_WT_plate)")
                        report_sections.append("- OD_tolC_norm = OD_tolC / median(OD_tolC_plate)")
                        report_sections.append("- OD_SA_norm = OD_SA / median(OD_SA_plate)")
                        report_sections.append("")
                        
                        report_sections.append("### 3. Robust Statistical Scoring")
                        report_sections.append("**Robust Z-scores (MAD-based, outlier-resistant):**")
                        report_sections.append("- Z = (value - median) / (1.4826 × MAD)")
                        report_sections.append("- MAD = median(|values - median(values)|)")
                        report_sections.append("- 1.4826 = consistency factor for normal distributions")
                        report_sections.append("")
                        report_sections.append("**Statistical Advantages:**")
                        report_sections.append("- Resistant to outliers (up to 50% contamination)")
                        report_sections.append("- No assumption of normal distribution")
                        report_sections.append("- More stable than mean/standard deviation")
                        report_sections.append("")
                        
                        if apply_b_scoring:
                            report_sections.append("### 4. B-score Spatial Correction")
                            report_sections.append("**Median Polish Algorithm:**")
                            report_sections.append("1. Subtract row medians: X'ᵢⱼ = Xᵢⱼ - median(row_i)")
                            report_sections.append("2. Subtract column medians: X''ᵢⱼ = X'ᵢⱼ - median(col_j)")
                            report_sections.append("3. Iterate until convergence (tolerance = 1e-6)")
                            report_sections.append("4. Apply robust scaling: B = X'' / (1.4826 × MAD(X''))")
                            report_sections.append("")
                        
                        report_sections.append("### 5. Viability Gating")
                        report_sections.append("**ATP-based Viability Filter:**")
                        report_sections.append(f"- viability_ok = BT ≥ {viability_threshold} × median(BT_plate)")
                        report_sections.append("- Excludes wells with insufficient ATP for reliable measurements")
                        report_sections.append("- Based on D-luciferin + ATP → oxyluciferin + light reaction")
                        report_sections.append("")
                        
                        report_sections.append("### 6. Multi-Stage Hit Calling")
                        report_sections.append("**Stage 1 - Reporter Hits:**")
                        report_sections.append(f"- lptA_hit = (Z_lptA ≥ {z_cutoff}) AND viability_ok")
                        report_sections.append(f"- ldtD_hit = (Z_ldtD ≥ {z_cutoff}) AND viability_ok")
                        report_sections.append("- reporter_hit = lptA_hit OR ldtD_hit")
                        report_sections.append("")
                        report_sections.append("**Stage 2 - Vitality Hits:**")
                        report_sections.append("- WT_resist = OD_WT_norm > 0.8 (intact OM protection)")
                        report_sections.append("- tolC_sensitive = OD_tolC_norm ≤ 0.8 (compromised OM vulnerability)")
                        report_sections.append("- SA_unaffected = OD_SA_norm > 0.8 (no OM target)")
                        report_sections.append("- vitality_hit = WT_resist AND tolC_sensitive AND SA_unaffected")
                        report_sections.append("")
                        report_sections.append("**Stage 3 - Platform Hits:**")
                        report_sections.append("- platform_hit = reporter_hit AND vitality_hit")
                        report_sections.append("- High-confidence OM permeabilizers with dual evidence")
                        report_sections.append("")
                    
                    # Methodology
                    if include_methodology:
                        report_sections.append("## Methodology")
                        report_sections.append("This analysis follows the plate data processing pipeline:")
                        report_sections.append("1. Data validation and column mapping")
                        report_sections.append("2. Ratio calculations (BG/BT)")
                        report_sections.append("3. Robust Z-score calculation using median and MAD")
                        report_sections.append("4. Viability gating based on ATP levels")
                        if apply_b_scoring:
                            report_sections.append("5. B-scoring for row/column bias correction")
                        report_sections.append("6. Edge effect detection and quality assessment")
                        report_sections.append("")
                    
                    report_text = "\n".join(report_sections)
                    
                    # Offer download
                    st.download_button(
                        "📥 Download Text Report",
                        report_text,
                        file_name=f"qc_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                    
                    st.success("Report generated successfully!")
        else:
            st.info("👆 Process plate data first to generate QC report.")
    
    # BREAKthrough project footer
    st.markdown("""
    ---
    <div style='text-align: center; padding: 2rem 0 1rem 0; color: #6b7280;'>
        <p style='margin: 0; font-size: 0.9rem;'>
            🏆 <strong>BREAKthrough Project</strong> - Novel Antimicrobial Strategies Against Gram-Negative Pathogens
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.8rem;'>
            🇪🇺 Funded by the European Union | 🧬 Advancing Combination Therapy Research
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.7rem; color: #9ca3af;'>
            Platform for identifying outer membrane permeabilizers as antibiotic adjuvants
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()