"""
Simple test script for geofence system without authentication
"""
import requests
import json

def test_geofence_endpoints():
    """Test geofence endpoints that don't require authentication"""
    
    base_url = "http://localhost:8000/api"
    
    print("🧪 Testing Geofence System - Simple Tests")
    print("=" * 50)
    
    # Test 1: Get example geometries
    print("\n1️⃣ Testing example geometries endpoint...")
    try:
        response = requests.get(f"{base_url}/geofences/examples/geometries")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Example geometries endpoint working")
            print(f"   Found {len(data['examples'])} geometry types")
            for geom_type in data['examples']:
                print(f"   - {geom_type}")
        else:
            print(f"❌ Example geometries failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Example geometries error: {e}")
    
    # Test 2: Test OpenAPI documentation
    print("\n2️⃣ Testing OpenAPI documentation...")
    try:
        response = requests.get("http://localhost:8000/openapi.json")
        if response.status_code == 200:
            openapi_data = response.json()
            geofence_paths = [path for path in openapi_data.get('paths', {}).keys() if 'geofence' in path]
            print(f"✅ OpenAPI documentation accessible")
            print(f"   Found {len(geofence_paths)} geofence endpoints:")
            for path in geofence_paths:
                print(f"   - {path}")
        else:
            print(f"❌ OpenAPI documentation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAPI documentation error: {e}")
    
    # Test 3: Test health endpoint
    print("\n3️⃣ Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Cache connected: {data.get('cache', {}).get('connected')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    print("\n✅ Simple tests completed!")
    print("\n📝 Note: Most geofence endpoints require authentication.")
    print("   To test authenticated endpoints, you need to:")
    print("   1. Create a user account")
    print("   2. Login to get a token")
    print("   3. Use the token in Authorization header")

if __name__ == "__main__":
    test_geofence_endpoints()
