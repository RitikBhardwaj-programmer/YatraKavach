"""Integration: load segments + replay rain into PostGIS, run the replay, check the 26 Aug 2025 Adhkuwari signal.

Skips with a clear message when no DB is reachable at DATABASE_URL (see conftest.py).
"""
import importlib.util
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import conn
from app.hazard import engine
from app.hazard.engine import IST

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
ORANGE_BY = datetime(2025, 8, 26, 12, 0, tzinfo=IST)      # shrine board closed the old track by ~12:00
RED_BY = datetime(2025, 8, 26, 14, 40, tzinfo=IST)        # landslide time


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def replay_gfs(db):
    _script("load_segments").main()
    _script("load_replay_rain").main()
    return engine.run("replay", "gfs_seamless")


def _level(segment_id: str, ts: datetime, source: str = "gfs_seamless") -> int:
    with conn() as c:
        return c.execute("SELECT level FROM segment_hazard WHERE segment_id = %s AND ts = %s AND mode = 'replay' "
                         "AND source = %s", (segment_id, ts, source)).fetchone()["level"]


def test_segments_loaded(replay_gfs):
    with conn() as c:
        rows = c.execute("SELECT id, rain_point, past_slide, past_slide_at, susceptibility FROM segments").fetchall()
    assert len(rows) == 35
    by_id = {r["id"]: r for r in rows}
    assert by_id["VD-OLD-01"]["past_slide"] and by_id["VD-OLD-01"]["rain_point"] == "adhkuwari"
    assert by_id["VD-OLD-01"]["past_slide_at"] == RED_BY
    assert by_id["VD-TRUNK-01"]["rain_point"] == "katra"
    assert sum(r["past_slide"] for r in rows) == 1
    assert all(r["susceptibility"] is None for r in rows)


def test_vd_old_01_orange_before_noon_and_red_before_landslide(replay_gfs):
    assert replay_gfs["segments"] == 35 and replay_gfs["rows"] > 0
    last_hour_before_noon = ORANGE_BY.replace(hour=11)
    last_hour_before_slide = RED_BY.replace(hour=14, minute=0)
    assert _level("VD-OLD-01", last_hour_before_noon) >= 2
    assert _level("VD-OLD-01", last_hour_before_slide) == 3


def test_run_is_idempotent(replay_gfs):
    with conn() as c:
        before = c.execute("SELECT count(*) AS n FROM segment_hazard WHERE source = 'gfs_seamless'").fetchone()["n"]
    again = engine.run("replay", "gfs_seamless")
    with conn() as c:
        after = c.execute("SELECT count(*) AS n FROM segment_hazard WHERE source = 'gfs_seamless'").fetchone()["n"]
    assert before == after == again["rows"]


def test_drivers_explain_level(replay_gfs):
    with conn() as c:
        d = c.execute("SELECT drivers FROM segment_hazard WHERE segment_id = 'VD-OLD-01' AND ts = %s "
                      "AND source = 'gfs_seamless'", (RED_BY.replace(minute=0),)).fetchone()["drivers"]
    # The 26 Aug slide happened at 14:40, so at 14:00 it must not raise the level (no hindsight in the replay).
    assert d["level_name"] == "RED" and d["rule"] and d["r24_mm"] > 0 and "PAST_SLIDE" not in d.get("step_up", [])


def test_api_timeline_and_run(replay_gfs):
    from app.main import app
    client = TestClient(app)
    tl = client.get("/api/replay/timeline").json()
    assert tl["start"] == "2025-08-10T00:00:00+05:30" and tl["end"] == "2025-08-28T23:00:00+05:30"
    assert tl["step_minutes"] == 60 and any("14:40" in e["ts"] for e in tl["events"])
    r = client.post("/api/hazard/run", params={"mode": "replay", "source": "gfs_seamless"})
    assert r.status_code == 200 and r.json()["rows"] == replay_gfs["rows"]
    assert client.post("/api/hazard/run", params={"mode": "replay"}).status_code == 422
    assert client.post("/api/hazard/run", params={"mode": "replay", "source": "nope"}).status_code == 404
