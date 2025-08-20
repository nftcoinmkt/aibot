"""
API router for database seeding operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import logging
import sys
import os

# Add the project root to the path to import seed_data
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from seed_data import cleanup_database, initialize_database, create_users, create_channels, create_conversations

logger = logging.getLogger(__name__)

router = APIRouter()

class SeedResponse(BaseModel):
    success: bool
    message: str
    summary: Dict[str, Any] = {}

@router.post("/seed-database", response_model=SeedResponse)
async def seed_database():
    """
    Seed the database with test data including users, channels, and conversations.
    This will clean existing data and create fresh test data.
    """
    try:
        logger.info("Starting database seeding via API...")

        # Clean up existing data first
        cleanup_database()
        logger.info("Database cleanup completed")

        # Initialize database tables
        initialize_database()
        logger.info("Database initialization completed")

        # Create users
        users = create_users()
        logger.info(f"Created {len(users['acme_corp']) + len(users['tech_startup'])} users")

        # Create channels
        channels = create_channels(users)
        logger.info(f"Created {len(channels['acme_corp']) + len(channels['tech_startup'])} channels")

        # Create conversations
        create_conversations(users, channels)
        logger.info("Created conversations")
        
        summary = {
            "users_created": len(users['acme_corp']) + len(users['tech_startup']),
            "channels_created": len(channels['acme_corp']) + len(channels['tech_startup']),
            "conversations_created": 40,
            "tenants": ["acme_corp", "tech_startup"],
            "login_credentials": {
                "acme_corp_admin": "admin1@acme.com / Admin123!",
                "acme_corp_super": "super1@acme.com / Super123!",
                "tech_startup_admin": "admin2@techstartup.com / Admin123!",
                "tech_startup_super": "super2@techstartup.com / Super123!",
                "regular_users": "user[1-6]@[acme.com|techstartup.com] / User123!"
            }
        }
        
        logger.info("Database seeding completed successfully")
        
        return SeedResponse(
            success=True,
            message="Database seeded successfully with test data",
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error during database seeding: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed database: {str(e)}"
        )

@router.post("/cleanup-database", response_model=SeedResponse)
async def cleanup_database_endpoint():
    """
    Clean up all existing data from the database.
    WARNING: This will delete all users, channels, and conversations.
    """
    try:
        logger.info("Starting database cleanup via API...")

        cleanup_database()
        
        logger.info("Database cleanup completed successfully")
        
        return SeedResponse(
            success=True,
            message="Database cleaned up successfully. All data has been removed.",
            summary={"action": "cleanup", "status": "completed"}
        )
        
    except Exception as e:
        logger.error(f"Error during database cleanup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup database: {str(e)}"
        )

@router.post("/initialize-database", response_model=SeedResponse)
async def initialize_database_endpoint():
    """
    Initialize database tables without adding any data.
    """
    try:
        logger.info("Starting database initialization via API...")

        initialize_database()
        
        logger.info("Database initialization completed successfully")
        
        return SeedResponse(
            success=True,
            message="Database tables initialized successfully",
            summary={"action": "initialize", "status": "completed"}
        )
        
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize database: {str(e)}"
        )

@router.get("/seed-status")
async def get_seed_status():
    """
    Get the current status of the database seeding.
    Returns information about existing users and channels.
    """
    try:
        from src.backend.shared.database_manager import DefaultSessionLocal, get_tenant_db
        from src.backend.auth import models as auth_models
        from src.backend.channels.channel_models import Channel
        
        status = {
            "default_db": {"users": 0},
            "acme_corp": {"channels": 0},
            "tech_startup": {"channels": 0}
        }
        
        # Check default database
        db = DefaultSessionLocal()
        try:
            user_count = db.query(auth_models.User).count()
            status["default_db"]["users"] = user_count
        finally:
            db.close()
        
        # Check tenant databases
        for tenant in ["acme_corp", "tech_startup"]:
            try:
                db_generator = get_tenant_db(tenant)
                db = next(db_generator)
                try:
                    channel_count = db.query(Channel).count()
                    status[tenant]["channels"] = channel_count
                finally:
                    db.close()
            except Exception as e:
                status[tenant]["error"] = str(e)
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error getting seed status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get seed status: {str(e)}"
        )
