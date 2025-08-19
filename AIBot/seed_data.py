#!/usr/bin/env python3
"""
Seed script to populate the database with test data.
Creates users, channels, and conversations for testing.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random
from sqlalchemy.orm import Session

from src.backend.shared.database_manager import DefaultSessionLocal, get_tenant_db, Base, default_engine
from src.backend.auth.user_management import user_management_service
from src.backend.auth import schemas as auth_schemas, models as auth_models
from src.backend.ai_service.channel_service import channel_service
from src.backend.ai_service import channel_schemas
from src.backend.ai_service.chat_service import chat_service
from src.backend.ai_service.channel_models import ChannelMessage, Channel, channel_members
from src.backend.ai_service.models import ChatMessage
from src.backend.core.settings import settings


# Sample conversation data
SALES_CONVERSATIONS = [
    ("What's our Q4 sales target?", "Based on current trends, our Q4 sales target should be $2.5M, representing a 15% increase from Q3."),
    ("How can we improve customer retention?", "Focus on personalized follow-ups, loyalty programs, and addressing customer feedback within 24 hours."),
    ("What's the best time to contact prospects?", "Research shows Tuesday-Thursday between 10-11 AM and 2-3 PM have the highest response rates."),
    ("How do we handle price objections?", "Emphasize value over price, offer payment plans, and demonstrate ROI with concrete examples."),
    ("What CRM features should we prioritize?", "Lead scoring, automated follow-ups, pipeline visualization, and integration with email marketing tools."),
    ("How to qualify leads effectively?", "Use BANT criteria: Budget, Authority, Need, and Timeline. Ask open-ended questions to understand pain points."),
    ("What's our conversion rate benchmark?", "Industry average is 2-3%, but top performers achieve 5-7% through targeted messaging and nurturing."),
    ("How to handle competitor comparisons?", "Focus on unique value propositions, customer success stories, and superior service quality."),
    ("What sales metrics should we track?", "Track conversion rates, average deal size, sales cycle length, and customer acquisition cost."),
    ("How to improve cold email responses?", "Personalize subject lines, keep emails under 100 words, include clear CTAs, and follow up strategically.")
]

HR_CONVERSATIONS = [
    ("What's our current employee turnover rate?", "Our turnover rate is 12% annually, which is below the industry average of 15%. Focus on retention strategies."),
    ("How do we improve employee engagement?", "Implement regular feedback sessions, recognition programs, flexible work arrangements, and career development plans."),
    ("What are the key hiring metrics to track?", "Time-to-hire, cost-per-hire, quality of hire, and candidate satisfaction scores are essential metrics."),
    ("How to conduct effective performance reviews?", "Use 360-degree feedback, set SMART goals, focus on development, and maintain regular check-ins."),
    ("What's the best approach for remote onboarding?", "Create digital welcome packages, assign mentors, schedule virtual coffee chats, and provide clear documentation."),
    ("How to handle workplace conflicts?", "Listen actively, remain neutral, focus on facts, facilitate open communication, and document resolutions."),
    ("What training programs should we prioritize?", "Leadership development, technical skills, diversity & inclusion, and mental health awareness training."),
    ("How to improve diversity in hiring?", "Expand sourcing channels, use inclusive job descriptions, implement blind resume reviews, and diverse interview panels."),
    ("What are effective employee retention strategies?", "Competitive compensation, growth opportunities, work-life balance, recognition programs, and strong company culture."),
    ("How to measure training effectiveness?", "Use Kirkpatrick's model: reaction, learning, behavior change, and business results measurement.")
]

ADMINISTRATION_CONVERSATIONS = [
    ("What's our office space utilization rate?", "Current utilization is 75% with hybrid work. Consider flexible seating arrangements to optimize space."),
    ("How can we reduce operational costs?", "Implement energy-efficient systems, negotiate vendor contracts, automate routine processes, and reduce paper usage."),
    ("What's the best way to manage vendor relationships?", "Regular performance reviews, clear SLAs, competitive bidding, and maintaining backup vendors for critical services."),
    ("How do we improve internal communication?", "Use collaboration tools, regular town halls, clear communication policies, and feedback mechanisms."),
    ("What security measures should we implement?", "Multi-factor authentication, regular security training, access controls, and incident response procedures."),
    ("How to streamline approval processes?", "Implement digital workflows, set clear approval hierarchies, automate routine approvals, and track processing times."),
    ("What's our disaster recovery plan status?", "Plan covers data backup, alternative work sites, communication protocols, and regular testing every 6 months."),
    ("How to manage office supplies efficiently?", "Implement inventory management system, bulk purchasing, usage tracking, and sustainable procurement practices."),
    ("What facilities maintenance schedule should we follow?", "Quarterly HVAC service, monthly safety inspections, annual equipment audits, and preventive maintenance programs."),
    ("How to improve meeting room booking system?", "Use smart booking software, implement usage policies, provide AV support, and track utilization metrics.")
]

EMPLOYEES_CONVERSATIONS = [
    ("What benefits are available to employees?", "Health insurance, dental/vision, 401k matching, PTO, professional development budget, and wellness programs."),
    ("How do I request time off?", "Use the HR portal to submit requests at least 2 weeks in advance, ensure coverage, and get manager approval."),
    ("What's the remote work policy?", "Hybrid model allows 3 days remote per week, requires home office setup, and maintains core collaboration hours."),
    ("How can I access professional development?", "Annual $2000 budget for courses, conferences, certifications. Submit requests through learning management system."),
    ("What's the process for internal transfers?", "Discuss with current manager, apply through internal job board, meet requirements, and complete transition plan."),
    ("How do I report workplace issues?", "Contact HR directly, use anonymous reporting system, or speak with your manager. All reports are confidential."),
    ("What's our performance review cycle?", "Annual reviews in Q1, mid-year check-ins in Q3, continuous feedback encouraged, and goal-setting quarterly."),
    ("How to access IT support?", "Submit tickets through help desk portal, call extension 4357, or visit IT office for urgent issues."),
    ("What wellness programs are available?", "Gym membership reimbursement, mental health resources, wellness challenges, and flexible work arrangements."),
    ("How do I update my personal information?", "Log into employee self-service portal, update details, submit required documentation, and notify payroll of changes.")
]

def create_users():
    """Create users for both tenants with specified roles."""
    db = DefaultSessionLocal()
    
    try:
        # Tenant 1 users (using valid tenant ID)
        tenant1_users = [
            {"email": "admin1@acme.com", "password": "Admin123!", "full_name": "Alice Admin", "role": auth_schemas.UserRole.ADMIN, "tenant_name": "acme_corp"},
            {"email": "super1@acme.com", "password": "Super123!", "full_name": "Bob SuperUser", "role": auth_schemas.UserRole.SUPER_USER, "tenant_name": "acme_corp"},
            {"email": "user1@acme.com", "password": "User123!", "full_name": "Carol User", "role": auth_schemas.UserRole.USER, "tenant_name": "acme_corp"},
            {"email": "user2@acme.com", "password": "User123!", "full_name": "David User", "role": auth_schemas.UserRole.USER, "tenant_name": "acme_corp"},
            {"email": "user3@acme.com", "password": "User123!", "full_name": "Eve User", "role": auth_schemas.UserRole.USER, "tenant_name": "acme_corp"},
        ]
        
        # Tenant 2 users (using valid tenant ID)
        tenant2_users = [
            {"email": "admin2@techstartup.com", "password": "Admin123!", "full_name": "Frank Admin", "role": auth_schemas.UserRole.ADMIN, "tenant_name": "tech_startup"},
            {"email": "super2@techstartup.com", "password": "Super123!", "full_name": "Grace SuperUser", "role": auth_schemas.UserRole.SUPER_USER, "tenant_name": "tech_startup"},
            {"email": "user4@techstartup.com", "password": "User123!", "full_name": "Henry User", "role": auth_schemas.UserRole.USER, "tenant_name": "tech_startup"},
            {"email": "user5@techstartup.com", "password": "User123!", "full_name": "Iris User", "role": auth_schemas.UserRole.USER, "tenant_name": "tech_startup"},
            {"email": "user6@techstartup.com", "password": "User123!", "full_name": "Jack User", "role": auth_schemas.UserRole.USER, "tenant_name": "tech_startup"},
        ]
        
        created_users = {"acme_corp": [], "tech_startup": []}
        
        # Create tenant1 users
        for user_data in tenant1_users:
            user_create = auth_schemas.UserCreate(
                email=user_data["email"],
                password=user_data["password"],
                full_name=user_data["full_name"],
                tenant_name=user_data["tenant_name"]
            )
            user = user_management_service.create_user(db, user_create)
            # Update role
            user.role = user_data["role"]
            db.commit()
            db.refresh(user)  # Refresh to ensure object is bound to session
            # Store user data as dict to avoid session issues
            user_dict = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "tenant_name": user.tenant_name
            }
            created_users["acme_corp"].append(user_dict)
            print(f"Created user: {user.email} ({user.role.value}) for acme_corp")
        
        # Create tenant2 users
        for user_data in tenant2_users:
            user_create = auth_schemas.UserCreate(
                email=user_data["email"],
                password=user_data["password"],
                full_name=user_data["full_name"],
                tenant_name=user_data["tenant_name"]
            )
            user = user_management_service.create_user(db, user_create)
            # Update role
            user.role = user_data["role"]
            db.commit()
            db.refresh(user)  # Refresh to ensure object is bound to session
            # Store user data as dict to avoid session issues
            user_dict = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "tenant_name": user.tenant_name
            }
            created_users["tech_startup"].append(user_dict)
            print(f"Created user: {user.email} ({user.role.value}) for tech_startup")
        
        return created_users
        
    finally:
        db.close()

def create_channels(users):
    """Create channels for both tenants."""
    created_channels = {"acme_corp": [], "tech_startup": []}

    tenant_channels_map = {
        "acme_corp": [
            ("sales", "Sales team discussions and strategies"),
            ("HR", "Human Resources discussions and policies"),
        ],
        "tech_startup": [
            ("administration", "Administrative processes and procedures"),
            ("employees", "General employee discussions and announcements"),
        ],
    }

    for tenant, channels_to_create in tenant_channels_map.items():
        db_generator = get_tenant_db(tenant)
        db = next(db_generator)
        try:
            admin_user = next(u for u in users[tenant] if u["role"] == auth_schemas.UserRole.ADMIN)

            for name, description in channels_to_create:
                channel = channel_service.create_channel(
                    db,
                    channel_schemas.ChannelCreate(
                        name=name, description=description, is_private=False
                    ),
                    admin_user["id"],
                )
                channel_dict = {
                    "id": channel.id,
                    "name": channel.name,
                    "description": channel.description,
                    "created_by": channel.created_by,
                }
                created_channels[tenant].append(channel_dict)
                print(f"Created channel: {channel.name} for {tenant}")

            # Add all tenant users to all channels for that tenant
            tenant_channel_ids = [c["id"] for c in created_channels[tenant]]
            for user in users[tenant]:
                if user["id"] != admin_user["id"]:
                    for channel_id in tenant_channel_ids:
                        channel_service.add_member(db, channel_id, user["id"], "member")

        finally:
            db.close()

    return created_channels

def create_conversations(users, channels):
    """Create conversations in each channel."""
    conversation_map = {
        "acme_corp": {
            "sales": SALES_CONVERSATIONS,
            "HR": HR_CONVERSATIONS
        },
        "tech_startup": {
            "administration": ADMINISTRATION_CONVERSATIONS,
            "employees": EMPLOYEES_CONVERSATIONS
        }
    }

    for tenant, tenant_channels in channels.items():
        db_generator = get_tenant_db(tenant)
        db = next(db_generator)
        try:
            tenant_users = users[tenant]
            for channel in tenant_channels:
                channel_name = channel["name"]
                conversations = conversation_map[tenant][channel_name]
                print(f"Creating conversations for {channel_name} in {tenant}")

                for i, (message, ai_response) in enumerate(conversations):
                    user = random.choice(tenant_users)
                    days_ago = random.randint(1, 30)
                    hours_ago = random.randint(0, 23)
                    minutes_ago = random.randint(0, 59)
                    timestamp = datetime.now(timezone.utc) - timedelta(
                        days=days_ago, hours=hours_ago, minutes=minutes_ago
                    )

                    user_message = ChannelMessage(
                        channel_id=channel["id"],
                        user_id=user["id"],
                        message=message,
                        message_type="user",
                        created_at=timestamp,
                    )
                    db.add(user_message)

                    ai_timestamp = timestamp + timedelta(seconds=random.randint(5, 30))
                    ai_message = ChannelMessage(
                        channel_id=channel["id"],
                        user_id=user["id"],
                        message=message,
                        response=ai_response,
                        provider=settings.AI_PROVIDER,
                        message_type="ai",
                        created_at=ai_timestamp,
                        message_length=len(message),
                    )
                    db.add(ai_message)
                    print(f"  - Created conversation {i+1}/10 by {user['full_name']}")
            db.commit()
        finally:
            db.close()

def cleanup_database():
    """Clean up existing data from all databases."""
    print("🧹 Cleaning up existing data...")
    
    # Clean default database
    db = DefaultSessionLocal()
    try:
        # Delete users (this will cascade to other related data)
        db.query(auth_models.User).delete()
        db.commit()
        print("✅ Cleaned default database")
    except Exception as e:
        print(f"⚠️ Error cleaning default database: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Clean tenant databases
    for tenant in ["acme_corp", "tech_startup"]:
        try:
            db_generator = get_tenant_db(tenant)
            db = next(db_generator)
            try:
                # Delete channel messages
                db.query(ChannelMessage).delete()
                # Delete channel members
                db.execute(channel_members.delete())
                # Delete channels
                db.query(Channel).delete()
                # Delete chat messages
                db.query(ChatMessage).delete()
                db.commit()
                print(f"✅ Cleaned {tenant} database")
            except Exception as e:
                print(f"⚠️ Error cleaning {tenant} database: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            print(f"⚠️ Could not access {tenant} database: {e}")

def initialize_database():
    """Initialize database tables."""
    print("🗄️ Initializing database tables...")
    
    # Create all tables in the default database
    Base.metadata.create_all(bind=default_engine)
    print("✅ Default database tables created")

def main():
    """Main seeding function."""
    print("🌱 Starting database seeding...")
    
    # Clean up existing data first
    cleanup_database()
    
    # Initialize database tables
    initialize_database()
    
    print("\n📝 Creating users...")
    users = create_users()
    
    print(f"\n✅ Created {len(users['acme_corp']) + len(users['tech_startup'])} users")
    
    print("\n🏢 Creating channels...")
    channels = create_channels(users)
    
    print(f"\n✅ Created {len(channels['acme_corp']) + len(channels['tech_startup'])} channels")
    
    print("\n💬 Creating conversations...")
    create_conversations(users, channels)
    
    print("\n🎉 Database seeding completed successfully!")
    print("\n📊 Summary:")
    print(f"  • Users: 10 (5 per tenant)")
    print(f"  • Channels: 4 (2 per tenant)")
    print(f"  • Conversations: 40 (10 per channel)")
    print("\n🔐 Login credentials:")
    print("  Acme Corp Admin: admin1@acme.com / Admin123!")
    print("  Acme Corp SuperUser: super1@acme.com / Super123!")
    print("  Tech Startup Admin: admin2@techstartup.com / Admin123!")
    print("  Tech Startup SuperUser: super2@techstartup.com / Super123!")
    print("  Regular users: user[1-6]@[acme.com|techstartup.com] / User123!")

if __name__ == "__main__":
    main()
