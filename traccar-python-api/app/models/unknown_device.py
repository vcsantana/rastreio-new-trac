"""
Unknown Device model for tracking unregistered devices
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base


class UnknownDevice(Base):
    __tablename__ = "unknown_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), nullable=False, index=True)
    protocol = Column(String(50), nullable=False)
    port = Column(Integer, nullable=False)
    protocol_type = Column(String(10), nullable=False)  # tcp, udp, http
    
    # Connection information
    client_address = Column(String(50))  # IP address
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    connection_count = Column(Integer, default=1)
    
    # Raw data received
    raw_data = Column(Text)  # Last raw message received
    parsed_data = Column(Text)  # JSON of parsed data if available
    
    # Status
    is_registered = Column(Boolean, default=False)  # True if device was later registered
    registered_device_id = Column(Integer)  # Reference to registered device if applicable
    
    # Additional info
    notes = Column(Text)
    
    def __repr__(self):
        return f"<UnknownDevice(id={self.id}, unique_id={self.unique_id}, protocol={self.protocol}, port={self.port})>"
