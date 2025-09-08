"""
Overspeed detection service for devices
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.device import Device
from app.models.position import Position
from app.models.geofence import Geofence

class OverspeedDetectionService:
    def __init__(self):
        # Default overspeed parameters
        self.default_speed_limit = 80.0  # km/h - default speed limit
        self.overspeed_threshold = 5.0  # km/h - threshold above speed limit
        self.min_speed_for_detection = 10.0  # km/h - minimum speed to consider for detection
        
    async def check_overspeed(self, db: AsyncSession, device_id: int, position: Position) -> bool:
        """Check if device is overspeeding based on current position"""
        # Get device
        result = await db.execute(
            select(Device)
            .options(selectinload(Device.overspeed_geofence))
            .where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            return False
        
        # Check if position has valid speed
        if not position.speed or position.speed < self.min_speed_for_detection:
            return False
        
        # Get speed limit for current location
        speed_limit = await self._get_speed_limit(db, device, position)
        
        if not speed_limit:
            return False
        
        # Check if overspeeding
        speed_kmh = position.speed * 3.6  # Convert m/s to km/h
        is_overspeeding = speed_kmh > (speed_limit + self.overspeed_threshold)
        
        if is_overspeeding:
            await self._handle_overspeed(db, device, position, speed_kmh, speed_limit)
        else:
            await self._clear_overspeed(db, device)
        
        return is_overspeeding
    
    async def _get_speed_limit(self, db: AsyncSession, device: Device, position: Position) -> Optional[float]:
        """Get speed limit for current position"""
        # Check if device has specific geofence for overspeed detection
        if device.overspeed_geofence_id:
            result = await db.execute(
                select(Geofence).where(Geofence.id == device.overspeed_geofence_id)
            )
            geofence = result.scalar_one_or_none()
            
            if geofence and self._is_position_in_geofence(position, geofence):
                # Get speed limit from geofence attributes
                speed_limit = self._get_speed_limit_from_attributes(geofence.attributes)
                if speed_limit:
                    return speed_limit
        
        # Check all geofences for the device's group
        if device.group_id:
            result = await db.execute(
                select(Geofence).where(Geofence.group_id == device.group_id)
            )
            geofences = result.scalars().all()
            
            for geofence in geofences:
                if self._is_position_in_geofence(position, geofence):
                    speed_limit = self._get_speed_limit_from_attributes(geofence.attributes)
                    if speed_limit:
                        return speed_limit
        
        # Return default speed limit
        return self.default_speed_limit
    
    def _is_position_in_geofence(self, position: Position, geofence: Geofence) -> bool:
        """Check if position is within geofence"""
        # This is a simplified implementation
        # In a real implementation, you would use proper geometric calculations
        # For now, we'll assume the geofence has a center point and radius
        
        # Parse geofence geometry (simplified)
        # In real implementation, you would parse the actual geometry
        return True  # Placeholder
    
    def _get_speed_limit_from_attributes(self, attributes: str) -> Optional[float]:
        """Extract speed limit from geofence attributes"""
        if not attributes:
            return None
        
        # Parse JSON attributes and look for speed limit
        # This is a simplified implementation
        # In real implementation, you would parse the JSON properly
        try:
            import json
            attrs = json.loads(attributes)
            return attrs.get('speedLimit', attrs.get('speed_limit'))
        except:
            return None
    
    async def _handle_overspeed(self, db: AsyncSession, device: Device, position: Position, speed: float, speed_limit: float) -> None:
        """Handle overspeed detection"""
        current_time = datetime.now()
        
        # Update device overspeed state
        await db.execute(
            update(Device)
            .where(Device.id == device.id)
            .values(
                overspeed_state=True,
                overspeed_time=current_time
            )
        )
        await db.commit()
        
        # Log overspeed event (you might want to create an event here)
        # This could trigger notifications, alerts, etc.
    
    async def _clear_overspeed(self, db: AsyncSession, device: Device) -> None:
        """Clear overspeed state"""
        if device.overspeed_state:
            await db.execute(
                update(Device)
                .where(Device.id == device.id)
                .values(overspeed_state=False)
            )
            await db.commit()
    
    async def get_overspeed_statistics(self, db: AsyncSession, device_id: int, days: int = 7) -> dict:
        """Get overspeed statistics for a device"""
        # Get device
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            return {}
        
        # Calculate statistics
        stats = {
            "device_id": device_id,
            "current_overspeed_state": device.overspeed_state or False,
            "last_overspeed_time": device.overspeed_time,
            "overspeed_geofence_id": device.overspeed_geofence_id,
            "default_speed_limit": self.default_speed_limit,
            "overspeed_threshold": self.overspeed_threshold
        }
        
        return stats
    
    async def set_overspeed_geofence(self, db: AsyncSession, device_id: int, geofence_id: Optional[int]) -> None:
        """Set overspeed detection geofence for a device"""
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(overspeed_geofence_id=geofence_id)
        )
        await db.commit()
    
    async def reset_overspeed_data(self, db: AsyncSession, device_id: int) -> None:
        """Reset overspeed data for a device"""
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                overspeed_state=False,
                overspeed_time=None,
                overspeed_geofence_id=None
            )
        )
        await db.commit()

# Global instance
overspeed_detection_service = OverspeedDetectionService()
