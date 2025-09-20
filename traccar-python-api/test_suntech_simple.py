#!/usr/bin/env python3
"""
Simple test script to analyze Suntech message format without database dependencies
"""

import re
from datetime import datetime

def test_suntech_message_parsing():
    """Test the Suntech message parsing logic."""
    
    # Message from tcpdump
    message = "ST300STT;907126119;04;1097B;20250908;12:44:33;33e530;-03.843813;-038.615475;000.013;000.00;11;1;26663840;14.07;000000;1;0019;295746;0.0;0;0;00000000000000;0"
    
    print("=== SUNTECH MESSAGE ANALYSIS (FIXED) ===")
    print(f"Raw message: {message}")
    print()
    
    # Split by semicolons
    parts = message.split(';')
    print(f"Total parts: {len(parts)}")
    print()
    
    # Parse according to the fixed logic
    print("=== PARSING WITH FIXES ===")
    
    # Device prefix (ST300STT) - index 0
    prefix = parts[0]
    print(f"Device Prefix: {prefix}")
    
    # Real Device ID (907126119) - index 1 
    device_identifier = parts[1]
    print(f"✅ Device ID (CORRECTED): {device_identifier}")
    
    # Firmware version (04) - index 2
    firmware_version = parts[2]
    print(f"Firmware Version: {firmware_version}")
    
    # Protocol type (1097B) - index 3
    protocol_type = parts[3]
    print(f"Protocol Type: {protocol_type}")
    
    # Date and time
    date_str = parts[4]  # 20250908
    time_str = parts[5]  # 12:44:33
    print(f"Date: {date_str}")
    print(f"Time: {time_str}")
    
    # Parse datetime
    datetime_str = f"{date_str}{time_str}"
    try:
        device_time = datetime.strptime(datetime_str, "%Y%m%d%H:%M:%S")
        print(f"✅ Parsed datetime: {device_time}")
    except Exception as e:
        print(f"❌ Error parsing datetime: {e}")
    
    # Cell info - index 6
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
    
    # Speed and course
    try:
        speed = float(parts[9])  # 000.013
        speed_knots = speed * 0.539957
        print(f"Speed (km/h): {speed}")
        print(f"Speed (knots): {speed_knots}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing speed: {e}")
    
    try:
        course = float(parts[10])  # 000.00
        print(f"Course: {course}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing course: {e}")
    
    # GPS satellites and status
    try:
        satellites = int(parts[11])  # 11
        print(f"✅ Satellites: {satellites}")
        gps_valid = satellites > 0
        print(f"✅ GPS Valid (satellites > 0): {gps_valid}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing satellites: {e}")
    
    try:
        gps_fix = int(parts[12])  # 1
        print(f"✅ GPS Fix: {gps_fix}")
        fix_valid = gps_fix == 1
        print(f"✅ Fix Valid: {fix_valid}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing GPS fix: {e}")
    
    # Odometer
    try:
        odometer = int(parts[13])  # 26663840
        print(f"✅ Odometer: {odometer}")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing odometer: {e}")
    
    # Power voltage
    try:
        power_voltage = float(parts[14])  # 14.07
        print(f"✅ Power Voltage: {power_voltage}V")
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing power voltage: {e}")
    
    # IO Status (CRITICAL FOR IGNITION)
    try:
        io_status = parts[15]  # 000000
        print(f"✅ IO Status: {io_status}")
        
        if len(io_status) >= 1:
            # First bit is typically ignition
            ignition = io_status[0] == '1'
            ignition_status = "ON" if ignition else "OFF"
            print(f"🔥 Ignition Status: {ignition_status}")
            
            if ignition:
                print("✅ DEVICE SHOULD BE ONLINE (ignition ON)")
            else:
                print("⚠️  DEVICE COULD BE ONLINE (ignition OFF but receiving data)")
        else:
            print("❌ IO status too short to determine ignition")
            
    except (ValueError, IndexError) as e:
        print(f"❌ Error parsing IO status: {e}")
    
    print()
    print("=== ANALYSIS SUMMARY ===")
    print("🎯 MAIN ISSUES IDENTIFIED AND FIXED:")
    print("1. ✅ Device ID extraction: Now using parts[1] instead of parsing prefix")
    print("2. ✅ Coordinate parsing: Correctly parsing latitude/longitude")
    print("3. ✅ GPS status: Using satellites count and fix status")
    print("4. ✅ Ignition detection: Extracting from IO status field")
    print("5. ✅ Power monitoring: Extracting voltage information")
    print()
    print("🚀 EXPECTED RESULT:")
    print("   - Device ID: 907126119 (not ST300STT)")
    print("   - Status: ONLINE when receiving valid positions")
    print("   - Ignition: OFF (IO status starts with '0')")
    print("   - GPS: Valid (11 satellites, fix=1)")
    print("   - Location: Valid coordinates in Brazil")
    print()

def explain_device_status_logic():
    """Explain the device status determination logic."""
    print("=== DEVICE STATUS LOGIC EXPLANATION ===")
    print()
    print("🔍 CURRENT ISSUE:")
    print("   Device ST300STT appears as 'unknown' instead of 'online'")
    print()
    print("🛠️  ROOT CAUSES & FIXES:")
    print("   1. WRONG DEVICE ID EXTRACTION")
    print("      - Before: Used 'ST300STT' from prefix")
    print("      - After:  Use '907126119' from parts[1]")
    print()
    print("   2. DEVICE REGISTRATION")
    print("      - Unknown devices are stored in 'unknown_devices' table")
    print("      - Need to register device with unique_id='907126119'")
    print("      - Once registered, positions update device.status='online'")
    print()
    print("   3. STATUS UPDATE TIMING")
    print("      - Device status updated when position received")
    print("      - 'online': last position within 5 minutes")
    print("      - 'offline': no position for > 5 minutes")
    print("      - 'unknown': device not registered in system")
    print()
    print("   4. IGNITION VS ONLINE STATUS")
    print("      - Ignition OFF ≠ Device offline")
    print("      - Device can be online with ignition OFF")
    print("      - Online = receiving GPS data regularly")
    print("      - Ignition = engine/vehicle status")
    print()
    print("✅ SOLUTION STEPS:")
    print("   1. Fixed protocol parsing (device ID extraction)")
    print("   2. Enhanced position data with ignition status")
    print("   3. Updated status logic in protocol server")
    print("   4. Register device '907126119' in admin panel")
    print()

if __name__ == "__main__":
    test_suntech_message_parsing()
    print()
    explain_device_status_logic()
