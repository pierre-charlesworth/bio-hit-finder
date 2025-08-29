"""Interactive demo mode for the bio-hit-finder platform.

This module provides guided walkthroughs and demonstrations of all platform features,
designed to help new users understand the workflow and capabilities.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import time
import logging
from typing import Dict, List, Optional, Tuple

# Import core modules
from core.plate_processor import PlateProcessor
from analytics.edge_effects import EdgeEffectDetector, WarningLevel
from analytics.bscore import BScoreProcessor
from visualizations.charts import create_histogram, create_scatter_plot
from visualizations.heatmaps import create_plate_heatmap
from sample_data_generator import create_demo_data

logger = logging.getLogger(__name__)

class DemoMode:
    """Interactive demo mode for guided platform exploration."""
    
    def __init__(self):
        self.demo_data_cache = {}
        self.current_step = 0
        self.max_steps = 6
        
    def initialize_session_state(self):
        """Initialize Streamlit session state for demo mode."""
        if 'demo_mode_active' not in st.session_state:
            st.session_state.demo_mode_active = False
        if 'demo_step' not in st.session_state:
            st.session_state.demo_step = 0
        if 'demo_data' not in st.session_state:
            st.session_state.demo_data = None
        if 'demo_results' not in st.session_state:
            st.session_state.demo_results = None
            
    def load_demo_data(self, demo_type: str) -> pd.DataFrame:
        """Load specific demo dataset."""
        data_files = {
            'normal': 'data/sample_plate_normal.csv',
            'hits': 'data/sample_plate_hits.csv',
            'edge_effects': 'data/sample_plate_edge_effects.csv',
            '384well': 'data/sample_plate_384well.csv',
            'multi_plate': 'data/multi_plate_dataset.csv'
        }
        
        try:
            if demo_type in data_files:
                file_path = Path(data_files[demo_type])
                if file_path.exists():
                    return pd.read_csv(file_path)
                else:
                    st.warning(f"Sample data file not found: {file_path}")
                    return create_demo_data()
            else:
                return create_demo_data()
        except Exception as e:
            st.error(f"Error loading demo data: {e}")
            return create_demo_data()
    
    def show_welcome(self):
        """Display welcome screen and demo options."""
        st.title("🧬 Bio Hit Finder - Interactive Demo")
        
        st.markdown("""
        Welcome to the Bio Hit Finder platform! This interactive demo will guide you through
        all the key features and capabilities of the system.
        
        ### What You'll Learn:
        1. **Data Upload & Validation** - How to load and validate plate data
        2. **Core Calculations** - Understanding Z-scores, B-scores, and ratios
        3. **Hit Identification** - Finding potential compounds of interest
        4. **Quality Control** - Detecting edge effects and plate artifacts
        5. **Visualization** - Creating publication-ready plots and heatmaps
        6. **Export & Reporting** - Generating comprehensive analysis reports
        
        ### Demo Scenarios Available:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 **Standard Workflow**", help="Typical plate analysis workflow"):
                st.session_state.demo_mode_active = True
                st.session_state.demo_scenario = 'standard'
                st.session_state.demo_step = 1
                st.rerun()
                
            if st.button("🔍 **Hit Discovery**", help="Focus on identifying strong hits"):
                st.session_state.demo_mode_active = True
                st.session_state.demo_scenario = 'hits'
                st.session_state.demo_step = 1
                st.rerun()
        
        with col2:
            if st.button("⚠️ **Quality Control**", help="Detecting and handling plate artifacts"):
                st.session_state.demo_mode_active = True
                st.session_state.demo_scenario = 'qc'
                st.session_state.demo_step = 1
                st.rerun()
                
            if st.button("📊 **High-Throughput**", help="Multi-plate analysis workflow"):
                st.session_state.demo_mode_active = True
                st.session_state.demo_scenario = 'htp'
                st.session_state.demo_step = 1
                st.rerun()
        
        st.markdown("---")
        st.markdown("*Each demo takes 5-10 minutes and includes interactive elements and explanations.*")
    
    def run_demo(self):
        """Main demo orchestration."""
        self.initialize_session_state()
        
        if not st.session_state.demo_mode_active:
            self.show_welcome()
            return
        
        # Demo navigation
        self.show_demo_navigation()
        
        # Route to appropriate demo step
        scenario = st.session_state.get('demo_scenario', 'standard')
        step = st.session_state.get('demo_step', 1)
        
        if scenario == 'standard':
            self.run_standard_workflow(step)
        elif scenario == 'hits':
            self.run_hit_discovery_demo(step)
        elif scenario == 'qc':
            self.run_quality_control_demo(step)
        elif scenario == 'htp':
            self.run_high_throughput_demo(step)
    
    def show_demo_navigation(self):
        """Show demo progress and navigation."""
        scenario = st.session_state.get('demo_scenario', 'standard')
        step = st.session_state.get('demo_step', 1)
        
        # Progress bar
        progress = step / self.max_steps
        st.progress(progress, text=f"Step {step} of {self.max_steps}")
        
        # Navigation controls
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("🏠 Start Over"):
                st.session_state.demo_mode_active = False
                st.session_state.demo_step = 0
                st.rerun()
        
        with col2:
            if step > 1 and st.button("⬅️ Previous"):
                st.session_state.demo_step = max(1, step - 1)
                st.rerun()
        
        with col3:
            if step < self.max_steps and st.button("Next ➡️"):
                st.session_state.demo_step = min(self.max_steps, step + 1)
                st.rerun()
        
        with col4:
            if st.button("🚪 Exit Demo"):
                st.session_state.demo_mode_active = False
                st.rerun()
        
        st.markdown("---")
    
    def run_standard_workflow(self, step: int):
        """Run the standard workflow demo."""
        if step == 1:
            self.demo_step_data_upload()
        elif step == 2:
            self.demo_step_calculations()
        elif step == 3:
            self.demo_step_statistics()
        elif step == 4:
            self.demo_step_visualizations()
        elif step == 5:
            self.demo_step_quality_control()
        elif step == 6:
            self.demo_step_export()
    
    def demo_step_data_upload(self):
        """Demo step 1: Data upload and validation."""
        st.header("📁 Step 1: Data Upload & Validation")
        
        st.markdown("""
        The first step in any analysis is loading and validating your plate data.
        The platform accepts CSV files with required measurement columns.
        """)
        
        # Load demo data
        with st.spinner("Loading sample plate data..."):
            demo_data = self.load_demo_data('normal')
            st.session_state.demo_data = demo_data
        
        st.success("✅ Sample data loaded successfully!")
        
        # Show data preview
        st.subheader("Data Preview")
        st.dataframe(demo_data.head(10), width='stretch')
        
        # Show data summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Wells", len(demo_data))
        with col2:
            st.metric("Plates", demo_data['PlateID'].nunique())
        with col3:
            st.metric("Missing Values", demo_data.isnull().sum().sum())
        
        # Explain data format
        st.subheader("📋 Required Data Format")
        st.markdown("""
        **Required Columns:**
        - `BG_lptA`, `BT_lptA` - Reporter and viability for lptA
        - `BG_ldtD`, `BT_ldtD` - Reporter and viability for ldtD  
        - `OD_WT`, `OD_tolC`, `OD_SA` - Growth measurements
        
        **Optional Columns:**
        - `PlateID`, `Well`, `Row`, `Col` - Position information
        - `Treatment`, `Compound_ID` - Experimental metadata
        """)
        
        if st.button("✨ Process Data"):
            with st.spinner("Processing plate data..."):
                processor = PlateProcessor()
                results = processor.process_dataframe(demo_data)
                st.session_state.demo_results = results
                st.success("Data processed successfully!")
                st.session_state.demo_step = 2
                st.rerun()
    
    def demo_step_calculations(self):
        """Demo step 2: Core calculations."""
        st.header("🧮 Step 2: Core Calculations")
        
        if st.session_state.demo_results is None:
            st.error("Please complete Step 1 first.")
            return
        
        results = st.session_state.demo_results
        
        st.markdown("""
        The platform performs several key calculations to transform raw measurements
        into meaningful biological metrics.
        """)
        
        # Show calculations with formulas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Reporter Ratios")
            st.markdown("""
            **Formula:** `Ratio = BG / BT`
            
            - Normalizes reporter signal by viability
            - Corrects for well-to-well growth differences
            - Lower ratios indicate potential hits
            """)
            
            # Show ratio distributions
            fig_hist = px.histogram(
                results, 
                x='Ratio_lptA', 
                title='lptA Reporter Ratio Distribution',
                nbins=30
            )
            st.plotly_chart(fig_hist, width='stretch')
        
        with col2:
            st.subheader("📈 Z-Score Normalization")
            st.markdown("""
            **Formula:** `Z = (value - median) / (1.4826 × MAD)`
            
            - Robust normalization using median and MAD
            - Accounts for plate-to-plate variation
            - Enables statistical hit calling
            """)
            
            # Show Z-score distributions
            fig_z = px.histogram(
                results, 
                x='Z_lptA', 
                title='lptA Z-Score Distribution',
                nbins=30
            )
            st.plotly_chart(fig_z, width='stretch')
        
        # Show calculation summary
        st.subheader("📋 Calculation Summary")
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            st.metric(
                "Median lptA Ratio", 
                f"{results['Ratio_lptA'].median():.3f}",
                help="Center of the distribution"
            )
        
        with metrics_col2:
            st.metric(
                "MAD lptA", 
                f"{results['Ratio_lptA'].mad():.3f}",
                help="Median Absolute Deviation (robust spread measure)"
            )
        
        with metrics_col3:
            st.metric(
                "Outliers (|Z| > 2)", 
                len(results[abs(results['Z_lptA']) > 2]),
                help="Wells with extreme Z-scores"
            )
        
        st.info("💡 **Next:** We'll use these calculations to identify potential hits!")
    
    def demo_step_statistics(self):
        """Demo step 3: Statistical analysis and hit identification."""
        st.header("🎯 Step 3: Hit Identification")
        
        if st.session_state.demo_results is None:
            st.error("Please complete previous steps first.")
            return
        
        results = st.session_state.demo_results
        
        st.markdown("""
        Statistical analysis helps identify compounds that significantly differ
        from the population baseline.
        """)
        
        # Hit calling parameters
        st.subheader("⚙️ Hit Calling Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            z_threshold = st.slider(
                "Z-Score Threshold", 
                min_value=1.0, 
                max_value=3.0, 
                value=2.0, 
                step=0.1,
                help="Wells with |Z-score| above this threshold are considered hits"
            )
        
        with col2:
            viability_threshold = st.slider(
                "Viability Threshold", 
                min_value=0.1, 
                max_value=1.0, 
                value=0.3, 
                step=0.05,
                help="Minimum relative viability for valid hits"
            )
        
        # Apply hit calling
        hits_lptA = (
            (abs(results['Z_lptA']) > z_threshold) & 
            (results['Viability_Gate_lptA'] == True)
        )
        
        hits_ldtD = (
            (abs(results['Z_ldtD']) > z_threshold) & 
            (results['Viability_Gate_ldtD'] == True)
        )
        
        # Show hit statistics
        st.subheader("📊 Hit Statistics")
        
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        
        with metrics_col1:
            st.metric("lptA Hits", hits_lptA.sum())
        
        with metrics_col2:
            st.metric("ldtD Hits", hits_ldtD.sum())
        
        with metrics_col3:
            st.metric("Dual Hits", (hits_lptA & hits_ldtD).sum())
        
        with metrics_col4:
            hit_rate = (hits_lptA | hits_ldtD).sum() / len(results) * 100
            st.metric("Hit Rate", f"{hit_rate:.1f}%")
        
        # Show hit visualization
        st.subheader("🎯 Hit Visualization")
        
        # Create scatter plot showing hits
        fig = px.scatter(
            results,
            x='Z_lptA',
            y='Z_ldtD',
            color=(hits_lptA | hits_ldtD).astype(str),
            color_discrete_map={'True': 'red', 'False': 'lightblue'},
            title='Hit Distribution (Z-Score Space)',
            labels={'color': 'Hit Status'}
        )
        
        # Add threshold lines
        fig.add_hline(y=z_threshold, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=-z_threshold, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_vline(x=z_threshold, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_vline(x=-z_threshold, line_dash="dash", line_color="red", opacity=0.5)
        
        st.plotly_chart(fig, width='stretch')
        
        # Show top hits table
        if (hits_lptA | hits_ldtD).any():
            st.subheader("🏆 Top Hits")
            
            hit_wells = results[hits_lptA | hits_ldtD].copy()
            hit_wells['Hit_Score'] = np.maximum(
                abs(hit_wells['Z_lptA']), 
                abs(hit_wells['Z_ldtD'])
            )
            
            top_hits = hit_wells.nlargest(10, 'Hit_Score')[
                ['Well', 'Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD', 'Hit_Score']
            ]
            
            st.dataframe(top_hits, width='stretch')
        
        st.info("💡 **Next:** We'll explore advanced visualizations and quality control!")
    
    def demo_step_visualizations(self):
        """Demo step 4: Advanced visualizations."""
        st.header("📊 Step 4: Advanced Visualizations")
        
        if st.session_state.demo_results is None:
            st.error("Please complete previous steps first.")
            return
        
        results = st.session_state.demo_results
        
        st.markdown("""
        Visualizations help identify patterns, validate results, and communicate findings.
        The platform provides multiple chart types optimized for plate-based data.
        """)
        
        # Visualization options
        viz_type = st.selectbox(
            "Select Visualization Type",
            ["Plate Heatmap", "Distribution Plots", "Correlation Analysis", "Time Series"],
            help="Choose different ways to visualize your data"
        )
        
        if viz_type == "Plate Heatmap":
            st.subheader("🔥 Plate Heatmap")
            
            # Metric selection
            metric = st.selectbox(
                "Select Metric", 
                ['Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD'],
                help="Choose which metric to display on the heatmap"
            )
            
            # Create heatmap
            try:
                fig_heatmap = create_plate_heatmap(results, metric)
                st.plotly_chart(fig_heatmap, width='stretch')
                
                st.markdown(f"""
                **Interpretation:**
                - **Blue areas**: Lower {metric} values (potential hits for ratios)
                - **Red areas**: Higher {metric} values 
                - **Spatial patterns**: May indicate edge effects or pipetting issues
                """)
            except Exception as e:
                st.error(f"Error creating heatmap: {e}")
        
        elif viz_type == "Distribution Plots":
            st.subheader("📈 Distribution Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Histogram
                fig_dist = px.histogram(
                    results, 
                    x='Ratio_lptA',
                    nbins=30,
                    title='lptA Ratio Distribution'
                )
                st.plotly_chart(fig_dist, width='stretch')
            
            with col2:
                # Box plot by row
                fig_box = px.box(
                    results, 
                    x='Row', 
                    y='Ratio_lptA',
                    title='lptA Ratio by Plate Row'
                )
                st.plotly_chart(fig_box, width='stretch')
        
        elif viz_type == "Correlation Analysis":
            st.subheader("🔗 Correlation Analysis")
            
            # Calculate correlation matrix
            corr_cols = ['Ratio_lptA', 'Ratio_ldtD', 'Z_lptA', 'Z_ldtD', 'OD_WT', 'OD_tolC']
            corr_matrix = results[corr_cols].corr()
            
            # Create correlation heatmap
            fig_corr = px.imshow(
                corr_matrix,
                aspect='auto',
                title='Measurement Correlation Matrix',
                color_continuous_scale='RdBu_r'
            )
            st.plotly_chart(fig_corr, width='stretch')
            
            st.markdown("""
            **Key Relationships:**
            - Strong correlations (|r| > 0.7) may indicate measurement redundancy
            - Negative correlations between ratios and OD could indicate growth inhibition
            - Z-scores should correlate with their corresponding ratios
            """)
        
        # Interactive controls
        st.subheader("🎛️ Interactive Controls")
        st.markdown("""
        **Try this:** Adjust the parameters above to see how visualizations change in real-time.
        This interactivity helps you explore your data and understand relationships.
        """)
        
        if st.button("🎨 Generate All Visualizations"):
            with st.spinner("Creating comprehensive visualization report..."):
                st.success("✅ Visualization report generated! (In a full implementation, this would create a PDF report)")
    
    def demo_step_quality_control(self):
        """Demo step 5: Quality control and diagnostics."""
        st.header("🔍 Step 5: Quality Control & Diagnostics")
        
        st.markdown("""
        Quality control is crucial for reliable results. The platform automatically
        detects common plate artifacts and provides diagnostic information.
        """)
        
        # Load edge effects demo data
        if st.button("Load Plate with Edge Effects"):
            edge_data = self.load_demo_data('edge_effects')
            with st.spinner("Processing edge effects data..."):
                processor = PlateProcessor()
                edge_results = processor.process_dataframe(edge_data)
                st.session_state.demo_edge_results = edge_results
        
        # Edge effect detection
        st.subheader("🌊 Edge Effect Detection")
        
        if 'demo_edge_results' in st.session_state:
            edge_results = st.session_state.demo_edge_results
            
            # Run edge effect detection
            try:
                detector = EdgeEffectDetector()
                edge_analysis = detector.analyze_edge_effects(edge_results)
                
                # Show results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Edge Effect Score", f"{edge_analysis['edge_score']:.2f}")
                    st.metric("Warning Level", edge_analysis['warning_level'].value)
                
                with col2:
                    st.metric("Affected Wells", len(edge_analysis['edge_wells']))
                    st.metric("Max Effect Size", f"{edge_analysis['max_effect_size']:.1%}")
                
                # Show edge effect heatmap
                fig_edge = create_plate_heatmap(edge_results, 'Ratio_lptA')
                st.plotly_chart(fig_edge, width='stretch')
                
                st.warning("⚠️ Edge effects detected! Consider B-score correction or exclude edge wells.")
                
            except Exception as e:
                st.error(f"Error in edge effect analysis: {e}")
        else:
            st.info("Click 'Load Plate with Edge Effects' to see edge effect detection in action.")
        
        # B-score correction demo
        st.subheader("📊 B-Score Correction")
        st.markdown("""
        B-scores correct for systematic row and column effects using median polish.
        This can improve hit detection in the presence of spatial artifacts.
        """)
        
        if st.button("Apply B-Score Correction") and 'demo_edge_results' in st.session_state:
            with st.spinner("Applying B-score correction..."):
                try:
                    bscore_processor = BScoreProcessor()
                    corrected_data = bscore_processor.calculate_bscores(
                        st.session_state.demo_edge_results
                    )
                    
                    # Compare before/after
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Before B-Score")
                        fig_before = create_plate_heatmap(
                            st.session_state.demo_edge_results, 
                            'Z_lptA'
                        )
                        st.plotly_chart(fig_before, width='stretch')
                    
                    with col2:
                        st.subheader("After B-Score")
                        fig_after = create_plate_heatmap(
                            corrected_data, 
                            'B_lptA'
                        )
                        st.plotly_chart(fig_after, width='stretch')
                    
                    st.success("✅ B-score correction applied! Note how spatial artifacts are reduced.")
                    
                except Exception as e:
                    st.error(f"Error in B-score calculation: {e}")
        
        # Quality metrics summary
        st.subheader("📋 Quality Metrics Summary")
        
        if st.session_state.demo_results is not None:
            results = st.session_state.demo_results
            
            # Calculate quality metrics
            cv_ratio = results['Ratio_lptA'].std() / results['Ratio_lptA'].mean()
            missing_rate = results.isnull().sum().sum() / (len(results) * len(results.columns))
            z_range = results['Z_lptA'].max() - results['Z_lptA'].min()
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric("CV (Coefficient of Variation)", f"{cv_ratio:.1%}")
                if cv_ratio < 0.15:
                    st.success("✅ Low variability")
                elif cv_ratio < 0.30:
                    st.warning("⚠️ Moderate variability")
                else:
                    st.error("❌ High variability")
            
            with metrics_col2:
                st.metric("Missing Data Rate", f"{missing_rate:.1%}")
                if missing_rate < 0.05:
                    st.success("✅ Low missing data")
                else:
                    st.warning("⚠️ Check data quality")
            
            with metrics_col3:
                st.metric("Z-Score Range", f"{z_range:.1f}")
                if z_range > 6:
                    st.success("✅ Good dynamic range")
                else:
                    st.info("ℹ️ Limited dynamic range")
        
        st.info("💡 **Next:** We'll generate comprehensive reports and export results!")
    
    def demo_step_export(self):
        """Demo step 6: Export and reporting."""
        st.header("📤 Step 6: Export & Reporting")
        
        st.markdown("""
        The final step is generating comprehensive reports and exporting results
        for further analysis or publication.
        """)
        
        # Export options
        st.subheader("📊 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Data Exports**")
            if st.button("Export Processed Data (CSV)"):
                st.success("✅ CSV file would be generated with all calculated metrics")
            
            if st.button("Export Hit List (Excel)"):
                st.success("✅ Excel file would be generated with ranked hit list")
            
            if st.button("Export Full Results Bundle (ZIP)"):
                st.success("✅ ZIP bundle would include data, plots, and QC reports")
        
        with col2:
            st.markdown("**📋 Reports**")
            if st.button("Generate QC Report (PDF)"):
                st.success("✅ Quality control report would be generated")
            
            if st.button("Generate Analysis Report (PDF)"):
                st.success("✅ Comprehensive analysis report would be generated")
            
            if st.button("Generate Publication Figures"):
                st.success("✅ High-resolution figures would be exported")
        
        # Report preview
        st.subheader("📋 Sample Report Preview")
        
        if st.session_state.demo_results is not None:
            results = st.session_state.demo_results
            
            # Generate sample report content
            st.markdown("### Analysis Summary")
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("Total Wells Analyzed", len(results))
                st.metric("Plates Processed", results.get('PlateID', ['DEMO']).nunique() if 'PlateID' in results.columns else 1)
            
            with summary_col2:
                potential_hits = len(results[abs(results.get('Z_lptA', 0)) > 2])
                st.metric("Potential Hits", potential_hits)
                hit_rate = potential_hits / len(results) * 100 if len(results) > 0 else 0
                st.metric("Hit Rate", f"{hit_rate:.1f}%")
            
            with summary_col3:
                st.metric("QC Status", "✅ PASS")
                st.metric("Edge Effects", "⚠️ MINOR")
            
            # Sample visualization for report
            st.markdown("### Key Findings")
            st.markdown("""
            - **Data Quality**: Good overall quality with low CV and minimal missing data
            - **Hit Detection**: Several compounds showing significant activity
            - **Spatial Effects**: Minor edge effects detected, B-score correction recommended
            - **Reproducibility**: Results consistent with expected biological patterns
            """)
            
            # Methods section preview
            st.markdown("### Methods Summary")
            st.markdown("""
            **Data Processing**: Raw luminescence values were normalized using robust Z-scores 
            calculated from median and median absolute deviation (MAD).
            
            **Hit Calling**: Compounds with |Z-score| > 2.0 and maintained viability 
            (BT > 30% of median) were classified as potential hits.
            
            **Quality Control**: Spatial artifacts were assessed using edge effect detection 
            algorithms. B-score correction was applied where appropriate.
            """)
        
        # Demo completion
        st.markdown("---")
        st.success("🎉 **Congratulations!** You've completed the Bio Hit Finder demo!")
        
        st.markdown("""
        ### What's Next?
        
        1. **Upload your own data** - Use the main application with your experimental data
        2. **Explore advanced features** - Try B-score correction, multi-plate analysis
        3. **Customize parameters** - Adjust thresholds and settings for your assay
        4. **Generate reports** - Create publication-ready outputs
        
        ### Get Help
        
        - 📚 Check the user documentation for detailed guides
        - 🐛 Report issues on the GitHub repository
        - 💬 Join the community discussion forum
        """)
        
        if st.button("🚀 Start Using Bio Hit Finder"):
            st.session_state.demo_mode_active = False
            st.success("Redirecting to main application...")
            st.rerun()
    
    def run_hit_discovery_demo(self, step: int):
        """Run the hit discovery focused demo."""
        # Implementation would be similar but focused on hit-finding workflow
        st.header(f"🔍 Hit Discovery Demo - Step {step}")
        st.info("Hit discovery demo implementation would go here...")
        
    def run_quality_control_demo(self, step: int):
        """Run the quality control focused demo."""
        # Implementation would be similar but focused on QC workflow  
        st.header(f"⚠️ Quality Control Demo - Step {step}")
        st.info("Quality control demo implementation would go here...")
        
    def run_high_throughput_demo(self, step: int):
        """Run the high-throughput analysis demo."""
        # Implementation would be similar but focused on multi-plate workflow
        st.header(f"📊 High-Throughput Demo - Step {step}")
        st.info("High-throughput demo implementation would go here...")


def show_demo_mode():
    """Main entry point for demo mode in Streamlit app."""
    demo = DemoMode()
    demo.run_demo()


if __name__ == "__main__":
    # For testing the demo mode standalone
    import streamlit as st
    show_demo_mode()