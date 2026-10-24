"""Shared DB reads for workstream B: segment topology and time windows."""
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.risk.topology import Segment, Topology

IST = timezone(timedelta(hours=5, minutes=30))


def load_topology(c) -> Topology:
    rows = c.execute(
        "SELECT id, route_id, seq, length_m, width_m, kind, landmark, ST_AsGeoJSON(geom) AS g FROM segments"
    ).fetchall()
    if not rows:
        raise LookupError("segments table is empty: run scripts/load_segments.py (workstream A) first")
    segs = []
    for r in rows:
        coords = json.loads(r["g"])["coordinates"]
        segs.append(Segment(r["id"], r["route_id"], r["seq"], float(r["length_m"]), float(r["width_m"]), r["kind"],
                            r["landmark"], tuple(coords[0]), tuple(coords[-1])))
    return Topology(segs)


def replay_window(c) -> tuple[datetime, datetime] | None:
    """First and last hour of replay data (rain if loaded, else hazard rows)."""
    for table in ("rain_hourly", "segment_hazard"):
        r = c.execute(f"SELECT min(ts) AS a, max(ts) AS b FROM {table} WHERE mode = 'replay'").fetchone()
        if r["a"] is not None:
            return r["a"], r["b"]
    return None


def ist(obj: Any) -> Any:
    """Recursively turn datetimes into ISO 8601 strings with +05:30 (API contract)."""
    if isinstance(obj, datetime):
        return obj.astimezone(IST).isoformat()
    if isinstance(obj, dict):
        return {k: ist(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ist(v) for v in obj]
    return obj
