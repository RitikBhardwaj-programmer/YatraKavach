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


def simulate(topo: Topology, start: datetime, end: datetime, p: SimParams = SimParams(),
             up_arrivals: dict[tuple[str, str], list[int]] | None = None,
             stop_ascent: dict[str, tuple[str, datetime]] | None = None) -> dict[tuple[str, datetime], int]:
    """Persons on each segment at each whole hour in [start, end] (inclusive). Deterministic for a seed.

    Pilgrims who entered on the previous day and are still walking are included.
    `up_arrivals`, if given with keys (leaf route, segment id), is filled with the number of ascending pilgrims
    on that leaf route who reach the start of that segment in each hour (input for the holding scenario).
    `stop_ascent` = {leaf route: (hold segment id, from_ts)} (impact counterfactual): an ascending pilgrim on that
    leaf route who reaches the start of the hold segment at or after `from_ts` stays on the hold segment for the
    rest of the window (not counted above it, no descent). Pilgrims who passed the hold point earlier are unchanged.
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
    # distance from the path start to the start of each watched segment, per leaf route
    watch: dict[str, list[tuple[str, float]]] = {}
    for (leaf, sid) in (up_arrivals or {}):
        path = up[leaf]
        if sid in path.ids:
            i = path.ids.index(sid)
            watch.setdefault(leaf, []).append((sid, path.cum_m[i - 1] if i else 0.0))
        up_arrivals[(leaf, sid)][:] = [0] * n_hours
    # per held leaf route: hold segment, distance to its start, hold time in hours from t_first
    holds: dict[str, tuple[str, float, float]] = {}
    for leaf, (sid, from_ts) in (stop_ascent or {}).items():
        if leaf not in up or sid not in up[leaf].ids:
            raise ValueError(f"stop_ascent: {sid} is not on the ascent path of {leaf}")
        i = up[leaf].ids.index(sid)
        holds[leaf] = (sid, up[leaf].cum_m[i - 1] if i else 0.0, (from_ts - t_first).total_seconds() / 3600)


    def mark_arrivals(leaf: str, t_start: float, speed_mph: float, max_dist: float = math.inf) -> None:
        for sid, dist in watch.get(leaf, ()):
            if dist > max_dist:
                continue
            k = math.floor(t_start + dist / speed_mph)
            if 0 <= k < n_hours:
                up_arrivals[(leaf, sid)][k] += 1

    def add(path: _Path, t_start: float, speed_mph: float, t_stop: float = math.inf) -> None:
        k = max(0, math.ceil(t_start))
        t_end = min(t_start + path.length_m / speed_mph, t_stop)
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
            dwell = rng.uniform(*p.dwell_h)  # drawn for every pilgrim, so a hold never shifts the random stream
            hold = holds.get(up_track)
            if hold and t0 + hold[1] / speed >= hold[2]:
                sid, dist, _ = hold
                t_hold = t0 + dist / speed
                add(up[up_track], t0, speed, t_stop=t_hold)
                mark_arrivals(up_track, t0, speed, max_dist=dist)
                for k in range(max(0, math.ceil(t_hold)), n_hours):
                    counts[sid][k] += 1
                continue
            add(up[up_track], t0, speed)
            mark_arrivals(up_track, t0, speed)
            add(down[down_track], t0 + up[up_track].length_m / speed + dwell, speed)
        day += timedelta(days=1)

    return {(sid, t_first + timedelta(hours=k)): c[k] for sid, c in counts.items() for k in range(n_hours)}


@dataclass(frozen=True)
class HoldingParams:
    """SIMULATED holding-area scenario (config/thresholds.yaml crowd.holding)."""
    points: tuple[str, ...]        # segments where pilgrims can be held, ascent order (gate first)
    hold_at_hazard_level: int      # ascent is stopped below the first segment at or above this hazard level
    release_per_hour: int          # SIMULATED rate at which a held queue moves on after the hold ends
    max_held_persons: int          # SIMULATED cap: registrations are assumed suspended beyond it


def hold_points(topo: Topology, hazard: dict[str, int], hp: HoldingParams) -> dict[str, str]:
    """Per leaf route: the holding point where ascent stops this hour, or no entry when nothing is held.

    The hold is the nearest holding point below the first segment (in ascent order) whose hazard level is at
    least `hold_at_hazard_level`. If that segment is the gate segment itself, pilgrims are held at the gate.
    """
    out: dict[str, str] = {}
    for leaf in topo.leaf_routes():
        path = [s.id for s in topo.ascent_path(leaf)]
        idx = next((i for i, sid in enumerate(path) if hazard.get(sid, 0) >= hp.hold_at_hazard_level), None)
        if idx is None:
            continue
        below = [sid for sid in path[:idx] if sid in hp.points]
        gate = next((sid for sid in path if sid in hp.points), None)
        hold = below[-1] if below else gate
        if hold is not None:
            out[leaf] = hold
    return out


def apply_holding(occupancy: dict[tuple[str, datetime], int], times: list[datetime],
                  holds: list[dict[str, str]], up_arrivals: dict[tuple[str, str], list[int]],
                  hp: HoldingParams) -> dict[tuple[str, datetime], dict]:
    """Add held queues to the holding segments (SIMULATED). Returns {(segment, ts): scenario note}.

    While a leaf route is held at H, its ascending pilgrims who reach H join the queue at H. When no route is
    held at H any more, the queue moves on at `release_per_hour`. Simplification (stated in the README): the
    base flow beyond a hold is not reduced, so exposure above the hold is overstated, not understated.
    """
    queue: dict[str, int] = {h: 0 for h in hp.points}
    notes: dict[tuple[str, datetime], dict] = {}
    for k, ts in enumerate(times):
        active = holds[k]
        for leaf, h in active.items():
            queue[h] = min(hp.max_held_persons, queue[h] + up_arrivals.get((leaf, h), [0] * len(times))[k])
        for h in hp.points:
            held_routes = sorted(leaf for leaf, x in active.items() if x == h)
            if not held_routes:
                queue[h] = max(0, queue[h] - hp.release_per_hour)
            if queue[h]:
                occupancy[(h, ts)] = occupancy.get((h, ts), 0) + queue[h]
                notes[(h, ts)] = {"scenario": "HOLDING_AREA", "held_persons": queue[h],
                                  "held_routes": held_routes, "releasing": not held_routes}
    return notes


def crowd_rows(topo: Topology, occupancy: dict[tuple[str, datetime], int], mode: str,
               bands: list[float], notes: dict[tuple[str, datetime], dict] | None = None) -> list[dict]:
    """`segment_crowd` rows; always `simulated = True`. `scenario` holds the holding-area note, if any."""
    rows = []
    for (sid, ts), persons in sorted(occupancy.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        seg = topo.by_id[sid]
        density = persons / (seg.length_m * seg.width_m)
        rows.append({"segment_id": sid, "ts": ts, "mode": mode, "persons": persons,
                     "density_ppm2": round(density, 4), "level": density_level(density, bands), "simulated": True,
                     "scenario": (notes or {}).get((sid, ts))})
    return rows

