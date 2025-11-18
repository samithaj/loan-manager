-- ============================================================================
-- User Metadata Column Rename Migration
-- Version: 0007
-- Description: Rename 'metadata' column to 'user_metadata' to avoid conflict
--              with SQLAlchemy's reserved 'metadata' attribute
-- ============================================================================

-- Rename the metadata column to user_metadata
ALTER TABLE users RENAME COLUMN metadata TO user_metadata;

-- Add comment for documentation
COMMENT ON COLUMN users.user_metadata IS 'Additional user metadata stored as JSONB';
