"""Live ingest parsing (saved real Open-Meteo response) and nearest rain point, without network or DB."""
import json
from datetime import timedelta
from pathlib import Path

from app.hazard import live
from app.hazard.points import RAIN_POINTS, nearest_point
from app.hazard.rules import R15D_H, R24_H

FIXTURE = Path(__file__).parent / "fixtures" / "openmeteo_forecast_adhkuwari.json"


def test_params_cover_15_days_and_next_24h():
    p = live.params(*RAIN_POINTS["adhkuwari"])
    assert (p["past_hours"], p["forecast_hours"], p["hourly"]) == (R15D_H, R24_H, "precipitation")
    assert "past_days" not in p


def test_parse_fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rows = live.parse("adhkuwari", payload)
    assert len(rows) == R15D_H + R24_H
    point, ts, source, mode, mm = rows[0]
    assert (point, source, mode) == ("adhkuwari", live.SOURCE, "live")
    assert ts.utcoffset() == timedelta(hours=5, minutes=30)
    assert rows[1][1] - ts == timedelta(hours=1)
    assert all(r[4] >= 0 for r in rows)


def test_parse_skips_null_hours():
    payload = {"utc_offset_seconds": 19800,
               "hourly": {"time": ["2026-10-24T00:00", "2026-10-24T01:00"], "precipitation": [None, 0.4]}}
    rows = live.parse("katra", payload)
    assert [r[4] for r in rows] == [0.4]


def test_nearest_point_at_each_point():
    for name, (lat, lon) in RAIN_POINTS.items():
        assert nearest_point(lat, lon) == name
