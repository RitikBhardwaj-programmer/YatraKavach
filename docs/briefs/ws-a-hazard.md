# Brief: workstream A — hazard engine

Read `CLAUDE.md` and `docs/PLAN.md` first; they are binding. Work on branch `ws-a-hazard` and open a PR to `main`.
Two other cloud sessions work at the same time: B (crowd, risk, alerts) and C (console). Touch only A's paths:
`backend/app/hazard/`, `backend/tests/hazard/`, `scripts/load_*.py`, `db/init/010-019_*.sql`.

## Build
1. `scripts/load_segments.py`: load `data/segments_vaishno_devi.geojson` into `segments`. Set `rain_point` to the
   nearest of katra (32.9922, 74.9315), adhkuwari (33.0085, 74.9447), bhawan (33.0311, 74.9491). Set
   `past_slide = true` for `VD-OLD-01` (26 Aug 2025 Adhkuwari landslide, sourced in `docs/research.md`).
   Leave `susceptibility` NULL (GSI data not available).
2. `scripts/load_replay_rain.py`: load every `data/replay/rain_*.json` into `rain_hourly`, mode `replay`
   (timestamps are IST; store as timestamptz).
3. `backend/app/hazard/rules.py`: pure functions (no DB) for the hazard rules in `docs/PLAN.md` "Rules", with
   values from `config/thresholds.yaml`: R24, R15d, I-D curve for D in {1,3,6,12,24}, slope/past-slide step-up,
   hysteresis. Return level 0-3 and a `drivers` dict that explains the level in numbers, with a short `rule` name.
4. `backend/app/hazard/engine.py`: for a mode (`replay`/`live`), a source and a time range, compute hourly
   `segment_hazard` rows per segment and upsert them (idempotent).
5. `backend/app/hazard/live.py`: fetch hourly precipitation for the 3 points from the Open-Meteo forecast API
   (past 15 days + next 24 h) into `rain_hourly`, mode `live`. If the network is blocked, code it, unit-test it
   with a saved fixture, and say in the PR that the real API was not called.
6. `backend/app/hazard/router.py` exposing `router`: `GET /replay/timeline` (contract in PLAN) and
   `POST /hazard/run?mode=&source=`. The app mounts it at `/api`.
7. Tests in `backend/tests/hazard/`:
   - Rules unit tests without a DB: each threshold edge, the I-D curve, step-up, hysteresis.
   - Integration test (skip with a clear message if no DB): load data, run the replay for `gfs_seamless`, assert
     `VD-OLD-01` is level >= 2 before 2025-08-26 12:00 IST and level 3 before 14:40 IST.
   - Put the measured first ORANGE and RED times for `ecmwf_ifs025`, `gfs_seamless` and `era5` in the PR text.

## Done
PR open, tests passing, and the PR description lists what you verified, which DB setup you used (Docker or apt
PostGIS), and any contract questions. Run pytest and the replay assertion before you report.
If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
Never mock, substitute or guess real-world data.
