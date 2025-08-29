"""Sample plate data generators for testing.

Provides various plate configurations with known characteristics for comprehensive testing:
- Normal plates with typical distributions
- Plates with edge effects  
- Plates with extreme outliers/hits
- Empty plates and missing data scenarios
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import json
from pathlib import Path


def create_normal_96_well_plate(seed: int = 42) -> pd.DataFrame:
    """Create normal 96-well plate with typical biological variation.
    
    Args:
        seed: Random seed for reproducible data
        
    Returns:
        DataFrame with 96 wells of normal biological data
    """
    np.random.seed(seed)
    
    # 96-well plate layout (8 rows x 12 columns)
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    cols = list(range(1, 13))
    
    data = []
    well_idx = 0
    
    for row in rows:
        for col in cols:
            well_data = {
                'Well': f"{row}{col:02d}",
                'Row': row,
                'Col': col,
                'PlateID': 'Normal_Plate_96',
                
                # BetaGlo measurements (reporter activity)
                'BG_lptA': np.random.normal(1000, 150, 1)[0],
                'BG_ldtD': np.random.normal(1200, 180, 1)[0],
                
                # BacTiter measurements (ATP/viability)
                'BT_lptA': np.random.normal(500, 75, 1)[0],
                'BT_ldtD': np.random.normal(600, 90, 1)[0],
                
                # Optical density measurements  
                'OD_WT': np.random.normal(1.5, 0.2, 1)[0],
                'OD_tolC': np.random.normal(1.2, 0.15, 1)[0],
                'OD_SA': np.random.normal(1.0, 0.12, 1)[0],
            }
            
            # Add some correlated noise between measurements
            correlation_factor = np.random.normal(1.0, 0.05)
            well_data['BG_lptA'] *= correlation_factor
            well_data['BT_lptA'] *= correlation_factor * 0.8
            
            # Ensure positive values
            for key in ['BG_lptA', 'BG_ldtD', 'BT_lptA', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']:
                well_data[key] = max(well_data[key], 10.0)
            
            data.append(well_data)
            well_idx += 1
    
    return pd.DataFrame(data)


def create_384_well_plate(seed: int = 43) -> pd.DataFrame:
    """Create normal 384-well plate data.
    
    Args:
        seed: Random seed for reproducible data
        
    Returns:
        DataFrame with 384 wells of normal biological data
    """
    np.random.seed(seed)
    
    # 384-well plate layout (16 rows x 24 columns) 
    rows = [chr(65 + i) for i in range(16)]  # A-P
    cols = list(range(1, 25))  # 1-24
    
    data = []
    
    for row in rows:
        for col in cols:
            well_data = {
                'Well': f"{row}{col:02d}",
                'Row': row, 
                'Col': col,
                'PlateID': 'Normal_Plate_384',
                
                # Scale measurements slightly for higher density
                'BG_lptA': np.random.normal(900, 120, 1)[0],
                'BG_ldtD': np.random.normal(1100, 140, 1)[0],
                'BT_lptA': np.random.normal(450, 60, 1)[0],
                'BT_ldtD': np.random.normal(550, 70, 1)[0],
                'OD_WT': np.random.normal(1.3, 0.18, 1)[0],
                'OD_tolC': np.random.normal(1.0, 0.12, 1)[0],
                'OD_SA': np.random.normal(0.9, 0.10, 1)[0],
            }
            
            # Ensure positive values
            for key in ['BG_lptA', 'BG_ldtD', 'BT_lptA', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']:
                well_data[key] = max(well_data[key], 5.0)
            
            data.append(well_data)
    
    return pd.DataFrame(data)


def create_plate_with_edge_effects(seed: int = 44) -> pd.DataFrame:
    """Create 96-well plate with pronounced edge effects.
    
    Args:
        seed: Random seed for reproducible data
        
    Returns:
        DataFrame with edge effects (evaporation, temperature gradients)
    """
    base_plate = create_normal_96_well_plate(seed)
    
    # Define edge positions
    edge_wells = set()
    
    # Add edge effects
    for idx, row in base_plate.iterrows():
        well_row = row['Row']
        well_col = row['Col']
        
        is_edge = (
            well_row in ['A', 'H'] or  # Top/bottom rows
            well_col in [1, 12]        # Left/right columns
        )
        
        if is_edge:
            edge_wells.add(row['Well'])
            
            # Edge effects: higher evaporation, temperature variations
            evaporation_factor = 1.3  # 30% higher concentration due to evaporation
            temp_variation = np.random.normal(1.0, 0.1)  # Temperature variation
            
            base_plate.loc[idx, 'BG_lptA'] *= evaporation_factor * temp_variation
            base_plate.loc[idx, 'BG_ldtD'] *= evaporation_factor * temp_variation
            base_plate.loc[idx, 'OD_WT'] *= evaporation_factor
            base_plate.loc[idx, 'OD_tolC'] *= evaporation_factor
            base_plate.loc[idx, 'OD_SA'] *= evaporation_factor
            
            # ATP might be affected differently
            base_plate.loc[idx, 'BT_lptA'] *= temp_variation * 0.9
            base_plate.loc[idx, 'BT_ldtD'] *= temp_variation * 0.9
    
    base_plate['PlateID'] = 'Edge_Effect_Plate'
    
    # Add metadata about edge wells
    base_plate['Is_Edge'] = base_plate['Well'].isin(edge_wells)
    
    return base_plate


def create_plate_with_hits(seed: int = 45, n_hits: int = 8) -> pd.DataFrame:
    """Create 96-well plate with known hits (extreme outliers).
    
    Args:
        seed: Random seed for reproducible data
        n_hits: Number of hit wells to include
        
    Returns:
        DataFrame with planted hits at known positions
    """
    base_plate = create_normal_96_well_plate(seed)
    
    # Select random positions for hits (avoid edges to make them cleaner)
    interior_indices = []
    for idx, row in base_plate.iterrows():
        if row['Row'] not in ['A', 'H'] and row['Col'] not in [1, 12]:
            interior_indices.append(idx)
    
    np.random.seed(seed + 10)  # Different seed for hit selection
    hit_indices = np.random.choice(interior_indices, size=n_hits, replace=False)
    
    hit_wells = set()
    
    for idx in hit_indices:
        hit_wells.add(base_plate.loc[idx, 'Well'])
        
        # Create strong hits - significantly higher reporter activity
        hit_strength = np.random.uniform(3.0, 5.0)  # 3-5x normal activity
        
        base_plate.loc[idx, 'BG_lptA'] *= hit_strength
        base_plate.loc[idx, 'BG_ldtD'] *= hit_strength
        
        # Viability might be affected
        viability_effect = np.random.uniform(0.7, 1.2)
        base_plate.loc[idx, 'BT_lptA'] *= viability_effect
        base_plate.loc[idx, 'BT_ldtD'] *= viability_effect
    
    base_plate['PlateID'] = 'Plate_With_Hits'
    base_plate['Is_Hit'] = base_plate.index.isin(hit_indices)
    base_plate['Hit_Wells'] = base_plate['Well'].isin(hit_wells)
    
    return base_plate


def create_plate_with_missing_data(seed: int = 46, missing_fraction: float = 0.1) -> pd.DataFrame:
    """Create 96-well plate with missing data points.
    
    Args:
        seed: Random seed for reproducible data
        missing_fraction: Fraction of wells with missing data
        
    Returns:
        DataFrame with randomly distributed missing values
    """
    base_plate = create_normal_96_well_plate(seed)
    
    np.random.seed(seed)
    n_wells = len(base_plate)
    n_missing = int(n_wells * missing_fraction)
    
    # Randomly select wells for missing data
    missing_indices = np.random.choice(n_wells, size=n_missing, replace=False)
    
    measurement_cols = ['BG_lptA', 'BG_ldtD', 'BT_lptA', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']
    
    for idx in missing_indices:
        # Randomly select which measurements to make missing
        cols_to_miss = np.random.choice(
            measurement_cols, 
            size=np.random.randint(1, len(measurement_cols) + 1),
            replace=False
        )
        
        for col in cols_to_miss:
            base_plate.loc[idx, col] = np.nan
    
    base_plate['PlateID'] = 'Plate_With_Missing'
    base_plate['Has_Missing'] = base_plate[measurement_cols].isna().any(axis=1)
    
    return base_plate


def create_empty_plate() -> pd.DataFrame:
    """Create empty plate template with well positions but no data.
    
    Returns:
        DataFrame with well positions but NaN measurements
    """
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    cols = list(range(1, 13))
    
    data = []
    for row in rows:
        for col in cols:
            data.append({
                'Well': f"{row}{col:02d}",
                'Row': row,
                'Col': col,
                'PlateID': 'Empty_Plate',
                'BG_lptA': np.nan,
                'BG_ldtD': np.nan,
                'BT_lptA': np.nan,
                'BT_ldtD': np.nan,
                'OD_WT': np.nan,
                'OD_tolC': np.nan,
                'OD_SA': np.nan,
            })
    
    return pd.DataFrame(data)


def create_constant_value_plate(value: float = 100.0) -> pd.DataFrame:
    """Create plate with constant values (for testing MAD=0 case).
    
    Args:
        value: Constant value for all measurements
        
    Returns:
        DataFrame with identical values in all wells
    """
    base_plate = create_normal_96_well_plate(42)
    
    measurement_cols = ['BG_lptA', 'BG_ldtD', 'BT_lptA', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']
    
    for col in measurement_cols:
        base_plate[col] = value
    
    base_plate['PlateID'] = 'Constant_Value_Plate'
    
    return base_plate


def create_multi_plate_dataset(n_plates: int = 3, seed: int = 47) -> List[pd.DataFrame]:
    """Create multiple plates for testing aggregation.
    
    Args:
        n_plates: Number of plates to create
        seed: Base random seed
        
    Returns:
        List of DataFrames representing different plates
    """
    plates = []
    
    for i in range(n_plates):
        plate_seed = seed + i * 10
        
        if i == 0:
            plate = create_normal_96_well_plate(plate_seed)
        elif i == 1:
            plate = create_plate_with_edge_effects(plate_seed)
        elif i == 2:
            plate = create_plate_with_hits(plate_seed)
        else:
            # Additional plates are normal with variation
            plate = create_normal_96_well_plate(plate_seed)
            # Add inter-plate variation
            variation_factor = 1.0 + (i - 3) * 0.1
            measurement_cols = ['BG_lptA', 'BG_ldtD', 'BT_lptA', 'BT_ldtD', 'OD_WT', 'OD_tolC', 'OD_SA']
            for col in measurement_cols:
                plate[col] *= variation_factor
        
        plate['PlateID'] = f'Plate_{i + 1:02d}'
        plates.append(plate)
    
    return plates


def create_reference_calculations() -> Dict[str, Any]:
    """Create reference calculations for golden tests.
    
    Returns:
        Dictionary with reference calculation results
    """
    # Use simple, hand-verifiable data
    simple_data = pd.DataFrame({
        'BG_lptA': [1000.0, 2000.0, 1500.0],
        'BT_lptA': [500.0, 1000.0, 750.0],
        'BG_ldtD': [1200.0, 2400.0, 1800.0],
        'BT_ldtD': [400.0, 800.0, 600.0],
        'OD_WT': [1.0, 2.0, 1.5],
        'OD_tolC': [0.8, 1.6, 1.2],
        'OD_SA': [1.2, 2.4, 1.8],
    })
    
    reference = {
        'input_data': simple_data,
        'expected_ratios': {
            'Ratio_lptA': [2.0, 2.0, 2.0],  # BG/BT = constant ratio
            'Ratio_ldtD': [3.0, 3.0, 3.0],  # BG/BT = constant ratio
        },
        'expected_od_norms': {
            'OD_WT_norm': [1.0/1.5, 2.0/1.5, 1.5/1.5],    # / median(1.5)
            'OD_tolC_norm': [0.8/1.2, 1.6/1.2, 1.2/1.2],  # / median(1.2)  
            'OD_SA_norm': [1.2/1.8, 2.4/1.8, 1.8/1.8],    # / median(1.8)
        },
        'statistics': {
            'ratio_lptA_median': 2.0,
            'ratio_lptA_mad': 0.0,  # All values identical
            'ratio_ldtD_median': 3.0,
            'ratio_ldtD_mad': 0.0,
        },
        'viability_thresholds': {
            'f_03': {
                'bt_lptA_threshold': 0.3 * 750.0,  # 225.0
                'bt_ldtD_threshold': 0.3 * 600.0,  # 180.0
                'expected_viable_lptA': [True, True, True],  # All above threshold
                'expected_viable_ldtD': [True, True, True],
            }
        }
    }
    
    return reference


def create_bscore_reference_data() -> Dict[str, Any]:
    """Create reference data for B-score testing.
    
    Returns:
        Dictionary with plate matrices and expected B-score results
    """
    # Create 8x12 matrix with known row/column effects
    np.random.seed(100)
    
    # Base random matrix
    base_matrix = np.random.normal(0, 1, (8, 12))
    
    # Add row effects (linear gradient)
    row_effects = np.arange(8).reshape(-1, 1) * 0.5
    
    # Add column effects (sinusoidal)
    col_effects = np.sin(np.arange(12) * np.pi / 6).reshape(1, -1) * 0.3
    
    # Combined matrix with bias
    biased_matrix = base_matrix + row_effects + col_effects
    
    return {
        'base_matrix': base_matrix,
        'row_effects': row_effects,
        'col_effects': col_effects,
        'biased_matrix': biased_matrix,
        'expected_properties': {
            'original_row_correlation': 'high',  # Should be high correlation with row index
            'bscore_row_correlation': 'low',     # Should be low after B-scoring
            'bscore_mean': 0.0,                  # Should be ~0
            'bscore_std': 1.0,                   # Should be ~1
        }
    }


def save_fixtures_to_files(output_dir: Optional[str] = None) -> Dict[str, str]:
    """Save all test fixtures to CSV files.
    
    Args:
        output_dir: Directory to save fixtures (defaults to fixtures/)
        
    Returns:
        Dictionary mapping fixture names to file paths
    """
    if output_dir is None:
        output_dir = Path(__file__).parent
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    fixtures = {
        'normal_96_well': create_normal_96_well_plate(),
        'normal_384_well': create_384_well_plate(),
        'edge_effects': create_plate_with_edge_effects(),
        'with_hits': create_plate_with_hits(),
        'with_missing': create_plate_with_missing_data(),
        'empty_plate': create_empty_plate(),
        'constant_values': create_constant_value_plate(),
    }
    
    file_paths = {}
    
    for name, data in fixtures.items():
        file_path = output_dir / f"{name}.csv"
        data.to_csv(file_path, index=False)
        file_paths[name] = str(file_path)
    
    # Save multi-plate dataset
    multi_plates = create_multi_plate_dataset()
    for i, plate in enumerate(multi_plates):
        file_path = output_dir / f"multi_plate_{i+1:02d}.csv"
        plate.to_csv(file_path, index=False)
        file_paths[f'multi_plate_{i+1:02d}'] = str(file_path)
    
    # Save reference calculations
    reference = create_reference_calculations()
    reference_path = output_dir / "reference_calculations.json"
    
    # Convert DataFrames to serializable format
    ref_serializable = {}
    for key, value in reference.items():
        if isinstance(value, pd.DataFrame):
            ref_serializable[key] = value.to_dict('records')
        else:
            ref_serializable[key] = value
    
    with open(reference_path, 'w') as f:
        json.dump(ref_serializable, f, indent=2)
    
    file_paths['reference_calculations'] = str(reference_path)
    
    # Save B-score reference
    bscore_ref = create_bscore_reference_data()
    bscore_path = output_dir / "bscore_reference.json"
    
    # Convert numpy arrays to lists for serialization
    bscore_serializable = {}
    for key, value in bscore_ref.items():
        if isinstance(value, np.ndarray):
            bscore_serializable[key] = value.tolist()
        else:
            bscore_serializable[key] = value
    
    with open(bscore_path, 'w') as f:
        json.dump(bscore_serializable, f, indent=2)
    
    file_paths['bscore_reference'] = str(bscore_path)
    
    return file_paths


if __name__ == "__main__":
    # Generate all fixtures when run directly
    fixture_dir = Path(__file__).parent
    file_paths = save_fixtures_to_files(str(fixture_dir))
    
    print("Generated test fixtures:")
    for name, path in file_paths.items():
        print(f"  {name}: {path}")
    
    print(f"\nTotal fixtures created: {len(file_paths)}")