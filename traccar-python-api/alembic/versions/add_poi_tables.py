"""Add POI tables

Revision ID: add_poi_tables
Revises: add_client_monitoring_fields
Create Date: 2025-09-20 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_poi_tables'
down_revision = 'add_client_monitoring_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pois table
    op.create_table('pois',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('radius', sa.Float(), nullable=True),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pois_device_id'), 'pois', ['device_id'], unique=False)
    op.create_index(op.f('ix_pois_group_id'), 'pois', ['group_id'], unique=False)
    op.create_index(op.f('ix_pois_id'), 'pois', ['id'], unique=False)
    op.create_index(op.f('ix_pois_name'), 'pois', ['name'], unique=False)
    op.create_index(op.f('ix_pois_person_id'), 'pois', ['person_id'], unique=False)

    # Create poi_visits table
    op.create_table('poi_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poi_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('position_entry_id', sa.Integer(), nullable=True),
        sa.Column('position_exit_id', sa.Integer(), nullable=True),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exit_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('entry_latitude', sa.Float(), nullable=True),
        sa.Column('entry_longitude', sa.Float(), nullable=True),
        sa.Column('exit_latitude', sa.Float(), nullable=True),
        sa.Column('exit_longitude', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['poi_id'], ['pois.id'], ),
        sa.ForeignKeyConstraint(['position_entry_id'], ['positions.id'], ),
        sa.ForeignKeyConstraint(['position_exit_id'], ['positions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_poi_visits_device_id'), 'poi_visits', ['device_id'], unique=False)
    op.create_index(op.f('ix_poi_visits_entry_time'), 'poi_visits', ['entry_time'], unique=False)
    op.create_index(op.f('ix_poi_visits_exit_time'), 'poi_visits', ['exit_time'], unique=False)
    op.create_index(op.f('ix_poi_visits_id'), 'poi_visits', ['id'], unique=False)
    op.create_index(op.f('ix_poi_visits_poi_id'), 'poi_visits', ['poi_id'], unique=False)


def downgrade() -> None:
    # Drop poi_visits table
    op.drop_index(op.f('ix_poi_visits_poi_id'), table_name='poi_visits')
    op.drop_index(op.f('ix_poi_visits_id'), table_name='poi_visits')
    op.drop_index(op.f('ix_poi_visits_exit_time'), table_name='poi_visits')
    op.drop_index(op.f('ix_poi_visits_entry_time'), table_name='poi_visits')
    op.drop_index(op.f('ix_poi_visits_device_id'), table_name='poi_visits')
    op.drop_table('poi_visits')
    
    # Drop pois table
    op.drop_index(op.f('ix_pois_person_id'), table_name='pois')
    op.drop_index(op.f('ix_pois_name'), table_name='pois')
    op.drop_index(op.f('ix_pois_id'), table_name='pois')
    op.drop_index(op.f('ix_pois_group_id'), table_name='pois')
    op.drop_index(op.f('ix_pois_device_id'), table_name='pois')
    op.drop_table('pois')
