# API fixtures (EXAMPLES, not real results)

Example responses for every endpoint in `docs/PLAN.md` "HTTP API", so the console can run before the
backend is merged (`frontend/index.html?fixtures=1`). Regenerate with
`python docs/api-fixtures/build_fixtures.py` (needs PyYAML).

What is real and what is not:
- **Real:** segment geometry and attributes (`data/segments_vaishno_devi.geojson`, OSM ODbL + Copernicus DEM)
  and the archived GFS rain (`data/replay/rain_*_gfs_seamless.json`, Open-Meteo CC BY 4.0).
- **Example:** hazard levels use a simplified form of the PLAN rules with values from `config/thresholds.yaml`;
  workstream A's engine is the real one. The rain point is the nearest of katra / adhkuwari / bhawan to the
  segment midpoint. Alerts, approvals, audit rows (real sha256 chain over the example rows) and CAP XML are
  illustrations of the contract. The CAP polygon is the convex hull of 100 m circles around the vertices, an
  approximation of the 100 m buffer. Hindi and Urdu text needs native-speaker review.
- **SIMULATED:** all crowd numbers (`persons`, `density_ppm2`, `crowd_level`), from a seeded generator.
- `segments_live.json` is NOT live data: it reuses the replay hour 2025-08-20 12:00 as an example shape.

| Endpoint | Fixture |
|---|---|
| `GET /api/health` | `health.json` |
| `GET /api/segments?mode=live` | `segments_live.json` |
| `GET /api/segments?mode=replay&at=2025-08-26T12:00+05:30` | `segments_replay.json` (other hours: built from `history/`) |
| `GET /api/replay/timeline` | `replay_timeline.json` |
| `GET /api/segments/{id}/history` | `history/{id}.json` (whole replay window, hourly) |
| `GET /api/alerts` | `alerts.json` (snapshot as of 2025-08-26 12:00) |
| `POST /api/alerts/{id}/approve` (and reject, cancel, ack, PATCH) | `alert_approve_example.json` (returns the alert) |
| `POST /api/alerts/{id}/break-glass` | `alert_break_glass_example.json` |
| `GET /api/alerts/{id}/cap.xml` | `cap/{id}.xml` |
| `GET /api/audit?alert_id=` | `audit/{id}.json` (all rows: `audit.json`) |
| `GET /api/audit/verify` | `audit_verify.json` |
| `GET /api/officers` | `officers.json` |
| `POST /api/replay/run` | `replay_run.json` |
| `GET /api/impact/counterfactual?source=gfs_seamless` | `impact_counterfactual_gfs_seamless.json` (also `_ecmwf_ifs025`) |
| `GET /api/vision/cameras` | `vision_cameras.json` |
| `GET /api/vision/samples` | `vision_samples.json` |
| `GET /api/vision/samples/{name}` | `vision/samples/{name}` |
| `POST /api/vision/count` | `vision_count.json` (same EXAMPLE result for any image, sample or `persist`) |
| (console header, no endpoint) | `lead_time_findings.json` |

### Impact and vision fixtures (EXAMPLES; `python docs/api-fixtures/build_console2_fixtures.py`, needs Pillow)
- **Impact (EXAMPLE numbers):** `persons_on_target` values (100, 200, 500, 700, 1000) are round EXAMPLE
  numbers, not simulation output; workstream I computes the real ones. Decision and event times are copied
  from `docs/replay-findings.md` "System result" (first ORANGE / RED of `VD-OLD-01` per source, the ~12:00
  board closure, the 14:40 slide). Hold points (`VD-TRUNK-13` for both leaf routes) are EXAMPLE values.
- **Vision (EXAMPLE):** the camera is `vision.cameras` from `config/thresholds.yaml` (its `view_area_m2` is
  an ASSUMED demo value). The sample `example-placeholder.png` is a generated picture of grey dots, NOT a photo
  and not a camera; workstream V ships the real, openly licensed photos and their credits. The count (300) and
  `ms` (500) are round EXAMPLE numbers, not model output; density, persons and level follow the PLAN maths from
  that count (300 / 150 m2 = 2.0 per m2 -> YELLOW; x 487.8 m x 6.0 m of `VD-TRUNK-01`). The heatmap is a blur
  of the drawn dots, not a model density map.
- **Lead time (measured, not an example):** `lead_time_findings.json` copies the first RED times of
  `docs/replay-findings.md` for GFS and ECMWF. The console uses it only when the impact API is unavailable,
  and labels it "from replay findings".

Fields the console reads beyond the contract (optional; the console works without them):
`level_name`, `expires_at`, `example` on alerts; `ts`, `mode`, `thresholds_version` on segment properties;
`fixture_note` and `example` on FeatureCollections. Audit rows: `id, ts, alert_id, actor, from_state,
to_state, reason, input_snapshot, message, thresholds_version, prev_hash, hash`, with
`hash = sha256(prev_hash + canonical JSON of the row without hash)`, canonical = sorted keys, no spaces.
