"""
User permission models for device and group access control
"""
from sqlalchemy import Column, Integer, ForeignKey, Table
from app.database import Base

# Association tables for many-to-many relationships
user_device_permissions = Table(
    'user_device_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('device_id', Integer, ForeignKey('devices.id', ondelete='CASCADE'), primary_key=True)
)

user_group_permissions = Table(
    'user_group_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)
)

user_managed_users = Table(
    'user_managed_users',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('managed_user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
)
