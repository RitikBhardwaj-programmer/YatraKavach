"""Risk API (workstream B): segments GeoJSON, segment history, replay run. Contract: docs/PLAN.md "HTTP API"."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app import db
from app.alerts.service import propose_from_risk
from app.crowd.service import run_crowd
from app.risk import service
from app.risk.hazard_adapter import run_hazard
from app.risk.repo import IST, ist, replay_window

router = APIRouter(tags=["risk"])
Mode = Literal["live", "replay"]
DEFAULT_REPLAY_SOURCE = "gfs_seamless"  # PLAN "Verification": the replay story is checked on GFS


def _at(at: datetime | None) -> datetime:
    if at is None:
        return datetime.now(IST)
    return at if at.tzinfo else at.replace(tzinfo=IST)


@router.get("/segments")
def segments(mode: Mode = "live", at: datetime | None = None, source: str | None = None):
    with db.conn() as c:
        src = source or service.default_source(c, mode)
        return ist(service.segments_geojson(c, mode, _at(at), src))


@router.get("/segments/{segment_id}/history")
def segment_history(segment_id: str, mode: Mode = "live", source: str | None = None,
                    start: datetime | None = Query(None, alias="from"), end: datetime | None = Query(None, alias="to")):
    with db.conn() as c:
        if not c.execute("SELECT 1 FROM segments WHERE id = %s", (segment_id,)).fetchone():
            raise HTTPException(404, f"segment {segment_id} not found")
        src = source or service.default_source(c, mode)
        return ist(service.history(c, segment_id, mode, start and _at(start), end and _at(end), src))


@router.post("/replay/run")
def replay_run(source: str = DEFAULT_REPLAY_SOURCE, until: datetime | None = None):
    """Recompute hazard (via A's engine, if merged), SIMULATED crowd, risk and alert proposals for the replay.

    `until` is the replay clock: proposals and withdrawals are walked only up to it (default: end of the
    window), so a demo can stop at e.g. 2025-08-26T14:00+05:30 and act on the alerts open at that moment.
    Calling again with a later `until` continues the walk; it never re-proposes what exists.
    """
    with db.conn() as c:
        window = replay_window(c)
        sources = [r["source"] for r in c.execute(
            "SELECT DISTINCT source FROM rain_hourly WHERE mode = 'replay' ORDER BY source").fetchall()]
    if window is None:
        raise HTTPException(409, "no replay data: load data/replay with scripts/load_replay_rain.py (workstream A)")
    start, end = window
    clock = min(end, _at(until)) if until else end
    hazard = [run_hazard("replay", s, start, end) for s in sources]
    with db.conn() as c:
        crowd_rows = run_crowd(c, "replay", start, end)
        risk_rows = service.run_risk(c, "replay", start, end)
        alerts = propose_from_risk(c, "replay", source, start, clock)
    return ist({"start": start, "end": end, "until": clock, "hazard": hazard, "crowd_rows": crowd_rows, "crowd_simulated": True,
                "risk_rows": risk_rows, "proposal_source": source, "alerts_proposed": alerts["proposed"],
                "alerts_withdrawn": alerts["withdrawn"]})
