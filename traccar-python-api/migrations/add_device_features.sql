-- Migration: Add device features (accumulators, motion detection, overspeed detection, expiration, scheduling)
-- Date: 2025-01-07
-- Description: Add missing fields to devices table to match Java Traccar functionality

-- Add accumulators fields
ALTER TABLE devices ADD COLUMN IF NOT EXISTS total_distance FLOAT DEFAULT 0.0;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS hours FLOAT DEFAULT 0.0;

-- Add motion detection fields
ALTER TABLE devices ADD COLUMN IF NOT EXISTS motion_streak BOOLEAN DEFAULT FALSE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS motion_state BOOLEAN DEFAULT FALSE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS motion_position_id INTEGER REFERENCES positions(id);
ALTER TABLE devices ADD COLUMN IF NOT EXISTS motion_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS motion_distance FLOAT DEFAULT 0.0;

-- Add overspeed detection fields
ALTER TABLE devices ADD COLUMN IF NOT EXISTS overspeed_state BOOLEAN DEFAULT FALSE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS overspeed_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS overspeed_geofence_id INTEGER REFERENCES geofences(id);

-- Add expiration and scheduling fields
ALTER TABLE devices ADD COLUMN IF NOT EXISTS expiration_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS calendar_id INTEGER; -- Will reference calendars table when implemented

-- Create device_images table
CREATE TABLE IF NOT EXISTS device_images (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_devices_motion_position_id ON devices(motion_position_id);
CREATE INDEX IF NOT EXISTS idx_devices_overspeed_geofence_id ON devices(overspeed_geofence_id);
CREATE INDEX IF NOT EXISTS idx_devices_expiration_time ON devices(expiration_time);
CREATE INDEX IF NOT EXISTS idx_devices_calendar_id ON devices(calendar_id);
CREATE INDEX IF NOT EXISTS idx_device_images_device_id ON device_images(device_id);
CREATE INDEX IF NOT EXISTS idx_device_images_created_at ON device_images(created_at);

-- Add comments for documentation
COMMENT ON COLUMN devices.total_distance IS 'Total distance traveled in meters';
COMMENT ON COLUMN devices.hours IS 'Total hours of operation';
COMMENT ON COLUMN devices.motion_streak IS 'Motion streak status';
COMMENT ON COLUMN devices.motion_state IS 'Current motion state';
COMMENT ON COLUMN devices.motion_position_id IS 'ID of the last motion position';
COMMENT ON COLUMN devices.motion_time IS 'Time of last motion';
COMMENT ON COLUMN devices.motion_distance IS 'Distance of motion';
COMMENT ON COLUMN devices.overspeed_state IS 'Current overspeed state';
COMMENT ON COLUMN devices.overspeed_time IS 'Time of last overspeed event';
COMMENT ON COLUMN devices.overspeed_geofence_id IS 'ID of the geofence where overspeed occurred';
COMMENT ON COLUMN devices.expiration_time IS 'Device expiration time';
COMMENT ON COLUMN devices.calendar_id IS 'Associated calendar ID for scheduling';

COMMENT ON TABLE device_images IS 'Stores device images and media files';
COMMENT ON COLUMN device_images.filename IS 'Generated unique filename for storage';
COMMENT ON COLUMN device_images.original_filename IS 'Original filename from upload';
COMMENT ON COLUMN device_images.content_type IS 'MIME type of the file';
COMMENT ON COLUMN device_images.file_size IS 'File size in bytes';
COMMENT ON COLUMN device_images.file_path IS 'Full path to the stored file';
COMMENT ON COLUMN device_images.description IS 'Optional description of the image';
