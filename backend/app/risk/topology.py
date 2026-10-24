"""Route topology from segment geometry (pure, no DB).

Segments of one route are ordered by `seq` (ascent direction). A route whose first segment starts where
another route ends is a branch of it (e.g. old track and Himkoti track both start at the trunk end).
"""
import math
from dataclasses import dataclass

JOIN_TOLERANCE_M = 50.0  # geometric tolerance for "starts where another route ends", not a risk threshold


@dataclass(frozen=True)
class Segment:
    id: str
    route_id: str
    seq: int
    length_m: float
    width_m: float
    kind: str
    landmark: str | None
    start: tuple[float, float]  # (lon, lat)
    end: tuple[float, float]


def from_geojson(fc: dict) -> list[Segment]:
    out = []
    for f in fc["features"]:
        p, c = f["properties"], f["geometry"]["coordinates"]
        out.append(Segment(p["id"], p["route_id"], p["seq"], float(p["length_m"]), float(p["width_m"]),
                           p.get("kind") or "trail", p.get("landmark"), tuple(c[0]), tuple(c[-1])))
    return out


def _dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat = math.radians((a[1] + b[1]) / 2)
    dx = math.radians(b[0] - a[0]) * math.cos(lat) * 6371000
    dy = math.radians(b[1] - a[1]) * 6371000
    return math.hypot(dx, dy)


class Topology:
    def __init__(self, segments: list[Segment]):
        self.by_id = {s.id: s for s in segments}
        self.routes: dict[str, list[Segment]] = {}
        for s in sorted(segments, key=lambda s: (s.route_id, s.seq)):
            self.routes.setdefault(s.route_id, []).append(s)
        self.parent: dict[str, str | None] = {r: self._find_parent(r) for r in self.routes}

    def _find_parent(self, route_id: str) -> str | None:
        start = self.routes[route_id][0].start
        best, best_d = None, JOIN_TOLERANCE_M
        for other, segs in self.routes.items():
            d = _dist_m(segs[-1].end, start)
            if other != route_id and d <= best_d:
                best, best_d = other, d
        return best

    def route_chain(self, route_id: str) -> list[str]:
        """Route ids from the root route down to `route_id`."""
        chain = [route_id]
        while self.parent[chain[-1]] is not None and len(chain) <= len(self.routes):
            chain.append(self.parent[chain[-1]])
        return chain[::-1]

    def leaf_routes(self) -> list[str]:
        parents = {p for p in self.parent.values() if p}
        return sorted(r for r in self.routes if r not in parents)

    def ascent_path(self, leaf_route: str) -> list[Segment]:
        """All segments from the start of the root route to the end of `leaf_route`, in walking order."""
        return [s for r in self.route_chain(leaf_route) for s in self.routes[r]]

    def below(self, segment_id: str) -> list[Segment]:
        """Segments before `segment_id` on the way up, nearest first (the way back down)."""
        seg = self.by_id[segment_id]
        path = self.ascent_path(seg.route_id)
        idx = [s.id for s in path].index(segment_id)
        return path[:idx][::-1]

    def landmark_below(self, segment_id: str) -> Segment | None:
        """Nearest segment with a landmark before `segment_id` on the ascent."""
        return next((s for s in self.below(segment_id) if s.landmark), None)

    def label(self, segment_id: str) -> str:
        seg = self.by_id[segment_id]
        return seg.landmark or seg.id
