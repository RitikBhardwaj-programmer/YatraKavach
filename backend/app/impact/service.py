"""DB reads for the impact counterfactual (SIMULATED crowd, replay hazard of one source)."""
from datetime import datetime

from app.crowd.service import holding_params
from app.crowd.simulator import SimParams
from app.hazard.router import EVENTS
from app.hazard.rules import ORANGE, RED
from app.impact.counterfactual import (
    Decision,
    counterfactual,
    snapshot_hour,
    warning_start,
)
from app.risk.repo import load_topology

CLOSURE_LABEL = "shrine board says old track closed"   # the replay timeline event (app.hazard.router.EVENTS)


def official_closure_ts() -> datetime:
    return next(ts for ts, label in EVENTS if CLOSURE_LABEL in label)


def _targets(c) -> tuple[list[str], datetime]:
    rows = c.execute("SELECT id, past_slide_at FROM segments WHERE past_slide_at IS NOT NULL ORDER BY id").fetchall()
    if not rows:
        raise LookupError("no segment has past_slide_at: run scripts/load_segments.py")
    events = {r["past_slide_at"] for r in rows}
    if len(events) > 1:
        raise ValueError(f"targets have {len(events)} different past_slide_at values; the contract has one event_ts")
    return [r["id"] for r in rows], events.pop()


def _target_levels(c, targets: list[str], source: str, until: datetime) -> list[tuple[datetime, int]]:
    """Hourly hazard level of the targets (max over them), replay mode, this source."""
    rows = c.execute("""SELECT ts, max(level) AS level FROM segment_hazard
                        WHERE mode = 'replay' AND source = %s AND segment_id = ANY(%s) AND ts <= %s
                        GROUP BY ts ORDER BY ts""", (source, targets, until)).fetchall()
    return [(r["ts"], r["level"]) for r in rows]


def _hazard_at(c, source: str, ts: datetime) -> dict[str, int]:
    rows = c.execute("SELECT segment_id, level FROM segment_hazard WHERE mode = 'replay' AND source = %s AND ts = %s",
                     (source, ts)).fetchall()
    return {r["segment_id"]: r["level"] for r in rows}


def run(c, source: str) -> dict:
    hp = holding_params()
    if hp is None:
        raise ValueError("crowd.holding is disabled in config/thresholds.yaml; the counterfactual needs hold points")
    topo = load_topology(c)
    targets, event_ts = _targets(c)
    snapshot = snapshot_hour(event_ts)
    levels = _target_levels(c, targets, source, snapshot)
    if not levels:
        raise LookupError(f"no replay hazard for source {source}: run POST /api/replay/run first")
    decisions = [
        Decision("no_action", "No action (SIMULATED)", None),
        Decision("first_orange", f"Hold approved at first ORANGE ({source})", warning_start(levels, ORANGE, snapshot)),
        Decision("first_red", f"Hold approved at first RED ({source})", warning_start(levels, RED, snapshot)),
        Decision("official_closure", "Shrine board closes old track (~12:00, approximate)", official_closure_ts()),
    ]
    hazard_at = {d.ts: _hazard_at(c, source, d.ts) for d in decisions if d.ts}
    return counterfactual(topo, targets, event_ts, decisions, hazard_at, hp, SimParams())
