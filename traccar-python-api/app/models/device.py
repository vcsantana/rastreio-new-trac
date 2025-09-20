"""
Device model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    unique_id = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(String(50), default="unknown")  # online, offline, unknown
    protocol = Column(String(50))
    
    # Last known position
    last_update = Column(DateTime(timezone=True))
    position_id = Column(Integer, ForeignKey("positions.id"))
    
    # Device attributes
    phone = Column(String(50))
    model = Column(String(255))
    contact = Column(String(255))
    category = Column(String(50))
    license_plate = Column(String(20))  # Placa do veículo
    disabled = Column(Boolean, default=False)
    
    # Client Management Fields for Central de Monitoramento
    client_code = Column(String(10))  # "#16", "#13", "#14" etc
    client_status = Column(String(20), default="active")  # active, delinquent, test, lost, removal
    priority_level = Column(Integer, default=3)  # 1=critical, 2=high, 3=normal, 4=low, 5=minimal
    fidelity_score = Column(Integer, default=3)  # 1-5 stars for client satisfaction
    last_service_date = Column(DateTime(timezone=True))  # Last service/maintenance
    notes = Column(Text)  # Client notes and observations
    
    # Relationships
    group_id = Column(Integer, ForeignKey("groups.id"))
    person_id = Column(Integer, ForeignKey("persons.id"))  # Associação com pessoa
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional attributes (JSON)
    attributes = Column(Text)
    
    # Accumulators
    total_distance = Column(Float, default=0.0)  # Total distance in meters
    hours = Column(Float, default=0.0)  # Total hours of operation
    
    # Motion Detection
    motion_streak = Column(Boolean, default=False)  # Motion streak status
    motion_state = Column(Boolean, default=False)  # Current motion state
    motion_position_id = Column(Integer, ForeignKey("positions.id"))  # Last motion position
    motion_time = Column(DateTime(timezone=True))  # Last motion time
    motion_distance = Column(Float, default=0.0)  # Motion distance
    
    # Overspeed Detection
    overspeed_state = Column(Boolean, default=False)  # Current overspeed state
    overspeed_time = Column(DateTime(timezone=True))  # Last overspeed time
    overspeed_geofence_id = Column(Integer, ForeignKey("geofences.id"))  # Overspeed geofence
    
    # Expiration and Scheduling
    expiration_time = Column(DateTime(timezone=True))  # Device expiration time
    calendar_id = Column(Integer)  # Associated calendar (no FK constraint for now)
    
    # Relationships
    positions = relationship("Position", back_populates="device", cascade="all, delete-orphan", foreign_keys="Position.device_id")
    events = relationship("Event", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="device", cascade="all, delete-orphan")
    images = relationship("DeviceImage", back_populates="device", cascade="all, delete-orphan")
    last_position = relationship("Position", foreign_keys=[position_id], post_update=True)
    motion_position = relationship("Position", foreign_keys=[motion_position_id], post_update=True)
    group = relationship("Group", back_populates="devices")
    person = relationship("Person", back_populates="devices")
    overspeed_geofence = relationship("Geofence", foreign_keys=[overspeed_geofence_id])
    # calendar = relationship("Calendar", foreign_keys=[calendar_id])  # TODO: Implement Calendar model
    user_permissions = relationship(
        "User", 
        secondary="user_device_permissions", 
        back_populates="device_permissions"
    )
    
    def is_expired(self) -> bool:
        """Check if device has expired"""
        if self.expiration_time:
            from datetime import datetime
            return datetime.now() > self.expiration_time
        return False
    
    def get_total_distance_km(self) -> float:
        """Get total distance in kilometers"""
        return self.total_distance / 1000.0 if self.total_distance else 0.0
    
    def get_hours_formatted(self) -> str:
        """Get formatted hours (hours:minutes)"""
        if not self.hours:
            return "0:00"
        hours = int(self.hours)
        minutes = int((self.hours - hours) * 60)
        return f"{hours}:{minutes:02d}"
    
    def get_communication_status(self) -> dict:
        """Get communication status with color coding"""
        from datetime import datetime, timedelta
        
        if not self.last_update:
            return {"status": "unknown", "color": "gray", "minutes_ago": None}
        
        now = datetime.utcnow()
        if self.last_update.tzinfo is None:
            # If last_update is naive, assume UTC
            last_update_utc = self.last_update
        else:
            last_update_utc = self.last_update.utctimetuple()
            last_update_utc = datetime(*last_update_utc[:6])
        
        minutes_ago = (now - last_update_utc).total_seconds() / 60
        
        if minutes_ago <= 10:
            return {"status": "excellent", "color": "green", "minutes_ago": int(minutes_ago)}
        elif minutes_ago <= 45:
            return {"status": "normal", "color": "yellow", "minutes_ago": int(minutes_ago)}
        elif minutes_ago <= 120:
            return {"status": "attention", "color": "orange", "minutes_ago": int(minutes_ago)}
        else:
            return {"status": "critical", "color": "red", "minutes_ago": int(minutes_ago)}
    
    def is_critical(self) -> bool:
        """Check if device requires critical attention"""
        comm_status = self.get_communication_status()
        return (
            self.client_status in ['delinquent', 'lost'] or
            self.priority_level <= 2 or
            comm_status["color"] == "red" or
            self.disabled
        )
    
    def get_client_type_display(self) -> str:
        """Get display text for client type"""
        type_map = {
            'active': 'Ativo',
            'delinquent': 'Inadimplente',
            'test': 'Teste',
            'lost': 'Perdido',
            'removal': 'Remoção'
        }
        return type_map.get(self.client_status, 'Desconhecido')
    
    def get_priority_display(self) -> str:
        """Get display text for priority level"""
        priority_map = {
            1: 'Crítico',
            2: 'Alto',
            3: 'Normal',
            4: 'Baixo',
            5: 'Mínimo'
        }
        return priority_map.get(self.priority_level, 'Normal')
    
    # Relationships
    group = relationship("Group", back_populates="devices")
    person = relationship("Person", back_populates="devices") 
    positions = relationship("Position", back_populates="device", cascade="all, delete-orphan", foreign_keys="Position.device_id")
    events = relationship("Event", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="device", cascade="all, delete-orphan")
    pois = relationship("POI", back_populates="device", cascade="all, delete-orphan")
