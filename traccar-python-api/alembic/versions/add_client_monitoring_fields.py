"""Add client monitoring fields

Revision ID: add_client_monitoring_fields
Revises: 
Create Date: 2025-09-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_client_monitoring_fields'
down_revision = None  # Update this with the latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add client monitoring fields to devices table"""
    # Add new columns to devices table
    op.add_column('devices', sa.Column('client_code', sa.String(length=10), nullable=True))
    op.add_column('devices', sa.Column('client_status', sa.String(length=20), nullable=True, default='active'))
    op.add_column('devices', sa.Column('priority_level', sa.Integer(), nullable=True, default=3))
    op.add_column('devices', sa.Column('fidelity_score', sa.Integer(), nullable=True, default=3))
    op.add_column('devices', sa.Column('last_service_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('devices', sa.Column('notes', sa.Text(), nullable=True))
    
    # Create indexes for better query performance
    op.create_index('idx_devices_client_status', 'devices', ['client_status'])
    op.create_index('idx_devices_priority_level', 'devices', ['priority_level'])
    op.create_index('idx_devices_client_code', 'devices', ['client_code'])


def downgrade() -> None:
    """Remove client monitoring fields from devices table"""
    # Drop indexes
    op.drop_index('idx_devices_client_code', table_name='devices')
    op.drop_index('idx_devices_priority_level', table_name='devices')
    op.drop_index('idx_devices_client_status', table_name='devices')
    
    # Drop columns
    op.drop_column('devices', 'notes')
    op.drop_column('devices', 'last_service_date')
    op.drop_column('devices', 'fidelity_score')
    op.drop_column('devices', 'priority_level')
    op.drop_column('devices', 'client_status')
    op.drop_column('devices', 'client_code')
