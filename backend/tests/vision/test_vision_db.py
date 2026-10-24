"""DB-backed: a camera count becomes the live, non-simulated crowd row of its segment (no model needed)."""
from datetime import datetime

from app import db as appdb
from app.crowd.simulator import IST
from app.vision import service

HOUR = datetime(2020, 1, 1, 9, tzinfo=IST)  # far from any real live hour; the row is deleted afterwards


def test_persist_upserts_camera_row_and_reruns_risk(db):
    cam = service.camera("CAM-KATRA-GATE")
    with appdb.conn() as c:
        try:
            length_m, width_m = service.segment_area(c, cam["segment_id"])
            crowd = service.measure(c, cam, 450.0)  # 450 people in the 150 m2 view = 3.0 /m2
            assert crowd == {"density_ppm2": 3.0, "persons_on_segment": round(3.0 * length_m * width_m), "level": 1}
            assert isinstance(service.persist(c, cam, crowd, HOUR), int)
            service.persist(c, cam, crowd, HOUR)  # idempotent upsert
            rows = c.execute("""SELECT persons, density_ppm2, level, simulated, scenario FROM segment_crowd
                                WHERE segment_id = %s AND mode = 'live' AND ts = %s""",
                             (cam["segment_id"], HOUR)).fetchall()
            assert len(rows) == 1
            r = rows[0]
            assert r["simulated"] is False and r["scenario"] == {"source": "camera", "camera_id": "CAM-KATRA-GATE"}
            assert (r["persons"], r["level"]) == (crowd["persons_on_segment"], 1)
        finally:
            c.rollback()
