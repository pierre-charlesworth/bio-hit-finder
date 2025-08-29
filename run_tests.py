#!/usr/bin/env python3
"""Test runner script for bio-hit-finder comprehensive test suite.

Provides convenient commands for running different test categories:
- Unit tests: Fast, isolated component tests
- Integration tests: End-to-end workflow validation  
- Golden tests: Reference data validation with numerical precision
- Performance tests: Benchmark validation against PRD targets
- All tests: Complete test suite

Usage:
    python run_tests.py unit           # Run unit tests only
    python run_tests.py integration    # Run integration tests  
    python run_tests.py golden         # Run golden reference tests
    python run_tests.py performance    # Run performance benchmarks
    python run_tests.py quick          # Run unit + integration (skip slow tests)
    python run_tests.py all            # Run complete test suite
    python run_tests.py coverage       # Run with detailed coverage report
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
import time


def run_command(cmd: List[str], description: str = "") -> int:
    """Run command and return exit code."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed_time = time.time() - start_time
    
    if description:
        print(f"\nCompleted in {elapsed_time:.1f}s with exit code {result.returncode}")
    
    return result.returncode


def get_test_commands() -> Dict[str, Dict[str, Any]]:
    """Return test command configurations."""
    base_cmd = ["python", "-m", "pytest"]
    
    return {
        "unit": {
            "cmd": base_cmd + ["-m", "unit", "-v"],
            "description": "Unit tests (fast, isolated component tests)",
            "estimated_time": "30s"
        },
        
        "integration": {
            "cmd": base_cmd + ["-m", "integration", "-v"],
            "description": "Integration tests (end-to-end workflow validation)",
            "estimated_time": "2-3 minutes"
        },
        
        "golden": {
            "cmd": base_cmd + ["-m", "golden", "-v"],
            "description": "Golden tests (reference data with numerical precision ≤1e-9)",
            "estimated_time": "1-2 minutes"
        },
        
        "performance": {
            "cmd": base_cmd + ["-m", "performance", "-v", "--tb=short"],
            "description": "Performance tests (benchmark validation against PRD targets)",
            "estimated_time": "3-5 minutes"
        },
        
        "visualization": {
            "cmd": base_cmd + ["-m", "visualization", "-v"],
            "description": "Visualization tests (chart generation and export)",
            "estimated_time": "1-2 minutes"
        },
        
        "export": {
            "cmd": base_cmd + ["-m", "export", "-v"],
            "description": "Export tests (CSV, PDF, ZIP validation)",
            "estimated_time": "1-2 minutes"
        },
        
        "quick": {
            "cmd": base_cmd + ["-m", "not slow", "-v", "--tb=short"],
            "description": "Quick tests (unit + integration, skip slow tests)",
            "estimated_time": "2-3 minutes"
        },
        
        "all": {
            "cmd": base_cmd + ["-v"],
            "description": "Complete test suite (all tests including slow ones)",
            "estimated_time": "10-15 minutes"
        },
        
        "coverage": {
            "cmd": base_cmd + [
                "--cov=core", "--cov=analytics", "--cov=visualizations", "--cov=export",
                "--cov-report=term-missing", "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml", "--cov-fail-under=80",
                "-v"
            ],
            "description": "Full test suite with detailed coverage analysis",
            "estimated_time": "10-15 minutes"
        },
        
        "fast": {
            "cmd": base_cmd + ["-m", "not slow and not performance", "-x", "--tb=short"],
            "description": "Fast tests only (skip performance and slow tests)",
            "estimated_time": "1-2 minutes"
        },
        
        "smoke": {
            "cmd": base_cmd + ["-m", "unit", "--maxfail=1", "-x"],
            "description": "Smoke tests (basic functionality check, stop on first failure)",
            "estimated_time": "30s"
        }
    }


def list_test_categories():
    """List available test categories."""
    commands = get_test_commands()
    
    print("\nAvailable test categories:")
    print("=" * 50)
    
    for category, config in commands.items():
        print(f"\n{category:12} - {config['description']}")
        print(f"{'':12}   Estimated time: {config['estimated_time']}")
    
    print("\nExamples:")
    print("  python run_tests.py unit           # Run unit tests")
    print("  python run_tests.py quick          # Run quick test suite")
    print("  python run_tests.py performance    # Run performance benchmarks")
    print("  python run_tests.py all            # Run complete test suite")


def validate_environment():
    """Validate test environment and dependencies."""
    print("Validating test environment...")
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("ERROR: tests/ directory not found. Run from project root.")
        return False
    
    # Check for required test files
    required_files = [
        "tests/test_calculations.py",
        "tests/test_integration.py", 
        "tests/test_golden.py",
        "tests/test_performance.py",
        "tests/test_visualizations.py",
        "tests/test_export.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("ERROR: Missing required test files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    # Try importing pytest
    try:
        import pytest
        print(f"pytest version: {pytest.__version__}")
    except ImportError:
        print("ERROR: pytest not installed. Run: pip install pytest pytest-cov")
        return False
    
    # Check core modules can be imported
    try:
        from core import calculations
        from analytics import bscore
        print("Core modules: OK")
    except ImportError as e:
        print(f"WARNING: Could not import core modules: {e}")
        print("Some tests may fail. Ensure all dependencies are installed.")
    
    print("Environment validation: PASSED")
    return True


def run_specific_tests(test_paths: List[str], extra_args: List[str] = None):
    """Run specific test files or functions."""
    cmd = ["python", "-m", "pytest"] + test_paths
    if extra_args:
        cmd.extend(extra_args)
    
    description = f"Running specific tests: {', '.join(test_paths)}"
    return run_command(cmd, description)


def generate_test_report():
    """Generate comprehensive test report."""
    print("\nGenerating comprehensive test report...")
    
    # Run coverage with all tests
    cmd = [
        "python", "-m", "pytest",
        "--cov=core", "--cov=analytics", "--cov=visualizations", "--cov=export",
        "--cov-report=html:htmlcov", "--cov-report=xml:coverage.xml",
        "--cov-report=term", "--junitxml=test_report.xml",
        "-v"
    ]
    
    exit_code = run_command(cmd, "Comprehensive test report with coverage")
    
    if exit_code == 0:
        print("\nTest report generated successfully!")
        print("Coverage report: htmlcov/index.html")
        print("JUnit XML: test_report.xml")
        print("Coverage XML: coverage.xml")
    
    return exit_code


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Bio-hit-finder comprehensive test suite runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
  unit          - Fast unit tests for individual components  
  integration   - End-to-end workflow tests
  golden        - Reference data validation (≤1e-9 precision)
  performance   - Benchmark tests (PRD requirements)
  visualization - Chart and plot generation tests
  export        - CSV/PDF/ZIP export tests
  quick         - Unit + integration (skip slow tests)
  all           - Complete test suite
  coverage      - Full suite with coverage analysis
  fast          - Skip performance and slow tests
  smoke         - Basic functionality check

Examples:
  %(prog)s unit                    # Run unit tests
  %(prog)s quick                   # Quick test run
  %(prog)s performance            # Performance benchmarks
  %(prog)s --list                 # List all categories
  %(prog)s --report               # Generate comprehensive report
  %(prog)s tests/test_golden.py   # Run specific test file
        """
    )
    
    parser.add_argument(
        "category", 
        nargs="?",
        help="Test category to run (use --list to see all categories)"
    )
    
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List all available test categories"
    )
    
    parser.add_argument(
        "--report",
        action="store_true", 
        help="Generate comprehensive test report with coverage"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate test environment setup"
    )
    
    parser.add_argument(
        "--extra-args",
        nargs="*",
        help="Extra arguments to pass to pytest"
    )
    
    args = parser.parse_args()
    
    # Handle special flags
    if args.list:
        list_test_categories()
        return 0
    
    if args.validate or not args.category:
        if not validate_environment():
            return 1
        if args.validate:
            return 0
    
    if args.report:
        return generate_test_report()
    
    # Get test commands
    commands = get_test_commands()
    
    # Handle specific test file paths
    if args.category and args.category not in commands:
        # Assume it's a test file path
        test_paths = [args.category]
        extra_args = args.extra_args or []
        return run_specific_tests(test_paths, extra_args)
    
    # Handle test categories
    if not args.category:
        print("ERROR: No test category specified.")
        list_test_categories()
        return 1
    
    if args.category not in commands:
        print(f"ERROR: Unknown test category '{args.category}'")
        list_test_categories()
        return 1
    
    # Run the specified test category
    config = commands[args.category]
    cmd = config["cmd"]
    
    if args.extra_args:
        cmd.extend(args.extra_args)
    
    print(f"\nEstimated time: {config['estimated_time']}")
    exit_code = run_command(cmd, config["description"])
    
    # Print summary
    if exit_code == 0:
        print(f"\n✓ {args.category.upper()} tests PASSED")
    else:
        print(f"\n✗ {args.category.upper()} tests FAILED (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)