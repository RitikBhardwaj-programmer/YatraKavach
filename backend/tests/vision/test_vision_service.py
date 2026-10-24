from datetime import datetime

import pytest

from app.crowd.simulator import IST
from app.risk.config import thresholds
from app.vision import service

BANDS = thresholds()["crowd"]["bands_ppm2"]


def test_camera_from_config_is_assumed():
    cams = service.cameras()
    assert cams == [{"id": "CAM-KATRA-GATE", "segment_id": "VD-TRUNK-01", "view_area_m2": 150.0,
                     "label": "Katra gate (demo camera)", "assumed": True}]
    assert service.camera("CAM-KATRA-GATE")["segment_id"] == "VD-TRUNK-01"
    assert service.camera("nope") is None


@pytest.mark.parametrize("count, level", [(0, 0), (299, 0), (300, 1), (600, 2), (899, 2), (900, 3)])
def test_level_from_density_bands(count, level):
    # 150 m2 view: 300 people = 2.0 /m2 (YELLOW), 600 = 4.0 (ORANGE), 900 = 6.0 (RED)
    assert service.crowd_from_count(count, 150.0, 500.0, 4.0, BANDS)["level"] == level


def test_density_and_persons_on_segment():
    out = service.crowd_from_count(375.0, 150.0, 480.0, 5.0, BANDS)
    assert out["density_ppm2"] == 2.5
    assert out["persons_on_segment"] == 6000  # 2.5 /m2 x 480 m x 5 m
    assert out["level"] == 1


def test_current_hour_is_ist():
    now = datetime(2026, 10, 24, 8, 47, 13, tzinfo=IST)
    assert service.current_hour(now) == datetime(2026, 10, 24, 8, tzinfo=IST)


def test_parse_attribution_table():
    text = """# Demo photos
| file | title | author | licence | source URL |
|---|---|---|---|---|
| crowd_a.jpg | Crowd at a fair | Some Author | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:A.jpg |
| notes | ignored | x | y | z |
"""
    assert service.parse_attribution(text) == [{
        "name": "crowd_a.jpg", "attribution": "Crowd at a fair by Some Author", "license": "CC BY-SA 4.0",
        "source_url": "https://commons.wikimedia.org/wiki/File:A.jpg"}]


def test_samples_need_the_file(tmp_path):
    (tmp_path / "ATTRIBUTION.md").write_text("| a.jpg | t | a | CC0 | u |\n| b.jpg | t | a | CC0 | u |\n")
    (tmp_path / "a.jpg").write_bytes(b"x")
    assert [s["name"] for s in service.samples(tmp_path / "ATTRIBUTION.md")] == ["a.jpg"]


def test_unlisted_sample_has_no_path():
    assert service.sample_path("../../../config/thresholds.yaml") is None
    assert service.sample_path("ATTRIBUTION.md") is None
