-- Migration: Add User and Group improvements
-- Date: 2025-01-08
-- Description: Add missing fields for User and Group models

-- Add new fields to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS login VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS salt VARCHAR(255),
ADD COLUMN IF NOT EXISTS readonly BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS temporary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS totp_key VARCHAR(255),
ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE;

-- Add index for login field
CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);

-- Add attributes field to groups table
ALTER TABLE groups 
ADD COLUMN IF NOT EXISTS attributes TEXT;

-- Add comments for documentation
COMMENT ON COLUMN users.login IS 'Unique login identifier (different from email)';
COMMENT ON COLUMN users.salt IS 'Salt for password hashing';
COMMENT ON COLUMN users.readonly IS 'Read-only user flag';
COMMENT ON COLUMN users.temporary IS 'Temporary user flag';
COMMENT ON COLUMN users.totp_key IS 'TOTP secret key for 2FA';
COMMENT ON COLUMN users.totp_enabled IS '2FA enabled status';
COMMENT ON COLUMN groups.attributes IS 'JSON string for dynamic attributes';
