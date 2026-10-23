"""Probe OpenStreetMap (Overpass API) for pilgrim trails in two bounding boxes."""
import json
import sys

import requests

OVERPASS = "https://overpass-api.de/api/interpreter"
BOXES = {
    # south, west, north, east
    "vaishno_devi": (32.97, 74.90, 33.04, 74.97),
    "machail": (33.25, 76.14, 33.45, 76.40),
}


def probe(name, box):
    s, w, n, e = box
    q = f"""
    [out:json][timeout:60];
    way["highway"~"path|footway|track|steps|pedestrian|unclassified|tertiary"]({s},{w},{n},{e});
    out tags geom;
    """
    r = requests.post(OVERPASS, data={"data": q}, timeout=90,
                      headers={"User-Agent": "YatraKavach-prototype/0.1"})
    r.raise_for_status()
    ways = r.json()["elements"]
    print(f"== {name}: {len(ways)} ways")
    named = {}
    for w_ in ways:
        nm = w_.get("tags", {}).get("name") or w_.get("tags", {}).get("name:en")
        if nm:
            named.setdefault(nm, 0)
            named[nm] += len(w_.get("geometry", []))
    for nm, pts in sorted(named.items(), key=lambda x: -x[1])[:25]:
        print(f"  {pts:5d} pts  {nm}")
    with open(f"data/raw/osm_{name}.json", "w", encoding="utf-8") as f:
        json.dump(ways, f)


if __name__ == "__main__":
    for k, b in BOXES.items():
        if len(sys.argv) == 1 or k in sys.argv[1:]:
            probe(k, b)
