-- Workstream B: alert workflow + hash-chained audit log. Contract: docs/PLAN.md "Alert workflow".

CREATE TABLE alerts (
    id                  serial PRIMARY KEY,
    segment_ids         text[] NOT NULL,
    level               smallint NOT NULL CHECK (level BETWEEN 2 AND 3),
    proposed_action     text NOT NULL,
    state               text NOT NULL CHECK (state IN ('PROPOSED', 'ESCALATED', 'APPROVED', 'SENT', 'ACKED',
                                                       'REJECTED', 'CANCELLED', 'EXPIRED')),
    mode                text NOT NULL CHECK (mode IN ('live', 'replay')),
    source              text NOT NULL,
    trigger_ts          timestamptz NOT NULL,        -- risk timestamp that caused the proposal (replay time in replay)
    needs_approvals     smallint NOT NULL,
    references_alert_id int REFERENCES alerts(id),   -- lower-level open alert this one upgrades (CAP references)
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    sent_at             timestamptz,
    expires_at          timestamptz,
    thresholds_version  text NOT NULL
);
CREATE INDEX alerts_state_idx ON alerts (state);
CREATE INDEX alerts_segments_idx ON alerts USING gin (segment_ids);

CREATE TABLE alert_approvals (
    alert_id    int  NOT NULL REFERENCES alerts(id),
    officer_id  text NOT NULL REFERENCES officers(id),
    ts          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (alert_id, officer_id)                -- one approval per officer per alert
);

CREATE TABLE audit_log (
    id                  bigserial PRIMARY KEY,
    ts                  timestamptz NOT NULL,
    alert_id            int REFERENCES alerts(id),
    actor               text NOT NULL,                -- officer id or 'system'
    action              text NOT NULL,                -- PROPOSE, APPROVE, SEND, REJECT, ESCALATE, ...
    from_state          text,
    to_state            text,
    reason              text,
    input_snapshot      jsonb NOT NULL,
    thresholds_version  text NOT NULL,
    message_text        text,
    prev_hash           char(64) NOT NULL,
    hash                char(64) NOT NULL UNIQUE      -- sha256(prev_hash + canonical JSON of the row)
);
CREATE INDEX audit_log_alert_idx ON audit_log (alert_id);

CREATE FUNCTION audit_log_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only: % is not allowed', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_append_only();
CREATE TRIGGER audit_log_no_truncate
    BEFORE TRUNCATE ON audit_log
    FOR EACH STATEMENT EXECUTE FUNCTION audit_log_append_only();
