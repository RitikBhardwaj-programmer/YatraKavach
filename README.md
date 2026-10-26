# YatraKavach

**Route-segment landslide and crowd risk for the Vaishno Devi tracks, with alerts that a named officer approves,
in three languages, with a tamper-evident audit log.**

Prototype for **Hack for Social Cause 2027** (VBYLD 2027, Ministry of Youth Affairs & Sports; knowledge partner
IIT Bombay). Theme 11: Disaster Mitigation & Resilience. Team **kavach**, Jammu & Kashmir (HSC|JK|00032).

> **The warning existed. The decision did not.**
> On 26 Aug 2025 at 14:40 a landslide on the old Vaishno Devi track near Adhkuwari killed at least 34 pilgrims.
> In a replay of the rain forecasts of that day, YatraKavach raises the Adhkuwari segment to **RED at 05:00 IST**
> (GFS forecast), about 9.5 hours before the slide, and proposes "clear the old track" for officer approval.
> With the ECMWF forecast the lead time is about 1.5 hours. Details: [docs/replay-findings.md](docs/replay-findings.md).
> In a SIMULATED crowd, a hold approved at the first ORANGE warning leaves **0** pilgrims on that segment at 14:00,
> in all three weather models; with no action there are **674**. The cost of that hold is a long queue at the
> Katra gate, which the system also models.

## The problem
Three recent yatra disasters in J&K show the same break (sources in [docs/research.md](docs/research.md)):

| Date | Place | What happened |
|---|---|---|
| 8 Jul 2022 | Amarnath cave | Flash flood; no rain data from the upper reaches |
| 14 Aug 2025 | Chasoti, Machail yatra | IMD alerts existed for the region; the yatra went on; about 61-64 dead |
| 26 Aug 2025 | Adhkuwari, Vaishno Devi | Landslide at 14:40; at least 34 dead; the board says it closed the old track by 12:00 |

India already has forecasts (IMD), landslide bulletins (GSI), crowd systems (RFID, CCTV) and mass alerts
(NDMA SACHET, cell broadcast). They work in silos and at district scale. What was missing each time was the step
from "regional alert" to **"close this 500 m stretch now, move the people on it, and record who decided"**.

## What YatraKavach does
1. **Splits each track into ~500 m segments** (35 segments: trunk Katra-Adhkuwari, old track, Himkoti track),
   with slope from a digital elevation model.
2. **Scores landslide hazard per segment every hour** from rain over 3 h, 24 h and 15 days, using published
   Himalayan rainfall thresholds, plus a step-up for steep slopes and recorded past slides. Every level comes
   with its reasons in numbers ("24 h rain 191 mm = 1.3x the 144 mm threshold; slope 41 deg").
3. **Adds people:** pilgrims on each segment (SIMULATED RFID gate counts, capped at the 50,000/day limit), and a
   SIMULATED holding-area scenario: when the ascent is stopped, pilgrims queue at Katra, Banganga or Adhkuwari.
   Risk rises when a hazardous segment has people on it.
4. **Proposes one action per track and level** ("Hold pilgrims at Adhkuwari; stop ascent beyond ...",
   "Clear segments ...; move pilgrims to ..."). Nothing goes out automatically.
5. **A named officer approves.** RED needs two different officers. No answer in 10 minutes: escalation.
   A senior officer can "break glass" with a written reason. Every step is written to a hash-chained audit log
   that cannot be edited (database triggers block UPDATE and DELETE) and can be verified.
6. **Sends a CAP 1.2 alert** (Common Alerting Protocol, the format NDMA SACHET uses) in English, Hindi and Urdu,
   with the affected area as a polygon. In this prototype every message is `status=Exercise` and delivery is SIMULATED.
7. **Replays August 2025** hour by hour, so anyone can check what the system would have proposed and when.
8. **Shows the cost of waiting** (SIMULATED): for each warning time, how many pilgrims would still have been on
   the slide segment if officers had approved the hold then (`GET /api/impact/counterfactual`).
9. **Counts people from a camera image** with an AI model (DM-Count, run on CPU with ONNX Runtime). A camera
   watches one segment; the count becomes a crowd density and level. In LIVE mode the count of an uploaded image
   can be applied to the live crowd instead of the simulated value; demo photos cannot. The demo uses openly
   licensed festival photos, not Vaishno Devi cameras, and the console says so.

## Architecture

```mermaid
flowchart LR
  subgraph Inputs
    OSM["OpenStreetMap tracks<br/>+ Copernicus DEM"] --> SEG[(segments<br/>PostGIS)]
    OM["Open-Meteo rain<br/>live + Aug 2025 archive"] --> RAIN[(rain_hourly)]
    SIM["Crowd simulator<br/>RFID gate counts<br/>SIMULATED"]
  end
  RAIN --> HZ["Hazard engine<br/>thresholds, slope,<br/>past slide, hysteresis"]
  SEG --> HZ
  HZ --> SH[(segment_hazard)]
  SH --> HOLD["Holding-area scenario<br/>SIMULATED"]
  SIM --> HOLD --> SC[(segment_crowd)]
  SH --> FUSE["Risk fusion"]
  SC --> FUSE --> SR[(segment_risk)]
  SR --> PROP["Proposals<br/>one per track + level"]
  PROP --> WF{"Officer approval<br/>2 officers for RED<br/>escalation, break-glass"}
  WF --> AUD[(audit_log<br/>hash chain)]
  WF --> CAP["CAP 1.2 XML<br/>en / hi / ur"]
  CAP --> OUT["SACHET, cell broadcast,<br/>SMS, PA: SIMULATED"]
  SR --> UI["Officer console<br/>map, replay, alerts"]
  WF --> UI
```

| Part | Code | Notes |
|---|---|---|
| Hazard rules (pure) and engine | `backend/app/hazard/` | Rules in `config/thresholds.yaml`, versioned; each row stores the version |
| Crowd simulator, holding scenario | `backend/app/crowd/` | Everything here is SIMULATED and labelled so |
| Risk fusion, segments API, replay | `backend/app/risk/` | `POST /api/replay/run` recomputes the whole chain |
| Alert workflow, CAP, audit | `backend/app/alerts/` | State machine is pure Python; DB layer locks and audits |
| Impact counterfactual | `backend/app/impact/` | Re-runs the SIMULATED crowd with the ascent stopped at each decision time |
| Camera crowd count | `backend/app/vision/` | DM-Count ONNX model (43 MB, sha256-checked), heatmap, demo photos |
| Officer console | `frontend/` | Static HTML + MapLibre GL, no build step |
| Schema | `db/init/*.sql` | PostgreSQL 16 + PostGIS 3 |
| Contract and design | `docs/PLAN.md` | Schema, rules, API, workflow |

Stack: Python 3.12, FastAPI, PostgreSQL 16 + PostGIS 3, psycopg 3, pytest, MapLibre GL JS, Docker Compose.

## Run it

Requirements: Docker Desktop (or Docker Engine with Compose), Git, free ports 5432 and 8000.

```bash
git clone https://github.com/RitikBhardwaj-programmer/YatraKavach.git
cd YatraKavach
docker compose up -d --build
docker compose exec api python scripts/load_segments.py
docker compose exec api python scripts/load_replay_rain.py
curl -X POST "http://localhost:8000/api/replay/run?until=2025-08-26T14:00:00%2B05:30"
```

Open http://localhost:8000/ and pick **REPLAY**. Move the slider to 26 Aug 2025 to watch the tracks turn red,
click a segment to see why, and approve an alert as two different demo officers.

- The replay run takes about 30-60 seconds.
- If a local PostgreSQL already uses port 5432 or something uses 8000, choose other host ports, for example
  `YK_DB_PORT=55432 YK_API_PORT=8010 docker compose up -d --build`.
- `until` is the replay clock: the run stops at 26 Aug 14:00 IST, 40 minutes before the slide, with 6 alerts
  open for officers. Without it the run goes to 28 Aug 23:00; by then the rain has stopped and the system
  withdraws every unapproved alert, so the console shows none open.
- The clock only moves forward and the audit log is append-only, so a later run with an earlier `until` changes
  nothing. To start the demo again, reset the database first: `docker compose down -v`, then repeat the steps above.
- Live mode: `curl -X POST "http://localhost:8000/api/hazard/run?mode=live"` fetches current Open-Meteo rain.
- API docs: http://localhost:8000/docs

### Tests
```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://yk:yk_dev_only@localhost:5432/yatrakavach python -m pytest
```
Use `python -m pytest`, not a bare `pytest`: it puts `backend/` on the import path so the tests can import `app`.
On a fresh clone with Python 3.12 and a fresh PostgreSQL 16 + PostGIS 3 database, 258 tests pass (measured
2026-10-26). Pure-logic tests run without a database (239 pass, 19 database tests skip with a message when none
is reachable). Use the port you gave `YK_DB_PORT`.

Without Docker: install PostgreSQL 16 + PostGIS 3, create database `yatrakavach` (user `yk`, password
`yk_dev_only`), run `db/init/*.sql` in order, then run the two `scripts/load_*.py` from the repo root and
`uvicorn app.main:app` from `backend/`, all with the `DATABASE_URL` above.

## Sample data in the repo
All data the demo needs are in the repo; nothing is downloaded at run time except live-mode rain.

| Path | What | Source |
|---|---|---|
| `data/segments_vaishno_devi.geojson` | 35 track segments (~500 m) with slope | OpenStreetMap + Copernicus DEM |
| `data/replay/rain_<point>_<model>.json` | Hourly rain 10-28 Aug 2025, IST, 3 points x 3 models | Open-Meteo |
| `backend/app/vision/samples/*.jpg` | 4 crowd photos for the camera demo (not Vaishno Devi) | Wikimedia Commons |
| `backend/app/vision/model/dmcount_sha_fp16.onnx` | DM-Count crowd-count model, 43 MB | DM-Count authors' weights |
| `docs/api-fixtures/` | Recorded API responses and CAP XML from a replay run | Generated by this code |

## Data sources and licences
- Tracks: © OpenStreetMap contributors, [ODbL](https://opendatacommons.org/licenses/odbl/).
- Elevation: Copernicus DEM GLO-90 via the [Open-Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api).
  © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European
  Union and ESA; all rights reserved.
- Rain: [Open-Meteo.com](https://open-meteo.com/), CC BY 4.0. Live forecast; Historical Forecast API (ECMWF IFS
  0.25, NOAA GFS) and ERA5 reanalysis for the replay. Free tier, non-commercial use.
- Thresholds: Shah et al. 2024 (NH-44 / Kashmir daily and antecedent rain), Dahal & Hasegawa 2008 (Nepal
  Himalaya intensity-duration curve, 144 mm/day). Full list with links in [docs/research.md](docs/research.md).
- How the data files were made: `scripts/build_segments.py`, `scripts/fetch_replay_rain.py`.
- Crowd-count model: [DM-Count](https://github.com/cvlab-stonybrook/DM-Count) (Wang et al., NeurIPS 2020), MIT
  licence, official ShanghaiTech A weights, exported to ONNX by `scripts/export_dmcount_onnx.py`.
  The ONNX file in the repo is that export (fp16) and stays under DM-Count's MIT licence, © 2020 CVLab@StonyBrook.
  The weights were trained by the DM-Count authors on the ShanghaiTech Part A dataset (Zhang et al., CVPR 2016),
  which is published for research use; no ShanghaiTech images are in this repo.
  Measured MAE 60.10 on the ShanghaiTech Part A test set (`scripts/eval_vision.py`).
- Demo photos: Wikimedia Commons, CC BY 4.0 / CC BY 2.5 / CC BY-SA 4.0; authors and links in
  [backend/app/vision/samples/ATTRIBUTION.md](backend/app/vision/samples/ATTRIBUTION.md). Resized copies of the
  CC BY-SA photos stay under CC BY-SA 4.0.

## Limitations (read before judging the numbers)
- **Thresholds are not calibrated for these tracks.** They come from studies of NH-44 and the Nepal Himalaya.
  A real deployment needs local slide records and a calibration season.
- **Rain data are coarse.** Forecast models use 9-25 km grid cells. They show a dangerous day over the area; they
  cannot see a single cloudburst cell or the exact slope that fails. A real deployment would use IMD Doppler radar
  (Jammu, Srinagar, Banihal) and rain gauges on the track.
- **Replay is not a real-time test.** The "historical forecast" data are short-lead forecasts stitched together,
  close to what a live system would have seen, but not identical. ERA5 is a later reanalysis and was not
  available on the day.
- **Lead time depends on the model:** about 9.5 h with GFS, about 1.5 h with ECMWF and ERA5 on 26 Aug 2025.
- **Crowd numbers are SIMULATED.** No RFID or CCTV feed was used. The holding-area queue is a scenario with
  assumed sites, capacity and release rate. It does not reduce the flow above a hold, so exposure there is overstated.
- **The impact numbers are SIMULATED.** They show the effect of decision timing in the crowd model, not real
  head counts. Only the ascent is stopped; pilgrims already above the hold keep walking.
- **The camera count is a demo.** No Vaishno Devi camera feed was used. The ground area a camera sees
  (150 m²) is an assumed value, so the density from a demo photo is illustrative. The model's average error on
  dense test crowds is about 60 people per image. The model takes 2-5 s per image on CPU; with the heatmap, a
  request takes 3-8 s. Applying a count to the live crowd is not tied to a named officer or audited yet, and the
  next simulated live crowd run can overwrite it. Uploads are limited to 10 MB and 40 megapixels.
- **The ~12:00 closure is modelled as a hold at the Katra gate** (the system's hold point that hour), 6.3 km
  below the slide, so it shows no effect at 14:00. The real closure was of the old track at Adhkuwari.
- **No GSI susceptibility layer.** The GSI 1:50k map could not be obtained in time; slope is the stand-in.
- **Delivery is SIMULATED.** No SMS, SACHET, cell broadcast or siren is triggered. CAP messages are `Exercise`.
- **Hindi and Urdu texts need review by native speakers.** Dogri and Kashmiri are not done yet.
- **Machail route is not included:** OpenStreetMap has no trek line past the road end.
- **No authentication:** demo officers are picked from a list. Production needs real identity (e.g. government SSO).
- CAP XML is checked for structure in tests, but not yet against the official OASIS schema file.

## What it integrates, not replaces
YatraKavach is a thin decision layer. In a deployment it would read IMD radar and GSI bulletins, SMVDSB RFID gate
counts and CCTV density, and hand approved CAP messages to NDMA SACHET, the shrine-board app and camp PA systems.
It does not build its own sensors or alert network.

## AI-use disclosure
The HSC 2027 rules ask for a disclosure of AI use and an estimate of its share.

- **Tool:** Claude Code (Anthropic, model Claude Opus 5.5), used as a coding and research agent, including
  parallel agent sessions for the hazard engine, the alert workflow, the console, the impact counterfactual and
  the camera crowd count. The crowd-count model itself (DM-Count) is published research, not generated.
- **What AI did:** web research and the sourced research report; most of the source code, tests and
  documentation; an independent code review that found the replay-hindsight bug and the alert flood.
- **What the team did:** chose the problem and the J&K focus; set the requirements and constraints; approved every
  design decision and each fix; ran, checked and judged the results; owns the pitch.
- **Share (team estimate):** about 85-90% of the code and documents were generated by AI under the team's
  direction; the problem framing, decisions and validation are the team's.

<!-- TODO before submission: confirm the share above is your honest estimate. -->

## Licence
Code: MIT, see [LICENSE](LICENSE). Data keep their own licences (above).
