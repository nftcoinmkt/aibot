#!/usr/bin/env python3
"""
Database migration script to add MessageCentral fields to otp_requests table.
"""
import sqlite3
import os

def migrate_database():
    """Add MessageCentral columns to existing database."""
    db_paths = [
        "app.db",
        "tenant_databases/acme_corp.db", 
        "tenant_databases/hippocampus.db",
        "tenant_databases/tech_startup.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Migrating {db_path}...")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if columns already exist
                cursor.execute("PRAGMA table_info(otp_requests)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'messagecentral_verification_id' not in columns:
                    cursor.execute("ALTER TABLE otp_requests ADD COLUMN messagecentral_verification_id TEXT")
                    print(f"  Added messagecentral_verification_id to {db_path}")
                
                if 'messagecentral_timeout' not in columns:
                    cursor.execute("ALTER TABLE otp_requests ADD COLUMN messagecentral_timeout TEXT")
                    print(f"  Added messagecentral_timeout to {db_path}")
                
                conn.commit()
                conn.close()
                print(f"  Migration completed for {db_path}")
                
            except Exception as e:
                print(f"  Error migrating {db_path}: {e}")
        else:
            print(f"  Database {db_path} not found, skipping...")

if __name__ == "__main__":
    migrate_database()
    print("Database migration completed!")
