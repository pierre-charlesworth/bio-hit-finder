"""Sample data generator for bio-hit-finder platform demonstration.

This module creates realistic sample plate data that can be used to test
and demonstrate the platform functionality without requiring real experimental data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import random


def generate_sample_plate(
    plate_id: str = "DEMO001",
    n_rows: int = 8, 
    n_cols: int = 12,
    add_hits: bool = True,
    add_edge_effects: bool = True,
    add_noise: bool = True,
    viability_issues: float = 0.05
) -> pd.DataFrame:
    """Generate a single sample plate with realistic biological data patterns.
    
    Args:
        plate_id: Identifier for the plate
        n_rows: Number of rows (default 8 for 96-well)
        n_cols: Number of columns (default 12 for 96-well)
        add_hits: Whether to include potential hit wells
        add_edge_effects: Whether to simulate edge effects
        add_noise: Whether to add realistic noise
        viability_issues: Fraction of wells with viability problems
        
    Returns:
        DataFrame with sample plate data
    """
    np.random.seed(hash(plate_id) % 2**32)  # Reproducible but plate-specific
    
    # Generate well positions
    rows = []
    cols = []
    wells = []
    
    row_labels = [chr(ord('A') + i) for i in range(n_rows)]
    
    for i, row_label in enumerate(row_labels):
        for j in range(1, n_cols + 1):
            rows.append(row_label)
            cols.append(j)
            wells.append(f"{row_label}{j:02d}")
    
    n_wells = len(wells)
    
    # Base signal levels (realistic ranges)
    base_bg_lptA = np.random.normal(1000, 200, n_wells)
    base_bt_lptA = np.random.normal(2000, 300, n_wells)
    base_bg_ldtD = np.random.normal(800, 150, n_wells)
    base_bt_ldtD = np.random.normal(1500, 250, n_wells)
    
    # OD measurements
    base_od_wt = np.random.normal(0.5, 0.1, n_wells)
    base_od_tolc = np.random.normal(0.4, 0.08, n_wells)
    base_od_sa = np.random.normal(0.45, 0.09, n_wells)
    
    # Add systematic edge effects if requested
    if add_edge_effects:
        for i, (row, col) in enumerate(zip(rows, cols)):
            row_idx = ord(row) - ord('A')
            col_idx = col - 1
            
            # Edge wells have 15% lower BG signals (evaporation effect)
            if row_idx == 0 or row_idx == n_rows - 1 or col_idx == 0 or col_idx == n_cols - 1:
                edge_factor = 0.85
                base_bg_lptA[i] *= edge_factor
                base_bg_ldtD[i] *= edge_factor
            
            # Corner wells have additional issues
            if ((row_idx == 0 or row_idx == n_rows - 1) and 
                (col_idx == 0 or col_idx == n_cols - 1)):
                corner_factor = 0.75
                base_bg_lptA[i] *= corner_factor
                base_bg_ldtD[i] *= corner_factor
    
    # Add potential hits if requested
    if add_hits:
        # 5-10 strong hits
        n_strong_hits = random.randint(5, 10)
        hit_indices = np.random.choice(n_wells, n_strong_hits, replace=False)
        
        for idx in hit_indices:
            # Strong inhibition: BG signal drops significantly
            hit_strength = np.random.uniform(0.2, 0.5)  # 20-50% of normal
            base_bg_lptA[idx] *= hit_strength
            base_bg_ldtD[idx] *= hit_strength
        
        # 10-20 moderate hits
        n_moderate_hits = random.randint(10, 20)
        moderate_indices = np.random.choice(
            [i for i in range(n_wells) if i not in hit_indices], 
            n_moderate_hits, 
            replace=False
        )
        
        for idx in moderate_indices:
            hit_strength = np.random.uniform(0.6, 0.8)  # 60-80% of normal
            base_bg_lptA[idx] *= hit_strength
            base_bg_ldtD[idx] *= hit_strength
    
    # Add viability issues
    n_low_viability = int(viability_issues * n_wells)
    if n_low_viability > 0:
        low_viab_indices = np.random.choice(n_wells, n_low_viability, replace=False)
        for idx in low_viab_indices:
            viability_factor = np.random.uniform(0.1, 0.3)
            base_bt_lptA[idx] *= viability_factor
            base_bt_ldtD[idx] *= viability_factor
            base_od_wt[idx] *= viability_factor
            base_od_tolc[idx] *= viability_factor
            base_od_sa[idx] *= viability_factor
    
    # Add measurement noise if requested
    if add_noise:
        noise_factor = 0.05  # 5% CV
        base_bg_lptA *= np.random.normal(1.0, noise_factor, n_wells)
        base_bt_lptA *= np.random.normal(1.0, noise_factor, n_wells)
        base_bg_ldtD *= np.random.normal(1.0, noise_factor, n_wells)
        base_bt_ldtD *= np.random.normal(1.0, noise_factor, n_wells)
        base_od_wt *= np.random.normal(1.0, noise_factor, n_wells)
        base_od_tolc *= np.random.normal(1.0, noise_factor, n_wells)
        base_od_sa *= np.random.normal(1.0, noise_factor, n_wells)
    
    # Ensure positive values
    measurements = {
        'BG_lptA': np.maximum(base_bg_lptA, 10),
        'BT_lptA': np.maximum(base_bt_lptA, 50),
        'BG_ldtD': np.maximum(base_bg_ldtD, 10),
        'BT_ldtD': np.maximum(base_bt_ldtD, 50),
        'OD_WT': np.maximum(base_od_wt, 0.01),
        'OD_tolC': np.maximum(base_od_tolc, 0.01),
        'OD_SA': np.maximum(base_od_sa, 0.01),
    }
    
    # Create DataFrame
    df = pd.DataFrame({
        'PlateID': [plate_id] * n_wells,
        'Well': wells,
        'Row': rows,
        'Col': cols,
        **{k: np.round(v, 1) for k, v in measurements.items()}
    })
    
    # Add some missing values randomly (1-2%)
    missing_rate = 0.015
    for col in ['BG_lptA', 'BT_lptA', 'BG_ldtD', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']:
        n_missing = int(missing_rate * n_wells)
        if n_missing > 0:
            missing_indices = np.random.choice(n_wells, n_missing, replace=False)
            df.loc[missing_indices, col] = np.nan
    
    return df


def generate_sample_dataset(
    n_plates: int = 3,
    plate_prefix: str = "DEMO",
    output_dir: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """Generate a complete sample dataset with multiple plates.
    
    Args:
        n_plates: Number of plates to generate
        plate_prefix: Prefix for plate IDs
        output_dir: Directory to save files (optional)
        
    Returns:
        Dictionary mapping plate IDs to DataFrames
    """
    plates = {}
    
    for i in range(n_plates):
        plate_id = f"{plate_prefix}{i+1:03d}"
        
        # Vary the characteristics across plates
        plate_df = generate_sample_plate(
            plate_id=plate_id,
            add_hits=True,
            add_edge_effects=(i % 2 == 0),  # Alternate edge effects
            add_noise=True,
            viability_issues=0.02 + 0.03 * (i / n_plates)  # Increasing issues
        )
        
        plates[plate_id] = plate_df
    
    # Save files if output directory specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Individual CSV files
        for plate_id, df in plates.items():
            csv_path = output_dir / f"{plate_id}.csv"
            df.to_csv(csv_path, index=False)
        
        # Combined Excel file with multiple sheets
        excel_path = output_dir / f"{plate_prefix}_combined.xlsx"
        with pd.ExcelWriter(excel_path) as writer:
            for plate_id, df in plates.items():
                df.to_excel(writer, sheet_name=plate_id, index=False)
        
        # Combined CSV
        combined_df = pd.concat(plates.values(), ignore_index=True)
        combined_csv_path = output_dir / f"{plate_prefix}_combined.csv"
        combined_df.to_csv(combined_csv_path, index=False)
        
        print(f"Sample data saved to {output_dir}")
        print(f"Files created:")
        print(f"  - {len(plates)} individual CSV files")
        print(f"  - 1 combined Excel file ({excel_path.name})")
        print(f"  - 1 combined CSV file ({combined_csv_path.name})")
    
    return plates


def create_demo_data() -> pd.DataFrame:
    """Create simple demo data for immediate use in the app."""
    plates = generate_sample_dataset(n_plates=2, plate_prefix="DEMO")
    return pd.concat(plates.values(), ignore_index=True)


if __name__ == "__main__":
    # Generate sample data for demonstration
    output_path = Path("data") / "samples"
    sample_plates = generate_sample_dataset(
        n_plates=3, 
        plate_prefix="DEMO", 
        output_dir=output_path
    )
    
    # Print summary
    for plate_id, df in sample_plates.items():
        print(f"\n{plate_id}:")
        print(f"  - {len(df)} wells")
        print(f"  - Missing values: {df.isnull().sum().sum()}")
        
        # Calculate some basic ratios to show variety
        df['ratio_lptA'] = df['BG_lptA'] / df['BT_lptA']
        df['ratio_ldtD'] = df['BG_ldtD'] / df['BT_ldtD']
        
        print(f"  - lptA ratio range: {df['ratio_lptA'].min():.3f} - {df['ratio_lptA'].max():.3f}")
        print(f"  - ldtD ratio range: {df['ratio_ldtD'].min():.3f} - {df['ratio_ldtD'].max():.3f}")
        
        # Count potential hits (low ratios)
        low_ratio_wells = ((df['ratio_lptA'] < 0.3) | (df['ratio_ldtD'] < 0.3)).sum()
        print(f"  - Potential hits (ratio < 0.3): {low_ratio_wells}")