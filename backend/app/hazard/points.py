"""Rain points: the 3 Open-Meteo grid points whose hourly rain drives the hazard rules."""
from pyproj import Geod

# Same coordinates as scripts/fetch_replay_rain.py and data/replay/*.json (lat, lon).
RAIN_POINTS: dict[str, tuple[float, float]] = {
    "katra": (32.9922, 74.9315),
    "adhkuwari": (33.0085, 74.9447),
    "bhawan": (33.0311, 74.9491),
}
_GEOD = Geod(ellps="WGS84")


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return _GEOD.inv(lon1, lat1, lon2, lat2)[2]


def nearest_point(lat: float, lon: float, points: dict[str, tuple[float, float]] = RAIN_POINTS) -> str:
    """Name of the rain point closest to (lat, lon) on the WGS84 ellipsoid."""
    return min(points, key=lambda p: distance_m(lat, lon, *points[p]))
