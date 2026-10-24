"""SIMULATED RFID gate counts -> persons per segment per hour (pure, no DB).

Every number this module produces is simulated and must stay labelled `simulated = true`.
Model: pilgrims pass the Katra gate, walk up at a fixed personal speed, take the old or the Himkoti track,
spend time at Bhawan (off-segment: the Bhawan complex is not a trail segment), then walk down a track.
Occupancy of a segment at an hourly snapshot = pilgrims whose position is on it (both directions),
which is what an entries - exits count between two RFID readers would give.
"""
import math
import random
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.risk.topology import Topology

IST = timezone(timedelta(hours=5, minutes=30))


@dataclass(frozen=True)
class SimParams:
    """Simulation assumptions. Only `daily_cap` and `speed_kmh` come from the brief; the rest are SIMULATED."""
    daily_cap: int = 50_000                  # NGT daily cap (sourced: docs/research.md, Tribune)
    daily_arrivals: int = 50_000             # SIMULATED demand: a fully booked day, never above the cap
    speed_kmh: tuple[float, float] = (2.0, 3.0)
    dwell_h: tuple[float, float] = (1.0, 3.0)  # SIMULATED time at Bhawan
    p_old_track: float = 0.5                 # SIMULATED share choosing the old track (each direction)
    peak_hour: float = 9.0                   # SIMULATED daytime peak of gate entries (IST)
    peak_sigma_h: float = 3.0
    night_weight: float = 0.15               # SIMULATED floor: the track is open at night, with few entries
    seed: int = 2025


def hourly_weights(p: SimParams) -> list[float]:
    """Relative gate-entry rate for each IST hour 0-23."""
    return [p.night_weight + math.exp(-0.5 * ((h - p.peak_hour) / p.peak_sigma_h) ** 2) for h in range(24)]


def density_level(density_ppm2: float, bands: list[float]) -> int:
    """0 GREEN .. 3 RED from persons/m2 bands [yellow, orange, red] (config/thresholds.yaml crowd.bands_ppm2)."""
    return sum(density_ppm2 >= b for b in bands)


@dataclass(frozen=True)
class _Path:
    ids: list[str]
    cum_m: list[float]  # distance at the end of each segment

    @property
    def length_m(self) -> float:
        return self.cum_m[-1]


def _path(segments) -> _Path:
    cum, total = [], 0.0
    for s in segments:
        total += s.length_m
        cum.append(total)
    return _Path([s.id for s in segments], cum)


def _choose_track(rng: random.Random, p: SimParams, tracks: list[str]) -> str:
    if len(tracks) == 1:
        return tracks[0]
    old = next((t for t in tracks if t.endswith("OLD")), tracks[0])
    others = [t for t in tracks if t != old]
    return old if rng.random() < p.p_old_track else rng.choice(others)


def simulate(topo: Topology, start: datetime, end: datetime, p: SimParams = SimParams()) -> dict[tuple[str, datetime], int]:
    """Persons on each segment at each whole hour in [start, end] (inclusive). Deterministic for a seed.

    Pilgrims who entered on the previous day and are still walking are included.
    """
    if p.daily_arrivals > p.daily_cap:
        raise ValueError("daily_arrivals must not exceed the daily cap")
    t_first = start.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    if t_first < start:
        t_first += timedelta(hours=1)
    n_hours = int((end - t_first).total_seconds() // 3600) + 1
    if n_hours <= 0:
        return {}
    tracks = topo.leaf_routes()
    up = {t: _path(topo.ascent_path(t)) for t in tracks}
    down = {t: _path(topo.ascent_path(t)[::-1]) for t in tracks}
    counts = {sid: [0] * n_hours for sid in topo.by_id}
    weights = hourly_weights(p)

    def add(path: _Path, t_start: float, speed_mph: float) -> None:
        k = max(0, math.ceil(t_start))
        t_end = t_start + path.length_m / speed_mph
        while k < n_hours and k < t_end:
            i = bisect_right(path.cum_m, (k - t_start) * speed_mph)
            counts[path.ids[min(i, len(path.ids) - 1)]][k] += 1
            k += 1

    day = (t_first - timedelta(days=1)).date()
    while day <= end.astimezone(IST).date():
        rng = random.Random(f"{p.seed}-{day.isoformat()}")
        day_offset_h = (datetime(day.year, day.month, day.day, tzinfo=IST) - t_first).total_seconds() / 3600
        for hour in rng.choices(range(24), weights=weights, k=p.daily_arrivals):
            t0 = day_offset_h + hour + rng.random()
            speed = rng.uniform(*p.speed_kmh) * 1000.0
            up_track, down_track = _choose_track(rng, p, tracks), _choose_track(rng, p, tracks)
            add(up[up_track], t0, speed)
            add(down[down_track], t0 + up[up_track].length_m / speed + rng.uniform(*p.dwell_h), speed)
        day += timedelta(days=1)

    return {(sid, t_first + timedelta(hours=k)): c[k] for sid, c in counts.items() for k in range(n_hours)}


def crowd_rows(topo: Topology, occupancy: dict[tuple[str, datetime], int], mode: str,
               bands: list[float]) -> list[dict]:
    """`segment_crowd` rows; always `simulated = True`."""
    rows = []
    for (sid, ts), persons in sorted(occupancy.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        seg = topo.by_id[sid]
        density = persons / (seg.length_m * seg.width_m)
        rows.append({"segment_id": sid, "ts": ts, "mode": mode, "persons": persons,
                     "density_ppm2": round(density, 4), "level": density_level(density, bands), "simulated": True})
    return rows

