"""Main FastAPI application for bio-hit-finder.

This serves both the API endpoints and the React frontend static files.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging
from typing import Dict, Any, Optional
import pandas as pd
import io
import json

from core.plate_processor import PlateProcessor
from analytics import (
    MultiStageHitCaller, 
    MultiStageConfig, 
    VitalityConfig,
    run_multi_stage_analysis
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BREAKthrough OM Screening Platform API",
    description="API for biological screening platform with B-scoring analysis",
    version="1.0.0"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes (to be implemented)
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bio-hit-finder"}

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint for development."""
    return {"message": "Backend API is working!"}

# Multi-stage Hit Calling Endpoints

@app.post("/api/v1/analyze/multi-stage")
async def analyze_multi_stage_hits(file: UploadFile = File(...), config: Optional[str] = None):
    """Analyze uploaded plate data using multi-stage hit calling.
    
    Args:
        file: Excel/CSV file with plate data
        config: JSON string with analysis configuration (optional)
    
    Returns:
        Dict with analysis results and hit summary
    """
    try:
        # Parse configuration
        analysis_config = {}
        if config:
            try:
                analysis_config = json.loads(config)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config parameter")
        
        # Load file data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO((await file.read()).decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(await file.read()))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel files.")
        
        # Initialize plate processor
        processor = PlateProcessor()
        
        # Process the plate data (this includes our new multi-stage hit calling)
        processed_df = processor.process_plate(df, plate_id="uploaded_plate", config=analysis_config)
        
        # Generate summary statistics
        summary = _generate_multi_stage_summary(processed_df)
        
        # Convert DataFrame to JSON-serializable format
        results = processed_df.to_dict(orient='records')
        
        return {
            "success": True,
            "results": results,
            "summary": summary,
            "total_wells": len(processed_df),
            "file_name": file.filename
        }
        
    except Exception as e:
        logger.error(f"Multi-stage analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/v1/analyze/vitality")  
async def analyze_vitality_only(file: UploadFile = File(...), config: Optional[str] = None):
    """Analyze vitality patterns only from uploaded plate data.
    
    Args:
        file: Excel/CSV file with OD measurements
        config: JSON string with vitality configuration (optional)
        
    Returns:
        Dict with vitality analysis results
    """
    try:
        # Parse vitality configuration
        vitality_config = VitalityConfig()
        if config:
            try:
                config_dict = json.loads(config)
                vitality_config = VitalityConfig(
                    tolc_threshold=config_dict.get('tolc_threshold', 0.8),
                    wt_threshold=config_dict.get('wt_threshold', 0.8),
                    sa_threshold=config_dict.get('sa_threshold', 0.8)
                )
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config parameter")
        
        # Load file data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO((await file.read()).decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(await file.read()))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel files.")
        
        # Run vitality-only analysis
        from analytics import VitalityAnalyzer
        analyzer = VitalityAnalyzer(vitality_config)
        
        result_df = analyzer.detect_vitality_hits(df)
        summary = analyzer.generate_vitality_summary(result_df)
        
        # Convert to JSON-serializable format
        results = result_df.to_dict(orient='records')
        
        return {
            "success": True,
            "results": results, 
            "summary": summary,
            "total_wells": len(result_df),
            "file_name": file.filename,
            "analysis_type": "vitality_only"
        }
        
    except Exception as e:
        logger.error(f"Vitality analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vitality analysis failed: {str(e)}")

@app.get("/api/v1/config/multi-stage-defaults")
async def get_multi_stage_defaults():
    """Get default configuration parameters for multi-stage analysis."""
    return {
        "z_threshold": 2.0,
        "viability_column": "PassViab",
        "reporter_columns": ["Z_lptA", "Z_ldtD"],
        "vitality_config": {
            "tolc_threshold": 0.8,
            "wt_threshold": 0.8, 
            "sa_threshold": 0.8
        },
        "require_both_stages": True,
        "include_partial_hits": True
    }

@app.post("/api/v1/analyze/demo")
async def analyze_demo_data(config: Optional[Dict[str, Any]] = None):
    """Analyze demo dual-readout data for testing multi-stage functionality.
    
    Returns:
        Dict with demo analysis results
    """
    try:
        # Generate demo dual-readout data
        demo_data = _generate_demo_dual_readout_data()
        
        # Use provided config or defaults
        if config is None:
            config = {}
        
        # Run multi-stage analysis
        results_df, summary = run_multi_stage_analysis(demo_data, config)
        
        # Convert to JSON-serializable format
        results = results_df.to_dict(orient='records')
        
        return {
            "success": True,
            "results": results,
            "summary": summary,
            "total_wells": len(results_df),
            "file_name": "demo_dual_readout_data.csv",
            "analysis_type": "demo_multi_stage"
        }
        
    except Exception as e:
        logger.error(f"Demo analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demo analysis failed: {str(e)}")

def _generate_multi_stage_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics from multi-stage analysis results."""
    total_wells = len(df)
    
    summary = {
        "total_wells": total_wells,
        "stage1_reporter_hits": int(df.get('Stage1_ReporterHit', pd.Series([False])).sum()),
        "stage2_vitality_hits": int(df.get('Stage2_VitalityHit', pd.Series([False])).sum()),
        "stage3_platform_hits": int(df.get('Stage3_PlatformHit', pd.Series([False])).sum()),
        "dual_readout_detected": 'Stage1_ReporterHit' in df.columns and 'Stage2_VitalityHit' in df.columns
    }
    
    # Calculate hit rates
    for stage in ['stage1_reporter_hits', 'stage2_vitality_hits', 'stage3_platform_hits']:
        rate_key = stage.replace('hits', 'hit_rate') 
        summary[rate_key] = summary[stage] / total_wells if total_wells > 0 else 0
        
    # Hit type distribution if available
    if 'Stage3_HitType' in df.columns:
        summary['hit_type_distribution'] = df['Stage3_HitType'].value_counts().to_dict()
        
    return summary

def _generate_demo_dual_readout_data() -> pd.DataFrame:
    """Generate synthetic dual-readout data for demo purposes."""
    import numpy as np
    
    np.random.seed(42)  # Reproducible demo data
    n_wells = 80
    
    # Generate well positions
    well_data = []
    for row in range(8):  # A-H
        for col in range(10):  # 1-10
            well_id = f"{chr(65+row)}{col+1:02d}"
            well_data.append(well_id)
    
    # Generate demo data
    demo_df = pd.DataFrame({
        'Well': well_data,
        # Reporter measurements (BG/BT ratios already calculated)
        'Ratio_lptA': np.random.lognormal(0, 0.5, n_wells),
        'Ratio_ldtD': np.random.lognormal(0, 0.5, n_wells),
        # OD measurements for vitality analysis
        'OD_WT': np.random.lognormal(0.1, 0.3, n_wells),
        'OD_tolC': np.random.lognormal(-0.2, 0.4, n_wells),  # Lower on average
        'OD_SA': np.random.lognormal(0.05, 0.3, n_wells),
        # Viability flags
        'PassViab': np.random.choice([True, False], n_wells, p=[0.85, 0.15])
    })
    
    # Calculate Z-scores for reporter ratios
    from core.statistics import calculate_robust_zscore
    demo_df['Z_lptA'] = calculate_robust_zscore(demo_df['Ratio_lptA'])
    demo_df['Z_ldtD'] = calculate_robust_zscore(demo_df['Ratio_ldtD'])
    
    return demo_df

# Serve React static files
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    logger.info(f"Serving React frontend from {frontend_dist}")
else:
    logger.warning(f"Frontend dist directory not found at {frontend_dist}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)