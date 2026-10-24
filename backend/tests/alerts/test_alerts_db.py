"""DB integration tests for workstream B. Each test runs in a transaction that is rolled back.

Needs PostgreSQL + PostGIS with db/init/*.sql applied (docker compose up -d db). Skips if it is not reachable.
Hazard rows are hand-made here: workstream A's engine is not used.
"""
import json
import math
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import psycopg
import pytest
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.alerts import cap, service
from app.alerts.workflow import WorkflowError
from app.crowd.service import run_crowd
from app.db import DATABASE_URL
from app.risk import service as risk_service
from app.risk.config import segments_geojson

RAIN_POINTS = {"katra": (32.9922, 74.9315), "adhkuwari": (33.0085, 74.9447), "bhawan": (33.0311, 74.9491)}
T0 = datetime.fromisoformat("2025-08-26T10:00:00+05:30")


@pytest.fixture
def c():
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=3)
    except psycopg.OperationalError as e:
        pytest.skip(f"no database at DATABASE_URL ({e.__class__.__name__}); run `docker compose up -d db`")
    if not conn.execute("SELECT to_regclass('audit_log') AS t").fetchone()["t"]:
        conn.close()
        pytest.skip("db/init/020_alerts.sql not applied (recreate the db container)")
    _load_segments(conn)
    yield conn
    conn.rollback()
    conn.close()


def _load_segments(conn) -> None:
    for f in segments_geojson()["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][0]
        point = min(RAIN_POINTS, key=lambda k: math.dist((lat, lon), RAIN_POINTS[k]))
        conn.execute("""INSERT INTO segments (id, route_id, route_name, seq, geom, length_m, width_m, kind, landmark,
                                              elev_m, terrain_slope_deg, grade_deg, rain_point)
                        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING""",
                     (p["id"], p["route_id"], p["route_name"], p["seq"], json.dumps(f["geometry"]), p["length_m"],
                      p["width_m"], p["kind"], p["landmark"], p["elev_m"], p["terrain_slope_deg"], p["grade_deg"], point))


def _hazard(conn, levels: dict[str, int], ts: datetime, source: str = "test_source") -> None:
    for sid, lvl in levels.items():
        conn.execute("""INSERT INTO segment_hazard (segment_id, ts, mode, source, level, drivers, thresholds_version)
                        VALUES (%s, %s, 'replay', %s, %s, %s, 'test') ON CONFLICT DO NOTHING""",
                     (sid, ts, source, lvl, Jsonb({"rule": "HANDMADE_TEST", "level": lvl})))


def _pipeline(conn, timeline: list[tuple[datetime, dict[str, int]]]) -> list[dict]:
    for ts, levels in timeline:
        _hazard(conn, levels, ts)
    start, end = timeline[0][0], timeline[-1][0]
    run_crowd(conn, "replay", start, end)
    risk_service.run_risk(conn, "replay", start, end, "test_source")
    return service.propose_from_risk(conn, "replay", "test_source", start, end)["proposed"]


def test_audit_log_rejects_update_and_delete(c):
    service.append_audit(c, _event(), None, {"t": 1}, "x")
    for sql in ("UPDATE audit_log SET reason = 'x'", "DELETE FROM audit_log", "TRUNCATE audit_log"):
        c.execute("SAVEPOINT s")
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            c.execute(sql)
        c.execute("ROLLBACK TO SAVEPOINT s")


def _event():
    from app.alerts.workflow import Event, State
    return Event("TEST", "system", None, State.PROPOSED, datetime.now(service.IST))


def test_crowd_rows_written_and_simulated(c):
    n = run_crowd(c, "replay", T0, T0 + timedelta(hours=1))
    assert n == 2 * 35
    r = c.execute("SELECT bool_and(simulated) AS sim, count(*) AS n FROM segment_crowd WHERE mode = 'replay' "
                  "AND ts BETWEEN %s AND %s", (T0, T0 + timedelta(hours=1))).fetchone()
    assert r == {"sim": True, "n": 70}


def test_full_red_flow_two_officers_cap_and_audit(c):
    created = _pipeline(c, [(T0, {"VD-OLD-01": 2, "VD-OLD-02": 2}), (T0 + timedelta(hours=1), {"VD-OLD-01": 3})])
    assert [(a["level"], a["segment_ids"]) for a in created] == [(2, ["VD-OLD-01", "VD-OLD-02"]), (3, ["VD-OLD-01"])]
    orange, red = created
    assert red["references_alert_id"] == orange["id"] and red["needs_approvals"] == 2

    # A second run proposes nothing new.
    again = service.propose_from_risk(c, "replay", "test_source", T0, T0 + timedelta(hours=1))
    assert again == {"proposed": [], "withdrawn": [], "extended": []}

    a = service.act(c, red["id"], "approve", "off-1")
    assert a["state"] == "PROPOSED" and [x["officer"] for x in a["approvals"]] == ["off-1"]
    with pytest.raises(WorkflowError, match="already approved"):
        service.act(c, red["id"], "approve", "off-1")
    a = service.act(c, red["id"], "approve", "off-2")
    assert a["state"] == "SENT" and a["expires_at"] is not None

    root = ET.fromstring(service.cap_xml(c, red["id"]))
    assert root.find(f"{{{cap.NS}}}status").text == "Exercise"
    assert len(root.findall(f"{{{cap.NS}}}info")) == 3

    actions = [r["action"] for r in service.audit_rows(c, red["id"])]
    assert actions == ["PROPOSE", "APPROVE", "APPROVE", "SEND"]
    assert service.verify_chain(c)["ok"] is True


def test_update_cap_after_orange_was_sent(c):
    orange, = _pipeline(c, [(T0, {"VD-HIMKOTI-03": 2})])
    service.act(c, orange["id"], "approve", "off-1")
    red, = _pipeline(c, [(T0 + timedelta(hours=1), {"VD-HIMKOTI-03": 3})])
    root = ET.fromstring(service.cap_xml(c, red["id"]))
    assert root.find(f"{{{cap.NS}}}msgType").text == "Update"
    assert f"alert-{orange['id']}," in root.find(f"{{{cap.NS}}}references").text


def test_break_glass_and_forbidden_paths(c):
    alert, = _pipeline(c, [(T0, {"VD-TRUNK-10": 3})])
    with pytest.raises(WorkflowError) as e:
        service.act(c, alert["id"], "break-glass", "off-1", "urgent")
    assert e.value.kind == "forbidden"
    with pytest.raises(WorkflowError) as e:
        service.act(c, alert["id"], "approve", "nobody")
    assert e.value.kind == "invalid"
    a = service.act(c, alert["id"], "break-glass", "sen-1", "slope cracking")
    assert a["state"] == "SENT"
    with pytest.raises(WorkflowError):
        service.act(c, alert["id"], "reject", "off-1")
    assert service.act(c, alert["id"], "ack", "off-2")["state"] == "ACKED"
    assert service.act(c, alert["id"], "cancel", "sen-1", "rain stopped")["state"] == "CANCELLED"
    rows = service.audit_rows(c, alert["id"])
    assert rows[1]["reason"] == "slope cracking" and rows[1]["actor"] == "sen-1"
    assert service.verify_chain(c)["ok"] is True


def test_pending_proposal_withdrawn_when_risk_clears(c):
    alert, = _pipeline(c, [(T0, {"VD-OLD-04": 2})])
    _hazard(c, {"VD-OLD-04": 1}, T0 + timedelta(hours=1))
    risk_service.run_risk(c, "replay", T0, T0 + timedelta(hours=1), "test_source")
    out = service.propose_from_risk(c, "replay", "test_source", T0, T0 + timedelta(hours=1))
    assert out == {"proposed": [], "withdrawn": [alert["id"]], "extended": []}
    assert service.get_alert(c, alert["id"])["state"] == "CANCELLED"
    row = service.audit_rows(c, alert["id"])[-1]
    assert (row["action"], row["actor"], row["to_state"]) == ("WITHDRAW", "system", "CANCELLED")


def test_escalation_and_expiry_by_time(c):
    alert, = _pipeline(c, [(T0, {"VD-OLD-05": 2})])
    later = datetime.now(service.IST) + timedelta(minutes=11)
    service.tick_all(c, later)
    assert service.get_alert(c, alert["id"])["state"] == "ESCALATED"
    sent = service.act(c, alert["id"], "approve", "off-2")
    assert sent["state"] == "SENT"
    service.tick_all(c, sent["expires_at"] + timedelta(seconds=1))
    assert service.get_alert(c, alert["id"])["state"] == "EXPIRED"


def test_verify_detects_tampering_in_db(c):
    _pipeline(c, [(T0, {"VD-OLD-03": 2})])
    assert service.verify_chain(c)["ok"] is True
    c.execute("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update_delete")
    c.execute("UPDATE audit_log SET reason = 'rewritten' WHERE id = (SELECT max(id) FROM audit_log)")
    result = service.verify_chain(c)
    assert result["ok"] is False and "content" in result["broken_row"]["reason"]


def test_segments_geojson_contract(c):
    _pipeline(c, [(T0, {"VD-OLD-01": 2})])
    fc = risk_service.segments_geojson(c, "replay", T0, "test_source")
    assert fc["type"] == "FeatureCollection" and len(fc["features"]) == 35
    props = next(f for f in fc["features"] if f["id"] == "VD-OLD-01")["properties"]
    for key in ("hazard_level", "crowd_level", "risk_level", "persons", "density_ppm2", "drivers", "simulated_crowd",
                "length_m", "width_m", "landmark"):
        assert key in props
    assert props["risk_level"] == 2 and props["simulated_crowd"] is True
    hist = risk_service.history(c, "VD-OLD-01", "replay", None, None, "test_source")
    assert hist[0]["risk_level"] == 2
