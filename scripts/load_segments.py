"""Load data/segments_vaishno_devi.geojson into `segments` (idempotent upsert).

rain_point = nearest rain point to the segment midpoint. past_slide_at = time of a recorded slide;
the hazard engine counts it only for later hours, so a replay never uses the slide it should warn about.
susceptibility stays NULL: GSI data was not available.
Run from the repo root: python scripts/load_segments.py
"""
import json
import sys
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import conn, pool  # noqa: E402
from app.hazard.points import nearest_point  # noqa: E402

GEOJSON = ROOT / "data" / "segments_vaishno_devi.geojson"
# 26 Aug 2025 Adhkuwari landslide on the old track (docs/research.md, docs/replay-findings.md).
PAST_SLIDES = {"VD-OLD-01": "2025-08-26T14:40:00+05:30"}
COLUMNS = ("id", "route_id", "route_name", "seq", "length_m", "width_m", "kind", "landmark", "elev_m",
           "terrain_slope_deg", "grade_deg")


def rows(features: list[dict]) -> list[dict]:
    out = []
    for f in features:
        p = f["properties"]
        mid = shape(f["geometry"]).interpolate(0.5, normalized=True)
        out.append({**{k: p.get(k) for k in COLUMNS}, "geom": json.dumps(f["geometry"]),
                    "past_slide": p["id"] in PAST_SLIDES, "past_slide_at": PAST_SLIDES.get(p["id"]), "rain_point": nearest_point(mid.y, mid.x)})
    return out


def main() -> None:
    data = rows(json.loads(GEOJSON.read_text(encoding="utf-8"))["features"])
    cols = (*COLUMNS, "past_slide", "past_slide_at", "rain_point")
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in (*cols[1:], "geom"))
    sql = (f"INSERT INTO segments ({', '.join(cols)}, geom) "
           f"VALUES ({', '.join(f'%({c})s' for c in cols)}, ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326)) "
           f"ON CONFLICT (id) DO UPDATE SET {updates}")
    with conn() as c, c.cursor() as cur:
        cur.executemany(sql, data)
    counts: dict[str, int] = {}
    for r in data:
        counts[r["rain_point"]] = counts.get(r["rain_point"], 0) + 1
    print(f"loaded {len(data)} segments; rain points {counts}; past_slide {sorted(PAST_SLIDES)}")


if __name__ == "__main__":
    main()
    pool().close()
