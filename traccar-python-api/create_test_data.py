#!/usr/bin/env python3
"""
Script to create test data for devices and positions
"""
import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.device import Device
from app.models.position import Position
from app.models.user import User
from app.models.group import Group
from sqlalchemy import select

# Test data
TEST_DEVICES = [
    {
        "name": "Carro 01",
        "unique_id": "CAR001",
        "phone": "+5511999999001",
        "model": "Toyota Corolla",
        "contact": "João Silva",
        "category": "car",
        "license_plate": "ABC-1234",
        "protocol": "osmand"
    },
    {
        "name": "Moto 01", 
        "unique_id": "MOT001",
        "phone": "+5511999999002",
        "model": "Honda CB 600",
        "contact": "Maria Santos",
        "category": "motorcycle",
        "license_plate": "XYZ-5678",
        "protocol": "osmand"
    },
    {
        "name": "Caminhão 01",
        "unique_id": "CAM001", 
        "phone": "+5511999999003",
        "model": "Volvo FH",
        "contact": "Pedro Costa",
        "category": "truck",
        "license_plate": "DEF-9012",
        "protocol": "osmand"
    },
    {
        "name": "Van 01",
        "unique_id": "VAN001",
        "phone": "+5511999999004", 
        "model": "Ford Transit",
        "contact": "Ana Oliveira",
        "category": "van",
        "license_plate": "GHI-3456",
        "protocol": "osmand"
    }
]

# São Paulo coordinates for realistic test data
SAO_PAULO_CENTER = (-23.5505, -46.6333)
COORDINATE_RANGE = 0.1  # ~11km radius

async def create_test_devices(db: AsyncSession):
    """Create test devices"""
    print("Creating test devices...")
    
    for device_data in TEST_DEVICES:
        # Check if device already exists
        result = await db.execute(
            select(Device).where(Device.unique_id == device_data["unique_id"])
        )
        existing_device = result.scalar_one_or_none()
        
        if not existing_device:
            device = Device(**device_data)
            db.add(device)
            print(f"  Created device: {device_data['name']} ({device_data['unique_id']})")
        else:
            print(f"  Device already exists: {device_data['name']} ({device_data['unique_id']})")
    
    await db.commit()

async def create_test_positions(db: AsyncSession):
    """Create test positions for devices"""
    print("Creating test positions...")
    
    # Get all devices
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    
    if not devices:
        print("  No devices found. Please create devices first.")
        return
    
    for device in devices:
        # Check if device already has positions
        result = await db.execute(
            select(Position).where(Position.device_id == device.id).limit(1)
        )
        existing_position = result.scalar_one_or_none()
        
        if existing_position:
            print(f"  Device {device.name} already has positions")
            continue
        
        # Create 20-50 positions for each device
        num_positions = random.randint(20, 50)
        print(f"  Creating {num_positions} positions for {device.name}")
        
        # Start from a random point near São Paulo
        start_lat = SAO_PAULO_CENTER[0] + random.uniform(-COORDINATE_RANGE, COORDINATE_RANGE)
        start_lon = SAO_PAULO_CENTER[1] + random.uniform(-COORDINATE_RANGE, COORDINATE_RANGE)
        
        current_lat = start_lat
        current_lon = start_lon
        current_time = datetime.now() - timedelta(hours=24)
        
        for i in range(num_positions):
            # Move slightly in a random direction
            current_lat += random.uniform(-0.01, 0.01)
            current_lon += random.uniform(-0.01, 0.01)
            
            # Ensure we stay within reasonable bounds
            current_lat = max(-90, min(90, current_lat))
            current_lon = max(-180, min(180, current_lon))
            
            # Create position
            position = Position(
                device_id=device.id,
                protocol=device.protocol or "osmand",
                server_time=current_time,
                device_time=current_time,
                fix_time=current_time,
                valid=True,
                latitude=current_lat,
                longitude=current_lon,
                altitude=random.uniform(700, 800),  # São Paulo altitude
                speed=random.uniform(0, 80),  # km/h
                course=random.uniform(0, 360),  # degrees
                address=f"Test Address {i+1}",
                accuracy=random.uniform(5, 15),  # meters
                attributes='{"battery": 85, "signal": 4}'
            )
            
            db.add(position)
            
            # Move time forward by 5-30 minutes
            current_time += timedelta(minutes=random.randint(5, 30))
        
        print(f"    Created {num_positions} positions for {device.name}")

async def main():
    """Main function to create test data"""
    print("Creating test data for Traccar system...")
    
    async for db in get_db():
        try:
            await create_test_devices(db)
            await create_test_positions(db)
            
            # Verify data
            devices_result = await db.execute(select(Device))
            devices = devices_result.scalars().all()
            
            positions_result = await db.execute(select(Position))
            positions = positions_result.scalars().all()
            
            print(f"\n✅ Test data created successfully!")
            print(f"   Devices: {len(devices)}")
            print(f"   Positions: {len(positions)}")
            
            # Show sample data
            print(f"\n📱 Sample devices:")
            for device in devices[:3]:
                print(f"   {device.id}: {device.name} ({device.unique_id}) - {device.category}")
            
            print(f"\n📍 Sample positions:")
            for position in positions[:5]:
                print(f"   Device {position.device_id}: {position.latitude:.4f}, {position.longitude:.4f} - {position.speed:.1f} km/h")
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(main())
