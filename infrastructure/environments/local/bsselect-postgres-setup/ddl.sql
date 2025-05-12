-- =================================================================================
-- Instantiate a dummy table which, when modified, will trigger notification events.
-- =================================================================================
CREATE TABLE subjects (
    id               SERIAL PRIMARY KEY,
    name             TEXT NOT NULL,
    age              INTEGER,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================================
-- Add logic to automatically update the updated_at column
-- =================================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
BEFORE UPDATE ON subjects
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =================================================================================
-- Add logic to emit notifications when the subjects table is modified
-- =================================================================================
CREATE OR REPLACE FUNCTION process_subjects_change_capture() RETURNS TRIGGER AS $$

    DECLARE channel varchar := 'subjects';

    BEGIN
        PERFORM pg_notify(channel, text(json_build_object('operation',TG_OP,'timestamp',CURRENT_TIMESTAMP,'data',NEW)));
        RETURN NULL; -- result is ignored since this is an AFTER trigger
    END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER subjects_change_capture
AFTER INSERT OR UPDATE OR DELETE ON subjects
    FOR EACH ROW EXECUTE FUNCTION process_subjects_change_capture();
