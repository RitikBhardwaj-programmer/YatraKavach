"""Hazard engine: hourly segment_hazard rows per segment for one mode + source, upserted (idempotent).

Pure scoring (score_point, score_segment) is separate from DB access (run) so it is testable without a DB.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Jsonb

from app.db import conn
from app.hazard.rules import R15D_H, HazardThresholds, HysteresisState, load_thresholds, segment_level

HOUR = timedelta(hours=1)
IST = timezone(timedelta(hours=5, minutes=30))   # Asia/Kolkata, no DST
MODES = ("live", "replay")


@dataclass(frozen=True)
class RainSeries:
    """Hourly rain on a gap-free grid. Missing hours count as 0 mm and are reported in drivers."""
    start: datetime
    precip_mm: list[float]
    present: list[bool]

    @property
    def times(self) -> list[datetime]:
        return [self.start + i * HOUR for i in range(len(self.precip_mm))]


@dataclass(frozen=True)
class Segment:
    id: str
    rain_point: str
    terrain_slope_deg: float | None
    susceptibility: int | None
    past_slide_at: datetime | None   # a past slide counts only for hours after it


def to_series(rows: list[tuple[datetime, float]]) -> RainSeries:
    """Put (ts, mm) rows, sorted by ts, on an hourly grid."""
    start, end = rows[0][0], rows[-1][0]
    n = int((end - start) / HOUR) + 1
    precip, present = [0.0] * n, [False] * n
    for ts, mm in rows:
        i = int((ts - start) / HOUR)
        precip[i], present[i] = float(mm), True
    return RainSeries(start, precip, present)


def _prefix(values: list[float]) -> list[float]:
    out = [0.0]
    for v in values:
        out.append(out[-1] + v)
    return out


def score_point(series: RainSeries, t: HazardThresholds) -> list[tuple[dict[int, float], dict[str, Any]]]:
    """Per hour: rain sums for every rule window ending at that hour, plus data-coverage notes."""
    rain = _prefix(series.precip_mm)
    seen = _prefix([1.0 if p else 0.0 for p in series.present])
    out = []
    for i in range(len(series.precip_mm)):
        sums = {h: rain[i + 1] - rain[max(0, i + 1 - h)] for h in t.windows_h}
        lo = max(0, i + 1 - R15D_H)
        notes: dict[str, Any] = {}
        if i + 1 < R15D_H:
            notes["r15d_hours_available"] = i + 1
        missing = (i + 1 - lo) - int(seen[i + 1] - seen[lo])
        if missing:
            notes["missing_hours_15d"] = missing
        out.append((sums, notes))
    return out


def score_segment(seg: Segment, point_scores: list[tuple[dict[int, float], dict[str, Any]]],
                  times: list[datetime], t: HazardThresholds) -> list[tuple[int, dict[str, Any]]]:
    """Per hour: (level, drivers) for one segment, with step-up and hysteresis carried hour to hour."""
    state, out = HysteresisState(), []
    for ts, (sums, notes) in zip(times, point_scores):
        slide = seg.past_slide_at is not None and ts > seg.past_slide_at
        state, drivers = segment_level(sums, state, seg.terrain_slope_deg, seg.susceptibility, slide, t)
        out.append((state.level, {**drivers, **notes, "rain_point": seg.rain_point}))
    return out


def _load(c, mode: str, source: str) -> tuple[list[Segment], dict[str, RainSeries]]:
    segs = [Segment(**r) for r in c.execute(
        "SELECT id, rain_point, terrain_slope_deg, susceptibility, past_slide_at FROM segments ORDER BY id").fetchall()]
    rows: dict[str, list[tuple[datetime, float]]] = {}
    for r in c.execute("SELECT point, ts, precip_mm FROM rain_hourly WHERE mode = %s AND source = %s ORDER BY point, ts",
                       (mode, source)):
        rows.setdefault(r["point"], []).append((r["ts"], r["precip_mm"]))
    return segs, {p: to_series(v) for p, v in rows.items()}


def run(mode: str, source: str, start: datetime | None = None, end: datetime | None = None,
        t: HazardThresholds | None = None) -> dict[str, Any]:
    """Compute and upsert segment_hazard for [start, end] (default: all rain hours). Returns a summary.

    Scoring always starts at the first rain hour so R15d and hysteresis see their full history.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    t = t or load_thresholds()
    with conn() as c:
        segs, series = _load(c, mode, source)
        missing = sorted({s.rain_point for s in segs} - series.keys())
        if not segs or missing:
            raise LookupError(f"no segments or no {mode}/{source} rain for points {missing}; run scripts/load_*.py")
        point_scores = {p: score_point(s, t) for p, s in series.items()}
        rows = []
        for seg in segs:
            times = series[seg.rain_point].times
            for ts, (level, drivers) in zip(times, score_segment(seg, point_scores[seg.rain_point], times, t)):
                if (start is None or ts >= start) and (end is None or ts <= end):
                    rows.append((seg.id, ts, mode, source, level, Jsonb(drivers), t.version))
        with c.cursor() as cur:
            cur.executemany(
                """INSERT INTO segment_hazard (segment_id, ts, mode, source, level, drivers, thresholds_version)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (segment_id, ts, mode, source) DO UPDATE
                   SET level = EXCLUDED.level, drivers = EXCLUDED.drivers,
                       thresholds_version = EXCLUDED.thresholds_version""", rows)
    times = [r[1] for r in rows]
    return {"mode": mode, "source": source, "segments": len(segs), "rows": len(rows),
            "from": min(times).astimezone(IST).isoformat() if times else None,
            "to": max(times).astimezone(IST).isoformat() if times else None,
            "thresholds_version": t.version}
