ALTER TABLE journal_entries
ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE;

ALTER TABLE journal_entries
ADD COLUMN tags TEXT[] DEFAULT '{}';