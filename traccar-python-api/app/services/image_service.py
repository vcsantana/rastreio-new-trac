"""
Image upload and management service
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.device_image import DeviceImage
from app.models.device import Device

class ImageService:
    def __init__(self):
        # Base directory for storing images
        self.base_dir = Path("media/device_images")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Allowed image types and max size
        self.allowed_types = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg", 
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg"
        }
        self.max_size = 500 * 1024  # 500KB
        
    def validate_image(self, file: UploadFile) -> None:
        """Validate uploaded image file"""
        # Check file type
        if file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_types.keys())}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {self.max_size // 1024}KB"
            )
    
    def generate_filename(self, original_filename: str, content_type: str) -> str:
        """Generate unique filename for storage"""
        extension = self.allowed_types[content_type]
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{extension}"
    
    def get_device_image_dir(self, device_id: int) -> Path:
        """Get directory path for device images"""
        device_dir = self.base_dir / str(device_id)
        device_dir.mkdir(parents=True, exist_ok=True)
        return device_dir
    
    async def save_image(self, file: UploadFile, device_id: int, description: Optional[str] = None) -> DeviceImage:
        """Save uploaded image to filesystem and database"""
        # Validate image
        self.validate_image(file)
        
        # Generate filename and path
        filename = self.generate_filename(file.filename, file.content_type)
        device_dir = self.get_device_image_dir(device_id)
        file_path = device_dir / filename
        
        # Save file to filesystem
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Create database record
        device_image = DeviceImage(
            device_id=device_id,
            filename=filename,
            original_filename=file.filename,
            content_type=file.content_type,
            file_size=file_size,
            file_path=str(file_path),
            description=description
        )
        
        return device_image
    
    def get_image_url(self, device_image: DeviceImage) -> str:
        """Generate URL for accessing the image"""
        return f"/api/devices/{device_image.device_id}/images/{device_image.id}"
    
    async def get_device_images(self, db: AsyncSession, device_id: int) -> List[DeviceImage]:
        """Get all images for a device"""
        result = await db.execute(
            select(DeviceImage).where(DeviceImage.device_id == device_id)
        )
        return result.scalars().all()
    
    async def get_device_image(self, db: AsyncSession, device_id: int, image_id: int) -> Optional[DeviceImage]:
        """Get specific device image"""
        result = await db.execute(
            select(DeviceImage).where(
                DeviceImage.id == image_id,
                DeviceImage.device_id == device_id
            )
        )
        return result.scalar_one_or_none()
    
    async def delete_image(self, db: AsyncSession, device_image: DeviceImage) -> None:
        """Delete image from filesystem and database"""
        # Delete file from filesystem
        file_path = Path(device_image.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        await db.delete(device_image)
        await db.commit()
    
    def cleanup_orphaned_images(self) -> None:
        """Clean up images that don't have corresponding database records"""
        # This would be called by a background task
        # Implementation would scan filesystem and remove orphaned files
        pass

# Global instance
image_service = ImageService()
