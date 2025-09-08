#!/usr/bin/env python3
"""
Test script to analyze Suntech message format from tcpdump data.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.protocols.suntech import SuntechProtocolHandler
from app.utils.date_utils import parse_date_time

def analyze_suntech_message():
    """Analyze the Suntech message from tcpdump."""
    
    # Message from tcpdump
    message = "ST300STT;907126119;04;1097B;20250908;12:44:33;33e530;-03.843813;-038.615475;000.013;000.00;11;1;26663840;14.07;000000;1;0019;295746;0.0;0;0;00000000000000;0"
    
    print("=== SUNTECH MESSAGE ANALYSIS ===")
    print(f"Raw message: {message}")
    print()
    
    # Split by semicolons
    parts = message.split(';')
    print(f"Total parts: {len(parts)}")
    print()
    
    for i, part in enumerate(parts):
        print(f"Part {i:2d}: '{part}'")
    
    print()
    print("=== PARSING ANALYSIS ===")
    
    # Extract device ID from prefix
    prefix = parts[0]  # ST300STT
    print(f"Prefix: {prefix}")
    
    # Check if it matches the expected pattern
    import re
    device_id_match = re.search(r'ST\w+STT', prefix)
    if device_id_match:
        device_identifier = device_id_match.group()
        print(f"Device ID extracted: {device_identifier}")
    else:
        print("❌ Could not extract device ID from prefix")
        return
    
    # Message type
    message_type = parts[1]  # 907126119
    print(f"Message type: {message_type}")
    
    # Firmware version
    firmware_version = parts[2]  # 04
    print(f"Firmware version: {firmware_version}")
    
    # Protocol type
    protocol_type = parts[3]  # 1097B
    print(f"Protocol type: {protocol_type}")
    
    # Date and time
    date_str = parts[4]  # 20250908
    time_str = parts[5]  # 12:44:33
    print(f"Date: {date_str}")
    print(f"Time: {time_str}")
    
    # Parse datetime
    datetime_str = f"{date_str}{time_str}"
    print(f"DateTime string: {datetime_str}")
    
    try:
        device_time = parse_date_time(datetime_str, "%Y%m%d%H:%M:%S")
        if device_time:
            print(f"✅ Parsed datetime: {device_time}")
        else:
            print("❌ Failed to parse datetime")
    except Exception as e:
        print(f"❌ Error parsing datetime: {e}")
    
    # Cell info (if protocol type 1)
    cell_info = parts[6]  # 33e530
    print(f"Cell info: {cell_info}")
    
    # Coordinates
    try:
        latitude = float(parts[7])  # -03.843813
        longitude = float(parts[8])  # -038.615475
        print(f"✅ Latitude: {latitude}")
        print(f"✅ Longitude: {longitude}")
        
        # Validate coordinates
        if (-90 <= latitude <= 90) and (-180 <= longitude <= 180):
            print("✅ Coordinates are valid")
        else:
            print("❌ Coordinates are invalid")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing coordinates: {e}")
    
    # Speed
    try:
        speed = float(parts[9])  # 000.013
        speed_knots = speed * 0.539957
        print(f"Speed (km/h): {speed}")
        print(f"Speed (knots): {speed_knots}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing speed: {e}")
    
    # Course
    try:
        course = float(parts[10])  # 000.00
        print(f"Course: {course}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing course: {e}")
    
    # GPS validity
    try:
        valid = parts[11] == "1"  # 11
        print(f"GPS valid: {valid}")
    except IndexError:
        print("❌ GPS validity not found")
    
    print()
    print("=== PROTOCOL HANDLER TEST ===")
    
    # Test with protocol handler
    handler = SuntechProtocolHandler()
    
    # Simulate client info
    client_info = {
        'host': '204.6.165.254',
        'port': 56740
    }
    
    # Test message parsing
    try:
        # Convert message to bytes
        message_bytes = message.encode('utf-8')
        
        # Test the parsing
        result = asyncio.run(handler.handle_message(message_bytes, client_info))
        
        if result:
            print(f"✅ Message parsed successfully: {len(result)} positions created")
            for i, pos in enumerate(result):
                print(f"  Position {i+1}: {pos}")
        else:
            print("❌ Message parsing failed")
            
    except Exception as e:
        print(f"❌ Error testing protocol handler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_suntech_message()
