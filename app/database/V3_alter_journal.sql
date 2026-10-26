ALTER TABLE journal_entries
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE journal_entries
ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';

UPDATE journal_entries SET is_favorite = FALSE WHERE is_favorite IS NULL;
UPDATE journal_entries SET tags = '{}' WHERE tags IS NULL;
