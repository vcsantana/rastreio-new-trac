#!/usr/bin/env python3
"""
Test script for new device features
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000/api"

async def test_device_features():
    """Test the new device features"""
    async with aiohttp.ClientSession() as session:
        # First, login to get token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status}")
                return
            
            token_data = await resp.json()
            token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        print("✅ Login successful")
        
        # Test 1: Get devices with new fields
        print("\n🔍 Testing device list with new fields...")
        async with session.get(f"{BASE_URL}/devices/", headers=headers) as resp:
            if resp.status == 200:
                devices = await resp.json()
                if devices:
                    device = devices[0]
                    print(f"✅ Device found: {device['name']}")
                    print(f"   - Total distance: {device.get('total_distance', 'N/A')}m")
                    print(f"   - Hours: {device.get('hours', 'N/A')}")
                    print(f"   - Motion state: {device.get('motion_state', 'N/A')}")
                    print(f"   - Overspeed state: {device.get('overspeed_state', 'N/A')}")
                    print(f"   - Expiration time: {device.get('expiration_time', 'N/A')}")
                    print(f"   - Calendar ID: {device.get('calendar_id', 'N/A')}")
                    device_id = device['id']
                else:
                    print("❌ No devices found")
                    return
            else:
                print(f"❌ Failed to get devices: {resp.status}")
                return
        
        # Test 2: Update accumulators
        print(f"\n📊 Testing accumulators update for device {device_id}...")
        accumulators_data = {
            "total_distance": 15000.0,  # 15km
            "hours": 120.5  # 120.5 hours
        }
        
        async with session.put(f"{BASE_URL}/devices/{device_id}/accumulators", 
                              json=accumulators_data, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ Accumulators updated successfully")
                print(f"   - Total distance: {result['total_distance']}m ({result['total_distance_km']}km)")
                print(f"   - Hours: {result['hours']} ({result['hours_formatted']})")
            else:
                print(f"❌ Failed to update accumulators: {resp.status}")
        
        # Test 3: Set device expiration
        print(f"\n⏰ Testing device expiration for device {device_id}...")
        expiration_time = datetime.now() + timedelta(days=30)
        expiration_data = {
            "expiration_time": expiration_time.isoformat()
        }
        
        async with session.put(f"{BASE_URL}/devices/{device_id}/expiration", 
                              json=expiration_data, headers=headers) as resp:
            if resp.status == 200:
                print(f"✅ Device expiration set successfully")
                print(f"   - Expiration time: {expiration_time}")
            else:
                print(f"❌ Failed to set expiration: {resp.status}")
        
        # Test 4: Get expiration info
        print(f"\n📅 Testing expiration info for device {device_id}...")
        async with session.get(f"{BASE_URL}/devices/{device_id}/expiration", headers=headers) as resp:
            if resp.status == 200:
                expiration_info = await resp.json()
                print(f"✅ Expiration info retrieved")
                print(f"   - Is expired: {expiration_info['is_expired']}")
                print(f"   - Days until expiration: {expiration_info.get('days_until_expiration', 'N/A')}")
            else:
                print(f"❌ Failed to get expiration info: {resp.status}")
        
        # Test 5: Set device schedule
        print(f"\n📅 Testing device scheduling for device {device_id}...")
        schedule_data = {
            "calendar_id": 1
        }
        
        async with session.put(f"{BASE_URL}/devices/{device_id}/schedule", 
                              json=schedule_data, headers=headers) as resp:
            if resp.status == 200:
                print(f"✅ Device schedule set successfully")
                print(f"   - Calendar ID: {schedule_data['calendar_id']}")
            else:
                print(f"❌ Failed to set schedule: {resp.status}")
        
        # Test 6: Get motion statistics
        print(f"\n🏃 Testing motion statistics for device {device_id}...")
        async with session.get(f"{BASE_URL}/devices/{device_id}/motion/statistics", headers=headers) as resp:
            if resp.status == 200:
                motion_stats = await resp.json()
                print(f"✅ Motion statistics retrieved")
                print(f"   - Current motion state: {motion_stats.get('current_motion_state', 'N/A')}")
                print(f"   - Motion threshold: {motion_stats.get('motion_threshold', 'N/A')}m")
            else:
                print(f"❌ Failed to get motion statistics: {resp.status}")
        
        # Test 7: Get overspeed statistics
        print(f"\n🚗 Testing overspeed statistics for device {device_id}...")
        async with session.get(f"{BASE_URL}/devices/{device_id}/overspeed/statistics", headers=headers) as resp:
            if resp.status == 200:
                overspeed_stats = await resp.json()
                print(f"✅ Overspeed statistics retrieved")
                print(f"   - Current overspeed state: {overspeed_stats.get('current_overspeed_state', 'N/A')}")
                print(f"   - Default speed limit: {overspeed_stats.get('default_speed_limit', 'N/A')} km/h")
            else:
                print(f"❌ Failed to get overspeed statistics: {resp.status}")
        
        # Test 8: Get scheduling statistics
        print(f"\n📊 Testing scheduling statistics...")
        async with session.get(f"{BASE_URL}/devices/scheduling/statistics", headers=headers) as resp:
            if resp.status == 200:
                scheduling_stats = await resp.json()
                print(f"✅ Scheduling statistics retrieved")
                print(f"   - Scheduled devices: {scheduling_stats.get('scheduled_devices', 'N/A')}")
                print(f"   - Unscheduled devices: {scheduling_stats.get('unscheduled_devices', 'N/A')}")
            else:
                print(f"❌ Failed to get scheduling statistics: {resp.status}")
        
        print(f"\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_device_features())
