# Troubleshooting Guide

This guide helps you diagnose and resolve common issues encountered when using Bio Hit Finder. Issues are organized by category with step-by-step solutions.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Data Upload Problems](#data-upload-problems)
3. [Analysis Errors](#analysis-errors)
4. [Performance Issues](#performance-issues)
5. [Visualization Problems](#visualization-problems)
6. [Export/Report Issues](#exportreport-issues)
7. [Biological Interpretation Concerns](#biological-interpretation-concerns)

## Installation Issues

### Problem: Python Version Error

**Symptoms**:
```
ERROR: This package requires Python 3.11 or higher
Your version: Python 3.9.x
```

**Solution**:
1. **Check Python version**:
   ```bash
   python --version
   # or
   python3 --version
   ```

2. **Install Python 3.11+**:
   - **Windows**: Download from [python.org](https://python.org)
   - **macOS**: Use Homebrew `brew install python@3.11`  
   - **Linux**: `sudo apt install python3.11` or similar

3. **Use virtual environment**:
   ```bash
   python3.11 -m venv bio-hit-finder
   source bio-hit-finder/bin/activate  # Linux/Mac
   # or
   bio-hit-finder\Scripts\activate     # Windows
   ```

### Problem: Package Installation Fails

**Symptoms**:
```
ERROR: Could not install packages due to an EnvironmentError
Permission denied: '/usr/local/lib/python3.11/site-packages/'
```

**Solutions**:

#### Option 1: Use --user flag
```bash
pip install --user -r requirements.txt
```

#### Option 2: Use virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

#### Option 3: Fix permissions (Linux/Mac)
```bash
sudo chown -R $(whoami) /usr/local/lib/python3.11/site-packages/
```

### Problem: Streamlit Won't Start

**Symptoms**:
```
streamlit: command not found
```

**Solutions**:

1. **Verify installation**:
   ```bash
   pip list | grep streamlit
   ```

2. **Reinstall streamlit**:
   ```bash
   pip install --upgrade streamlit
   ```

3. **Use full path**:
   ```bash
   python -m streamlit run app.py
   ```

4. **Check PATH**:
   ```bash
   echo $PATH  # Should include Python scripts directory
   ```

### Problem: Browser Doesn't Open

**Symptoms**: Streamlit starts but browser doesn't open automatically

**Solutions**:

1. **Manual browser access**:
   - Open browser manually
   - Navigate to `http://localhost:8501`

2. **Check firewall**:
   - Ensure port 8501 is not blocked
   - Try different port: `streamlit run app.py --server.port 8502`

3. **Network configuration**:
   ```bash
   streamlit run app.py --server.address 127.0.0.1
   ```

## Data Upload Problems

### Problem: "File Format Not Supported"

**Symptoms**: Error when trying to upload non-CSV files

**Solutions**:

1. **Convert to CSV**:
   - **Excel**: Save As → CSV (Comma delimited)
   - **Google Sheets**: File → Download → CSV
   - **R/Python**: Use appropriate export functions

2. **Check file extension**:
   ```bash
   # File must have .csv extension
   mv mydata.txt mydata.csv
   ```

3. **Verify CSV format**:
   ```bash
   head -5 mydata.csv  # Should show comma-separated values
   ```

### Problem: "Required Columns Missing"

**Symptoms**:
```
ERROR: Required column 'BG_lptA' not found in data
Available columns: ['BG_LPTA', 'BT_LPTA', ...]
```

**Solutions**:

1. **Check column names exactly**:
   - Case sensitive: `BG_lptA` not `bg_lpta` or `BG_LPTA`
   - Underscores: `BG_lptA` not `BG-lptA` or `BG lptA`

2. **Common naming fixes**:
   ```python
   # In Excel or text editor, rename columns to:
   BG_lptA, BT_lptA, BG_ldtD, BT_ldtD, OD_WT, OD_tolC, OD_SA
   ```

3. **Use column mapping**:
   - If available in interface, map your column names to required names

### Problem: "Invalid Numeric Values"

**Symptoms**: 
```
WARNING: Non-numeric values detected in BG_lptA column
Values: ['Not_Detected', 'Error', '<50']
```

**Solutions**:

1. **Replace text with numbers**:
   ```csv
   # Wrong:
   BG_lptA
   "Not_Detected"
   "Error"
   "<50"
   
   # Right:
   BG_lptA
   
   
   50
   ```

2. **Handle missing values**:
   - Leave cell empty (not "NA" or "NULL")
   - Or use actual numeric values where possible

3. **Remove quotes around numbers**:
   ```csv
   # Wrong: "123.4"
   # Right: 123.4
   ```

### Problem: "Too Many Missing Values"

**Symptoms**:
```
WARNING: High missing data rate (15.3%) in BG_ldtD column
Consider data quality review
```

**Solutions**:

1. **Acceptable missing data**: < 5% per column
2. **Check data export**: Ensure all measurements exported correctly
3. **Instrument issues**: Review raw data collection
4. **Consider exclusion**: Remove wells/plates with systematic failures

### Problem: Large File Upload Timeout

**Symptoms**: Upload progress bar stalls or times out

**Solutions**:

1. **Reduce file size**:
   ```python
   # Split large datasets
   df = pd.read_csv('large_file.csv')
   df.iloc[:1000].to_csv('subset_1.csv', index=False)
   ```

2. **Increase timeout** (if running locally):
   ```bash
   streamlit run app.py --server.maxUploadSize 1000
   ```

3. **Use data subsets**: Start with smaller datasets for testing

## Analysis Errors

### Problem: "Calculation Failed"

**Symptoms**:
```
ERROR: Unable to calculate Z-scores
Division by zero in MAD calculation
```

**Causes and Solutions**:

#### Cause: All values identical
```python
# Check for constant values
df['BG_lptA'].nunique()  # Should be > 1
```
**Solution**: Verify assay worked correctly, check instrument calibration

#### Cause: Insufficient valid data
```python
# Check valid data count
df['BG_lptA'].notna().sum()  # Should be > 10
```
**Solution**: Include more wells or reduce missing data rate

### Problem: "Memory Error" 

**Symptoms**:
```
MemoryError: Unable to allocate array with shape (10000, 10000)
```

**Solutions**:

1. **Process in chunks**:
   - Analyze plates separately
   - Use data subsets for initial exploration

2. **Increase system memory**:
   - Close other applications
   - Use cloud deployment for large datasets

3. **Enable low-memory mode** (if available):
   ```python
   processor = PlateProcessor(low_memory=True)
   ```

### Problem: "Edge Effect Detection Failed"

**Symptoms**: Edge effect analysis doesn't complete

**Solutions**:

1. **Check plate layout**: Ensure Row/Col columns present
2. **Verify well positions**: Should follow standard format (A01, B12, etc.)
3. **Minimum plate size**: Need at least 96 wells for edge detection

### Problem: B-Score Calculation Issues

**Symptoms**: B-score correction produces unexpected results

**Solutions**:

1. **Check plate format**: B-scores require rectangular plate layout
2. **Sufficient data**: Need >80% wells with valid measurements  
3. **Review parameters**:
   ```python
   # Adjust iteration limits if needed
   bscore_processor = BScoreProcessor(max_iter=100, tolerance=1e-6)
   ```

## Performance Issues

### Problem: Slow Processing

**Symptoms**: Analysis takes >5 minutes for single plate

**Diagnostic Steps**:

1. **Check data size**:
   ```python
   print(f"Data shape: {df.shape}")
   print(f"Memory usage: {df.memory_usage().sum()} bytes")
   ```

2. **Monitor system resources**:
   - CPU usage should be <100%
   - Available RAM should be >2GB

**Solutions**:

1. **Use faster backend**:
   ```python
   # If available
   processor = PlateProcessor(backend='polars')
   ```

2. **Enable parallel processing**:
   ```python
   processor = PlateProcessor(n_jobs=-1)  # Use all cores
   ```

3. **Optimize data types**:
   ```python
   # Reduce memory usage
   df = df.astype({'BG_lptA': 'float32', 'BT_lptA': 'float32'})
   ```

### Problem: Application Becomes Unresponsive

**Symptoms**: Streamlit interface freezes during analysis

**Solutions**:

1. **Refresh browser page**: Press F5 or Ctrl+R

2. **Restart application**:
   ```bash
   # Press Ctrl+C in terminal, then restart
   streamlit run app.py
   ```

3. **Check browser memory**: Close other tabs, restart browser

4. **Use production deployment**: For heavy workloads

## Visualization Problems

### Problem: Plots Not Displaying

**Symptoms**: Empty plot areas or error messages

**Solutions**:

1. **Check data availability**: Ensure analysis completed successfully

2. **Browser compatibility**: Use modern browser (Chrome, Firefox, Safari)

3. **Clear browser cache**: Refresh with Ctrl+Shift+R

4. **JavaScript errors**: Check browser console (F12) for errors

### Problem: Heat Maps Show Wrong Values

**Symptoms**: Heat map colors don't match expected patterns

**Solutions**:

1. **Check metric selection**: Verify correct column selected for visualization

2. **Color scale issues**:
   - Try different color scales
   - Manually set min/max ranges

3. **Data processing**: Ensure analysis completed without errors

### Problem: Plot Export Fails

**Symptoms**: Cannot download or save plots

**Solutions**:

1. **Browser permissions**: Allow downloads from localhost

2. **Right-click save**: Use browser's "Save image as" option

3. **Use export functionality**: Try different export formats (PNG, SVG, PDF)

## Export/Report Issues

### Problem: PDF Generation Fails

**Symptoms**:
```
ERROR: Failed to generate PDF report
WeasyPrint installation issue
```

**Solutions**:

1. **Install system dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt install libffi-dev libssl-dev
   
   # macOS
   brew install libffi openssl
   
   # Windows: Use pre-built wheels
   pip install --upgrade weasyprint
   ```

2. **Alternative export**: Use HTML export instead of PDF

### Problem: CSV Export Contains Errors

**Symptoms**: Exported CSV has formatting issues

**Solutions**:

1. **Check file encoding**: Use UTF-8 encoding
2. **Verify decimal places**: Ensure appropriate precision
3. **Column order**: Check that all expected columns present

### Problem: ZIP Bundle Creation Fails

**Symptoms**: Export bundle doesn't include all files

**Solutions**:

1. **Check disk space**: Ensure sufficient storage available
2. **File permissions**: Verify write permissions in output directory
3. **Try individual exports**: Export components separately

## Biological Interpretation Concerns

### Problem: No Hits Found

**Symptoms**: Analysis completes but identifies zero hits

**Diagnostic Steps**:

1. **Check thresholds**:
   ```python
   print(f"Z-score threshold: {z_threshold}")
   print(f"Max |Z-score| in data: {abs(df['Z_lptA']).max()}")
   ```

2. **Review data quality**:
   ```python
   print(f"CV of ratios: {df['Ratio_lptA'].std() / df['Ratio_lptA'].mean()}")
   ```

3. **Check positive controls**: If available, verify known actives are detected

**Solutions**:

1. **Lower thresholds**: Try Z-score cutoff of 1.5-2.0
2. **Review library**: May contain inactive compounds
3. **Check assay optimization**: Verify assay is working correctly

### Problem: Too Many Hits

**Symptoms**: >20% of compounds flagged as hits

**Possible Causes**:
- Thresholds too permissive
- Assay artifacts (edge effects)
- Cytotoxic compound library
- Data quality issues

**Solutions**:

1. **Raise thresholds**: Increase Z-score cutoff to 2.5-3.0
2. **Apply B-score correction**: Address spatial artifacts  
3. **Strengthen viability gating**: Increase viability threshold
4. **Review assay conditions**: May need optimization

### Problem: Hits Only at Plate Edges

**Symptoms**: Activity concentrated in edge wells

**Diagnosis**: Almost certainly edge effects (evaporation, temperature)

**Solutions**:

1. **Apply B-score correction**: Automatically corrects spatial effects
2. **Exclude edge wells**: Remove rows A,H and columns 1,12 from analysis
3. **Improve experimental conditions**: Better incubator, plate sealing

### Problem: Inconsistent Results Across Plates

**Symptoms**: Same compounds show different activity across plates

**Possible Causes**:
- Batch effects (different days/operators)
- Reagent variability  
- Instrument drift
- Environmental conditions

**Solutions**:

1. **Plate-wise normalization**: Calculate Z-scores within each plate
2. **Include more controls**: More reference wells per plate
3. **Batch correction methods**: Use statistical correction if available
4. **Protocol standardization**: Improve experimental consistency

## Getting Additional Help

### Self-Help Resources

1. **Documentation**: Check user guides for detailed procedures
2. **Sample data**: Practice with provided example datasets
3. **Error logs**: Check console/terminal for detailed error messages
4. **FAQ section**: Look for common questions and answers

### Community Support

1. **GitHub Issues**: 
   - Search existing issues: `https://github.com/bio-hit-finder/issues`
   - Create new issue with:
     - Clear problem description
     - Steps to reproduce
     - Error messages
     - System information

2. **Discussion Forums**:
   - User community discussions
   - Share experiences and solutions
   - Ask for advice on experimental design

3. **Professional Support**:
   - Email support for technical issues
   - Training workshops and webinars
   - Custom development and consulting

### When Reporting Issues

**Include This Information**:

1. **System details**:
   ```bash
   python --version
   pip list | grep -E "(streamlit|pandas|numpy|plotly)"
   # Operating system and version
   ```

2. **Data characteristics**:
   - Number of plates/wells
   - File size
   - Data format details

3. **Error reproduction**:
   - Exact steps taken
   - Complete error messages
   - Screenshots if helpful

4. **Expected vs. actual behavior**:
   - What you expected to happen
   - What actually happened
   - Any workarounds you've tried

**Sample Issue Report**:
```
Title: B-score calculation fails with "singular matrix" error

System: Windows 10, Python 3.11.2, Bio Hit Finder v2.1.0

Problem: When trying to apply B-score correction to a 96-well plate 
with 15% missing data, I get "numpy.linalg.LinAlgError: Singular matrix"

Steps to reproduce:
1. Load attached CSV file (plate_with_missing.csv)  
2. Navigate to QC Report tab
3. Click "Apply B-Score Correction"
4. Error appears immediately

Expected: B-scores calculated successfully
Actual: Error message and calculation fails

Data: 96-well plate, 14 wells with missing BG_lptA values (15% missing)
Error message: [paste complete error traceback]

Workaround attempted: Tried reducing missing data threshold, same error
```

---

**Still having issues? Don't hesitate to reach out to the community or create a GitHub issue. We're here to help!**