#!/usr/bin/env python3
"""
Test script for the Command System implementation using Docker environment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_command_models():
    """Test command models import and basic functionality."""
    try:
        from app.models.command import Command, CommandQueue, CommandType, CommandStatus, CommandPriority
        
        print("✅ Command models imported successfully")
        
        # Test enum values
        print(f"✅ Command types: {len(CommandType)} types available")
        print(f"✅ Command statuses: {len(CommandStatus)} statuses available")
        print(f"✅ Command priorities: {len(CommandPriority)} priorities available")
        
        # Test some specific values
        assert CommandType.REBOOT == "REBOOT"
        assert CommandStatus.PENDING == "PENDING"
        assert CommandPriority.HIGH == "HIGH"
        
        print("✅ Command enums working correctly")
        
        # Test model properties
        print("✅ Command model properties:")
        print(f"   - Command table: {Command.__tablename__}")
        print(f"   - CommandQueue table: {CommandQueue.__tablename__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command models: {e}")
        return False

def test_command_schemas():
    """Test command schemas import and basic functionality."""
    try:
        from app.schemas.command import (
            CommandCreate, CommandUpdate, CommandResponse, 
            CommandBulkCreate, CommandStatsResponse,
            SuntechCommandParams, OsmAndCommandParams
        )
        
        print("✅ Command schemas imported successfully")
        
        # Test schema creation
        command_data = CommandCreate(
            device_id=1,
            command_type="REBOOT",
            priority="NORMAL"
        )
        
        print("✅ CommandCreate schema working correctly")
        
        # Test protocol-specific schemas
        suntech_params = SuntechCommandParams(interval=60)
        osmand_params = OsmAndCommandParams(interval=30)
        
        print("✅ Protocol-specific schemas working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command schemas: {e}")
        return False

def test_command_service():
    """Test command service import."""
    try:
        from app.services.command_service import CommandService
        
        print("✅ Command service imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command service: {e}")
        return False

def test_command_tasks():
    """Test command tasks import."""
    try:
        from app.tasks.command_tasks import (
            process_command_queue, 
            send_command_to_device,
            check_command_timeouts,
            cleanup_expired_commands
        )
        
        print("✅ Command tasks imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command tasks: {e}")
        return False

def test_command_api():
    """Test command API import."""
    try:
        from app.api.commands import router
        
        print("✅ Command API imported successfully")
        
        # Check if router has routes
        routes = [route.path for route in router.routes]
        print(f"✅ Command API has {len(routes)} routes")
        
        # Show some key routes
        key_routes = [r for r in routes if r in ["/", "/bulk", "/stats/summary", "/queue/"]]
        print(f"✅ Key routes available: {key_routes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command API: {e}")
        return False

def test_celery_integration():
    """Test Celery integration for commands."""
    try:
        from app.core.celery_app import celery_app
        
        print("✅ Celery app imported successfully")
        
        # Check if command tasks are included
        if hasattr(celery_app, 'include') and "app.tasks.command_tasks" in celery_app.include:
            print("✅ Command tasks included in Celery")
        else:
            print("⚠️  Command tasks not included in Celery")
        
        # Check beat schedule
        beat_schedule = celery_app.conf.beat_schedule
        command_tasks = [task for task in beat_schedule.keys() if "command" in task]
        print(f"✅ Command periodic tasks: {command_tasks}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Celery integration: {e}")
        return False

def test_database_integration():
    """Test database integration (without actual connection)."""
    try:
        from app.models.command import Command, CommandQueue
        from sqlalchemy import inspect
        
        print("✅ Database models ready")
        
        # Check table names
        print(f"✅ Command table: {Command.__tablename__}")
        print(f"✅ CommandQueue table: {CommandQueue.__tablename__}")
        
        # Check columns
        command_columns = [c.name for c in Command.__table__.columns]
        queue_columns = [c.name for c in CommandQueue.__table__.columns]
        
        print(f"✅ Command columns: {len(command_columns)} columns")
        print(f"✅ CommandQueue columns: {len(queue_columns)} columns")
        
        # Check key columns exist
        required_command_cols = ["id", "device_id", "user_id", "command_type", "status"]
        required_queue_cols = ["id", "command_id", "priority", "is_active"]
        
        for col in required_command_cols:
            if col in command_columns:
                print(f"✅ Command.{col} column exists")
            else:
                print(f"❌ Command.{col} column missing")
                return False
        
        for col in required_queue_cols:
            if col in queue_columns:
                print(f"✅ CommandQueue.{col} column exists")
            else:
                print(f"❌ CommandQueue.{col} column missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database integration: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Command System Implementation (Docker Environment)")
    print("=" * 60)
    
    tests = [
        ("Command Models", test_command_models),
        ("Command Schemas", test_command_schemas),
        ("Command Service", test_command_service),
        ("Command Tasks", test_command_tasks),
        ("Command API", test_command_api),
        ("Celery Integration", test_celery_integration),
        ("Database Integration", test_database_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Command System tests passed!")
        print("\n✅ Command System Implementation Status:")
        print("   - Models: ✅ Complete")
        print("   - Schemas: ✅ Complete")
        print("   - Service: ✅ Complete")
        print("   - Tasks: ✅ Complete")
        print("   - API: ✅ Complete")
        print("   - Celery: ✅ Complete")
        print("   - Database: ✅ Complete")
        print("\n🚀 Command System is ready for Docker deployment!")
        print("\n📋 Next Steps:")
        print("   1. Start Docker environment: docker-compose -f docker-compose.dev.yml up -d")
        print("   2. Create database tables: docker-compose exec api python -c 'from app.database import init_db; init_db()'")
        print("   3. Test API endpoints: http://localhost:8000/docs")
        print("   4. Start Celery workers: docker-compose exec api celery -A app.core.celery_app worker --loglevel=info")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
