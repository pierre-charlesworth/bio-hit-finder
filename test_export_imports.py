#!/usr/bin/env python3
"""Test script to verify export module imports work correctly."""

import sys
from pathlib import Path

def test_export_imports():
    """Test that all export modules can be imported successfully."""
    
    print("Testing bio-hit-finder export module imports...")
    
    try:
        # Test core export imports
        from export import (
            CSVExporter,
            PDFReportGenerator,
            BundleExporter,
            create_export_metadata,
            generate_quick_summary,
            create_analysis_bundle
        )
        print("+ Core export modules imported successfully")
        
        # Test individual module imports
        from export.csv_export import CSVExporter as CSVExp
        print("+ CSV export module imported")
        
        from export.pdf_generator import PDFReportGenerator as PDFGen  
        print("+ PDF generator module imported")
        
        from export.bundle import BundleExporter as BundleExp
        print("+ Bundle export module imported")
        
        # Test that classes can be instantiated
        csv_exp = CSVExporter()
        print("+ CSVExporter instantiated")
        
        pdf_gen = PDFReportGenerator()
        print("+ PDFReportGenerator instantiated")
        
        bundle_exp = BundleExporter()
        print("+ BundleExporter instantiated")
        
        print("\nSUCCESS: All export functionality imports passed!")
        return True
        
    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    
    print("\nTesting required dependencies...")
    
    required_deps = [
        'pandas',
        'numpy', 
        'plotly',
        'jinja2',
        'weasyprint',
        'yaml'
    ]
    
    missing_deps = []
    
    for dep in required_deps:
        try:
            if dep == 'yaml':
                import yaml
            else:
                __import__(dep)
            print(f"+ {dep} available")
        except ImportError:
            print(f"- {dep} missing")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\nERROR: Missing dependencies: {missing_deps}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False
    else:
        print("\nSUCCESS: All required dependencies available!")
        return True

if __name__ == "__main__":
    deps_ok = test_dependencies()
    imports_ok = test_export_imports()
    
    if deps_ok and imports_ok:
        print("\nSUCCESS: Export functionality is ready to use!")
        sys.exit(0)
    else:
        print("\nERROR: Export functionality has issues that need to be resolved.")
        sys.exit(1)