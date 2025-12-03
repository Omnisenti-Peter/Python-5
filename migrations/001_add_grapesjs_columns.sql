-- Migration: Add GrapesJS columns to themes table
-- Date: 2025-12-02
-- Description: Adds support for visual theme builder with GrapesJS

-- Add new columns for GrapesJS data
ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    gjs_data JSONB DEFAULT NULL;

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    gjs_assets JSONB DEFAULT '[]'::jsonb;

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    html_export TEXT DEFAULT NULL;

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    react_export TEXT DEFAULT NULL;

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    theme_type VARCHAR(50) DEFAULT 'manual';

ALTER TABLE themes ADD COLUMN IF NOT EXISTS
    ai_prompt TEXT DEFAULT NULL;

-- Add comment to explain columns
COMMENT ON COLUMN themes.gjs_data IS 'GrapesJS editor data including components and styles';
COMMENT ON COLUMN themes.gjs_assets IS 'Array of uploaded assets (images, files) used in theme';
COMMENT ON COLUMN themes.html_export IS 'Exported HTML code from visual builder';
COMMENT ON COLUMN themes.react_export IS 'Exported React component code';
COMMENT ON COLUMN themes.theme_type IS 'Type of theme: visual, ai_generated, or manual';
COMMENT ON COLUMN themes.ai_prompt IS 'Original AI prompt if theme was AI-generated';

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_themes_group_id ON themes(group_id);
CREATE INDEX IF NOT EXISTS idx_themes_theme_type ON themes(theme_type);
CREATE INDEX IF NOT EXISTS idx_themes_created_by ON themes(created_by);

-- Migrate existing themes to have proper theme_type
UPDATE themes
SET theme_type = 'manual'
WHERE theme_type IS NULL OR theme_type = '';

-- Display migration status
SELECT 'Migration completed successfully' AS status;
