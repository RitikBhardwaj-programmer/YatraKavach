"""Integration: replay hazard in PostGIS -> GET /api/impact/counterfactual (contract shape). SIMULATED counts.

Skips with a clear message when no DB is reachable at DATABASE_URL. Loads segments and replay rain and runs the
GFS hazard replay (the same committed data as tests/hazard/test_replay_db.py).
"""
import importlib.util
from pathlib import Path

import psycopg
import pytest
from app.db import DATABASE_URL
from fastapi.testclient import TestClient

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def client():
    try:
        psycopg.connect(DATABASE_URL, connect_timeout=3).close()
    except psycopg.Error as e:
        pytest.skip(f"no database at DATABASE_URL ({e.__class__.__name__}); start it with "
                    "`docker compose up -d db` to run the integration tests")
    from app.hazard import engine
    from app.main import app
    _script("load_segments").main()
    _script("load_replay_rain").main()
    engine.run("replay", "gfs_seamless")
    return TestClient(app)


def test_counterfactual_contract_shape(client):
    r = client.get("/api/impact/counterfactual", params={"source": "gfs_seamless"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"simulated", "target_segments", "event_ts", "snapshot_ts", "scenarios"}
    assert body["simulated"] is True and body["target_segments"] == ["VD-OLD-01"]
    assert body["event_ts"] == "2025-08-26T14:40:00+05:30" and body["snapshot_ts"] == "2025-08-26T14:00:00+05:30"
    keys = [s["key"] for s in body["scenarios"]]
    assert keys[0] == "no_action" and set(keys) <= {"no_action", "first_orange", "first_red", "official_closure"}
    for s in body["scenarios"]:
        assert set(s) == {"key", "label", "decision_ts", "hold_points", "persons_on_target"}
        assert isinstance(s["persons_on_target"], int) and s["persons_on_target"] >= 0
        if s["key"] == "no_action":
            assert s["decision_ts"] is None and s["hold_points"] is None
        else:
            assert s["decision_ts"] <= body["snapshot_ts"] and s["decision_ts"].endswith("+05:30")
            assert s["persons_on_target"] <= body["scenarios"][0]["persons_on_target"]
    closure = next(s for s in body["scenarios"] if s["key"] == "official_closure")
    assert closure["decision_ts"] == "2025-08-26T12:00:00+05:30" and "approximate" in closure["label"]


def test_unknown_source_is_404(client):
    r = client.get("/api/impact/counterfactual", params={"source": "no_such_model"})
    assert r.status_code == 404 and "replay/run" in r.json()["detail"]
