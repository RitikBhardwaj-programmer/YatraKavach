import re
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import pytest
from shapely.geometry import Point, Polygon

from app.alerts import cap, templates
from app.risk.config import segments_geojson
from app.risk.topology import Topology, from_geojson

NS = {"cap": cap.NS}
T0 = datetime.fromisoformat("2025-08-26T11:00:00+05:30")
FC = segments_geojson()
TOPO = Topology(from_geojson(FC))
SEGS = ["VD-OLD-01", "VD-OLD-02"]
LINES = [f["geometry"]["coordinates"] for f in FC["features"] if f["properties"]["id"] in SEGS]
CAP_TIME = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$")


def build(state="SENT", level=3, reference=None) -> ET.Element:
    a = cap.CapInput(7, "replay", level, state, SEGS, "Clear segment VD-OLD-01 to VD-OLD-02", T0,
                     T0 + timedelta(minutes=3), T0 + timedelta(hours=3), reference)
    xml = cap.build(a, templates.context(TOPO, SEGS), cap.area_polygon(LINES))
    assert xml.startswith(b"<?xml")
    return ET.fromstring(xml)


def text(el: ET.Element, path: str) -> str:
    found = el.find(path, NS)
    assert found is not None, f"missing {path}"
    return found.text


def test_root_and_required_elements():
    root = build()
    assert root.tag == f"{{{cap.NS}}}alert"
    for tag in ("identifier", "sender", "sent", "status", "msgType", "scope"):
        assert text(root, f"cap:{tag}")
    assert text(root, "cap:status") == "Exercise"
    assert text(root, "cap:msgType") == "Alert"
    assert root.find("cap:references", NS) is None
    assert CAP_TIME.match(text(root, "cap:sent"))
    assert "SIMULATED" in text(root, "cap:note")


def test_one_info_per_language_with_required_fields():
    infos = build().findall("cap:info", NS)
    assert [text(i, "cap:language") for i in infos] == ["en-IN", "hi-IN", "ur-IN"]
    for info in infos:
        for tag in ("category", "event", "urgency", "severity", "certainty", "headline", "instruction"):
            assert text(info, f"cap:{tag}")
        assert (text(info, "cap:urgency"), text(info, "cap:severity")) == ("Immediate", "Extreme")
        assert text(info, "cap:parameter/cap:valueName") == "officer_action"
        assert CAP_TIME.match(text(info, "cap:expires"))
    assert re.search("[\u0900-\u097f]", text(infos[1], "cap:headline"))  # Devanagari
    assert re.search("[\u0600-\u06ff]", text(infos[2], "cap:headline"))  # Arabic script
    assert "{" not in "".join(text(i, "cap:instruction") for i in infos)  # every placeholder filled


def test_orange_severity():
    info = build(level=2).find("cap:info", NS)
    assert (text(info, "cap:urgency"), text(info, "cap:severity"), text(info, "cap:responseType")) == \
        ("Expected", "Severe", "Avoid")


def test_polygon_closed_and_covers_segments():
    polys = [text(i, "cap:area/cap:polygon") for i in build().findall("cap:info", NS)]
    assert len(set(polys)) == 1
    pairs = [tuple(map(float, p.split(","))) for p in polys[0].split()]
    assert len(pairs) >= 4 and pairs[0] == pairs[-1]
    ring = Polygon([(lon, lat) for lat, lon in pairs])
    assert ring.is_valid
    for line in LINES:
        for lon, lat in line:
            assert ring.contains(Point(lon, lat))


def test_buffer_is_about_100_m():
    pairs = cap.area_polygon([LINES[0]])
    lat0, lon0 = LINES[0][0][1], LINES[0][0][0]
    nearest = min(((lat - lat0) * 111_000) ** 2 + ((lon - lon0) * 93_000) ** 2 for lat, lon in pairs) ** 0.5
    assert 85 <= nearest <= 115


def test_update_references_previous_alert():
    root = build(reference=(5, T0))
    assert text(root, "cap:msgType") == "Update"
    assert text(root, "cap:references") == f"{cap.SENDER},yatrakavach-replay-alert-5,{cap.cap_time(T0)}"


def test_cancel_references_original():
    root = build(state="CANCELLED")
    assert text(root, "cap:msgType") == "Cancel"
    assert text(root, "cap:identifier").endswith("-cancel")
    assert ",yatrakavach-replay-alert-7," in text(root, "cap:references")
    assert text(root.find("cap:info", NS), "cap:responseType") == "AllClear"


def test_cancel_is_sent_at_cancel_time_and_references_original_send():
    sent_at, cancelled_at = T0 + timedelta(minutes=3), T0 + timedelta(hours=1)
    a = cap.CapInput(7, "replay", 3, "CANCELLED", SEGS, "x", T0, sent_at, T0 + timedelta(hours=3), None, cancelled_at)
    root = ET.fromstring(cap.build(a, templates.context(TOPO, SEGS), cap.area_polygon(LINES)))
    assert text(root, "cap:sent") == cap.cap_time(cancelled_at)
    assert text(root, "cap:references").endswith("," + cap.cap_time(sent_at))


def test_cancel_of_never_sent_alert_is_refused():
    a = cap.CapInput(7, "replay", 3, "CANCELLED", SEGS, "x", T0, None, None, None, T0)
    with pytest.raises(ValueError):
        cap.build(a, templates.context(TOPO, SEGS), cap.area_polygon(LINES))


@pytest.mark.parametrize("lang", templates.LANGUAGES)
def test_templates_have_both_levels_and_cancel(lang):
    t = templates.load(lang)["cap"]
    assert {2, 3, "cancel"} <= set(t)
