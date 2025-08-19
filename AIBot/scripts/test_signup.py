#!/usr/bin/env python3
"""
Test script to verify signup and login functionality.
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_signup_flow(base_url: str = "http://localhost:8000"):
    """Test the complete signup and login flow."""
    
    print("🧪 Testing Signup Flow")
    print("=" * 50)
    print(f"📍 Target URL: {base_url}")
    print(f"⏰ Started at: {datetime.now()}")
    print("-" * 50)
    
    session = requests.Session()
    
    # Test 1: Get available tenants
    print("1️⃣ Testing: Get Available Tenants")
    try:
        response = session.get(f"{base_url}/api/v1/auth/tenants")
        if response.status_code == 200:
            tenants = response.json()["tenants"]
            print(f"   ✅ Found {len(tenants)} available tenants")
            if tenants:
                selected_tenant = tenants[0]["id"]
                print(f"   📋 Will use tenant: {tenants[0]['name']} ({selected_tenant})")
            else:
                print("   ❌ No tenants available")
                return False
        else:
            print(f"   ❌ Failed to get tenants: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error getting tenants: {e}")
        return False
    
    # Test 2: Test signup
    print("\n2️⃣ Testing: User Signup")
    test_user = {
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "tenant_name": selected_tenant
    }
    
    try:
        response = session.post(
            f"{base_url}/api/v1/auth/signup",
            headers={"Content-Type": "application/json"},
            json=test_user
        )
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"   ✅ User created successfully: {user_data.get('email')}")
            print(f"   📋 User ID: {user_data.get('id')}")
        else:
            print(f"   ❌ Signup failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error during signup: {e}")
        return False
    
    # Test 3: Test login
    print("\n3️⃣ Testing: User Login")
    try:
        login_data = {
            "username": test_user["email"],  # OAuth2 uses 'username' field
            "password": test_user["password"]
        }
        
        response = session.post(
            f"{base_url}/api/v1/auth/login/access-token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=login_data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   ✅ Login successful")
            print(f"   🔑 Token type: {token_data.get('token_type')}")
            print(f"   👤 User ID: {token_data.get('user_id')}")
            access_token = token_data.get("access_token")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error during login: {e}")
        return False
    
    # Test 4: Test authenticated request
    print("\n4️⃣ Testing: Authenticated Request")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = session.get(f"{base_url}/api/v1/channels", headers=headers)
        
        if response.status_code == 200:
            channels = response.json()
            print(f"   ✅ Authenticated request successful")
            print(f"   📢 Found {len(channels)} channels")
        else:
            print(f"   ❌ Authenticated request failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error during authenticated request: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Signup flow is working correctly.")
    return True


def main():
    """Main function to run the tests."""
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    try:
        success = test_signup_flow(base_url)
        if success:
            print("\n✅ Signup flow test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Signup flow test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
