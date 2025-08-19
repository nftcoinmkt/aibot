#!/usr/bin/env python3
"""
Production data seeding script with safety checks.
This script includes additional safety measures for production environments.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from seed_data import DataSeeder


def confirm_production_seeding():
    """Confirm that user wants to seed production data."""
    print("⚠️  PRODUCTION ENVIRONMENT DETECTED ⚠️")
    print("This will create initial data in your production environment.")
    print("This should only be done ONCE when first deploying to production.")
    print()
    
    # Check if this is automated (GitHub Actions)
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("🤖 Running in GitHub Actions - proceeding automatically")
        return True
    
    # Manual confirmation for interactive runs
    response = input("Are you sure you want to proceed? (type 'YES' to confirm): ")
    return response == "YES"


def main():
    """Main function for production seeding."""
    print("🌱 Production Data Seeding")
    print("=" * 50)
    
    # Get configuration
    base_url = os.getenv("BACKEND_URL")
    if not base_url:
        print("❌ BACKEND_URL environment variable is required")
        sys.exit(1)
    
    environment = "production"
    
    print(f"📍 Target URL: {base_url}")
    print(f"🌍 Environment: {environment}")
    print(f"⏰ Started at: {datetime.now()}")
    print("-" * 50)
    
    # Safety confirmation
    if not confirm_production_seeding():
        print("❌ Production seeding cancelled by user")
        sys.exit(1)
    
    # Verify admin password is set
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        print("❌ ADMIN_PASSWORD environment variable is required for production")
        sys.exit(1)
    
    # Create seeder
    seeder = DataSeeder(base_url, environment)
    
    # Run seeding
    print("🚀 Starting production data seeding...")
    success = asyncio.run(seeder.run_seeding())
    
    print("-" * 50)
    if success:
        print("✅ Production data seeding completed successfully!")
        print("\n🔗 Access your production application:")
        print(f"   • API Docs: {base_url}/docs")
        print(f"   • Health Check: {base_url}/health")
        print("\n🔐 Admin Credentials:")
        print("   • Username: admin")
        print("   • Password: [ADMIN_PASSWORD from environment]")
        print("\n⚠️  IMPORTANT: Change the admin password after first login!")
        sys.exit(0)
    else:
        print("❌ Production data seeding failed!")
        print("🔍 Check the logs above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
