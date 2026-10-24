"""DB side of the alert workflow: load/store alerts, apply workflow transitions, append the audit chain."""
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from psycopg.types.json import Jsonb

from app.alerts import audit, cap, proposals, templates, workflow
from app.alerts.workflow import Alert, Event, Officer, Rules, State, WorkflowError
from app.risk.config import thresholds
from app.risk.repo import load_topology

IST = timezone(timedelta(hours=5, minutes=30))
AUDIT_LOCK = 4242_0020  # pg advisory lock key: serialises appends so the chain stays linear


def now() -> datetime:
    return datetime.now(IST)


def rules() -> Rules:
    return Rules.from_config(thresholds())


def _jsonable(x: Any) -> Any:
    return json.loads(json.dumps(x, default=str, ensure_ascii=False))


# --- audit ---------------------------------------------------------------------------------------------------

def append_audit(c, event: Event, alert_id: int | None, snapshot: dict[str, Any], message: str | None) -> dict:
    c.execute("SELECT pg_advisory_xact_lock(%s)", (AUDIT_LOCK,))
    last = c.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    detail = {"detail": event.detail} if event.detail else {}
    row = audit.chain({
        "ts": event.at, "alert_id": alert_id, "actor": event.actor, "action": event.action,
        "from_state": event.from_state.value if event.from_state else None, "to_state": event.to_state.value,
        "reason": event.reason, "input_snapshot": _jsonable({**snapshot, **detail}),
        "thresholds_version": thresholds()["version"], "message_text": message,
    }, last["hash"] if last else audit.GENESIS)
    c.execute("""INSERT INTO audit_log (ts, alert_id, actor, action, from_state, to_state, reason, input_snapshot,
                                        thresholds_version, message_text, prev_hash, hash)
                 VALUES (%(ts)s, %(alert_id)s, %(actor)s, %(action)s, %(from_state)s, %(to_state)s, %(reason)s,
                         %(input_snapshot)s, %(thresholds_version)s, %(message_text)s, %(prev_hash)s, %(hash)s)""",
              {**row, "input_snapshot": Jsonb(row["input_snapshot"])})
    return row


def audit_rows(c, alert_id: int | None = None) -> list[dict]:
    return c.execute("SELECT * FROM audit_log WHERE (%s::int IS NULL OR alert_id = %s) ORDER BY id",
                     (alert_id, alert_id)).fetchall()


def verify_chain(c) -> dict:
    return audit.verify(audit_rows(c))


# --- alerts --------------------------------------------------------------------------------------------------

def officers(c) -> list[dict]:
    return c.execute("SELECT id, name, role FROM officers ORDER BY id").fetchall()


def _officer(c, officer_id: str | None) -> Officer:
    r = c.execute("SELECT id, role FROM officers WHERE id = %s", (officer_id,)).fetchone()
    if not r:
        raise WorkflowError(f"unknown officer {officer_id!r}", "invalid")
    return Officer(r["id"], r["role"])


def _row(c, alert_id: int, lock: bool = False) -> dict:
    r = c.execute("SELECT * FROM alerts WHERE id = %s" + (" FOR UPDATE" if lock else ""), (alert_id,)).fetchone()
    if not r:
        raise WorkflowError(f"alert {alert_id} not found", "not_found")
    r["approvals"] = c.execute("SELECT officer_id AS officer, ts FROM alert_approvals WHERE alert_id = %s ORDER BY ts",
                               (alert_id,)).fetchall()
    return r


def _to_model(r: dict) -> Alert:
    return Alert(r["level"], State(r["state"]), r["proposed_action"], r["created_at"], r["needs_approvals"],
                 tuple(a["officer"] for a in r["approvals"]), r["sent_at"], r["expires_at"])


def _store(c, r: dict, new: Alert, events: list[Event], snapshot: dict[str, Any]) -> None:
    at = events[-1].at if events else now()
    c.execute("""UPDATE alerts SET state = %s, proposed_action = %s, sent_at = %s, expires_at = %s, updated_at = %s
                 WHERE id = %s""", (new.state.value, new.proposed_action, new.sent_at, new.expires_at, at, r["id"]))
    for officer_id in new.approvals[len(r["approvals"]):]:
        c.execute("INSERT INTO alert_approvals (alert_id, officer_id, ts) VALUES (%s, %s, %s)", (r["id"], officer_id, at))
    for e in events:
        append_audit(c, e, r["id"], snapshot, new.proposed_action)


def public(r: dict) -> dict:
    """API shape (docs/PLAN.md "HTTP API") plus a few extra read-only fields."""
    keys = ("id", "segment_ids", "level", "proposed_action", "state", "created_at", "updated_at", "needs_approvals",
            "mode", "source", "trigger_ts", "sent_at", "expires_at", "references_alert_id")
    return {**{k: r[k] for k in keys}, "approvals": r["approvals"], "delivery": "SIMULATED"}


def tick_all(c, at: datetime | None = None) -> int:
    """Escalate unanswered proposals and expire sent alerts. Returns the number of transitions."""
    at = at or now()
    ids = [r["id"] for r in c.execute(
        "SELECT id FROM alerts WHERE state IN ('PROPOSED', 'SENT', 'ACKED') ORDER BY id FOR UPDATE").fetchall()]
    n = 0
    for alert_id in ids:
        r = _row(c, alert_id)
        new, events = workflow.tick(_to_model(r), at, rules())
        if events:
            _store(c, r, new, events, {"trigger": "time"})
            n += len(events)
    return n


def list_alerts(c, state: str | None = None) -> list[dict]:
    tick_all(c)
    ids = c.execute("SELECT id FROM alerts WHERE (%s::text IS NULL OR state = %s) ORDER BY id DESC",
                    (state, state)).fetchall()
    return [public(_row(c, r["id"])) for r in ids]


def get_alert(c, alert_id: int) -> dict:
    return public(_row(c, alert_id))


def act(c, alert_id: int, action: str, officer_id: str | None, reason: str | None = None,
        proposed_action: str | None = None) -> dict:
    """Run one officer action (approve | reject | cancel | ack | break-glass | edit) on an alert."""
    officer = _officer(c, officer_id)
    r = _row(c, alert_id, lock=True)
    ticked, tick_events = workflow.tick(_to_model(r), now(), rules())
    if tick_events:
        _store(c, r, ticked, tick_events, {"trigger": "time"})
        r = _row(c, alert_id, lock=True)
    t, rs = now(), rules()
    steps: dict[str, Callable[[], tuple[Alert, list[Event]]]] = {
        "approve": lambda: workflow.approve(ticked, officer, t, rs, reason),
        "reject": lambda: workflow.reject(ticked, officer, t, reason),
        "cancel": lambda: workflow.cancel(ticked, officer, t, reason),
        "ack": lambda: workflow.ack(ticked, officer, t, reason),
        "break-glass": lambda: workflow.break_glass(ticked, officer, t, rs, reason),
        "edit": lambda: workflow.edit(ticked, officer, t, proposed_action),
    }
    new, events = steps[action]()
    _store(c, r, new, events, {"request": {"action": action, "officer_id": officer.id, "role": officer.role,
                                           "reason": reason, "proposed_action": proposed_action},
                               "alert_before": {"state": r["state"], "approvals": [a["officer"] for a in r["approvals"]]}})
    return get_alert(c, alert_id)


# --- proposals -----------------------------------------------------------------------------------------------

def propose_from_risk(c, mode: str, source: str, start: datetime, end: datetime) -> dict[str, list]:
    """Walk risk in [start, end]: propose alerts (rules in app.alerts.proposals) and withdraw pending proposals
    whose risk condition cleared. Returns {"proposed": [alerts], "withdrawn": [alert ids]}."""
    tick_all(c)
    topo = load_topology(c)
    stored = [proposals.OpenAlert(r["id"], list(r["segment_ids"]), r["level"], r["trigger_ts"]) for r in c.execute(
        "SELECT id, segment_ids, level, trigger_ts FROM alerts WHERE mode = %s AND source = %s ORDER BY id",
        (mode, source)).fetchall()]
    risk_at: dict[datetime, dict[str, dict]] = {}
    for r in c.execute("""SELECT segment_id, ts, hazard_level, crowd_level, risk_level, drivers FROM segment_risk
                          WHERE mode = %s AND source = %s AND ts BETWEEN %s AND %s ORDER BY ts""",
                       (mode, source, start, end)).fetchall():
        risk_at.setdefault(r["ts"], {})[r["segment_id"]] = {k: r[k] for k in ("hazard_level", "crowd_level",
                                                                              "risk_level", "drivers")}
    rs, version = rules(), thresholds()["version"]
    new, cleared = proposals.propose(topo, risk_at, stored, rs.propose_at)
    created, withdrawn = [], []
    for p in new:
        t = now()
        model, events = workflow.propose(p.level, p.proposed_action, t, rs)
        r = c.execute("""INSERT INTO alerts (segment_ids, level, proposed_action, state, mode, source, trigger_ts,
                                             needs_approvals, references_alert_id, created_at, updated_at,
                                             thresholds_version)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                      (p.segment_ids, model.level, model.proposed_action, model.state.value, mode, source,
                       p.trigger_ts, model.needs_approvals, p.references_alert_id, t, t, version)).fetchone()
        p.open.id = r["id"]
        for e in events:
            append_audit(c, e, r["id"], {"mode": mode, "source": source, **p.snapshot}, model.proposed_action)
        created.append(r["id"])
    for a in cleared:
        r = _row(c, a.id, lock=True)
        if State(r["state"]) not in workflow.PENDING:
            continue
        model, events = workflow.withdraw(
            _to_model(r), now(), f"risk below level {a.level} on all segments at {a.cleared_at.isoformat()}")
        _store(c, r, model, events, {"mode": mode, "source": source, "cleared_at": a.cleared_at.isoformat(),
                                     "risk": {s: risk_at[a.cleared_at].get(s) for s in a.segment_ids}})
        withdrawn.append(a.id)
    return {"proposed": [get_alert(c, i) for i in created], "withdrawn": withdrawn}


# --- CAP -----------------------------------------------------------------------------------------------------

def cap_xml(c, alert_id: int) -> bytes:
    r = _row(c, alert_id)
    topo = load_topology(c)
    ref = None
    if r["references_alert_id"]:
        prev = c.execute("SELECT id, sent_at FROM alerts WHERE id = %s", (r["references_alert_id"],)).fetchone()
        if prev and prev["sent_at"]:
            ref = (prev["id"], prev["sent_at"])
    lines = [json.loads(g["g"])["coordinates"] for g in c.execute(
        "SELECT ST_AsGeoJSON(geom) AS g FROM segments WHERE id = ANY(%s)", (list(r["segment_ids"]),)).fetchall()]
    ordered = list(r["segment_ids"])
    data = cap.CapInput(r["id"], r["mode"], r["level"], r["state"], ordered, r["proposed_action"], r["created_at"],
                        r["sent_at"], r["expires_at"], ref)
    return cap.build(data, templates.context(topo, ordered), cap.area_polygon(lines))
