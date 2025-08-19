#!/usr/bin/env python3
"""
Test the application startup using uv virtual environment.
"""

import subprocess
import sys
import time
import requests
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

def test_app_startup():
    """Test if the app can start with uv."""
    print("🧪 Testing Application Startup with UV")
    print("=" * 50)
    
    # Change to AIBot directory
    aibot_dir = Path(__file__).parent
    os.chdir(aibot_dir)
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "PORT": "8080",
        "HOST": "0.0.0.0",
        "SECRET_KEY": "test-secret-key-for-testing",
        "GROQ_API_KEY": "test-key",
        "GEMINI_API_KEY": "test-key",
        "ENVIRONMENT": "test"
    })
    
    print("🔧 Environment variables set:")
    for key in ["PORT", "HOST", "SECRET_KEY", "ENVIRONMENT"]:
        print(f"   {key}={env.get(key)}")
    
    # Test 1: Check if uv is available
    print("\n1️⃣ Checking UV availability...")
    success, stdout, stderr = run_command("uv --version")
    if success:
        print(f"   ✅ UV available: {stdout.strip()}")
    else:
        print(f"   ❌ UV not available: {stderr}")
        return False
    
    # Test 2: Install dependencies
    print("\n2️⃣ Installing dependencies...")
    success, stdout, stderr = run_command("uv sync", timeout=120)
    if success:
        print("   ✅ Dependencies installed successfully")
    else:
        print(f"   ❌ Failed to install dependencies: {stderr}")
        return False
    
    # Test 3: Test import
    print("\n3️⃣ Testing imports...")
    test_import_cmd = 'uv run python -c "from src.main import app; print(\\"✅ Import successful\\")"'
    success, stdout, stderr = run_command(test_import_cmd)
    if success:
        print(f"   ✅ {stdout.strip()}")
    else:
        print(f"   ❌ Import failed: {stderr}")
        return False
    
    # Test 4: Start server in background and test health endpoint
    print("\n4️⃣ Testing server startup...")
    
    # Start server in background
    server_cmd = "uv run uvicorn src.main:app --host 0.0.0.0 --port 8080"
    
    try:
        # Start the server process
        server_process = subprocess.Popen(
            server_cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("   🚀 Server starting...")
        
        # Wait for server to start
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8080/health", timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ Server started successfully! Health check: {response.json()}")
                    
                    # Test WebSocket endpoint exists
                    try:
                        # Just check if the endpoint is registered (will fail without proper WebSocket client)
                        ws_response = requests.get("http://localhost:8080/docs", timeout=2)
                        if "websocket" in ws_response.text.lower():
                            print("   ✅ WebSocket endpoints detected in API docs")
                        else:
                            print("   ⚠️ WebSocket endpoints not found in API docs")
                    except:
                        print("   ⚠️ Could not check WebSocket endpoints")
                    
                    return True
                    
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            print(f"   ⏳ Waiting for server... ({attempt + 1}/{max_attempts})")
        
        print("   ❌ Server failed to start within timeout")
        
        # Get server output for debugging
        try:
            stdout, stderr = server_process.communicate(timeout=5)
            if stdout:
                print(f"   📄 Server stdout: {stdout}")
            if stderr:
                print(f"   📄 Server stderr: {stderr}")
        except:
            pass
        
        return False
        
    except Exception as e:
        print(f"   ❌ Failed to start server: {e}")
        return False
        
    finally:
        # Clean up server process
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            try:
                server_process.kill()
            except:
                pass

def main():
    """Run the startup test."""
    try:
        success = test_app_startup()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 Application startup test PASSED!")
            print("✅ The app should work in Cloud Run")
            return 0
        else:
            print("💥 Application startup test FAILED!")
            print("❌ There are issues that need to be fixed")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
