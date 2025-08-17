#!/usr/bin/env python3
"""
Database initialization script.
Creates tables and seeds initial data.
"""

from src.backend.shared.database_manager import Base, default_engine
from src.backend.auth import models as auth_models
from src.backend.ai_service import models as ai_models
from src.backend.ai_service import channel_models

def init_database():
    """Initialize database tables."""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=default_engine)
    
    print("✅ Database tables created successfully!")
    print("\nTables created:")
    print("- users")
    print("- tenants") 
    print("- chat_messages")
    print("- channels")
    print("- channel_messages")
    print("- channel_members")

if __name__ == "__main__":
    init_database()
