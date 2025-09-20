#!/usr/bin/env python3
"""
Test script to verify Suntech protocol fixes
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.protocols.suntech import SuntechProtocolHandler
from app.utils.date_utils import parse_date_time

async def test_suntech_message_parsing():
    """Test the Suntech message parsing with the actual message."""
    
    # Message from tcpdump
    message = "ST300STT;907126119;04;1097B;20250908;12:44:33;33e530;-03.843813;-038.615475;000.013;000.00;11;1;26663840;14.07;000000;1;0019;295746;0.0;0;0;00000000000000;0"
    
    print("=== SUNTECH PROTOCOL FIX TEST ===")
    print(f"Raw message: {message}")
    print()
    
    # Create handler
    handler = SuntechProtocolHandler()
    
    # Simulate client info
    client_address = ('204.6.165.254', 56740)
    
    try:
        # Test the parsing
        protocol_message = await handler.parse_message(message.encode('utf-8'), client_address)
        
        if protocol_message:
            print("✅ Message parsed successfully!")
            print(f"   Device ID: {protocol_message.device_id}")
            print(f"   Message Type: {protocol_message.message_type}")
            print(f"   Valid: {protocol_message.valid}")
            print(f"   Timestamp: {protocol_message.timestamp}")
            print()
            
            # Test position creation
            position_data = await handler.create_position(protocol_message)
            
            if position_data:
                print("✅ Position data created successfully!")
                print(f"   Device ID: {position_data['device_id']}")
                print(f"   Latitude: {position_data['latitude']}")
                print(f"   Longitude: {position_data['longitude']}")
                print(f"   Speed: {position_data['speed']}")
                print(f"   Course: {position_data['course']}")
                print(f"   Valid: {position_data['valid']}")
                print(f"   Device Time: {position_data['device_time']}")
                print(f"   Fix Time: {position_data['fix_time']}")
                
                # Check attributes
                attributes = position_data.get('attributes', {})
                print("   Attributes:")
                for key, value in attributes.items():
                    print(f"     {key}: {value}")
                
                # Check ignition status
                ignition = attributes.get('ignition')
                if ignition is not None:
                    ignition_status = "ON" if ignition else "OFF"
                    print(f"   🔥 Ignition: {ignition_status}")
                else:
                    print("   ❌ Ignition status not detected")
                
                # Check power
                power = attributes.get('power')
                if power is not None:
                    print(f"   🔋 Power: {power}V")
                else:
                    print("   ❌ Power not detected")
                    
                # Check satellites
                satellites = attributes.get('satellites')
                if satellites is not None:
                    print(f"   🛰️  Satellites: {satellites}")
                else:
                    print("   ❌ Satellites not detected")
                    
                print()
                print("🎯 EXPECTED STATUS: ONLINE (device should be online when receiving valid position)")
                
            else:
                print("❌ Failed to create position data")
                
        else:
            print("❌ Message parsing failed")
            
    except Exception as e:
        print(f"❌ Error testing protocol: {e}")
        import traceback
        traceback.print_exc()

async def test_device_status_logic():
    """Test device status determination logic."""
    print("\n=== DEVICE STATUS LOGIC TEST ===")
    
    # This would test the status logic, but requires database connection
    # For now, just explain the expected behavior
    print("Device Status Logic:")
    print("1. When a valid position is received:")
    print("   - Registered device: status = 'online', last_update = now()")
    print("   - Unknown device: last_seen = now(), appears in unknown devices list")
    print("2. Device is considered offline after 5 minutes without position")
    print("3. ST300STT should show as 'online' when receiving positions")
    print("4. Ignition status should be extracted from IO field (index 15)")
    print()

if __name__ == "__main__":
    asyncio.run(test_suntech_message_parsing())
    asyncio.run(test_device_status_logic())
