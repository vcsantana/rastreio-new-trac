"""
Test script for the improved event system
"""
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.database import DATABASE_URL
from app.models import Event, Device, Position, User
from app.services.event_service import EventService
from app.services.event_handler import EventHandler
from app.services.event_notification_service import EventNotificationService
from app.services.event_report_service import EventReportService


async def test_event_system():
    """Test the improved event system"""
    
    # Setup database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🚀 Testing Improved Event System")
        print("=" * 50)
        
        # Test 1: Event Service with Typed Attributes
        print("\n1. Testing Event Service with Typed Attributes")
        print("-" * 40)
        
        event_service = EventService(db)
        
        # Create a test event with attributes
        test_event = Event(
            type=Event.TYPE_ALARM,
            device_id=1,
            event_time=datetime.utcnow(),
            attributes=json.dumps({
                "alarmType": "panic",
                "speed": 120.5,
                "location": "Highway 101",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        db.add(test_event)
        db.commit()
        db.refresh(test_event)
        
        print(f"✅ Created event: {test_event}")
        
        # Test typed attribute access
        print(f"📊 Alarm type: {test_event.get_string_attribute('alarmType')}")
        print(f"📊 Speed: {test_event.get_double_attribute('speed')}")
        print(f"📊 Location: {test_event.get_string_attribute('location')}")
        print(f"📊 Severity: {test_event.get_string_attribute('severity')}")
        print(f"📊 Has speed attribute: {test_event.has_attribute('speed')}")
        
        # Test attribute modification
        test_event.set_attribute("newAttribute", "test_value")
        print(f"📊 New attribute: {test_event.get_string_attribute('newAttribute')}")
        
        # Test 2: Event Handler (Automatic Events)
        print("\n2. Testing Event Handler (Automatic Events)")
        print("-" * 40)
        
        event_handler = EventHandler(db)
        
        # Get rule statistics
        rule_stats = event_handler.get_rule_stats()
        print(f"📊 Active rules: {len([r for r in rule_stats.values() if r['enabled']])}")
        
        for rule_name, stats in rule_stats.items():
            print(f"   - {rule_name}: {stats['trigger_count']} triggers")
        
        # Test 3: Event Notification Service
        print("\n3. Testing Event Notification Service")
        print("-" * 40)
        
        notification_service = EventNotificationService(db)
        
        # Test notification creation
        await notification_service.send_immediate_notification(
            user_id=1,
            title="Test Notification",
            message="This is a test notification for the improved event system",
            notification_type="info",
            data={"test": True}
        )
        
        print("✅ Test notification sent")
        
        # Test 4: Event Report Service
        print("\n4. Testing Event Report Service")
        print("-" * 40)
        
        report_service = EventReportService(db)
        
        # Generate summary report
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        summary = report_service.generate_events_summary_report(
            user=None,  # In real usage, you'd pass a user object
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"📊 Total events in last 7 days: {summary['summary']['total_events']}")
        print(f"📊 Unique devices: {summary['summary']['unique_devices']}")
        print(f"📊 Event types: {summary['summary']['unique_event_types']}")
        
        # Test CSV export
        csv_content = report_service.export_events_to_csv(
            user=None,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"📊 CSV export length: {len(csv_content)} characters")
        
        # Test 5: Event Trends
        print("\n5. Testing Event Trends")
        print("-" * 40)
        
        trends = report_service.get_event_trends(
            user=None,
            days=30
        )
        
        print(f"📊 Events by hour: {len(trends['events_by_hour'])} hours with data")
        print(f"📊 Events by day of week: {trends['events_by_day_of_week']}")
        
        # Test 6: Performance Comparison
        print("\n6. Performance Comparison")
        print("-" * 40)
        
        # Test attribute access performance
        import time
        
        # Without cache (old method)
        start_time = time.time()
        for _ in range(1000):
            if test_event.attributes:
                attrs = json.loads(test_event.attributes)
                value = attrs.get('speed', 0)
        old_time = time.time() - start_time
        
        # With cache (new method)
        start_time = time.time()
        for _ in range(1000):
            value = test_event.get_double_attribute('speed', 0)
        new_time = time.time() - start_time
        
        print(f"📊 Old method (1000 accesses): {old_time:.4f}s")
        print(f"📊 New method (1000 accesses): {new_time:.4f}s")
        print(f"📊 Performance improvement: {((old_time - new_time) / old_time * 100):.1f}%")
        
        print("\n✅ All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


async def test_event_automation():
    """Test event automation with position data"""
    
    print("\n🤖 Testing Event Automation")
    print("=" * 30)
    
    # Setup database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        event_handler = EventHandler(db)
        
        # Create test position data
        test_position = Position(
            device_id=1,
            latitude=37.7749,
            longitude=-122.4194,
            speed=85.0,  # Above speed limit
            course=180.0,
            device_time=datetime.utcnow(),
            server_time=datetime.utcnow(),
            attributes=json.dumps({
                "ignition": True,
                "fuel": 75.5
            })
        )
        
        db.add(test_position)
        db.commit()
        db.refresh(test_position)
        
        print(f"✅ Created test position: {test_position}")
        
        # Process position and generate events
        generated_events = event_handler.process_position(test_position)
        
        print(f"📊 Generated {len(generated_events)} events:")
        for event in generated_events:
            print(f"   - {event.type} at {event.event_time}")
        
        # Test device status change
        device = db.query(Device).filter(Device.id == 1).first()
        if device:
            status_event = event_handler.process_device_status(device, "offline")
            if status_event:
                print(f"📊 Generated status event: {status_event.type}")
        
    except Exception as e:
        print(f"❌ Error during automation testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    print("🧪 Event System Improvement Tests")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_event_system())
    asyncio.run(test_event_automation())
    
    print("\n🎉 All tests completed!")
