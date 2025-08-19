#!/usr/bin/env python3
"""
Test script to verify that all imports work without SQLAlchemy conflicts.
"""

import sys
import os
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    # Set required environment variables
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    
    try:
        print("  ✅ Testing basic imports...")
        from fastapi import FastAPI
        
        print("  ✅ Testing settings import...")
        from backend.core.settings import settings
        
        print("  ✅ Testing database import...")
        from backend.shared.database_manager import default_engine, Base
        
        print("  ✅ Testing auth models import...")
        from backend.auth import models as auth_models
        
        print("  ✅ Testing channels models import...")
        from backend.channels import models as channel_models
        
        print("  ✅ Testing AI service models import...")
        from backend.ai_service import models as ai_models
        
        print("  ✅ Testing main app import...")
        from main import app
        
        print("  ✅ Testing routes...")
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"  📋 Found {len(routes)} routes")
        
        # Check for essential routes
        essential_routes = ["/health", "/api/v1/auth/tenants", "/api/v1/auth/signup"]
        for route in essential_routes:
            if any(route in r for r in routes):
                print(f"  ✅ Found essential route: {route}")
            else:
                print(f"  ⚠️ Missing route: {route}")
        
        print("  ✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the import test."""
    print("🧪 SQLAlchemy Table Conflict Test")
    print("=" * 40)
    
    success = test_imports()
    
    print("=" * 40)
    if success:
        print("🎉 All imports successful!")
        print("✅ SQLAlchemy table conflicts resolved")
        return 0
    else:
        print("💥 Import test failed!")
        print("❌ There are still issues to fix")
        return 1

if __name__ == "__main__":
    sys.exit(main())
