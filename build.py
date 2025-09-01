#!/usr/bin/env python3
"""Build script for bio-hit-finder monolithic deployment."""

import subprocess
import os
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and handle errors."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return False

def build_frontend():
    """Build the React frontend."""
    print("📦 Building React frontend...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend dependencies...")
        if not run_command("npm install", cwd=frontend_dir):
            return False
    
    # Build the frontend
    if not run_command("npm run build", cwd=frontend_dir):
        return False
    
    print("✅ Frontend build complete!")
    return True

def setup_backend():
    """Set up the backend environment."""
    print("🐍 Setting up Python backend...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    # Check if virtual environment should be created
    print("Backend ready!")
    return True

def main():
    """Main build process."""
    print("🚀 Building bio-hit-finder for deployment...")
    
    # Build frontend
    if not build_frontend():
        print("❌ Frontend build failed!")
        return False
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed!")
        return False
    
    print("✅ Build complete! Ready for deployment.")
    print("\n📋 Next steps:")
    print("1. Deploy to Render or run locally with: cd backend && python main.py")
    print("2. Backend will serve frontend at http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)