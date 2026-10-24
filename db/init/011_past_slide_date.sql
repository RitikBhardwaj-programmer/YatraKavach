-- A past slide counts only after it happened, so a replay never "knows" the slide it should warn about.
ALTER TABLE segments ADD COLUMN IF NOT EXISTS past_slide_at timestamptz;
