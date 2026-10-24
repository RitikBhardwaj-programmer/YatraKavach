"""CAP 1.2 XML for one alert (pure, no DB). Contract: docs/PLAN.md "Alert workflow".

status is always Exercise (prototype). msgType: Cancel for a cancelled alert, Update when the alert upgrades
an earlier alert that was sent, else Alert. One <info> per language; <area> polygon = buffer of the segments.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

from pyproj import Transformer
from shapely.geometry import LineString, Polygon
from shapely.ops import transform, unary_union

from app.alerts import templates
from app.risk.config import thresholds

NS = "urn:oasis:names:tc:emergency:cap:1.2"
IST = timezone(timedelta(hours=5, minutes=30))
SENDER = "yatrakavach-prototype"            # no real issuing authority: this is an exercise
BUFFER_M = float(thresholds()["alerts"]["cap_area_buffer_m"])
UTM_43N = "EPSG:32643"                      # metric CRS for the Vaishno Devi area (74.9 E)
_SEVERITY = {2: ("Expected", "Severe", "Likely", "Avoid"), 3: ("Immediate", "Extreme", "Likely", "Evacuate")}


@dataclass(frozen=True)
class CapInput:
    alert_id: int
    mode: str
    level: int
    state: str
    segment_ids: list[str]
    proposed_action: str
    created_at: datetime
    sent_at: datetime | None
    expires_at: datetime | None
    reference: tuple[int, datetime] | None   # (alert id, sent time) of the alert this one updates
    updated_at: datetime | None = None       # time of the last transition (the cancel time for a Cancel)


def identifier(alert_id: int, mode: str) -> str:
    return f"yatrakavach-{mode}-alert-{alert_id}"


def cap_time(ts: datetime) -> str:
    """CAP dateTime: no fractional seconds, explicit offset."""
    return ts.astimezone(IST).replace(microsecond=0).isoformat()


def area_polygon(lines: list[list[tuple[float, float]]], buffer_m: float = BUFFER_M) -> list[tuple[float, float]]:
    """Closed ring of (lat, lon) for the union of `buffer_m` buffers around the segment lines (lon, lat)."""
    fwd = Transformer.from_crs("EPSG:4326", UTM_43N, always_xy=True).transform
    back = Transformer.from_crs(UTM_43N, "EPSG:4326", always_xy=True).transform
    shape = unary_union([transform(fwd, LineString(c)).buffer(buffer_m) for c in lines]).simplify(5.0)
    if not isinstance(shape, Polygon):  # far-apart segments: keep the outline of all of them
        shape = shape.convex_hull
    ring = list(transform(back, Polygon(shape.exterior)).exterior.coords)
    return [(round(lat, 6), round(lon, 6)) for lon, lat in ring]


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = text
    return el


def msg_type(a: CapInput) -> str:
    if a.state == "CANCELLED":
        return "Cancel"
    return "Update" if a.reference else "Alert"


def build(a: CapInput, ctx: dict[str, str], polygon: list[tuple[float, float]]) -> bytes:
    kind = msg_type(a)
    ident = identifier(a.alert_id, a.mode) + ("-cancel" if kind == "Cancel" else "")
    if kind == "Cancel" and a.sent_at is None:
        raise ValueError("a Cancel needs the original alert to have been sent")
    # A Cancel is a new message: its <sent> is the cancel time; <references> points at the original send.
    sent = (a.updated_at or a.sent_at) if kind == "Cancel" else (a.sent_at or a.created_at)
    root = ET.Element(f"{{{NS}}}alert")
    _sub(root, "identifier", ident)
    _sub(root, "sender", SENDER)
    _sub(root, "sent", cap_time(sent))
    _sub(root, "status", "Exercise")
    _sub(root, "msgType", kind)
    _sub(root, "scope", "Public")
    _sub(root, "note", "SIMULATED prototype exercise (YatraKavach). Not an official warning. "
                       f"Mode: {a.mode}. Workflow state: {a.state}. Delivery channels are SIMULATED.")
    if kind == "Cancel":
        _sub(root, "references", f"{SENDER},{identifier(a.alert_id, a.mode)},{cap_time(a.sent_at)}")
    elif kind == "Update":
        ref_id, ref_sent = a.reference
        _sub(root, "references", f"{SENDER},{identifier(ref_id, a.mode)},{cap_time(ref_sent)}")
    urgency, severity, certainty, response = _SEVERITY[a.level]
    key = "cancel" if kind == "Cancel" else a.level
    poly_text = " ".join(f"{lat},{lon}" for lat, lon in polygon)
    for lang in templates.LANGUAGES:
        text = templates.cap_text(lang, key, ctx)
        info = _sub(root, "info")
        _sub(info, "language", lang)
        _sub(info, "category", "Geo")
        _sub(info, "event", templates.event_name(lang))
        _sub(info, "responseType", "AllClear" if kind == "Cancel" else response)
        _sub(info, "urgency", "Past" if kind == "Cancel" else urgency)
        _sub(info, "severity", "Minor" if kind == "Cancel" else severity)
        _sub(info, "certainty", "Observed" if kind == "Cancel" else certainty)
        if a.expires_at:
            _sub(info, "expires", cap_time(a.expires_at))
        _sub(info, "senderName", "YatraKavach prototype (exercise)")
        for tag in ("headline", "description", "instruction"):
            _sub(info, tag, text[tag])
        param = _sub(info, "parameter")
        _sub(param, "valueName", "officer_action")
        _sub(param, "value", a.proposed_action)
        area = _sub(info, "area")
        _sub(area, "areaDesc", f"Vaishno Devi track, segments {ctx['segments']} ({int(BUFFER_M)} m buffer)")
        _sub(area, "polygon", poly_text)
    ET.register_namespace("", NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
