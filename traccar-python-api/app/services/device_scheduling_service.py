"""
Device scheduling service
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.models.device import Device

class DeviceSchedulingService:
    def __init__(self):
        self.schedule_check_interval = 300  # Check every 5 minutes
        
    async def get_device_schedule(self, db: AsyncSession, device_id: int) -> Optional[Dict[str, Any]]:
        """Get device schedule information"""
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            return None
        
        # For now, we'll return basic schedule info
        # In a full implementation, you would integrate with a calendar system
        schedule_info = {
            "device_id": device_id,
            "calendar_id": device.calendar_id,
            "has_schedule": device.calendar_id is not None,
            "schedule_active": False,  # Placeholder
            "next_scheduled_action": None,  # Placeholder
            "schedule_rules": []  # Placeholder
        }
        
        return schedule_info
    
    async def set_device_calendar(self, db: AsyncSession, device_id: int, calendar_id: Optional[int]) -> None:
        """Set calendar for device scheduling"""
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(calendar_id=calendar_id)
        )
        await db.commit()
    
    async def get_scheduled_devices(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get all devices with active schedules"""
        result = await db.execute(
            select(Device).where(Device.calendar_id.isnot(None))
        )
        scheduled_devices = result.scalars().all()
        
        devices_info = []
        for device in scheduled_devices:
            devices_info.append({
                "device_id": device.id,
                "device_name": device.name,
                "unique_id": device.unique_id,
                "calendar_id": device.calendar_id,
                "group_id": device.group_id,
                "status": device.status
            })
        
        return devices_info
    
    async def check_scheduled_actions(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for scheduled actions that need to be executed"""
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Check calendar events
        # 2. Determine which actions need to be executed
        # 3. Execute the actions (e.g., send commands to devices)
        
        current_time = datetime.now()
        scheduled_actions = []
        
        # Placeholder logic
        result = await db.execute(
            select(Device).where(Device.calendar_id.isnot(None))
        )
        devices = result.scalars().all()
        
        for device in devices:
            # Placeholder: check if device needs scheduled action
            # In real implementation, you would check calendar events
            if device.calendar_id:
                scheduled_actions.append({
                    "device_id": device.id,
                    "action_type": "scheduled_check",  # Placeholder
                    "scheduled_time": current_time,
                    "calendar_id": device.calendar_id
                })
        
        return scheduled_actions
    
    async def get_scheduling_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get scheduling statistics"""
        # Count devices with schedules
        result = await db.execute(
            select(Device).where(Device.calendar_id.isnot(None))
        )
        scheduled_devices = len(result.scalars().all())
        
        result = await db.execute(
            select(Device).where(Device.calendar_id.is_(None))
        )
        unscheduled_devices = len(result.scalars().all())
        
        return {
            "scheduled_devices": scheduled_devices,
            "unscheduled_devices": unscheduled_devices,
            "total_devices": scheduled_devices + unscheduled_devices,
            "scheduling_percentage": (scheduled_devices / (scheduled_devices + unscheduled_devices) * 100) if (scheduled_devices + unscheduled_devices) > 0 else 0
        }

# Global instance
device_scheduling_service = DeviceSchedulingService()
