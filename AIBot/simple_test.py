#!/usr/bin/env python3
"""
Simple test to check if the application can start.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, timeout=30):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def main():
    """Test the application."""
    print("🧪 Simple Application Test")
    print("=" * 40)
    
    # Change to AIBot directory
    aibot_dir = Path(__file__).parent
    os.chdir(aibot_dir)
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "PORT": "8080",
        "SECRET_KEY": "test-secret-key",
        "GROQ_API_KEY": "test-key",
        "GEMINI_API_KEY": "test-key"
    })
    
    # Test 1: Check UV
    print("1️⃣ Checking UV...")
    success, stdout, stderr = run_command("uv --version")
    if success:
        print(f"   ✅ UV: {stdout.strip()}")
    else:
        print(f"   ❌ UV not found: {stderr}")
        return 1
    
    # Test 2: Sync dependencies
    print("\n2️⃣ Syncing dependencies...")
    success, stdout, stderr = run_command("uv sync", timeout=120)
    if success:
        print("   ✅ Dependencies synced")
    else:
        print(f"   ❌ Sync failed: {stderr}")
        return 1
    
    # Test 3: Test import
    print("\n3️⃣ Testing imports...")
    import_cmd = 'uv run python -c "import sys; sys.path.insert(0, \\"src\\"); from main import app; print(\\"Import successful\\"); print(f\\"Routes: {len(app.routes)}\\")"'
    success, stdout, stderr = run_command(import_cmd, timeout=30)
    if success:
        print(f"   ✅ {stdout.strip()}")
    else:
        print(f"   ❌ Import failed:")
        print(f"      stdout: {stdout}")
        print(f"      stderr: {stderr}")
        return 1
    
    # Test 4: Test server start (just for a few seconds)
    print("\n4️⃣ Testing server start...")
    server_cmd = "timeout 10 uv run uvicorn src.main:app --host 0.0.0.0 --port 8080"
    success, stdout, stderr = run_command(server_cmd, timeout=15)
    
    # For server test, we expect it to timeout (that's good - means it started)
    if "timeout" in stderr.lower() or "started server process" in stdout.lower() or "uvicorn running" in stdout.lower():
        print("   ✅ Server started successfully (timed out as expected)")
    else:
        print(f"   ❌ Server failed to start:")
        print(f"      stdout: {stdout}")
        print(f"      stderr: {stderr}")
        return 1
    
    print("\n" + "=" * 40)
    print("🎉 All tests passed!")
    print("✅ Application should work in Cloud Run")
    return 0

if __name__ == "__main__":
    sys.exit(main())
