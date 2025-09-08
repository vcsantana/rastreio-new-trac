"""
Device image serving endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.database import get_db
from app.models.user import User
from app.models.device import Device
from app.models.device_image import DeviceImage
from app.api.groups import get_user_accessible_groups
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/{device_id}/images/{image_id}")
async def get_device_image(
    device_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Serve device image file"""
    # Get image record
    result = await db.execute(
        select(DeviceImage).where(
            DeviceImage.id == image_id,
            DeviceImage.device_id == device_id
        )
    )
    device_image = result.scalar_one_or_none()
    
    if not device_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Check device permissions for non-admin users
    if not current_user.is_admin:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        
        if device:
            accessible_groups = await get_user_accessible_groups(db, current_user.id, current_user.is_admin)
            if device.group_id and device.group_id not in accessible_groups:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this image"
                )
    
    # Check if file exists
    file_path = Path(device_image.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )
    
    # Return file
    return FileResponse(
        path=str(file_path),
        media_type=device_image.content_type,
        filename=device_image.original_filename
    )
