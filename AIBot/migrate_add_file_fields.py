#!/usr/bin/env python3
"""
Migration script to add file attachment fields to channel_messages table.
Run this script to update existing databases with the new file fields.
"""

import sqlite3
import os
from pathlib import Path

try:
    # Prefer configured settings
    from src.backend.core.settings import settings
    TENANT_DB_DIR = Path(settings.TENANT_DATABASE_PATH)
except Exception:
    # Fallback to default relative path
    TENANT_DB_DIR = Path("tenant_databases")

def migrate_database(db_path):
    """Add file attachment fields to channel_messages table."""
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(channel_messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add file_url column if it doesn't exist
        if 'file_url' not in columns:
            cursor.execute("ALTER TABLE channel_messages ADD COLUMN file_url TEXT")
            print("  Added file_url column")
        
        # Add file_name column if it doesn't exist
        if 'file_name' not in columns:
            cursor.execute("ALTER TABLE channel_messages ADD COLUMN file_name TEXT")
            print("  Added file_name column")
        
        # Add file_type column if it doesn't exist
        if 'file_type' not in columns:
            cursor.execute("ALTER TABLE channel_messages ADD COLUMN file_type TEXT")
            print("  Added file_type column")

        # Add is_archived column if it doesn't exist
        if 'is_archived' not in columns:
            cursor.execute("ALTER TABLE channel_messages ADD COLUMN is_archived BOOLEAN DEFAULT 0")
            print("  Added is_archived column")

        # Add message_length column if it doesn't exist
        if 'message_length' not in columns:
            cursor.execute("ALTER TABLE channel_messages ADD COLUMN message_length INTEGER")
            print("  Added message_length column")

        # Check and update channels table
        cursor.execute("PRAGMA table_info(channels)")
        channel_columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns to channels table
        if 'is_private' not in channel_columns:
            cursor.execute("ALTER TABLE channels ADD COLUMN is_private BOOLEAN DEFAULT 0")
            print("  Added is_private column to channels")

        if 'max_members' not in channel_columns:
            cursor.execute("ALTER TABLE channels ADD COLUMN max_members INTEGER DEFAULT 100")
            print("  Added max_members column to channels")

        if 'updated_at' not in channel_columns:
            cursor.execute("ALTER TABLE channels ADD COLUMN updated_at DATETIME")
            # Set updated_at to created_at for existing records
            cursor.execute("UPDATE channels SET updated_at = created_at WHERE updated_at IS NULL")
            print("  Added updated_at column to channels")

        conn.commit()
        print(f"  Migration completed successfully for {db_path}")
        
    except Exception as e:
        print(f"  Error migrating {db_path}: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Run migration on all tenant databases only."""
    print("Starting tenant database migration to add file attachment fields...")

    # Migrate tenant databases only
    if TENANT_DB_DIR.exists():
        for db_file in TENANT_DB_DIR.glob("*.db"):
            migrate_database(str(db_file))
    else:
        print(f"Tenant database directory not found: {TENANT_DB_DIR}")

    print("Migration completed!")

if __name__ == "__main__":
    main()
