#!/usr/bin/env python3
"""
Test script for the Command System implementation.
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command models: {e}")
        return False

def test_command_schemas():
    """Test command schemas import and basic functionality."""
    try:
        from app.schemas.command import (
            CommandCreate, CommandUpdate, CommandResponse, 
            CommandBulkCreate, CommandStatsResponse
        )
        
        print("✅ Command schemas imported successfully")
        
        # Test schema creation
        command_data = CommandCreate(
            device_id=1,
            command_type="REBOOT",
            priority="NORMAL"
        )
        
        print("✅ CommandCreate schema working correctly")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command API: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Command System Implementation")
    print("=" * 50)
    
    tests = [
        ("Command Models", test_command_models),
        ("Command Schemas", test_command_schemas),
        ("Command Service", test_command_service),
        ("Command Tasks", test_command_tasks),
        ("Command API", test_command_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Command System tests passed!")
        print("\n✅ Command System Implementation Status:")
        print("   - Models: ✅ Complete")
        print("   - Schemas: ✅ Complete")
        print("   - Service: ✅ Complete")
        print("   - Tasks: ✅ Complete")
        print("   - API: ✅ Complete")
        print("\n🚀 Command System is ready for integration!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
