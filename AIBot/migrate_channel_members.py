#!/usr/bin/env python3
"""
Migration script to create channel_members table if it doesn't exist.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database(db_path):
    """Migrate a single database file."""
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if channel_members table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='channel_members'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Create channel_members table
            cursor.execute("""
                CREATE TABLE channel_members (
                    channel_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at DATETIME,
                    role VARCHAR DEFAULT 'member',
                    PRIMARY KEY (channel_id, user_id),
                    FOREIGN KEY(channel_id) REFERENCES channels (id)
                )
            """)
            print("  Created channel_members table")
            
            # Add all existing channel creators as admin members
            cursor.execute("SELECT id, created_by FROM channels")
            channels = cursor.fetchall()
            
            for channel_id, created_by in channels:
                cursor.execute("""
                    INSERT OR IGNORE INTO channel_members (channel_id, user_id, role, joined_at)
                    VALUES (?, ?, 'admin', datetime('now'))
                """, (channel_id, created_by))
            
            if channels:
                print(f"  Added {len(channels)} channel creators as admin members")
        else:
            print("  channel_members table already exists")
        
        conn.commit()
        print(f"  Migration completed successfully for {db_path}")
        
    except Exception as e:
        print(f"  Error migrating {db_path}: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main migration function."""
    print("Starting channel_members table migration...")
    
    # Migrate main database
    if os.path.exists("app.db"):
        migrate_database("app.db")
    
    # Migrate tenant databases
    tenant_db_dir = Path("tenant_databases")
    if tenant_db_dir.exists():
        for db_file in tenant_db_dir.glob("*.db"):
            migrate_database(str(db_file))
    
    print("Migration completed!")

if __name__ == "__main__":
    main()
