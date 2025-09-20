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
    
    # Dynamic attributes (JSON field for flexibility)
    attributes = Column(Text)  # JSON string for additional attributes
    
    # Relationships
    devices = relationship("Device", back_populates="group")
    person = relationship("Person", back_populates="groups")
    pois = relationship("POI", back_populates="group", cascade="all, delete-orphan")
    user_permissions = relationship(
        "User", 
        secondary="user_group_permissions", 
        back_populates="group_permissions"
    )
    
    # Hierarchical relationships
    parent = relationship("Group", remote_side=[id], back_populates="children")
    children = relationship("Group", back_populates="parent", cascade="all, delete-orphan")
    
    # Methods for dynamic attributes
    def get_string_attribute(self, key: str, default: str = None) -> str:
        """Get string attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            return attrs.get(key, default)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_double_attribute(self, key: str, default: float = None) -> float:
        """Get double/float attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return float(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def get_boolean_attribute(self, key: str, default: bool = False) -> bool:
        """Get boolean attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return bool(value) if value is not None else default
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_integer_attribute(self, key: str, default: int = None) -> int:
        """Get integer attribute from JSON attributes field"""
        if not self.attributes:
            return default
        try:
            import json
            attrs = json.loads(self.attributes)
            value = attrs.get(key, default)
            return int(value) if value is not None else default
        except (json.JSONDecodeError, TypeError, ValueError):
            return default
    
    def set_attribute(self, key: str, value) -> None:
        """Set attribute in JSON attributes field"""
        import json
        if not self.attributes:
            attrs = {}
        else:
            try:
                attrs = json.loads(self.attributes)
            except json.JSONDecodeError:
                attrs = {}
        
        attrs[key] = value
        self.attributes = json.dumps(attrs)
