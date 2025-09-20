#!/usr/bin/env python3
"""
Test script for Client Monitoring functionality
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import AsyncSessionLocal
from app.models.device import Device
from app.models.person import Person, PersonType
from app.models.group import Group
from sqlalchemy import select

async def test_client_monitoring():
    """Test client monitoring functionality"""
    print("🧪 Testing Client Monitoring System...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Test 1: Check if new fields exist
            print("\n1. Testing new Device fields...")
            result = await db.execute(select(Device).limit(1))
            device = result.scalar_one_or_none()
            
            if device:
                print(f"   ✅ Device found: {device.name}")
                print(f"   - Client Code: {device.client_code}")
                print(f"   - Client Status: {device.client_status}")
                print(f"   - Priority Level: {device.priority_level}")
                print(f"   - Fidelity Score: {device.fidelity_score}")
                print(f"   - Communication Status: {device.get_communication_status()}")
                print(f"   - Is Critical: {device.is_critical()}")
                print(f"   - Client Type Display: {device.get_client_type_display()}")
                print(f"   - Priority Display: {device.get_priority_display()}")
            else:
                print("   ⚠️  No devices found")
            
            # Test 2: Create test data for monitoring
            print("\n2. Creating test data...")
            
            # Create test person
            test_person = Person(
                name="João Silva - Protege Express",
                email="joao@protegeexpress.com",
                phone="(85) 99999-9999",
                type=PersonType.PHYSICAL,
                document="123.456.789-00",
                address="Rua Teste, 123",
                city="Fortaleza",
                state="CE",
                postal_code="60000-000"
            )
            db.add(test_person)
            await db.commit()
            await db.refresh(test_person)
            print(f"   ✅ Test person created: {test_person.name}")
            
            # Create test group
            test_group = Group(
                name="Clientes Protege Express",
                description="Grupo de clientes da Protege Express"
            )
            db.add(test_group)
            await db.commit()
            await db.refresh(test_group)
            print(f"   ✅ Test group created: {test_group.name}")
            
            # Create test devices with different statuses
            test_devices = [
                {
                    "name": "Cliente João Silva",
                    "unique_id": "907126119",
                    "client_code": "#16",
                    "client_status": "delinquent",
                    "priority_level": 1,
                    "fidelity_score": 2,
                    "status": "offline",
                    "last_update": datetime.utcnow() - timedelta(hours=3),
                    "notes": "Cliente inadimplente há 2 meses"
                },
                {
                    "name": "Teste Equipamento",
                    "unique_id": "TEST001",
                    "client_code": "#13",
                    "client_status": "test",
                    "priority_level": 4,
                    "fidelity_score": 5,
                    "status": "online",
                    "last_update": datetime.utcnow() - timedelta(minutes=5),
                    "notes": "Equipamento de teste para novos protocolos"
                },
                {
                    "name": "Perdido - Maria Santos",
                    "unique_id": "LOST001",
                    "client_code": "#14",
                    "client_status": "lost",
                    "priority_level": 1,
                    "fidelity_score": 1,
                    "status": "unknown",
                    "last_update": datetime.utcnow() - timedelta(days=30),
                    "notes": "Equipamento perdido há 1 mês"
                },
                {
                    "name": "Empresa ABC",
                    "unique_id": "EMP001",
                    "client_code": None,
                    "client_status": "active",
                    "priority_level": 3,
                    "fidelity_score": 4,
                    "status": "online",
                    "last_update": datetime.utcnow() - timedelta(minutes=2),
                    "notes": "Cliente ativo, sem problemas"
                }
            ]
            
            created_devices = []
            for device_data in test_devices:
                device = Device(
                    name=device_data["name"],
                    unique_id=device_data["unique_id"],
                    client_code=device_data["client_code"],
                    client_status=device_data["client_status"],
                    priority_level=device_data["priority_level"],
                    fidelity_score=device_data["fidelity_score"],
                    status=device_data["status"],
                    last_update=device_data["last_update"],
                    notes=device_data["notes"],
                    person_id=test_person.id,
                    group_id=test_group.id,
                    category="vehicle"
                )
                db.add(device)
                created_devices.append(device)
            
            await db.commit()
            
            for device in created_devices:
                await db.refresh(device)
                print(f"   ✅ Test device created: {device.name} ({device.client_status})")
            
            # Test 3: Test filtering and priority logic
            print("\n3. Testing filtering and priority logic...")
            
            # Get critical devices
            result = await db.execute(select(Device))
            all_devices = result.scalars().all()
            
            critical_devices = [d for d in all_devices if d.is_critical()]
            print(f"   📊 Total devices: {len(all_devices)}")
            print(f"   🚨 Critical devices: {len(critical_devices)}")
            
            for device in critical_devices:
                comm_status = device.get_communication_status()
                print(f"   - {device.name}: {device.get_client_type_display()} | "
                      f"Priority: {device.get_priority_display()} | "
                      f"Comm: {comm_status['status']} ({comm_status['color']})")
            
            # Test different client statuses
            for status in ['active', 'delinquent', 'test', 'lost']:
                count = len([d for d in all_devices if d.client_status == status])
                print(f"   📈 {status.capitalize()}: {count} devices")
            
            print("\n✅ All tests completed successfully!")
            print("\n🎯 Next steps:")
            print("   1. Run the API server: cd new/traccar-python-api && python -m uvicorn app.main:app --reload")
            print("   2. Run the frontend: cd new/traccar-react-frontend && npm start")
            print("   3. Access: http://localhost:3000/client-monitoring")
            print("   4. Login with: admin@traccar.com / admin123")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(test_client_monitoring())
