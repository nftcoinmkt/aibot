"""
API router for database seeding operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import logging

# Import the seed functions (import inside functions to avoid circular imports)

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

        # Import seed functions locally to avoid circular imports
        try:
            from scripts.seed_data import cleanup_database, initialize_database, create_users, create_channels, create_conversations
        except ImportError:
            # Fallback for different import paths
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from scripts.seed_data import cleanup_database, initialize_database, create_users, create_channels, create_conversations

        # Clean up existing data first
        cleanup_database()
        logger.info("Database cleanup completed")

        # Initialize database tables
        initialize_database()
        logger.info("Database initialization completed")

        # Create users
        users = create_users()
        logger.info(f"Created {len(users['tenant1']) + len(users['tenant2'])} users")

        # Create channels
        channels = create_channels(users)
        logger.info(f"Created {len(channels['tenant1']) + len(channels['tenant2'])} channels")

        # Create conversations
        create_conversations(users, channels)
        logger.info("Created conversations")
        
        summary = {
            "users_created": len(users['tenant1']) + len(users['tenant2']),
            "channels_created": len(channels['tenant1']) + len(channels['tenant2']),
            "conversations_created": 40,
            "tenants": ["tenant1", "tenant2"],
            "login_credentials": {
                "tenant1_admin": "admin1@company1.com / Admin123!",
                "tenant1_super": "super1@company1.com / Super123!",
                "tenant2_admin": "admin2@company2.com / Admin123!",
                "tenant2_super": "super2@company2.com / Super123!",
                "regular_users": "user[1-6]@company[1-2].com / User123!"
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

        # Import locally to avoid circular imports
        try:
            from scripts.seed_data import cleanup_database
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from scripts.seed_data import cleanup_database

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

        # Import locally to avoid circular imports
        try:
            from scripts.seed_data import initialize_database
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from scripts.seed_data import initialize_database

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
        from src.backend.ai_service.channel_models import Channel
        
        status = {
            "default_db": {"users": 0},
            "tenant1": {"channels": 0},
            "tenant2": {"channels": 0}
        }
        
        # Check default database
        db = DefaultSessionLocal()
        try:
            user_count = db.query(auth_models.User).count()
            status["default_db"]["users"] = user_count
        finally:
            db.close()
        
        # Check tenant databases
        for tenant in ["tenant1", "tenant2"]:
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
