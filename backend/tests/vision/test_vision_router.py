import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.vision import service

client = TestClient(app)


def test_cameras():
    r = client.get("/api/vision/cameras")
    assert r.status_code == 200
    assert r.json()[0]["id"] == "CAM-KATRA-GATE" and r.json()[0]["assumed"] is True


def test_samples_list_shape():
    r = client.get("/api/vision/samples")
    assert r.status_code == 200
    for s in r.json():
        assert set(s) == {"name", "attribution", "license", "source_url"}


def test_unknown_sample_image_404():
    assert client.get("/api/vision/samples/does-not-exist.jpg").status_code == 404


def test_count_unknown_camera_404():
    r = client.post("/api/vision/count", params={"camera_id": "CAM-NOPE"}, data={"sample": "x.jpg"})
    assert r.status_code == 404


def test_count_unknown_sample_404():
    r = client.post("/api/vision/count", params={"camera_id": "CAM-KATRA-GATE"}, data={"sample": "x.jpg"})
    assert r.status_code == 404


def test_count_unreadable_image_422():
    r = client.post("/api/vision/count", params={"camera_id": "CAM-KATRA-GATE"},
                    files={"image": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 422


def test_count_needs_image_or_sample_422():
    assert client.post("/api/vision/count", params={"camera_id": "CAM-KATRA-GATE"}).status_code == 422


def test_count_sample_with_db(model, db):
    names = [s["name"] for s in service.samples()]
    if not names:
        pytest.skip("no demo samples in backend/app/vision/samples yet")
    r = client.post("/api/vision/count", params={"camera_id": "CAM-KATRA-GATE"}, data={"sample": names[0]})
    assert r.status_code == 200, r.text
    body = r.json()
    for k in ("camera_id", "segment_id", "count", "density_ppm2", "persons_on_segment", "level",
              "heatmap_png_b64", "model", "demo_image", "ms"):
        assert k in body
    assert body["demo_image"] is True and body["count"] >= 0 and 0 <= body["level"] <= 3


def test_count_persist_writes_live_camera_row(model, db):
    names = [s["name"] for s in service.samples()]
    if not names:
        pytest.skip("no demo samples in backend/app/vision/samples yet")
    from app import db as appdb
    r = client.post("/api/vision/count", params={"camera_id": "CAM-KATRA-GATE", "persist": "true"},
                    data={"sample": names[0]})
    assert r.status_code == 200, r.text
    with appdb.conn() as c:
        row = c.execute("""SELECT persons, level, simulated, scenario FROM segment_crowd
                           WHERE segment_id = 'VD-TRUNK-01' AND mode = 'live' AND ts = %s""",
                        (service.current_hour(),)).fetchone()
    assert row is not None and row["simulated"] is False
    assert row["scenario"] == {"source": "camera", "camera_id": "CAM-KATRA-GATE"}
    assert row["persons"] == r.json()["persons_on_segment"] and row["level"] == r.json()["level"]
