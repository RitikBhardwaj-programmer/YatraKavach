"""Impact counterfactual (pure, no DB). Every person count here is SIMULATED.

Question: "If officers had approved the hold at time T, how many (SIMULATED) pilgrims would have been on the
slide segment at the last hourly snapshot before the slide?" (docs/PLAN.md "Impact counterfactual").
"""
from dataclasses import dataclass
from datetime import datetime

from app.crowd.simulator import IST, HoldingParams, SimParams, hold_points, simulate
from app.risk.topology import Topology


@dataclass(frozen=True)
class Decision:
    key: str
    label: str
    ts: datetime | None   # None = no action


def snapshot_hour(event_ts: datetime) -> datetime:
    """Last whole IST hour at or before the event."""
    return event_ts.astimezone(IST).replace(minute=0, second=0, microsecond=0)


def warning_start(levels: list[tuple[datetime, int]], min_level: int, at: datetime) -> datetime | None:
    """First hour of the run of hours with level >= `min_level` that is still in force at `at`.

    `levels` are one series of hourly levels (any order). The run must include the last hour at or before `at`;
    an earlier warning that cleared before it (e.g. a storm days before) does not count. None if not in force.
    """
    start = None
    for ts, level in sorted(x for x in levels if x[0] <= at):
        if level >= min_level:
            start = start or ts
        else:
            start = None
    return start


def persons_on_target(topo: Topology, targets: list[str], snapshot: datetime, params: SimParams,
                      stop_ascent: dict[str, tuple[str, datetime]] | None) -> int:
    """SIMULATED persons on the target segments at the snapshot hour.

    The window is the snapshot hour alone: `simulate` always includes pilgrims from the day before the window,
    which covers everyone who can still be on the trail at the snapshot (a round trip is shorter than a day).
    """
    occ = simulate(topo, snapshot, snapshot, params, stop_ascent=stop_ascent)
    return sum(occ[(sid, snapshot)] for sid in targets)


def counterfactual(topo: Topology, targets: list[str], event_ts: datetime, decisions: list[Decision],
                   hazard_at: dict[datetime, dict[str, int]], hp: HoldingParams,
                   params: SimParams) -> dict:
    """Contract shape of GET /api/impact/counterfactual (docs/PLAN.md), always `simulated: true`.

    `hazard_at` = hazard levels per segment at each decision hour (same source). A decision without a time
    (other than no action), after the snapshot, or with no hold point at its hour (nothing to hold) is omitted.
    """
    snapshot = snapshot_hour(event_ts)
    scenarios = []
    for d in decisions:
        if d.key != "no_action" and (d.ts is None or d.ts > snapshot):
            continue
        holds = hold_points(topo, hazard_at.get(d.ts, {}), hp) if d.ts else None
        if d.ts and not holds:
            continue
        stop = {leaf: (sid, d.ts) for leaf, sid in holds.items()} if holds else None
        scenarios.append({"key": d.key, "label": d.label, "decision_ts": d.ts, "hold_points": holds,
                          "persons_on_target": persons_on_target(topo, targets, snapshot, params, stop)})
    return {"simulated": True, "target_segments": targets, "event_ts": event_ts, "snapshot_ts": snapshot,
            "scenarios": scenarios}
