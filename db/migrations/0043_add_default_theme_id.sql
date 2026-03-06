-- Add default property report theme to accounts
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS default_theme_id INTEGER DEFAULT 4;
