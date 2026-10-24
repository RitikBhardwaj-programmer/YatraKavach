"""Camera crowd count -> segment crowd level (docs/PLAN.md "Camera crowd count").

Pure helpers (cameras, samples, crowd maths) are separate from the DB writes so they test without a DB.
A camera sees `view_area_m2` of its segment (ASSUMED demo value); the density it measures is spread over the
whole segment to get persons_on_segment.
"""
from datetime import datetime
from pathlib import Path

from psycopg.types.json import Jsonb

from app.crowd.service import UPSERT as CROWD_UPSERT
from app.crowd.simulator import IST, density_level
from app.risk.config import thresholds
from app.risk.service import run_risk
from app.vision.infer import VISION_DIR, vision_config

SAMPLES_DIR = VISION_DIR / "samples"
ATTRIBUTION = SAMPLES_DIR / "ATTRIBUTION.md"
SAMPLE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def cameras() -> list[dict]:
    return [{"id": c["id"], "segment_id": c["segment_id"], "view_area_m2": float(c["view_area_m2"]),
             "label": c["label"], "assumed": True} for c in vision_config()["cameras"]]


def camera(camera_id: str) -> dict | None:
    return next((c for c in cameras() if c["id"] == camera_id), None)


def parse_attribution(text: str) -> list[dict]:
    """Rows of the markdown table `| file | title | author | licence | source URL |` in ATTRIBUTION.md."""
    out = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or not cells[0].lower().endswith(SAMPLE_SUFFIXES):
            continue
        name, title, author, licence, url = cells
        out.append({"name": name, "attribution": f"{title} by {author}", "license": licence, "source_url": url})
    return out


def samples(path: Path = ATTRIBUTION) -> list[dict]:
    """Demo photos with their licence (only files that are both listed and present)."""
    if not path.exists():
        return []
    return [s for s in parse_attribution(path.read_text(encoding="utf-8")) if (path.parent / s["name"]).is_file()]


def sample_path(name: str) -> Path | None:
    """Path of a listed sample; None for anything not in ATTRIBUTION.md (so no path traversal)."""
    return SAMPLES_DIR / name if any(s["name"] == name for s in samples()) else None


def crowd_from_count(count: float, view_area_m2: float, length_m: float, width_m: float,
                     bands: list[float]) -> dict:
    """density = count / view area; persons on the segment = density x segment area; level from the bands."""
    density = count / view_area_m2
    return {"density_ppm2": round(density, 4), "persons_on_segment": round(density * length_m * width_m),
            "level": density_level(density, bands)}


def current_hour(now: datetime | None = None) -> datetime:
    """The current IST hour (the live `segment_crowd` row this count updates)."""
    return (now or datetime.now(IST)).astimezone(IST).replace(minute=0, second=0, microsecond=0)


def segment_area(c, segment_id: str) -> tuple[float, float]:
    r = c.execute("SELECT length_m, width_m FROM segments WHERE id = %s", (segment_id,)).fetchone()
    if r is None:
        raise LookupError(f"segment {segment_id} not in the segments table")
    return float(r["length_m"]), float(r["width_m"])


def measure(c, cam: dict, count: float) -> dict:
    length_m, width_m = segment_area(c, cam["segment_id"])
    return crowd_from_count(count, cam["view_area_m2"], length_m, width_m, thresholds()["crowd"]["bands_ppm2"])


def persist(c, cam: dict, crowd: dict, hour: datetime) -> int:
    """Upsert the live crowd row of the camera's segment (simulated = false), then re-run live risk for the hour."""
    c.execute(CROWD_UPSERT, {"segment_id": cam["segment_id"], "ts": hour, "mode": "live",
                             "persons": crowd["persons_on_segment"], "density_ppm2": crowd["density_ppm2"],
                             "level": crowd["level"], "simulated": False,
                             "scenario": Jsonb({"source": "camera", "camera_id": cam["id"]})})
    return run_risk(c, "live", hour, hour)
