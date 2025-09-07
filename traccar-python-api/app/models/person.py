"""
Person model (Physical/Legal Entity)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class PersonType(str, enum.Enum):
    """Person type enumeration."""
    PHYSICAL = "physical"  # Pessoa Física
    LEGAL = "legal"        # Pessoa Jurídica

class Person(Base):
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    person_type = Column(Enum(PersonType), nullable=False, default=PersonType.PHYSICAL)
    
    # Physical person fields
    cpf = Column(String(14), unique=True, index=True)  # Format: 000.000.000-00
    birth_date = Column(DateTime)
    
    # Legal person fields
    cnpj = Column(String(18), unique=True, index=True)  # Format: 00.000.000/0000-00
    company_name = Column(String(255))
    trade_name = Column(String(255))
    
    # Common fields
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(10))
    country = Column(String(50), default="Brazil")
    
    # Status
    active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    groups = relationship("Group", back_populates="person")
    devices = relationship("Device", back_populates="person")

