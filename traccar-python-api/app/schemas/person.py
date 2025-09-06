"""
Person schemas
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class PersonType(str, Enum):
    """Person type enumeration."""
    PHYSICAL = "physical"  # Pessoa Física
    LEGAL = "legal"        # Pessoa Jurídica

class PersonBase(BaseModel):
    name: str
    person_type: PersonType
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Brazil"
    active: Optional[bool] = True

class PersonPhysicalCreate(PersonBase):
    person_type: PersonType = PersonType.PHYSICAL
    cpf: str
    birth_date: Optional[datetime] = None
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove non-numeric characters
        cpf = ''.join(filter(str.isdigit, v))
        if len(cpf) != 11:
            raise ValueError('CPF must have 11 digits')
        return cpf

class PersonLegalCreate(PersonBase):
    person_type: PersonType = PersonType.LEGAL
    cnpj: str
    company_name: str
    trade_name: Optional[str] = None
    
    @validator('cnpj')
    def validate_cnpj(cls, v):
        # Remove non-numeric characters
        cnpj = ''.join(filter(str.isdigit, v))
        if len(cnpj) != 14:
            raise ValueError('CNPJ must have 14 digits')
        return cnpj

class PersonCreate(BaseModel):
    name: str
    person_type: PersonType
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Brazil"
    active: Optional[bool] = True
    
    # Physical person fields
    cpf: Optional[str] = None
    birth_date: Optional[datetime] = None
    
    # Legal person fields
    cnpj: Optional[str] = None
    company_name: Optional[str] = None
    trade_name: Optional[str] = None
    
    @validator('cpf', pre=True)
    def validate_cpf(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('cnpj', pre=True)
    def validate_cnpj(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('birth_date', pre=True)
    def validate_birth_date(cls, v):
        if v == "" or v is None:
            return None
        return v

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    active: Optional[bool] = None
    
    # Physical person fields
    cpf: Optional[str] = None
    birth_date: Optional[datetime] = None
    
    # Legal person fields
    cnpj: Optional[str] = None
    company_name: Optional[str] = None
    trade_name: Optional[str] = None
    
    @validator('cpf', pre=True)
    def validate_cpf(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('cnpj', pre=True)
    def validate_cnpj(cls, v):
        if v == "" or v is None:
            return None
        return v
    
    @validator('birth_date', pre=True)
    def validate_birth_date(cls, v):
        if v == "" or v is None:
            return None
        return v

class PersonResponse(PersonBase):
    id: int
    cpf: Optional[str] = None
    birth_date: Optional[datetime] = None
    cnpj: Optional[str] = None
    company_name: Optional[str] = None
    trade_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    group_count: Optional[int] = 0

    class Config:
        from_attributes = True

