#!/usr/bin/env python3
"""
Local development data seeding script.
Run this to seed data in your local development environment.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from seed_data import DataSeeder


def main():
    """Main function for local seeding."""
    print("🌱 Local Development Data Seeding")
    print("=" * 50)
    
    # Local development configuration
    base_url = "http://localhost:8000"
    environment = "staging"
    
    print(f"📍 Target URL: {base_url}")
    print(f"🌍 Environment: {environment}")
    print(f"⏰ Started at: {datetime.now()}")
    print("-" * 50)
    
    # Create seeder
    seeder = DataSeeder(base_url, environment)
    
    # Run seeding
    print("🚀 Starting local data seeding...")
    success = asyncio.run(seeder.run_seeding())
    
    print("-" * 50)
    if success:
        print("✅ Local data seeding completed successfully!")
        print("\n🔗 Access your local application:")
        print(f"   • API Docs: {base_url}/docs")
        print(f"   • Health Check: {base_url}/health")
        print("\n🔐 Test Credentials:")
        print("   • Admin: admin / staging_admin_123")
        print("   • User: alice_staging / alice123")
        print("   • User: bob_staging / bob123")
        sys.exit(0)
    else:
        print("❌ Local data seeding failed!")
        print("💡 Make sure your local server is running on http://localhost:8000")
        sys.exit(1)


if __name__ == "__main__":
    main()
