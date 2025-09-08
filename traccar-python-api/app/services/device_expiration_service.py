"""
Device expiration service
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.models.device import Device
from app.models.event import Event

class DeviceExpirationService:
    def __init__(self):
        self.expiration_check_interval = 3600  # Check every hour
        self.grace_period = 86400  # 24 hours grace period before disabling
        
    async def check_expired_devices(self, db: AsyncSession) -> List[int]:
        """Check for expired devices and disable them"""
        current_time = datetime.now()
        
        # Find devices that have expired
        result = await db.execute(
            select(Device).where(
                and_(
                    Device.expiration_time.isnot(None),
                    Device.expiration_time <= current_time,
                    Device.disabled == False
                )
            )
        )
        expired_devices = result.scalars().all()
        
        disabled_device_ids = []
        
        for device in expired_devices:
            # Disable the device
            await db.execute(
                update(Device)
                .where(Device.id == device.id)
                .values(disabled=True)
            )
            
            # Create expiration event
            await self._create_expiration_event(db, device)
            
            disabled_device_ids.append(device.id)
        
        if disabled_device_ids:
            await db.commit()
        
        return disabled_device_ids
    
    async def _create_expiration_event(self, db: AsyncSession, device: Device) -> None:
        """Create an event for device expiration"""
        event = Event(
            device_id=device.id,
            type=Event.TYPE_DEVICE_OFFLINE,  # Use offline event type for expiration
            event_time=datetime.now(),
            attributes=f'{{"reason": "expired", "expiration_time": "{device.expiration_time.isoformat()}"}}'
        )
        db.add(event)
    
    async def get_expiring_devices(self, db: AsyncSession, days_ahead: int = 7) -> List[dict]:
        """Get devices that will expire within the specified days"""
        current_time = datetime.now()
        future_time = current_time + timedelta(days=days_ahead)
        
        result = await db.execute(
            select(Device).where(
                and_(
                    Device.expiration_time.isnot(None),
                    Device.expiration_time > current_time,
                    Device.expiration_time <= future_time,
                    Device.disabled == False
                )
            )
        )
        expiring_devices = result.scalars().all()
        
        devices_info = []
        for device in expiring_devices:
            days_until_expiration = (device.expiration_time - current_time).days
            devices_info.append({
                "device_id": device.id,
                "device_name": device.name,
                "unique_id": device.unique_id,
                "expiration_time": device.expiration_time,
                "days_until_expiration": days_until_expiration,
                "group_id": device.group_id
            })
        
        return devices_info
    
    async def set_device_expiration(self, db: AsyncSession, device_id: int, expiration_time: Optional[datetime]) -> None:
        """Set expiration time for a device"""
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(expiration_time=expiration_time)
        )
        await db.commit()
    
    async def extend_device_expiration(self, db: AsyncSession, device_id: int, additional_days: int) -> None:
        """Extend device expiration by specified days"""
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            return
        
        current_expiration = device.expiration_time or datetime.now()
        new_expiration = current_expiration + timedelta(days=additional_days)
        
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(expiration_time=new_expiration)
        )
        await db.commit()
    
    async def get_expiration_statistics(self, db: AsyncSession) -> dict:
        """Get expiration statistics"""
        current_time = datetime.now()
        
        # Count devices by expiration status
        result = await db.execute(
            select(Device).where(
                and_(
                    Device.expiration_time.isnot(None),
                    Device.expiration_time <= current_time
                )
            )
        )
        expired_count = len(result.scalars().all())
        
        result = await db.execute(
            select(Device).where(
                and_(
                    Device.expiration_time.isnot(None),
                    Device.expiration_time > current_time
                )
            )
        )
        active_with_expiration = len(result.scalars().all())
        
        result = await db.execute(
            select(Device).where(Device.expiration_time.is_(None))
        )
        no_expiration = len(result.scalars().all())
        
        return {
            "expired_devices": expired_count,
            "active_with_expiration": active_with_expiration,
            "no_expiration": no_expiration,
            "total_devices": expired_count + active_with_expiration + no_expiration
        }

# Global instance
device_expiration_service = DeviceExpirationService()
