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

Vision upgrade (24-25 Oct), one branch and PR each:
| Path | Owner |
|---|---|
| `backend/app/vision/`, `backend/tests/vision/`, `scripts/export_dmcount_onnx.py`, `scripts/eval_vision.py`, `backend/requirements.txt`, the `vision:` block of `config/thresholds.yaml` | **V: vision** |
| `backend/app/impact/`, `backend/tests/impact/`, `backend/app/crowd/simulator.py` (new optional `stop_ascent` parameter only), new test files in `backend/tests/crowd/` | **I: impact** |
| `frontend/`, `docs/api-fixtures/` | **U: console 2** |
| `docs/PLAN.md`, `backend/app/main.py`, `README.md`, `docs/replay-findings.md`, `docs/pitch/` | integration (main session) |

Each workstream works on its own branch and opens its own PR. Never edit another workstream's paths.

## Database contract (`db/init/001_schema.sql`)
- `segments(id, route_id, route_name, seq, geom LineString 4326, length_m, width_m, kind, landmark, elev_m, terrain_slope_deg, grade_deg, susceptibility, past_slide, past_slide_at)`; `past_slide_at` (011) = time of a recorded slide
- `rain_hourly(point, ts, precip_mm, source, mode)`; mode = `live` or `replay`
- `segment_hazard(segment_id, ts, mode, level, drivers jsonb, thresholds_version)` — written by A
- `segment_crowd(segment_id, ts, mode, persons, density_ppm2, level, simulated, scenario jsonb)` — written by B;
  `scenario` (021) = SIMULATED holding-area note `{scenario, held_persons, held_routes, releasing}` or NULL
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
  level >= 1 by one step (max 3). Two limits (review fixes, 2026-10-24):
  - A past slide counts only for hours after `past_slide_at`, so a replay never uses the slide it should warn about.
  - No step-up from `YELLOW_R15D` alone (`step_up_rules_excluded`): antecedent rain stays high all monsoon and
    would keep steep segments ORANGE for weeks (alert fatigue).
- Hysteresis: a level drops only after 2 consecutive updates below it.
- `drivers` must explain the level in words and numbers, e.g. `{"r24_mm": 63.9, "r24_threshold": 14.35, "ratio": 4.5, "slope_deg": 39.0, "rule": "ORANGE_R24"}`.

Crowd per segment (B): density = persons / (length_m x width_m). <2 GREEN, 2-4 YELLOW, 4-6 ORANGE, >=6 RED
(persons/m2; 2-3 and 6 sourced, 4 interpolated).

Risk fusion (B): risk = max(hazard, crowd); if hazard >= 2 and crowd >= 1, risk = min(3, hazard + 1)
(levels in `config/thresholds.yaml` `risk`).

Holding-area scenario (SIMULATED, `crowd.holding`): per leaf route and hour, ascent stops at the nearest holding
point (Katra gate, Banganga, Adhkuwari) below the first segment with hazard >= ORANGE. Ascending pilgrims who
reach the holding point join a queue there (capped at `max_held_persons`: registrations assumed suspended);
after the hold ends the queue moves on at `release_per_hour`. This shows the second-order risk: closing a track
crowds the people below it. The base flow above a hold is not reduced (exposure there is overstated).

Impact counterfactual (I, SIMULATED): "how many pilgrims would have been on the slide segment if the hold had
been approved at time T". `simulate(..., stop_ascent={leaf: (hold_segment_id, from_ts)})`: an ascending pilgrim
on that leaf route who reaches the start of the hold segment at or after `from_ts` stays there (not counted
above it, no descent). `stop_ascent=None` gives exactly the current output. Targets = segments with
`past_slide_at`; event = their `past_slide_at`; snapshot = last whole hour at or before the event. Hold points
per leaf route come from `hold_points()` with the hazard at the decision hour. Scenarios: `no_action`,
`first_orange` and `first_red` (first hour of the ORANGE / RED warning still in force at the snapshot, in
`segment_hazard` for the source; an earlier warning that cleared does not count),
`official_closure` (the replay timeline event "~12:00 shrine board says old track closed", approximate).

Camera crowd count (V): DM-Count (MIT) exported to ONNX, run with onnxruntime on CPU. A camera
(`vision.cameras`) watches one segment and sees `view_area_m2` of it (ASSUMED, demo value).
density = count / view_area_m2; persons_on_segment = density x length_m x width_m; level from `crowd.bands_ppm2`.
Demo photos are openly licensed crowd photos, not Vaishno Devi cameras, and the UI says so.

## Alert workflow (B)
States: PROPOSED -> APPROVED -> SENT -> ACKED; PROPOSED -> REJECTED; PROPOSED -> ESCALATED (no action in
10 min) -> APPROVED/REJECTED; any open state -> CANCELLED; SENT/ACKED -> EXPIRED (after `expires_at`); PROPOSED/ESCALATED -> CANCELLED by
the system (action WITHDRAW) when the risk condition cleared before anyone acted. Sending is SIMULATED and
happens as soon as the approvals are complete.
- Auto-proposal when risk_level >= 2 on a segment with no covering alert. An alert covers its segments from
  its `trigger_ts` (risk time, so replay-safe) until their risk falls below the alert's own level. All
  segments of one route at one level form one alert. While that alert is pending and has no approval, later
  segments of the same route and level join it (system action EXTEND, audited) instead of a new alert.
  A RED over an ORANGE references it (CAP Update if sent).
- An alert with an approval is never withdrawn by the system; escalation counts from the latest officer action.
- CAP Cancel: `<sent>` = cancel time, `<references>` = the original send; a never-sent cancelled alert has no
  CAP message (HTTP 409).
- Every write transaction takes the audit advisory lock first (no deadlock, no duplicate proposals).
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
  `alerts.cap_area_buffer_m` (100 m) buffer of the segments. Templates in `backend/app/alerts/templates/`. Dogri/Kashmiri: TODO, need a native speaker.

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
- `GET /api/impact/counterfactual?source=gfs_seamless` -> `{"simulated":true,"target_segments":[...],"event_ts","snapshot_ts",
  "scenarios":[{"key","label","decision_ts","hold_points":{"<leaf route>":"<segment id>"},"persons_on_target"}]}`
  (`decision_ts` and `hold_points` are null for `no_action`; a scenario whose decision time is missing or after the
  snapshot is omitted)
- `GET /api/vision/cameras` -> `[{"id","segment_id","view_area_m2","label","assumed":true}]`
- `GET /api/vision/samples` -> `[{"name","attribution","license","source_url"}]`; `GET /api/vision/samples/{name}` -> the image
- `POST /api/vision/count?camera_id=&persist=false`, multipart field `image` or form field `sample=<name>` ->
  `{"camera_id","segment_id","count","density_ppm2","persons_on_segment","level","heatmap_png_b64","model","demo_image","ms","persisted"}`;
  `demo_image` is true when a sample photo was used; unknown camera or sample -> 404, unreadable image, image
  outside `vision.max_image_pixels` / `vision.min_side_px`, or `persist=true` with a sample -> 422 (a demo photo is
  never written as a live crowd row); upload above `vision.max_upload_bytes` -> 413; model file missing or sha256
  mismatch -> 503.
- `GET /api/impact/counterfactual` errors: no replay hazard for the source -> 404; holding disabled or targets with
  different slide times -> 409. A scenario with no hold point at its decision hour is omitted. `persist=true` (live mode) upserts the camera segment's
  current-hour `segment_crowd` row with `simulated=false`, `scenario={"source":"camera","camera_id"}`, then re-runs
  live risk for that hour.
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
