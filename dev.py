#!/usr/bin/env python3
"""Development script to run both frontend and backend concurrently."""

import subprocess
import os
import sys
import signal
import time
from pathlib import Path

processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Shutting down development servers...")
    for process in processes:
        try:
            process.terminate()
        except:
            pass
    sys.exit(0)

def run_backend():
    """Run the FastAPI backend."""
    backend_dir = Path(__file__).parent / "backend"
    print("🐍 Starting FastAPI backend on http://localhost:8000")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        processes.append(process)
        
        # Print backend output
        for line in process.stdout:
            print(f"[Backend] {line.strip()}")
            
    except KeyboardInterrupt:
        pass

def run_frontend():
    """Run the Vite frontend dev server."""
    frontend_dir = Path(__file__).parent / "frontend"
    print("⚛️  Starting React dev server on http://localhost:5173")
    
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        processes.append(process)
        
        # Print frontend output
        for line in process.stdout:
            print(f"[Frontend] {line.strip()}")
            
    except KeyboardInterrupt:
        pass

def main():
    """Main development server."""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting bio-hit-finder development environment...")
    print("📋 Services:")
    print("   - Backend (FastAPI): http://localhost:8000")  
    print("   - Frontend (Vite): http://localhost:5173")
    print("   - API Base URL: http://localhost:8000/api")
    print("\n💡 Press Ctrl+C to stop all services\n")
    
    # Check if frontend dependencies are installed
    frontend_dir = Path(__file__).parent / "frontend"
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    
    # Start backend in a separate process
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=Path(__file__).parent / "backend"
    )
    processes.append(backend_process)
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Start frontend in a separate process  
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir
    )
    processes.append(frontend_process)
    
    try:
        # Wait for processes to complete
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()