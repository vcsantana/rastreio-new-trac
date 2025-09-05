"""
Event model
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Event(Base):
    """
    Event model representing various tracking events and alarms.
    Migrated from org.traccar.model.Event
    """
    __tablename__ = "events"

    # Event types - matching Java constants
    TYPE_COMMAND_RESULT = "commandResult"
    TYPE_DEVICE_ONLINE = "deviceOnline"
    TYPE_DEVICE_UNKNOWN = "deviceUnknown"
    TYPE_DEVICE_OFFLINE = "deviceOffline"
    TYPE_DEVICE_INACTIVE = "deviceInactive"
    TYPE_QUEUED_COMMAND_SENT = "queuedCommandSent"
    TYPE_DEVICE_MOVING = "deviceMoving"
    TYPE_DEVICE_STOPPED = "deviceStopped"
    TYPE_DEVICE_OVERSPEED = "deviceOverspeed"
    TYPE_DEVICE_FUEL_DROP = "deviceFuelDrop"
    TYPE_DEVICE_FUEL_INCREASE = "deviceFuelIncrease"
    TYPE_GEOFENCE_ENTER = "geofenceEnter"
    TYPE_GEOFENCE_EXIT = "geofenceExit"
    TYPE_ALARM = "alarm"
    TYPE_IGNITION_ON = "ignitionOn"
    TYPE_IGNITION_OFF = "ignitionOff"
    TYPE_MAINTENANCE = "maintenance"
    TYPE_DRIVER_CHANGED = "driverChanged"
    TYPE_MEDIA = "media"

    # All valid event types
    VALID_EVENT_TYPES = {
        TYPE_COMMAND_RESULT,
        TYPE_DEVICE_ONLINE,
        TYPE_DEVICE_UNKNOWN,
        TYPE_DEVICE_OFFLINE,
        TYPE_DEVICE_INACTIVE,
        TYPE_QUEUED_COMMAND_SENT,
        TYPE_DEVICE_MOVING,
        TYPE_DEVICE_STOPPED,
        TYPE_DEVICE_OVERSPEED,
        TYPE_DEVICE_FUEL_DROP,
        TYPE_DEVICE_FUEL_INCREASE,
        TYPE_GEOFENCE_ENTER,
        TYPE_GEOFENCE_EXIT,
        TYPE_ALARM,
        TYPE_IGNITION_ON,
        TYPE_IGNITION_OFF,
        TYPE_MAINTENANCE,
        TYPE_DRIVER_CHANGED,
        TYPE_MEDIA
    }

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core fields
    type = Column(String(128), nullable=False, index=True)
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True, index=True)
    geofence_id = Column(Integer, ForeignKey("geofences.id"), nullable=True, index=True)
    maintenance_id = Column(Integer, nullable=True, index=True)  # Will link to maintenance table later
    
    # Additional event data
    attributes = Column(Text, nullable=True)  # JSON string for additional attributes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="events")
    position = relationship("Position", back_populates="events")
    geofence = relationship("Geofence", back_populates="events")

    def __init__(self, type: str, device_id: int, position_id: Optional[int] = None, **kwargs):
        """
        Initialize Event with type and device_id.
        Matches Java constructors.
        """
        super().__init__(**kwargs)
        self.type = type
        self.device_id = device_id
        self.position_id = position_id
        self.event_time = kwargs.get('event_time', datetime.utcnow())

    @classmethod
    def create_from_position(cls, event_type: str, position, **kwargs):
        """
        Create event from position data.
        Matches Java constructor Event(String type, Position position)
        """
        return cls(
            type=event_type,
            device_id=position.device_id,
            position_id=position.id,
            event_time=position.device_time or datetime.utcnow(),
            **kwargs
        )

    @classmethod
    def create_device_event(cls, event_type: str, device_id: int, **kwargs):
        """
        Create device-only event.
        Matches Java constructor Event(String type, long deviceId)
        """
        return cls(
            type=event_type,
            device_id=device_id,
            event_time=datetime.utcnow(),
            **kwargs
        )

    def is_alarm(self) -> bool:
        """Check if this event is an alarm type"""
        return self.type == self.TYPE_ALARM

    def is_device_status_event(self) -> bool:
        """Check if this is a device status change event"""
        status_events = {
            self.TYPE_DEVICE_ONLINE,
            self.TYPE_DEVICE_OFFLINE,
            self.TYPE_DEVICE_UNKNOWN,
            self.TYPE_DEVICE_INACTIVE
        }
        return self.type in status_events

    def is_geofence_event(self) -> bool:
        """Check if this is a geofence event"""
        return self.type in {self.TYPE_GEOFENCE_ENTER, self.TYPE_GEOFENCE_EXIT}

    def is_motion_event(self) -> bool:
        """Check if this is a motion-related event"""
        return self.type in {self.TYPE_DEVICE_MOVING, self.TYPE_DEVICE_STOPPED}

    def __repr__(self):
        return f"<Event(id={self.id}, type='{self.type}', device_id={self.device_id}, time={self.event_time})>"
