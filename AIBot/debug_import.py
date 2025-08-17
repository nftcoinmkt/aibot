#!/usr/bin/env python3
"""Debug script to check import issues."""

try:
    print("Starting import test...")
    
    print("1. Importing settings...")
    from src.backend.core.settings import settings
    print(f"   API_V1_STR: {settings.API_V1_STR}")
    
    print("2. Importing auth router...")
    from src.backend.auth import router as auth_router
    print(f"   Auth router loaded: {len(auth_router.router.routes)} routes")
    
    print("3. Importing AI router...")
    from src.backend.ai_service import router as ai_router
    print(f"   AI router loaded: {len(ai_router.router.routes)} routes")
    
    print("4. Importing main app...")
    from src.main import app
    print(f"   Main app loaded: {len(app.routes)} total routes")
    
    print("5. Listing all routes:")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"   - {route.path} {getattr(route, 'methods', 'N/A')}")
    
    print("SUCCESS: All imports completed")
    
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    print(f"Traceback: {traceback.format_exc()}")
