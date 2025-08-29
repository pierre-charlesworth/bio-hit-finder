"""Quick test to verify all imports work correctly."""

try:
    from core.plate_processor import PlateProcessor
    print("[OK] PlateProcessor imported successfully")
except Exception as e:
    print(f"[FAIL] PlateProcessor import failed: {e}")

try:
    from analytics.edge_effects import EdgeEffectDetector, WarningLevel
    print("[OK] EdgeEffectDetector imported successfully")
except Exception as e:
    print(f"[FAIL] EdgeEffectDetector import failed: {e}")

try:
    from analytics.bscore import BScoreProcessor
    print("[OK] BScoreProcessor imported successfully")
except Exception as e:
    print(f"[FAIL] BScoreProcessor import failed: {e}")

try:
    from sample_data_generator import create_demo_data
    print("[OK] sample_data_generator imported successfully")
except Exception as e:
    print(f"[FAIL] sample_data_generator import failed: {e}")

try:
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import yaml
    print("[OK] All external dependencies imported successfully")
except Exception as e:
    print(f"[FAIL] External dependencies import failed: {e}")

print("\nTesting demo data generation...")
try:
    from sample_data_generator import create_demo_data
    demo_df = create_demo_data()
    print(f"[OK] Demo data created: {len(demo_df)} rows, {len(demo_df.columns)} columns")
    print(f"  Plates: {demo_df['PlateID'].unique()}")
    print(f"  Required columns present: {all(col in demo_df.columns for col in ['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA'])}")
except Exception as e:
    print(f"[FAIL] Demo data generation failed: {e}")

print("\nAll import tests completed!")