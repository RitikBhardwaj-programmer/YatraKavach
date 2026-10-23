"""List OSM place/amenity nodes and unnamed ways in a box, to locate villages and landmarks."""
import json
import sys

import requests

OVERPASS = "https://overpass-api.de/api/interpreter"


def main(s, w, n, e, raw):
    q = f"""
    [out:json][timeout:60];
    (node["place"]({s},{w},{n},{e});
     node["amenity"]({s},{w},{n},{e});
     node["tourism"]({s},{w},{n},{e});
     node["natural"="peak"]({s},{w},{n},{e}););
    out;
    """
    r = requests.post(OVERPASS, data={"data": q}, timeout=90,
                      headers={"User-Agent": "YatraKavach-prototype/0.1"})
    r.raise_for_status()
    for el in r.json()["elements"]:
        t = el.get("tags", {})
        print(f"{el['lat']:.5f},{el['lon']:.5f}  {t.get('place') or t.get('amenity') or t.get('tourism') or t.get('natural')}  {t.get('name', '')}")
    ways = json.load(open(raw, encoding="utf-8"))
    print("-- ways")
    for wy in ways:
        g = wy.get("geometry", [])
        t = wy.get("tags", {})
        print(f"{wy['id']} {t.get('highway')} {t.get('name', '-')} pts={len(g)} start={g[0]['lat']:.4f},{g[0]['lon']:.4f} end={g[-1]['lat']:.4f},{g[-1]['lon']:.4f}")


if __name__ == "__main__":
    s, w, n, e = map(float, sys.argv[1:5])
    main(s, w, n, e, sys.argv[5])
