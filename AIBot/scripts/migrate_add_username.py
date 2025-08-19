#!/usr/bin/env python3
"""
Database migration script to add username field to users table.
This script safely adds the username column and populates it for existing users.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.core.settings import settings
from backend.shared.database_manager import get_default_db
from backend.auth.models import User


def migrate_add_username():
    """Add username column to users table and populate for existing users."""
    
    print("🔄 Starting username migration...")
    
    # Get database session
    db_generator = get_default_db()
    db = next(db_generator)
    
    try:
        # Check if username column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'username'
        """))
        
        if result.fetchone():
            print("✅ Username column already exists, skipping migration")
            return
        
        print("📝 Adding username column to users table...")
        
        # Add username column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN username VARCHAR(50) UNIQUE
        """))
        
        # Get all existing users
        users = db.query(User).all()
        
        print(f"👥 Found {len(users)} existing users, generating usernames...")
        
        # Generate usernames for existing users
        for user in users:
            # Generate username from email (part before @)
            base_username = user.email.split('@')[0]
            
            # Ensure username is unique
            username = base_username
            counter = 1
            
            while True:
                # Check if username exists
                existing = db.execute(text(
                    "SELECT id FROM users WHERE username = :username"
                ), {"username": username}).fetchone()
                
                if not existing:
                    break
                
                username = f"{base_username}_{counter}"
                counter += 1
            
            # Update user with generated username
            db.execute(text("""
                UPDATE users 
                SET username = :username 
                WHERE id = :user_id
            """), {"username": username, "user_id": user.id})
            
            print(f"  ✅ {user.email} → {username}")
        
        # Make username column NOT NULL after populating
        print("🔒 Making username column NOT NULL...")
        db.execute(text("""
            ALTER TABLE users 
            ALTER COLUMN username SET NOT NULL
        """))
        
        # Create index on username
        print("📊 Creating index on username...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON users(username)
        """))
        
        db.commit()
        print("✅ Username migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function to run the migration."""
    print("🗄️  Database Username Migration")
    print("=" * 50)
    
    try:
        migrate_add_username()
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
