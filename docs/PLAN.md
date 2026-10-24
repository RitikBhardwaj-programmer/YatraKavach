# YatraKavach build plan and interface contract

Hack for Social Cause 2027 (team kavach, HSC|JK|00032). Theme 11: Disaster Mitigation & Resilience.
Deadline: submit on the MY Bharat portal by **26 Oct 2026** (official: 27 Oct; the PDF says 15 Oct).

## Goal
A working prototype that joins hazard risk and crowd load per ~500 m segment of the Vaishno Devi
tracks, proposes an action, and sends a multilingual CAP alert only after a named officer approves it.
Every step is logged. Pitch: "The warning existed. The decision did not."

## Scope
- Route: Vaishno Devi only (35 segments in `data/segments_vaishno_devi.geojson`). Machail is a stretch goal.
- Replay: 10-28 Aug 2025 rain in `data/replay/` (see `docs/replay-findings.md`).
- Built for real: segments, rain ingest (live + replay), scoring, crowd fusion, approval state machine,
  hash-chained audit log, CAP 1.2 XML, officer console map.
- Simulated and labelled "SIMULATED" in UI and API: RFID gate counts, sensors, SMS/SACHET/cell broadcast.

## Stack
Python 3.12, FastAPI, PostgreSQL 16 + PostGIS 3 (Docker), psycopg 3, pytest. Frontend: static
HTML + JS + MapLibre GL JS (no build step), served by FastAPI at `/`. MIT licence.

## Repository layout and ownership
| Path | Owner (workstream) |
|---|---|
| `db/init/001_schema.sql`, `docker-compose.yml`, `backend/app/main.py`, `backend/app/db.py`, `config/thresholds.yaml` | shared skeleton (already written; change only by note in PR description) |
| `backend/app/hazard/`, `backend/tests/hazard/`, `scripts/load_*.py`, `db/init/010-019_*.sql` | **A: hazard** |
| `backend/app/crowd/`, `backend/app/risk/`, `backend/app/alerts/`, `backend/tests/{crowd,risk,alerts}/`, `db/init/020-029_*.sql` | **B: crowd + alerts** |
| `frontend/`, `docs/api-fixtures/` (read only for others) | **C: console** |

Each workstream works on its own branch and opens its own PR. Never edit another workstream's paths.

## Database contract (`db/init/001_schema.sql`)
- `segments(id, route_id, route_name, seq, geom LineString 4326, length_m, width_m, kind, landmark, elev_m, terrain_slope_deg, grade_deg, susceptibility)`
- `rain_hourly(point, ts, precip_mm, source, mode)`; mode = `live` or `replay`
- `segment_hazard(segment_id, ts, mode, level, drivers jsonb, thresholds_version)` — written by A
- `segment_crowd(segment_id, ts, mode, persons, density_ppm2, level, simulated)` — written by B
- `segment_risk(segment_id, ts, mode, hazard_level, crowd_level, risk_level, drivers jsonb)` — written by B
- `alerts(...)`, `alert_approvals(...)`, `audit_log(...)`, `officers(...)` — written by B
Levels everywhere: 0 GREEN, 1 YELLOW (watch), 2 ORANGE (warning), 3 RED (severe).

## Rules (versioned in `config/thresholds.yaml`)
Hazard per segment (A). Rain point = nearest of katra / adhkuwari / bhawan.
- R24 = rain in last 24 h, R15d = rain in last 15 days, R3 = rain in last 3 h.
- YELLOW: R24 >= 14.35 mm or R15d >= 53 mm (Shah et al. 2024, NH-44 values).
- ORANGE: R24 >= 2 x 14.35 mm and R15d >= 53 mm, or R24 >= 72 mm.
- RED: R24 >= 144 mm (Dahal & Hasegawa 2008), or mean intensity over D hours >= 73.90 x D^-0.79 mm/h for D in {1, 3, 6, 12, 24}.
- Segment factor: if terrain_slope_deg >= 40 or susceptibility >= 3 (or a past slide is recorded), raise a
  level >= 1 by one step (max 3).
- Hysteresis: a level drops only after 2 consecutive updates below it.
- `drivers` must explain the level in words and numbers, e.g. `{"r24_mm": 63.9, "r24_threshold": 14.35, "ratio": 4.5, "slope_deg": 39.0, "rule": "ORANGE_R24"}`.

Crowd per segment (B): density = persons / (length_m x width_m). <2 GREEN, 2-4 YELLOW, 4-6 ORANGE, >=6 RED
(persons/m2; 2-3 and 6 sourced, 4 interpolated).

Risk fusion (B): risk = max(hazard, crowd); if hazard >= 2 and crowd >= 1, risk = min(3, hazard + 1).

## Alert workflow (B)
States: PROPOSED -> APPROVED -> SENT -> ACKED; PROPOSED -> REJECTED; PROPOSED -> ESCALATED (no action in
10 min) -> APPROVED/REJECTED; any open state -> CANCELLED; SENT/ACKED -> EXPIRED (after `expires_at`); PROPOSED/ESCALATED -> CANCELLED by
the system (action WITHDRAW) when the risk condition cleared before anyone acted. Sending is SIMULATED and
happens as soon as the approvals are complete.
- Auto-proposal when risk_level >= 2 on a segment with no covering alert. An alert covers its segments from
  its `trigger_ts` (risk time, so replay-safe) until their risk falls below the alert's own level. Contiguous
  segments of one route at one level form one alert; a RED over an ORANGE references it (CAP Update if sent).
  Action text from templates:
  ORANGE "Hold pilgrims at <upstream landmark>; stop ascent beyond <segment landmark>";
  RED "Clear segment <id> (<landmark>); move pilgrims to <nearest shelter>".
- RED alerts need two approvals from two different officers. ORANGE needs one.
- Break-glass: a `senior` officer can move PROPOSED -> SENT with a written reason (logged).
- Audit: every transition appends a row with actor, from/to state, reason, input snapshot, thresholds
  version, message text, `prev_hash`, `hash` = sha256(prev_hash + canonical JSON of the row). No UPDATE or
  DELETE (DB trigger). `GET /api/audit/verify` recomputes the chain.
- CAP 1.2 XML per alert: `status=Exercise`, `msgType` Alert/Update/Cancel with `references`,
  one `<info>` per language (en-IN, hi-IN, ur-IN) from pre-written templates, `<area>` polygon =
  100 m buffer of the segments. Templates in `backend/app/alerts/templates/`. Dogri/Kashmiri: TODO, need a native speaker.

## HTTP API contract (all JSON unless stated; times ISO 8601 with +05:30)
- `GET /api/health` -> `{"status":"ok"}`
- `GET /api/segments?mode=live|replay&at=<ts>&source=<optional>` -> GeoJSON FeatureCollection; each feature's properties =
  segment columns + `hazard_level, crowd_level, risk_level, persons, density_ppm2, drivers, simulated_crowd`
- `GET /api/replay/timeline` -> `{"start","end","step_minutes":60,"events":[{"ts","label"}]}`
- `GET /api/segments/{id}/history?mode=&from=&to=&source=<optional>` -> `[{"ts","hazard_level","crowd_level","risk_level","drivers"}]`
- `GET /api/alerts?state=` -> list of alerts `{"id","segment_ids","level","proposed_action","state","created_at","updated_at","approvals":[{"officer","ts"}],"needs_approvals","mode"}`
  (+ read-only extras: `source`, `trigger_ts`, `sent_at`, `expires_at`, `references_alert_id`, `delivery`)
- `POST /api/alerts/{id}/approve|reject|cancel|ack` body `{"officer_id","reason"?}` -> the alert
- `POST /api/alerts/{id}/break-glass` body `{"officer_id","reason"}` -> the alert
- `PATCH /api/alerts/{id}` body `{"officer_id","proposed_action"}` (edit before approval) -> the alert
- `GET /api/alerts/{id}/cap.xml` -> `application/cap+xml`
- `GET /api/audit?alert_id=` -> rows; `GET /api/audit/verify` -> `{"ok":true,"rows":n}` or first broken row
- `GET /api/officers` -> demo officers `[{"id","name","role"}]`
- `POST /api/replay/run?source=gfs_seamless&until=<ts>` -> recompute hazard + crowd + risk for the replay window,
  then walk alert proposals up to `until` (the replay clock; default: end of window). Idempotent.
Example responses live in `docs/api-fixtures/*.json` so the console can be built before the backend.

## Verification (definition of done)
- `docker compose up` starts db + api; `/api/health` ok; console loads at `http://localhost:8000/`.
- `pytest` passes (pure logic tests need no DB; DB tests skip with a clear message if no DB).
- Replay of 26 Aug 2025: Adhkuwari old-track segments reach ORANGE before 12:00 IST and RED before 14:40
  in at least the GFS source; an alert is proposed, approved by two officers, CAP XML validates against the
  structure above, audit chain verifies.
- README: setup, architecture diagram, data sources and licences, limitations, AI-use disclosure.

## Day plan
- Day 1 (23-24 Oct): data spike (done), skeleton (done), workstreams A, B, C in parallel.
- Day 2 (25 Oct): merge A + B + C, end-to-end replay, fix, review.
- Day 3 (26 Oct): README, deck (6-7 slides), video, Annexure 1, submit.
