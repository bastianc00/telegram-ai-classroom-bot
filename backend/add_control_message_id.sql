-- Migration: Add control_message_id to sync_sessions table
-- Date: 2025-11-29
-- Description: Adds control_message_id field to persist Telegram control keyboard message IDs

ALTER TABLE sync_sessions
ADD COLUMN IF NOT EXISTS control_message_id VARCHAR(100);

-- Add comment to document the column
COMMENT ON COLUMN sync_sessions.control_message_id IS 'ID del mensaje de control en Telegram (para evitar duplicados entre workers)';
