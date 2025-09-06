"""
Group model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    disabled = Column(Boolean, default=False)
    
    # Person relationship
    person_id = Column(Integer, ForeignKey("persons.id"))
    
    # Hierarchical relationship - self-referencing foreign key
    parent_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="group")
    person = relationship("Person", back_populates="groups")
    user_permissions = relationship(
        "User", 
        secondary="user_group_permissions", 
        back_populates="group_permissions"
    )
    
    # Hierarchical relationships
    parent = relationship("Group", remote_side=[id], back_populates="children")
    children = relationship("Group", back_populates="parent", cascade="all, delete-orphan")
