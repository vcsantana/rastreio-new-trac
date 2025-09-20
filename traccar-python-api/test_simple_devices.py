#!/usr/bin/env python3
"""
Simple test script to verify devices API
"""
import asyncio
import requests
import json

async def test_devices_api():
    """Test devices API endpoints"""
    print("🧪 Testing Devices API...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Health endpoint working")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            return
        
        # Test 2: Try to access devices without auth (should get 401)
        print("\n2. Testing devices endpoint without auth...")
        response = requests.get(f"{base_url}/api/devices")
        if response.status_code == 401:
            print("   ✅ Devices endpoint properly protected")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
        
        # Test 3: Try client monitoring endpoint
        print("\n3. Testing client monitoring endpoint...")
        response = requests.get(f"{base_url}/api/client-monitoring/summary")
        if response.status_code == 401:
            print("   ✅ Client monitoring endpoint exists and is protected")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
        
        print("\n✅ Basic API tests completed!")
        print("\n🎯 Next steps:")
        print("   1. Access: http://localhost:3000")
        print("   2. Login with: admin@traccar.com / admin123")
        print("   3. Go to: Central de Monitoramento")
        print("   4. Or directly: http://localhost:3000/client-monitoring")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_devices_api())
