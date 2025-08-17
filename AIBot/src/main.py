
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.backend.auth import router as auth_router
from src.backend.auth import schemas as auth_schemas
from src.backend.auth.authentication_service import (
    get_current_active_user, 
    get_current_active_superuser, 
    get_current_active_admin
)
from src.backend.ai_service import router as ai_router
from src.backend.core.settings import settings
from src.backend.shared.database_manager import default_engine, Base

# Create default database tables
Base.metadata.create_all(bind=default_engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="FastAPI Multi-Tenant AI Application with LangGraph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Public API ---
@app.get(f"{settings.API_V1_STR}/hello")
def read_root():
    return {"message": "Hello, world!"}

# --- Authentication Required API ---
@app.get(f"{settings.API_V1_STR}/welcome", response_model=auth_schemas.Msg)
def welcome(
    current_user: auth_schemas.User = Depends(get_current_active_user)
):
    return {"msg": f"Welcome, {current_user.full_name}!"}

# --- Role-Specific APIs ---
@app.get(f"{settings.API_V1_STR}/user/me", response_model=auth_schemas.Msg)
def read_user_me(
    current_user: auth_schemas.User = Depends(get_current_active_user)
):
    return {"msg": "This is a user-specific endpoint."}

@app.get(f"{settings.API_V1_STR}/superuser/me", response_model=auth_schemas.Msg)
def read_superuser_me(
    current_user: auth_schemas.User = Depends(get_current_active_superuser)
):
    return {"msg": "This is a superuser-specific endpoint."}

@app.get(f"{settings.API_V1_STR}/admin/me", response_model=auth_schemas.Msg)
def read_admin_me(
    current_user: auth_schemas.User = Depends(get_current_active_admin)
):
    return {"msg": "This is an admin-specific endpoint."}

# --- Include Routers ---
app.include_router(auth_router.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(ai_router.router, prefix=settings.API_V1_STR, tags=["ai_service"])

# Import and include channel router
from src.backend.channels import router as channels_router
app.include_router(channels_router.router, prefix=settings.API_V1_STR, tags=["channels"])

# Mount static files for uploads
import os
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# --- Debug: Print all registered routes ---
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
for route in app.routes:
    if hasattr(route, "path"):
        logger.info(f"Registered route: {route.path} Methods: {getattr(route, 'methods', 'N/A')}")

