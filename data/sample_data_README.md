# Sample Data for Bio Hit Finder Platform

This directory contains realistic biological plate data files designed to demonstrate all features and capabilities of the bio-hit-finder platform.

## Sample Data Files

### Individual Plate Examples

#### `sample_plate_normal.csv`
- **Description**: Typical biological variation without major artifacts
- **Format**: 96-well plate (8 rows × 12 columns)
- **Features**: Normal biological noise, DMSO controls in outer columns
- **Use Case**: Baseline functionality testing, standard workflow demonstration
- **Wells**: 96 total (A01-H12)
- **Controls**: DMSO negative controls in columns 1 and 12

#### `sample_plate_hits.csv`
- **Description**: Contains obvious strong and moderate hits
- **Format**: 96-well plate with embedded hit annotations
- **Features**: 
  - 5 strong hits (>70% inhibition): B03, C10, E07, F04, G05
  - 6 moderate hits (40-60% inhibition): D04, D07, E12, F12, G09
- **Use Case**: Hit identification, scoring algorithm validation
- **Hit Criteria**: Based on reduced BG/BT ratios for both lptA and ldtD
- **Quality**: High viability maintained (BT values normal)

#### `sample_plate_edge_effects.csv`
- **Description**: Demonstrates systematic edge effects and temperature gradients
- **Format**: 96-well plate with spatial annotation
- **Features**:
  - 15% signal reduction in edge wells (rows A,H and columns 1,12)
  - 25% signal reduction in corner wells (A01, A12, H01, H12)
  - Normal values in interior wells
- **Use Case**: Edge effect detection, spatial bias correction
- **Pattern**: Evaporation-like effects with gradual signal loss toward plate edges

#### `sample_plate_384well.csv`
- **Description**: 384-well format demonstration (first 50 wells shown)
- **Format**: 384-well plate (16 rows × 24 columns, sample shown)
- **Features**: Higher density screening format
- **Use Case**: High-throughput format validation, scalability testing
- **Note**: Full 384-well plates contain 384 wells (A01-P24)

### Multi-Plate Datasets

#### `multi_plate_dataset.csv`
- **Description**: Combined dataset from 5 plates for aggregation testing
- **Plates**: BATCH_A_001 through BATCH_A_005
- **Total Wells**: 480 (5 × 96-well plates)
- **Features**:
  - Varying hit rates across plates
  - Different edge effect patterns
  - Experimental metadata included
- **Use Case**: Cross-plate analysis, batch effect detection
- **Library**: Kinase Inhibitor Library v2

## Data Format Specification

### Required Columns

| Column | Type | Description | Units |
|--------|------|-------------|-------|
| `PlateID` | String | Unique plate identifier | - |
| `Well` | String | Well position (A01-H12 format) | - |
| `Row` | String | Row letter (A-H for 96-well) | - |
| `Col` | Integer | Column number (1-12 for 96-well) | - |
| `BG_lptA` | Float | BetaGlo signal for lptA reporter | RLU |
| `BT_lptA` | Float | BacTiter signal for lptA (ATP/viability) | RLU |
| `BG_ldtD` | Float | BetaGlo signal for ldtD reporter | RLU |
| `BT_ldtD` | Float | BacTiter signal for ldtD (ATP/viability) | RLU |
| `OD_WT` | Float | Optical density for wild-type strain | OD600 |
| `OD_tolC` | Float | Optical density for ΔtolC strain | OD600 |
| `OD_SA` | Float | Optical density for SA strain | OD600 |

### Optional Metadata Columns

| Column | Type | Description | Example Values |
|--------|------|-------------|---------------|
| `Treatment` | String | Treatment type | DMSO, Compound, Control |
| `Control_Type` | String | Control designation | Negative, Positive, Test |
| `Compound_ID` | String | Compound identifier | CMPD_0001, KIN_0234 |
| `Hit_Type` | String | Hit classification | Strong_Hit, Moderate_Hit |
| `Edge_Position` | String | Spatial annotation | Top_Edge, Interior, Corner |
| `Experiment_Date` | String | Date of experiment | 2024-01-15 |
| `Operator` | String | Person who ran experiment | Dr. Smith |
| `Library_Name` | String | Compound library used | Kinase_Inhibitor_Library_v2 |
| `Assay_Type` | String | Type of assay performed | Cell_Viability_Screen |

## Biological Context

### Reporter System
- **lptA**: Essential lipopolysaccharide transport gene
- **ldtD**: L,D-transpeptidase involved in peptidoglycan synthesis
- **BG/BT Ratio**: Reporter signal normalized by viability (ATP levels)

### Growth Measurements
- **WT**: Wild-type reference strain
- **ΔtolC**: Efflux-deficient strain (increased compound sensitivity)
- **SA**: Slow-growing strain control

### Expected Patterns

#### Normal Plates
- BG/BT ratios: 0.4-0.7 (typical range)
- OD values: 0.3-0.6 (healthy growth)
- Coefficient of variation: 15-25% (biological noise)

#### Hit Wells
- Strong hits: BG/BT ratio < 0.2 (>80% inhibition)
- Moderate hits: BG/BT ratio 0.2-0.4 (40-80% inhibition)
- Maintained viability: BT values within 2-fold of median

#### Edge Effects
- Signal reduction: 10-30% lower than interior wells
- Pattern: Gradient from edge to center
- Cause: Evaporation, temperature variation, handling artifacts

## Usage Examples

### Loading Sample Data in Python

```python
import pandas as pd

# Load individual plate
normal_plate = pd.read_csv('data/sample_plate_normal.csv')
hits_plate = pd.read_csv('data/sample_plate_hits.csv')
edge_plate = pd.read_csv('data/sample_plate_edge_effects.csv')

# Load multi-plate dataset
multi_plates = pd.read_csv('data/multi_plate_dataset.csv')

# Basic analysis
hits_plate['ratio_lptA'] = hits_plate['BG_lptA'] / hits_plate['BT_lptA']
hits_plate['ratio_ldtD'] = hits_plate['BG_ldtD'] / hits_plate['BT_ldtD']

# Identify potential hits
low_ratio_wells = hits_plate[
    (hits_plate['ratio_lptA'] < 0.3) | (hits_plate['ratio_ldtD'] < 0.3)
]
print(f"Potential hits: {len(low_ratio_wells)} wells")
```

### Streamlit App Usage

1. Start the application: `streamlit run app.py`
2. Navigate to "Data Upload" section
3. Select "Load Demo Data" for quick start
4. Or upload any of these CSV files directly
5. Explore different tabs to see various analyses

## Validation

All sample data has been validated to ensure:

- Realistic dynamic ranges matching experimental observations
- Appropriate noise levels and biological variation
- Correct hit patterns with expected statistical properties
- Proper edge effect magnitudes and spatial patterns
- Compatible data types and formatting

## Questions or Issues

If you encounter any issues with the sample data or need additional examples, please refer to the main documentation or create an issue in the repository.