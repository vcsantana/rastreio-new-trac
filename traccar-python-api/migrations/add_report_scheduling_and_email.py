"""
Migration: Add report scheduling and email functionality
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_report_scheduling_email'
down_revision = 'previous_revision'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Add report scheduling and email functionality."""
    
    # Create calendars table
    op.create_table('calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendars_id'), 'calendars', ['id'], unique=False)
    op.create_index(op.f('ix_calendars_user_id'), 'calendars', ['user_id'], unique=False)
    
    # Add new columns to reports table
    op.add_column('reports', sa.Column('attributes', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('is_scheduled', sa.Boolean(), nullable=True, default=False))
    op.add_column('reports', sa.Column('schedule_cron', sa.String(length=100), nullable=True))
    op.add_column('reports', sa.Column('calendar_id', sa.Integer(), nullable=True))
    op.add_column('reports', sa.Column('next_run', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('last_run', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('email_recipients', sa.JSON(), nullable=True))
    
    # Add indexes for new columns
    op.create_index(op.f('ix_reports_is_scheduled'), 'reports', ['is_scheduled'], unique=False)
    op.create_index(op.f('ix_reports_next_run'), 'reports', ['next_run'], unique=False)
    
    # Add foreign key constraint for calendar_id
    op.create_foreign_key('fk_reports_calendar_id', 'reports', 'calendars', ['calendar_id'], ['id'])
    
    # Update existing reports to have default values
    op.execute("UPDATE reports SET is_scheduled = false WHERE is_scheduled IS NULL")
    op.execute("UPDATE reports SET attributes = '{}' WHERE attributes IS NULL")
    op.execute("UPDATE reports SET email_recipients = '[]' WHERE email_recipients IS NULL")


def downgrade():
    """Remove report scheduling and email functionality."""
    
    # Remove foreign key constraint
    op.drop_constraint('fk_reports_calendar_id', 'reports', type_='foreignkey')
    
    # Remove indexes
    op.drop_index(op.f('ix_reports_next_run'), table_name='reports')
    op.drop_index(op.f('ix_reports_is_scheduled'), table_name='reports')
    
    # Remove columns from reports table
    op.drop_column('reports', 'email_recipients')
    op.drop_column('reports', 'last_run')
    op.drop_column('reports', 'next_run')
    op.drop_column('reports', 'calendar_id')
    op.drop_column('reports', 'schedule_cron')
    op.drop_column('reports', 'is_scheduled')
    op.drop_column('reports', 'attributes')
    
    # Drop calendars table
    op.drop_index(op.f('ix_calendars_user_id'), table_name='calendars')
    op.drop_index(op.f('ix_calendars_id'), table_name='calendars')
    op.drop_table('calendars')
