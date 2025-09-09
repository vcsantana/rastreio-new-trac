-- Migration: Add command enhancements (attributes, description, text_channel)
-- Date: 2025-01-07
-- Description: Add dynamic attributes, description, and text channel support to commands

-- Add new columns to commands table
ALTER TABLE commands 
ADD COLUMN attributes JSON,
ADD COLUMN description VARCHAR(512),
ADD COLUMN text_channel BOOLEAN DEFAULT FALSE NOT NULL;

-- Create command_templates table
CREATE TABLE command_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    command_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'NORMAL' NOT NULL,
    parameters JSON,
    attributes JSON,
    text_channel BOOLEAN DEFAULT FALSE NOT NULL,
    max_retries INTEGER DEFAULT 3 NOT NULL,
    is_public BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    usage_count INTEGER DEFAULT 0 NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for command_templates
CREATE INDEX idx_command_templates_name ON command_templates(name);
CREATE INDEX idx_command_templates_command_type ON command_templates(command_type);
CREATE INDEX idx_command_templates_user_id ON command_templates(user_id);
CREATE INDEX idx_command_templates_is_active ON command_templates(is_active);
CREATE INDEX idx_command_templates_is_public ON command_templates(is_public);

-- Create scheduled_commands table
CREATE TABLE scheduled_commands (
    id SERIAL PRIMARY KEY,
    command_id INTEGER NOT NULL UNIQUE,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_executed BOOLEAN DEFAULT FALSE NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE,
    repeat_interval INTEGER,
    repeat_count INTEGER DEFAULT 0 NOT NULL,
    max_repeats INTEGER,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    FOREIGN KEY (command_id) REFERENCES commands(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for scheduled_commands
CREATE INDEX idx_scheduled_commands_command_id ON scheduled_commands(command_id);
CREATE INDEX idx_scheduled_commands_scheduled_at ON scheduled_commands(scheduled_at);
CREATE INDEX idx_scheduled_commands_is_active ON scheduled_commands(is_active);
CREATE INDEX idx_scheduled_commands_is_executed ON scheduled_commands(is_executed);
CREATE INDEX idx_scheduled_commands_user_id ON scheduled_commands(user_id);

-- Add comments for documentation
COMMENT ON COLUMN commands.attributes IS 'Dynamic attributes for extensibility';
COMMENT ON COLUMN commands.description IS 'Command description';
COMMENT ON COLUMN commands.text_channel IS 'Use SMS channel for command';

COMMENT ON TABLE command_templates IS 'Reusable command templates for quick command creation';
COMMENT ON COLUMN command_templates.name IS 'Template name';
COMMENT ON COLUMN command_templates.description IS 'Template description';
COMMENT ON COLUMN command_templates.command_type IS 'Type of command';
COMMENT ON COLUMN command_templates.priority IS 'Command priority';
COMMENT ON COLUMN command_templates.parameters IS 'Command-specific parameters';
COMMENT ON COLUMN command_templates.attributes IS 'Dynamic attributes';
COMMENT ON COLUMN command_templates.text_channel IS 'Use SMS channel for command';
COMMENT ON COLUMN command_templates.max_retries IS 'Maximum number of retries';
COMMENT ON COLUMN command_templates.is_public IS 'Make template public for all users';
COMMENT ON COLUMN command_templates.is_active IS 'Template active status';
COMMENT ON COLUMN command_templates.usage_count IS 'Number of times template was used';

COMMENT ON TABLE scheduled_commands IS 'Scheduled commands for delayed execution';
COMMENT ON COLUMN scheduled_commands.command_id IS 'Command to schedule';
COMMENT ON COLUMN scheduled_commands.scheduled_at IS 'When to execute the command';
COMMENT ON COLUMN scheduled_commands.is_executed IS 'Whether command has been executed';
COMMENT ON COLUMN scheduled_commands.executed_at IS 'When command was executed';
COMMENT ON COLUMN scheduled_commands.repeat_interval IS 'Repeat interval in seconds';
COMMENT ON COLUMN scheduled_commands.repeat_count IS 'Number of times executed';
COMMENT ON COLUMN scheduled_commands.max_repeats IS 'Maximum number of repeats';
COMMENT ON COLUMN scheduled_commands.is_active IS 'Scheduled command active status';
