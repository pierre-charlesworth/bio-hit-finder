# Quick Start Guide - 5 Minutes to Results

Get up and running with Bio Hit Finder in just 5 minutes. This guide takes you from installation to your first analysis results.

## ⏱️ 5-Minute Setup

### Step 1: Install (1 minute)

**Option A: Use Git (recommended)**
```bash
git clone https://github.com/bio-hit-finder/bio-hit-finder.git
cd bio-hit-finder
pip install -r requirements.txt
```

**Option B: Direct Download**
1. Download ZIP from GitHub
2. Extract to your desired folder
3. Open terminal in extracted folder
4. Run: `pip install -r requirements.txt`

### Step 2: Launch (30 seconds)

```bash
streamlit run app.py
```

Your browser should automatically open to `http://localhost:8501`

### Step 3: Try the Demo (3 minutes)

1. **Click "🚀 Start Demo"** on the welcome page
2. **Select "Standard Workflow"** 
3. **Follow the guided tour** - it will walk you through:
   - Loading sample data
   - Understanding calculations
   - Identifying hits
   - Viewing results

### Step 4: Load Your Data (30 seconds)

1. **Go to "Data Upload" tab**
2. **Click "Browse files"** and select your CSV file
3. **Wait for processing** (usually 10-30 seconds)
4. **Review the data preview** to confirm it loaded correctly

## ✅ Quick Validation Checklist

Before diving into analysis, verify your setup:

- [ ] Application opens in browser without errors
- [ ] Demo mode works completely 
- [ ] Sample data loads and processes
- [ ] Plots and heatmaps display correctly
- [ ] No error messages in browser console (F12)

## 🎯 Essential Data Format

Your CSV file **must have** these columns (case-sensitive):

```csv
BG_lptA,BT_lptA,BG_ldtD,BT_ldtD,OD_WT,OD_tolC,OD_SA
1052.3,2134.5,876.2,1567.8,0.48,0.42,0.45
987.1,2087.3,823.7,1489.2,0.51,0.38,0.47
```

**Optional but helpful columns:**
- `PlateID` - Plate identifier
- `Well` - Well position (A01, B12, etc.)
- `Compound_ID` - Compound names/IDs

## 📊 Understanding Your First Results

After processing, look at these key tabs:

### Summary Tab
- **Total Wells**: Number of data points processed
- **Hit Rate**: Percentage of potential active compounds
- **Quality Metrics**: CV, missing data, dynamic range

### Hits Tab
- **Ranked List**: Compounds sorted by statistical significance  
- **Z-Score**: How many standard deviations from normal
- **Viability**: Whether cells remained healthy

### Visualizations Tab
- **Histograms**: Distribution of your measurements
- **Scatter Plots**: Relationship between different readouts
- **Quality Plots**: Data quality assessment

### Heatmaps Tab
- **Plate Layout**: Spatial view of your results
- **Color Coding**: Blue = low activity, Red = high activity
- **Pattern Detection**: Spots systematic issues

## 🔍 Quick Hit Identification

**Strong Hits** (High Priority):
- Z-score magnitude > 3.0
- Maintained cell viability
- Reproducible if you have replicates

**Moderate Hits** (Medium Priority):
- Z-score magnitude 2.0-3.0
- Good viability
- May need additional validation

**Questions to Ask:**
1. Do the hits make biological sense?
2. Are they concentrated in certain plate regions? (may indicate artifacts)
3. Do positive controls (if any) behave as expected?

## ⚠️ Common First-Time Issues

### "Required columns missing"
**Fix**: Check column names are exactly: `BG_lptA`, `BT_lptA`, `BG_ldtD`, `BT_ldtD`, `OD_WT`, `OD_tolC`, `OD_SA`

### "No hits found"
**Try**: Lower the Z-score threshold from 2.0 to 1.5 in the sidebar

### "Too many hits" (>20%)
**Try**: Raise the Z-score threshold to 2.5 or 3.0

### Application won't start
**Fix**: 
```bash
pip install --upgrade streamlit pandas plotly numpy
python --version  # Should be 3.11+
```

### Plots not showing
**Fix**: Try a different browser (Chrome recommended), clear cache (Ctrl+F5)

## 🚀 Next Steps After Your First Analysis

### Immediate Actions
1. **Export Results**: Download CSV with all calculated metrics
2. **Save Plots**: Download key visualizations for presentations
3. **Review Quality**: Check the QC Report tab for data issues

### For Better Results
1. **Read the [Data Format Guide](docs/user_guide/data_format.md)** for optimal data preparation
2. **Try Different Parameters**: Adjust Z-score thresholds based on your needs
3. **Learn Statistical Methods**: Understand when to use B-scores vs Z-scores

### For Advanced Usage
1. **Multi-Plate Analysis**: Combine data from multiple experiments
2. **Custom Exports**: Generate publication-ready reports
3. **API Usage**: Integrate into larger analysis pipelines

## 📚 Quick Reference

### Key Metrics Explained

| Metric | Good Range | Interpretation |
|--------|------------|----------------|
| **Ratio_lptA** | 0.4-0.7 | Lower values = potential hits |
| **Z_lptA** | -2 to +2 | \|Z\| > 2 = statistically significant |
| **OD_WT_norm** | 0.7-1.3 | Growth relative to plate median |
| **Viability_Gate** | TRUE | Cell health maintained |

### Default Thresholds

| Parameter | Default | When to Adjust |
|-----------|---------|----------------|
| **Z-score threshold** | 2.0 | Lower for more hits, higher for fewer |
| **Viability threshold** | 0.3 | Lower if compounds are cytotoxic |
| **Missing data limit** | 5% | Platform handles automatically |

### File Size Limits

| Data Size | Performance | Recommendation |
|-----------|-------------|----------------|
| < 1,000 wells | Instant | Perfect for testing |
| 1,000-10,000 wells | < 30 seconds | Standard analysis |
| 10,000+ wells | 1-2 minutes | Consider using subsets first |

## 🎓 5-Minute Tutorial Workflow

**Follow this exact sequence for your first analysis:**

1. **Launch**: `streamlit run app.py` ✓
2. **Demo**: Click "Start Demo" → "Standard Workflow" ✓
3. **Upload**: Try with `data/sample_plate_hits.csv` ✓
4. **Summary**: Check total wells processed and hit rate ✓
5. **Hits**: Look at the ranked hit list ✓
6. **Heatmap**: View spatial distribution of activity ✓
7. **Export**: Download the processed results CSV ✓

## 💡 Pro Tips

1. **Always start with demo data** to familiarize yourself with the interface
2. **Check the Summary tab first** to validate your data loaded correctly
3. **Use the QC Report** to identify any systematic issues
4. **Export early and often** - save your processed results
5. **Document your analysis parameters** for reproducibility

## 🆘 Get Help Fast

### Self-Service
- **Demo Mode**: Built-in guided tutorial
- **Sample Data**: Realistic examples to practice with
- **Error Messages**: Usually contain specific fix suggestions
- **Browser Console**: F12 key shows technical details

### Community Support  
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Comprehensive guides for all features
- **FAQ**: Common questions and answers

### Contact
- **Email**: support@bio-hit-finder.com
- **Documentation**: https://bio-hit-finder.readthedocs.io
- **GitHub**: https://github.com/bio-hit-finder/bio-hit-finder

---

## 🎉 Congratulations!

You're now ready to analyze your biological screening data with Bio Hit Finder. 

**What you've accomplished:**
- ✅ Installed and launched the platform
- ✅ Completed the demo walkthrough  
- ✅ Loaded and processed real data
- ✅ Identified potential hit compounds
- ✅ Visualized results spatially and statistically

**Ready for more?** Continue to the [full documentation](docs/user_guide/getting_started.md) for advanced features and detailed analysis workflows.

---

*Time to results: 5 minutes. Time to expertise: Keep exploring!* 🚀