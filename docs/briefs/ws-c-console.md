# Brief: workstream C — officer console (frontend)

Read `CLAUDE.md` and `docs/PLAN.md` first; they are binding. Work on branch `ws-c-console` and open a PR to `main`.
Two other cloud sessions build the backend at the same time, so build against the API contract in
`docs/PLAN.md` "HTTP API". Touch only C's paths: `frontend/` and `docs/api-fixtures/`.

## Build
1. `docs/api-fixtures/*.json`: example responses for every endpoint in the contract. Use the real segment
   geometry from `data/segments_vaishno_devi.geojson`, with plausible levels for 26 Aug 2025 (label the
   fixtures as examples, not real results).
2. `frontend/index.html`, `frontend/app.js`, `frontend/style.css`: static, no build step, served by FastAPI at `/`.
   Use MapLibre GL JS from a pinned CDN version (e.g. unpkg `maplibre-gl@4.7.1`) and OSM raster tiles with attribution.
   - Map: segments coloured by `risk_level` (GREEN/YELLOW/ORANGE/RED). The legend also shows the level name in
     text (not only colour). Click a segment: a side panel shows hazard, crowd, the drivers in words
     ("24 h rain 63.9 mm = 4.5x threshold; slope 39 deg; 1,240 people"), and a small history chart.
   - Mode switch: LIVE / REPLAY. Replay has a time slider over the timeline (10-28 Aug 2025, hourly), play/pause,
     and event markers (14 Aug Chasoti, 26 Aug 14:40 Adhkuwari).
   - Alerts panel: proposed/open alerts, needed vs given approvals, buttons Approve / Edit / Reject /
     Break-glass, with an officer picker (from `/api/officers`). Show the CAP XML and the audit trail for an alert,
     and an "Audit chain verified" badge from `/api/audit/verify`.
   - A visible "SIMULATED" tag wherever crowd numbers or delivery channels are simulated, and a footer with
     data attribution (OSM ODbL, Open-Meteo CC BY 4.0, Copernicus DEM).
   - A `?fixtures=1` URL flag that reads `docs/api-fixtures/` instead of the API, so the console works before the
     backend is merged. Default is the real API.
3. Make it work on a 1366x768 laptop screen and on a phone (the stall demo may use a phone). Keyboard focus visible.
4. Check your work: serve the repo root with `python -m http.server`, open `frontend/index.html?fixtures=1` in a
   headless browser if one is available (e.g. Playwright), take screenshots of map, replay and alert approval, and
   attach them to the PR. If no browser is available, say so in the PR.

## Done
PR open, with screenshots or an exact note of what you could not check.
If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
Never mock, substitute or guess real-world data.
