#!/usr/bin/env python3
"""
Script to create a test user and get authentication token
"""
import asyncio
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def create_test_user():
    """Create a test user"""
    print("Creating test user...")
    
    user_data = {
        "name": "Test User",
        "email": "test@traccar.com",
        "password": "test123",
        "admin": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/register", json=user_data)
        if response.status_code == 200:
            print("✅ Test user created successfully")
            return True
        elif response.status_code == 400:
            print("ℹ️  Test user already exists")
            return True
        else:
            print(f"❌ Error creating user: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def login_and_get_token():
    """Login and get authentication token"""
    print("Logging in...")
    
    login_data = {
        "email": "test@traccar.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("✅ Login successful")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_api_endpoints(token):
    """Test API endpoints with authentication"""
    if not token:
        print("❌ No token available")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Testing API endpoints...")
    
    # Test devices endpoint
    try:
        response = requests.get(f"{API_BASE}/api/devices", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Devices endpoint: {len(devices)} devices found")
            for device in devices[:3]:
                print(f"   - {device['name']} ({device['unique_id']}) - {device['status']}")
        else:
            print(f"❌ Devices endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Devices endpoint error: {e}")
    
    # Test positions endpoint
    try:
        response = requests.get(f"{API_BASE}/api/positions/latest", headers=headers)
        if response.status_code == 200:
            positions = response.json()
            print(f"✅ Positions endpoint: {len(positions)} positions found")
            for position in positions[:3]:
                print(f"   - Device {position['device_id']}: {position['latitude']:.4f}, {position['longitude']:.4f}")
        else:
            print(f"❌ Positions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Positions endpoint error: {e}")
    
    # Test device history endpoint
    try:
        response = requests.get(f"{API_BASE}/api/positions/device/12/history", headers=headers)
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Device history endpoint: {len(history)} positions for device 12")
        else:
            print(f"❌ Device history endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Device history endpoint error: {e}")

def main():
    """Main function"""
    print("🔧 Setting up test user and testing API...")
    
    # Create test user
    if not create_test_user():
        return
    
    # Login and get token
    token = login_and_get_token()
    if not token:
        return
    
    # Test API endpoints
    test_api_endpoints(token)
    
    print(f"\n🔑 Authentication token: {token}")
    print("\n💡 You can use this token to test the API manually:")
    print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/devices")

if __name__ == "__main__":
    main()
