"""Build ~500 m route segments for the Vaishno Devi tracks from raw OSM ways.

Input:  data/raw/osm_vaishno_devi.json (from probe_osm.py)
Output: data/segments_vaishno_devi.geojson

Each segment gets: id, route_id, seq, length_m, grade_deg (trail steepness),
terrain_slope_deg (hillside steepness at the midpoint, from a 90 m DEM),
elev_m, landmark, kind, width_m.
Elevation comes from the Open-Meteo Elevation API (Copernicus DEM GLO-90).
"""
import json
import math
import time

import requests
from pyproj import Geod, Transformer
from shapely.geometry import LineString, mapping
from shapely.ops import linemerge, substring

RAW = "data/raw/osm_vaishno_devi.json"
OUT = "data/segments_vaishno_devi.geojson"
SEG_LEN_M = 500.0
ELEV_API = "https://api.open-meteo.com/v1/elevation"

# OSM way ids in walking order (Katra -> Bhawan), checked by hand from endpoints.
ROUTES = {
    "VD-TRUNK": {"name": "Katra - Banganga - Adhkuwari",
                 "ways": [102769575, 864300417, 419064290], "width_m": 6.0},
    "VD-OLD": {"name": "Old track: Adhkuwari - Hathimata - Bhawan",
               "ways": [419064291, 166322201], "width_m": 4.0},
    "VD-HIMKOTI": {"name": "New track: Adhkuwari - Himkoti - Bhawan",
                   "ways": [419064289], "width_m": 5.0},
}
# Known landmarks (lat, lon) used to label the nearest segment.
LANDMARKS = {
    "Katra (Banganga Road start)": (32.9922, 74.9315),
    "Banganga": (33.0031, 74.9471),
    "Adhkuwari (track junction)": (33.0085, 74.9447),
    "Bhawan": (33.0311, 74.9491),
}

geod = Geod(ellps="WGS84")
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)  # UTM 43N
to_wgs = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)


def way_lines():
    ways = {w["id"]: w for w in json.load(open(RAW, encoding="utf-8"))}
    return {wid: [(p["lon"], p["lat"]) for p in w["geometry"]] for wid, w in ways.items()}


def chain(coords_list):
    """Join ways end to end, flipping a way when its end touches the chain."""
    out = list(coords_list[0])
    for nxt in coords_list[1:]:
        d_start = _dist(out[-1], nxt[0])
        d_end = _dist(out[-1], nxt[-1])
        if d_end < d_start:
            nxt = list(reversed(nxt))
        if min(d_start, d_end) > 150:  # short connector ways are not in the list
            raise ValueError(f"gap of {min(d_start, d_end):.0f} m between ways")
        out.extend(nxt[1:])
    return out


def _dist(a, b):
    return geod.inv(a[0], a[1], b[0], b[1])[2]


def project(coords):
    return LineString([to_utm.transform(x, y) for x, y in coords])


def unproject(line):
    return [to_wgs.transform(x, y) for x, y in line.coords]


def elevations(points):
    """Return elevation (m) for each (lon, lat), 100 points per request."""
    res = []
    for i in range(0, len(points), 100):
        chunk = points[i:i + 100]
        r = requests.get(ELEV_API, params={
            "latitude": ",".join(f"{p[1]:.5f}" for p in chunk),
            "longitude": ",".join(f"{p[0]:.5f}" for p in chunk)}, timeout=60)
        r.raise_for_status()
        res.extend(r.json()["elevation"])
        time.sleep(0.5)
    return res


def main():
    lines = way_lines()
    features = []
    probes = []  # points needing elevation, filled per segment
    for route_id, cfg in ROUTES.items():
        merged = project(chain([lines[w] for w in cfg["ways"]]))
        total = merged.length
        n = max(1, round(total / SEG_LEN_M))
        step = total / n
        for i in range(n):
            part = substring(merged, i * step, (i + 1) * step)
            mid = part.interpolate(0.5, normalized=True)
            start, end = part.coords[0], part.coords[-1]
            # midpoint plus 4 neighbours 90 m away (N, S, E, W) for terrain slope
            nb = [(mid.x, mid.y), (mid.x, mid.y + 90), (mid.x, mid.y - 90),
                  (mid.x + 90, mid.y), (mid.x - 90, mid.y), start, end]
            probes.append([to_wgs.transform(x, y) for x, y in nb])
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": unproject(part)},
                "properties": {
                    "id": f"{route_id}-{i + 1:02d}", "route_id": route_id,
                    "route_name": cfg["name"], "seq": i + 1,
                    "length_m": round(part.length, 1), "width_m": cfg["width_m"],
                    "kind": "trail", "landmark": None,
                },
            })
    flat = [p for group in probes for p in group]
    elev = elevations(flat)
    for k, f in enumerate(features):
        e = elev[k * 7:(k + 1) * 7]
        mid, n_, s_, e_, w_, a, b = e
        dzdx = (e_ - w_) / 180.0
        dzdy = (n_ - s_) / 180.0
        props = f["properties"]
        props["elev_m"] = round(mid, 1)
        props["terrain_slope_deg"] = round(math.degrees(math.atan(math.hypot(dzdx, dzdy))), 1)
        props["grade_deg"] = round(math.degrees(math.atan(abs(b - a) / props["length_m"])), 1)
    for name, (lat, lon) in LANDMARKS.items():
        best = min(features, key=lambda f: min(_dist((lon, lat), c) for c in f["geometry"]["coordinates"]))
        best["properties"]["landmark"] = name
        if "junction" in name:
            best["properties"]["kind"] = "junction"
    json.dump({"type": "FeatureCollection", "features": features,
               "attribution": "Trails (c) OpenStreetMap contributors, ODbL. Elevation: Open-Meteo / Copernicus DEM GLO-90."},
              open(OUT, "w", encoding="utf-8"), indent=1)
    for f in features:
        p = f["properties"]
        print(f"{p['id']:14s} {p['length_m']:6.0f} m  elev {p['elev_m']:6.0f}  slope {p['terrain_slope_deg']:4.1f}  grade {p['grade_deg']:4.1f}  {p['landmark'] or ''}")


if __name__ == "__main__":
    main()
