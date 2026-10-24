"""Hazard HTTP API (docs/PLAN.md "HTTP API contract"). Mounted at /api by app.main."""
from datetime import datetime
from typing import Literal

import requests
from fastapi import APIRouter, HTTPException

from app.db import conn
from app.hazard import engine, live
from app.hazard.engine import IST

router = APIRouter(tags=["hazard"])
STEP_MINUTES = 60

# Replay events, sourced in docs/research.md. Chasoti's time of day is not in the sources, so it marks the day.
EVENTS = [
    (datetime(2025, 8, 14, tzinfo=IST), "14 Aug 2025: Chasoti/Machail cloudburst, Kishtwar (other route; time not sourced)"),
    (datetime(2025, 8, 26, 12, 0, tzinfo=IST), "26 Aug 2025 ~12:00: shrine board says old track closed"),
    (datetime(2025, 8, 26, 14, 40, tzinfo=IST), "26 Aug 2025 14:40: Adhkuwari landslide, old track"),
]


def _iso(ts: datetime) -> str:
    return ts.astimezone(IST).isoformat()


@router.get("/replay/timeline")
def replay_timeline() -> dict:
    with conn() as c:
        r = c.execute("SELECT min(ts) AS start, max(ts) AS end FROM rain_hourly WHERE mode = 'replay'").fetchone()
    if r["start"] is None:
        raise HTTPException(404, "no replay rain loaded; run scripts/load_replay_rain.py")
    return {"start": _iso(r["start"]), "end": _iso(r["end"]), "step_minutes": STEP_MINUTES,
            "events": [{"ts": _iso(ts), "label": label} for ts, label in EVENTS]}


@router.post("/hazard/run")
def hazard_run(mode: Literal["live", "replay"], source: str | None = None) -> dict:
    """Recompute segment_hazard. Live mode first fetches fresh rain from Open-Meteo."""
    if mode == "replay" and not source:
        raise HTTPException(422, "source is required for replay (ecmwf_ifs025 | gfs_seamless | era5)")
    fetched = None
    if mode == "live":
        if source not in (None, live.SOURCE):
            raise HTTPException(422, f"live mode only has source {live.SOURCE}")
        source = live.SOURCE
        try:
            fetched = live.ingest()
        except requests.RequestException as e:
            raise HTTPException(502, f"Open-Meteo fetch failed: {e}") from e
    try:
        summary = engine.run(mode, source)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    return {**summary, "fetched_rows": fetched} if fetched is not None else summary
