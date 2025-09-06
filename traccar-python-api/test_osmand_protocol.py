#!/usr/bin/env python3
"""
Test script for OsmAnd protocol implementation
"""
import asyncio
import json
import aiohttp
from datetime import datetime

# Test data for OsmAnd protocol
TEST_QUERY_DATA = {
    "id": "test-device-001",
    "lat": "-23.5505",
    "lon": "-46.6333",
    "timestamp": str(int(datetime.now().timestamp())),
    "speed": "15.5",
    "course": "180.0",
    "altitude": "760.0",
    "accuracy": "5.0",
    "battery": "85.0",
    "valid": "1",
    "motion": "1"
}

TEST_JSON_DATA = {
    "device_id": "test-device-002",
    "location": {
        "timestamp": datetime.now().isoformat(),
        "coords": {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "speed": 15.5,
            "heading": 180.0,
            "altitude": 760.0,
            "accuracy": 5.0
        },
        "event": "location_update",
        "is_moving": True
    },
    "battery": 85.0,
    "network": {
        "wifi": "TestWiFi",
        "cell": "TestCell"
    }
}

async def test_osmand_protocol():
    """Test OsmAnd protocol with both query string and JSON formats"""
    
    base_url = "http://localhost:5055"
    
    print("🧪 Testing OsmAnd Protocol Implementation")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Query String Format (GET)
        print("\n📡 Test 1: Query String Format (GET)")
        print("-" * 30)
        
        query_params = "&".join([f"{k}={v}" for k, v in TEST_QUERY_DATA.items()])
        url = f"{base_url}/?{query_params}"
        
        try:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
                print(f"✅ Query string test {'PASSED' if response.status == 200 else 'FAILED'}")
        except Exception as e:
            print(f"❌ Query string test FAILED: {e}")
        
        # Test 2: Query String Format (POST)
        print("\n📡 Test 2: Query String Format (POST)")
        print("-" * 30)
        
        try:
            async with session.post(base_url, data=TEST_QUERY_DATA) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
                print(f"✅ POST query test {'PASSED' if response.status == 200 else 'FAILED'}")
        except Exception as e:
            print(f"❌ POST query test FAILED: {e}")
        
        # Test 3: JSON Format (POST)
        print("\n📡 Test 3: JSON Format (POST)")
        print("-" * 30)
        
        headers = {"Content-Type": "application/json"}
        
        try:
            async with session.post(base_url, json=TEST_JSON_DATA, headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
                print(f"✅ JSON test {'PASSED' if response.status == 200 else 'FAILED'}")
        except Exception as e:
            print(f"❌ JSON test FAILED: {e}")
        
        # Test 4: Health Check
        print("\n📡 Test 4: Health Check")
        print("-" * 30)
        
        try:
            async with session.get(f"{base_url}/health") as response:
                print(f"Status: {response.status}")
                health_data = await response.json()
                print(f"Response: {json.dumps(health_data, indent=2)}")
                print(f"✅ Health check {'PASSED' if response.status == 200 else 'FAILED'}")
        except Exception as e:
            print(f"❌ Health check FAILED: {e}")
        
        # Test 5: Invalid Data
        print("\n📡 Test 5: Invalid Data")
        print("-" * 30)
        
        invalid_data = {"invalid": "data"}
        
        try:
            async with session.post(base_url, json=invalid_data, headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
                print(f"✅ Invalid data test {'PASSED' if response.status == 400 else 'FAILED'}")
        except Exception as e:
            print(f"❌ Invalid data test FAILED: {e}")

def print_test_data():
    """Print test data for reference"""
    print("\n📋 Test Data Reference")
    print("=" * 50)
    
    print("\n🔗 Query String Format:")
    query_params = "&".join([f"{k}={v}" for k, v in TEST_QUERY_DATA.items()])
    print(f"GET /?{query_params}")
    
    print("\n📄 JSON Format:")
    print(json.dumps(TEST_JSON_DATA, indent=2))

if __name__ == "__main__":
    print("🚀 OsmAnd Protocol Test Suite")
    print("Make sure the server is running on port 5055")
    print("Start with: uvicorn app.main:app --reload")
    
    print_test_data()
    
    try:
        asyncio.run(test_osmand_protocol())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
    
    print("\n✅ Test suite completed!")


