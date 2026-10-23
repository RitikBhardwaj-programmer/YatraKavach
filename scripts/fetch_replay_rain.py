"""Download archived hourly rainfall for the August 2025 replay window.

Two Open-Meteo sources, saved side by side so the replay can show both:
- historical-forecast (ECMWF IFS 0.25 deg, GFS): short-lead forecasts archived as they ran,
  i.e. close to what a live system would have seen at the time
- archive (ERA5 reanalysis): a later best estimate of what fell (not available in real time)

Output: data/replay/rain_<point>_<source>.json  (hourly mm)
"""
import json
import os
import sys

import requests

POINTS = {
    "adhkuwari": (33.0085, 74.9447),
    "katra": (32.9922, 74.9315),
    "bhawan": (33.0311, 74.9491),
}
WINDOW = ("2025-08-10", "2025-08-28")
# The default "best_match" model gave the same numbers from both APIs, so name models explicitly.
SOURCES = {
    "ecmwf_ifs025": ("https://historical-forecast-api.open-meteo.com/v1/forecast", {"models": "ecmwf_ifs025"}),
    "gfs_seamless": ("https://historical-forecast-api.open-meteo.com/v1/forecast", {"models": "gfs_seamless"}),
    "era5": ("https://archive-api.open-meteo.com/v1/archive", {"models": "era5"}),
}


def fetch(point, source):
    lat, lon = POINTS[point]
    url, extra = SOURCES[source]
    params = {"latitude": lat, "longitude": lon, "start_date": WINDOW[0], "end_date": WINDOW[1],
              "hourly": "precipitation", "timezone": "Asia/Kolkata", **extra}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    os.makedirs("data/replay", exist_ok=True)
    out = {"point": point, "lat": lat, "lon": lon, "source": source, "source_url": url,
           "timezone": "Asia/Kolkata", "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
           "time": data["hourly"]["time"],
           "precip_mm": next(v for k, v in data["hourly"].items() if k != "time")}
    json.dump(out, open(f"data/replay/rain_{point}_{source}.json", "w", encoding="utf-8"))
    return out


def daily(out):
    days = {}
    for t, p in zip(out["time"], out["precip_mm"]):
        days.setdefault(t[:10], []).append(p or 0.0)
    return {d: (round(sum(v), 1), round(max(v), 1)) for d, v in days.items()}


if __name__ == "__main__":
    for point in POINTS:
        for source in SOURCES:
            d = daily(fetch(point, source))
            print(f"== {point} / {source}: day -> (total mm, max 1 h mm)")
            print("  " + "  ".join(f"{k[5:]}:{v[0]}/{v[1]}" for k, v in d.items()))
    sys.exit(0)
