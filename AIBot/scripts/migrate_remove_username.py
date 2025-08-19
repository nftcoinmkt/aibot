#!/usr/bin/env python3
"""
Database migration script to remove username field from users table.
This script safely removes the username column if it exists.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.core.settings import settings
from backend.shared.database_manager import get_default_db


def migrate_remove_username():
    """Remove username column from users table if it exists."""
    
    print("🔄 Starting username removal migration...")
    
    # Get database session
    db_generator = get_default_db()
    db = next(db_generator)
    
    try:
        # Check if username column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'username'
        """))
        
        if not result.fetchone():
            print("✅ Username column doesn't exist, skipping migration")
            return
        
        print("📝 Removing username column from users table...")
        
        # Drop index on username if it exists
        try:
            db.execute(text("DROP INDEX IF EXISTS idx_users_username"))
            print("  ✅ Dropped username index")
        except Exception as e:
            print(f"  ⚠️  Could not drop username index: {e}")
        
        # Remove username column
        db.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS username"))
        print("  ✅ Dropped username column")
        
        db.commit()
        print("✅ Username removal migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function to run the migration."""
    print("🗄️  Database Username Removal Migration")
    print("=" * 50)
    
    try:
        migrate_remove_username()
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
