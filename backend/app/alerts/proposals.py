"""Auto-proposal of alerts from segment risk (pure, no DB).

Walks the risk timeline hour by hour. An alert (in any state) covers its segments from its `trigger_ts` until
the risk on all of its segments falls below the alert's own level ("the condition cleared"): a RED proposal
is stale once the segments are back to ORANGE, and an ORANGE alert below ORANGE.
A segment needs a new alert when its risk >= `alerts.propose_at_risk_level` and no covering alert has the same or a higher level.
Contiguous segments of one route at the same level form one alert. A RED proposal over a segment covered by an
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
    runs: list[list[str]] = []
    for segs in topo.routes.values():
        current: list[str] = []
        for s in segs:
            if s.id in needs and current and levels[current[-1]] == levels[s.id]:
                current.append(s.id)
                continue
            if current:
                runs.append(current)
            current = [s.id] if s.id in needs else []
        if current:
            runs.append(current)
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
            lower = [a for a in _covering(active, run[0]) if a.level < level]
            ctx = templates.context(topo, run)
            new = OpenAlert(None, run, level, ts)
            out.append(Proposal(run, level, ts, templates.officer_action(level, ctx), lower[-1] if lower else None,
                                new, {"trigger_ts": ts.isoformat(), "risk": {sid: rows[sid] for sid in run}}))
            alerts.append(new)
    return out, cleared
