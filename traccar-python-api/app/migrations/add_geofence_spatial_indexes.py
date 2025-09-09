"""
Migration: Add spatial indexes for geofences
This migration adds spatial indexes to improve geofence query performance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_geofence_spatial_indexes'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    """Add spatial indexes for geofences"""
    
    # Add indexes for common geofence queries
    op.create_index('idx_geofences_disabled', 'geofences', ['disabled'])
    op.create_index('idx_geofences_type', 'geofences', ['type'])
    op.create_index('idx_geofences_calendar_id', 'geofences', ['calendar_id'])
    op.create_index('idx_geofences_created_at', 'geofences', ['created_at'])
    op.create_index('idx_geofences_updated_at', 'geofences', ['updated_at'])
    
    # Add composite indexes for common query patterns
    op.create_index('idx_geofences_active_type', 'geofences', ['disabled', 'type'])
    op.create_index('idx_geofences_active_calendar', 'geofences', ['disabled', 'calendar_id'])
    
    # Add partial indexes for active geofences only
    op.execute("""
        CREATE INDEX idx_geofences_active_only 
        ON geofences (id, name, type, area) 
        WHERE disabled = false
    """)
    
    # Add index for geofence name searches
    op.create_index('idx_geofences_name_gin', 'geofences', 
                   [sa.text("name gin_trgm_ops")], 
                   postgresql_using='gin')
    
    # Add index for geofence description searches
    op.create_index('idx_geofences_description_gin', 'geofences', 
                   [sa.text("description gin_trgm_ops")], 
                   postgresql_using='gin')
    
    # Add index for attributes JSON queries (if using PostgreSQL)
    op.execute("""
        CREATE INDEX idx_geofences_attributes_gin 
        ON geofences USING gin ((attributes::jsonb))
        WHERE attributes IS NOT NULL
    """)


def downgrade():
    """Remove spatial indexes for geofences"""
    
    # Drop indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_geofences_attributes_gin")
    op.execute("DROP INDEX IF EXISTS idx_geofences_description_gin")
    op.execute("DROP INDEX IF EXISTS idx_geofences_name_gin")
    op.execute("DROP INDEX IF EXISTS idx_geofences_active_only")
    
    op.drop_index('idx_geofences_active_calendar', table_name='geofences')
    op.drop_index('idx_geofences_active_type', table_name='geofences')
    op.drop_index('idx_geofences_updated_at', table_name='geofences')
    op.drop_index('idx_geofences_created_at', table_name='geofences')
    op.drop_index('idx_geofences_calendar_id', table_name='geofences')
    op.drop_index('idx_geofences_type', table_name='geofences')
    op.drop_index('idx_geofences_disabled', table_name='geofences')
