-- SIMULATED holding-area scenario note per crowd row (NULL when no queue is held on the segment).
ALTER TABLE segment_crowd ADD COLUMN IF NOT EXISTS scenario jsonb;
