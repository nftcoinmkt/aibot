"""
Configuration for data seeding in different environments.
"""

import os
from typing import Dict, List


class SeedConfig:
    """Configuration for data seeding."""
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment."""
        return os.getenv("ENVIRONMENT", "staging")
    
    @staticmethod
    def get_admin_user(environment: str) -> Dict:
        """Get admin user configuration for environment."""
        configs = {
            "staging": {
                "email": "admin@staging.aibot.com",
                "password": "staging_admin_123",
                "full_name": "Staging Administrator",
                "tenant_name": "acme_corp",
                "role": "admin"
            },
            "production": {
                "email": "admin@aibot.com",
                "password": os.getenv("ADMIN_PASSWORD", "secure_admin_password_123"),
                "full_name": "Production Administrator",
                "tenant_name": "acme_corp",
                "role": "admin"
            }
        }
        return configs.get(environment, configs["staging"])
    
    @staticmethod
    def get_sample_users(environment: str) -> List[Dict]:
        """Get sample users for environment."""
        if environment == "production":
            # Minimal users for production
            return [
                {
                    "email": "demo@aibot.com",
                    "password": "demo123",
                    "full_name": "Demo User",
                    "tenant_name": "acme_corp",
                    "role": "user"
                }
            ]
        
        # Full sample data for staging
        return [
            {
                "email": "alice@staging.aibot.com",
                "password": "alice123",
                "full_name": "Alice Johnson (Staging)",
                "tenant_name": "tech_startup",
                "role": "user"
            },
            {
                "email": "bob@staging.aibot.com",
                "password": "bob123",
                "full_name": "Bob Smith (Staging)",
                "tenant_name": "tech_startup",
                "role": "user"
            },
            {
                "email": "charlie@staging.aibot.com",
                "password": "charlie123",
                "full_name": "Charlie Brown (Staging)",
                "tenant_name": "university",
                "role": "user"
            },
            {
                "email": "diana@staging.aibot.com",
                "password": "diana123",
                "full_name": "Diana Prince (Staging)",
                "tenant_name": "design_agency",
                "role": "admin"
            }
        ]
    
    @staticmethod
    def get_sample_channels(environment: str) -> List[Dict]:
        """Get sample channels for environment."""
        if environment == "production":
            # Minimal channels for production
            return [
                {
                    "name": "Welcome",
                    "description": "Welcome to AI Bot! Start your conversations here.",
                    "is_private": False,
                    "max_members": 1000
                }
            ]
        
        # Full sample channels for staging
        return [
            {
                "name": "General Discussion",
                "description": "General chat for all team members",
                "is_private": False,
                "max_members": 100
            },
            {
                "name": "AI Development",
                "description": "Discussions about AI development and features",
                "is_private": False,
                "max_members": 50
            },
            {
                "name": "Project Updates",
                "description": "Important project announcements and updates",
                "is_private": True,
                "max_members": 20
            },
            {
                "name": "Random",
                "description": "Off-topic discussions and fun conversations",
                "is_private": False,
                "max_members": 200
            },
            {
                "name": "Testing Ground",
                "description": "Channel for testing new features and functionality",
                "is_private": False,
                "max_members": 50
            }
        ]
    
    @staticmethod
    def get_sample_messages(environment: str) -> List[str]:
        """Get sample messages for environment."""
        if environment == "production":
            return [
                "Welcome to AI Bot! 🤖",
                "This is your AI-powered chat assistant. Feel free to ask questions!",
                "Try uploading images or documents for AI analysis.",
            ]
        
        # Comprehensive sample messages for staging
        return [
            "Hello everyone! Welcome to the AI Bot chat system! 🤖",
            "This is a staging environment for testing the chat functionality.",
            "How is everyone doing today?",
            "The AI integration is working great! Try asking some questions.",
            "Don't forget to test the file upload feature with images and PDFs.",
            "Real-time chat is now enabled - you should see messages instantly!",
            "What do you think about the new UI improvements?",
            "Feel free to create new channels for different topics.",
            "This message tests the multi-user chat functionality.",
            "Try opening multiple browser tabs to see real-time updates!",
            "The typing indicators should work when someone is composing a message.",
            "File attachments now show previews - very cool! 📎",
            "The archive system keeps old messages organized.",
            "Dashboard shows recent activity and channel information.",
            "WebSocket connections enable instant message delivery.",
        ]
