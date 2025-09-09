"""
Notification model
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Notification(Base):
    """
    Notification model for storing user notifications
    """
    __tablename__ = "notifications"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User who receives the notification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Notification type and status
    type = Column(String(50), default="info")  # info, warning, error, success
    read = Column(Boolean, default=False)
    
    # Additional data
    data = Column(Text, nullable=True)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}')>"
