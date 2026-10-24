"""Auto-proposal of alerts from segment risk (pure, no DB).

Walks the risk timeline hour by hour. An alert (in any state) covers its segments from its `trigger_ts` until
the risk on all of its segments falls below the alert's own level ("the condition cleared"): a RED proposal
is stale once the segments are back to ORANGE, and an ORANGE alert below ORANGE.
A segment needs a new alert when its risk >= `alerts.propose_at_risk_level` and no covering alert has the same or a higher level.
All segments of one route at the same level form one alert (one alert per track and level, to limit alert fatigue).
While that alert is still pending and nobody has approved it, later segments of the same route and level join it
(`extended`) instead of starting another alert; once an officer approved it, a new alert is proposed. A RED proposal over a segment covered by an
ORANGE alert references that alert (CAP Update once it was sent).

Because coverage is computed from `trigger_ts`, the walk is replay-safe (replay time, not wall-clock time) and
idempotent: re-running it over the same risk rows and the same stored alerts proposes nothing new.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.alerts import templates
from app.risk.topology import Topology


@dataclass
class OpenAlert:
    id: int | None
    segment_ids: list[str]
    level: int
    trigger_ts: datetime
    cleared_at: datetime | None = None
    extendable: bool = True            # pending and nobody approved yet: new segments of its route+level join it
    extended: list[tuple[datetime, list[str]]] = field(default_factory=list)   # (hour, segments added) this walk


@dataclass
class Proposal:
    segment_ids: list[str]
    level: int
    trigger_ts: datetime
    proposed_action: str
    references: OpenAlert | None       # lower-level covering alert this one upgrades
    open: OpenAlert                    # this proposal as a covering alert; the writer sets `open.id` on insert
    snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def references_alert_id(self) -> int | None:
        return self.references.id if self.references else None


def _covering(active: list[OpenAlert], segment_id: str) -> list[OpenAlert]:
    return [a for a in active if segment_id in a.segment_ids]


def _runs(topo: Topology, levels: dict[str, int], needs: set[str]) -> list[list[str]]:
    """One group per route and level (segments in ascent order), so officers get one alert per track, not per stretch."""
    runs: list[list[str]] = []
    for segs in topo.routes.values():
        by_level: dict[int, list[str]] = {}
        for s in segs:
            if s.id in needs:
                by_level.setdefault(levels[s.id], []).append(s.id)
        runs.extend(by_level[lvl] for lvl in sorted(by_level, reverse=True))
    return runs


def propose(topo: Topology, risk_at: dict[datetime, dict[str, dict[str, Any]]], alerts: list[OpenAlert],
            propose_at: int) -> tuple[list[Proposal], list[OpenAlert]]:
    """`risk_at[ts][segment_id]` = segment_risk row (risk_level, drivers ...); `alerts` = stored alerts.

    Returns (new proposals, alerts whose condition cleared during the walk). `alerts` is extended in place.
    """
    out: list[Proposal] = []
    cleared: list[OpenAlert] = []
    for ts in sorted(risk_at):
        rows = risk_at[ts]
        levels = {sid: r["risk_level"] for sid, r in rows.items()}
        active = []
        for a in alerts:
            if a.trigger_ts > ts or a.cleared_at is not None:
                continue
            if a.trigger_ts < ts and all(levels.get(s, 0) < a.level for s in a.segment_ids):
                a.cleared_at = ts
                cleared.append(a)
                continue
            active.append(a)
        needs = {sid for sid, lvl in levels.items() if lvl >= propose_at and sid in topo.by_id
                 and not any(a.level >= lvl for a in _covering(active, sid))}
        for run in _runs(topo, levels, needs):
            level = levels[run[0]]
            route = topo.by_id[run[0]].route_id
            target = next((a for a in active if a.extendable and a.level == level
                           and topo.by_id[a.segment_ids[0]].route_id == route), None)
            if target is not None:   # one pending alert per route and level: grow it instead of adding another
                target.segment_ids[:] = sorted({*target.segment_ids, *run}, key=lambda s: topo.by_id[s].seq)
                target.extended.append((ts, run))
                continue
            lower = [a for a in _covering(active, run[0]) if a.level < level]
            new = OpenAlert(None, list(run), level, ts)
            out.append(Proposal(new.segment_ids, level, ts, templates.officer_action(level, templates.context(topo, run)),
                                lower[-1] if lower else None, new,
                                {"trigger_ts": ts.isoformat(), "risk": {sid: rows[sid] for sid in run}}))
            alerts.append(new)
            active.append(new)
    for p in out:   # text for the final segment set, after any growth during the walk
        p.proposed_action = templates.officer_action(p.level, templates.context(topo, p.segment_ids))
    return out, cleared
