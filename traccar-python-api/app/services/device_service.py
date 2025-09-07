"""
Device service with Redis caching
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import structlog
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.cache import (
    cache_manager, 
    cached, 
    device_cache_key, 
    invalidate_device_cache
)

logger = structlog.get_logger(__name__)


class DeviceService:
    """Device service with caching"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @cached(key_func=lambda self, device_id: device_cache_key(device_id), expire=600)
    async def get_device_by_id(self, device_id: int) -> Optional[Device]:
        """Get device by ID with caching"""
        try:
            result = await self.db.execute(
                select(Device)
                .options(selectinload(Device.group))
                .options(selectinload(Device.person))
                .where(Device.id == device_id)
            )
            device = result.scalar_one_or_none()
            
            if device:
                logger.debug("Device retrieved from database", device_id=device_id)
            else:
                logger.warning("Device not found", device_id=device_id)
            
            return device
            
        except Exception as e:
            logger.error("Error getting device by ID", device_id=device_id, error=str(e))
            return None
    
    @cached(key_func=lambda self, unique_id: f"device:unique:{unique_id}", expire=600)
    async def get_device_by_unique_id(self, unique_id: str) -> Optional[Device]:
        """Get device by unique ID with caching"""
        try:
            result = await self.db.execute(
                select(Device)
                .options(selectinload(Device.group))
                .options(selectinload(Device.person))
                .where(Device.unique_id == unique_id)
            )
            device = result.scalar_one_or_none()
            
            if device:
                logger.debug("Device retrieved by unique ID", unique_id=unique_id)
            else:
                logger.warning("Device not found by unique ID", unique_id=unique_id)
            
            return device
            
        except Exception as e:
            logger.error("Error getting device by unique ID", unique_id=unique_id, error=str(e))
            return None
    
    @cached(key_func=lambda self, user_id: f"user_devices:{user_id}", expire=300)
    async def get_user_devices(self, user_id: int) -> List[Device]:
        """Get all devices for a user with caching"""
        try:
            # This would need to be implemented based on your user-device relationship
            # For now, returning all devices (you might want to filter by user permissions)
            result = await self.db.execute(
                select(Device)
                .options(selectinload(Device.group))
                .options(selectinload(Device.person))
                .order_by(Device.name)
            )
            devices = result.scalars().all()
            
            logger.debug("User devices retrieved", user_id=user_id, count=len(devices))
            return list(devices)
            
        except Exception as e:
            logger.error("Error getting user devices", user_id=user_id, error=str(e))
            return []
    
    @cached(key_func=lambda self: "devices:all", expire=300)
    async def get_all_devices(self) -> List[Device]:
        """Get all devices with caching"""
        try:
            result = await self.db.execute(
                select(Device)
                .options(selectinload(Device.group))
                .options(selectinload(Device.person))
                .order_by(Device.name)
            )
            devices = result.scalars().all()
            
            logger.debug("All devices retrieved", count=len(devices))
            return list(devices)
            
        except Exception as e:
            logger.error("Error getting all devices", error=str(e))
            return []
    
    async def create_device(self, device_data: DeviceCreate) -> Optional[Device]:
        """Create a new device and invalidate cache"""
        try:
            device = Device(**device_data.dict())
            self.db.add(device)
            await self.db.commit()
            await self.db.refresh(device)
            
            # Invalidate relevant caches
            await self._invalidate_device_caches()
            
            logger.info("Device created", device_id=device.id, name=device.name)
            return device
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating device", error=str(e))
            return None
    
    async def update_device(self, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
        """Update device and invalidate cache"""
        try:
            # Get existing device
            device = await self.get_device_by_id(device_id)
            if not device:
                return None
            
            # Update fields
            update_data = device_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(device, field, value)
            
            await self.db.commit()
            await self.db.refresh(device)
            
            # Invalidate device-specific cache
            await invalidate_device_cache(device_id)
            await self._invalidate_device_caches()
            
            logger.info("Device updated", device_id=device_id)
            return device
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating device", device_id=device_id, error=str(e))
            return None
    
    async def delete_device(self, device_id: int) -> bool:
        """Delete device and invalidate cache"""
        try:
            # Check if device exists
            device = await self.get_device_by_id(device_id)
            if not device:
                return False
            
            # Delete device
            await self.db.execute(delete(Device).where(Device.id == device_id))
            await self.db.commit()
            
            # Invalidate caches
            await invalidate_device_cache(device_id)
            await self._invalidate_device_caches()
            
            logger.info("Device deleted", device_id=device_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error deleting device", device_id=device_id, error=str(e))
            return False
    
    async def toggle_device_status(self, device_id: int) -> Optional[Device]:
        """Toggle device disabled status and invalidate cache"""
        try:
            device = await self.get_device_by_id(device_id)
            if not device:
                return None
            
            device.disabled = not device.disabled
            await self.db.commit()
            await self.db.refresh(device)
            
            # Invalidate caches
            await invalidate_device_cache(device_id)
            await self._invalidate_device_caches()
            
            logger.info("Device status toggled", device_id=device_id, disabled=device.disabled)
            return device
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Error toggling device status", device_id=device_id, error=str(e))
            return None
    
    async def get_device_stats(self) -> Dict[str, Any]:
        """Get device statistics with caching"""
        cache_key = "device_stats"
        cached_stats = await cache_manager.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        try:
            # Get total devices
            total_result = await self.db.execute(select(Device))
            total_devices = len(total_result.scalars().all())
            
            # Get online devices (you might want to implement this based on last_update)
            online_result = await self.db.execute(
                select(Device).where(Device.disabled == False)
            )
            online_devices = len(online_result.scalars().all())
            
            # Get disabled devices
            disabled_result = await self.db.execute(
                select(Device).where(Device.disabled == True)
            )
            disabled_devices = len(disabled_result.scalars().all())
            
            stats = {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "disabled_devices": disabled_devices,
                "offline_devices": total_devices - online_devices
            }
            
            # Cache for 5 minutes
            await cache_manager.set(cache_key, stats, expire=300)
            
            logger.debug("Device stats calculated", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Error getting device stats", error=str(e))
            return {
                "total_devices": 0,
                "online_devices": 0,
                "disabled_devices": 0,
                "offline_devices": 0
            }
    
    async def _invalidate_device_caches(self):
        """Invalidate device-related caches"""
        patterns = [
            "devices:all",
            "user_devices:*",
            "device_stats"
        ]
        
        for pattern in patterns:
            await cache_manager.clear_pattern(pattern)
        
        logger.debug("Device caches invalidated")


# Service functions for backward compatibility
async def get_device_by_id(db: AsyncSession, device_id: int) -> Optional[Device]:
    """Get device by ID"""
    service = DeviceService(db)
    return await service.get_device_by_id(device_id)


async def get_device_by_unique_id(db: AsyncSession, unique_id: str) -> Optional[Device]:
    """Get device by unique ID"""
    service = DeviceService(db)
    return await service.get_device_by_unique_id(unique_id)


async def get_user_devices(db: AsyncSession, user_id: int) -> List[Device]:
    """Get user devices"""
    service = DeviceService(db)
    return await service.get_user_devices(user_id)


async def get_all_devices(db: AsyncSession) -> List[Device]:
    """Get all devices"""
    service = DeviceService(db)
    return await service.get_all_devices()


async def create_device(db: AsyncSession, device_data: DeviceCreate) -> Optional[Device]:
    """Create device"""
    service = DeviceService(db)
    return await service.create_device(device_data)


async def update_device(db: AsyncSession, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
    """Update device"""
    service = DeviceService(db)
    return await service.update_device(device_id, device_data)


async def delete_device(db: AsyncSession, device_id: int) -> bool:
    """Delete device"""
    service = DeviceService(db)
    return await service.delete_device(device_id)


async def toggle_device_status(db: AsyncSession, device_id: int) -> Optional[Device]:
    """Toggle device status"""
    service = DeviceService(db)
    return await service.toggle_device_status(device_id)


async def get_device_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get device statistics"""
    service = DeviceService(db)
    return await service.get_device_stats()
