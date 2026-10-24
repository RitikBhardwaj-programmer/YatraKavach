"""Build EXAMPLE API responses for the console (docs/api-fixtures/). Not real results.

Geometry is the real segment file; rain is the archived GFS replay rain in data/replay/.
Hazard levels follow the rules in docs/PLAN.md with values from config/thresholds.yaml, in a
simplified form (workstream A owns the real engine). Crowd numbers are SIMULATED with a seeded
generator. Alerts, approvals, audit rows and CAP XML are illustrative examples of the contract.

Run from the repo root:  python docs/api-fixtures/build_fixtures.py   (needs PyYAML)
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = "gfs_seamless"
POINTS = ("katra", "adhkuwari", "bhawan")
TZ = "+05:30"
LEVELS = ("GREEN", "YELLOW", "ORANGE", "RED")
# Fixture "now" for alert/audit snapshots and the replay segment snapshot.
SNAPSHOT = "2025-08-26T12:00"
LIVE_EXAMPLE = "2025-08-20T12:00"   # a quiet replay hour reused as the LIVE example (not live data)
NOTE = ("EXAMPLE fixture for building the console; not a real result. Rain: Open-Meteo GFS historical "
        "forecast (CC BY 4.0). Trails: OpenStreetMap (ODbL). Elevation: Copernicus DEM via Open-Meteo. "
        "Crowd numbers are SIMULATED.")
SEED = 20250826
OFFICERS = [
    {"id": "off-1", "name": "Demo Officer A (Katra control room)", "role": "officer"},
    {"id": "off-2", "name": "Demo Officer B (SDRF liaison)", "role": "officer"},
    {"id": "sen-1", "name": "Demo Senior Officer (Incident Commander)", "role": "senior"},
]


def iso(ts: str) -> str:
    return f"{ts}:00{TZ}"


def load_rain() -> tuple[list[str], dict[str, dict[str, Any]]]:
    rain = {}
    for p in POINTS:
        rain[p] = json.loads((ROOT / f"data/replay/rain_{p}_{SOURCE}.json").read_text())
    times = rain[POINTS[0]]["time"]
    assert all(r["time"] == times for r in rain.values()), "rain files must share one time axis"
    return times, rain


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_point(coords: list[list[float]], rain: dict[str, dict[str, Any]]) -> str:
    lon, lat = coords[len(coords) // 2]
    return min(POINTS, key=lambda p: haversine_m(lat, lon, rain[p]["lat"], rain[p]["lon"]))


def raw_hazard(precip: list[float], i: int, slope: float | None, th: dict[str, Any]) -> tuple[int, dict]:
    """Level before hysteresis, and the drivers that explain it."""
    def window(h: int) -> float:
        return sum(precip[max(0, i - h + 1): i + 1])

    r24, r15d, r3 = window(24), window(15 * 24), window(3)
    curve = th["id_curve"]
    id_hit = next((d for d in curve["durations_h"]
                   if window(d) / d >= curve["a"] * d ** curve["b"]), None)
    daily = th["daily_watch_mm"]
    if r24 >= th["red_r24_mm"]:
        level, rule = 3, "RED_R24"
    elif id_hit is not None:
        level, rule = 3, f"RED_ID_{id_hit}H"
    elif r24 >= th["orange_r24_mm"]:
        level, rule = 2, "ORANGE_R24"
    elif r24 >= 2 * daily and r15d >= th["antecedent_15d_mm"]:
        level, rule = 2, "ORANGE_R24_ANTECEDENT"
    elif r24 >= daily:
        level, rule = 1, "YELLOW_R24"
    elif r15d >= th["antecedent_15d_mm"]:
        level, rule = 1, "YELLOW_R15D"
    else:
        level, rule = 0, "BELOW_WATCH"
    raised = slope is not None and slope >= th["steep_slope_deg"] and 1 <= level < 3
    if raised:
        level += 1
    drivers = {"rule": rule, "r24_mm": round(r24, 1), "r24_threshold": daily,
               "ratio": round(r24 / daily, 1), "r15d_mm": round(r15d, 1),
               "r15d_threshold": th["antecedent_15d_mm"], "r3_mm": round(r3, 1),
               "slope_deg": slope, "slope_raise": raised, "steep_slope_deg": th["steep_slope_deg"]}
    if id_hit is not None:
        drivers["id_duration_h"] = id_hit
    return level, drivers


def hazard_series(precip: list[float], slope: float | None, th: dict[str, Any]) -> list[tuple[int, dict]]:
    out, level, below = [], 0, 0
    for i in range(len(precip)):
        raw, drivers = raw_hazard(precip, i, slope, th)
        if raw >= level:
            level, below = raw, 0
        else:
            below += 1
            if below >= th["hysteresis_updates"]:
                level, below = raw, 0
        drivers["held_by_hysteresis"] = raw < level
        out.append((level, drivers))
    return out


def diurnal(hour: int) -> float:
    """SIMULATED share of peak load by hour of day: low at night, peak around midday."""
    return 0.15 + 0.85 * math.exp(-((hour - 12.5) / 4.0) ** 2)


def crowd_level(density: float, bands: list[float]) -> int:
    return sum(density >= b for b in bands)


def crowd_series(props: dict, times: list[str], bands: list[float], rng: random.Random) -> list[dict]:
    base = {"VD-TRUNK": 1500, "VD-OLD": 900, "VD-HIMKOTI": 1100}[props["route_id"]]
    if props["kind"] == "junction":
        base *= 5   # holding area at the Adhkuwari junction
    area = props["length_m"] * props["width_m"]
    rows = []
    for t in times:
        persons = int(base * diurnal(int(t[11:13])) * rng.uniform(0.8, 1.2))
        density = persons / area
        rows.append({"persons": persons, "density_ppm2": round(density, 3),
                     "level": crowd_level(density, bands)})
    return rows


def fuse(hazard: int, crowd: int) -> int:
    if hazard >= 2 and crowd >= 1:
        return min(3, hazard + 1)
    return max(hazard, crowd)


def build_history(segments: list[dict], times: list[str], rain: dict, th: dict) -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    history = {}
    for f in segments:
        p = f["properties"]
        haz = hazard_series(rain[p["rain_point"]]["precip_mm"], p["terrain_slope_deg"], th["hazard"])
        crowd = crowd_series(p, times, th["crowd"]["bands_ppm2"], rng)
        rows = []
        for t, (hl, hd), c in zip(times, haz, crowd):
            drivers = {**hd, "rain_point": p["rain_point"], "source": SOURCE, "persons": c["persons"],
                       "density_ppm2": c["density_ppm2"], "crowd_simulated": True}
            rows.append({"ts": iso(t), "hazard_level": hl, "crowd_level": c["level"],
                         "risk_level": fuse(hl, c["level"]), "drivers": drivers})
        history[p["id"]] = rows
    return history


def snapshot(segments: list[dict], history: dict, times: list[str], ts: str, mode: str) -> dict:
    i = times.index(ts)
    feats = []
    for f in segments:
        row = history[f["properties"]["id"]][i]
        d = row["drivers"]
        props = {**f["properties"], "ts": row["ts"], "mode": mode, "hazard_level": row["hazard_level"],
                 "crowd_level": row["crowd_level"], "risk_level": row["risk_level"],
                 "persons": d["persons"], "density_ppm2": d["density_ppm2"], "drivers": d,
                 "simulated_crowd": True, "thresholds_version": THRESHOLDS["version"]}
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": props})
    return {"type": "FeatureCollection", "fixture_note": NOTE, "example": True,
            "attribution": SEGMENTS["attribution"], "features": feats}


# ---- alerts, audit, CAP -------------------------------------------------------------------

def first_hour(history: dict, ids: list[str], times: list[str], level: int, since: str) -> str:
    """First hour from `since` at which at least half of the route's segments reach `level`."""
    for i, t in enumerate(times):
        if t >= since and 2 * sum(history[s][i]["risk_level"] >= level for s in ids) >= len(ids):
            return t
    raise ValueError(f"no hour from {since} reaches level {level} for {ids}")


def plus_min(ts: str, minutes: int) -> str:
    return (datetime.fromisoformat(ts) + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M")


def canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def audit_chain(events: list[dict]) -> list[dict]:
    rows, prev = [], "0" * 64
    for n, e in enumerate(sorted(events, key=lambda e: e["ts"]), start=1):
        row = {"id": n, **e, "thresholds_version": THRESHOLDS["version"], "prev_hash": prev}
        row["hash"] = hashlib.sha256((prev + canonical(row)).encode()).hexdigest()
        prev = row["hash"]
        rows.append(row)
    return rows


ACTION_EN = {
    2: "Hold pilgrims at {up}; stop ascent beyond {seg}",
    3: "Clear segments {seg} ({where}); move pilgrims to the nearest designated shelter",
}
# Example translations, needs native-speaker review (workstream B owns the real templates).
TEXT = {
    "en-IN": {2: "EXERCISE. Landslide warning on {route}. Hold pilgrims at {up}. Do not climb beyond {seg}.",
              3: "EXERCISE. Severe landslide risk on {route}. Leave {seg} now and go to the nearest shelter."},
    "hi-IN": {2: "अभ्यास। {route} पर भूस्खलन की चेतावनी। यात्री {up} पर रुकें। {seg} से आगे न चढ़ें।",
              3: "अभ्यास। {route} पर भूस्खलन का गंभीर खतरा। {seg} तुरंत खाली करें और निकटतम आश्रय में जाएँ।"},
    "ur-IN": {2: "مشق۔ {route} پر لینڈ سلائیڈ کی وارننگ۔ یاتری {up} پر رکیں۔ {seg} سے آگے نہ چڑھیں۔",
              3: "مشق۔ {route} پر لینڈ سلائیڈ کا شدید خطرہ۔ {seg} فوراً خالی کریں اور قریب ترین پناہ گاہ میں جائیں۔"},
}


def buffer_polygon(segments: list[dict], ids: list[str], metres: float = 100.0) -> list[list[float]]:
    """Approximate 100 m buffer: convex hull of 12-point circles around every vertex (example only)."""
    pts = []
    for f in segments:
        if f["properties"]["id"] not in ids:
            continue
        for lon, lat in f["geometry"]["coordinates"]:
            dlat = metres / 111320.0
            dlon = metres / (111320.0 * math.cos(math.radians(lat)))
            pts += [(lon + dlon * math.cos(a), lat + dlat * math.sin(a))
                    for a in (k * math.pi / 6 for k in range(12))]
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return [[round(x, 5), round(y, 5)] for x, y in hull + [hull[0]]]


def cap_xml(alert: dict, route: str, up: str, seg_label: str, polygon: list[list[float]]) -> str:
    sev = {2: "Severe", 3: "Extreme"}[alert["level"]]
    poly = " ".join(f"{lat},{lon}" for lon, lat in polygon)   # CAP: lat,lon pairs
    infos = []
    for lang, tpl in TEXT.items():
        text = tpl[alert["level"]].format(route=route, up=up, seg=seg_label)
        infos.append(f"""  <info>
    <language>{lang}</language>
    <category>Geo</category>
    <event>Landslide risk on pilgrim track</event>
    <urgency>Immediate</urgency>
    <severity>{sev}</severity>
    <certainty>Likely</certainty>
    <senderName>YatraKavach demo (EXAMPLE)</senderName>
    <headline>{LEVELS[alert['level']]}: {seg_label}</headline>
    <description>{text}</description>
    <instruction>{alert['proposed_action']}</instruction>
    <expires>{alert['expires_at']}</expires>
    <area>
      <areaDesc>{route}: {seg_label} (approx. 100 m buffer)</areaDesc>
      <polygon>{poly}</polygon>
    </area>
  </info>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- EXAMPLE fixture, not a real alert. Hindi and Urdu text needs native-speaker review. -->
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>yatrakavach-{alert['id']}</identifier>
  <sender>yatrakavach@example.invalid</sender>
  <sent>{alert['created_at']}</sent>
  <status>Exercise</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
{chr(10).join(infos)}
</alert>
"""


def build_alerts(segments: list[dict], history: dict, times: list[str]) -> tuple[list, list, dict]:
    th = THRESHOLDS["alerts"]
    old = [f["properties"]["id"] for f in segments if f["properties"]["route_id"] == "VD-OLD"]
    him = [f["properties"]["id"] for f in segments if f["properties"]["route_id"] == "VD-HIMKOTI"]
    since = plus_min(SNAPSHOT, -36 * 60)
    t_orange = first_hour(history, old, times, th["propose_at_risk_level"], since)
    t_red = first_hour(history, old, times, 3, since)
    t_him = first_hour(history, him, times, 3, since)
    up = "Adhkuwari (track junction)"
    specs = [  # (id, ids, level, created, route, seg_label, transitions)
        ("A-0001", old, 2, t_orange, "old track", f"{old[0]}",
         [("off-1", "PROPOSED", "APPROVED", 4, "Rain over watch level since early morning."),
          ("system", "APPROVED", "SENT", 5, "Sent to SIMULATED channels (SMS, SACHET, cell broadcast).")]),
        ("A-0002", old, 3, t_red, "old track", f"{old[0]} to {old[-1]}",
         [("off-1", "PROPOSED", "PROPOSED", 6, "First approval; RED needs a second officer.")]),
        ("A-0003", him, 3, t_him, "Himkoti track", f"{him[0]} to {him[-1]}",
         [("system", "PROPOSED", "ESCALATED", th["escalate_after_min"],
           f"No officer action within {th['escalate_after_min']} min; escalated to senior officer.")]),
    ]
    alerts, events, caps = [], [], {}
    for aid, ids, level, created, route, seg_label, steps in specs:
        need = th["red_needs_approvals"] if level == 3 else th["orange_needs_approvals"]
        action = ACTION_EN[level].format(up=up, seg=seg_label, where=route)
        alert = {"id": aid, "segment_ids": ids, "level": level, "level_name": LEVELS[level],
                 "proposed_action": action, "state": "PROPOSED", "created_at": iso(created),
                 "updated_at": iso(created), "approvals": [], "needs_approvals": need, "mode": "replay",
                 "expires_at": iso(plus_min(created, th["expires_after_min"])), "example": True}
        snap = {s: history[s][times.index(created)]["risk_level"] for s in ids}
        events.append({"ts": iso(created), "alert_id": aid, "actor": "system", "from_state": None,
                       "to_state": "PROPOSED", "reason": f"risk_level >= {th['propose_at_risk_level']}",
                       "input_snapshot": {"risk_level": snap}, "message": action})
        for actor, frm, to, mins, reason in steps:
            ts = iso(plus_min(created, mins))
            if actor != "system":
                alert["approvals"].append({"officer": actor, "ts": ts})
            alert["state"], alert["updated_at"] = to, ts
            events.append({"ts": ts, "alert_id": aid, "actor": actor, "from_state": frm, "to_state": to,
                           "reason": reason, "input_snapshot": None, "message": action})
        alerts.append(alert)
        caps[aid] = cap_xml(alert, route, up, seg_label, buffer_polygon(segments, ids))
    return alerts, audit_chain(events), caps


def write(name: str, obj: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main() -> None:
    times, rain = load_rain()
    segments = SEGMENTS["features"]
    for f in segments:
        p = f["properties"]
        p.setdefault("susceptibility", None)
        p.setdefault("past_slide", False)
        p["rain_point"] = nearest_point(f["geometry"]["coordinates"], rain)
    history = build_history(segments, times, rain, THRESHOLDS)
    alerts, audit, caps = build_alerts(segments, history, times)

    write("health.json", {"status": "ok"})
    write("officers.json", OFFICERS)
    write("segments_replay.json", snapshot(segments, history, times, SNAPSHOT, "replay"))
    write("segments_live.json", snapshot(segments, history, times, LIVE_EXAMPLE, "live"))
    write("replay_timeline.json", {
        "start": iso(times[0]), "end": iso(times[-1]), "step_minutes": 60, "source": SOURCE,
        "events": [
            {"ts": iso("2025-08-14T00:00"), "label": "14 Aug: Chasoti cloudburst, Machail route (off this map; date only)"},
            {"ts": iso("2025-08-26T12:00"), "label": "26 Aug ~12:00: Board says old track closed"},
            {"ts": iso("2025-08-26T14:40"), "label": "26 Aug 14:40: Adhkuwari landslide, old track"},
        ]})
    for sid, rows in history.items():
        write(f"history/{sid}.json", rows)
    write("alerts.json", alerts)
    for a in alerts:
        write(f"cap/{a['id']}.xml", caps[a["id"]])
        write(f"audit/{a['id']}.json", [r for r in audit if r["alert_id"] == a["id"]])
    write("audit.json", audit)
    write("audit_verify.json", {"ok": True, "rows": len(audit)})
    write("replay_run.json", {"ok": True, "mode": "replay", "start": iso(times[0]), "end": iso(times[-1]),
                              "segments": len(segments), "alerts_proposed": len(alerts), "example": True})
    # Example responses for the POST/PATCH endpoints: each returns the alert.
    a2 = next(a for a in alerts if a["id"] == "A-0002")
    approved = {**a2, "state": "APPROVED", "updated_at": iso(plus_min(SNAPSHOT, 2)),
                "approvals": a2["approvals"] + [{"officer": "off-2", "ts": iso(plus_min(SNAPSHOT, 2))}]}
    write("alert_approve_example.json", approved)
    write("alert_break_glass_example.json", {**a2, "state": "SENT", "updated_at": iso(plus_min(SNAPSHOT, 1)),
                                             "break_glass": {"officer": "sen-1", "reason": "Example reason"}})
    print(f"wrote fixtures: {len(segments)} segments, {len(times)} hours, {len(alerts)} alerts, "
          f"{len(audit)} audit rows; snapshot {SNAPSHOT}")
    for a in alerts:
        print(f"  {a['id']} {LEVELS[a['level']]} created {a['created_at']} state {a['state']}")


THRESHOLDS = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
SEGMENTS = json.loads((ROOT / "data/segments_vaishno_devi.geojson").read_text())

if __name__ == "__main__":
    main()
