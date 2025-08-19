#!/usr/bin/env python3
"""
Data seeding script for AI Bot application.
Seeds initial data including users, channels, and sample messages.
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from backend.core.settings import settings
except ImportError:
    # Fallback if settings not available
    settings = None

from seed_config import SeedConfig


class DataSeeder:
    """Handles seeding of initial data for the AI Bot application."""

    def __init__(self, base_url: str, environment: str = "staging"):
        self.base_url = base_url.rstrip('/')
        self.environment = environment
        self.session = requests.Session()
        self.admin_token = None
        self.users = []
        self.channels = []
        self.config = SeedConfig()
    
    def log(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def create_admin_user(self) -> Dict:
        """Create the admin user."""
        admin_data = self.config.get_admin_user(self.environment)
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=admin_data
            )
            
            if response.status_code == 200:
                self.log("✅ Admin user created successfully")
                return response.json()
            else:
                self.log(f"❌ Failed to create admin user: {response.text}")
                return None
        except Exception as e:
            self.log(f"❌ Error creating admin user: {e}")
            return None
    
    def login_admin(self) -> bool:
        """Login as admin and get token."""
        admin_config = self.config.get_admin_user(self.environment)
        login_data = {
            "username": admin_config["email"],  # OAuth2 uses 'username' field but we pass email
            "password": admin_config["password"]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login/access-token",
                data=login_data  # Form data for OAuth2
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                self.log("✅ Admin login successful")
                return True
            else:
                self.log(f"❌ Admin login failed: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error during admin login: {e}")
            return False
    
    def create_sample_users(self) -> List[Dict]:
        """Create sample users for testing."""
        sample_users = self.config.get_sample_users(self.environment)
        
        created_users = []
        for user_data in sample_users:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data
                )
                
                if response.status_code == 200:
                    user = response.json()
                    created_users.append(user)
                    self.log(f"✅ Created user: {user_data['username']}")
                else:
                    self.log(f"❌ Failed to create user {user_data['username']}: {response.text}")
            except Exception as e:
                self.log(f"❌ Error creating user {user_data['username']}: {e}")
        
        self.users = created_users
        return created_users
    
    def create_sample_channels(self) -> List[Dict]:
        """Create sample channels."""
        sample_channels = self.config.get_sample_channels(self.environment)
        
        created_channels = []
        for channel_data in sample_channels:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/channels",
                    json=channel_data
                )
                
                if response.status_code == 200:
                    channel = response.json()
                    created_channels.append(channel)
                    self.log(f"✅ Created channel: {channel_data['name']}")
                else:
                    self.log(f"❌ Failed to create channel {channel_data['name']}: {response.text}")
            except Exception as e:
                self.log(f"❌ Error creating channel {channel_data['name']}: {e}")
        
        self.channels = created_channels
        return created_channels
    
    def create_sample_messages(self):
        """Create sample messages in channels."""
        if not self.channels:
            self.log("❌ No channels available for seeding messages")
            return
        
        sample_messages = self.config.get_sample_messages(self.environment)
        
        # Send messages to the first channel
        if self.channels:
            channel_id = self.channels[0]["id"]
            
            for i, message_text in enumerate(sample_messages):
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/v1/ai/chat/channel/{channel_id}",
                        json={"message": message_text}
                    )
                    
                    if response.status_code == 200:
                        self.log(f"✅ Created sample message {i+1}")
                    else:
                        self.log(f"❌ Failed to create message {i+1}: {response.text}")
                        
                    # Add small delay between messages
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.log(f"❌ Error creating message {i+1}: {e}")
    
    def verify_deployment(self) -> bool:
        """Verify that the deployment is healthy."""
        try:
            # Check health endpoint
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log("✅ Health check passed")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}")
            return False
    
    async def run_seeding(self):
        """Run the complete data seeding process."""
        self.log("🌱 Starting data seeding process...")
        
        # Wait for deployment to be ready
        self.log("⏳ Waiting for deployment to be ready...")
        for attempt in range(30):  # Wait up to 5 minutes
            if self.verify_deployment():
                break
            await asyncio.sleep(10)
        else:
            self.log("❌ Deployment not ready after 5 minutes")
            return False
        
        # Create admin user
        self.log("👤 Creating admin user...")
        admin_user = self.create_admin_user()
        if not admin_user:
            return False
        
        # Login as admin
        self.log("🔐 Logging in as admin...")
        if not self.login_admin():
            return False
        
        # Create sample users
        self.log("👥 Creating sample users...")
        users = self.create_sample_users()
        self.log(f"✅ Created {len(users)} sample users")
        
        # Create sample channels
        self.log("📢 Creating sample channels...")
        channels = self.create_sample_channels()
        self.log(f"✅ Created {len(channels)} sample channels")
        
        # Create sample messages
        self.log("💬 Creating sample messages...")
        self.create_sample_messages()
        
        self.log("🎉 Data seeding completed successfully!")
        return True


def main():
    """Main function to run data seeding."""
    # Get configuration from environment
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    environment = os.getenv("ENVIRONMENT", "staging")

    print(f"🌱 AI Bot Data Seeding")
    print(f"📍 Target URL: {base_url}")
    print(f"🌍 Environment: {environment}")
    print(f"⏰ Started at: {datetime.now()}")
    print("-" * 50)

    seeder = DataSeeder(base_url, environment)
    
    # Run seeding
    success = asyncio.run(seeder.run_seeding())
    
    print("-" * 50)
    if success:
        print("✅ Data seeding completed successfully!")
        sys.exit(0)
    else:
        print("❌ Data seeding failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
