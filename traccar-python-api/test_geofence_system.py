"""
Test script for the complete geofence system
Tests all components: detection, cache, events, and API endpoints
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.geofence import Geofence
from app.models.device import Device
from app.models.position import Position
from app.models.user import User
from app.services.geofence_detection_service import GeofenceDetectionService
from app.services.geofence_cache_service import geofence_cache_service
from app.services.geofence_event_service import GeofenceEventService


async def test_geofence_system():
    """Test the complete geofence system"""
    
    print("🧪 Testing Geofence System Implementation")
    print("=" * 50)
    
    # Create database session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Test 1: Create test geofences
        print("\n1️⃣ Creating test geofences...")
        await test_create_geofences(db)
        
        # Test 2: Test geofence detection
        print("\n2️⃣ Testing geofence detection...")
        await test_geofence_detection(db)
        
        # Test 3: Test cache system
        print("\n3️⃣ Testing cache system...")
        await test_cache_system(db)
        
        # Test 4: Test event system
        print("\n4️⃣ Testing event system...")
        await test_event_system(db)
        
        # Test 5: Test typed attributes
        print("\n5️⃣ Testing typed attributes...")
        await test_typed_attributes(db)
        
        print("\n✅ All geofence system tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def test_create_geofences(db):
    """Test creating geofences with different geometries"""
    
    # Create a polygon geofence (São Paulo area)
    polygon_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [-46.6333, -23.5505],  # Southwest corner
            [-46.6300, -23.5505],  # Southeast corner
            [-46.6300, -23.5480],  # Northeast corner
            [-46.6333, -23.5480],  # Northwest corner
            [-46.6333, -23.5505]   # Close polygon
        ]]
    }
    
    polygon_geofence = Geofence(
        name="São Paulo Downtown",
        description="Downtown São Paulo area",
        geometry=json.dumps(polygon_geometry),
        type="polygon",
        disabled=False,
        attributes=json.dumps({
            "bufferDistance": 50.0,
            "alertEnabled": True,
            "maxSpeed": 60.0
        })
    )
    
    # Create a circle geofence (Rio de Janeiro)
    circle_geometry = {
        "type": "Circle",
        "coordinates": [-43.1729, -22.9068, 2000]  # [lon, lat, radius_meters]
    }
    
    circle_geofence = Geofence(
        name="Rio de Janeiro Center",
        description="Central Rio de Janeiro area",
        geometry=json.dumps(circle_geometry),
        type="circle",
        disabled=False,
        attributes=json.dumps({
            "alertEnabled": True,
            "maxSpeed": 50.0
        })
    )
    
    # Create a polyline geofence (highway)
    polyline_geometry = {
        "type": "LineString",
        "coordinates": [
            [-46.6333, -23.5505],  # Start point
            [-46.6300, -23.5480],  # Middle point
            [-46.6250, -23.5450]   # End point
        ]
    }
    
    polyline_geofence = Geofence(
        name="Highway Route",
        description="Main highway route",
        geometry=json.dumps(polyline_geometry),
        type="polyline",
        disabled=False,
        attributes=json.dumps({
            "bufferDistance": 100.0,
            "alertEnabled": True
        })
    )
    
    db.add(polygon_geofence)
    db.add(circle_geofence)
    db.add(polyline_geofence)
    db.commit()
    
    print(f"✅ Created {len([polygon_geofence, circle_geofence, polyline_geofence])} test geofences")
    return [polygon_geofence, circle_geofence, polyline_geofence]


async def test_geofence_detection(db):
    """Test geofence detection service"""
    
    detection_service = GeofenceDetectionService(db)
    
    # Test point inside polygon
    inside_point = detection_service.get_geofences_for_point(-46.6315, -23.5492)
    print(f"✅ Point inside polygon detected {len(inside_point)} geofences")
    
    # Test point outside all geofences
    outside_point = detection_service.get_geofences_for_point(-46.6000, -23.5000)
    print(f"✅ Point outside all geofences detected {len(outside_point)} geofences")
    
    # Test point inside circle
    circle_point = detection_service.get_geofences_for_point(-43.1729, -22.9068)
    print(f"✅ Point inside circle detected {len(circle_point)} geofences")


async def test_cache_system(db):
    """Test geofence cache system"""
    
    # Test getting active geofences from cache
    active_geofences = await geofence_cache_service.get_active_geofences(db)
    print(f"✅ Retrieved {len(active_geofences)} active geofences from cache")
    
    # Test getting geofences by type
    polygon_geofences = await geofence_cache_service.get_geofences_by_type("polygon", db)
    print(f"✅ Retrieved {len(polygon_geofences)} polygon geofences from cache")
    
    # Test cache stats
    cache_stats = await geofence_cache_service.get_cache_stats()
    print(f"✅ Cache stats: {cache_stats}")
    
    # Test cache invalidation
    await geofence_cache_service.invalidate_geofence_cache()
    print("✅ Cache invalidated successfully")


async def test_event_system(db):
    """Test geofence event system"""
    
    event_service = GeofenceEventService(db)
    
    # Create a test device and position
    test_device = Device(
        name="Test Device",
        unique_id="TEST001",
        protocol="test",
        disabled=False
    )
    
    test_position = Position(
        device_id=1,  # Will be updated after device is saved
        protocol="test",
        device_time=datetime.utcnow(),
        valid=True,
        latitude=-23.5492,
        longitude=-46.6315,
        speed=50.0,
        course=90.0
    )
    
    db.add(test_device)
    db.commit()
    db.refresh(test_device)
    
    test_position.device_id = test_device.id
    db.add(test_position)
    db.commit()
    db.refresh(test_position)
    
    # Get a geofence for testing
    geofence = db.query(Geofence).filter(Geofence.type == "polygon").first()
    
    if geofence:
        # Test creating geofence events
        enter_event = await event_service.create_geofence_event(
            test_position, test_device, geofence, "geofenceEnter"
        )
        
        if enter_event:
            print(f"✅ Created geofence enter event: {enter_event.id}")
        
        # Test getting geofence events
        events = await event_service.get_geofence_events(
            device_id=test_device.id,
            limit=10
        )
        print(f"✅ Retrieved {len(events)} geofence events")
        
        # Test event statistics
        stats = await event_service.get_geofence_event_stats(
            device_id=test_device.id,
            days=30
        )
        print(f"✅ Event stats: {stats.get('total_events', 0)} total events")


async def test_typed_attributes(db):
    """Test typed attribute methods"""
    
    geofence = db.query(Geofence).first()
    
    if geofence:
        # Test string attribute
        buffer_distance = geofence.get_double_attribute("bufferDistance", 50.0)
        print(f"✅ Buffer distance: {buffer_distance}")
        
        # Test boolean attribute
        alert_enabled = geofence.get_boolean_attribute("alertEnabled", False)
        print(f"✅ Alert enabled: {alert_enabled}")
        
        # Test setting attributes
        geofence.set_attribute("testAttribute", "testValue")
        test_value = geofence.get_string_attribute("testAttribute")
        print(f"✅ Test attribute: {test_value}")
        
        # Test removing attributes
        removed = geofence.remove_attribute("testAttribute")
        print(f"✅ Attribute removed: {removed}")
        
        # Test getting all attributes
        all_attrs = geofence.get_all_attributes()
        print(f"✅ All attributes: {len(all_attrs)} items")


async def test_api_endpoints():
    """Test API endpoints (would require running server)"""
    
    print("\n6️⃣ API Endpoints Test (requires running server)")
    print("To test API endpoints, start the server and run:")
    print("curl -X GET 'http://localhost:8000/geofences/'")
    print("curl -X POST 'http://localhost:8000/geofences/test' -H 'Content-Type: application/json' -d '{\"latitude\": -23.5492, \"longitude\": -46.6315}'")
    print("curl -X GET 'http://localhost:8000/geofences/events/'")
    print("curl -X GET 'http://localhost:8000/geofences/cache/stats'")


if __name__ == "__main__":
    asyncio.run(test_geofence_system())
