"""Build EXAMPLE fixtures for the impact and vision endpoints (docs/PLAN.md "HTTP API"). Not real results.

- Impact: decision and event times are copied from docs/replay-findings.md ("System result", measured
  2026-10-24); every persons number is a round EXAMPLE, not a simulation output.
- Vision: the camera comes from `vision.cameras` in config/thresholds.yaml. The sample image is a generated
  placeholder (grey background and dots), not a photo; the real photos and their credits come from
  workstream V (backend/app/vision/samples/ATTRIBUTION.md). The count is a round EXAMPLE, not model output.
- Lead time: docs/replay-findings.md values, for the console header when the impact API is unavailable.

Run from the repo root:  python docs/api-fixtures/build_console2_fixtures.py   (needs PyYAML and Pillow)
"""
from __future__ import annotations

import base64
import io
import json
import random
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SAMPLE_NAME = "example-placeholder.png"
SAMPLE_SIZE = (640, 400)
SAMPLE_DOTS = 300            # dots drawn on the placeholder; equal to the EXAMPLE count
EXAMPLE_COUNT = 300
EXAMPLE_MS = 500
SEED = 20251024
NOTE = ("EXAMPLE fixture for building the console; not a real result. Times from docs/replay-findings.md; "
        "numbers are round examples.")

TARGET = "VD-OLD-01"
EVENT = "2025-08-26T14:40:00+05:30"
SNAPSHOT = "2025-08-26T14:00:00+05:30"
CLOSURE = "2025-08-26T12:00:00+05:30"
HOLD = {"VD-OLD": "VD-TRUNK-13", "VD-HIMKOTI": "VD-TRUNK-13"}   # EXAMPLE hold points (Adhkuwari)
# (source, first ORANGE, first RED) from docs/replay-findings.md "System result".
SOURCES = {
    "gfs_seamless": ("2025-08-25T15:00:00+05:30", "2025-08-26T05:00:00+05:30"),
    "ecmwf_ifs025": ("2025-08-26T02:00:00+05:30", "2025-08-26T13:00:00+05:30"),
}
# Round EXAMPLE persons on the target per scenario; an earlier hold gives fewer people.
EXAMPLE_PERSONS = {
    "gfs_seamless": {"first_orange": 100, "first_red": 200, "official_closure": 500, "no_action": 1000},
    "ecmwf_ifs025": {"first_orange": 200, "official_closure": 500, "first_red": 700, "no_action": 1000},
}
LABELS = {
    "no_action": "No action",
    "first_orange": "Hold at first ORANGE",
    "first_red": "Hold at first RED",
    "official_closure": "Official closure (~12:00, approximate)",
}


def write_json(name: str, data: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def impact(source: str) -> dict[str, Any]:
    first_orange, first_red = SOURCES[source]
    times = {"first_orange": first_orange, "first_red": first_red, "official_closure": CLOSURE}
    scenarios = [{"key": "no_action", "label": LABELS["no_action"], "decision_ts": None, "hold_points": None,
                  "persons_on_target": EXAMPLE_PERSONS[source]["no_action"]}]
    for key, ts in times.items():
        scenarios.append({"key": key, "label": LABELS[key], "decision_ts": ts, "hold_points": dict(HOLD),
                          "persons_on_target": EXAMPLE_PERSONS[source][key]})
    return {"simulated": True, "example": True, "fixture_note": NOTE, "source": source,
            "target_segments": [TARGET], "event_ts": EVENT, "snapshot_ts": SNAPSHOT, "scenarios": scenarios}


def segment(seg_id: str) -> dict[str, Any]:
    fc = json.loads((ROOT / "data/segments_vaishno_devi.geojson").read_text())
    return next(f["properties"] for f in fc["features"] if f["properties"]["id"] == seg_id)


def level(density: float, bands: list[float]) -> int:
    return sum(density >= b for b in bands)


def placeholder() -> tuple[Image.Image, list[tuple[int, int]]]:
    rng = random.Random(SEED)
    w, h = SAMPLE_SIZE
    img = Image.new("RGB", SAMPLE_SIZE, (150, 154, 160))
    draw = ImageDraw.Draw(img)
    dots = []
    for _ in range(SAMPLE_DOTS):
        y = int(h * (0.3 + 0.7 * rng.random() ** 0.7))
        x = int(w * (0.5 + (rng.random() - 0.5) * (0.4 + 0.6 * y / h)))
        r = max(2, int(2 + 6 * y / h))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(60, 62, 70))
        dots.append((x, y))
    draw.rectangle((0, 0, w, 34), fill=(255, 224, 138))
    draw.text((10, 11), "EXAMPLE PLACEHOLDER - generated dots, not a photo, not a camera", fill=(74, 58, 0))
    return img, dots


def heatmap(img: Image.Image, dots: list[tuple[int, int]]) -> str:
    """Blend a blue-to-red colour map of a blurred dot map over the image, as the real heatmap does."""
    acc = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(acc)
    for x, y in dots:
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=255)
    acc = acc.filter(ImageFilter.GaussianBlur(16))
    peak = max(acc.tobytes()) or 1
    dens = acc.point(lambda v: v * 255 // peak)
    lut = [(min(255, 2 * v), 255 - abs(2 * v - 255), max(0, 255 - 2 * v)) for v in range(256)]
    colour = Image.new("RGB", img.size)
    colour.putdata([lut[v] for v in dens.tobytes()])
    alpha = dens.point(lambda v: min(150, v * 3))
    blended = Image.composite(colour, img, alpha)
    buf = io.BytesIO()
    blended.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def vision() -> None:
    cfg = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    cams = cfg["vision"]["cameras"]
    write_json("vision_cameras.json", [{"id": c["id"], "segment_id": c["segment_id"],
                                        "view_area_m2": c["view_area_m2"], "label": c["label"], "assumed": True}
                                       for c in cams])
    write_json("vision_samples.json", [{
        "name": SAMPLE_NAME,
        "attribution": "EXAMPLE placeholder, generated, not a photo",
        "license": "CC0 (generated placeholder)",
        "source_url": None,
        "example": True,
    }])
    img, dots = placeholder()
    (OUT / "vision/samples").mkdir(parents=True, exist_ok=True)
    img.save(OUT / "vision/samples" / SAMPLE_NAME, "PNG", optimize=True)
    cam = cams[0]
    seg = segment(cam["segment_id"])
    density = EXAMPLE_COUNT / cam["view_area_m2"]
    write_json("vision_count.json", {
        "camera_id": cam["id"], "segment_id": cam["segment_id"], "count": EXAMPLE_COUNT,
        "density_ppm2": round(density, 2),
        "persons_on_segment": round(density * seg["length_m"] * seg["width_m"]),
        "level": level(density, cfg["crowd"]["bands_ppm2"]),
        "heatmap_png_b64": heatmap(img, dots),
        "model": "EXAMPLE (no model run; real: DM-Count, MIT)",
        "demo_image": True, "ms": EXAMPLE_MS, "example": True, "fixture_note": NOTE,
    })


def lead_time() -> None:
    write_json("lead_time_findings.json", {
        "example": False,
        "from": "docs/replay-findings.md, 'System result' (measured 2026-10-24, thresholds 2026-10-24.1)",
        "target_segment": TARGET, "event_ts": EVENT,
        "first_red": {src: red for src, (_, red) in SOURCES.items()},
    })


def main() -> None:
    for src in SOURCES:
        write_json(f"impact_counterfactual_{src}.json", impact(src))
    vision()
    lead_time()


if __name__ == "__main__":
    main()
