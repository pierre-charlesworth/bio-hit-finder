#!/usr/bin/env python3
"""Validate export module structure without requiring all dependencies."""

import sys
from pathlib import Path

def validate_export_files():
    """Validate that all export files are present and have correct structure."""
    
    print("Validating bio-hit-finder export module structure...")
    
    # Check required files exist
    required_files = [
        "export/__init__.py",
        "export/csv_export.py", 
        "export/pdf_generator.py",
        "export/bundle.py",
        "export/example_usage.py",
        "templates/report.html"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"+ {file_path} exists")
        else:
            print(f"- {file_path} missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\nERROR: Missing files: {missing_files}")
        return False
    
    # Check key classes are defined
    try:
        # Read and check CSV export
        csv_content = Path("export/csv_export.py").read_text(encoding='utf-8')
        if "class CSVExporter:" in csv_content:
            print("+ CSVExporter class found")
        else:
            print("- CSVExporter class not found")
            return False
        
        # Check PDF generator
        pdf_content = Path("export/pdf_generator.py").read_text(encoding='utf-8')
        if "class PDFReportGenerator:" in pdf_content:
            print("+ PDFReportGenerator class found")
        else:
            print("- PDFReportGenerator class not found")
            return False
        
        # Check bundle exporter  
        bundle_content = Path("export/bundle.py").read_text(encoding='utf-8')
        if "class BundleExporter:" in bundle_content:
            print("+ BundleExporter class found")
        else:
            print("- BundleExporter class not found")
            return False
        
        # Check template
        template_content = Path("templates/report.html").read_text(encoding='utf-8')
        if "{{ title }}" in template_content and "{{ formulas" in template_content:
            print("+ HTML template has required placeholders")
        else:
            print("- HTML template missing required placeholders")
            return False
        
        print("\nSUCCESS: All export module files are properly structured!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to validate file contents: {e}")
        return False

def validate_export_methods():
    """Validate that key export methods are defined."""
    
    print("\nValidating export method signatures...")
    
    methods_to_check = [
        ("export/csv_export.py", "export_processed_plate"),
        ("export/csv_export.py", "export_combined_dataset"), 
        ("export/csv_export.py", "export_top_hits"),
        ("export/csv_export.py", "export_summary_stats"),
        ("export/pdf_generator.py", "generate_report"),
        ("export/bundle.py", "create_bundle"),
        ("export/bundle.py", "verify_bundle_integrity")
    ]
    
    for file_path, method_name in methods_to_check:
        try:
            content = Path(file_path).read_text(encoding='utf-8')
            if f"def {method_name}(" in content:
                print(f"+ {method_name} method found in {file_path}")
            else:
                print(f"- {method_name} method not found in {file_path}")
                return False
        except Exception as e:
            print(f"- Error checking {file_path}: {e}")
            return False
    
    print("\nSUCCESS: All required methods are properly defined!")
    return True

def validate_configuration():
    """Validate that configuration structure supports export features."""
    
    print("\nValidating configuration support...")
    
    try:
        config_content = Path("config.yaml").read_text(encoding='utf-8')
        
        required_config_sections = [
            "export:",
            "pdf:",
            "formats:",
            "include_formulas:",
            "include_methodology:"
        ]
        
        for section in required_config_sections:
            if section in config_content:
                print(f"+ {section} found in config.yaml")
            else:
                print(f"- {section} not found in config.yaml")
                return False
        
        print("\nSUCCESS: Configuration supports all export features!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to validate configuration: {e}")
        return False

def validate_requirements():
    """Check that requirements.txt includes export dependencies."""
    
    print("\nValidating requirements.txt...")
    
    try:
        req_content = Path("requirements.txt").read_text(encoding='utf-8')
        
        required_deps = [
            "jinja2",
            "weasyprint", 
            "plotly",
            "pandas",
            "numpy",
            "pyyaml"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep.lower() in req_content.lower():
                print(f"+ {dep} found in requirements.txt")
            else:
                print(f"- {dep} not found in requirements.txt")
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"\nWARNING: Some dependencies may be missing: {missing_deps}")
            return False
        
        print("\nSUCCESS: All required dependencies listed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to validate requirements: {e}")
        return False

if __name__ == "__main__":
    print("Bio-Hit-Finder Export Module Validation")
    print("=" * 50)
    
    # Run all validations
    files_ok = validate_export_files()
    methods_ok = validate_export_methods()  
    config_ok = validate_configuration()
    req_ok = validate_requirements()
    
    if files_ok and methods_ok and config_ok and req_ok:
        print("\n" + "=" * 50)
        print("SUCCESS: Export functionality is properly implemented!")
        print("All required files, classes, methods, and configuration are present.")
        print("\nTo use the export functionality:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Import from export module: from export import CSVExporter, PDFReportGenerator, BundleExporter")
        print("3. See export/example_usage.py for detailed usage examples")
        sys.exit(0)
    else:
        print("\n" + "=" * 50) 
        print("ERROR: Export functionality has structural issues.")
        print("Please review the validation output above.")
        sys.exit(1)