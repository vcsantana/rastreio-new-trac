"""
Motion detection service for devices
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.device import Device
from app.models.position import Position

class MotionDetectionService:
    def __init__(self):
        # Motion detection parameters
        self.motion_threshold = 50.0  # meters - minimum distance to consider motion
        self.motion_timeout = 300  # seconds - timeout for motion state
        self.streak_threshold = 3  # minimum consecutive positions for motion streak
        
    async def update_motion_state(self, db: AsyncSession, device_id: int, position: Position) -> None:
        """Update motion state for a device based on new position"""
        # Get device with current motion data
        result = await db.execute(
            select(Device)
            .options(selectinload(Device.motion_position))
            .where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            return
        
        # Calculate motion distance
        motion_distance = 0.0
        motion_detected = False
        
        if device.motion_position_id and device.motion_position:
            # Calculate distance from last motion position
            motion_distance = self._calculate_distance(
                device.motion_position.latitude,
                device.motion_position.longitude,
                position.latitude,
                position.longitude
            )
            
            # Check if motion is detected
            if motion_distance >= self.motion_threshold:
                motion_detected = True
        
        # Update motion state
        current_time = datetime.now()
        
        if motion_detected:
            # Motion detected
            if not device.motion_state:
                # Start new motion
                await self._start_motion(db, device, position, current_time)
            else:
                # Continue existing motion
                await self._continue_motion(db, device, position, current_time, motion_distance)
        else:
            # No motion detected
            if device.motion_state:
                # Check if motion timeout has passed
                if device.motion_time and (current_time - device.motion_time).total_seconds() > self.motion_timeout:
                    await self._stop_motion(db, device, current_time)
                else:
                    # Update motion time but keep state
                    await self._update_motion_time(db, device, current_time)
    
    async def _start_motion(self, db: AsyncSession, device: Device, position: Position, current_time: datetime) -> None:
        """Start new motion detection"""
        await db.execute(
            update(Device)
            .where(Device.id == device.id)
            .values(
                motion_state=True,
                motion_streak=True,
                motion_position_id=position.id,
                motion_time=current_time,
                motion_distance=0.0
            )
        )
        await db.commit()
    
    async def _continue_motion(self, db: AsyncSession, device: Device, position: Position, current_time: datetime, motion_distance: float) -> None:
        """Continue existing motion"""
        new_distance = (device.motion_distance or 0.0) + motion_distance
        
        await db.execute(
            update(Device)
            .where(Device.id == device.id)
            .values(
                motion_position_id=position.id,
                motion_time=current_time,
                motion_distance=new_distance
            )
        )
        await db.commit()
    
    async def _stop_motion(self, db: AsyncSession, device: Device, current_time: datetime) -> None:
        """Stop motion detection"""
        await db.execute(
            update(Device)
            .where(Device.id == device.id)
            .values(
                motion_state=False,
                motion_streak=False,
                motion_time=current_time
            )
        )
        await db.commit()
    
    async def _update_motion_time(self, db: AsyncSession, device: Device, current_time: datetime) -> None:
        """Update motion time without changing state"""
        await db.execute(
            update(Device)
            .where(Device.id == device.id)
            .values(motion_time=current_time)
        )
        await db.commit()
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    async def get_motion_statistics(self, db: AsyncSession, device_id: int, days: int = 7) -> dict:
        """Get motion statistics for a device"""
        # Get device
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if not device:
            return {}
        
        # Calculate statistics
        stats = {
            "device_id": device_id,
            "current_motion_state": device.motion_state or False,
            "current_motion_streak": device.motion_streak or False,
            "total_motion_distance": device.motion_distance or 0.0,
            "last_motion_time": device.motion_time,
            "motion_threshold": self.motion_threshold,
            "motion_timeout": self.motion_timeout
        }
        
        return stats
    
    async def reset_motion_data(self, db: AsyncSession, device_id: int) -> None:
        """Reset motion data for a device"""
        await db.execute(
            update(Device)
            .where(Device.id == device_id)
            .values(
                motion_state=False,
                motion_streak=False,
                motion_position_id=None,
                motion_time=None,
                motion_distance=0.0
            )
        )
        await db.commit()

# Global instance
motion_detection_service = MotionDetectionService()
