"""Risk writer and read queries. Reads `segment_hazard` (workstream A) only; never writes it."""
import json
from datetime import datetime
from typing import Any

from psycopg.types.json import Jsonb

from app.risk.fuse import fuse

UPSERT = """
INSERT INTO segment_risk (segment_id, ts, mode, source, hazard_level, crowd_level, risk_level, drivers)
VALUES (%(segment_id)s, %(ts)s, %(mode)s, %(source)s, %(hazard_level)s, %(crowd_level)s, %(risk_level)s, %(drivers)s)
ON CONFLICT (segment_id, ts, mode, source) DO UPDATE SET hazard_level = EXCLUDED.hazard_level,
    crowd_level = EXCLUDED.crowd_level, risk_level = EXCLUDED.risk_level, drivers = EXCLUDED.drivers
"""


def run_risk(c, mode: str, start: datetime, end: datetime, source: str | None = None) -> int:
    """Fuse every hazard row in [start, end] with the crowd row of the same segment and hour."""
    rows = c.execute(
        """SELECT h.segment_id, h.ts, h.source, h.level, h.drivers, h.thresholds_version,
                  c.persons, c.density_ppm2, c.level AS crowd_level, c.simulated
           FROM segment_hazard h
           LEFT JOIN segment_crowd c ON c.segment_id = h.segment_id AND c.ts = h.ts AND c.mode = h.mode
           WHERE h.mode = %s AND h.ts BETWEEN %s AND %s AND (%s::text IS NULL OR h.source = %s)""",
        (mode, start, end, source, source)).fetchall()
    out = []
    for r in rows:
        crowd = None if r["persons"] is None else {
            "persons": r["persons"], "density_ppm2": r["density_ppm2"], "level": r["crowd_level"],
            "simulated": r["simulated"]}
        fused = fuse(r["level"], {**r["drivers"], "thresholds_version": r["thresholds_version"]}, crowd)
        out.append({"segment_id": r["segment_id"], "ts": r["ts"], "mode": mode, "source": r["source"],
                    **fused, "drivers": Jsonb(fused["drivers"])})
    with c.cursor() as cur:
        cur.executemany(UPSERT, out)
    return len(out)


def default_source(c, mode: str) -> str | None:
    r = c.execute("SELECT source FROM segment_risk WHERE mode = %s GROUP BY source ORDER BY source = 'gfs_seamless' DESC,"
                  " max(ts) DESC LIMIT 1", (mode,)).fetchone()
    return r["source"] if r else None


def segments_geojson(c, mode: str, at: datetime, source: str | None) -> dict[str, Any]:
    """Segments with the latest risk/crowd at or before `at`. Levels are null when nothing is computed yet."""
    rows = c.execute(
        """SELECT s.id, s.route_id, s.route_name, s.seq, s.length_m, s.width_m, s.kind, s.landmark, s.elev_m,
                  s.terrain_slope_deg, s.grade_deg, s.susceptibility, s.past_slide, s.rain_point,
                  ST_AsGeoJSON(s.geom) AS geometry, r.ts, r.hazard_level, r.crowd_level, r.risk_level, r.drivers,
                  c.persons, c.density_ppm2, c.simulated
           FROM segments s
           LEFT JOIN LATERAL (SELECT * FROM segment_risk r WHERE r.segment_id = s.id AND r.mode = %(mode)s
                              AND r.source = %(source)s AND r.ts <= %(at)s ORDER BY r.ts DESC LIMIT 1) r ON true
           LEFT JOIN LATERAL (SELECT * FROM segment_crowd c WHERE c.segment_id = s.id AND c.mode = %(mode)s
                              AND c.ts <= %(at)s ORDER BY c.ts DESC LIMIT 1) c ON true
           ORDER BY s.route_id, s.seq""",
        {"mode": mode, "source": source, "at": at}).fetchall()
    features = []
    for r in rows:
        props = {k: v for k, v in r.items() if k not in ("geometry", "ts", "simulated")}
        props.update(ts=r["ts"], mode=mode, source=source,
                     simulated_crowd=bool(r["simulated"]) if r["simulated"] is not None else True)
        features.append({"type": "Feature", "id": r["id"], "geometry": json.loads(r["geometry"]), "properties": props})
    return {"type": "FeatureCollection", "features": features}


def history(c, segment_id: str, mode: str, start: datetime | None, end: datetime | None,
            source: str | None) -> list[dict[str, Any]]:
    rows = c.execute(
        """SELECT ts, hazard_level, crowd_level, risk_level, drivers FROM segment_risk
           WHERE segment_id = %s AND mode = %s AND source = %s
             AND (%s::timestamptz IS NULL OR ts >= %s) AND (%s::timestamptz IS NULL OR ts <= %s)
           ORDER BY ts""", (segment_id, mode, source, start, start, end, end)).fetchall()
    return rows
