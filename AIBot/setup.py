#!/usr/bin/env python3
"""
Setup script for FastAPI Multi-Tenant AI Project
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_environment():
    """Set up the development environment."""
    print("🚀 Setting up FastAPI Multi-Tenant AI Project")
    print("=" * 50)
    
    # Check if UV is installed
    if not shutil.which("uv"):
        print("❌ UV package manager not found. Please install UV first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   or visit: https://docs.astral.sh/uv/getting-started/installation/")
        return False
    
    # Install dependencies
    if not run_command("uv sync", "Installing dependencies"):
        return False
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
        print("⚠️  Please edit .env file with your API keys and settings")
    
    # Create database
    if not run_command("uv run python -c \"from src.Backend.Shared.database import Base, engine; Base.metadata.create_all(bind=engine)\"", "Creating database"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: uv run uvicorn src.main:app --reload")
    print("3. Visit: http://localhost:8000/docs")
    
    return True

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    return run_command("uv run pytest", "Running test suite")

def start_server():
    """Start the development server."""
    print("🌐 Starting development server...")
    os.system("uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            run_tests()
        elif sys.argv[1] == "start":
            start_server()
        else:
            print("Usage: python setup.py [test|start]")
    else:
        setup_environment()
