"""Live rain ingest: hourly precipitation for the 3 rain points from the Open-Meteo forecast API (CC BY 4.0).

Window: the past 15 days (R15d) plus the next 24 h, stored in rain_hourly with mode `live`.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from app.db import conn
from app.hazard.points import RAIN_POINTS
from app.hazard.rules import R15D_H, R24_H

URL = "https://api.open-meteo.com/v1/forecast"
SOURCE = "best_match"          # Open-Meteo's default model blend for the location
TIMEOUT_S = 30


def params(lat: float, lon: float) -> dict[str, Any]:
    # past_hours/forecast_hours, not past_days: forecast_hours alone would cut the past window.
    return {"latitude": lat, "longitude": lon, "hourly": "precipitation", "timezone": "Asia/Kolkata",
            "past_hours": R15D_H, "forecast_hours": R24_H}


def fetch_point(point: str) -> dict[str, Any]:
    lat, lon = RAIN_POINTS[point]
    r = requests.get(URL, params=params(lat, lon), timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def parse(point: str, payload: dict[str, Any], source: str = SOURCE) -> list[tuple[str, datetime, str, str, float]]:
    """Open-Meteo JSON -> rain_hourly rows (point, ts, source, mode, precip_mm). Null hours are skipped."""
    tz = timezone(timedelta(seconds=payload["utc_offset_seconds"]))
    hourly = payload["hourly"]
    return [(point, datetime.fromisoformat(t).replace(tzinfo=tz), source, "live", float(mm))
            for t, mm in zip(hourly["time"], hourly["precipitation"]) if mm is not None]


def store(rows: list[tuple[str, datetime, str, str, float]]) -> int:
    with conn() as c, c.cursor() as cur:
        cur.executemany(
            """INSERT INTO rain_hourly (point, ts, source, mode, precip_mm) VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (point, ts, source, mode) DO UPDATE SET precip_mm = EXCLUDED.precip_mm""", rows)
    return len(rows)


def ingest() -> dict[str, int]:
    """Fetch and store live rain for every rain point. Returns rows stored per point."""
    return {p: store(parse(p, fetch_point(p))) for p in RAIN_POINTS}
